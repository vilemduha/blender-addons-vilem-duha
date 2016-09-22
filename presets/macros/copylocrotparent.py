#copylocrotparent matrix
import bpy
a=bpy.context.active_object
bpy.context.scene.cursor_location=a.location
obs=bpy.context.selected_objects
for ob in obs:
    if ob!=a:
        bpy.ops.mesh.primitive_cube_add()
        c=bpy.context.active_object
        c.rotation_euler=a.rotation_euler
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.editmode_toggle()
        ob.select=True
        bpy.ops.object.join()
        #c.parent=a.parent