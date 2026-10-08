#!/usr/bin/env python3
"""Record actual static/advisory coverage and findings; absent coverage is never PASS."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def query_osv(item):
    original=item['query'];request=dict(original);seen=set();pages=[];findings={}
    try:
        for _ in range(100):
            raw=json.dumps(request).encode()
            req=urllib.request.Request('https://api.osv.dev/v1/query',data=raw,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=30) as response:
                body=response.read(8*1024*1024+1)
            if len(body)>8*1024*1024:raise ValueError('advisory response limit')
            value=json.loads(body);pages.append(dict(request=request,response_sha256=hashlib.sha256(body).hexdigest(),response=value))
            for entry in value.get('vulns',[]):
                findings[entry['id']]=dict(id=entry['id'],modified=entry['modified'],aliases=entry.get('aliases',[]),
                    withdrawn=entry.get('withdrawn'),severity=entry.get('severity',[]),
                    references=entry.get('references',[]),affected=entry.get('affected',[]))
            token=value.get('next_page_token')
            if not token:break
            if token in seen:raise ValueError('repeated advisory page token')
            seen.add(token);request=dict(original,page_token=token)
        else:raise ValueError('advisory pagination limit; coverage incomplete')
        return dict(**item,status='FINDINGS' if findings else 'NO_REPORTED_MATCHES',findings=list(findings.values()),pages=pages)
    except (OSError,ValueError,KeyError) as exc:
        return dict(**item,status='BLOCKED',error=type(exc).__name__+': '+str(exc),findings=list(findings.values()),pages=pages)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--inventory-dir',type=Path)
    parser.add_argument('--advisories',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=1,executed_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').rglob('*')) if p.is_file()},
        scope='Project C/C++ source warnings/performance/portability; missing external-header semantic coverage is explicit. '
              'OSV database matches are not exploitability analysis, and absence of matches does not prove package coverage or safety.',
        static=None,advisories=None)
    cppcheck=shutil.which('cppcheck')
    if not cppcheck:report['static']=dict(status='BLOCKED',reason='cppcheck executable unavailable')
    else:
        command=[cppcheck,'--enable=warning,performance,portability','--std=c++17','--xml','--xml-version=2',
                 '--error-exitcode=1','-Isrc','-Isrc/ui','-Isrc/console','--suppress=missingIncludeSystem','src']
        try:
            result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=300)
            errors=[dict(e.attrib,locations=[p.attrib for p in e.findall('location')]) for e in ET.fromstring(result.stderr).findall('./errors/error')]
            report['static']=dict(status='FINDINGS' if errors else 'NO_REPORTED_FINDINGS' if result.returncode==0 else 'BLOCKED',
                command=command,version=subprocess.check_output([cppcheck,'--version'],text=True).strip(),
                exit_code=result.returncode,findings=errors,stdout=result.stdout,stderr_xml=result.stderr)
        except (OSError,subprocess.TimeoutExpired,ET.ParseError) as exc:report['static']=dict(status='BLOCKED',error=str(exc))
    if args.advisories:
        if not args.inventory_dir:parser.error('--advisories requires --inventory-dir with actual dependency reports')
        try:
            inventory_report=json.loads((args.inventory_dir/'report.json').read_text())
            if not inventory_report['successful'] or not inventory_report['images']:
                raise ValueError('complete actual container inventory required')
            for name,expected in inventory_report['artifacts'].items():
                if hashlib.sha256((args.inventory_dir/name).read_bytes()).hexdigest()!=expected:
                    raise ValueError('inventory artifact digest mismatch: '+name)
        except (OSError,ValueError,KeyError) as exc:
            report['advisories']=dict(queried_components=0,blocked=1,matching_queries=0,error=str(exc))
            (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            raise SystemExit(3)
        adopted=json.loads((args.inventory_dir/'adopted-dependencies.json').read_text())
        items=[dict(component=x['name'],scope='application',query={'commit':x['commit']}) for x in adopted['application']]
        for tool in adopted['ci_tools']:
            items.append(dict(component=tool['name'],scope='CI-tool',query={'commit':tool['commit']}))
            for item in tool['runtime_packages']:
                items.append(dict(component=item['name'],scope='CI-tool-transitive',
                    query=dict(package={'name':item['name'].rsplit('node_modules/',1)[1],'ecosystem':'npm'},version=item['version'])))
        for inventory in sorted(args.inventory_dir.glob('image-*-platform.json')):
            platform=json.loads(inventory.read_text())
            if 'ID=debian\n' not in platform['os_release'] or 'VERSION_ID="13"' not in platform['os_release']:
                raise ValueError('advisory distro mapping requires reviewed Debian 13 source metadata')
            for package in platform['packages']:
                items.append(dict(component=package['source'],scope=inventory.name,
                    query=dict(package={'name':package['source'],'ecosystem':'Debian:13'},version=package['source_version'])))
            for package in platform.get('python_packages',[]):
                items.append(dict(component=package['name'],scope=inventory.name,
                    query=dict(package={'name':package['name'],'ecosystem':'PyPI'},version=package['version'])))
            items.append(dict(component='CPython',scope=inventory.name,query=dict(
                package={'name':'https://github.com/python/cpython.git','ecosystem':'GIT'},version='v'+platform['python']['version'])))
        unique={}
        for item in items:
            key=json.dumps(item['query'],sort_keys=True)
            if key not in unique:unique[key]=dict(component=item['component'],scopes=[],query=item['query'])
            unique[key]['scopes'].append(item['scope'])
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(query_osv,unique.values()))
        # Raw responses remain local. Public summaries contain identifiers,
        # affected-version facts and upstream references, not advisory prose.
        raw=args.output/'osv-raw.json';raw.write_text(json.dumps(results,indent=2)+'\n')
        for item in results:
            item['pages']=[dict(request=p['request'],response_sha256=p['response_sha256']) for p in item['pages']]
        report['advisories']=dict(queries=results,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
            queried_components=len(results),blocked=sum(x['status']=='BLOCKED' for x in results),
            matching_queries=sum(x['status']=='FINDINGS' for x in results),
            source='https://osv.dev; upstream advisory references retained; imported GitHub advisory data CC-BY-4.0',
            unassessed='Native host packages, kernel/daemon/hosted runner internals and unindexed sources; no reachability proof.')
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'static':report['static']['status'],'advisory_queries':(report['advisories'] or {}).get('queried_components')}))
    if report['static']['status']=='BLOCKED' or (report['advisories'] and report['advisories']['blocked']):raise SystemExit(3)
    if report['static']['status']=='FINDINGS' or (report['advisories'] and report['advisories']['matching_queries']):raise SystemExit(1)


if __name__=='__main__':main()
