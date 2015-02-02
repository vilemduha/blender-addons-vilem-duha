import bpy

res=1024

#
c=bpy.context
g_lp=bpy.data.groups['bake']
g_hp=bpy.data.groups['highpoly']
s=c.scene


def getBchildren(o):
    ch=[]
    tocheck=[]
    tocheck.extend(o.children[:])
    while len(tocheck)>0:
        o=tocheck.pop()
        if o.type!='EMPTY':
            if o.name in g_hp.objects:
                ch.append(o)
        if o.name not in g_lp:        
            tocheck.extend(o.children)
    return ch

def activate(o):
    s=c.scene
    s.objects.active=o
    o.select=True

def sel(obs):
    for o in obs:
        o.select=True
    
def bpreset(type='normal'):
    r=s.render
    if type=='normal':
        r.engine='BLENDER_RENDER'
        r.bake_type='NORMALS'
        r.bake_normal_space='TANGENT'
    elif type=='diffuse':
        r.engine='BLENDER_RENDER'
        r.bake_type='FULL'
        r.bake_normal_space='TANGENT'
    else:
        return False
    r.use_bake_selected_to_active=True
    r.use_bake_clear=False
    r.bake_margin=4
    return True

bobs=[]
for o in g_lp.objects:
    if o.select:
        bobs.append(o)
        
for o in bobs:
    
    ch=getBchildren(o)
    activate(o)
    sel(ch)
    
    
    m=o.data
    mat=o.material_slots[0].material
   
    for idx,ts in enumerate(o.material_slots[0].material.texture_slots):
        if ts!=None:
            t=ts.texture
            mat.use_textures[idx]=False
            if t.image==None or t.image.size[0]!=res:
                i=bpy.data.images.new(mat.name+'_'+ts.name,res,res, alpha=False)
                t.image=i
            for f in o.data.uv_textures['UVMap'].data:
                f.image=t.image
           
            do_bake = bpreset(t.name)
            if do_bake:
                print('baking '+o.name + ' ' + t.name)
                bpy.ops.object.bake_image()
            mat.use_textures[idx]=True
            print('done')