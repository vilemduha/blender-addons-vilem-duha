import bpy
i=bpy.data.images[0]

for o in bpy.context.selected_objects:
    if o.type=='MESH':
        m=o.data
        for uvt in m.uv_textures:
            for d in uvt.data:
                d.image=i    