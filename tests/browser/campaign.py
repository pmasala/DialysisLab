"""Shared prospective portability experiment, executed by CPython and Pyodide."""
import copy
import json
from dialysislab.browser import BrowserSession


def campaign(config, transport, reset, emit):
    epoch='0123456789abcdef0123456789abcdef'
    for mode in ('HD','HDF_PRE','HDF_POST'):
        reset(epoch)
        c=copy.deepcopy(config);c['workflow']=[]
        c['treatment'].update(mode=mode,replacement_mL_min=0 if mode=='HD' else 60)
        s=BrowserSession(c,transport,epoch)
        assert s.command(0,'START','f'*32)=='rejected_old_session'
        stages=set()
        for i in range(2200):
            if s.record:
                stage=s.record['machine']['stage']
                action={'PREPARATION':'PRIME','CONFIGURATION':'CONNECT','CONNECTED':'START','FINISHED':'RETURN','DISCONNECTING':'DISCONNECT','DISCONNECTED':'CLEAN'}.get(stage)
                if action:assert s.command(0,action,epoch)=='queued'
            record=s.step();stages.add(record['machine']['stage'])
            assert record['machine']['alarm_mask']==0
            assert max(map(abs,record['patient']['mass_residual_mmol']))<=1e-6
            prep=record['physical']['preparation']
            assert abs(prep['water_residual_mL'])<=1e-6
            assert max(map(abs,prep['mass_residual_mmol']))<=1e-6
            emit(json.dumps(dict(mode=mode,tick=i,record=record),allow_nan=False,separators=(',',':')))
            if record['machine']['stage']=='CLEANED':break
        assert {'SELF_TEST','PRIMING','TREATMENT','RETURNING','CLEANED'}<=stages
        assert record['machine']['stage']=='CLEANED'
        assert s.command(0,'STOP',epoch)=='acknowledged'
        from dialysislab import machine
        view=machine.view(['VIEW5',*s.views()[0].split()[3:]])
        assert view['machine']['stage']=='STOPPED'
