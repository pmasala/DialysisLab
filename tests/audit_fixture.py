"""Actual plant/patient pipe harness; does not establish RPC/container isolation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from dialysislab import circuit,treatment,machine,physical
from dialysislab.compartments import Compartments
from dialysislab.protocol import expect


def compile_driver(directory):
    binary=Path(directory)/'audit-plant'
    subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'tests/guided_plant.cpp'),'-o',str(binary)],check=True,capture_output=True,timeout=90)
    return binary


class Coupled:
    def __init__(self,binary,config):
        self.config=copy.deepcopy(config);self.sequence=0;self.time=0;self.snapshot=None;self.stage='SELF_TEST';self.record=None;self.saved={}
        self.process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            with patch.object(circuit,'rpc',side_effect=self.call),patch.object(treatment,'rpc',side_effect=self.call),patch.object(machine,'rpc',side_effect=self.call),patch.object(physical,'rpc',side_effect=self.call):
                circuit.configure(0,config);treatment.configure(0,config);machine.configure(0,config)
            self.patient=Compartments(physical.patient_configuration(config),True,True)
        except BaseException:
            self.close(check=False);raise

    def call(self,role,*fields):
        self.process.stdin.write(str(role)+' DL1 '+' '.join(str(x) for x in fields)+'\n');self.process.stdin.flush()
        line=self.process.stdout.readline().strip().split()
        if not line or line[0]!='DL1' or 'DRIVER_ERROR' in line:raise ValueError('plant driver: '+repr(line))
        return line[1:]

    def save(self,key):
        expect(self.call(4,key),'OK',1)
        self.saved[key]=copy.deepcopy((self.sequence,self.time,self.snapshot,self.stage,self.record,self.patient))

    def restore(self,key):
        expect(self.call(5,key),'OK',1)
        self.sequence,self.time,self.snapshot,self.stage,self.record,self.patient=copy.deepcopy(self.saved[key])

    def step(self,action=None,rx=None,mask=None,faults=('none','none'),auto=True):
        c=self.config;n=self.sequence;t=self.time;dt=c['dt_ms']
        if self.snapshot:
            with patch.object(physical,'rpc',side_effect=self.call):physical.update_blood(0,self.snapshot)
        expect(self.call(0,'PREPARE',n,t,dt,c['resistance_mmHg_min_mL'],*faults),'OK',1)
        if action is None and auto:
            action={'PREPARATION':'PRIME','CONFIGURATION':'CONNECT','CONNECTED':'START','FINISHED':'RETURN','DISCONNECTING':'DISCONNECT','DISCONNECTED':'CLEAN'}.get(self.stage)
        if action:expect(self.call(1,'CHANGE5',n,t,action),'OK',1)
        if rx:expect(self.call(1,'RX5',n,t,*rx),'OK',1)
        if mask is None:expect(self.call(3,n,t),'OK',1)
        else:
            expect(self.call(1,'DEMAND5',n,t,300,140,120),'OK',1)
            expect(self.call(2,'PROTECT5',n,t,mask,1),'OK',1)
        record=machine.committed(self.call(0,'COMMIT5',n,t));m=record['machine'];g=m['guided'];h=record['circuit'];o=record['online']
        rinse=bool(g['return_in_tick_mL'] or g['return_out_tick_mL'])
        request=dict(sequence=n,time_ms=t,dt_ms=dt,draw_mL=h['draw_tick_mL']-m['flush_in_tick_mL'],return_mL=h['return_tick_mL']-m['flush_out_tick_mL'],uf_mL=h['uf_tick_mL'],stored_mL=h['stored_mL'],clearance_mL_min=h['clearance_mL_min'],sieving=c['circuit']['profile']['sieving'],dialysate_mmol_L=o['concentration_mmol_L'],pre_mL=o['pre_tick_mL'],post_mL=o['post_tick_mL'],substitution_mmol_L=o['concentration_mmol_L'],flush_in_mL=m['flush_in_tick_mL'],flush_out_mL=m['flush_out_tick_mL'],flush_mmol_L=[0,154,0,154,0,0] if rinse else o['concentration_mmol_L'],rinseback=rinse)
        physical.attach_transaction(request,record,c)
        self.snapshot=self.patient.advance(request);record['patient']=self.snapshot
        physical.verify_record(record,c)
        self.sequence+=1;self.time+=dt;self.stage=m['stage'];self.record=record
        return record

    def close(self,check=True):
        p=self.process
        if p.stdin and not p.stdin.closed:p.stdin.close()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait()
        if p.stdout:p.stdout.close()
        errors=p.stderr.read() if p.stderr else ''
        if p.stderr:p.stderr.close()
        if check and p.returncode:raise RuntimeError('plant process failed: '+errors)
