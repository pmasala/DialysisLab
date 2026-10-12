"""Reproducible, explicitly limited calibration of the 12-cell transport law."""
from .distributed import solve


def clearance(koa, blood, dialysate, segments=12):
    """Steady zero-UF limit of the production finite-volume exchange equations.

    Unit inlet concentration, solute-free dialysate; no patient or protein model.
    """
    if not (0<koa<=5000 and 0<blood<=1000 and 0<dialysate<=1000 and 2<=segments<=96):
        raise ValueError('clearance benchmark domain')
    a=[[0.0]*(2*segments) for _ in range(2*segments)];rhs=[0.0]*(2*segments)
    k=koa/segments
    for j in range(segments):
        a[j][j]=blood+k;a[j][segments+j]=-k
        if j:a[j][j-1]=-blood
        else:rhs[j]=blood
        a[segments+j][segments+j]=dialysate+k;a[segments+j][j]=-k
        if j+1<segments:a[segments+j][segments+j+1]=-dialysate
    return blood*(1-solve(a,rhs)[segments-1])


def fit(profile):
    target=profile['fit_clearance_mL_min'];blood=profile['fit_blood_mL_min'];qd=profile['dialysate_mL_min']
    low,high=.001,5000
    if not clearance(low,blood,qd)<=target<=clearance(high,blood,qd):raise ValueError('reference outside model range')
    for _ in range(48):
        mid=(low+high)/2
        if clearance(mid,blood,qd)<target:low=mid
        else:high=mid
    koa=(low+high)/2
    predicted=clearance(koa,profile['holdout_blood_mL_min'],qd)
    error=(predicted-profile['holdout_clearance_mL_min'])/profile['holdout_clearance_mL_min']
    return dict(id=profile['id'],effective_urea_koa_mL_min=koa,fit_clearance_mL_min=clearance(koa,blood,qd),
        holdout_prediction_mL_min=predicted,holdout_relative_error=error,
        criterion_relative_error=.05,accepted=abs(error)<=.05,
        status='limited-in-vitro-transport-fit',segments=12,
        uncalibrated=['blood rheology','needle/access resistance','gas actuator','dialysate controller',
                      'electrolyte-specific KoA','conductivity','vascular refill','patient response'])
