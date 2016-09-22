import bpy
o=bpy.context.active_object
m=o.data
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='DESELECT')

bpy.ops.object.editmode_toggle()
for i in range(0,len(m.vertices)):
    m.vertices[i].select=False
    if m.vertex_paint_masks[0].data[i].value>0.01:
        m.vertices[i].select=True
    else:
        m.vertices[i].select=False
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.editmode_toggle()
bpy.ops.sculpt.sculptmode_toggle()
