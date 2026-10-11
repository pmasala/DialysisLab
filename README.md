# DialysisLab

DialysisLab is an open-source laboratory for experimenting with dialysis software.
It simulates a patient, a dialysis circuit and the software that operates and protects
the machine. It connects only to simulated equipment and patients.

You can run haemodialysis (HD) or haemodiafiltration (HDF), choose a patient and
dialyzer, change treatment settings, inject faults and inspect the results.
HDF supports both predilution and postdilution, including a simplified model of
online substitution-fluid preparation.

There are two separate graphical applications:

- **Machine interface (LVGL):** operate the simulated machine, view measurements and handle alarms.
- **Experiment console (Dear ImGui):** configure patients and scenarios, run experiments and inspect their results.

The machine components are written in C++; the patient and experiment tools use
Python. Control, protection and the machine interface run separately, with Docker
Compose deployments available for Linux and WSL2.

## Run your first simulation

Install a C++17 compiler, CMake 3.16 or newer, make and Python 3.9 or newer.
From the repository root:

```bash
cmake -S . -B build/core -DCMAKE_BUILD_TYPE=Release
cmake --build build/core --parallel 3
PYTHONPATH=python python3 -m dialysislab.runner --local --build-dir build/core --config scenarios/machine_hdf_pre.json --output build/first-run
```

This runs a short, scripted predilution HDF experiment without a graphical display.
It creates `build/first-run/trajectory.jsonl` (one record per simulation step) and
`build/first-run/manifest.json` (configuration, outcome and file hashes).
Use a new output directory for each run.

For a graphical session or Docker deployment, follow the
[Linux and WSL2 running guide](docs/QUICKSTART.md).

## Understand and explore

- [How the simulation works](docs/SIMULATION.md): fluid-path diagrams, pressures, dialyzer exchange and patient weight.
- [Visual inspection](docs/UI_INSPECTION.md): animated circuits, selectable trends and recorded-data inspection.
- [Software architecture](docs/ARCHITECTURE.md): what each process does and how they communicate.
- [Documentation guide](docs/README.md): operating instructions, technical references and development checks.

The models and alarm settings are synthetic and have not been clinically validated.
This is a simulation and development template, not software for treating patients.
The repository includes requirements, risk records and tests; it does not establish
medical-device compliance. See the [evidence and remaining work](assurance/STATUS.md).

[MIT licensed](LICENSE). Third-party dependencies retain their own licences;
see the [dependency policy](DEPENDENCY_POLICY.md).
