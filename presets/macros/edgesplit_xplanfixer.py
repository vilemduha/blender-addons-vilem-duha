import bpy
for ob in bpy.data.objects:
    m=ob.modifiers.get('EdgeSplit')
    #print(ob.name,m)
    if m!=None:
        if m.split_angle<3.14/5:
            print(ob.name,m.split_angle)  
            m.split_angle=3.14/4  
    