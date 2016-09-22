iterations = 50
import bpy
o=bpy.context.active_object
m=o.data
sv=m.skin_vertices[0].data

edit=False
if bpy.context.edit_object!=None:
    edit=True
    bpy.ops.object.editmode_toggle()
    m.update()
    #o.update_from_editmode()


keepverts=[]
everts=[]
for e in m.edges:
    if e.select:
        everts.extend(e.vertices)
for vi in everts:
    if everts.count(vi)==1:
       keepverts.append(vi)

for i in range(0,iterations):
   
    #print(keepverts)
    for e in m.edges:
        if e.select:
            v1=e.vertices[0]
            v2=e.vertices[1]
            r1=sv[v1].radius
            r2=sv[v2].radius
            r1x=r1[0]
            r1y=r1[1]
            r2x=r2[0]
            r2y=r2[1]
            if v1 not in keepverts:
                r1[0]=r1x+(r2x-r1x)/2
                r1[1]=r1y+(r2y-r1y)/2
            if v2 not in keepverts:
                r2[0]=r2x+(r1x-r2x)/2
                r2[1]=r2y+(r1y-r2y)/2
            
            #print(e)
if edit:
    if edit:
        
        bpy.ops.object.editmode_toggle()

