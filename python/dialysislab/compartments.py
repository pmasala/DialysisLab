"""Conservative synthetic body/circuit compartments; no clinical calibration."""
import copy
import math
from .circuit import keys, number, vector, index
from .protocol import ProtocolError

FIELDS = ('id provenance volume_mL concentration_mmol_L exchange_mL_min partition '
          'refill_mL_min prime_mL initial_weight_kg pco2_mmHg external_in_mL_min '
          'external_out_mL_min external_mmol_L generation_mmol_min')
# At the largest supported compartment this slack represents <=1e-7 mmol,
# below the unchanged whole-system 1e-6 mmol residual criterion. Never clip mass.
CONCENTRATION_CEILING = 1000 + 1e-9


def validate(config):
    keys(config, FIELDS)
    if config['provenance'] != 'synthetic' or config['id'] not in ('synthetic-baseline', 'synthetic-overload', 'synthetic-imbalance', 'synthetic-custom'):
        raise ValueError('patient identity/provenance')
    if not isinstance(config['volume_mL'], list) or len(config['volume_mL']) != 2:
        raise ValueError('two body volumes required')
    for value in config['volume_mL']: number(value, 100, 100000)
    if not 1000 <= sum(config['volume_mL']) <= 100000:
        raise ValueError('total body volume')
    concentrations = config['concentration_mmol_L']
    if not isinstance(concentrations, list) or len(concentrations) != 2:
        raise ValueError('two concentration vectors required')
    for values in concentrations: vector(values, 0, 1000)
    vector(config['exchange_mL_min'], 0, 2000)
    vector(config['partition'], 0.001, 1000)
    vector(config['external_mmol_L'], 0, 1000)
    vector(config['generation_mmol_min'], 0, 10)
    for key, low, high in [('refill_mL_min', 0, 5000), ('prime_mL', 10, 1000),
                           ('initial_weight_kg', 1, 300), ('pco2_mmHg', 10, 100),
                           ('external_in_mL_min', 0, 100), ('external_out_mL_min', 0, 100)]:
        number(config[key], low, high)
    if config['initial_weight_kg'] < sum(config['volume_mL']) / 1000:
        raise ValueError('weight cannot be less than initial body water mass')
    return config


def validate_scenario(config, validate_circuit):
    keys(config, 'schema_version model seed ticks dt_ms blood_mL_min uf_mL_min resistance_mmHg_min_mL '
                'pressure_limit_mmHg patient_volume_mL faults circuit transport patient')
    if type(config['schema_version']) is not int or config['schema_version'] != 3 or config['model'] != 'm3-patient-1':
        raise ValueError('coupled scenario version/model')
    patient = validate(config['patient'])
    base = {k: v for k, v in config.items() if k != 'patient'}
    base.update(schema_version=2, model='m2-circuit-1')
    validate_circuit(base)
    if abs(sum(patient['volume_mL']) - config['patient_volume_mL']) > 1e-8:
        raise ValueError('initial patient volume mismatch')
    if patient['concentration_mmol_L'][0] != config['transport']['blood_mmol_L']:
        raise ValueError('initial blood concentration mismatch')
    return config


def validate_snapshot(state, online=False):
    if online:
        number(state.get('substitution_mL'), 0, 1e9)
        vector(state.get('substitution_mmol'), 0, 1e9)
        base = {k: v for k, v in state.items() if k not in ('substitution_mL', 'substitution_mmol')}
        validate_snapshot(base)
        return state
    keys(state, 'sequence time_ms volume_mL mass_mmol concentration_mmol_L gross_uf_mL external_in_mL '
                'external_out_mL net_patient_loss_mL weight_kg illustrative_pH mass_residual_mmol '
                'diffusive_mmol convective_mmol input_mmol output_mmol')
    index(state['sequence'], 0, 99999); index(state['time_ms'], 0, 100000000)
    if not isinstance(state['volume_mL'], list) or len(state['volume_mL']) != 3:
        raise ProtocolError('compartment volume vector')
    for v in state['volume_mL']: number(v, 1, 100000)
    for name, limit in [('mass_mmol', 100000), ('concentration_mmol_L', CONCENTRATION_CEILING)]:
        if not isinstance(state[name], list) or len(state[name]) != 3:
            raise ProtocolError('compartment matrix')
        for row in state[name]: vector(row, 0, limit)
    for name in ('diffusive_mmol', 'convective_mmol', 'input_mmol', 'output_mmol'):
        vector(state[name], -1e9, 1e9)
    vector(state['mass_residual_mmol'], -1e-6, 1e-6)
    for name in ('gross_uf_mL', 'external_in_mL', 'external_out_mL'): number(state[name], 0, 1e9)
    number(state['net_patient_loss_mL'], -100000, 100000)
    number(state['weight_kg'], 0, 400)
    if state['illustrative_pH'] is not None: number(state['illustrative_pH'], -400, 400)
    return state


class Sum:
    def __init__(self):
        self.value = self.correction = 0.0

    def add(self, value):
        increment = value - self.correction
        updated = self.value + increment
        self.correction = (updated - self.value) - increment
        self.value = updated


def solve(matrix, rhs):
    """Tiny pivoted balance solve. Inputs remain unchanged on rejection."""
    a = [list(row) + [value] for row, value in zip(matrix, rhs)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(a[row][col]))
        a[col], a[pivot] = a[pivot], a[col]
        if not math.isfinite(a[col][col]) or abs(a[col][col]) < 1e-12:
            raise ProtocolError('singular compartment balance')
        for row in range(col + 1, 3):
            multiplier = a[row][col] / a[col][col]
            for j in range(col, 4): a[row][j] -= multiplier * a[col][j]
    result = [0.0] * 3
    for row in range(2, -1, -1):
        result[row] = (a[row][3] - math.fsum(a[row][j] * result[j] for j in range(row + 1, 3))) / a[row][row]
    if not all(math.isfinite(x) and 0 <= x <= CONCENTRATION_CEILING for x in result):
        raise ProtocolError('concentration outside model bounds')
    return result


class Compartments:
    def __init__(self, config, online=False):
        self.online = online
        self.config = copy.deepcopy(validate(config))
        self.volume = [*map(float, config['volume_mL']), float(config['prime_mL'])]
        self.initial_body = sum(self.volume[:2])
        self.concentration = copy.deepcopy(config['concentration_mmol_L']) + [list(config['concentration_mmol_L'][0])]
        self.mass = [[v * c / 1000 for c in values] for v, values in zip(self.volume, self.concentration)]
        self.initial_mass = [math.fsum(row[i] for row in self.mass) for i in range(6)]
        self.water = {name: Sum() for name in (('uf', 'in', 'out', 'sub') if online else ('uf', 'in', 'out'))}
        self.solute = {name: [Sum() for _ in range(6)] for name in (('diffusive', 'convective', 'input', 'output', 'substitution') if online else ('diffusive', 'convective', 'input', 'output'))}
        self.next_sequence = self.time_ms = self.sequence = 0
        self.mass_residual = [0.0] * 6

    def snapshot(self):
        body = math.fsum(self.volume[:2])
        bicarbonate = self.concentration[0][4]
        return dict(**(dict(substitution_mL=self.water['sub'].value) if self.online else {}),
                    sequence=self.sequence, time_ms=self.time_ms,
                    volume_mL=list(self.volume), mass_mmol=copy.deepcopy(self.mass),
                    concentration_mmol_L=copy.deepcopy(self.concentration),
                    gross_uf_mL=self.water['uf'].value, external_in_mL=self.water['in'].value,
                    external_out_mL=self.water['out'].value, net_patient_loss_mL=self.initial_body - body,
                    weight_kg=self.config['initial_weight_kg'] + (body - self.initial_body) / 1000,
                    illustrative_pH=(6.1 + math.log10(bicarbonate) - math.log10(0.03 * self.config['pco2_mmHg'])
                                     if bicarbonate > 0 else None),
                    mass_residual_mmol=list(self.mass_residual),
                    **{name + '_mmol': [s.value for s in values] for name, values in self.solute.items()})

    def advance(self, request):
        keys(request, 'sequence time_ms dt_ms draw_mL return_mL uf_mL stored_mL clearance_mL_min sieving dialysate_mmol_L'
             + (' pre_mL post_mL substitution_mmol_L' if self.online else ''))
        for key in ('sequence', 'time_ms', 'dt_ms'):
            if type(request[key]) is not int: raise ProtocolError('clock type')
        if (request['sequence'] != self.next_sequence or request['time_ms'] != self.time_ms
                or not 1 <= request['dt_ms'] <= 1000 or self.next_sequence >= 100000):
            raise ProtocolError('patient tick order')
        dt = request['dt_ms'] / 60000
        for key, high in [('draw_mL', 500 * dt), ('return_mL', 100000), ('uf_mL', (140 if self.online else 20) * dt), ('stored_mL', 96000)]:
            number(request[key], 0, high)
        vector(request['clearance_mL_min'], 0, 2000)
        vector(request['sieving'], 0, 1)
        vector(request['dialysate_mmol_L'], 0, 1000)
        draw, returned, uf = (request[k] for k in ('draw_mL', 'return_mL', 'uf_mL'))
        pre = post = 0
        replacement_c = [0] * 6
        if self.online:
            pre, post = (number(request[k], 0, 120 * dt) for k in ('pre_mL', 'post_mL'))
            if pre > 0 and post > 0: raise ProtocolError('two simultaneous replacement routes')
            replacement_c = request['substitution_mmol_L']
            vector(replacement_c, 0, CONCENTRATION_CEILING)
        circuit_volume = self.config['prime_mL'] + request['stored_mL']
        if abs(circuit_volume - self.volume[2] - draw - pre + returned + uf) > 1e-8:
            raise ProtocolError('circuit water mismatch')
        incoming, outgoing = (self.config[k] * dt for k in ('external_in_mL_min', 'external_out_mL_min'))
        water = copy.deepcopy(self.water)
        for name, value in [('uf', uf), ('in', incoming), ('out', outgoing)]: water[name].add(value)
        if self.online: water['sub'].add(pre + post)
        # Reconstruct body total from absolute conserved ledgers, avoiding drainage
        # drift at the volume ceiling; compare independent hydraulic deltas above.
        body = math.fsum([self.initial_body, water['in'].value, -water['out'].value,
                          -water['uf'].value, water['sub'].value if self.online else 0, -request['stored_mL']])
        ve, vi = body - self.volume[1], self.volume[1]
        te, ti = self.config['volume_mL']
        kd = self.config['refill_mL_min'] * dt
        refill = kd * (vi / ti - ve / te) / (1 + kd * (1 / ti + 1 / te))
        ve += refill
        vi = body - ve
        volumes = [ve, vi, circuit_volume]
        if not 1 <= body <= 100000 or not all(1 <= v <= 100000 for v in volumes):
            raise ProtocolError('compartment volume outside model bounds')
        solute = copy.deepcopy(self.solute)
        concentrations = [[0.0] * 6 for _ in range(3)]
        masses = [[0.0] * 6 for _ in range(3)]
        residuals = []
        for i in range(6):
            exchange = self.config['exchange_mL_min'][i] * dt
            reverse = exchange / self.config['partition'][i]
            ei, ie = max(-refill, 0), max(refill, 0)
            kd = request['clearance_mL_min'][i] * dt
            conv = uf * request['sieving'][i]
            external = incoming * self.config['external_mmol_L'][i] + self.config['generation_mmol_min'][i] * dt * 1000
            matrix = [[ve + draw + outgoing + exchange + ei, -reverse - ie, -returned],
                      [-exchange - ei, vi + reverse + ie, 0],
                      [-draw, 0, circuit_volume + returned + kd + conv]]
            rhs = [self.mass[0][i] * 1000 + external + post * replacement_c[i], self.mass[1][i] * 1000,
                   self.mass[2][i] * 1000 + kd * request['dialysate_mmol_L'][i] + pre * replacement_c[i]]
            result = solve(matrix, rhs)
            for j in range(3):
                concentrations[j][i] = result[j]
                masses[j][i] = result[j] * volumes[j] / 1000
            for name, value in [('input', external / 1000), ('output', outgoing * result[0] / 1000),
                                ('diffusive', kd * (result[2] - request['dialysate_mmol_L'][i]) / 1000),
                                ('convective', conv * result[2] / 1000)]:
                solute[name][i].add(value)
            if self.online: solute['substitution'][i].add((pre + post) * replacement_c[i] / 1000)
            residual = math.fsum([*(row[i] for row in masses), solute['diffusive'][i].value,
                                  solute['convective'][i].value, solute['output'][i].value,
                                  -solute['input'][i].value, -solute['substitution'][i].value if self.online else 0, -self.initial_mass[i]])
            if abs(residual) > 1e-6: raise ProtocolError('patient mass conservation residual')
            residuals.append(residual)
        # Validate the complete prospective response before mutating accepted state.
        proposed = copy.copy(self)
        proposed.volume, proposed.concentration, proposed.mass = volumes, concentrations, masses
        proposed.water, proposed.solute, proposed.mass_residual = water, solute, residuals
        proposed.sequence = self.next_sequence
        proposed.next_sequence += 1
        proposed.time_ms += request['dt_ms']
        snapshot = validate_snapshot(proposed.snapshot(), self.online)
        self.__dict__.update(proposed.__dict__)
        return snapshot
