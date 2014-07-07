import bpy
a=bpy.context.active_object
#prop='data.use_uv_as_generated'
#d=a.path_resolve(prop)
d=a.data.use_auto_texspace
d1=a.data.texspace_size
print(d)
for ob in bpy.context.selected_objects:
    ob.data.use_auto_texspace=d
    ob.data.texspace_size=d1
    #p=ob.path_resolve(prop,False)
    #print(p)
    #p=d
    