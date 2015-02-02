import bpy
def a(ob):
    s=bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    ob.select=True
    s.objects.active=ob
    
obs =bpy.context.selected_objects
for ob in obs:
    a(ob)
    c=ob.color#material_slots[0].material.diffuse_color
    print(c[0],c[1],c[2])
    bpy.ops.paint.vertex_paint_toggle()
    bpy.context.tool_settings.vertex_paint.brush.color=(c[0],c[1],c[2])
    bpy.ops.paint.vertex_color_set()

    bpy.ops.paint.vertex_paint_toggle()


    #=bpy.context.active_object.data.vertex_colors['Col'].data[0].color
