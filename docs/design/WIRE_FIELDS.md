# Fixed-field DL1 dictionary

Document ID ICD-02; generated from [wire-contract.json](../wire-contract.json).

Read the [wire protocol](WIRE_PROTOCOL.md) for framing, authorization, ordering,
composite payloads, patient JSON and experiment operations. Positions below start
at 1 **after the tag**; neither DL1 nor the tag is counted. Bounds are inclusive
parser limits, not clinical limits. A dash means a token or additional semantic rule.
Real values must be finite. C++ is the bound reference unless a note says otherwise.
This inventory does not claim every legacy protocol version is fully specified.

## physical-request — PHYSICAL9

**Endpoint:** `admin/plant.sock`; request; 22 fields.

**Conditions:** Administrator only, configured circuit/online fluid, before first PREPARE and before MACHINE5; once per fresh process. Initial Hct < maximum filter Hct; replaces legacy graph geometry.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `arterial_diameter_mm` | real | mm | 0.5 … 3 |
| 2 | `arterial_length_mm` | real | mm | 5 … 100 |
| 3 | `venous_diameter_mm` | real | mm | 0.5 … 3 |
| 4 | `venous_length_mm` | real | mm | 5 … 100 |
| 5 | `tube_diameter_mm` | real | mm | 2 … 8 |
| 6 | `arterial_tube_mm` | real | mm | 50 … 3000 |
| 7 | `venous_tube_mm` | real | mm | 50 … 3000 |
| 8 | `arterial_chamber_mL` | real | mL | 1 … 100 |
| 9 | `venous_chamber_mL` | real | mL | 1 … 100 |
| 10 | `filter_mL` | real | mL | 1 … 250 |
| 11 | `filter_R` | real | mmHg min/mL | 0.01 … 2 |
| 12 | `kuf_mL_min_mmHg` | real | mL/min/mmHg | 0.01 … 2 |
| 13 | `max_filter_hct` | real | 1 | 0.4 … 0.7 |
| 14 | `max_plasma_filtration_fraction` | real | 1 | 0.05 … 0.6 |
| 15 | `dialysate_min_mmHg` | real | mmHg | -500 … 0 |
| 16 | `dialysate_max_mmHg` | real | mmHg | 0 … 500 |
| 17 | `dialysate_R` | real | mmHg min/mL | 0.001 … 1 |
| 18 | `access_mmHg` | real | mmHg | 0 … 100 |
| 19 | `pump_head_mmHg` | real | mmHg | 100 … 600 |
| 20 | `initial_hematocrit` | real | 1 | 0.1 … 0.6 |
| 21 | `protein_g_dL` | real | g/dL | 1 … 15 |
| 22 | `temperature_C` | real | degC | 30 … 42 |

## fluid-request — FLUID9

**Endpoint:** `admin/plant.sock`; request; 21 fields.

**Conditions:** Administrator only, configured circuit/online fluid, before first PREPARE and before MACHINE5; once per fresh process. Requires physical blood; acid_fraction + bicarbonate_fraction < 1.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `acid_mL` | real | mL | 0 … 20000 |
| 2 | `bicarbonate_g` | real | g | 0 … 2000 |
| 3 | `acid_installed` | integer | 1 | 0 … 1 |
| 4 | `bicarbonate_installed` | integer | 1 | 0 … 1 |
| 5 | `acid_fraction` | real | 1 | 0 … 0.1 |
| 6 | `bicarbonate_fraction` | real | 1 | 0 … 0.2 |
| 7 | `bicarbonate_stock_mmol_L` | real | mmol/L | 100 … 1500 |
| 8 | `dissolution_g_min` | real | g/min | 0 … 100 |
| 9 | `heater_max_W` | real | W | 0 … 5000 |
| 10 | `heater_capacity_J_K` | real | J/K | 1 … 10000 |
| 11 | `heater_loss_W_K` | real | W/K | 0 … 100 |
| 12 | `ambient_C` | real | degC | 0 … 50 |
| 13 | `heater_gain_W_K` | real | W/K | 0 … 5000 |
| 14 | `conductivity_factor` | real | 1 | 0.1 … 1 |
| 15 | `temperature_coefficient` | real | 1/K | 0.001 … 0.03 |
| 16 | `acid_urea` | real | mmol/L | 0 … 10000 |
| 17 | `acid_sodium` | real | mmol/L | 0 … 10000 |
| 18 | `acid_potassium` | real | mmol/L | 0 … 10000 |
| 19 | `acid_chloride` | real | mmol/L | 0 … 10000 |
| 20 | `acid_bicarbonate` | real | mmol/L | 0 … 10000 |
| 21 | `acid_calcium` | real | mmol/L | 0 … 10000 |

## dynamics-request — DYNAMICS10

**Endpoint:** `admin/plant.sock`; request; 11 fields.

**Conditions:** Administrator only, configured circuit/online fluid, before first PREPARE and before MACHINE5; once per fresh process. Requires physical blood; volume + compliance * minimum dialysate pressure > 1 mL.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `arterial_air_mL` | real | mL | 5 … 100 |
| 2 | `venous_air_mL` | real | mL | 5 … 100 |
| 3 | `level_gain_mL_s_mL` | real | 1/s | 0 … 10 |
| 4 | `gas_max_mL_s` | real | mL/s | 0 … 10 |
| 5 | `dialysate_compliance_mL_mmHg` | real | mL/mmHg | 0.01 … 1 |
| 6 | `pump_tau_s` | real | s | 0.05 … 5 |
| 7 | `sensor_tau_s` | real | s | 0.01 … 5 |
| 8 | `pressure_gain_mL_min_mmHg` | real | mL/min/mmHg | 0.1 … 20 |
| 9 | `uf_pump_max_mL_min` | real | mL/min | 20 … 200 |
| 10 | `balance_chamber_mL` | real | mL | 5 … 100 |
| 11 | `dialysate_volume_mL` | real | mL | 50 … 1000 |

## blood-update — BLOOD9

**Endpoint:** `admin/plant.sock`; request; 7 fields.

**Conditions:** Between ticks; sequence/time equal next expected; not halted; physical model enabled.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `hematocrit` | real | 1 | 0.01 … 0.7 |
| 4 | `protein_g_dL` | real | g/dL | 0.1 … 30 |
| 5 | `temperature_C` | real | degC | 30 … 42 |
| 6 | `circuit_hematocrit` | real | 1 | 0 … 0.8 |
| 7 | `circuit_protein_g_dL` | real | g/dL | 0 … 40 |

## inventory-update — INVENTORY10

**Endpoint:** `admin/plant.sock`; request; 26 fields.

**Conditions:** Same next-tick clock; dynamic model enabled; validate entire input before replacing retained properties.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `segment_1_hematocrit` | real | 1 | 0 … 0.8 |
| 4 | `segment_1_protein_g_dL` | real | g/dL | 0 … 40 |
| 5 | `segment_2_hematocrit` | real | 1 | 0 … 0.8 |
| 6 | `segment_2_protein_g_dL` | real | g/dL | 0 … 40 |
| 7 | `segment_3_hematocrit` | real | 1 | 0 … 0.8 |
| 8 | `segment_3_protein_g_dL` | real | g/dL | 0 … 40 |
| 9 | `segment_4_hematocrit` | real | 1 | 0 … 0.8 |
| 10 | `segment_4_protein_g_dL` | real | g/dL | 0 … 40 |
| 11 | `segment_5_hematocrit` | real | 1 | 0 … 0.8 |
| 12 | `segment_5_protein_g_dL` | real | g/dL | 0 … 40 |
| 13 | `segment_6_hematocrit` | real | 1 | 0 … 0.8 |
| 14 | `segment_6_protein_g_dL` | real | g/dL | 0 … 40 |
| 15 | `segment_7_hematocrit` | real | 1 | 0 … 0.8 |
| 16 | `segment_7_protein_g_dL` | real | g/dL | 0 … 40 |
| 17 | `segment_8_hematocrit` | real | 1 | 0 … 0.8 |
| 18 | `segment_8_protein_g_dL` | real | g/dL | 0 … 40 |
| 19 | `segment_9_hematocrit` | real | 1 | 0 … 0.8 |
| 20 | `segment_9_protein_g_dL` | real | g/dL | 0 … 40 |
| 21 | `segment_10_hematocrit` | real | 1 | 0 … 0.8 |
| 22 | `segment_10_protein_g_dL` | real | g/dL | 0 … 40 |
| 23 | `segment_11_hematocrit` | real | 1 | 0 … 0.8 |
| 24 | `segment_11_protein_g_dL` | real | g/dL | 0 … 40 |
| 25 | `segment_12_hematocrit` | real | 1 | 0 … 0.8 |
| 26 | `segment_12_protein_g_dL` | real | g/dL | 0 … 40 |

## machine-request — MACHINE5

**Endpoint:** `admin/plant.sock`; request; 5 fields.

**Conditions:** After ONLINE4, before arming; one-time. Blood + replacement <=500; HD replacement zero. Mode comes from ONLINE4.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `blood` | real | mL/min | 0 … 500 |
| 2 | `net_uf` | real | mL/min | 0 … 20 |
| 3 | `replacement` | real | mL/min | 0 … 120 |
| 4 | `pressure_limit` | real | mmHg | 1 … 1000 |
| 5 | `prime` | real | mL | 10 … 1000 |

## guided-request — GUIDED8

**Endpoint:** `admin/plant.sock`; request; 4 fields.

**Conditions:** After MACHINE5, before arming, once; sensor node is dialyzer inlet; enters self_test.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `test_ms` | integer | ms | 1 … 600000 |
| 2 | `treatment_ms` | integer | ms | 1 … 86400000 |
| 3 | `disinfection_ms` | integer | ms | 1 … 3600000 |
| 4 | `return_mL` | real | mL | 10 … 1000 |

## observation5 — OBS5

**Endpoint:** `control/protection plant replies`; response; 18 fields.

**Conditions:** Frozen role-specific observation; usable only with valid=1 and exact requested sequence/time.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |

## observation8 — OBS8

**Endpoint:** `control/protection plant replies`; response; 20 fields.

**Conditions:** Guided observation; inherited sample validity rules.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |
| 19 | `dialysate_mL_min` | real | mL/min | 0 … 2000 |
| 20 | `tmp_mmHg` | real | mmHg | -1000 … 1000 |

## observation9 — OBS9

**Endpoint:** `control/protection plant replies`; response; 27 fields.

**Conditions:** Physical observation. Numeric domains agree between actual C++ and Python decoders; validity and exact requested clock are additional consumer checks.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |
| 19 | `dialysate_mL_min` | real | mL/min | 0 … 2000 |
| 20 | `tmp_mmHg` | real | mmHg | -1000 … 1000 |
| 21 | `arterial_mmHg` | real | mmHg | -1000 … 1000 |
| 22 | `limitation` | atom | code | — |
| 23 | `dialysate_mmHg` | real | mmHg | -1000 … 1000 |
| 24 | `heater_W` | real | W | 0 … 5000 |
| 25 | `acid_remaining_mL` | real | mL | 0 … 20000 |
| 26 | `bicarbonate_remaining_g` | real | g | 0 … 2000 |
| 27 | `conductivity_raw_mS_cm` | real | mS/cm | 0 … 1000 |

## observation10 — OBS10

**Endpoint:** `control/protection plant replies`; response; 35 fields.

**Conditions:** Dynamic observation. Numeric domains agree between actual C++ and Python decoders. Bypass/phase are bounded real-valued indications in 0..1.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |
| 19 | `dialysate_mL_min` | real | mL/min | 0 … 2000 |
| 20 | `tmp_mmHg` | real | mmHg | -1000 … 1000 |
| 21 | `arterial_mmHg` | real | mmHg | -1000 … 1000 |
| 22 | `limitation` | atom | code | — |
| 23 | `dialysate_mmHg` | real | mmHg | -1000 … 1000 |
| 24 | `heater_W` | real | W | 0 … 5000 |
| 25 | `acid_remaining_mL` | real | mL | 0 … 20000 |
| 26 | `bicarbonate_remaining_g` | real | g | 0 … 2000 |
| 27 | `conductivity_raw_mS_cm` | real | mS/cm | 0 … 1000 |
| 28 | `arterial_level` | real | 1 | 0 … 1 |
| 29 | `venous_level` | real | 1 | 0 … 1 |
| 30 | `dialysate_drain_mL_min` | real | mL/min | 0 … 2000 |
| 31 | `uf_pump_mL_min` | real | mL/min | 0 … 200 |
| 32 | `balance_position_mL` | real | mL | 0 … 100 |
| 33 | `bypass` | real | 1 | 0 … 1 |
| 34 | `balance_capacity_mL` | real | mL | 5 … 100 |
| 35 | `balance_phase` | real | 1 | 0 … 1 |

## machine-state5 — MACHINE5

**Endpoint:** `META5 / VIEW5 / COMMITTED5`; response; 25 fields.

**Conditions:** Legacy state. Integer maxima are parser bounds, not achievable values. C++ and Python metadata decoders use the same numeric domains.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `stage` | integer | enum | 0 … 9 |
| 4 | `mode` | integer | enum | 0 … 2 |
| 5 | `blood` | real | mL/min | 0 … 500 |
| 6 | `net_uf` | real | mL/min | 0 … 20 |
| 7 | `replacement` | real | mL/min | 0 … 120 |
| 8 | `pressure_limit` | real | mmHg | 1 … 1000 |
| 9 | `prime` | real | mL | 10 … 1000 |
| 10 | `mask` | integer | bitmask | 0 … 8191 |
| 11 | `acknowledged` | integer | bitmask | 0 … 8191 |
| 12 | `silence_until` | integer | ms | 0 … 100120000 |
| 13 | `safe` | integer | count | 0 … 3 |
| 14 | `ready` | integer | count | 0 … 3 |
| 15 | `cycles` | integer | count | 0 … 100000000 |
| 16 | `revision` | integer | revision | 0 … 100000000 |
| 17 | `action` | atom | code | — |
| 18 | `terminal` | integer | 1 | 0 … 1 |
| 19 | `phase_flush` | real | mL | 0 … 1000000000.0 |
| 20 | `flush_in` | real | mL | 0 … 1000000000.0 |
| 21 | `flush_out` | real | mL | 0 … 1000000000.0 |
| 22 | `expected_net` | real | mL | -1000000000.0 … 1000000000.0 |
| 23 | `measured_net` | real | mL | -1000000000.0 … 1000000000.0 |
| 24 | `flush_in_tick` | real | mL | 0 … 100000 |
| 25 | `flush_out_tick` | real | mL | 0 … 100000 |

## machine-state8 — MACHINE8

**Endpoint:** `META5 / VIEW5 / COMMITTED5`; response; 39 fields.

**Conditions:** Guided state. Effective stage may differ from tick_stage, which names the integrated phase.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `stage` | integer | enum | 0 … 15 |
| 4 | `mode` | integer | enum | 0 … 2 |
| 5 | `blood` | real | mL/min | 0 … 500 |
| 6 | `net_uf` | real | mL/min | 0 … 20 |
| 7 | `replacement` | real | mL/min | 0 … 120 |
| 8 | `pressure_limit` | real | mmHg | 1 … 1000 |
| 9 | `prime` | real | mL | 10 … 1000 |
| 10 | `mask` | integer | bitmask | 0 … 8191 |
| 11 | `acknowledged` | integer | bitmask | 0 … 8191 |
| 12 | `silence_until` | integer | ms | 0 … 100120000 |
| 13 | `safe` | integer | count | 0 … 3 |
| 14 | `ready` | integer | count | 0 … 3 |
| 15 | `cycles` | integer | count | 0 … 100000000 |
| 16 | `revision` | integer | revision | 0 … 100000000 |
| 17 | `action` | atom | code | — |
| 18 | `terminal` | integer | 1 | 0 … 1 |
| 19 | `phase_flush` | real | mL | 0 … 1000000000.0 |
| 20 | `flush_in` | real | mL | 0 … 1000000000.0 |
| 21 | `flush_out` | real | mL | 0 … 1000000000.0 |
| 22 | `expected_net` | real | mL | -1000000000.0 … 1000000000.0 |
| 23 | `measured_net` | real | mL | -1000000000.0 … 1000000000.0 |
| 24 | `flush_in_tick` | real | mL | 0 … 100000 |
| 25 | `flush_out_tick` | real | mL | 0 … 100000 |
| 26 | `phase_elapsed` | integer | ms | 0 … 100000000 |
| 27 | `treatment_elapsed` | integer | ms | 0 … 100000000 |
| 28 | `duration` | integer | ms | 0 … 100000000 |
| 29 | `test_duration` | integer | ms | 0 … 100000000 |
| 30 | `clean_duration` | integer | ms | 0 … 100000000 |
| 31 | `rinse_target` | real | mL | 10 … 1000 |
| 32 | `rinse_volume` | real | mL | 0 … 1000000000.0 |
| 33 | `resume_stage` | integer | enum | 0 … 15 |
| 34 | `patient_connected` | integer | 1 | 0 … 1 |
| 35 | `return_in_tick` | real | mL | 0 … 100000 |
| 36 | `return_out_tick` | real | mL | 0 … 100000 |
| 37 | `tests_passed` | integer | bitmask | 0 … 127 |
| 38 | `primed` | integer | 1 | 0 … 1 |
| 39 | `tick_stage` | integer | enum | 0 … 15 |

## physical-state — PHYSICS9

**Endpoint:** `COMMITTED5 optional trailer`; response; 80 fields.

**Conditions:** Broad finite diagnostic decoder bounds are not physical validity limits. Per-record verifier checks conservation, pressure and filtration.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `end_ms` | integer | ms | 0 … 100000000 |
| 3 | `arterial_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 4 | `venous_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 5 | `prefilter_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 6 | `postfilter_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 7 | `dialysate_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 8 | `tmp_mmHg` | real | mmHg | -1000000.0 … 1000000.0 |
| 9 | `inlet_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 10 | `outlet_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 11 | `return_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 12 | `plasma_filtration_fraction` | real | 1 | -1000000.0 … 1000000.0 |
| 13 | `acid_remaining_mL` | real | mL | -1000000.0 … 1000000.0 |
| 14 | `bicarbonate_remaining_g` | real | g | -1000000.0 … 1000000.0 |
| 15 | `heater_W` | real | W | -1000000.0 … 1000000.0 |
| 16 | `conductivity_raw_mS_cm` | real | mS/cm | -1000000.0 … 1000000.0 |
| 17 | `arterial_chamber_mL` | real | mL | -1000000.0 … 1000000.0 |
| 18 | `venous_chamber_mL` | real | mL | -1000000.0 … 1000000.0 |
| 19 | `filter_mL` | real | mL | -1000000.0 … 1000000.0 |
| 20 | `limitation` | atom | code | — |
| 21 | `segment_1_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 22 | `segment_1_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 23 | `segment_1_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 24 | `segment_1_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 25 | `segment_1_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 26 | `segment_2_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 27 | `segment_2_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 28 | `segment_2_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 29 | `segment_2_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 30 | `segment_2_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 31 | `segment_3_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 32 | `segment_3_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 33 | `segment_3_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 34 | `segment_3_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 35 | `segment_3_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 36 | `segment_4_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 37 | `segment_4_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 38 | `segment_4_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 39 | `segment_4_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 40 | `segment_4_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 41 | `segment_5_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 42 | `segment_5_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 43 | `segment_5_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 44 | `segment_5_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 45 | `segment_5_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 46 | `segment_6_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 47 | `segment_6_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 48 | `segment_6_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 49 | `segment_6_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 50 | `segment_6_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 51 | `segment_7_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 52 | `segment_7_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 53 | `segment_7_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 54 | `segment_7_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 55 | `segment_7_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 56 | `segment_8_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 57 | `segment_8_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 58 | `segment_8_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 59 | `segment_8_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 60 | `segment_8_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 61 | `segment_9_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 62 | `segment_9_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 63 | `segment_9_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 64 | `segment_9_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 65 | `segment_9_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 66 | `segment_10_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 67 | `segment_10_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 68 | `segment_10_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 69 | `segment_10_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 70 | `segment_10_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 71 | `segment_11_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 72 | `segment_11_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 73 | `segment_11_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 74 | `segment_11_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 75 | `segment_11_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |
| 76 | `segment_12_hematocrit` | real | 1 | -1000000.0 … 1000000.0 |
| 77 | `segment_12_viscosity` | real | mPa s | -1000000.0 … 1000000.0 |
| 78 | `segment_12_blood_pressure` | real | mmHg | -1000000.0 … 1000000.0 |
| 79 | `segment_12_uf` | real | mL/min | -1000000.0 … 1000000.0 |
| 80 | `segment_12_oncotic` | real | mmHg | -1000000.0 … 1000000.0 |

## dynamics-state — DYNAMICS10

**Endpoint:** `PHYSICS9 optional trailer`; response; 15 fields.

**Conditions:** 15 fields; distinct from the 11-field administrator request with the same tag. Parser validates finite diagnostics; physical verifier checks actual constraints.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `arterial_volume_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 2 | `venous_volume_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 3 | `arterial_level` | real | 1 | -1000000000.0 … 1000000000.0 |
| 4 | `venous_level` | real | 1 | -1000000000.0 … 1000000000.0 |
| 5 | `arterial_gas_mL_s` | real | mL/s | -1000000000.0 … 1000000000.0 |
| 6 | `venous_gas_mL_s` | real | mL/s | -1000000000.0 … 1000000000.0 |
| 7 | `feed_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 8 | `drain_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 9 | `uf_pump_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 10 | `sensed_dialysate_mmHg` | real | mmHg | -1000000000.0 … 1000000000.0 |
| 11 | `dialysate_storage_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 12 | `dialysate_residual_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 13 | `balance_position_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 14 | `balance_cycles` | real | count | -1000000000.0 … 1000000000.0 |
| 15 | `bypass` | real | 1 | -1000000000.0 … 1000000000.0 |

## prescription — PRESCRIBE5

**Endpoint:** `device/control.sock`; request; 4 fields.

**Conditions:** Sum <=500; HD replacement=0; HDF >=2. Server phase guards apply when intent is applied.

**Response / interpretation:** CONFIRM5 id

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `mode` | integer | enum | 0 … 2 |
| 2 | `blood` | real | mL/min | 0 … 500 |
| 3 | `net_uf` | real | mL/min | 0 … 20 |
| 4 | `replacement` | real | mL/min | 0 … 120 |

## request — REQUEST5

**Endpoint:** `device/control.sock or device/protection.sock`; request; 1 fields.

**Conditions:** Control actions PRIME CONFIGURE START PAUSE RECOVER FINISH CLEAN COMPLETE CONNECT RETURN DISCONNECT RESUME. Protection allows RESET only.

**Response / interpretation:** CONFIRM5 id

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `action` | atom | code | — |

## confirm — CONFIRM5

**Endpoint:** `device producer endpoint`; request; 1 fields.

**Conditions:** Exact pending ID; not queued or expired; one pending intent; 10 s wall expiration.

**Response / interpretation:** QUEUED5 id

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `id` | integer | token | 0 … 100000000 |

## silence — SILENCE5

**Endpoint:** `device/protection.sock`; request; 1 fields.

**Conditions:** Annotates alarm until virtual deadline; does not release restrictions.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `duration` | integer | ms | 0 … 120000 |

## ack5 — ACK5

**Endpoint:** `device producer endpoint`; request; 0 fields.

**Conditions:** Protection only; acknowledge current mask.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |

## stop5 — STOP5

**Endpoint:** `device producer endpoint`; request; 0 fields.

**Conditions:** Control only; immediate stop, cancels pending intent.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |

## status5 — STATUS5

**Endpoint:** `device producer endpoint`; request; 0 fields.

**Conditions:** Both producers; current state plus own sample and intent.

**Response / interpretation:** VIEW5 MACHINE5|MACHINE8 OBS5|OBS8|OBS9|OBS10 INTENT5

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |

## hello6 — HELLO6

**Endpoint:** `device producer endpoint`; request; 0 fields.

**Conditions:** Both producers; returns fresh process epoch.

**Response / interpretation:** SESSION6 epoch

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |

## step5 — STEP5

**Endpoint:** `decision service`; request; 2 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK (control) / DECISION mask (protection)

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |

## sense5 — SENSE5

**Endpoint:** `role/plant.sock`; request; 2 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OBS5|OBS8|OBS9|OBS10

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |

## commit5 — COMMIT5

**Endpoint:** `admin/plant.sock`; request; 2 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** COMMITTED5 STATE4 CIRCUIT3 ONLINE4 MACHINE5|MACHINE8 [PHYSICS9 [DYNAMICS10]]

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |

## demand5 — DEMAND5

**Endpoint:** `control/plant.sock`; request; 5 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `blood` | real | mL/min | 0 … 500 |
| 4 | `gross_uf` | real | mL/min | 0 … 140 |
| 5 | `replacement` | real | mL/min | 0 … 120 |

## protect5 — PROTECT5

**Endpoint:** `protection/plant.sock`; request; 4 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `mask` | integer | bitmask | 0 … 8191 |
| 4 | `valid` | integer | 1 | 0 … 1 |

## reset5 — RESET5

**Endpoint:** `protection/plant.sock`; request; 2 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK / REJECT reason

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |

## change5 — CHANGE5

**Endpoint:** `control/plant.sock`; request; 3 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK / REJECT reason

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `action` | atom | code | — |

## rx5 — RX5

**Endpoint:** `control/plant.sock`; request; 6 fields.

**Conditions:** Exact current prepared sequence/time; role/state/single-decision guards apply. STEP5 belongs to service, not plant. RESET5 after protection decision; CHANGE5/RX5 before both decisions.

**Response / interpretation:** OK / REJECT reason

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 100000 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `mode` | integer | enum | 0 … 2 |
| 4 | `blood` | real | mL/min | 0 … 500 |
| 5 | `net_uf` | real | mL/min | 0 … 20 |
| 6 | `replacement` | real | mL/min | 0 … 120 |

## prepare — PREPARE

**Endpoint:** `admin/plant.sock`; request; 6 fields.

**Conditions:** One tick in flight, contiguous sequence/time; fault enum none invalid missing stale future replay. Resistance pertains to legacy model.

**Response / interpretation:** OK

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `start_ms` | integer | ms | 0 … 100000000 |
| 3 | `dt_ms` | integer | ms | 1 … 1000 |
| 4 | `resistance` | real | mmHg min/mL | 0.01 … 100 |
| 5 | `control_fault` | atom | code | — |
| 6 | `protection_fault` | atom | code | — |

## preparation-request — PREPARATION11

**Endpoint:** `admin/plant.sock`; request; 9 fields.

**Conditions:** Configured physical+dynamic model, before MACHINE5/arming; target <= capacity-10; nonzero nominal source contributions.

**Response / interpretation:** OK; atomically initializes dry cartridge and water-filled tanks.

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `acid_line_mL` | real | mL | 0.1 … 50 |
| 2 | `bicarbonate_line_mL` | real | mL | 0.1 … 50 |
| 3 | `cartridge_mL` | real | mL | 20 … 500 |
| 4 | `cartridge_target_mL` | real | mL | 10 … 450 |
| 5 | `fill_mL_min` | real | mL/min | 0 … 1000 |
| 6 | `step_s` | real | s | 0.005 … 0.05 |
| 7 | `sensor_latency_s` | real | s | 0 … 0.4 |
| 8 | `dwell_s` | real | s | 0.5 … 30 |
| 9 | `initial_line_occupancy` | integer | code | 0 … 2 |

## preparation-fault — PREPFAULT11

**Endpoint:** `admin/plant.sock`; request; 2 fields.

**Conditions:** Admin only, preparation enabled, outside a prepared transaction. Names: acid_scale, vent_blocked, inlet_blocked, sensor_invalid, sensor_stale; flags must be integers 0/1.

**Response / interpretation:** OK; source truth/sensor fault only, no replacement/reset.

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `name` | atom | atom | — |
| 2 | `value` | real | fraction/flag | 0 … 1 |

## observation11 — OBS11

**Endpoint:** `control/protection plant replies`; response; 37 fields.

**Conditions:** Preparation enabled; OBS10 physical/dynamic fields followed by qualification and latched fault.

**Response / interpretation:** none

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |
| 19 | `dialysate_mL_min` | real | mL/min | 0 … 2000 |
| 20 | `tmp_mmHg` | real | mmHg | -1000 … 1000 |
| 21 | `arterial_mmHg` | real | mmHg | -1000 … 1000 |
| 22 | `limitation` | atom | code | — |
| 23 | `dialysate_mmHg` | real | mmHg | -1000 … 1000 |
| 24 | `heater_W` | real | W | 0 … 5000 |
| 25 | `acid_remaining_mL` | real | mL | 0 … 20000 |
| 26 | `bicarbonate_remaining_g` | real | g | 0 … 2000 |
| 27 | `conductivity_raw_mS_cm` | real | mS/cm | 0 … 1000 |
| 28 | `arterial_level` | real | 1 | 0 … 1 |
| 29 | `venous_level` | real | 1 | 0 … 1 |
| 30 | `dialysate_drain_mL_min` | real | mL/min | 0 … 2000 |
| 31 | `uf_pump_mL_min` | real | mL/min | 0 … 200 |
| 32 | `balance_position_mL` | real | mL | 0 … 100 |
| 33 | `bypass` | real | 1 | 0 … 1 |
| 34 | `balance_capacity_mL` | real | mL | 5 … 100 |
| 35 | `balance_phase` | real | 1 | 0 … 1 |
| 36 | `preparation_ready` | integer | flag | 0 … 1 |
| 37 | `preparation_fault` | integer | flag | 0 … 1 |

## preparation-state — PREPARATION11

**Endpoint:** `plant observations/committed physical state`; response; 31 fields.

**Conditions:** Appended after PHYSICS9/DYNAMICS10 only when preparation enabled; inspector truth, not a controller input.

**Response / interpretation:** Retained source/mixer ledgers and state; qualified volume is a preparation-manifold output, not patient delivery.

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `stage` | real | code | -1000000000.0 … 1000000000.0 |
| 2 | `acid_state` | real | code | -1000000000.0 … 1000000000.0 |
| 3 | `bicarbonate_state` | real | code | -1000000000.0 … 1000000000.0 |
| 4 | `ready` | real | code | -1000000000.0 … 1000000000.0 |
| 5 | `fault` | real | code | -1000000000.0 … 1000000000.0 |
| 6 | `reason` | atom | atom | — |
| 7 | `cartridge_liquid_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 8 | `cartridge_gas_atm_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 9 | `solid_g` | real | g | -1000000000.0 … 1000000000.0 |
| 10 | `dissolved_mmol` | real | mmol | -1000000000.0 … 1000000000.0 |
| 11 | `pressure_mmHg` | real | mmHg | -1000000000.0 … 1000000000.0 |
| 12 | `acid_line_liquid_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 13 | `bicarbonate_line_liquid_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 14 | `acid_command_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 15 | `acid_actual_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 16 | `bicarbonate_command_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 17 | `bicarbonate_actual_mL_min` | real | mL/min | -1000000000.0 … 1000000000.0 |
| 18 | `stable_s` | real | s | -1000000000.0 … 1000000000.0 |
| 19 | `sensor_time_s` | real | s | -1000000000.0 … 1000000000.0 |
| 20 | `source_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 21 | `waste_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 22 | `qualified_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 23 | `water_residual_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 24 | `cartridge_gas_residual_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 25 | `line_gas_residual_mL` | real | mL | -1000000000.0 … 1000000000.0 |
| 26 | `mass_residual_0` | real | mmol | -1000000000.0 … 1000000000.0 |
| 27 | `mass_residual_1` | real | mmol | -1000000000.0 … 1000000000.0 |
| 28 | `mass_residual_2` | real | mmol | -1000000000.0 … 1000000000.0 |
| 29 | `mass_residual_3` | real | mmol | -1000000000.0 … 1000000000.0 |
| 30 | `mass_residual_4` | real | mmol | -1000000000.0 … 1000000000.0 |
| 31 | `mass_residual_5` | real | mmol | -1000000000.0 … 1000000000.0 |

## observation12 — OBS12

**Endpoint:** `control/protection plant replies`; response; 42 fields.

**Conditions:** Guided model with preparation enabled; OBS11 prefix plus modeled drive and sensed liquid telemetry. Previous versions remain accepted.

**Response / interpretation:** Drive is model mL/min equivalent, not RPM. Liquid flows are delayed/filtered outlet observations and are unavailable unless concentrate_valid is 1. Freshness uses the existing preparation 0.5 s guard. This observation adds no actuator authority.

| Position | Field | Type | Unit | Inclusive bounds |
| --- | --- | --- | --- | --- |
| 1 | `sequence` | integer | tick | 0 … 99999 |
| 2 | `time_ms` | integer | ms | 0 … 100000000 |
| 3 | `valid` | integer | 1 | 0 … 1 |
| 4 | `blood_mL_min` | real | mL/min | 0 … 500 |
| 5 | `pressure_mmHg` | real | mmHg | 0 … 1000 |
| 6 | `uf_mL_min` | real | mL/min | 0 … 140 |
| 7 | `temperature_C` | real | degC | 0 … 100 |
| 8 | `conductivity_mS_cm` | real | mS/cm | 0 … 6250 |
| 9 | `replacement_mL_min` | real | mL/min | 0 … 120 |
| 10 | `filter_pressure_mmHg` | real | mmHg | 0 … 24000 |
| 11 | `integrity` | integer | 1 | 0 … 1 |
| 12 | `route` | integer | 1 | 0 … 3 |
| 13 | `downstream_mmHg` | real | mmHg | 0 … 1000 |
| 14 | `air_signal` | real | 1 | 0 … 1 |
| 15 | `leak_signal` | real | 1 | 0 … 1 |
| 16 | `measured_uf_mL` | real | mL | 0 … 1000000000.0 |
| 17 | `measured_substitution_mL` | real | mL | 0 … 1000000000.0 |
| 18 | `supply_ready` | integer | 1 | 0 … 1 |
| 19 | `dialysate_mL_min` | real | mL/min | 0 … 2000 |
| 20 | `tmp_mmHg` | real | mmHg | -1000 … 1000 |
| 21 | `arterial_mmHg` | real | mmHg | -1000 … 1000 |
| 22 | `limitation` | atom | code | — |
| 23 | `dialysate_mmHg` | real | mmHg | -1000 … 1000 |
| 24 | `heater_W` | real | W | 0 … 5000 |
| 25 | `acid_remaining_mL` | real | mL | 0 … 20000 |
| 26 | `bicarbonate_remaining_g` | real | g | 0 … 2000 |
| 27 | `conductivity_raw_mS_cm` | real | mS/cm | 0 … 1000 |
| 28 | `arterial_level` | real | 1 | 0 … 1 |
| 29 | `venous_level` | real | 1 | 0 … 1 |
| 30 | `dialysate_drain_mL_min` | real | mL/min | 0 … 2000 |
| 31 | `uf_pump_mL_min` | real | mL/min | 0 … 200 |
| 32 | `balance_position_mL` | real | mL | 0 … 100 |
| 33 | `bypass` | real | 1 | 0 … 1 |
| 34 | `balance_capacity_mL` | real | mL | 5 … 100 |
| 35 | `balance_phase` | real | 1 | 0 … 1 |
| 36 | `preparation_ready` | integer | flag | 0 … 1 |
| 37 | `preparation_fault` | integer | flag | 0 … 1 |
| 38 | `acid_drive_mL_min` | real | mL/min | 0 … 60 |
| 39 | `bicarbonate_drive_mL_min` | real | mL/min | 0 … 60 |
| 40 | `acid_liquid_mL_min` | real | mL/min | 0 … 60 |
| 41 | `bicarbonate_liquid_mL_min` | real | mL/min | 0 … 60 |
| 42 | `concentrate_valid` | integer | 1 | 0 … 1 |
