import bpy
g=bpy.data.groups['bake']
bpy.ops.group.objects_remove_all()

for ob in bpy.context.selected_objects:
     if ob.name not in g.objects:
         g.objects.link(ob)