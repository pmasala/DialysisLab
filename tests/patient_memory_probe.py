"""Independent fresh-process 100000-step patient RSS/conservation probe."""
import json
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.compartments import Compartments

config = json.loads((ROOT / 'scenarios/patient_baseline.json').read_text())
patient = Compartments(config['patient'])
for n in range(100000):
    patient.advance(dict(sequence=n, time_ms=n * 10, dt_ms=10, draw_mL=0.05, return_mL=0.05,
                         uf_mL=0, stored_mL=0, clearance_mL_min=[100] * 6,
                         sieving=config['circuit']['profile']['sieving'],
                         dialysate_mmol_L=config['transport']['dialysate_mmol_L']))
snapshot = patient.snapshot()
print(json.dumps(dict(ticks=patient.next_sequence, time_ms=patient.time_ms,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                      maximum_mass_residual_mmol=max(map(abs, snapshot['mass_residual_mmol'])),
                      snapshot=snapshot)))
