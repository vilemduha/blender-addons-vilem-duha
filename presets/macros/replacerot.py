import bpy
def activate(o):
    s=bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    s.objects.active=o
    o.select=True

s=bpy.context.scene

obs=bpy.context.selected_objects
chassign=[]
for ob in obs:
    
    cube=s.objects['replacement']
    activate(cube)
    bpy.ops.object.duplicate(linked=True)
    nob=bpy.context.active_object
    nob.location=ob.location
    nob.rotation_euler=ob.rotation_euler
    nob.animation_data.action=ob.animation_data.action
    chassign.append((ob.children,nob)
    #nob.children=ob.children
    nob.parent=ob.parent        