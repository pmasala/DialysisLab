"""Version-5 lifecycle, device-only requests and recorded machine snapshots."""
from . import treatment
from .circuit import keys, number, index
from .protocol import rpc, expect, integer, real, ProtocolError

STAGES = ('PREPARATION', 'PRIMING', 'CONFIGURATION', 'TREATMENT', 'PAUSED', 'STOPPED',
          'RECOVERY', 'FINISHED', 'CLEANING', 'CLEANED')
GUIDED_STAGES = STAGES + ('SELF_TEST', 'CONNECTED', 'RETURNING', 'DISCONNECTING', 'DISCONNECTED', 'RECOVERY_READY')
ALARMS = ('pressure', 'low_flow', 'air', 'blood_leak', 'measurement', 'temperature',
          'composition', 'filter_pressure', 'integrity', 'route', 'supply', 'balance', 'communication')
ACTIONS = ('PRIME', 'CONFIGURE', 'START', 'PAUSE', 'STOP', 'RECOVER', 'FINISH', 'CLEAN',
           'COMPLETE', 'RESET', 'ACK', 'SILENCE', 'PRESCRIBE', 'CONNECT', 'RETURN', 'DISCONNECT', 'RESUME')
FAULT_RANGES = {'air': (0, 1), 'leak': (0, 1), 'air_stuck': (0, 1), 'leak_stuck': (0, 1),
                'supply_stuck': (0, 1), 'pump_stalled': (0, 1), 'meter_bias': (0, 1000)}


def validate(config, validate_treatment):
    if config.get('model') != 'm5-device-1' or type(config['schema_version']) is not int:
        raise ValueError('device version/model')
    base = {k: v for k, v in config.items() if k not in ('workflow', 'guided', 'physical')}
    base.update(schema_version=4, model='m4-treatment-1', faults=[])
    validate_treatment(base)
    if 'physical' in config:
        from .physical import validate as validate_physical
        validate_physical(config)
    if 'guided' in config:
        guided=config['guided'];keys(guided,'test_ms treatment_ms disinfection_ms return_mL')
        index(guided['test_ms'],1,600000);index(guided['treatment_ms'],1,86400000)
        index(guided['disinfection_ms'],1,3600000);number(guided['return_mL'],10,1000)
        edge=config['circuit']['edges'][config['circuit']['dialyzer_edge']]
        if config['circuit']['sensor_node']!=edge[0]:raise ValueError('guided arterial sensor must be at dialyzer inlet')
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
        if target.startswith('preparation:'):
            if 'preparation' not in config.get('physical',{}):raise ValueError('preparation fault requires preparation model')
            name=target[len('preparation:'):]
            if name not in ('acid_scale','vent_blocked','inlet_blocked','sensor_invalid','sensor_stale'):raise ValueError('preparation fault name')
            number(fault['value'],0,1)
            if name!='acid_scale':index(fault['value'],0,1)
        elif target.startswith('device:'):
            name = target[7:]
            if name not in FAULT_RANGES: raise ValueError('device fault name')
            number(fault['value'], *FAULT_RANGES[name])
            if name.endswith('_stuck') or name == 'pump_stalled': index(fault['value'], 0, 1)
        else: other.append(fault)
    base['faults'] = other; validate_treatment(base)
    return config


def configure(admin, config):
    if 'physical' in config:
        from . import physical
        physical.configure(admin,config)
    expect(rpc(admin, 'MACHINE5', config['blood_mL_min'], config['uf_mL_min'],
               config['treatment']['replacement_mL_min'], config['pressure_limit_mmHg'],
               config['patient']['prime_mL']), 'OK', 1)
    if 'guided' in config:
        g=config['guided']
        expect(rpc(admin,'GUIDED8',g['test_ms'],g['treatment_ms'],g['disinfection_ms'],g['return_mL']),'OK',1)


def request(runtime, event, scheduled=False):
    """Use the same confirmation contracts as a device; return intent, not completion."""
    action, values = event['action'], event['values']
    role = 'protection' if action in ('ACK', 'SILENCE', 'RESET') else 'control'
    path = runtime / 'device' / (role + '.sock')
    if scheduled: path = runtime / role / 'service.sock'
    def call(*args):
        return rpc(path, *(['OPERATOR7'] if scheduled else []), *args)
    if action in ('STOP', 'ACK', 'SILENCE'):
        expect(call(action + '5', *values), 'OK', 1)
        return dict(action=action, delivery='acknowledged')
    response = call('PRESCRIBE5', *values) if action == 'PRESCRIBE' else call('REQUEST5', action)
    token = integer(expect(response, 'CONFIRM5', 2)[1])
    expect(call('CONFIRM5', token), 'QUEUED5', 2)
    return dict(action=action, values=values, delivery='queued')


def observation(response):
    preparation=response[0]=='OBS11'
    dynamic=response[0] in ('OBS10','OBS11')
    physical=response[0] in ('OBS9','OBS10','OBS11')
    extended=response[0] in ('OBS8','OBS9','OBS10','OBS11')
    expect(response,'OBS11' if preparation else 'OBS10' if dynamic else 'OBS9' if physical else 'OBS8' if extended else 'OBS5',38 if preparation else 36 if dynamic else 28 if physical else 21 if extended else 19)
    result = treatment.observation(['OBS4', *response[1:13]])
    result['sequence'] = integer(response[1], 99999)
    for name, value, high in zip(('downstream_mmHg', 'air_signal', 'leak_signal', 'measured_uf_mL', 'measured_substitution_mL'),
                               response[13:18], (1000, 1, 1, 1e9, 1e9)):
        result[name] = real(value, 0, high)
    result['supply_ready'] = integer(response[18], 1)
    if extended:result.update(dialysate_mL_min=real(response[19],0,2000),tmp_mmHg=real(response[20],-1000,1000))
    if physical:
        result.update(arterial_mmHg=real(response[21],-1000,1000),limitation=response[22])
        for name, value, low, high in zip(
            ('dialysate_mmHg','heater_W','acid_remaining_mL','bicarbonate_remaining_g','conductivity_raw_mS_cm'),
            response[23:28], (-1000,0,0,0,0), (1000,5000,20000,2000,1000)):
            result[name] = real(value, low, high)
    if dynamic:
        for name, value, low, high in zip(
            ('arterial_level','venous_level','dialysate_drain_mL_min','uf_pump_mL_min','balance_position_mL','bypass','balance_capacity_mL','balance_phase'),
            response[28:36], (0,0,0,0,0,0,5,0), (1,1,2000,200,100,1,100,1)):
            result[name] = real(value, low, high)
    if preparation:result.update(preparation_ready=bool(integer(response[36],1)),preparation_fault=bool(integer(response[37],1)))
    return result


def metadata(response):
    guided=response[0]=='MACHINE8'
    expect(response,'MACHINE8' if guided else 'MACHINE5',40 if guided else 26)
    result = dict(sequence=integer(response[1], 99999), time_ms=integer(response[2]),
                  stage=(GUIDED_STAGES if guided else STAGES)[integer(response[3],15 if guided else 9)], mode=treatment.MODES[integer(response[4], 2)])
    for name, value, low, high in zip(('blood_prescribed_mL_min', 'net_uf_prescribed_mL_min', 'replacement_prescribed_mL_min',
                                  'pressure_limit_mmHg', 'prime_mL'), response[5:10], (0,0,0,1,10), (500, 20, 120, 1000, 1000)):
        result[name] = real(value, low, high)
    for name, value, high in zip(('alarm_mask', 'acknowledged_mask', 'silence_until_ms', 'safe_cycles', 'ready_cycles',
                                 'treatment_cycles', 'revision'), response[10:17], (8191, 8191, 100120000, 3, 3, 100000000, 100000000)):
        result[name] = integer(value, high)
    result.update(action=response[17], terminal=bool(integer(response[18], 1)))
    for name, value in zip(('phase_flush_mL', 'flush_in_mL', 'flush_out_mL', 'expected_net_mL', 'measured_net_mL',
                           'flush_in_tick_mL', 'flush_out_tick_mL'), response[19:26]):
        result[name] = real(value, -1e9 if 'net' in name else 0, 100000 if 'tick' in name else 1e9)
    if guided:
        names=('phase_elapsed_ms','treatment_elapsed_ms','duration_ms','test_duration_ms','disinfection_duration_ms')
        result['guided']={name:integer(value) for name,value in zip(names,response[26:31])}
        result['guided'].update(return_target_mL=real(response[31],10,1000),returned_mL=real(response[32],0,1e9),
            resume_stage=GUIDED_STAGES[integer(response[33],15)],patient_connected=bool(integer(response[34],1)),
            return_in_tick_mL=real(response[35],0,100000),return_out_tick_mL=real(response[36],0,100000),tests_passed=integer(response[37],127),primed=bool(integer(response[38],1)),integrated_stage=GUIDED_STAGES[integer(response[39],15)])
    result['alarms'] = [name for i, name in enumerate(ALARMS) if result['alarm_mask'] & (1 << i)]
    result['annunciating'] = bool(result['alarm_mask'] & ~result['acknowledged_mask']) and result['time_ms'] >= result['silence_until_ms']
    return result


def committed(response):
    if not response or response[0]!='COMMITTED5':raise ProtocolError('commit5 schema')
    tag='MACHINE8' if 'MACHINE8' in response else 'MACHINE5'
    if tag not in response:raise ProtocolError('commit5 machine schema')
    split=response.index(tag)
    result = treatment.committed(['COMMITTED4', *response[1:split]])
    end=response.index('PHYSICS9') if 'PHYSICS9' in response else len(response)
    result['machine'] = metadata(response[split:end])
    if end<len(response):
        from . import physical
        result['physical']=physical.state(response[end:])
    return result


def view(response):
    expect(response[:1], 'VIEW5', 1)
    if len(response)<2:raise ProtocolError('device view size')
    m_end=41 if response[1]=='MACHINE8' else 27
    if len(response)<=m_end:raise ProtocolError('device view size')
    o_end=m_end+(38 if response[m_end]=='OBS11' else 36 if response[m_end]=='OBS10' else 28 if response[m_end]=='OBS9' else 21 if response[m_end]=='OBS8' else 19)
    if len(response)!=o_end+4:raise ProtocolError('device view size')
    result=dict(machine=metadata(response[1:m_end]),observation=observation(response[m_end:o_end]))
    expect(response[o_end:],'INTENT5',4)
    result['intent']=dict(id=integer(response[o_end+1]),state=response[o_end+2],result=response[o_end+3])
    return result
