import bpy
s=100
e=200
step = 10
sval=-1.0
eval=1.0
i=0

scene=bpy.context.scene
obs = bpy.context.selected_objects
for ob in obs:
    scene.objects.active=ob
    for f in range(s,e+1,step):
        scene.frame_current = f
        v=sval + ((f-s)/(e-s))*(eval-sval)
        ob.xplane['datarefs'][i]['value'] = v
        bpy.ops.object.add_xplane_dataref_keyframe(index=i)
