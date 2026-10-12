"""RSS probe in a fresh process; generates full-size synthetic M1 records."""
import hashlib
import json
from pathlib import Path
import resource
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from dialysislab.trajectory import TrajectoryWriter, scan


def rss_sample():
    # Linux getrusage can retain the spawning parent's pre-exec high-water mark.
    # VmHWM belongs to this executable's address space; retain both counters.
    fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines() if ':' in line}
    peak,unit=fields['VmHWM'].split()
    assert unit=='kB'
    return dict(peak_rss_bytes=int(peak)*1024,metric='Linux /proc/self/status VmHWM',
                getrusage_high_water_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)


def main():
    directory = Path(sys.argv[1])
    reports = []
    for repetition in range(2):
        writer = TrajectoryWriter(directory / str(repetition))
        try:
            for n in range(100000):
                observation = dict(sequence=n, time_ms=n*100, valid=1,
                                   blood_mL_min=300.0, pressure_mmHg=150.0, uf_mL_min=10.0)
                record = dict(sequence=n, time_ms=(n+1)*100, blood_mL_min=300.0,
                              pressure_mmHg=150.0, uf_mL_min=10.0, removed_total_mL=(n+1)/60,
                              removed_tick_mL=1/60, latched=False, clamp_closed=False,
                              reason='none', patient_volume_mL=40000-(n+1)/60,
                              patient_removed_mL=(n+1)/60, protection_decision='none',
                              observations=dict(control=observation, protection=observation))
                writer.append(record)
        finally:
            writer.close()
        checked = scan(writer.trajectory.path)
        independent = hashlib.sha256()
        with writer.trajectory.path.open('rb') as stream:
            for block in iter(lambda: stream.read(262144), b''):
                independent.update(block)
        assert checked['records'] == 100000
        assert checked['sha256'] == independent.hexdigest() == writer.hasher.hexdigest()
        reports.append(dict(records=checked['records'], bytes=checked['complete_bytes'],
                            sha256=checked['sha256'], first_sequence=checked['first']['sequence'],
                            last_sequence=checked['last']['sequence']))
    memory=rss_sample()
    assert memory['peak_rss_bytes'] <= 64 * 1024**2, memory
    assert reports[0]['sha256'] == reports[1]['sha256']
    print(json.dumps(dict(**memory, rss_budget_bytes=64*1024**2,
                          compose_limit_bytes=128*1024**2, runs=reports)))


if __name__ == '__main__':
    main()
