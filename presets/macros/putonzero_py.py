import bpy
for ob in bpy.context.selected_objects:
    z=-ob.bound_box[0][2]
    ob.location.z=z