#!/usr/bin/env python3
"""Source-bound temporal, kernel mesh and physical-parameter verification bench.

No experimental/clinical validation; proposed budgets are never approvals.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'python'), str(ROOT/'tools')]
from flow_refinement import configuration, connected
from dialysislab.distributed import advect_face, solve
from dialysislab.protocol import expect
from dialysislab import physical
from dialysislab.compartments import Compartments

STEPS = (400, 200, 100, 50, 25)
MODES = ('hd', 'hdf_pre', 'hdf_post')
DURATION = 12000
WINDOW = 400
# Proposed absolute floors plus 0.5% of finest trajectory maximum. Engineering
# discrimination targets, not calibrated clinical tolerances or error bounds.
FLOORS = {'net_uf_demand_mL_min': .1, 'prepared_mmol_L': .01, 'pressure_mmHg': .5, 'level': .002, 'body_mmol_L': .01,
          'blood_local_mmol_L': .02, 'dialysate_local_mmol_L': .02,
          'transfer_mmol': .002, 'net_loss_mL': .05, 'gross_uf_mL': .05,
          'feed_volume_mL': .05, 'drain_volume_mL': .05,
          'feed_mean_mL_min': .5, 'drain_mean_mL_min': .5,
          'blood_mean_mL_min': .5, 'uf_mean_mL_min': .1}
SOLUTES = ('urea', 'sodium', 'potassium', 'chloride', 'bicarbonate', 'calcium')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False, default=vars).encode()).hexdigest()


def compile_bench(directory):
    binary = Path(directory)/'numerical-plant'
    command = ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
               '-DDIALYSISLAB_NUMERICAL_STIMULI', str(ROOT/'tests/guided_plant.cpp'), '-o', str(binary)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if completed.returncode:
        raise RuntimeError('numerical bench compilation: '+completed.stderr)
    return binary


def stimulus(f, scenario, elapsed):
    """All events precede integration; all tested dt exactly divide event times."""
    if elapsed not in (2400, 6400, 8800):
        return None
    config = f.config
    if scenario in ('concentration', 'combined'):
        # Change source composition, never edit stored mass/concentration in place.
        acid = config['physical']['fluid']['acid_mmol_L']
        urea, potassium = (90, 135) if elapsed == 2400 else (acid[0], acid[2])
        expect(f.call(6, 'ACID', urea, potassium), 'OK', 1)
    net = {2400: 12, 6400: 2, 8800: 5}[elapsed]
    if scenario in ('uf', 'combined'):
        expect(f.call(6, 'UF', net), 'OK', 1)
    if scenario == 'combined':
        return (MODES.index(config['treatment']['mode'].lower()),
                {2400: 220, 6400: 340, 8800: 300}[elapsed], net,
                0 if config['treatment']['mode'] == 'HD' else 40)
    return None


def observables(r, origin, cumulative, window):
    p, patient = r['physical'], r['patient']
    d, network = p['dynamics'], patient['distributed']
    result = dict(net_uf_demand_mL_min=[r['machine']['net_uf_prescribed_mL_min']], pressure_mmHg=[p[k] for k in ('arterial_mmHg', 'venous_mmHg', 'tmp_mmHg', 'dialysate_mmHg')],
                  level=[d['arterial_level'], d['venous_level']],
                  net_loss_mL=[patient['net_patient_loss_mL']-origin['net_patient_loss_mL']],
                  gross_uf_mL=[patient['gross_uf_mL']-origin['gross_uf_mL']],
                  feed_volume_mL=[cumulative[0]], drain_volume_mL=[cumulative[1]])
    for i, name in enumerate(('feed_mean_mL_min', 'drain_mean_mL_min', 'blood_mean_mL_min', 'uf_mean_mL_min')):
        result[name] = [window[i]*60000/WINDOW]
    for s, name in enumerate(SOLUTES):
        result['prepared_mmol_L/'+name] = [r['online']['concentration_mmol_L'][s]]
        result['body_mmol_L/'+name] = [row[s] for row in patient['concentration_mmol_L'][:2]]
        result['blood_local_mmol_L/'+name] = [c['concentration_mmol_L'][s] for c in network['compartments']]
        result['dialysate_local_mmol_L/'+name] = [row[s] for row in network['dialysate_concentration_mmol_L']]
        result['transfer_mmol/'+name] = [network['dialysate_transfer_mmol'][s]-origin['distributed']['dialysate_transfer_mmol'][s]]
    return result


def run(f, dt, scenario, parameter=None, factor=1.0, samples=None):
    f.config['dt_ms'] = dt
    initial = digest(dict(record=f.record, patient=f.patient.__dict__))
    if parameter == 'koa':
        f.patient.config['extracorporeal']['koa_mL_min'] = [x*factor for x in f.patient.config['extracorporeal']['koa_mL_min']]
    elif parameter == 'refill':
        f.patient.config['hemodynamics']['refill_mL_min'] *= factor
    elif parameter == 'pump_tau':
        expect(f.call(6, 'PUMP_TAU', f.config['physical']['dynamics']['pump_tau_s']*factor), 'OK', 1)
    origin = copy.deepcopy(f.record['patient'])
    samples = [] if samples is None else samples
    events = []
    cumulative, window = [0.0, 0.0], [0.0]*4
    maxima = dict(body_and_circuit_water_mL=0.0, water_mL=0.0, solute_mmol=0.0, rbc_mL=0.0, protein_g=0.0)
    peaks = dict(pressure_mmHg=[0.0]*4, level=[0.0]*2)
    previous_cycle = f.record['physical']['dynamics']['balance_cycles']
    limitations, bypass_ticks = {}, 0
    for elapsed in range(0, DURATION, dt):
        r = f.step(rx=stimulus(f, scenario, elapsed))
        if r['machine']['alarm_mask'] or f.stage != 'TREATMENT':
            raise ValueError('unexpected alarm or stage at %d ms' % elapsed)
        p, patient = r['physical'], r['patient']
        d, h = p['dynamics'], patient['hemodynamics']
        limitations[p['limitation']] = limitations.get(p['limitation'], 0)+1
        bypass_ticks += bool(d['bypass'])
        for i, flow in enumerate((d['feed_mL_min'], d['drain_mL_min'], r['blood_mL_min'], r['uf_mL_min'])):
            amount = flow*dt/60000
            window[i] += amount
            if i < 2: cumulative[i] += amount
        maxima['body_and_circuit_water_mL'] = max(maxima['body_and_circuit_water_mL'], abs(math.fsum([
            f.patient.initial_body, f.config['patient']['prime_mL'], patient['external_in_mL'],
            -patient['external_out_mL'], -patient['gross_uf_mL'], patient['substitution_mL'],
            patient['flush_in_mL'], -patient['flush_out_mL'], -sum(patient['volume_mL'])])))
        maxima['water_mL'] = max(maxima['water_mL'], abs(d['dialysate_residual_mL']))
        maxima['solute_mmol'] = max(maxima['solute_mmol'], *map(abs, patient['mass_residual_mmol']),
                                   *map(abs, patient['distributed']['dialysate_residual_mmol']))
        maxima['rbc_mL'] = max(maxima['rbc_mL'], abs(h['rbc_residual_mL']))
        maxima['protein_g'] = max(maxima['protein_g'], abs(h['protein_residual_g']))
        cycle = d['balance_cycles']
        if cycle != previous_cycle:
            events.append(dict(cycle=int(cycle), lower_ms=elapsed, upper_ms=elapsed+dt))
            previous_cycle = cycle
        values = observables(r, origin, cumulative, window)
        for key in peaks:
            peaks[key] = [max(a, abs(b)) for a, b in zip(peaks[key], values[key])]
        if (elapsed+dt) % WINDOW == 0:
            samples.append(dict(time_ms=elapsed+dt, values=values))
            window = [0.0]*4
    if len(samples) != DURATION//WINDOW or max(maxima.values()) > 1e-6:
        raise ValueError('sample count/conservation regression')
    return dict(dt_ms=dt, initial_sha256=initial, samples=samples,
                trajectory_sha256=digest(samples), residual_maxima=maxima,
                all_tick_absolute_peaks=peaks, valve_event_brackets=events,
                limitations_ticks=limitations, bypass_ticks=bypass_ticks,
                final_2s_pressure_range_mmHg=[max(s['values']['pressure_mmHg'][j] for s in samples[-5:])-min(s['values']['pressure_mmHg'][j] for s in samples[-5:]) for j in range(4)],
                settling_status='Not established: short horizon and persistent valve cycles; final 2s range is not a settling-time oracle.',
                parameter=parameter, factor=factor)


def metrics(a, b):
    if not a or len(a) != len(b) or [s['time_ms'] for s in a] != [s['time_ms'] for s in b]:
        raise ValueError('unaligned observation grid')
    result = {}
    for key in a[0]['values']:
        errors, reference = [], []
        for x, y in zip(a, b):
            if set(x['values']) != set(y['values']) or len(x['values'][key]) != len(y['values'][key]):
                raise ValueError('observable shape mismatch')
            errors.extend(u-v for u, v in zip(x['values'][key], y['values'][key]))
            reference.extend(y['values'][key])
        if not all(math.isfinite(v) for v in errors+reference):
            raise ValueError('nonfinite observation')
        scale = max(map(abs, reference))
        budget = FLOORS[key.split('/')[0]]+.005*scale
        result[key] = dict(rms=math.sqrt(math.fsum(e*e for e in errors)/len(errors)),
                           maximum_absolute=max(map(abs, errors)), final_maximum=max(abs(u-v) for u,v in zip(a[-1]['values'][key], b[-1]['values'][key])),
                           reference_scale=scale, proposed_budget=budget,
                           within_proposed_budget=max(map(abs, errors)) <= budget)
    return result


def comparisons(runs):
    if len({r['initial_sha256'] for r in runs}) != 1:
        raise ValueError('unequal initial checkpoint')
    adjacent = [dict(coarse_ms=a['dt_ms'], fine_ms=b['dt_ms'], metrics=metrics(a['samples'], b['samples'])) for a, b in zip(runs, runs[1:])]
    orders = {}
    for key in adjacent[0]['metrics']:
        errors = [a['metrics'][key]['rms'] for a in adjacent]
        orders[key] = dict(adjacent_rms=errors, decreases=all(y <= x+1e-10 for x,y in zip(errors,errors[1:])),
                           observed_orders=[math.log(x/y, 2) if min(x,y)>1e-10 else None for x,y in zip(errors, errors[1:])])
    return dict(adjacent=adjacent, against_finest=[dict(dt_ms=a['dt_ms'], metrics=metrics(a['samples'],runs[-1]['samples'])) for a in runs[:-1]],
                trends=orders, interpretation='Differences, not exact errors. Observed orders are diagnostics; no Richardson/global bound near switching events.')


def analytic_exchange():
    """Exact two-body-compartment exchange with all external transfers disabled."""
    config = physical.patient_configuration(configuration('hd', 100))
    config['concentration_mmol_L'][1][0] = 10.0
    config['generation_mmol_min'] = [0.0]*6
    config['hemodynamics']['refill_mL_min'] = 0
    v1, v2 = config['volume_mL']
    mean = (v1*20+v2*10)/(v1+v2)
    rate = config['exchange_mL_min'][0]*(1/v1+1/v2)
    cases = []
    for dt in STEPS:
        patient = Compartments(config, True, True)
        ec = config['extracorporeal']
        maximum = residual = 0.0
        for n, elapsed in enumerate(range(0, DURATION, dt)):
            request = dict(sequence=n, time_ms=elapsed, dt_ms=dt, draw_mL=0, return_mL=0,
                uf_mL=0, stored_mL=0, clearance_mL_min=[0]*6, sieving=[1]*6,
                dialysate_mmol_L=[0]*6, pre_mL=0, post_mL=0, substitution_mmol_L=[0]*6,
                flush_in_mL=0, flush_out_mL=0, flush_mmol_L=[0]*6, rinseback=False,
                distributed=dict(volumes_mL=ec['volumes_mL'], filtration_mL=[0]*12,
                dialysate_mL_min=0, dialysate_storage_mL=0, dialysate_drain_mL_min=0, membrane_open=False))
            snapshot = patient.advance(request)
            exact = mean+(20-mean)*math.exp(-rate*(elapsed+dt)/60000)
            maximum = max(maximum, abs(snapshot['concentration_mmol_L'][0][0]-exact))
            residual = max(residual, *map(abs,snapshot['mass_residual_mmol']))
        cases.append(dict(dt_ms=dt, maximum_error_mmol_L=maximum,
                          final_mmol_L=snapshot['concentration_mmol_L'][0][0], exact_final_mmol_L=exact,
                          maximum_mass_residual_mmol=residual))
    return dict(scope='Actual distributed patient integrator, isolated body exchange; analytic continuous-time oracle.', cases=cases)


def kernel_mesh():
    """Countercurrent steady exchanger; fixed total KoA and two boundary values.

    Independent continuum oracle from two constant-coefficient ODEs. Uses actual
    production advection/linear-solve kernels; does NOT remesh the coupled plant.
    """
    qb, qd, koa, inlet = 300., 500., 300., 20.
    exponent = math.exp(koa*(1/qd-1/qb))
    clearance = (1-exponent)/(1/qb-exponent/qd)
    exact = inlet*(1-clearance/qb)
    cases = []
    for n in (6, 12, 24, 48, 96):
        a = [[0.0]*(2*n) for _ in range(2*n)]; rhs = [0.0]*(2*n)
        for j in range(n):
            k = koa/n
            a[j][j] = qb+k; a[j][n+j] = -k
            if j: a[j][j-1] = -qb
            else: rhs[j] = qb*inlet
            a[n+j][n+j] = k; a[n+j][j] = -k
        for j in range(1,n): advect_face(a,n+j-1,n+j,qd)
        a[n][n] += qd
        c = solve(a,rhs)
        cases.append(dict(cells=n, blood_out_mmol_L=c[n-1], exact_mmol_L=exact,
                          absolute_error_mmol_L=abs(c[n-1]-exact),
                          mass_residual_mmol_min=abs(qb*(inlet-c[n-1])-qd*c[n])/1000))
    return dict(scope='Isolated steady donor-cell exchanger; no UF, patient feedback, or hydraulic spatial refinement.', cases=cases)


def identity():
    paths = [p for folder in ('src', 'python/dialysislab') for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.cpp','.hpp')]
    paths += [ROOT/p for p in ('tools/numerical_campaign.py','tools/flow_refinement.py','tests/audit_fixture.py','tests/guided_plant.cpp','tests/test_numerical_campaign.py')]
    paths += [ROOT/'scenarios'/('physical_'+mode+'.json') for mode in MODES]
    return dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                working_tree_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
                python=sys.version, platform=platform.platform(),
                compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
                compile_flags='-std=c++17 -O2 -Wall -Wextra -Werror -DDIALYSISLAB_NUMERICAL_STIMULI')


def campaign(report, traces):
    with tempfile.TemporaryDirectory() as directory:
        binary = compile_bench(directory)
        report['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        for mode in MODES:
            c = configuration(mode, 100)
            c['treatment']['replacement_mL_min'] = 0 if mode == 'hd' else 40
            f = connected(binary, c)
            try:
                for _ in range(40): f.step()
                f.save(0)
                report['configurations'][mode] = c
                def execute(dt, scenario, parameter=None, factor=1.0):
                    f.restore(0)
                    # Sum objects carry compensated accumulators; encode all state explicitly.
                    key = '%s/%s/%s/%s/%s' % (mode, scenario, dt, parameter or 'nominal', factor)
                    report['active_run'] = key
                    traces[key] = []
                    try:
                        result = run(f, dt, scenario, parameter, factor, traces[key])
                    except BaseException:
                        report['failed_run_last_accepted_time_ms'] = f.time
                        report['failed_run_last_record'] = f.record
                        raise
                    result['trace_id'] = key
                    return result
                for scenario in ('concentration', 'uf', 'combined'):
                    print(mode, scenario, flush=True)
                    runs = [execute(dt, scenario) for dt in STEPS]
                    entry = dict(mode=mode, scenario=scenario, runs=runs, comparison=comparisons(runs))
                    report['coupled'].append(entry)
                    if scenario == 'combined':
                        nominal = {r['dt_ms']:r for r in runs}
                        repeat = execute(25, scenario)
                        report['repeatability'].append(dict(mode=mode, dt_ms=25, expected=nominal[25]['trajectory_sha256'], actual=repeat['trajectory_sha256'], identical=repeat['trajectory_sha256']==nominal[25]['trajectory_sha256']))
                        for parameter in ('koa','refill','pump_tau'):
                            variants = {}
                            for dt in (50,25):
                                variants[dt] = [execute(dt, scenario, parameter, factor) for factor in (.9,1.1)]
                            response = {}
                            for dt, pair in variants.items():
                                response[dt] = [dict(time_ms=x['time_ms'], values={k:[(v-u)/.2 for u,v in zip(x['values'][k],y['values'][k])] for k in x['values']}) for x,y in zip(pair[0]['samples'],pair[1]['samples'])]
                            # dY/d(relative parameter), and its dt sensitivity; not physical uncertainty.
                            response_difference = metrics(response[50],response[25])
                            resolution = {k: dict(response_peak=v['reference_scale'], refinement_difference=v['maximum_absolute'],
                                relative_difference=v['maximum_absolute']/v['reference_scale'] if v['reference_scale']>1e-8 else None,
                                proposed_resolved=v['reference_scale']>1e-8 and v['maximum_absolute']<=.1*v['reference_scale'])
                                for k,v in response_difference.items()}
                            report['sensitivity'].append(dict(mode=mode, parameter=parameter, factors=[.9,1.1],
                                runs=[r for pair in variants.values() for r in pair],
                                response_at_25ms=response[25], discretization_of_response=response_difference, proposed_response_resolution=resolution,
                                effect_at_25ms=metrics(variants[25][0]['samples'],variants[25][1]['samples'])))
                # Remove bulky samples from report after every comparison uses them.
                for entry in report['coupled']:
                    for r in entry['runs']: r.pop('samples',None)
                for entry in report['sensitivity']:
                    for r in entry['runs']: r.pop('samples',None)
            finally:
                f.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=int, default=600)
    args = parser.parse_args()
    if args.timeout_seconds < 1: parser.error('timeout must be positive')
    trace_path = args.output.with_suffix('.trajectories.json')
    if args.output.exists() or trace_path.exists(): parser.error('use fresh output paths; existing evidence is immutable')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(schema_version=1, executed_at=datetime.now(timezone.utc).isoformat(), identity=identity(),
                  execution_complete=False, acceptance='proposed criteria; CLOSE-NUM-01 remains open',
                  steps_ms=STEPS, observation_window_ms=WINDOW, duration_ms=DURATION,
                  events_ms=[2400,6400,8800], checkpoint='100 ms preparation plus 40 treatment steps; full C++ Plant and Python patient restored for every run',
                  proposed_absolute_floors=FLOORS, proposed_relative_budget=.005,
                  configurations={}, coupled=[], sensitivity=[], repeatability=[], timeout_seconds=args.timeout_seconds)
    traces = {}; started = time.monotonic()
    def interrupted(signum, frame):
        raise TimeoutError('campaign timeout/interruption signal %d' % signum)
    old_alarm = signal.signal(signal.SIGALRM, interrupted)
    old_term = signal.signal(signal.SIGTERM, interrupted)
    signal.alarm(args.timeout_seconds)
    try:
        report['kernel_mesh'] = kernel_mesh()
        report['analytic_exchange'] = analytic_exchange()
        campaign(report,traces)
        if not all(r['identical'] for r in report['repeatability']): raise ValueError('repeatability regression')
        report.pop('active_run', None)
        report['execution_complete'] = True
    except BaseException as error:
        report['error'] = type(error).__name__+': '+str(error)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_alarm)
        signal.signal(signal.SIGTERM, old_term)
        report['wall_seconds'] = time.monotonic()-started
        payload = json.dumps(traces, separators=(',',':'), allow_nan=False).encode()
        trace_path.write_bytes(payload)
        report['trajectory_artifact'] = dict(file=trace_path.name, sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(), traces=len(traces))
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(execution_complete=True, traces=len(traces), wall_seconds=report['wall_seconds'])))


if __name__ == '__main__':
    main()
