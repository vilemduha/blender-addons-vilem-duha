import bpy
'''
ac=bpy.context.active_object
obs=bpy.context.selected_objects

bpy.ops.object.select_all(action='DESELECT')
tempt=bpy.data.objects['TEMPT']
temps=bpy.data.objects['TEMPS']

tempt.select=True
temps.select=True
bpy.context.scene.objects.active=tempt
bpy.ops.object.bake(type='NORMAL', use_selected_to_active= True)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.scene.objects.active=ac
for ob in obs:
    ob.select=True
'''
bpy.ops.object.hierarchy_bake()