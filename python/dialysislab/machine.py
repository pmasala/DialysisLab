"""Version-5 lifecycle, device-only requests and recorded machine snapshots."""
from . import treatment
from .circuit import keys, number, index
from .protocol import rpc, expect, integer, real, ProtocolError

STAGES = ('PREPARATION', 'PRIMING', 'CONFIGURATION', 'TREATMENT', 'PAUSED', 'STOPPED',
          'RECOVERY', 'FINISHED', 'CLEANING', 'CLEANED')
ALARMS = ('pressure', 'low_flow', 'air', 'blood_leak', 'measurement', 'temperature',
          'composition', 'filter_pressure', 'integrity', 'route', 'supply', 'balance', 'communication')
ACTIONS = ('PRIME', 'CONFIGURE', 'START', 'PAUSE', 'STOP', 'RECOVER', 'FINISH', 'CLEAN',
           'COMPLETE', 'RESET', 'ACK', 'SILENCE', 'PRESCRIBE')
FAULT_RANGES = {'air': (0, 1), 'leak': (0, 1), 'air_stuck': (0, 1), 'leak_stuck': (0, 1),
                'supply_stuck': (0, 1), 'pump_stalled': (0, 1), 'meter_bias': (0, 1000)}


def validate(config, validate_treatment):
    if config.get('model') != 'm5-device-1' or type(config['schema_version']) is not int:
        raise ValueError('device version/model')
    base = {k: v for k, v in config.items() if k != 'workflow'}
    base.update(schema_version=4, model='m4-treatment-1', faults=[])
    validate_treatment(base)
    if not isinstance(config.get('workflow'), list) or len(config['workflow']) > 1000:
        raise ValueError('bounded workflow list')
    previous = -1
    for event in config['workflow']:
        keys(event, 'tick action values')
        index(event['tick'], 0, config['ticks'] - 1)
        if event['tick'] <= previous: raise ValueError('workflow strictly ordered; one event per tick')
        previous = event['tick']
        if event['action'] not in ACTIONS or not isinstance(event['values'], list): raise ValueError('workflow action')
        if event['action'] == 'PRESCRIBE':
            if len(event['values']) != 4: raise ValueError('prescription fields')
            mode, blood, uf, sub = event['values']
            index(mode, 0, 2); number(blood, 0, 500); number(uf, 0, 20); number(sub, 0, 120)
            if blood + sub > 500 or (mode == 0 and sub != 0) or (mode != 0 and sub < 2): raise ValueError('prescription bounds')
        elif event['action'] == 'SILENCE':
            if len(event['values']) != 1: raise ValueError('silence fields')
            index(event['values'][0], 0, 120000)
        elif event['values']: raise ValueError('unexpected workflow values')
    if not isinstance(config['faults'], list) or len(config['faults']) > 1000: raise ValueError('bounded fault list')
    other, seen = [], set()
    for fault in config['faults']:
        keys(fault, 'tick target value'); index(fault['tick'], 0, config['ticks'] - 1)
        target = fault['target']
        if not isinstance(target, str) or (fault['tick'], target) in seen: raise ValueError('duplicate/invalid fault')
        seen.add((fault['tick'], target))
        if target.startswith('device:'):
            name = target[7:]
            if name not in FAULT_RANGES: raise ValueError('device fault name')
            number(fault['value'], *FAULT_RANGES[name])
            if name.endswith('_stuck') or name == 'pump_stalled': index(fault['value'], 0, 1)
        else: other.append(fault)
    base['faults'] = other; validate_treatment(base)
    return config


def configure(admin, config):
    expect(rpc(admin, 'MACHINE5', config['blood_mL_min'], config['uf_mL_min'],
               config['treatment']['replacement_mL_min'], config['pressure_limit_mmHg'],
               config['patient']['prime_mL']), 'OK', 1)


def request(runtime, event):
    """Use the same confirmation contracts as a device; return intent, not completion."""
    action, values = event['action'], event['values']
    role = 'protection' if action in ('ACK', 'SILENCE', 'RESET') else 'control'
    path = runtime / 'device' / (role + '.sock')
    if action in ('STOP', 'ACK', 'SILENCE'):
        expect(rpc(path, action + '5', *values), 'OK', 1)
        return dict(action=action, delivery='acknowledged')
    response = rpc(path, 'PRESCRIBE5', *values) if action == 'PRESCRIBE' else rpc(path, 'REQUEST5', action)
    token = integer(expect(response, 'CONFIRM5', 2)[1])
    expect(rpc(path, 'CONFIRM5', token), 'QUEUED5', 2)
    return dict(action=action, values=values, delivery='queued')


def observation(response):
    expect(response, 'OBS5', 19)
    result = treatment.observation(['OBS4', *response[1:13]])
    for name, value, high in zip(('downstream_mmHg', 'air_signal', 'leak_signal', 'measured_uf_mL', 'measured_substitution_mL'),
                               response[13:18], (1000, 1, 1, 1e9, 1e9)):
        result[name] = real(value, 0, high)
    result['supply_ready'] = integer(response[18], 1)
    return result


def metadata(response):
    expect(response, 'MACHINE5', 26)
    result = dict(sequence=integer(response[1], 99999), time_ms=integer(response[2]),
                  stage=STAGES[integer(response[3], 9)], mode=treatment.MODES[integer(response[4], 2)])
    for name, value, high in zip(('blood_prescribed_mL_min', 'net_uf_prescribed_mL_min', 'replacement_prescribed_mL_min',
                                  'pressure_limit_mmHg', 'prime_mL'), response[5:10], (500, 20, 120, 1000, 1000)):
        result[name] = real(value, 0, high)
    for name, value, high in zip(('alarm_mask', 'acknowledged_mask', 'silence_until_ms', 'safe_cycles', 'ready_cycles',
                                 'treatment_cycles', 'revision'), response[10:17], (8191, 8191, 100120000, 3, 3, 100000, 100000)):
        result[name] = integer(value, high)
    result.update(action=response[17], terminal=bool(integer(response[18], 1)))
    for name, value in zip(('phase_flush_mL', 'flush_in_mL', 'flush_out_mL', 'expected_net_mL', 'measured_net_mL',
                           'flush_in_tick_mL', 'flush_out_tick_mL'), response[19:26]):
        result[name] = real(value, -1e9 if 'net' in name else 0, 1e9)
    result['alarms'] = [name for i, name in enumerate(ALARMS) if result['alarm_mask'] & (1 << i)]
    result['annunciating'] = bool(result['alarm_mask'] & ~result['acknowledged_mask']) and result['time_ms'] >= result['silence_until_ms']
    return result


def committed(response):
    if not response or response[0] != 'COMMITTED5' or 'MACHINE5' not in response: raise ProtocolError('commit5 schema')
    split = response.index('MACHINE5')
    result = treatment.committed(['COMMITTED4', *response[1:split]])
    result['machine'] = metadata(response[split:])
    return result


def view(response):
    expect(response[:1], 'VIEW5', 1)
    if len(response) != 50: raise ProtocolError('device view size')
    result = dict(machine=metadata(response[1:27]), observation=observation(response[27:46]))
    expect(response[46:], 'INTENT5', 4)
    result['intent'] = dict(id=integer(response[47]), state=response[48], result=response[49])
    return result
