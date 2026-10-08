#!/usr/bin/env python3
"""Check adopted dependency metadata and generate a deterministic CycloneDX 1.6 SBOM."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from dialysislab.runner import build_identity
from build_identity import source_hashes

BINARY_NAMES=('plant','control','protection','child-guard','device-ui','sim-console')


def validate_image_application(actual,expected):
    if actual.get('schema_version')!=1 or actual['build']['source_sha256']!=expected:
        raise ValueError('stale/mismatched image application build inputs')
    binaries=actual['binary_sha256']
    if not set(BINARY_NAMES[:4])<=set(binaries) or set(binaries)-set(BINARY_NAMES):
        raise ValueError('image application binary set')
    if ('device-ui' in binaries)!=('sim-console' in binaries):raise ValueError('incomplete image GUI profile')
    if any(not re.fullmatch('[0-9a-f]{64}',value) for value in binaries.values()):raise ValueError('binary identity')
    runtime={k:v for k,v in expected.items() if k.startswith(('python/dialysislab/','scenarios/'))}
    if 'device-ui' in binaries:runtime['gui_dependencies.json']=expected['gui_dependencies.json']
    if actual['runtime_source_sha256']!=runtime:raise ValueError('image runtime files differ from declared build')
    return actual['build']


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root):
    data=json.loads((root/'dependency_inventory.json').read_text())
    lock=json.loads((root/'gui_dependencies.json').read_text())
    if data['schema_version']!=1 or data['profile']!=lock['profile']: raise ValueError('inventory schema/profile')
    if len(data['application'])!=len(lock['components']): raise ValueError('unrecorded application dependency')
    preferred={'MIT','BSD-2-Clause','BSD-3-Clause','Apache-2.0','Zlib'}
    for actual,declared in zip(lock['components'],data['application']):
        for field in ('name','version','commit','sha256','url','license'):
            if actual[field]!=declared[field]: raise ValueError('dependency inventory mismatch: '+field)
        if not re.fullmatch('[0-9a-f]{40}',actual['commit']) or not re.fullmatch('[0-9a-f]{64}',actual['sha256']):
            raise ValueError('dependency must have immutable identity')
        if not actual['url'].startswith('https://'): raise ValueError('dependency requires TLS')
        if set(actual['license'].split(' AND '))-preferred: raise ValueError('unreviewed application license')
        if not declared['consumers'] or not (root/declared['notices']).is_file():raise ValueError('missing consumer/notices')
    for item in data['embedded']:
        if item['license'] not in preferred or not (root/item['notices']).is_file():raise ValueError('embedded license/notices')
    for name,expected in data['reviewed_files'].items():
        if digest(root/name)!=expected: raise ValueError('reviewed dependency file changed: '+name)
    workflow=(root/'.github/workflows/verify.yaml').read_text()
    actions=re.findall(r'uses:\s*([^\s#]+)',workflow)
    expected=[t['name']+'@'+t['commit'] for t in data['ci_tools']]
    if any(action not in expected for action in actions) or set(actions)!=set(expected):
        raise ValueError('unreviewed/unpinned CI action')
    for tool in data['ci_tools']:
        if not re.fullmatch('[0-9a-f]{40}',tool['commit']):raise ValueError('CI commit')
        for package in tool['runtime_packages']:
            if package['license'] not in ('MIT','ISC','Apache-2.0') or not package['integrity'].startswith('sha512-'):
                raise ValueError('unassessed CI transitive dependency')
    docker=(root/'Dockerfile').read_text()
    for base in re.findall(r'^FROM\s+(\S+)',docker,re.M):
        if base not in ('build','runtime') and not re.fullmatch(r'python@sha256:[0-9a-f]{64}',base):
            raise ValueError('unpinned container source')
        if base not in ('build','runtime') and base!=data['container_profile']['base']:
            raise ValueError('container base differs from assessed inventory')
    if data['container_profile']['snapshot'] not in docker:raise ValueError('container snapshot mismatch')
    for name,version in data['container_profile']['tool_pins'].items():
        if name+'='+version not in docker:raise ValueError('container package pin missing: '+name)
    return data


def component(name,version,kind='library',license=None,sha=None,properties=None):
    result={'type':kind,'bom-ref':name,'name':name,'version':version}
    if license:result['licenses']=[{'expression':license}]
    if sha:result['hashes']=[{'alg':'SHA-256','content':sha}]
    if properties:result['properties']=[{'name':k,'value':str(v)} for k,v in sorted(properties.items())]
    return result


def application_bom(data,identity,build_dir=None,binary_hashes=None,runtime_hashes=None):
    if binary_hashes is None:
        binary_hashes={name:digest(build_dir/name) for name in BINARY_NAMES if (build_dir/name).is_file()}
    if runtime_hashes is None:
        runtime_hashes={k:v for k,v in identity['source_sha256'].items() if k.startswith('python/dialysislab/')}
    project=component('DialysisLab',identity['source_revision'],'application','MIT')
    components=[];dependencies=[]
    active=[item for item in data['application'] if any(name in binary_hashes for name in item['consumers'])]
    for item in active:
        components.append(component(item['name'],item['version'],license=item['license'],sha=item['sha256'],
            properties={'dialysislab:commit':item['commit'],'dialysislab:archive':item['url'],
                        'dialysislab:notice':item['notices']}))
        dependencies.append({'ref':item['name'],'dependsOn':[e['name'] for e in data['embedded'] if e['parent']==item['name']]})
    for item in data['embedded']:
        if item['parent'] not in [p['name'] for p in active]: continue
        components.append(component(item['name'],item['version'],kind='library',license=item['license'],
                                    properties={'dialysislab:parent':item['parent'],'dialysislab:notice':item['notices']}))
    for item in data['project_assets']:
        if 'device-ui' not in binary_hashes:continue
        components.append(component(item['name'],identity['source_revision'],kind='file',license=item['license'],sha=identity['source_sha256'][item['path']]))
    for name in BINARY_NAMES:
        if name in binary_hashes:
            uses=[x['name'] for x in data['application'] if name in x['consumers']]
            licenses={'MIT'}
            for item in data['application']:
                if item['name'] in uses: licenses.update(item['license'].split(' AND '))
            components.append(component('binary:'+name,identity['source_revision'],'application',' AND '.join(sorted(licenses)),binary_hashes[name]))
            if name=='device-ui':uses += [a['name'] for a in data['project_assets']]
            dependencies.append({'ref':'binary:'+name,'dependsOn':uses})
    for name,sha in sorted(runtime_hashes.items()):
        if name.startswith('python/dialysislab/'):
            components.append(component('module:'+name,identity['source_revision'],'file','MIT',sha))
    dependencies.append({'ref':'DialysisLab','dependsOn':[c['bom-ref'] for c in components if c['name'].startswith(('binary:','module:'))]})
    return dict(bomFormat='CycloneDX',specVersion='1.6',version=1,metadata={'component':project},
                components=components,dependencies=dependencies,
                properties=[{'name':'dialysislab:scope','value':'Selected application and built executable identities; platform/CI tools separately inventoried, not complete image license clearance.'},
                            {'name':'dialysislab:build-sha256','value':hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()}])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--images',nargs='*',default=[])
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    data=check(ROOT);identity=build_identity(args.build_dir);expected=source_hashes(ROOT)
    if identity['source_sha256']!=expected:raise ValueError('native build inputs are stale; reconfigure/rebuild')
    def write(name,value):
        (args.output/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    write('application.cdx.json',application_bom(data,identity,args.build_dir))
    write('build.json',identity);write('adopted-dependencies.json',data)
    script=(ROOT/'tools/platform_inventory.py').read_text()
    write('native-platform.json',json.loads(subprocess.check_output([sys.executable,'-c',script],text=True)))
    images=[]
    for index,name in enumerate(args.images):
        inspected=json.loads(subprocess.check_output(['docker','image','inspect',name],text=True))[0]
        # Inventory by immutable actual image ID, never by a tag that could move.
        command=['docker','run','--rm','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',inspected['Id'],'python3','-','--python-packages']
        platform=json.loads(subprocess.check_output(command,input=script,text=True))
        actual=json.loads(subprocess.check_output(command,input=(ROOT/'tools/image_application.py').read_text(),text=True))
        image_identity=validate_image_application(actual,expected)
        build_filename='image-'+str(index)+'-build.json';write(build_filename,actual)
        app_filename='image-'+str(index)+'-application.cdx.json'
        app=application_bom(data,image_identity,binary_hashes=actual['binary_sha256'],runtime_hashes=actual['runtime_source_sha256'])
        app['properties'] += [{'name':'dialysislab:image-id','value':inspected['Id']},
                              {'name':'dialysislab:image-build-record','value':build_filename}]
        write(app_filename,app)
        filename='image-'+str(index)+'-platform.json';write(filename,platform)
        packages=[component('deb:'+p['name'],p['version'],properties={'dialysislab:source-package':p['source'],
                    'dialysislab:source-version':p['source_version'],'dialysislab:copyright-record':filename}) for p in platform['packages']]
        packages.append(component('CPython',platform['python']['version'],sha=platform['python']['sha256'],properties={'dialysislab:license-assessment':platform['python']['license']}))
        for package in platform['python_packages']:
            packages.append(component('python:'+package['name'],package['version'],properties={'dialysislab:license-assessment':package['license'] or 'not declared'}))
        bom=dict(bomFormat='CycloneDX',specVersion='1.6',version=1,
                 metadata={'component':component(name,inspected['Id'],'container')},components=packages+[app['metadata']['component']]+app['components'],
                 dependencies=app['dependencies']+[{'ref':'module:'+p,'dependsOn':['CPython']} for p in actual['runtime_source_sha256'] if p.startswith('python/dialysislab/')],
                 properties=[{'name':'dialysislab:scope','value':'Actual immutable-image application binary/module hashes, declared build inputs and installed OS/interpreter. Build metadata is not a signed attestation; copyright labels do not establish complete image redistribution clearance.'},
                             {'name':'dialysislab:application-sbom','value':app_filename},
                             {'name':'dialysislab:application-sbom-sha256','value':digest(args.output/app_filename)}])
        write('image-'+str(index)+'.cdx.json',bom)
        images.append(dict(name=name,id=inspected['Id'],repo_digests=inspected['RepoDigests'],inventory=filename,application=app_filename,build=build_filename))
    write('report.json',dict(schema_version=1,successful=True,command=sys.argv,images=images,
                            artifacts={p.name:digest(p) for p in sorted(args.output.glob('*.json'))}))
    print(json.dumps({'successful':True,'application_components':len(application_bom(data,identity,args.build_dir)['components']),'images':len(images)}))


if __name__=='__main__':main()
