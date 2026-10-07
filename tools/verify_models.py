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
from dialysislab.runner import LocalCluster, simulate, build_identity, canonical, digest, validate
from dialysislab.trajectory import scan, read_records
from verify_compose import collect_case, ComposeRunFailure


def verify(directory, expected_config, expected_sources):
    manifest = json.loads((directory / 'manifest.json').read_text())
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
            p, c = record['patient'], record['circuit']
            elapsed = record['time_ms'] / 60000
            incoming = elapsed * patient_config['external_in_mL_min']
            outgoing = elapsed * patient_config['external_out_mL_min']
            error = abs(config['patient_volume_mL'] + incoming - outgoing - record['patient_volume_mL'] - storage - record['removed_total_mL'])
            for i in range(6):
                concentration = p['concentration_mmol_L'][2][i]
                integrated_diffusion[i] += c['clearance_mL_min'][i] * config['dt_ms'] / 60000 * (concentration - config['transport']['dialysate_mmol_L'][i]) / 1000
                integrated_convection[i] += c['uf_tick_mL'] * config['circuit']['profile']['sieving'][i] * concentration / 1000
                inputs = incoming * patient_config['external_mmol_L'][i] / 1000 + elapsed * patient_config['generation_mmol_min'][i]
                residual = abs(math.fsum(row[i] for row in p['mass_mmol']) + integrated_diffusion[i] + integrated_convection[i]
                               + p['output_mmol'][i] - inputs - initial_mass[i])
                maximum_mass_error = max(maximum_mass_error, residual)
                if residual > 1e-6:
                    raise ValueError('independent solute conservation: ' + str(residual))
        maximum_error = max(maximum_error, error)
        if record['latched'] and first_latch_ms is None:
            first_latch_ms = record['time_ms']
        if record['latched'] and (record['blood_mL_min'] != 0 or record['uf_mL_min'] != 0):
            raise ValueError('active output despite protective latch')
        if error > 1e-6:
            raise ValueError('water conservation: ' + str(error))
    return dict(manifest=manifest, scan=summary, maximum_water_error_mL=maximum_error,
                expected_water_error_mL=1e-6, first_latch_ms=first_latch_ms,
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
                if args.compose:
                    collected = collect_case(name, repeat, args.output, timeout=900)
                    if collected['compose_exit_code'] or collected['collection_errors'] or collected['cleanup_errors']:
                        raise ComposeRunFailure(collected)
                    directory = Path(collected['directory']) / 'results/run'
                else:
                    directory = args.output / (name + '-' + str(repeat))
                    with LocalCluster(args.build_dir) as cluster:
                        simulate(config, cluster.runtime, args.build_dir, directory)
                    collected = None
                case = verify(directory, config, expected_sources)
                if name == 'circuit_occlusion' and not (case['first_latch_ms'] is not None and 2000 <= case['first_latch_ms'] <= 3000):
                    raise ValueError('circuit occlusion did not trip within the declared 1000 ms bound')
                case.update(scenario=name, repeat=repeat, collection=collected,
                            directory=str(directory))
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
