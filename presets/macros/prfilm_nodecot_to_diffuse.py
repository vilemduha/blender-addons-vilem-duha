import bpy
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.name=='Emission':
                m.diffuse_color = n.inputs['Color'].default_value[:3]