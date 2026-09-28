#!/usr/bin/env python3
"""Read-only native PCB / BOM / placement / Gerber / drill / PDF consistency.
Run with bundled KiCad Python. This creates fresh scratch native Gerbers, never
saves/refills the source PCB, and must run after final exports exist.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
WORK=HERE.parent
CLI=WORK/'kicad_runtime/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PDF_PYTHON=WORK/'venv/bin/python'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def readcsv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def refs(text):return [v for v in re.split(r'[,;\s]+',text) if v]
def netlist_signature(path):
    root=ET.parse(path).getroot()
    comps={c.attrib['ref']:{'value':c.findtext('value'),'footprint':c.findtext('footprint'),'mpn':c.findtext('fields/field[@name="MPN"]'),'uuid':c.findtext('tstamps'),'pins':sorted(p.attrib['num']for p in c.findall('units/unit/pins/pin'))}for c in root.findall('components/comp')}
    nets={n.attrib['name']:sorted((p.attrib['ref'],p.attrib['pin'],p.attrib.get('pintype')) for p in n.findall('node'))for n in root.findall('nets/net')}
    return {'components':comps,'nets':nets,'sheet_count':len(root.findall('design/sheet'))}
def clean_gerber(text):
    # Remove only native creation-time comments; all commands/geometry remain.
    return '\n'.join(line for line in text.splitlines() if not line.startswith('%TF.CreationDate,') and not line.startswith('G04 Created by KiCad (PCBNEW '))
def drill_records(path):
    text=path.read_text()
    if not ('METRIC' in text and 'M30' in text and 'absolute / metric / decimal' in text):raise ValueError('Expected native metric decimal absolute Excellon')
    tools={int(a):float(b) for a,b in re.findall(r'^T(\d+)C([0-9.]+)',text,re.M)}
    tool=None;holes=[];x=y=None
    for line in text.splitlines():
        line=line.strip()
        mt=re.fullmatch(r'T(\d+)',line)
        if mt:tool=int(mt.group(1));continue
        if line.startswith(('G85','G00','G01','G02','G03','M15','M16')) or 'G85' in line:raise ValueError('Slots/routed drill commands require explicit review: '+line)
        if line.startswith(('X','Y')):
            mx=re.search(r'X(-?\d+(?:\.\d+)?)',line);my=re.search(r'Y(-?\d+(?:\.\d+)?)',line)
            if mx:x=float(mx.group(1))
            if my:y=float(my.group(1))
            if x is None or y is None or tool not in tools:raise ValueError('Incomplete drill coordinate/tool')
            holes.append((round(tools[tool],3),round(x,3),round(y,3)))
    return Counter(holes)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=HERE/'design_manifest.json')
    ap.add_argument('--project-dir',type=Path,default=HERE/'project')
    ap.add_argument('--output-dir',type=Path,default=HERE/'independent_exports')
    ap.add_argument('--cli',type=Path,default=CLI)
    ap.add_argument('--pdf-python',type=Path,default=PDF_PYTHON)
    ap.add_argument('--retained-mock-dir',type=Path,help='Optional promoted validation directory containing historical132-test evidence')
    args=ap.parse_args();project=args.project_dir.resolve();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    draft=project/'exports/draft';val=project/'validation/design'
    m=json.loads(args.manifest.read_text());stem=m['project'];pcb=project/(stem+'.kicad_pcb');sch=project/(stem+'.kicad_sch')
    expected={p['ref']:p for p in m['parts']};fitted={r:p for r,p in expected.items()if p['mpn']!='PCB_COPPER_FEATURE'};features={r:p for r,p in expected.items()if p['mpn']=='PCB_COPPER_FEATURE'}
    names=['bom_fitted.csv','bom_grouped.csv','bom_testpoints.csv','placement_all.csv','schematic.pdf']
    required=[draft/n for n in names]+[val/'schematic_netlist.xml',pcb,sch,project/(stem+'.kicad_pro')]
    missing=[str(p)for p in required if not p.exists()]
    if missing:
        result={'status':'NOT_RUN','reason':'Required final exports absent','missing':missing}
        (out/'export_consistency.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 2
    tracked=[args.manifest.resolve(),pcb,project/(stem+'.kicad_pro'),project/'fp-lib-table']+sorted(project.glob('*.kicad_sch'))+sorted((project/'libraries').rglob('*.kicad_mod'))+sorted((project/'libraries/3dmodels').rglob('*'))+sorted(p for p in draft.rglob('*')if p.is_file())+[val/'schematic_netlist.xml']
    tracked=list(dict.fromkeys(p for p in tracked if p.is_file()))
    hashes={str(p):sha(p)for p in tracked};errors=[];commands=[]
    def check(ok,category,**details):
        if not ok:errors.append(dict(category=category,**details))
    def run(cmd):
        p=subprocess.run([str(v)for v in cmd],text=True,capture_output=True)
        commands.append({'argv':[str(v)for v in cmd],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});return p
    bom=readcsv(draft/'bom_fitted.csv');grouped=readcsv(draft/'bom_grouped.csv');tp=readcsv(draft/'bom_testpoints.csv');pos=readcsv(draft/'placement_all.csv')
    b={r['Reference']:r for r in bom};t={r['Reference']:r for r in tp};placement={r['Ref']:r for r in pos}
    check(len(b)==len(bom),'duplicate_bom_reference');check(len(t)==len(tp),'duplicate_testpoint_reference');check(len(placement)==len(pos),'duplicate_placement_reference')
    check(set(b)==set(fitted),'fitted_bom_reference_set',missing=sorted(set(fitted)-set(b)),extra=sorted(set(b)-set(fitted)))
    check(set(t)==set(features),'testpoint_bom_reference_set');check(set(placement)==set(fitted),'placement_reference_set',missing=sorted(set(fitted)-set(placement)),extra=sorted(set(placement)-set(fitted)))
    check(len(fitted)==121 and len({p['mpn']for p in fitted.values()})==43,'reviewed_design_inventory',fitted=len(fitted),mpns=len({p['mpn']for p in fitted.values()}))
    saved_netlist=netlist_signature(val/'schematic_netlist.xml');comps=saved_netlist['components']
    check(set(comps)==set(expected),'exported_netlist_reference_set');check(saved_netlist['sheet_count']==7,'native_sheet_count',actual=saved_netlist['sheet_count'])
    fresh=out/'fresh_schematic.net.xml';rc=run([args.cli,'sch','export','netlist','--format','kicadxml','-o',fresh,sch])
    check(rc.returncode==0 and fresh.exists(),'fresh_netlist_export')
    if fresh.exists():check(saved_netlist==netlist_signature(fresh),'saved_netlist_stale_or_different')
    for ref,p in fitted.items():
        row=b.get(ref);comp=comps.get(ref);position=placement.get(ref)
        if row is None:continue
        want={'MPN':p['mpn'],'Value_from_manifest':p['value'],'Footprint':p['footprint'],'Package':p['footprint'].split(':',1)[1],'Quantity_per_board':'1'}
        for k,v in want.items():check(row.get(k)==v,'bom_field',ref=ref,field=k,actual=row.get(k),expected=v)
        check('DRAFT' in row.get('Release_status','')and'NOT RELEASED' in row.get('Release_status',''),'bom_release_status',ref=ref)
        check(bool(row.get('Manufacturer'))and row.get('Source_URL','').startswith('https://'),'bom_source_metadata',ref=ref)
        if comp:check(comp['value']==p['value']and comp['footprint']==p['footprint']and comp['mpn']==p['mpn'],'bom_native_netlist_fields',ref=ref)
        if position:check(position['Val']==p['value']and position['Package']==p['footprint'].split(':',1)[1],'placement_value_package',ref=ref)
    grouped_refs=[]
    for row in grouped:
        rr=refs(row['References']);grouped_refs+=rr
        check(int(row['Quantity_per_board'])==len(rr),'grouped_quantity',references=rr)
        for ref in rr:
            original=b.get(ref)
            check(original is not None,'grouped_unknown_reference',ref=ref)
            if original:
                for field in ['MPN','Manufacturer','Footprint','Package','Mount','Category']:
                    check(row[field]==original[field],'grouped_bom_field',ref=ref,field=field)
        expected_aliases={b[ref]['Value_from_manifest']for ref in rr if ref in b}
        check(set(row['Value_from_manifest'].split(' | '))==expected_aliases,'grouped_value_alias_set',references=rr,actual=row['Value_from_manifest'],expected=sorted(expected_aliases))
    check(Counter(grouped_refs)==Counter({r:1 for r in fitted}),'grouped_reference_multiplicity')
    for ref,p in features.items():
        row=t.get(ref)
        if row:check(row['Purchased_quantity']=='0'and row['PCB_feature_quantity']=='1'and row['MPN']=='PCB_COPPER_FEATURE'and row['Footprint']==p['footprint']and row['Net']==p['pins'][0]['net'],'copper_feature_record',ref=ref)

    import wx
    app=wx.App(False);quiet=wx.LogNull()
    import pcbnew as pn
    board=pn.LoadBoard(str(pcb));fps={fp.GetReference():fp for fp in board.GetFootprints()};origin=board.GetDesignSettings().GetAuxOrigin();ox,oy=pn.ToMM(origin.x),pn.ToMM(origin.y)
    check(abs(ox-50)<1e-6 and abs(oy-150)<1e-6,'native_aux_origin',actual=[ox,oy])
    edges=[v for v in board.GetDrawings()if v.GetLayer()==pn.Edge_Cuts]
    endpoints=[]
    for e in edges:
        check(e.GetShape()==pn.SHAPE_T_SEGMENT,'outline_nonsegment')
        endpoints += [(round(pn.ToMM(e.GetStart().x),6),round(pn.ToMM(e.GetStart().y),6)),(round(pn.ToMM(e.GetEnd().x),6),round(pn.ToMM(e.GetEnd().y),6))]
    check(len(edges)==4 and Counter(endpoints)==Counter({(50.,50.):2,(150.,50.):2,(150.,150.):2,(50.,150.):2}),'100x100_closed_rectangle',endpoints=endpoints)
    model_rows=[];all_model_paths=[]
    for ref,p in fitted.items():
        fp=fps.get(ref);check(fp is not None,'fitted_pcb_missing',ref=ref)
        if fp is None:continue
        check(fp.GetValue()==p['value']and fp.GetFPIDAsString()==p['footprint']and fp.GetFieldText('MPN')==p['mpn'],'pcb_bom_identity',ref=ref)
        check(not fp.IsExcludedFromBOM()and not fp.IsExcludedFromPosFiles(),'fitted_exclusion',ref=ref)
        position=placement.get(ref)
        if position:
            actual=[float(position[x])for x in ['PosX','PosY','Rot']];xy=fp.GetPosition();want=[pn.ToMM(xy.x)-ox,oy-pn.ToMM(xy.y),fp.GetOrientationDegrees()]
            check(abs(actual[0]-want[0])<1e-5 and abs(actual[1]-want[1])<1e-5 and abs((actual[2]-want[2]+180)%360-180)<1e-5,'placement_native_coordinates',ref=ref,actual=actual,expected=want)
            check(position['Side']==('bottom'if fp.IsFlipped()else'top'),'placement_native_side',ref=ref)
            check(0<=actual[0]<=100 and 0<=actual[1]<=100,'placement_outside_outline',ref=ref)
        models=list(fp.Models());check(len(models)==1,'fitted_model_binding_count',ref=ref,count=len(models))
        lib,name=p['footprint'].split(':',1)
        library_fp=pn.FootprintLoad(str(project/'libraries'/(lib+'.pretty')),name)
        check(library_fp is not None,'local_library_footprint_load',ref=ref)
        def model_signature(model):
            return (str(model.m_Filename),bool(model.m_Show),tuple(round(float(v),9)for v in [model.m_Scale.x,model.m_Scale.y,model.m_Scale.z,model.m_Offset.x,model.m_Offset.y,model.m_Offset.z,model.m_Rotation.x,model.m_Rotation.y,model.m_Rotation.z]))
        if library_fp is not None:
            check(Counter(model_signature(v)for v in models)==Counter(model_signature(v)for v in library_fp.Models()),'embedded_vs_library_model_bindings',ref=ref)
        for model in models:
            path=str(model.m_Filename);all_model_paths.append(path);portable=path.startswith('${KIPRJMOD}/')
            resolved=project/path[len('${KIPRJMOD}/'):]if portable else Path(path)
            check(portable and resolved.is_file(),'model_missing_nonportable',ref=ref,path=path)
            check(model.m_Show,'model_hidden',ref=ref,path=path)
            check(all(float(v)>0 for v in [model.m_Scale.x,model.m_Scale.y,model.m_Scale.z]),'model_nonpositive_scale',ref=ref)
            model_rows.append({'ref':ref,'path':path,'exists':resolved.is_file(),'sha256':sha(resolved)if resolved.is_file()else None,'shown':bool(model.m_Show),'scale':[model.m_Scale.x,model.m_Scale.y,model.m_Scale.z],'offset':[model.m_Offset.x,model.m_Offset.y,model.m_Offset.z],'rotation':[model.m_Rotation.x,model.m_Rotation.y,model.m_Rotation.z]})
    # Native manufacturing holes: derive from every physical drilled pad/via.
    native_holes={'PTH':Counter(),'NPTH':Counter()};hole_detail=[]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            d=pad.GetDrillSize()
            if not d.x and not d.y:continue
            check(d.x==d.y,'unsupported_slotted_pad',ref=fp.GetReference(),pin=pad.GetNumber(),drill=[d.x,d.y])
            typ='NPTH'if pad.GetAttribute()==pn.PAD_ATTRIB_NPTH else'PTH';p=pad.GetPosition();key=(round(pn.ToMM(d.x),3),round(pn.ToMM(p.x)-ox,6),round(oy-pn.ToMM(p.y),6));native_holes[typ][key]+=1
            hole_detail.append({'kind':typ,'source':'pad','ref':fp.GetReference(),'pin':pad.GetNumber(),'diameter_x_y_mm':list(key)})
    for via in board.GetTracks():
        if via.GetClass()!='PCB_VIA':continue
        p=via.GetPosition();key=(round(pn.ToMM(via.GetDrillValue()),3),round(pn.ToMM(p.x)-ox,6),round(oy-pn.ToMM(p.y),6));native_holes['PTH'][key]+=1;hole_detail.append({'kind':'PTH','source':'via','uuid':via.m_Uuid.AsString(),'diameter_x_y_mm':list(key)})
    drills={}
    for typ in ['PTH','NPTH']:
        path=draft/'drills'/(stem+'-'+typ+'.drl');check(path.exists(),'drill_missing',kind=typ)
        if not path.exists():continue
        try: exported=drill_records(path)
        except Exception as exc:check(False,'drill_parse',kind=typ,reason=str(exc));continue
        # Excellon decimal metric output has 0.001mm coordinate resolution.
        # Compare native nanometre coordinates before rounding, one-to-one, to
        # half that resolution; Python banker's rounding need not match C++.
        coordinate_decimals=re.findall(r'[XY]-?\d+\.(\d+)',path.read_text())
        # KiCad omits trailing zeros: e.g. the NPTH file only needs X4.6.
        # Decimal metric format and at most three digits are required; the
        # one-to-one geometry check below still enforces 0.0005 mm tolerance.
        check('METRIC' in path.read_text() and '/ metric / decimal}' in path.read_text()
              and bool(coordinate_decimals) and max(map(len,coordinate_decimals))<=3,
              'drill_coordinate_decimal_precision',kind=typ)
        unmatched=list(exported.elements());missing=[];maximum_error=0.0
        for expected_hole in native_holes[typ].elements():
            candidates=[(max(abs(actual_hole[1]-expected_hole[1]),abs(actual_hole[2]-expected_hole[2])),i)for i,actual_hole in enumerate(unmatched)if abs(actual_hole[0]-expected_hole[0])<1e-6 and abs(actual_hole[1]-expected_hole[1])<=.00050001 and abs(actual_hole[2]-expected_hole[2])<=.00050001]
            if not candidates:missing.append(expected_hole)
            else:
                error,index=min(candidates);maximum_error=max(maximum_error,error);unmatched.pop(index)
        check(not missing and not unmatched,'drill_native_geometry',kind=typ,missing=missing,extra=unmatched)

        drills[typ]={'native_count':sum(native_holes[typ].values()),'export_count':sum(exported.values()),'pad_count':sum(x['kind']==typ and x['source']=='pad'for x in hole_detail),'via_count':sum(x['kind']==typ and x['source']=='via'for x in hole_detail),'sha256':sha(path),'coordinate_resolution_mm':.001,'maximum_axis_rounding_error_mm':maximum_error,'matching':'one-to-one within half native export coordinate resolution'}
    check(len(list((draft/'drills').glob('*.drl')))==2,'drill_file_set')

    required_layers={'.gtl':'Copper,L1,Top','.gbl':'Copper,L2,Bot','.gtp':'Paste,Top','.gts':'Soldermask,Top','.gbs':'Soldermask,Bot','.gto':'Legend,Top','.gbo':'Legend,Bot','.gm1':'Profile,NP'}
    gerbers=[p for p in(draft/'gerbers').iterdir()if p.suffix.lower()in required_layers]
    check(len(gerbers)==8 and {p.suffix.lower()for p in gerbers}==set(required_layers),'gerber_layer_set',actual=[p.name for p in gerbers])
    freshgerber=out/'fresh_gerbers';freshgerber.mkdir(exist_ok=True)
    # Fresh export to scratch establishes geometry identity, not just syntactic completeness.
    gr=run([args.cli,'pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts','--use-drill-file-origin','-o',str(freshgerber)+'/',pcb])
    check(gr.returncode==0,'fresh_gerber_export')
    gerber_rows=[]
    for p in gerbers:
        text=p.read_text();func=required_layers[p.suffix.lower()];other=freshgerber/p.name
        check('%MOMM*%'in text and 'M02*'in text and ('%TF.FileFunction,'+func)in text,'gerber_header_end_layer',file=p.name,expected_function=func)
        check(other.exists(),'fresh_gerber_missing',file=p.name)
        matches=other.exists()and clean_gerber(text)==clean_gerber(other.read_text());check(matches,'gerber_native_fresh_geometry',file=p.name)
        gerber_rows.append({'file':p.name,'file_function':func,'sha256':sha(p),'matches_fresh_native_export_except_creation_time':matches})
    pdf_code='''import pymupdf as fitz
import json,sys,re
from pathlib import Path
p=Path(sys.argv[1]);d=fitz.open(p);pages=[]
for page in d:
 t=page.get_text();pages.append({'page':page.number+1,'width_pt':page.rect.width,'height_pt':page.rect.height,'text_chars':len(t),'references':sorted(set(re.findall(r'(?<![A-Za-z0-9_])(?:C|R|U|J|Q|D|F|SW|TP)\\d+(?![A-Za-z0-9_])',t)))})
print(json.dumps({'pages':pages,'page_count':len(d),'encrypted':d.is_encrypted}))
'''
    pdfrun=run([args.pdf_python,'-c',pdf_code,draft/'schematic.pdf']);pdf=None
    check(pdfrun.returncode==0,'schematic_pdf_parse')
    if pdfrun.returncode==0:
        pdf=json.loads(pdfrun.stdout);check(pdf['page_count']==7 and not pdf['encrypted'],'schematic_pdf_page_count',actual=pdf['page_count'])
        found=set(v for page in pdf['pages']for v in page['references']);check(set(expected)<=found,'schematic_pdf_missing_references',missing=sorted(set(expected)-found))
        check(all(page['text_chars']>100 for page in pdf['pages']),'schematic_pdf_empty_page')
    retained={'status':'NOT_CHECKED','reason':'Supply --retained-mock-dir after promotion; no historical evidence is generated or altered.'}
    if args.retained_mock_dir:
        fixed={'software_test_report.md':'ba52e1a29b1bbdef4f2432df6b0ea7b43c350fd1529ff60e16fccd07312ffaf3','mock_tests.junit.xml':'db5a70a947769df63656d36b0bc726911738cb661d2122e831d8d5e0c567b473'}
        retained={name:{'exists':(args.retained_mock_dir/name).exists(),'sha256':sha(args.retained_mock_dir/name)if(args.retained_mock_dir/name).exists()else None,'expected_sha256':h}for name,h in fixed.items()}
        for name,item in retained.items():check(item['sha256']==item['expected_sha256'],'historical_mock_report_changed',file=name)
    changed=[str(p)for p in tracked if not p.exists()or sha(p)!=hashes[str(p)]];check(not changed,'inputs_changed_during_audit',files=changed)
    result={'date':datetime.now(timezone.utc).isoformat(),'status':'PASS'if not errors else'FAIL','scope':'Digital native/export consistency only; no visual approval, production release, model fit or physical validation','versions':{'pcbnew':pn.GetBuildVersion()},'counts':{'manifest':len(expected),'fitted_bom':len(bom),'unique_fitted_mpns':len({r['MPN']for r in bom}),'grouped_rows':len(grouped),'copper_features':len(tp),'placement':len(pos),'fitted_model_bindings':len(model_rows),'unique_model_paths':len(set(all_model_paths))},'outline_mm':[100,100],'native_aux_origin_mm':[ox,oy],'placement_convention':'X right, Y up from native PCB (50,150) mm; rotations reconciled to pcbnew','drills':drills,'native_drilled_features':hole_detail,'models':model_rows,'gerbers':gerber_rows,'schematic_pdf':pdf,'preserved_mock_evidence':retained,'input_sha256':hashes,'errors':errors,'limits':['PDF check covers7 readable pages and manifest reference presence, not visual layout or graphical circuit correctness.','Model paths/existence/transforms are checked; nominal model geometry and mechanical fit need visual/manufacturer review.','Fresh Gerber comparison ignores creation-time comment lines only; no source copper was refilled or modified.','Drill counts and every diameter/coordinate are derived from current native pads/vias, not old-board totals. Slots are explicitly rejected pending a slot-aware audit.','This report does not evaluate procurement availability, assembly vendor acceptance, thermal behavior or current capacity.']}
    (out/'export_consistency.json').write_text(json.dumps(result,indent=2)+'\n');(out/'command_log.json').write_text(json.dumps(commands,indent=2)+'\n')
    markdown=['# Independent 12 V export consistency review','',result['date'],'',f"**{result['status']}** — digital artifact consistency; no fabrication release.",'',f"Inventory: {len(bom)} fitted references, {result['counts']['unique_fitted_mpns']} fitted MPNs, {len(tp)} copper features, {len(pos)} placement rows, {len(model_rows)} fitted model bindings.",'',f"Board:100×100 mm centerline outline; native export origin ({ox},{oy}) mm. Every placement coordinate, rotation and side is compared to pcbnew.",'',f"Actual drill inventory: `{json.dumps(drills,sort_keys=True)}`.",'',f"Gerbers: {len(gerber_rows)} layers checked against fresh native exports. Schematic PDF: {pdf['page_count'] if pdf else 'unreadable'} pages.",'','## Limits','']+['- '+v for v in result['limits']]+['','## Findings','']
    markdown+=['- None within these checks.']if not errors else['- `'+json.dumps(e,sort_keys=True)+'`'for e in errors]
    (out/'export_consistency.md').write_text('\n'.join(markdown)+'\n');print(json.dumps({k:result[k]for k in ['status','counts','drills']},indent=2));print('Errors:',len(errors),'Report:',out/'export_consistency.json');return int(bool(errors))

if __name__=='__main__':sys.exit(main())
