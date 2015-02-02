import bpy
n='dp'
def a(ob):
    s=bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    ob.select=True
    s.objects.active=ob
    
obs=bpy.context.selected_objects
s=bpy.context.scene

for ob in obs:
    s.cursor_location=ob.matrix_world.translation
    a(ob)
    d=max(ob.dimensions.x,ob.dimensions.y,ob.dimensions.z)
    #bpy.ops.object.editmode_toggle()
    #bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, size=d/2, view_align=False, enter_editmode=False)
    #bpy.ops.mesh.select_all(action='INVERT')
    #bpy.ops.mesh.delete(type='VERT')

    #bpy.ops.object.editmode_toggle()
    #
    #bpy.ops.object.shade_smooth()
    bpy.ops.object.metaball_add(type='BALL', view_align=False, enter_editmode=False)
    bpy.context.object.name = n
    
    m=bpy.context.active_object
    m.scale*=ob.dimensions.z*.6
    m.data.resolution=0.2
bpy.ops.object.editmode_toggle()
bpy.ops.object.editmode_toggle()

