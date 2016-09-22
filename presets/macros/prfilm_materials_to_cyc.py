import bpy
s=bpy.context.scene
sobs = s.objects

for ob in bpy.context.selected_objects:
    ob.select=True
    sobs.active=ob
    #ob = bpy.context.active_object
    if len(ob.material_slots)>0:
        for ms in ob.material_slots:
            m=ms.material
            if m.use_nodes==False:
                m.use_nodes=True
                
                tree = m.node_tree
                
                for n in tree.nodes:
                    tree.nodes.remove(n)
                
                n1 = tree.nodes.new(type = 'ShaderNodeEmission')
                
                n2=tree.nodes.new('ShaderNodeLightPath')
                n3 = tree.nodes.new('ShaderNodeOutputMaterial')
                tree.links.new(n2.outputs['Is Camera Ray'],n1.inputs['Strength'])
                tree.links.new(n1.outputs['Emission'],n3.inputs['Surface'])
                n1.inputs[0].default_value[0] = m.diffuse_color[0]
                n1.inputs[0].default_value[1] = m.diffuse_color[1]
                n1.inputs[0].default_value[2] = m.diffuse_color[2]
                
            tree = m.node_tree
            
            