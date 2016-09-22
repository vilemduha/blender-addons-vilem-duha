import bpy
scale = 1
bpy.ops.object.shade_smooth()
sobs=bpy.context.selected_objects
for o in sobs:
    d=o.data
    dim=o.dimensions
    print(dim)
    maxdim=max(dim.x,dim.y)
    c=o.data
    c.dimensions='2D'
    c.offset=0#-0.001 * scale
	     
    c.bevel_depth=0#0.001 * scale
    c.bevel_resolution=0#* scale
    c.extrude=.009#0.0065* scale
    c.fill_mode = 'BOTH'
    #for c in d.splines:
        #print (c.type)
       # c.type='POLY'
    s=bpy.context.scene
    s.objects.active=o
    bpy.ops.object.select_all(action='DESELECT')
    o.select=True
    bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', obdata=True)

    bpy.ops.object.convert(target='MESH')
    
    bpy.ops.object.editmode_toggle()
    #bpy.ops.mesh.select_non_manifold()
    #bpy.ops.mesh.select_similar(type='FACE_ANGLE', threshold=0.5)
    #bpy.ops.mesh.mark_freestyle_edge(clear=False)
    #bpy.ops.mesh.remove_doubles()
    bpy.ops.object.editmode_toggle()
    
    bpy.ops.object.material_slot_add()
    m1=bpy.data.materials['freestyler']
    o.material_slots[0].material=m1
    
    bpy.ops.object.modifier_add(type='REMESH')
    bpy.ops.object.modifier_add(type='DECIMATE')
    #bpy.context.object.modifiers["Remesh"].show_viewport = False
    bpy.context.object.modifiers["Decimate"].show_viewport = False
    bpy.context.object.modifiers["Decimate"].ratio = 0.1
    
    
#import bpy
    bpy.context.active_object.update_tag()
    #dim=o.dimensions
    print(dim)
    print(o.name)
    #maxdim=max(dim.x,dim.y)
    print(maxdim)
    res=6
    if maxdim>.15:
        res=7
    if maxdim>.30:
        res=8
    if maxdim>.5:
        res=9  
    if maxdim>1.0:
        res=10 
    if maxdim>2.0:
        res=11
    if maxdim>3.0:
        res=12
    bpy.context.object.modifiers["Remesh"].octree_depth = res

    
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")


    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.mesh.edges_select_sharp(sharpness=0.8)
    bpy.ops.mesh.mark_freestyle_edge(clear=False)

    bpy.ops.object.editmode_toggle()
    
