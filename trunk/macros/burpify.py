import bpy,random

def fix_duplis():
    dupligroups=[]
    s=bpy.context.scene
    groups=[]
    sobs=tuple(s.objects)
    for ob in sobs:
        if ob.dupli_type=='GROUP':
            if ob.dupli_group not in groups and ob.dupli_group!=None:
                groups.append(ob.dupli_group)
        for ps in ob.particle_systems: 
            if ps.settings.render_type=='GROUP':
                if (ps.settings.dupli_group not in groups) and ps.settings.dupli_group!=None:
                    groups.append(ps.settings.dupli_group)
                
              
                
    print(groups)
    linkobs=[]
    for g in groups:
        for ob in g.objects:
            print(ob, ob in sobs)
            if not ob  in sobs and not ob in linkobs:
                linkobs.append(ob)
    for ob in linkobs:
        s.objects.link(ob)
        ob.layers=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True)
    print('object forced to be linked to scene:')
    print(linkobs)
    #print(len(linkobs))   
    

def bakeCurveSoftbodies():
   

    s=bpy.context.scene
    for ob in s.objects:
        bpy.ops.object.select_all(action='DESELECT')
        s.objects.active=ob
        ob.select=True
        a=ob
        c=a.data
        

        if a.soft_body!=None:
            for m in a.modifiers:
                if m.type=='SOFT_BODY':
                    n=m.name
                    bpy.ops.object.duplicate()
                    copyob=bpy.context.active_object
                    bpy.ops.object.modifier_remove(modifier=n)
                    
                    bpy.ops.object.shape_key_add(from_mix=False)
                    copyob.data.shape_keys.use_relative=False
                    pc=m.point_cache
                    
                    bob=c.bevel_object
                    bdpt=c.bevel_depth
                    U=c.resolution_u
                    
                    c.resolution_u=0
                    c.bevel_object=None
                    c.bevel_depth=0
                    
                    
                    pc.name='cache'+str(int(random.random()*25000000))
                    for f in range(pc.frame_start,pc.frame_end,pc.frame_step):
                        s.frame_current=f
                        copyob.data.shape_keys.eval_time=f
                        copyob.data.shape_keys.keyframe_insert('eval_time',frame=f)
                        d=a.to_mesh(s, apply_modifiers=True, settings='PREVIEW')
                        
                        bpy.ops.object.shape_key_add(from_mix=False)
                        
                        
                        bpy.ops.object.editmode_toggle()
                        si=0
                        ci=0
                        for i,v in enumerate(d.vertices):
                            
                            spline=copyob.data.splines[si]
                            points=spline.bezier_points[:]
                            points.extend(spline.points)
                            points[ci].co[0]=v.co[0]
                            points[ci].co[1]=v.co[1]
                            points[ci].co[2]=v.co[2]
                            print(v.co)          
                            ci+=1
                            if ci==len(points):
                                ci=0
                                si+=1
                            
                        bpy.ops.curve.handle_type_set(type='AUTOMATIC')
                 
                        bpy.ops.object.editmode_toggle()
                        #k=copyob.data.shape_keys.key_blocks[-1]
                        #k.keyframe_insert('value',frame=f-pc.frame_step)
                        #k.keyframe_insert('value',frame=f+pc.frame_step)
                        #k.value=1
                        #k.keyframe_insert('value',frame=f)
                    c.resolution_u=U
                    c.bevel_object=bob
                    c.bevel_depth=bdpt
                    
                    
            a.select=True
            bpy.ops.object.make_links_data(type='OBDATA')
            s.objects.active=copyob
            bpy.ops.object.modifier_remove(modifier=n)
            
           

            s.objects.unlink(copyob)

            
           
#bpy.ops.wm.save_mainfile()
p=bpy.data.filepath
p1=bpy.path.abspath(p)
n=bpy.path.basename(p1)
p1=p1[:-len(n)]
s=bpy.context.scene
nn=p1+'BURP_' + s.name +'.blend'
print(nn)
#first save - if there's error in the script, I could fuck up my file by saving accidentaly after running it
bpy.ops.wm.save_as_mainfile(filepath=nn, compress=False)

r=s.render
r.resolution_percentage=100
r.use_simplify=False
s.world.light_settings.samples=15
r.use_antialiasing=True
i=r.image_settings
i.file_format='PNG'
i.color_mode='RGBA'
i.color_depth='8'
#r.use_overwrite=False

bakeCurveSoftbodies()  
fix_duplis()

for s1 in bpy.data.scenes:
    if s1!=s:
        bpy.data.scenes.remove(s1)
for t in bpy.data.texts:
    bpy.data.texts.remove(t)
   
    
bpy.ops.wm.save_as_mainfile(filepath=nn, compress=True)
bpy.ops.wm.revert_mainfile()
bpy.ops.wm.save_as_mainfile(filepath=nn, compress=True)
bpy.ops.wm.revert_mainfile()
bpy.ops.wm.save_as_mainfile(filepath=nn, compress=True)