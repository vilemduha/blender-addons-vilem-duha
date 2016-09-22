import bpy

#bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")
#bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")


bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='DESELECT')

bpy.ops.mesh.edges_select_sharp(sharpness=0.8)
bpy.ops.mesh.mark_freestyle_edge(clear=False)

bpy.ops.object.editmode_toggle()