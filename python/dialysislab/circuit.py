"""Strict scenario-v2 configuration and authorized circuit truth decoding."""
import math
import re
from .protocol import ProtocolError, expect, integer, real, rpc, state as plant_state

SOLUTES = ('urea', 'sodium', 'potassium', 'chloride', 'bicarbonate', 'calcium')
KINDS = ('tube', 'resistor', 'clamp', 'dialyzer')


def keys(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError('configuration fields: ' + names)


def number(value, low, high):
    # Compare bounded JSON integers before math.isfinite converts them to double.
    if type(value) not in (int, float) or not low <= value <= high or not math.isfinite(value):
        raise ValueError('configuration numeric range')
    return value


def index(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('configuration index')
    return value


def vector(values, low, high):
    if not isinstance(values, list) or len(values) != len(SOLUTES):
        raise ValueError('solute vector')
    for value in values:
        number(value, low, high)


def validate(config, validate_m1):
    required = ('schema_version model seed ticks dt_ms blood_mL_min uf_mL_min '
                'resistance_mmHg_min_mL pressure_limit_mmHg patient_volume_mL faults circuit transport')
    keys(config, required)
    if type(config['schema_version']) is not int or config['schema_version'] != 2 or config['model'] != 'm2-circuit-1':
        raise ValueError('configuration version/model')
    base = {k: v for k, v in config.items() if k not in ('circuit', 'transport')}
    base.update(schema_version=1, model='m1-hd-1', faults=[])
    validate_m1(base)  # Scalar types/bounds must be checked before using them as dimensions.
    circuit, transport = config['circuit'], config['transport']
    keys(circuit, 'compliance_mL_mmHg edges pump_node pump_head_mmHg sensor_node sensor_edge dialyzer_edge profile')
    values, edges = circuit['compliance_mL_mmHg'], circuit['edges']
    if not isinstance(values, list) or not 1 <= len(values) <= 16:
        raise ValueError('node count')
    for value in values:
        number(value, 0.001, 10)
    if not isinstance(edges, list) or not 1 <= len(edges) <= 32:
        raise ValueError('edge count')
    for field in ('pump_node', 'sensor_node'):
        index(circuit[field], 1, len(values))
    for field in ('sensor_edge', 'dialyzer_edge'):
        index(circuit[field], 0, len(edges) - 1)
    number(circuit['pump_head_mmHg'], 1, 600)
    dialyzers = []
    for i, edge in enumerate(edges):
        if not isinstance(edge, list) or len(edge) != 5:
            raise ValueError('edge tuple')
        a, b, resistance, kind, closed = edge
        index(a, 0, len(values)); index(b, 0, len(values))
        if a == b or kind not in KINDS or type(closed) is not bool:
            raise ValueError('edge type')
        number(resistance, 0.01, 100)
        if kind == 'dialyzer':
            if a == 0:
                raise ValueError('dialyzer upstream must be compliant node')
            dialyzers.append(i)
    if dialyzers != [circuit['dialyzer_edge']]:
        raise ValueError('exactly one selected dialyzer')
    profile = circuit['profile']
    keys(profile, 'id provenance resistance_mmHg_min_mL kuf_mL_min_mmHg koa_mL_min sieving')
    if (not isinstance(profile['id'], str) or not re.fullmatch(r'[a-z0-9-]{1,48}', profile['id'])
            or profile['provenance'] != 'synthetic'):
        raise ValueError('profile identity/provenance')
    number(profile['resistance_mmHg_min_mL'], 0.01, 100)
    number(profile['kuf_mL_min_mmHg'], 0, 1)
    vector(profile['koa_mL_min'], 0, 2000); vector(profile['sieving'], 0, 1)
    keys(transport, 'blood_mmol_L dialysate_mmol_L dialysate_mL_min')
    vector(transport['blood_mmol_L'], 0, 1000); vector(transport['dialysate_mmol_L'], 0, 1000)
    number(transport['dialysate_mL_min'], 0, 1000)
    if not isinstance(config['faults'], list):
        raise ValueError('fault timeline')
    sensor_faults, seen = [], set()
    for fault in config['faults']:
        keys(fault, 'tick target value')
        index(fault['tick'], 0, config['ticks'] - 1)
        target = fault['target']
        if not isinstance(target, str) or (fault['tick'], target) in seen:
            raise ValueError('fault target/duplicate')
        seen.add((fault['tick'], target))
        if target.startswith('edge:'):
            if not re.fullmatch(r'edge:(0|[1-9][0-9]?)', target):
                raise ValueError('edge fault index')
            index(int(target[5:]), 0, len(edges) - 1)
            keys(fault['value'], 'resistance closed')
            number(fault['value']['resistance'], 0.01, 100)
            if type(fault['value']['closed']) is not bool:
                raise ValueError('clamp flag')
        elif target in ('control_sensor', 'protection_sensor'):
            sensor_faults.append(fault)
        else:
            raise ValueError('unsupported circuit fault')
    base.update(faults=sensor_faults)
    validate_m1(base)
    return config


def configure(admin, config):
    c, tr = config['circuit'], config['transport']
    p = c['profile']
    fields = ['CONFIG2', len(c['compliance_mL_mmHg']), len(c['edges']), c['pump_node'], c['pump_head_mmHg'],
              c['sensor_node'], c['sensor_edge'], c['dialyzer_edge'], p['resistance_mmHg_min_mL'], p['kuf_mL_min_mmHg']]
    fields.extend(c['compliance_mL_mmHg'])
    for a, b, r, kind, closed in c['edges']:
        fields.extend((a, b, r, KINDS.index(kind), int(closed)))
    expect(rpc(admin, *fields), 'OK', 1)
    transport(admin, config, tr['blood_mmol_L'])


def transport(admin, config, blood):
    p, tr = config['circuit']['profile'], config['transport']
    expect(rpc(admin, 'TRANSPORT3' if config['schema_version'] >= 3 else 'TRANSPORT2',
               tr['dialysate_mL_min'], *p['koa_mL_min'], *p['sieving'], *blood, *tr['dialysate_mmol_L']), 'OK', 1)


def state(response):
    if len(response) < 13 or response[0] not in ('CIRCUIT2', 'CIRCUIT3'):
        raise ProtocolError('circuit schema')
    n, t, nodes, edges = (integer(x) for x in response[1:5])
    coupled = response[0] == 'CIRCUIT3'
    if not 1 <= nodes <= 16 or not 1 <= edges <= 32 or len(response) != 13 + nodes + edges + (18 if coupled else 12):
        raise ProtocolError('circuit vector dimensions')
    scalar_names = ('pump_mL_min', 'return_mL_min', 'uf_mL_min', 'stored_mL', 'storage_change_mL',
                    'draw_tick_mL', 'return_tick_mL', 'uf_tick_mL')
    result = dict(sequence=n, time_ms=t)
    result.update((name, real(value, -1e9, 1e9)) for name, value in zip(scalar_names, response[5:13]))
    offset = 13
    for field, size in (('pressure_mmHg', nodes), ('edge_mL_min', edges),
                        ('diffusion_mmol_min', 6), ('convection_mmol_min', 6)):
        result[field] = [real(x, -1e9, 1e9) for x in response[offset:offset + size]]
        offset += size
    if coupled:
        result['clearance_mL_min'] = [real(x, 0, 2000) for x in response[offset:]]
        for name in ('diffusion_mmol_min', 'convection_mmol_min'):
            result['boundary_' + name] = result.pop(name)
    return result


def committed(response, coupled=False):
    if not response or response[0] != ('COMMITTED3' if coupled else 'COMMITTED2'):
        raise ProtocolError('atomic circuit commit schema')
    if len(response) <= 12 or response[12] != ('CIRCUIT3' if coupled else 'CIRCUIT2'):
        raise ProtocolError('commit payload version mismatch')
    result = plant_state(response[1:12])
    result['circuit'] = state(response[12:])
    return result
