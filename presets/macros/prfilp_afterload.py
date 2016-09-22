import bpy
s=bpy.context.scene




#link materials
for selob in bpy.context.scene.objects:
    if selob.name.startswith('Curve'):
        #selob = bpy.context.active_object
        if len(selob.material_slots)>0:
            m=selob.material_slots[0].material
            if m!=None:   
                c=m.diffuse_color
                for ob in bpy.context.visible_objects:
                    if len(ob.material_slots)>0:
                        m1=ob.material_slots[0].material
                        if m1!=None:
                            c1=m1.diffuse_color
                            if c==c1:
                                    ob.material_slots[0].material = m
    
sobs = s.objects

for ob in bpy.data.objects:
    ob.select=True
    sobs.active=ob
    #ob = bpy.context.active_object
    if len(ob.material_slots)>0:
        for ms in ob.material_slots:
            m=ms.material
            if m!=None:
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

z=0
for ob in bpy.context.scene.objects:
    if ob.name.startswith('Curve'):
        ob.location.z-=z*.001
        z+=1