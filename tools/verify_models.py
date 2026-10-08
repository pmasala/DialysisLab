#!/usr/bin/env python3
"""Run configured real-process models, scan exact evidence and check water balance."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import LocalCluster, simulate, build_identity, canonical, digest, validate, stop_plant
from dialysislab.trajectory import scan, read_records, strict_json
from dialysislab.compartments import validate_snapshot
from dialysislab.machine import ALARMS, STAGES
from verify_compose import collect_case, ComposeRunFailure


def verify(directory, expected_config, expected_sources):
    manifest = strict_json((directory / 'manifest.json').read_text())
    summary = scan(directory / 'trajectory.jsonl')
    config = manifest['configuration']
    validate(config)
    expected_digest = digest(canonical(expected_config).encode())
    if (canonical(config) != canonical(expected_config) or manifest['configuration_sha256'] != expected_digest):
        raise ValueError('executed configuration does not match requested configuration/digest')
    if manifest['build']['source_sha256'] != expected_sources:
        raise ValueError('executed build sources do not match the expected build; rebuild the image')
    if manifest['outcome'] != 'completed' or summary['records'] != config['ticks']:
        raise ValueError('scenario incomplete')
    if summary['sha256'] != manifest['trajectory_sha256']:
        raise ValueError('trajectory hash mismatch')
    maximum_error = 0
    maximum_mass_error = 0
    integrated_diffusion, integrated_convection = [0.0] * 6, [0.0] * 6
    replacement = 0.0
    replacement_mass = [0.0] * 6
    flush_in = flush_out = 0.0
    flush_input_mass, flush_output_mass = [0.0] * 6, [0.0] * 6
    first_quality_ms = None
    patient_config = config.get('patient')
    initial_mass = None
    if patient_config:
        initial_mass = [math.fsum(patient_config['volume_mL'][j] * patient_config['concentration_mmol_L'][j][i] / 1000
                                 for j in range(2)) + patient_config['prime_mL'] * patient_config['concentration_mmol_L'][0][i] / 1000
                        for i in range(6)]
    first_latch_ms = None
    for record in read_records(directory / 'trajectory.jsonl'):
        storage = record.get('circuit', {}).get('stored_mL', 0)
        error = abs(config['patient_volume_mL'] - record['patient_volume_mL'] - storage - record['removed_total_mL'])
        if patient_config:
            lifecycle = config['schema_version'] >= 5
            p, c = validate_snapshot(record['patient'], config['schema_version'] >= 4, lifecycle), record['circuit']
            online = record.get('online')
            dialysate = config['transport']['dialysate_mmol_L']
            if config['schema_version'] >= 4 and not isinstance(online, dict):
                raise ValueError('missing online evidence')
            if online:
                if online['sequence'] != record['sequence'] or online['time_ms'] != record['time_ms']:
                    raise ValueError('online clock mismatch in evidence')
                volume = online['pre_tick_mL'] + online['post_tick_mL']
                rate = online['replacement_mL_min']
                if not math.isfinite(rate) or not 0 <= rate <= 120 or abs(rate * config['dt_ms'] / 60000 - volume) > 1e-8:
                    raise ValueError('replacement actuator/tick volume mismatch')
                replacement += volume
                dialysate = online['concentration_mmol_L']
                for i in range(6):
                    replacement_mass[i] += volume * dialysate[i] / 1000
                    if abs(replacement_mass[i] - p['substitution_mmol'][i]) > 1e-6:
                        raise ValueError('substitution solute ledger mismatch')
                if abs(replacement - online['substitution_total_mL']) > 1e-6 or abs(replacement - p['substitution_mL']) > 1e-6:
                    raise ValueError('substitution ledger mismatch')
                if online['quality_latched']:
                    first_quality_ms = first_quality_ms if first_quality_ms is not None else record['time_ms']
                    if volume != 0 or rate != 0 or record['uf_mL_min'] != 0 or any(c['clearance_mL_min']):
                        raise ValueError('active fluid output despite quality latch')
                if record['latched'] and rate != 0:
                    raise ValueError('active replacement output despite blood isolation')
            if lifecycle:
                m = record['machine']
                mask = m['alarm_mask']
                if type(mask) is not int or not 0 <= mask <= 8191 or m['stage'] not in STAGES:
                    raise ValueError('machine alarm/state schema')
                blood_blocked = bool(mask & (1 | 2 | 4 | 8 | 16 | 4096)) or m['terminal']
                fluid_blocked = mask != 0 or m['terminal'] or m['stage'] != 'TREATMENT'
                if (record['latched'] != blood_blocked or online['quality_latched'] != bool(mask)
                        or record['clamp_closed'] != (blood_blocked or m['stage'] != 'TREATMENT')
                        or m['alarms'] != [name for i, name in enumerate(ALARMS) if mask & (1 << i)]
                        or (m['terminal'] and (not mask & 4096 or m['stage'] != 'STOPPED'))):
                    raise ValueError('machine mask/constraint fields disagree')
                if fluid_blocked and (record['uf_mL_min'] or record['removed_tick_mL'] or volume or rate or c['uf_mL_min']
                        or c['uf_tick_mL'] or any(c['clearance_mL_min'])
                        or any(c['boundary_diffusion_mmol_min']) or any(c['boundary_convection_mmol_min'])):
                    raise ValueError('active fluid output despite machine constraint')
                pump_blocked = blood_blocked or (m['stage'] in ('PRIMING', 'CLEANING') and mask)
                if pump_blocked and (record['blood_mL_min'] or c['pump_mL_min'] or c['return_mL_min']
                        or c['draw_tick_mL'] or c['return_tick_mL'] or any(c['edge_mL_min'])):
                    raise ValueError('active circulation despite machine constraint')
                if m['sequence'] != record['sequence'] or m['time_ms'] != record['time_ms']:
                    raise ValueError('machine clock mismatch')
                flushing = m['stage'] in ('PRIMING', 'CLEANING')
                fin, fout = (c['draw_tick_mL'], c['return_tick_mL']) if flushing else (0, 0)
                if abs(fin - m['flush_in_tick_mL']) > 1e-8 or abs(fout - m['flush_out_tick_mL']) > 1e-8:
                    raise ValueError('flush path mismatch')
                flush_in += fin; flush_out += fout
                for name, value in [('flush_in_mL', flush_in), ('flush_out_mL', flush_out)]:
                    if abs(value - p[name]) > 1e-6 or abs(value - m[name]) > 1e-6:
                        raise ValueError('flush water ledger mismatch')
                for i in range(6):
                    flush_input_mass[i] += fin * dialysate[i] / 1000
                    flush_output_mass[i] += fout * p['concentration_mmol_L'][2][i] / 1000
                    if abs(flush_input_mass[i] - p['flush_input_mmol'][i]) > 1e-6 or abs(flush_output_mass[i] - p['flush_output_mmol'][i]) > 1e-6:
                        raise ValueError('flush solute ledger mismatch')
                if m['stage'] != 'TREATMENT' and (volume or record['uf_mL_min'] or any(c['clearance_mL_min'])):
                    raise ValueError('patient fluid output outside treatment')
                if m['stage'] not in ('TREATMENT', 'PRIMING', 'CLEANING') and record['blood_mL_min']:
                    raise ValueError('circulation outside active lifecycle state')
            if p['sequence'] != record['sequence'] or p['time_ms'] != record['time_ms']:
                raise ValueError('patient/plant clock mismatch in evidence')
            body = math.fsum(p['volume_mL'][:2])
            if (abs(body - record['patient_volume_mL']) > 1e-8
                    or abs(p['volume_mL'][2] - patient_config['prime_mL'] - storage) > 1e-8):
                raise ValueError('patient compartment/summary volume mismatch')
            elapsed = record['time_ms'] / 60000
            incoming = elapsed * patient_config['external_in_mL_min']
            outgoing = elapsed * patient_config['external_out_mL_min']
            error = abs(config['patient_volume_mL'] + patient_config['prime_mL'] + incoming - outgoing + replacement + flush_in - flush_out
                        - math.fsum(p['volume_mL']) - record['removed_total_mL'])
            for i in range(6):
                concentration = p['concentration_mmol_L'][2][i]
                integrated_diffusion[i] += c['clearance_mL_min'][i] * config['dt_ms'] / 60000 * (concentration - dialysate[i]) / 1000
                integrated_convection[i] += c['uf_tick_mL'] * config['circuit']['profile']['sieving'][i] * concentration / 1000
                inputs = incoming * patient_config['external_mmol_L'][i] / 1000 + elapsed * patient_config['generation_mmol_min'][i]
                residual = abs(math.fsum(row[i] for row in p['mass_mmol']) + integrated_diffusion[i] + integrated_convection[i]
                               + p['output_mmol'][i] - inputs - replacement_mass[i] - initial_mass[i] + flush_output_mass[i] - flush_input_mass[i])
                if not math.isfinite(residual) or residual > 1e-6:
                    raise ValueError('independent solute conservation: ' + str(residual))
                maximum_mass_error = max(maximum_mass_error, residual)
        if record['latched'] and first_latch_ms is None:
            first_latch_ms = record['time_ms']
        if record['latched'] and (record['blood_mL_min'] != 0 or record['uf_mL_min'] != 0):
            raise ValueError('active output despite protective latch')
        if not math.isfinite(error) or error > 1e-6:
            raise ValueError('water conservation: ' + str(error))
        maximum_error = max(maximum_error, error)
    return dict(manifest=manifest, scan=summary, maximum_water_error_mL=maximum_error,
                expected_water_error_mL=1e-6, first_latch_ms=first_latch_ms, first_quality_ms=first_quality_ms,
                maximum_mass_error_mmol=maximum_mass_error if patient_config else None,
                requested_configuration_sha256=expected_digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', nargs='+', default=['circuit_small', 'circuit_large', 'circuit_occlusion'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--build-dir', default='build', type=Path)
    parser.add_argument('--compose', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(executed_at=datetime.now(timezone.utc).isoformat(), command=[sys.executable, *sys.argv],
                  successful=False, cases=[])
    expected_sources = build_identity(args.build_dir)['source_sha256']
    report['expected_source_sha256'] = expected_sources
    try:
        for name in args.scenarios:
            hashes = []
            for repeat in (1, 2):
                config = json.loads((ROOT / 'scenarios' / (name + '.json')).read_text())
                observed_stop = None
                if args.compose:
                    collected = collect_case(name, repeat, args.output, timeout=900)
                    if collected['compose_exit_code'] or collected['collection_errors'] or collected['cleanup_errors']:
                        raise ComposeRunFailure(collected)
                    directory = Path(collected['directory']) / 'results/run'
                else:
                    directory = args.output / (name + '-' + str(repeat))
                    with LocalCluster(args.build_dir) as cluster:
                        simulate(config, cluster.runtime, args.build_dir, directory)
                        if config['schema_version'] >= 4:
                            observed_stop = stop_plant(cluster.runtime / 'admin/plant.sock', online=True)
                            if not observed_stop['acknowledged'] or not observed_stop['outputs_zero_observed']:
                                raise ValueError('treatment stop not confirmed by live observation')
                    collected = None
                case = verify(directory, config, expected_sources)
                if name == 'circuit_occlusion' and not (case['first_latch_ms'] is not None and 2000 <= case['first_latch_ms'] <= 3000):
                    raise ValueError('circuit occlusion did not trip within the declared 1000 ms bound')
                if name in ('treatment_temperature', 'treatment_ratio', 'treatment_supply', 'treatment_integrity', 'treatment_route', 'treatment_filter1'):
                    event_ms = config['faults'][0]['tick'] * config['dt_ms']
                    if case['first_quality_ms'] is None or not event_ms <= case['first_quality_ms'] <= event_ms + 10000 + config['dt_ms']:
                        raise ValueError('quality fixture failed to latch within declared bound')
                case.update(scenario=name, repeat=repeat, collection=collected,
                            directory=str(directory), observed_stop=observed_stop)
                report['cases'].append(case)
                hashes.append(case['scan']['sha256'])
            if hashes[0] != hashes[1]:
                raise ValueError('reproduction failed: ' + name)
        report['successful'] = True
    except Exception as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        (args.output / 'models.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(successful=True, runs=len(report['cases']))))


if __name__ == '__main__':
    main()
