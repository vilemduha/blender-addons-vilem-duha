import bpy

selob = bpy.context.active_object
m=selob.material_slots[0].material
if m.use_nodes:
    pass;
else:
    c=m.diffuse_color
    for ob in bpy.context.visible_objects:
        if len(ob.material_slots)>0:
            m1=ob.material_slots[0].material
            c1=m1.diffuse_color
            if c==c1:
                ob.material_slots[0].material = m
        