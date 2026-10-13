"""Conservative finite-volume blood / countercurrent dialysate transport.

All solute concentrations use the existing apparent whole-compartment convention.
RBC and protein inventories are separate and do not cross the membrane.
"""
import copy
import math
from .circuit import keys, number, vector
from .protocol import ProtocolError

NAMES = ['arterial_tube', 'arterial_chamber'] + ['filter_%02d' % (i+1) for i in range(12)] + ['venous_chamber', 'venous_tube']


def validate_config(c):
    keys(c, 'volumes_mL koa_mL_min dialysate_volume_mL dialysate_mmol_L')
    if len(c['volumes_mL']) != 16: raise ValueError('distributed volumes')
    for v in c['volumes_mL']: number(v, .001, 1000)
    vector(c['koa_mL_min'], 0, 3000)
    vector(c['dialysate_mmol_L'], 0, 1000)
    number(c['dialysate_volume_mL'], 1, 1000)


def initialize(patient):
    c=patient.config['extracorporeal'];v=list(c['volumes_mL'])
    return dict(volumes=v, concentration=[list(patient.concentration[2]) for _ in v],
                cells=[0.0]*16, proteins=[0.0]*16,
                dialysate=[list(c['dialysate_mmol_L']) for _ in range(12)],dialysate_volume=c['dialysate_volume_mL'],
                dialysate_input=[0.0]*6,dialysate_output=[0.0]*6,dialysate_transfer=[0.0]*6,dialysate_residual=[0.0]*6)


def solve(a, rhs):
    """Pivoted solve; caller owns the matrix. Reject, never clip, bad inventories."""
    n=len(rhs);a=[row[:]+[y] for row,y in zip(a,rhs)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(a[r][col]));a[col],a[pivot]=a[pivot],a[col]
        if abs(a[col][col])<1e-12:raise ProtocolError('singular distributed balance')
        for row in range(col+1,n):
            if not a[row][col]:continue
            m=a[row][col]/a[col][col]
            for j in range(col+1,n+1):a[row][j]-=m*a[col][j]
            a[row][col]=0
    result=[0.0]*n
    for i in range(n-1,-1,-1):result[i]=(a[i][n]-math.fsum(a[i][j]*result[j] for j in range(i+1,n)))/a[i][i]
    if not all(math.isfinite(x) and x>=-1e-10 for x in result):raise ProtocolError('distributed inventory domain')
    return result


def topology(patient, request):
    d=request['distributed'];keys(d,'volumes_mL filtration_mL dialysate_mL_min dialysate_storage_mL dialysate_drain_mL_min membrane_open')
    if type(d['membrane_open']) is not bool:raise ProtocolError('membrane valve state')
    v=d['volumes_mL'];f=d['filtration_mL']
    if len(v)!=16 or len(f)!=12:raise ProtocolError('distributed dimensions')
    for x in v:number(x,.001,1000)
    for x in f:number(x,0,3)
    number(d['dialysate_mL_min'],0,1000)
    number(d['dialysate_storage_mL'],-patient.config['extracorporeal']['dialysate_volume_mL']+1,1000);number(d['dialysate_drain_mL_min'],0,2000)
    if abs(sum(v)-patient.config['prime_mL']-request['stored_mL'])>1e-7:raise ProtocolError('distributed volume mismatch')
    if abs(sum(f)-request['uf_mL'])>1e-7:raise ProtocolError('distributed filtration mismatch')
    before=patient.network['volumes'];incoming=request['draw_mL']+request.get('flush_in_mL',0)
    flows=[]
    for i in range(16):
        incoming+=(request['pre_mL'] if i==2 else request['post_mL'] if i==14 else 0)
        outgoing=incoming-(f[i-2] if 2<=i<14 else 0)-(v[i]-before[i])
        if outgoing < -1e-8:raise ProtocolError('reverse distributed blood flow')
        flows.append(outgoing);incoming=outgoing
    if abs(flows[-1]-request['return_mL']-request['post_mL']-request.get('flush_out_mL',0))>1e-7:raise ProtocolError('distributed outlet mismatch')
    return v,f,flows


def advect_face(matrix, left, right, volume):
    """Implicit donor-cell transfer; positive volume travels right to left.

    The same signed face volume must enter both adjacent cell equations. Internal
    flow reversal during a valve hold is permitted; external ports stay one-way.
    """
    donor, receiver = (right, left) if volume >= 0 else (left, right)
    amount = abs(volume)
    matrix[donor][donor] += amount
    matrix[receiver][donor] -= amount


def solute_balance(patient,request,volumes,refill,dt,incoming,outgoing):
    v,f,flows=topology(patient,request);cfg=patient.config['extracorporeal'];old=patient.network
    network=copy.deepcopy(old);network['volumes']=list(v)
    cs=[[0.0]*6 for _ in range(3)];mass=[[0.0]*6 for _ in range(3)];flux=[]
    d=request['distributed'];qd=d['dialysate_mL_min']*dt
    dv=(cfg['dialysate_volume_mL']+d['dialysate_storage_mL'])/12;old_dv=old['dialysate_volume']/12
    network['dialysate_volume']=dv*12
    if abs(dv*12-old_dv*12-qd-sum(f)+d['dialysate_drain_mL_min']*dt)>1e-6:raise ProtocolError('distributed dialysate water balance')
    draw=request['draw_mL'];returned=request['return_mL']+request['post_mL'];flush=request.get('flush_out_mL',0)
    for s in range(6):
        a=[[0.0]*30 for _ in range(30)];rhs=[0.0]*30
        exchange=patient.config['exchange_mL_min'][s]*dt;reverse=exchange/patient.config['partition'][s]
        ei,ie=max(-refill,0),max(refill,0)
        a[0][0]=volumes[0]+draw+outgoing+exchange+ei;a[0][1]=-reverse-ie;a[0][17]=-returned
        a[1][0]=-exchange-ei;a[1][1]=volumes[1]+reverse+ie
        external=incoming*patient.config['external_mmol_L'][s]+patient.config['generation_mmol_min'][s]*dt*1000
        rhs[0]=patient.mass[0][s]*1000+external;rhs[1]=patient.mass[1][s]*1000
        for i in range(16):
            row=i+2;a[row][row]=v[i]+flows[i]
            if i:a[row][row-1]=-flows[i-1]
            else:a[row][0]=-draw
            rhs[row]=old['volumes'][i]*old['concentration'][i][s]
            if i==0:rhs[row]+=request.get('flush_in_mL',0)*request.get('flush_mmol_L',[0]*6)[s]
            if i in (2,14):rhs[row]+=request['pre_mL' if i==2 else 'post_mL']*request['substitution_mmol_L'][s]
        diffusion=0;convection=0
        # Nominal countercurrent direction is toward segment zero. A valve hold
        # and compliant storage can reverse an INTERNAL face; use its actual
        # donor concentration instead of rejecting a conservative transaction.
        for j in range(12):
            br=j+4;dr=j+18;k=cfg['koa_mL_min'][s]*dt/12 if d['membrane_open'] else 0
            conv=f[j]*request['sieving'][s]
            a[br][br]+=k+conv;a[br][dr]-=k
            a[dr][dr]=dv+k;a[dr][br]=-k-conv
            rhs[dr]=old_dv*old['dialysate'][j][s]
        for face in range(1,12):
            transferred=qd+math.fsum(f[face:])-(12-face)*(dv-old_dv)
            advect_face(a,17+face,18+face,transferred)
        # Port volumes are validated nonnegative; their consistency with storage
        # and filtration is checked above. Neither port is silently reversed.
        a[18][18]+=d['dialysate_drain_mL_min']*dt
        rhs[29]+=qd*request['dialysate_mmol_L'][s]
        result=solve(a,rhs)
        if any(x>1000+1e-9 for x in result):raise ProtocolError('distributed concentration ceiling')
        for i in range(16):network['concentration'][i][s]=result[i+2]
        for j in range(12):
            network['dialysate'][j][s]=result[j+18]
            k=cfg['koa_mL_min'][s]*dt/12 if d['membrane_open'] else 0
            diffusion+=k*(result[j+4]-result[j+18])/1000
            convection+=f[j]*request['sieving'][s]*result[j+4]/1000
        network['dialysate_input'][s]+=qd*request['dialysate_mmol_L'][s]/1000
        network['dialysate_output'][s]+=d['dialysate_drain_mL_min']*dt*result[18]/1000
        network['dialysate_transfer'][s]+=diffusion+convection
        network['dialysate_residual'][s]=math.fsum([*(dv*result[j+18]/1000 for j in range(12)),
            -cfg['dialysate_volume_mL']*cfg['dialysate_mmol_L'][s]/1000,-network['dialysate_input'][s],
            network['dialysate_output'][s],-network['dialysate_transfer'][s]])
        if abs(network['dialysate_residual'][s])>1e-6:raise ProtocolError('dialysate solute conservation')
        cs[0][s]=result[0];cs[1][s]=result[1]
        mass[0][s]=volumes[0]*result[0]/1000;mass[1][s]=volumes[1]*result[1]/1000
        mass[2][s]=math.fsum(v[i]*result[i+2]/1000 for i in range(16));cs[2][s]=mass[2][s]*1000/volumes[2]
        flux.append(dict(input=external/1000,output=outgoing*result[0]/1000,diffusive=diffusion,convective=convection,
            substitution=(request['pre_mL']+request['post_mL'])*request['substitution_mmol_L'][s]/1000,
            flush_input=request.get('flush_in_mL',0)*request.get('flush_mmol_L',[0]*6)[s]/1000,
            flush_output=flush*result[17]/1000))
    return cs,mass,flux,network


def retained(patient,request,vascular,network):
    v,f,flows=topology(patient,request)
    a=[[0.0]*17 for _ in range(17)]
    draw=request['draw_mL'];ret=request['return_mL']+request['post_mL'];waste=request.get('flush_out_mL',0)
    a[0][0]=vascular+draw;a[0][-1]=-ret
    for i in range(16):
        a[i+1][i+1]=v[i]+flows[i]
        a[i+1][i]=-(flows[i-1] if i else draw)
    result=[]
    for name,body in [('cells',patient.cells[0]),('proteins',patient.proteins[0])]:
        concentration=solve(a,[body]+patient.network[name])
        network[name]=[concentration[i+1]*v[i] for i in range(16)]
        result.append(([concentration[0]*vascular,math.fsum(network[name])],waste*concentration[-1]))
    return result


def snapshot(network):
    return dict(compartments=[dict(name=NAMES[i],volume_mL=v,concentration_mmol_L=network['concentration'][i],
        rbc_mL=network['cells'][i],protein_g=network['proteins'][i],hematocrit=network['cells'][i]/v,
        protein_g_dL=100*network['proteins'][i]/(v-network['cells'][i])) for i,v in enumerate(network['volumes'])],
        dialysate_concentration_mmol_L=copy.deepcopy(network['dialysate']),dialysate_volume_mL=network['dialysate_volume'],
        dialysate_input_mmol=list(network['dialysate_input']),dialysate_output_mmol=list(network['dialysate_output']),
        dialysate_transfer_mmol=list(network['dialysate_transfer']),dialysate_residual_mmol=list(network['dialysate_residual']))
