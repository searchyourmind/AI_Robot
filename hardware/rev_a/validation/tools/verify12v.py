#!/usr/bin/env python3
"""Independent read-only manifest / native netlist / pcbnew verifier for Rev A 12 V.
Run with bundled KiCad Python (wx + pcbnew), not the generic authoring venv.
All output is written beneath --output-dir; native inputs are never saved/filled.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
CLI = WORK / 'kicad_runtime/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sexp(text):
    toks = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)
    stack, out = [], []
    for tok in toks:
        if tok == '(':
            node = []
            (stack[-1] if stack else out).append(node)
            stack.append(node)
        elif tok == ')':
            stack.pop()
        else:
            stack[-1].append(json.loads(tok) if tok.startswith('"') else tok)
    return out[0]

def children(node, tag):
    return [v for v in node if isinstance(v, list) and v and v[0] == tag]

def first(node, tag):
    return children(node, tag)[0][1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, default=HERE / 'design_manifest.json')
    ap.add_argument('--project-dir', type=Path, default=HERE / 'project')
    ap.add_argument('--output-dir', type=Path, default=HERE / 'independent_verification')
    ap.add_argument('--cli', type=Path, default=CLI)
    ap.add_argument('--stage', choices=['placement', 'routed'], default='routed')
    args = ap.parse_args()
    project, out = args.project_dir.resolve(), args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    m = json.loads(args.manifest.read_text())
    stem = m['project']
    sch, pcb, pro = (project / (stem + suffix) for suffix in ['.kicad_sch', '.kicad_pcb', '.kicad_pro'])
    tracked = [args.manifest.resolve(), pcb, pro, project / 'fp-lib-table', project / 'sym-lib-table']
    tracked += sorted(project.glob('*.kicad_sch'))
    tracked += sorted((project / 'libraries').rglob('*.kicad_sym'))
    tracked += sorted((project / 'libraries').rglob('*.kicad_mod'))
    before = {str(p): digest(p) for p in tracked}
    errors, commands = [], []
    def check(ok, category, **details):
        if not ok:
            errors.append(dict(category=category, **details))
    def run(cmd):
        p = subprocess.run([str(v) for v in cmd], capture_output=True, text=True)
        commands.append(dict(argv=[str(v) for v in cmd], exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr))
        return p.returncode
    xml_path = out / 'schematic_native.net.xml'
    rc = run([args.cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', xml_path, sch])
    if rc or not xml_path.exists():
        (out / 'command_log.json').write_text(json.dumps(commands, indent=2) + '\n')
        raise RuntimeError('Native netlist export failed; see command_log.json')
    root = ET.parse(xml_path).getroot()
    part_list = m['parts']
    expected = {p['ref']: p for p in part_list}
    check(len(expected) == len(part_list), 'duplicate_manifest_reference')
    components = {c.attrib['ref']: c for c in root.findall('components/comp')}
    check(len(components) == len(root.findall('components/comp')), 'duplicate_schematic_reference')
    check(set(components) == set(expected), 'schematic_reference_set', missing=sorted(set(expected)-set(components)), extra=sorted(set(components)-set(expected)))
    libparts = {(p.attrib['lib'], p.attrib['part']): p for p in root.findall('libparts/libpart')}
    xmlpins, xmlnets, logical = {}, {}, {}
    for net in root.findall('nets/net'):
        name = net.attrib['name']
        nodes = net.findall('node')
        members = {(n.attrib['ref'], n.attrib['pin']) for n in nodes}
        check(len(members) == len(nodes), 'duplicate_node_in_net', net=name)
        xmlnets[name] = members
        for n in nodes:
            key = (n.attrib['ref'], n.attrib['pin'])
            check(key not in xmlpins, 'multiple_nets_on_schematic_pin', pin=key)
            xmlpins[key] = (name, n.attrib.get('pinfunction'), n.attrib.get('pintype'))
    expected_netsets = defaultdict(set)
    nc, pins_review = [], []
    for ref, p in expected.items():
        c = components.get(ref)
        if c is None:
            continue
        for field in ('value', 'footprint'):
            check(c.findtext(field) == p[field], 'schematic_' + field, ref=ref, expected=p[field], actual=c.findtext(field))
        mpn = c.find('fields/field[@name="MPN"]')
        check(mpn is not None and mpn.text == p['mpn'], 'schematic_mpn', ref=ref)
        check(c.findtext('tstamps') == p['uuid'], 'schematic_uuid', ref=ref)
        is_feature = p['mpn'] == 'PCB_COPPER_FEATURE'
        check((c.find('property[@name="exclude_from_bom"]') is not None) == is_feature, 'schematic_bom_exclusion', ref=ref)
        pp = {str(x['number']): x for x in p['pins']}
        check(len(pp) == len(p['pins']), 'duplicate_manifest_pin', ref=ref)
        exported = [x.attrib['num'] for x in c.findall('units/unit/pins/pin')]
        check(set(exported) == set(pp) and len(exported) == len(pp), 'schematic_package_pin_set', ref=ref, actual=exported, expected=sorted(pp))
        ls = c.find('libsource')
        lp = libparts.get((ls.attrib['lib'], ls.attrib['part'])) if ls is not None else None
        libpins = {x.attrib['num']: x.attrib for x in lp.findall('pins/pin')} if lp is not None else {}
        check(set(libpins) == set(pp), 'symbol_library_pin_set', ref=ref)
        for number, pin in pp.items():
            key, found = (ref, number), xmlpins.get((ref, number))
            check(found is not None, 'missing_schematic_pin_net', pin=key)
            lp = libpins.get(number, {})
            check(lp.get('name') == pin['name'] and lp.get('type') == pin['type'], 'symbol_pin_name_type', pin=key, expected=[pin['name'], pin['type']], actual=lp)
            if found is None:
                continue
            name, function, pintype = found
            # KiCad 10's node pinfunction appends _<number> to the library
            # name. The raw library pin name is checked independently above.
            check(function in (pin['name'], pin['name'] + '_' + number) and pintype.split('+')[0] == pin['type'], 'schematic_pin_name_type', pin=key, actual=found)
            if pin['net'] is None:
                nc.append(key)
                check(name.startswith('unconnected-') and xmlnets[name] == {key} and 'no_connect' in pintype.split('+'), 'explicit_nc_isolation', pin=key, actual=found)
                logical[key] = None
            else:
                expected_netsets[pin['net']].add(key)
                check(name == pin['net'], 'schematic_pin_net', pin=key, expected=pin['net'], actual=name)
                check('no_connect' not in pintype.split('+'), 'connected_pin_marked_nc', pin=key)
                logical[key] = name
            pins_review.append(dict(ref=ref, pin=number, name=pin['name'], type=pin['type'], manifest_net=pin['net'], schematic_net=name))
    expected_keys = {(r, str(pin['number'])) for r, p in expected.items() for pin in p['pins']}
    check(set(xmlpins) == expected_keys, 'complete_schematic_pin_coverage', missing=sorted(expected_keys-set(xmlpins)), extra=sorted(set(xmlpins)-expected_keys))
    for name, members in expected_netsets.items():
        check(xmlnets.get(name) == members, 'entire_schematic_net_membership', net=name)
    check(set(xmlnets) == set(expected_netsets) | {xmlpins[k][0] for k in nc}, 'schematic_net_set')

    import wx
    app = wx.App(False)
    quiet = wx.LogNull()
    import pcbnew as pn
    board = pn.LoadBoard(str(pcb))
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    fps = defaultdict(list)
    for fp in board.GetFootprints():
        fps[fp.GetReference()].append(fp)
    check(all(len(v) == 1 for v in fps.values()), 'duplicate_pcb_reference')
    check(set(expected) <= set(fps), 'missing_pcb_references', missing=sorted(set(expected)-set(fps)))
    extras = sorted(set(fps)-set(expected))
    for ref in extras:
        fp = fps[ref][0]
        check(re.fullmatch(r'H[1-4]', ref) is not None and fp.IsExcludedFromBOM() and fp.IsExcludedFromPosFiles() and fp.IsBoardOnly(), 'unapproved_board_only_component', ref=ref)
        check(all(not pad.GetNetCode() and pad.GetAttribute() == pn.PAD_ATTRIB_NPTH for pad in fp.Pads()), 'board_only_electrical_pad', ref=ref)
    check(set(extras) == {'H1','H2','H3','H4'}, 'mechanical_reference_set', actual=extras)
    table = sexp((project / 'fp-lib-table').read_text())
    libraries = {first(v, 'name'): Path(first(v, 'uri').replace('${KIPRJMOD}', str(project))) for v in children(table, 'lib')}
    def pad_geometry(pad):
        pos, size, drill = pad.GetFPRelativePosition(), pad.GetSize(), pad.GetDrillSize()
        return (pad.GetNumber(), int(pos.x), int(pos.y), round(pad.GetFPRelativeOrientation().AsDegrees() % 360, 6), int(size.x), int(size.y), int(drill.x), int(drill.y), int(pad.GetAttribute()), int(pad.GetShape()), int(pad.GetDrillShape()), tuple(pad.GetLayerSet().Seq()), round(pad.GetRoundRectRadiusRatio(), 9))
    pads_by_key, boardnets, library_checks, repeated = defaultdict(list), defaultdict(set), [], []
    physical_numbered = 0
    for ref, p in expected.items():
        if ref not in fps:
            continue
        fp = fps[ref][0]
        c = components.get(ref)
        check(fp.GetValue() == p['value'], 'pcb_value', ref=ref, actual=fp.GetValue())
        check(fp.GetFPIDAsString() == p['footprint'], 'pcb_footprint_id', ref=ref, actual=fp.GetFPIDAsString())
        check(fp.GetFieldText('MPN') == p['mpn'], 'pcb_mpn', ref=ref, actual=fp.GetFieldText('MPN'))
        if c is not None:
            sheet = c.find('sheetpath').attrib['tstamps'].strip('/')
            fullpath = '/' + '/'.join(v for v in [m['root_uuid'], sheet, p['uuid']] if v)
            check(fp.GetPath().AsString() == fullpath, 'pcb_hierarchy_uuid', ref=ref, actual=fp.GetPath().AsString(), expected=fullpath)
        feature = p['mpn'] == 'PCB_COPPER_FEATURE'
        check(fp.IsExcludedFromBOM() == feature and fp.IsExcludedFromPosFiles() == feature, 'pcb_bom_position_exclusion', ref=ref)
        check(not fp.IsBoardOnly(), 'electrical_part_marked_board_only', ref=ref)
        check(not fp.IsFlipped(), 'unreviewed_bottom_placement', ref=ref)
        lib, name = p['footprint'].split(':', 1)
        libpath = libraries.get(lib)
        file = libpath / (name + '.kicad_mod') if libpath else None
        check(file is not None and file.exists(), 'footprint_library_missing', ref=ref, path=str(file))
        if file is not None and file.exists():
            lf = pn.FootprintLoad(str(libpath), name)
            check(lf is not None, 'footprint_native_load', ref=ref)
            if lf is not None:
                actual_geo = Counter(pad_geometry(x) for x in fp.Pads())
                lib_geo = Counter(pad_geometry(x) for x in lf.Pads())
                check(actual_geo == lib_geo, 'embedded_vs_library_pad_geometry', ref=ref, board_only=list((actual_geo-lib_geo).elements()), library_only=list((lib_geo-actual_geo).elements()))
                library_checks.append(dict(ref=ref, footprint=p['footprint'], sha256=digest(file), physical_pads=sum(actual_geo.values()), geometry_equal=actual_geo == lib_geo))
        numbers = Counter()
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                check(not pad.GetNetCode(), 'unnumbered_pad_has_net', ref=ref, net=pad.GetNetname())
                continue
            numbers[num] += 1
            physical_numbered += 1
            key = (ref, num)
            pads_by_key[key].append(pad)
            boardnets[pad.GetNetname()].add(key)
            check(key in xmlpins and pad.GetNetname() == xmlpins[key][0], 'pcb_pad_net', pin=key, actual=pad.GetNetname(), expected=xmlpins.get(key))
        check(set(numbers) == {str(x['number']) for x in p['pins']}, 'pcb_logical_pad_set', ref=ref, actual=sorted(numbers))
        for num, count in numbers.items():
            if count > 1:
                repeated.append(dict(ref=ref, pin=num, physical_pad_count=count, net=[pad.GetNetname() for pad in pads_by_key[(ref,num)]]))
    check(set(pads_by_key) == expected_keys, 'complete_pcb_pin_coverage', missing=sorted(expected_keys-set(pads_by_key)), extra=sorted(set(pads_by_key)-expected_keys))
    for name, members in xmlnets.items():
        check(boardnets.get(name) == members, 'entire_pcb_net_membership', net=name, missing=sorted(members-boardnets.get(name,set())), extra=sorted(boardnets.get(name,set())-members))
    nc_review = []
    for key in nc:
        attached = []
        for pad in pads_by_key.get(key, []):
            for item in connectivity.GetConnectedTracks(pad):
                attached.append(item.m_Uuid.AsString())
            for other in connectivity.GetConnectedPads(pad):
                if (other.GetParentFootprint().GetReference(), other.GetNumber()) != key:
                    attached.append('pad:' + other.GetParentFootprint().GetReference() + '.' + other.GetNumber())
        name = xmlpins[key][0]
        assigned = [t.m_Uuid.AsString() for t in board.GetTracks() if t.GetNetname() == name]
        zones = [z.m_Uuid.AsString() for z in board.Zones() if z.GetNetname() == name]
        check(not attached and not assigned and not zones, 'nc_has_copper_connections', pin=key, attached=attached, assigned_tracks_vias=assigned, assigned_zones=zones)
        nc_review.append(dict(ref=key[0], pin=key[1], net=name, connected_items=attached, assigned_tracks_vias=assigned, assigned_zones=zones))
    for row in pins_review:
        row['pcb_physical_pad_count'] = len(pads_by_key.get((row['ref'],row['pin']), []))
        row['pcb_nets'] = [p.GetNetname() for p in pads_by_key.get((row['ref'],row['pin']), [])]

    # Deliberately independent, design-specific assertions beyond agreement of files.
    schematic_map = {key: (None if key in nc else v[0]) for key,v in xmlpins.items()}
    pcb_map = {key: (None if key in nc else pads[0].GetNetname()) for key,pads in pads_by_key.items()}
    manifest_map = {(ref,str(x['number'])):x['net'] for ref,p in expected.items() for x in p['pins']}
    logic_results = []
    for source, pinmap in [('manifest',manifest_map),('native_schematic',schematic_map),('native_pcb',pcb_map)]:
        def nets(ref):
            return {int(num):v for (r,num),v in pinmap.items() if r==ref}
        def required(ref, mapping):
            actual = nets(ref)
            for number, name in mapping.items():
                check(actual.get(number, '__missing__') == name, 'logic_connection_constraint', source=source, ref=ref, pin=number, expected=name, actual=actual.get(number,'__missing__'))
        required('U4',{1:'PI_3V3',2:'WD_SELECT',3:'LOGIC_GOOD',4:'GND',5:'PI_3V3',6:'HB',7:'WD_RAW',8:'WD_RAW',9:'GND'})
        required('U5',{1:'ARM_PULSE',2:'PI_3V3',3:None,4:'GND',5:'ARM_Q',6:'ALL_OK',7:'PI_3V3',8:'PI_3V3'})
        required('U6',{1:'LOGIC_GOOD',2:'PHYS_OK',13:'FAULT_OK',12:'RAILS_OK',3:'RAILS_OK',4:'WD_OK',5:'RUN_REQ',6:'ALL_OK',9:'ARM_Q',10:'ALL_OK',11:'PI_3V3',8:'DRIVE_ENABLE_CMD',7:'GND',14:'PI_3V3'})
        required('U14',{1:'LOGIC_GOOD',2:'PHYS_OK',3:'GND',4:'FEED_ENABLE',5:'PI_3V3'})
        required('U13',{1:'EFUSE_IN',2:'EFUSE_IN',3:'EFUSE_BGATE',4:'EFUSE_DRV',5:'FUSED_IN',6:'EFUSE_UV',7:'EFUSE_OV',8:'GND',9:'EFUSE_DVDT',10:'EFUSE_ILIM',11:None,12:'EFUSE_SHDN',13:None,14:'FAULT_OK_RAW',15:'EFUSE_PG_SENSE',16:'FAULT_OK_RAW',17:'VM',18:'VM',19:None,20:None,21:None,22:None,23:None,24:None,25:'GND'})
        required('Q1',{1:'FUSED_IN',2:'FUSED_IN',3:'FUSED_IN',4:'EFUSE_BGATE',5:'EFUSE_IN',6:'EFUSE_IN',7:'EFUSE_IN',8:'EFUSE_IN'})
        required('Q2',{1:'EFUSE_DRV',2:'FUSED_IN',3:'EFUSE_BGATE'})
        required('U11',{1:'FAULT_OK_RAW',6:'FAULT_OK_RAW',2:'GND',5:'PI_3V3'})
        required('R45',{1:'VM',2:'EFUSE_PG_SENSE'})
        required('R46',{1:'EFUSE_PG_SENSE',2:'GND'})
        required('R11',{1:'FEED_ENABLE',2:'EFUSE_SHDN'})
        required('R12',{1:'EFUSE_SHDN',2:'GND'})
        required('J6',{1:'PI_3V3',2:'GND',3:'GPIO18',4:'GND',5:'GPIO23',6:None,7:'GPIO13',8:'GND',9:'GPIO5',10:None,11:'GPIO25',12:'GPIO17',13:'GPIO27',14:'GND',15:'GND',16:'GND'})
        for ref,wheel,left in [('U20','FL',True),('U21','FR',False),('U22','BL',True),('U23','BR',False)]:
            side='LEFT' if left else 'RIGHT'
            required(ref,{1:side+'_IN1',2:side+'_IN2',3:'FEED_ENABLE',4:'FAULT_OK_RAW',5:wheel+'_VREF',6:wheel+'_IPROPI',7:None,8:wheel+'_OUT1',9:'GND',10:wheel+'_OUT2',11:'VM',12:wheel+'_VCP',13:wheel+'_CPH',14:wheel+'_CPL',15:'GND',16:'PI_3V3',17:'GND'})
            i = int(ref[1:]) - 20
            cb, rb = 20 + 5*i, 20 + 4*i
            for offset, pair in enumerate([('VM','GND'),('VM','GND'),(wheel+'_VCP','VM'),(wheel+'_CPH',wheel+'_CPL'),(wheel+'_VREF','GND')]):
                required('C'+str(cb+offset),{1:pair[0],2:pair[1]})
            for offset, pair in enumerate([('PI_3V3',wheel+'_VREF'),(wheel+'_VREF','GND'),(wheel+'_IPROPI','GND'),('FEED_ENABLE','GND')]):
                required('R'+str(rb+offset),{1:pair[0],2:pair[1]})
            required('J'+str(2+i),{1:wheel+'_OUT1',2:wheel+'_OUT2'})
        passed=0
        for a,pl,dl,pr,dr in itertools.product([False,True],repeat=5):
            values={'GND':False,'PI_3V3':True,'DRIVE_ENABLE_CMD':a,'PWM_A_RAW':pl,'AIN1_RAW':dl,'PWM_B_RAW':pr,'BIN1_RAW':dr}
            for _ in range(4):
                for ref in ['U15','U16','U3']:
                    n=nets(ref)
                    tuples=[(1,6),(3,4)] if ref=='U15' else [(1,2,3),(4,5,6),(9,10,8),(12,13,11)]
                    for spec in tuples:
                        inputs=[n.get(p) for p in spec[:-1]]
                        if all(net in values for net in inputs):
                            result=all(values[net] for net in inputs)
                            values[n.get(spec[-1])]=not result if ref in ['U15','U16'] else result
            for ref,left in [('U20',True),('U21',False),('U22',True),('U23',False)]:
                p,d=(pl,dl) if left else (pr,dr)
                want=(False,False) if not a else ((True,True) if not p else ((True,False) if d else (False,True)))
                n=nets(ref); got=(values.get(n.get(1)),values.get(n.get(2)))
                check(got==want,'decoder_truth_table',source=source,ref=ref,case=[a,pl,dl,pr,dr],expected=want,actual=got)
                passed += int(got==want)
        logic_results.append(dict(source=source, cases=32, driver_input_pairs=128, matching_pairs=passed))
    for ref,mpn in {'U3':'SN74LVC08APWR','U15':'SN74LVC2G14DBVR','U16':'SN74LVC132APWR', **{r:'DRV8874PWPR' for r in ['U20','U21','U22','U23']}}.items():
        check(expected.get(ref,{}).get('mpn')==mpn,'logic_part_identity',ref=ref,expected=mpn)

    tracks=list(board.GetTracks())
    routing=dict(stage=args.stage, track_segments=sum(t.GetClass()=='PCB_TRACK' for t in tracks), vias=sum(t.GetClass()=='PCB_VIA' for t in tracks), zones=len(list(board.Zones())), native_connectivity_unconnected=int(connectivity.GetUnconnectedCount(False)))
    drc=None
    if args.stage=='routed':
        drc_path=out/'native_drc.json'
        rc=run([args.cli,'pcb','drc','--format','json','--schematic-parity','--severity-all','--exit-code-violations','-o',drc_path,pcb])
        check(drc_path.exists(),'native_drc_report_missing',exit_code=rc)
        if drc_path.exists():
            drc=json.loads(drc_path.read_text())
            counts={k:len(drc.get(k,[])) for k in ['violations','unconnected_items','schematic_parity']}
            routing['native_drc_counts']=counts
            check(rc==0 and all(v==0 for v in counts.values()),'native_routed_drc',exit_code=rc,counts=counts)
        check(routing['native_connectivity_unconnected']==0,'native_unconnected_count',actual=routing['native_connectivity_unconnected'])
    else:
        routing['routing_verdict']='NOT EVALUATED: placement-only check; no routed connectivity approval'
    proj=json.loads(pro.read_text())
    severities=proj.get('board',{}).get('design_settings',{}).get('rule_severities',{})
    ignored={k:v for k,v in severities.items() if v=='ignore'}
    exclusions=proj.get('board',{}).get('design_settings',{}).get('drc_exclusions',[])
    if args.stage=='routed':
        check(not ignored,'ignored_drc_rule_classes',actual=ignored)
        check(not exclusions,'drc_exclusions',actual=exclusions)
    changed=[str(p) for p in tracked if not p.exists() or digest(p)!=before[str(p)]]
    check(not changed,'inputs_changed_during_audit',paths=changed)
    report=dict(date=datetime.now(timezone.utc).isoformat(), kind='Read-only native-file consistency and Boolean desk review; not electrical/thermal/physical validation', stage=args.stage,status='PASS' if not errors else 'FAIL', versions=dict(pcbnew=pn.GetBuildVersion(),schematic_export=root.findtext('design/tool')), counts=dict(manifest_parts=len(expected), schematic_parts=len(components), pcb_electrical_footprints=len(set(fps)&set(expected)), pcb_mechanical_footprints=len(extras), logical_pins=len(expected_keys), physical_numbered_pads=physical_numbered, connected_nets=len(expected_netsets), explicit_nc_pins=len(nc), footprint_library_checks=len(library_checks)), routing=routing, ignored_drc_rule_classes=ignored,drc_exclusions=exclusions, logic=logic_results, repeated_pad_numbers=repeated, intentional_nc=nc_review, footprint_libraries=library_checks, all_pins=pins_review, errors=errors, input_sha256=before, native_netlist_sha256=digest(xml_path), limitations=['Matching files can share the same design error; explicit circuit assertions are bounded to documented architecture.','No analog/timing/SPICE simulation, motor test, thermal measurement or mechanical-fit approval.','Geometry comparison includes numbered and unnamed pads with shape/position/size/rotation/layers/drill/roundrect data, not manufacturer land-pattern certification.','No copper width/current-capacity or thermal-area approval is implied by this consistency check.'])
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'command_log.json').write_text(json.dumps(commands,indent=2)+'\n')
    text=['# Independent 12 V native consistency review','',report['date'],'',f"**{report['status']} — {args.stage} stage.** Read-only checks; native inputs were not saved, refilled or edited.",'',f"Compared {len(expected)} manifest/schematic electrical components, {len(expected_keys)} logical pins, {physical_numbered} physical numbered pads and {len(nc)} intentional NCs. PCB has {len(extras)} separately checked mechanical holes. Resolved {len(library_checks)} local footprint instances and compared all physical pad geometry, preserving repeated EP/drain pad numbers.",'',f"Boolean checks: 32 input cases / 128 driver outcomes independently evaluated from each of manifest, native XML and PCB pad nets. Normal PWM off-time brakes; cleared permission coasts. Latch, independent wake, watchdog/fault chain, power-good output sensing, driver mode and duplicate power-pin constraints checked.",'',f"Routing: `{json.dumps(routing,sort_keys=True)}`",'',f"Ignored DRC classes: `{json.dumps(ignored)}`. DRC exclusions: `{json.dumps(exclusions)}`.",'','## Limits','']+['- '+v for v in report['limitations']]+['','## Evidence','','`verification.json` contains every compared pin, NC, repeated pad and input hash. `schematic_native.net.xml` was freshly exported by KiCad. `command_log.json` contains exact commands and exits; routed mode also creates `native_drc.json`.','','## Findings','']
    text+=['- None within the checks above.'] if not errors else ['- `'+json.dumps(e,sort_keys=True)+'`' for e in errors]
    (out/'verification.md').write_text('\n'.join(text)+'\n')
    print(json.dumps({k:report[k] for k in ['status','stage','counts','routing','logic']},indent=2))
    print('Errors:',len(errors),'Report:',out/'verification.json')
    return 1 if errors else 0

if __name__=='__main__':
    sys.exit(main())
