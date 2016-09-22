import bpy
s=100
e=200
step = 10

i=0

a=bpy.context.active_object

scene=bpy.context.scene
obs = bpy.context.selected_objects
for ob in obs:
    if ob!=a:
        #scene.objects.active=ob
        #bpy.ops.object.select_all(action='DESELECT')
        
        
        for f in range(s,e+1,step):
            #scene.objects.active=a
            #a.select=True
            #ob.select=True
            
            scene.frame_current = f
            scene.update()
            bpy.ops.object.copy_obj_vis_rot()
            #v=sval + ((f-s)/(e-s))*(eval-sval)
            #ob.xplane['datarefs'][i]['value'] = v
            #scene.objects.active=ob
            #a.select=False
            bpy.ops.anim.keyframe_insert_menu(type='Rotation')

           # bpy.ops.object.add_xplane_dataref_keyframe(index=i)
