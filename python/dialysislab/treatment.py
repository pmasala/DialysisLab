"""Version-4 treatment configuration and admin/observed snapshot contracts."""
from .circuit import keys, number, index, vector, state as circuit_state
from .protocol import expect, rpc, real, integer, ProtocolError, state as physical_state

MODES = ('HD', 'HDF_PRE', 'HDF_POST')
FIELDS = ('mode replacement_mL_min reservoir_mL ratio inlet_temperature_C setpoint_C '
          'heater_min_inverse initial_temperature_C head_mmHg filter1_R filter2_R line_R '
          'penetration1 penetration2 source_contaminant concentrate_mmol_L')
FAULT_RANGES = {'ratio': (0, 1), 'temperature': (0, 90), 'supply': (0, 1),
                'integrity': (0, 1), 'route': (0, 3), 'breach1': (0, 1),
                'breach2': (0, 1), 'contaminant': (0, 1e6), 'filter1': (0.01, 100)}


def validate(config, validate_patient):
    keys(config, 'schema_version model seed ticks dt_ms blood_mL_min uf_mL_min resistance_mmHg_min_mL '
                'pressure_limit_mmHg patient_volume_mL faults circuit transport patient treatment')
    if type(config['schema_version']) is not int or config['schema_version'] != 4 or config['model'] != 'm4-treatment-1':
        raise ValueError('treatment version/model')
    treatment = config['treatment']
    keys(treatment, FIELDS)
    if treatment['mode'] not in MODES: raise ValueError('treatment mode')
    for name, lo, hi in [('replacement_mL_min', 0, 120), ('reservoir_mL', 1, 1000), ('ratio', 0, 1),
                         ('inlet_temperature_C', 0, 90), ('setpoint_C', 0, 90), ('heater_min_inverse', 0, 100),
                         ('initial_temperature_C', 0, 90), ('head_mmHg', 1, 600), ('filter1_R', .01, 100),
                         ('filter2_R', .01, 100), ('line_R', .01, 100), ('penetration1', 0, 1),
                         ('penetration2', 0, 1), ('source_contaminant', 0, 1e6)]:
        number(treatment[name], lo, hi)
    if treatment['mode'] == 'HD' and treatment['replacement_mL_min'] != 0: raise ValueError('HD replacement')
    if treatment['mode'] != 'HD' and treatment['replacement_mL_min'] < 2: raise ValueError('HDF minimum command')
    vector(treatment['concentrate_mmol_L'], 0, 25000)
    if any(c * treatment['ratio'] > 1000 for c in treatment['concentrate_mmol_L']): raise ValueError('mixture range')
    base = {k: v for k, v in config.items() if k != 'treatment'}
    base.update(schema_version=3, model='m3-patient-1', faults=[])
    validate_patient(base)  # Scalar dimensions must be bounded before indexing faults.
    other_faults, seen = [], set()
    if not isinstance(config['faults'], list): raise ValueError('fault list')
    for fault in config['faults']:
        keys(fault, 'tick target value'); index(fault['tick'], 0, config['ticks'] - 1)
        target = fault['target']
        if not isinstance(target, str) or (fault['tick'], target) in seen: raise ValueError('duplicate/invalid fault')
        seen.add((fault['tick'], target))
        if target.startswith('online:'):
            name = target[7:]
            if name not in FAULT_RANGES: raise ValueError('online fault name')
            number(fault['value'], *FAULT_RANGES[name])
            if name in ('supply', 'integrity', 'route', 'breach1', 'breach2'):
                index(fault['value'], 0, 3 if name == 'route' else 1)
            if name == 'ratio' and any(c * fault['value'] > 1000 for c in treatment['concentrate_mmol_L']):
                raise ValueError('fault mixture bounds')
        else: other_faults.append(fault)
    base['faults'] = other_faults
    validate_patient(base)
    if config['blood_mL_min'] + treatment['replacement_mL_min'] > 500:
        raise ValueError('combined circulation outside sensor model range')
    return config


def configure(admin, config):
    t = config['treatment']
    fields = ['ONLINE4', MODES.index(t['mode'])]
    fields.extend(t[k] for k in FIELDS.split()[2:-1])
    fields.extend(t['concentrate_mmol_L'])
    expect(rpc(admin, *fields), 'OK', 1)


def observation(response):
    expect(response, 'OBS4', 13)
    values = dict(sequence=integer(response[1]), time_ms=integer(response[2]), valid=integer(response[3], 1))
    for name, value, lo, hi in zip(('blood_mL_min', 'pressure_mmHg', 'uf_mL_min', 'temperature_C',
                                  'conductivity_mS_cm', 'replacement_mL_min', 'filter_pressure_mmHg'),
                                 response[4:11], (0,) * 7, (500, 1000, 140, 100, 6250, 120, 24000)):
        values[name] = real(value, lo, hi)
    values.update(integrity=integer(response[11], 1), route=integer(response[12], 3))
    return values


def online_state(response):
    expect(response, 'ONLINE4', 24)
    n, t, mode, route = (integer(x) for x in response[1:5])
    if mode > 2 or route > 3: raise ProtocolError('online route')
    result = dict(sequence=n, time_ms=t, mode=MODES[mode], route=route)
    fields = ('temperature_C conductivity_mS_cm replacement_mL_min pre_tick_mL post_tick_mL substitution_total_mL').split()
    for name, value in zip(fields, response[5:11]): result[name] = real(value, 0, 1e9)
    result.update(quality_latched=bool(integer(response[11], 1)), reason=response[12])
    for name, value in zip(('filter1_pressure_mmHg', 'filter2_pressure_mmHg', 'tank_contaminant', 'delivered_contaminant', 'mixing_mL_min'), response[13:18]):
        result[name] = real(value, 0, 1e9)
    result['concentration_mmol_L'] = [real(x, 0, 1000 + 1e-9) for x in response[18:24]]
    return result


def state(response):
    expect(response, 'STATE4', 11)
    # Keep the v1 decoder's strict UF bounds untouched.
    surrogate = list(response); surrogate[0] = 'STATE'; surrogate[5] = surrogate[6] = surrogate[7] = '0'
    result = physical_state(surrogate)
    result['uf_mL_min'] = real(response[5], 0, 140)
    result['removed_total_mL'] = real(response[6], 0, 140 * 100000 / 60 + 1e-6)
    result['removed_tick_mL'] = real(response[7], 0, 140 / 60)
    return result


def committed(response):
    if not response or response[0] != 'COMMITTED4' or 'ONLINE4' not in response: raise ProtocolError('commit4 schema')
    split = response.index('ONLINE4')
    result = state(response[1:12]); result['circuit'] = circuit_state(response[12:split])
    result['online'] = online_state(response[split:])
    return result


def live(response):
    if not response or response[0] != 'LIVE4': raise ProtocolError('live4 schema')
    result = state(response[1:12]); result['online'] = online_state(response[12:])
    return result
