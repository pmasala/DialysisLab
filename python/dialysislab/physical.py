"""Generic physical profiles; configured by the scenario administrator only."""
from .circuit import keys, number, vector
from .protocol import rpc, expect, real, integer, ProtocolError

DYNAMIC_FIELDS='arterial_air_mL venous_air_mL level_gain_mL_s_mL gas_max_mL_s dialysate_compliance_mL_mmHg pump_tau_s sensor_tau_s pressure_gain_mL_min_mmHg uf_pump_max_mL_min balance_chamber_mL dialysate_volume_mL'

BLOOD_FIELDS = ('arterial_diameter_mm arterial_length_mm venous_diameter_mm venous_length_mm '
                'tube_diameter_mm arterial_tube_mm venous_tube_mm arterial_chamber_mL venous_chamber_mL '
                'filter_mL filter_R kuf_mL_min_mmHg '
                'max_filter_hct max_plasma_filtration_fraction dialysate_min_mmHg dialysate_max_mmHg '
                'dialysate_R access_mmHg pump_head_mmHg')
FLUID_FIELDS = ('acid_mL bicarbonate_g acid_installed bicarbonate_installed acid_fraction bicarbonate_fraction '
                'bicarbonate_stock_mmol_L dissolution_g_min heater_max_W heater_capacity_J_K heater_loss_W_K '
                'ambient_C heater_gain_W_K conductivity_factor temperature_coefficient')
PREPARATION_FIELDS='acid_line_mL bicarbonate_line_mL cartridge_mL cartridge_target_mL fill_mL_min step_s sensor_latency_s dwell_s initial_line_occupancy'
PREPARATION_RANGES=[(.1,50),(.1,50),(20,500),(10,450),(0,1000),(.005,.05),(0,.4),(.5,30),(0,2)]

def validate(config):
    if 'guided' not in config:raise ValueError('physical model requires guided lifecycle')
    if any(f['target'].startswith('edge:') or f['target']=='resistance' for f in config['faults']):raise ValueError('use physical geometry; legacy edge faults are not supported')
    p=config['physical'];keys(p,'blood fluid'+(' dynamics' if 'dynamics' in p else '')+(' preparation' if 'preparation' in p else ''))
    if 'preparation' in p:
        if 'dynamics' not in p:raise ValueError('preparation requires dynamic physical model')
        q=p['preparation'];keys(q,PREPARATION_FIELDS)
        for k,bounds in zip(PREPARATION_FIELDS.split(),PREPARATION_RANGES):number(q[k],*bounds)
        if type(q['initial_line_occupancy']) is not int:raise ValueError('line occupancy code')
        if q['cartridge_target_mL']>q['cartridge_mL']-10:raise ValueError('cartridge headspace')
        if p['fluid']['acid_fraction']<=0 or p['fluid']['bicarbonate_fraction']<=0 or not any(p['fluid']['acid_mmol_L'][1:]):raise ValueError('preparation nominal concentration')
    if 'dynamics' in p:
        keys(p['dynamics'],DYNAMIC_FIELDS)
        for k,bounds in zip(DYNAMIC_FIELDS.split(),[(5,100),(5,100),(0,10),(0,10),(.01,1),(.05,5),(.01,5),(.1,20),(20,200),(5,100),(50,1000)]):number(p['dynamics'][k],*bounds)
    b=p['blood'];keys(b,BLOOD_FIELDS)
    ranges=[(.5,3),(5,100),(.5,3),(5,100),(2,8),(50,3000),(50,3000),(1,100),(1,100),
            (1,250),(.01,2),(.01,2),(.4,.7),(.05,.6),(-500,0),(0,500),(.001,1),(0,100),(100,600)]
    for k,bounds in zip(BLOOD_FIELDS.split(),ranges):number(b[k],*bounds)
    if 'dynamics' in p and p['dynamics']['dialysate_volume_mL']+p['dynamics']['dialysate_compliance_mL_mmHg']*b['dialysate_min_mmHg']<=1:raise ValueError('dialysate compliance exceeds inventory')
    h=config['patient'].get('hemodynamics')
    if not h:raise ValueError('physical scenario requires patient hemodynamics')
    if h['initial_hematocrit']>=b['max_filter_hct']:raise ValueError('initial hematocrit exceeds filter limit')
    import math
    volume=math.pi*(b['tube_diameter_mm']/2)**2*(b['arterial_tube_mm']+b['venous_tube_mm'])/1000+b['arterial_chamber_mL']+b['venous_chamber_mL']+b['filter_mL']
    if abs(volume-config['patient']['prime_mL'])>1e-6:raise ValueError('disposable priming volume mismatch')
    f=p['fluid'];keys(f,FLUID_FIELDS+' acid_mmol_L')
    ranges=[(0,20000),(0,2000),(0,1),(0,1),(0,.1),(0,.2),(100,1500),(0,100),
            (0,5000),(1,10000),(0,100),(0,50),(0,5000),(.1,1),(.001,.03)]
    for k,bounds in zip(FLUID_FIELDS.split(),ranges):number(int(f[k]) if type(f[k]) is bool else f[k],*bounds)
    for k in ('acid_installed','bicarbonate_installed'):
        if type(f[k]) is not bool:raise ValueError('installation flag')
    vector(f['acid_mmol_L'],0,10000)
    if f['acid_fraction']+f['bicarbonate_fraction']>=1:raise ValueError('water mixing ratio')
    return p

def configure(admin,config):
    p=validate(config);h=config['patient']['hemodynamics']
    fields=[p['blood'][k] for k in BLOOD_FIELDS.split()]
    expect(rpc(admin,'PHYSICAL9',*fields,h['initial_hematocrit'],h['protein_g_dL'],h['temperature_C']),'OK',1)
    fields=[int(p['fluid'][k]) if type(p['fluid'][k]) is bool else p['fluid'][k] for k in FLUID_FIELDS.split()]
    expect(rpc(admin,'FLUID9',*fields,*p['fluid']['acid_mmol_L']),'OK',1)
    if 'dynamics' in p:expect(rpc(admin,'DYNAMICS10',*[p['dynamics'][k] for k in DYNAMIC_FIELDS.split()]),'OK',1)
    if 'preparation' in p:expect(rpc(admin,'PREPARATION11',*[p['preparation'][k] for k in PREPARATION_FIELDS.split()]),'OK',1)

def update_blood(admin,snapshot):
    h=snapshot['hemodynamics']
    if 'distributed' in snapshot:
        values=[x for c in snapshot['distributed']['compartments'][2:14] for x in (c['hematocrit'],c['protein_g_dL'])]
        expect(rpc(admin,'INVENTORY10',snapshot['sequence']+1,snapshot['time_ms'],*values),'OK',1)
    expect(rpc(admin,'BLOOD9',snapshot['sequence']+1,snapshot['time_ms'],h['hematocrit'],h['protein_g_dL'],h['temperature_C'],h['circuit_hematocrit'],h['circuit_protein_g_dL']),'OK',1)

DIAGNOSTICS=('arterial_mmHg venous_mmHg prefilter_mmHg postfilter_mmHg dialysate_mmHg tmp_mmHg '
             'inlet_hematocrit outlet_hematocrit return_hematocrit plasma_filtration_fraction '
             'acid_remaining_mL bicarbonate_remaining_g heater_W conductivity_raw_mS_cm '
             'arterial_chamber_mL venous_chamber_mL filter_mL')
def state(response):
    preparation=None
    if 'PREPARATION11' in response:
        end=response.index('PREPARATION11');preparation=response[end+1:];response=response[:end]
        if len(preparation)!=31:raise ProtocolError('preparation state schema')
    dynamic=None
    if 'DYNAMICS10' in response:
        end=response.index('DYNAMICS10');dynamic=response[end+1:];response=response[:end]
        if len(dynamic)!=15:raise ProtocolError('dynamic state schema')
    if len(response)!=1+2+17+1+12*5 or response[0]!='PHYSICS9':raise ProtocolError('physical state schema')
    result=dict(sequence=integer(response[1]),time_ms=integer(response[2]))
    result.update({name:real(x,-1e6,1e6) for name,x in zip(DIAGNOSTICS.split(),response[3:20])})
    result['limitation']=response[20]
    result['segments']=[dict(zip(('hematocrit','viscosity_mPa_s','blood_mmHg','uf_mL_min','oncotic_mmHg'),
        [real(x,-1e6,1e6) for x in response[21+i*5:26+i*5]])) for i in range(12)]
    if dynamic is not None:
        names='arterial_volume_mL venous_volume_mL arterial_level venous_level arterial_gas_mL_s venous_gas_mL_s feed_mL_min drain_mL_min uf_pump_mL_min sensed_dialysate_mmHg dialysate_storage_mL dialysate_residual_mL balance_position_mL balance_cycles bypass'
        result['dynamics']=dict(zip(names.split(),[real(x,-1e9,1e9) for x in dynamic]))
    if preparation is not None:
        names='stage acid_state bicarbonate_state ready fault reason cartridge_liquid_mL cartridge_gas_atm_mL solid_g dissolved_mmol pressure_mmHg acid_line_liquid_mL bicarbonate_line_liquid_mL acid_command_mL_min acid_actual_mL_min bicarbonate_command_mL_min bicarbonate_actual_mL_min stable_s sensor_time_s source_mL waste_mL qualified_mL water_residual_mL cartridge_gas_residual_mL line_gas_residual_mL'
        result['preparation']={k:(v if k=='reason' else real(v,-1e9,1e9)) for k,v in zip(names.split(),preparation[:25])}
        result['preparation']['mass_residual_mmol']=[real(v,-1e9,1e9) for v in preparation[25:]]
    return result


def verify_record(record, config):
    """Independent ledger/equation checks on retained physical telemetry."""
    import math
    p=record['physical'];b=config['physical']['blood'];h=record['patient']['hemodynamics']
    if (p['sequence'],p['time_ms'])!=(record['sequence'],record['time_ms']):raise ValueError('physical clock mismatch')
    initial=config['patient']['hemodynamics']
    if abs(h['vascular_rbc_mL']+h['circuit_rbc_mL']+h['lost_rbc_mL']-initial['vascular_mL']*initial['initial_hematocrit'])>1e-6:raise ValueError('RBC conservation')
    if abs(h['hematocrit']*h['vascular_mL']-h['vascular_rbc_mL'])>1e-6:raise ValueError('hematocrit/volume mismatch')
    initial_protein=initial['vascular_mL']*(1-initial['initial_hematocrit'])*initial['protein_g_dL']/100
    if abs(h['vascular_protein_g']+h['circuit_protein_g']+h['lost_protein_g']-initial_protein)>1e-6:raise ValueError('protein conservation')
    if abs(h['protein_g_dL']*(h['vascular_mL']-h['vascular_rbc_mL'])/100-h['vascular_protein_g'])>1e-6:raise ValueError('protein concentration mismatch')
    qb=record['blood_mL_min'];uf=record['uf_mL_min'];sub=record['online']['replacement_mL_min']
    if abs(sum(s['uf_mL_min'] for s in p['segments'])-uf)>1e-5:raise ValueError('segment UF sum')
    if not b['dialysate_min_mmHg']-1e-6<=p['dialysate_mmHg']<=b['dialysate_max_mmHg']+1e-6:raise ValueError('dialysate pressure bound')
    if not qb and 'dynamics' not in p:return
    route=record['online']['mode'];q=qb+(sub if route=='HDF_PRE' else 0)
    cells=qb*p['inlet_hematocrit'];out=q-uf
    if qb and (out<=0 or abs(p['outlet_hematocrit']*out-cells)>1e-5):raise ValueError('filter cell flux')
    if p['outlet_hematocrit']>b['max_filter_hct']+1e-6:raise ValueError('filter hematocrit bound')
    if p['plasma_filtration_fraction']>b['max_plasma_filtration_fraction']+1e-6:raise ValueError('plasma filtration bound')
    if p['prefilter_mmHg']-p['arterial_mmHg']>b['pump_head_mmHg']+1e-5:raise ValueError('pump head bound')
    qd=config['transport']['dialysate_mL_min'] if record['machine']['guided']['integrated_stage']=='TREATMENT' and not record['machine']['alarm_mask'] else 0
    if 'dynamics' in p:
        d=p['dynamics'];qd=d['feed_mL_min']
        if abs(d['dialysate_residual_mL'])>1e-5:raise ValueError('dialysate water ledger')
        if 'distributed' not in record['patient']:raise ValueError('missing distributed inventory')
        cells_record=record['patient']['distributed']['compartments']
        if abs(sum(c['volume_mL'] for c in cells_record)-record['patient']['volume_mL'][2])>1e-7:raise ValueError('distributed volume summary')
        if abs(sum(c['rbc_mL'] for c in cells_record)-h['circuit_rbc_mL'])>1e-7:raise ValueError('distributed RBC summary')
        if abs(sum(c['protein_g'] for c in cells_record)-h['circuit_protein_g'])>1e-7:raise ValueError('distributed protein summary')
        for cell in cells_record:
            if abs(cell['hematocrit']*cell['volume_mL']-cell['rbc_mL'])>1e-7:raise ValueError('local hematocrit inventory')
            if abs(cell['protein_g_dL']*(cell['volume_mL']-cell['rbc_mL'])/100-cell['protein_g'])>1e-7:raise ValueError('local protein inventory')
        for j in range(6):
            if abs(sum(c['volume_mL']*c['concentration_mmol_L'][j]/1000 for c in cells_record)-record['patient']['mass_mmol'][2][j])>1e-7:raise ValueError('distributed solute summary')
    if not qb:return
    for i,s in enumerate(p['segments']):
        mid=q-s['uf_mL_min']/2
        if 'dynamics' not in p and abs(mid*s['hematocrit']-cells)>1e-5:raise ValueError('segment cell flux')
        pd=p['dialysate_mmHg']+b['dialysate_R']*qd*(.5-(i+.5)/12)
        expected=0 if p.get('dynamics',{}).get('bypass') else max(0,b['kuf_mL_min_mmHg']/12*(s['blood_mmHg']-s['oncotic_mmHg']-pd))
        if abs(expected-s['uf_mL_min'])>1e-5:raise ValueError('segment Starling flux')
        if not math.isfinite(s['viscosity_mPa_s']) or s['viscosity_mPa_s']<=0:raise ValueError('viscosity domain')
        q-=s['uf_mL_min']


def patient_configuration(config):
    """Keep geometry in one scenario location; expand only the patient INIT frame."""
    import copy,math
    p=copy.deepcopy(config['patient'])
    if 'dynamics' in config.get('physical',{}):
        b=config['physical']['blood'];area=math.pi*(b['tube_diameter_mm']/2)**2/1000
        p['extracorporeal']=dict(volumes_mL=[area*b['arterial_tube_mm'],b['arterial_chamber_mL']]+[b['filter_mL']/12]*12+[b['venous_chamber_mL'],area*b['venous_tube_mm']],
            koa_mL_min=config['circuit']['profile']['koa_mL_min'],dialysate_volume_mL=config['physical']['dynamics']['dialysate_volume_mL'],
            dialysate_mmol_L=config['transport']['dialysate_mmol_L'])
    return p


def attach_transaction(transaction,record,config):
    d=record.get('physical',{}).get('dynamics')
    if d is None:return
    volumes=patient_configuration(config)['extracorporeal']['volumes_mL']
    volumes[1]=d['arterial_volume_mL'];volumes[14]=d['venous_volume_mL']
    transaction['distributed']=dict(volumes_mL=volumes,
        filtration_mL=[s['uf_mL_min']*transaction['dt_ms']/60000 for s in record['physical']['segments']],
        dialysate_mL_min=d['feed_mL_min'],dialysate_storage_mL=d['dialysate_storage_mL'],dialysate_drain_mL_min=d['drain_mL_min'],membrane_open=not bool(d['bypass']))
