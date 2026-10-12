"""Generic physical profiles; configured by the scenario administrator only."""
from .circuit import keys, number, vector
from .protocol import rpc, expect, real, integer, ProtocolError

BLOOD_FIELDS = ('arterial_diameter_mm arterial_length_mm venous_diameter_mm venous_length_mm '
                'tube_diameter_mm arterial_tube_mm venous_tube_mm arterial_chamber_mL venous_chamber_mL '
                'filter_mL filter_R kuf_mL_min_mmHg '
                'max_filter_hct max_plasma_filtration_fraction dialysate_min_mmHg dialysate_max_mmHg '
                'dialysate_R access_mmHg pump_head_mmHg')
FLUID_FIELDS = ('acid_mL bicarbonate_g acid_installed bicarbonate_installed acid_fraction bicarbonate_fraction '
                'bicarbonate_stock_mmol_L dissolution_g_min heater_max_W heater_capacity_J_K heater_loss_W_K '
                'ambient_C heater_gain_W_K conductivity_factor temperature_coefficient')

def validate(config):
    if 'guided' not in config:raise ValueError('physical model requires guided lifecycle')
    if any(f['target'].startswith('edge:') or f['target']=='resistance' for f in config['faults']):raise ValueError('use physical geometry; legacy edge faults are not supported')
    p=config['physical'];keys(p,'blood fluid')
    b=p['blood'];keys(b,BLOOD_FIELDS)
    ranges=[(.5,3),(5,100),(.5,3),(5,100),(2,8),(50,3000),(50,3000),(1,100),(1,100),
            (1,250),(.01,2),(.01,1),(.4,.7),(.05,.6),(-500,0),(0,500),(.001,1),(0,100),(100,600)]
    for k,bounds in zip(BLOOD_FIELDS.split(),ranges):number(b[k],*bounds)
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

def update_blood(admin,snapshot):
    h=snapshot['hemodynamics']
    expect(rpc(admin,'BLOOD9',snapshot['sequence']+1,snapshot['time_ms'],h['hematocrit'],h['protein_g_dL'],h['temperature_C'],h['circuit_hematocrit'],h['circuit_protein_g_dL']),'OK',1)

DIAGNOSTICS=('arterial_mmHg venous_mmHg prefilter_mmHg postfilter_mmHg dialysate_mmHg tmp_mmHg '
             'inlet_hematocrit outlet_hematocrit return_hematocrit plasma_filtration_fraction '
             'acid_remaining_mL bicarbonate_remaining_g heater_W conductivity_raw_mS_cm '
             'arterial_chamber_mL venous_chamber_mL filter_mL')
def state(response):
    if len(response)!=1+2+17+1+12*5 or response[0]!='PHYSICS9':raise ProtocolError('physical state schema')
    result=dict(sequence=integer(response[1]),time_ms=integer(response[2]))
    result.update({name:real(x,-1e6,1e6) for name,x in zip(DIAGNOSTICS.split(),response[3:20])})
    result['limitation']=response[20]
    result['segments']=[dict(zip(('hematocrit','viscosity_mPa_s','blood_mmHg','uf_mL_min','oncotic_mmHg'),
        [real(x,-1e6,1e6) for x in response[21+i*5:26+i*5]])) for i in range(12)]
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
    if not qb:return
    route=record['online']['mode'];q=qb+(sub if route=='HDF_PRE' else 0)
    cells=qb*p['inlet_hematocrit'];out=q-uf
    if out<=0 or abs(p['outlet_hematocrit']*out-cells)>1e-5:raise ValueError('filter cell flux')
    if p['outlet_hematocrit']>b['max_filter_hct']+1e-6:raise ValueError('filter hematocrit bound')
    if p['plasma_filtration_fraction']>b['max_plasma_filtration_fraction']+1e-6:raise ValueError('plasma filtration bound')
    if p['prefilter_mmHg']-p['arterial_mmHg']>b['pump_head_mmHg']+1e-5:raise ValueError('pump head bound')
    qd=config['transport']['dialysate_mL_min'] if record['machine']['guided']['integrated_stage']=='TREATMENT' and not record['machine']['alarm_mask'] else 0
    for i,s in enumerate(p['segments']):
        mid=q-s['uf_mL_min']/2
        if abs(mid*s['hematocrit']-cells)>1e-5:raise ValueError('segment cell flux')
        pd=p['dialysate_mmHg']+b['dialysate_R']*qd*(.5-(i+.5)/12)
        expected=max(0,b['kuf_mL_min_mmHg']/12*(s['blood_mmHg']-s['oncotic_mmHg']-pd))
        if abs(expected-s['uf_mL_min'])>1e-5:raise ValueError('segment Starling flux')
        if not math.isfinite(s['viscosity_mPa_s']) or s['viscosity_mPa_s']<=0:raise ValueError('viscosity domain')
        q-=s['uf_mL_min']
