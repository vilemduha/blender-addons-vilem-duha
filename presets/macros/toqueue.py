import bpy

def getBchildren(o):
    g_lp=bpy.data.groups['bake']
    g_hp=bpy.data.groups['highpoly']
    ch=[]
    tocheck=[]
    tocheck.extend(o.children[:])
    while len(tocheck)>0:
        o=tocheck.pop()
        if o.type!='EMPTY':
            if o.name in g_hp.objects:
                ch.append(o.name)
        if o.name not in g_lp:        
            tocheck.extend(o.children)
    return ch

g_lp=bpy.data.groups['bake']
g_hp=bpy.data.groups['highpoly']
bobs=[]
for o in g_lp.objects:
    if o.select:
        bobs.append(o.name)

path=bpy.data.filepath[:-len(bpy.path.basename(bpy.data.filepath))]+'//queue.txt'
print(path)
try:
    f=open(path,'r')
    list=f.readlines()
    f.close()
except:
    list=[]

for l in list:
    if l =='\n':
        list.remove(l)
        
for o in bobs:
    #ch=getBchildren(bpy.data.objects[o])
    layers=[]
    for layer in bpy.context.scene.layers:
        if layer:
            layers.append(1)
        else:
            layers.append(0)
    
    l=str((bpy.data.filepath,bpy.context.scene.name,o,layers))
    
    #command = 'F:\blenders\current\blender-2.73-51a60cb-win64\blender-2.73-51a60cb-win64\blender.exe -b testbake.blend -P queueworker01.py -- -o='+str(l)
    if l not in list:
        list.append(l)

f=open(path,'w')
for l in list:
    f.writelines(l+'\n')
f.close()