#!/usr/bin/env python3
"""Read-only native plated-hole/paste intersection and selective process map.
Native KiCad Python extracts true transformed polygons with <=1um chord error;
the separate authoring venv performs polygon intersections. No CAD is saved.
"""
import argparse,csv,hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classify(args):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    data=json.loads(args.geometry.read_text())
    def shape(polys):return unary_union([Polygon(p['outer'],p['holes'])for p in polys])
    paste=[(a,shape(a['polygons']))for a in data['paste_apertures']]
    under=[];clear=[]
    for hole in data['plated_holes']:
        hg=shape(hole['polygons']);hits=[];mindist=None
        for ap,pg in paste:
            if not set(hole['board_layers']).intersection(ap['board_layers']):continue
            area=hg.intersection(pg).area;dist=hg.distance(pg)
            if mindist is None or dist<mindist:mindist=dist
            if area>1e-10:
                hits.append({'paste_ref':ap['ref'],'paste_pad_number':ap['pad_number'],'paste_uuid':ap['uuid'],'layer':ap['layer'],'intersection_mm2':round(area,9),'hole_area_fraction':round(area/hg.area,7)})
        record={k:v for k,v in hole.items()if k!='polygons'}
        record['paste_intersections']=hits
        if hits:
            record['required_process']='Filled, capped and planarized; material, cap and planarity subject to later qualified vendor agreement'
            under.append(record)
        else:
            record['distance_to_nearest_paste_mm']=round(mindist,6)if mindist is not None else None
            clear.append(record)
    under.sort(key=lambda x:(x['ref'],x['native_y_mm'],x['native_x_mm']))
    drv=[v for v in clear if v['ref']in ['U20','U21','U22','U23']and v['pad_number']=='17']
    errors=list(data['extraction_errors'])
    if len(drv)!=16:errors.append({'driver_thermal_holes_outside_paste':len(drv),'expected':16})
    u13=[v for v in under if v['ref']=='U13'and v['pad_number']=='25']
    if len(u13)!=4:errors.append({'u13_thermal_holes_under_paste':len(u13),'expected':4})
    refs=sorted(set(h['paste_ref']for v in under for h in v['paste_intersections']))
    report={'date':datetime.now(timezone.utc).isoformat(),'status':'PASS_PROCESS_MAP_REQUIRED'if not errors else'FAIL','scope':'Geometric manufacturing-process allocation, not fabrication authorization or process qualification','source_pcb':data['source_pcb'],'source_pcb_sha256':data['source_pcb_sha256'],'native_version':data['native_version'],'method':'Native PAD.TransformShapeToPolygon on actual F.Paste/B.Paste pad apertures with zero effective paste margin; native TransformHoleToPolygon for drilled pads and polygonized via drill circles; true polygon area intersection rather than center/bounding-box test. Native1um outside chord bound; via256-segment circle. Non-pad paste graphics or nonzero margins fail extraction for explicit review.','paste_aperture_count':len(paste),'plated_hole_count':len(data['plated_holes']),'selective_fill_count':len(under),'u13_thermal_holes_under_paste':len(u13),'driver_thermal_holes_outside_paste':len(drv),'driver_minimum_hole_to_paste_distance_mm':min(v['distance_to_nearest_paste_mm']for v in drv)if drv else None,'affected_component_references':refs,'selected_holes':under,'other_plated_holes':clear,'errors':errors,'requirements':['All selected holes require filled/capped/planarized treatment; ordinary via tenting alone does not fulfill this selected process.','The CSV is a coordinate map keyed to the PCB SHA-256. The Gerbers and Excellon files alone do not specify material/cap/planarity acceptance.','U20–U23 thermal holes remain outside paste and use the separately specified tented process.','The fabricator/assembler must approve material, plating/cap thickness, finish, planarity, cleaning and inspection before later release.','Additional process complexity and cost are unquoted; fabrication, assembly and physical testing remain deferred.']}
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'selective_via_fill_review.json').write_text(json.dumps(report,indent=2)+'\n')
    fields=['Feature_type','Reference','Pad_number','Net','UUID','Native_X_mm','Native_Y_mm','Export_X_mm','Export_Y_mm','Drill_X_mm','Drill_Y_mm','Board_layers','Paste_layer','Paste_references','Paste_aperture_UUIDs','Required_process','Source_PCB_SHA256']
    with(args.output_dir/'selective_via_fill_map.csv').open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=fields,quoting=csv.QUOTE_ALL);w.writeheader()
        for v in under:
            w.writerow({'Feature_type':v['feature_type'],'Reference':v['ref'],'Pad_number':v['pad_number'],'Net':v['net'],'UUID':v['uuid'],'Native_X_mm':v['native_x_mm'],'Native_Y_mm':v['native_y_mm'],'Export_X_mm':v['export_x_mm'],'Export_Y_mm':v['export_y_mm'],'Drill_X_mm':v['drill_x_mm'],'Drill_Y_mm':v['drill_y_mm'],'Board_layers':','.join(v['board_layers']),'Paste_layer':','.join(sorted(set(h['layer']for h in v['paste_intersections']))),'Paste_references':','.join(sorted(set(h['paste_ref']+'.'+(h['paste_pad_number']or'(aperture)')for h in v['paste_intersections']))),'Paste_aperture_UUIDs':','.join(h['paste_uuid']for h in v['paste_intersections']),'Required_process':v['required_process'],'Source_PCB_SHA256':data['source_pcb_sha256']})
    print(json.dumps({k:report[k]for k in ['status','paste_aperture_count','plated_hole_count','selective_fill_count','u13_thermal_holes_under_paste','driver_thermal_holes_outside_paste','driver_minimum_hole_to_paste_distance_mm','affected_component_references','errors']},indent=2));return int(bool(errors))

def extract(args):
    import math
    import wx
    app=wx.App(False);quiet=wx.LogNull()
    import pcbnew as p
    pcb=args.project_dir/'ai_robot_interface.kicad_pcb';before=hashfile(pcb);b=p.LoadBoard(str(pcb));origin=b.GetDesignSettings().GetAuxOrigin();errors=[];paste=[];holes=[]
    def mm(v):return p.ToMM(v)
    def chain(c):return [[mm(c.CPoint(i).x),mm(c.CPoint(i).y)]for i in range(c.PointCount())]
    def polygons(poly):return [{'outer':chain(poly.COutline(i)),'holes':[chain(poly.CHole(i,j))for j in range(poly.HoleCount(i))]}for i in range(poly.OutlineCount())]
    for fp in b.GetFootprints():
        for gi in fp.GraphicalItems():
            if gi.GetLayer()in[p.F_Paste,p.B_Paste]:errors.append({'unsupported_paste_graphic':fp.GetReference(),'uuid':gi.m_Uuid.AsString()})
        for pad in fp.Pads():
            for layer in[p.F_Paste,p.B_Paste]:
                if not pad.IsOnLayer(layer):continue
                margin=pad.GetSolderPasteMargin(layer)
                if margin.x or margin.y:errors.append({'nonzero_paste_margin':fp.GetReference(),'pin':pad.GetNumber(),'margin_nm':[margin.x,margin.y]})
                poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(.001),p.ERROR_OUTSIDE)
                paste.append({'ref':fp.GetReference(),'pad_number':pad.GetNumber(),'uuid':pad.m_Uuid.AsString(),'layer':b.GetLayerName(layer),'board_layers':['F.Cu'if layer==p.F_Paste else'B.Cu'],'polygons':polygons(poly)})
            d=pad.GetDrillSize()
            if not(d.x or d.y)or pad.GetAttribute()==p.PAD_ATTRIB_NPTH:continue
            poly=p.SHAPE_POLY_SET();pad.TransformHoleToPolygon(poly,0,p.FromMM(.001),p.ERROR_OUTSIDE);pos=pad.GetPosition()
            holes.append({'feature_type':'plated_component_or_thermal_pad','ref':fp.GetReference(),'pad_number':pad.GetNumber(),'net':pad.GetNetname(),'uuid':pad.m_Uuid.AsString(),'native_x_mm':mm(pos.x),'native_y_mm':mm(pos.y),'export_x_mm':mm(pos.x-origin.x),'export_y_mm':mm(origin.y-pos.y),'drill_x_mm':mm(d.x),'drill_y_mm':mm(d.y),'board_layers':[b.GetLayerName(l)for l in[p.F_Cu,p.B_Cu]if pad.IsOnLayer(l)],'polygons':polygons(poly)})
    for gi in b.GetDrawings():
        if gi.GetLayer()in[p.F_Paste,p.B_Paste]:errors.append({'unsupported_board_paste_graphic':gi.m_Uuid.AsString()})
    for zone in b.Zones():
        if zone.IsOnLayer(p.F_Paste)or zone.IsOnLayer(p.B_Paste):errors.append({'unsupported_paste_zone':zone.m_Uuid.AsString()})
    for via in b.GetTracks():
        if via.GetClass()!='PCB_VIA':continue
        pos=via.GetPosition();x,y=mm(pos.x),mm(pos.y);d=mm(via.GetDrillValue());poly={'outer':[[x+(d/2)*math.cos(2*math.pi*i/256),y+(d/2)*math.sin(2*math.pi*i/256)]for i in range(256)],'holes':[]}
        holes.append({'feature_type':'routed_via','ref':'(via)','pad_number':'','net':via.GetNetname(),'uuid':via.m_Uuid.AsString(),'native_x_mm':x,'native_y_mm':y,'export_x_mm':mm(pos.x-origin.x),'export_y_mm':mm(origin.y-pos.y),'drill_x_mm':d,'drill_y_mm':d,'board_layers':[b.GetLayerName(l)for l in[p.F_Cu,p.B_Cu]if via.IsOnLayer(l)],'polygons':[poly]})
    if before!=hashfile(pcb):errors.append({'source_changed_during_extraction':True})
    data={'source_pcb':str(pcb.resolve()),'source_pcb_sha256':before,'native_version':p.GetBuildVersion(),'extraction_errors':errors,'paste_apertures':paste,'plated_holes':holes}
    args.output_dir.mkdir(parents=True,exist_ok=True);geometry=args.output_dir/'native_hole_paste_geometry.json';geometry.write_text(json.dumps(data,indent=2)+'\n')
    r=subprocess.run([str(args.geometry_python),str(Path(__file__).resolve()),'--classify','--geometry',str(geometry),'--output-dir',str(args.output_dir)],text=True,capture_output=True)
    (args.output_dir/'selective_fill_command_log.json').write_text(json.dumps({'argv':r.args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n');print(r.stdout);print(r.stderr,file=sys.stderr);return r.returncode

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project-dir',type=Path,default=HERE/'project');ap.add_argument('--output-dir',type=Path,default=HERE/'selective_fill_preflight');ap.add_argument('--geometry-python',type=Path,default=HERE.parent/'venv/bin/python');ap.add_argument('--classify',action='store_true');ap.add_argument('--geometry',type=Path);args=ap.parse_args();return classify(args)if args.classify else extract(args)
if __name__=='__main__':sys.exit(main())
