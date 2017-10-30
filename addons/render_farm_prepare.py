import bpy,random
from mathutils import Vector, Color

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
        if ob.mode=='POSE':
            s.objects.active=ob
            bpy.ops.object.posemode_toggle()

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
            s.objects.active=a
            bpy.ops.object.modifier_remove(modifier=n)
            
           

            s.objects.unlink(copyob)

def make_local():
    s=bpy.context.scene
    for ob in s.objects:
        

def bakeDrivers():
    if "Drivers in File" in bpy.data.texts:
        text = bpy.data.texts["Drivers in File"]
    else:
        text = bpy.data.texts["Drivers in File"]
    text.clear()

    all_drivers = []
    

    collections = ["scenes","objects","meshes","materials","textures","speakers","worlds","curves","armatures","particles","lattices","shape_keys","lamps","cameras"]
    text.write("-"*70 + "\n")
    text.write("DRIVERS IN %s\n" % bpy.data.filepath)
    text.write("-"*70 + "\n")
    for col in collections:
        collection = eval("bpy.data.%s"%col)
        for ob in collection:
            if ob.animation_data is not None:
                for driver in ob.animation_data.drivers:
                    
                    dp = driver.data_path
                    pp = dp
                    if dp.find("[") != 0:pp = "%s"%dp
                    resolved = False
                    try:
                        dob = ob.path_resolve(dp)
                        resolved = True
                        #all_drivers.append(dp)
                    except:
                        dob = None
                        
                    if not resolved:
                        try:
                            path = 'bpy.data.%s["%s"]%s' % (col,ob.name,pp)
                            dob = eval( path)
                            resolved = True
                            #all_drivers.append(path)
                        except:
                            dob = None
                        
                    idx = driver.array_index
                    if dob is not None and (isinstance(dob,Vector) or isinstance(dob,Color)):
                        pp = "%s[%d]"%(pp,idx)
                    text.write('bpy.data.%s["%s"]%s  (%s)\n' % (col,ob.name, pp, driver.driver.expression) )
                    all_drivers.append(['bpy.data.%s["%s"]' % (col,ob.name) , pp])
    s = bpy.context.scene
    if s.node_tree != None:
        if s.node_tree.animation_data != None:
            for d in bpy.context.scene.node_tree.animation_data.drivers:
                all_drivers.append(['bpy.context.scene.node_tree' ,d.data_path])
                #print(d.evaluate(1))
                #print(d.evaluate(10))
    print(all_drivers)
    for f in range(s.frame_start, s.frame_end):
        print(' baking drivers frame ', str(f))
        s.frame_set(f)
        for dp in all_drivers:
            print(dp)
            datablock = eval(dp[0])
            
            
            #s.frame_current_final = f
            #s.update()
            
            
            #datablock.update()
            prop = eval(dp[0]+'.'+dp[1])
            #s.update
            value = prop
            print(f,value, datablock)
            datablock.keyframe_insert(dp[1], frame = f)
        #d.convert_to_keyframes(s.frame_start, s.frame_end)
    
  


def main(context):
              
         
    for m in bpy.data.meshes:
        if m.auto_smooth_angle<0.1:
            m.auto_smooth_angle=1.39
                  
    #bpy.ops.wm.save_mainfile()
    p=bpy.data.filepath
    p1=bpy.path.abspath(p)
    n=bpy.path.basename(p1)
    p1=p1[:-len(n)]
    s=bpy.context.scene
    nn=p1+'SHEEPIT_' + s.name +'.blend'
    print(nn)
    #first save - if there's error in the script, I could fuck up my file by saving accidentaly after running it
    bpy.ops.wm.save_as_mainfile(filepath=nn, compress=False)

    r=s.render
    r.resolution_percentage=100
    r.use_simplify=False
    #s.world.light_settings.samples=15
    #r.use_antialiasing=True
    i=r.image_settings
    i.file_format='PNG'
    i.color_mode='RGBA'
    i.color_depth='8'
    #r.use_overwrite=False
    
    make_local()
    '''
    bakeCurveSoftbodies()  
    fix_duplis()
    bakeDrivers()

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
    '''


class SheepifyOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.sheepify_operator"
    bl_label = "Export sheepit compatible scene"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SheepifyOperator)


def unregister():
    bpy.utils.unregister_class(SheepifyOperator)


if __name__ == "__main__":
    register()

    # test call
    #bpy.ops.object.simple_operator()
