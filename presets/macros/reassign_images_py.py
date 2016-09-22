import bpy
for i in bpy.data.images:
    if i.name.find('.0')==-1:
        #getting base image
        path=i.filepath
        #relpath = bpy.path.relpath(path)
        basename=bpy.path.basename(path)
        i.filepath='//'+basename
        print ('//'+basename)
        print(i.name.find('.0'))
        print(i.name)
        for m in bpy.data.materials:
            for n in m.node_tree.nodes:
                if n.name == 'Image Texture':
                    #for  i1 in bpy.data.images:
                    if bpy.path.basename(n.image.filepath) == basename:
                        print('material')
                        print(n.image.name)
                        print(i.name)
                        n.image = i
                        pass