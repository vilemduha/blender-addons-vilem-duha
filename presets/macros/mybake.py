import bpy
import time

engine='CYCLES'


g_lp=bpy.data.groups['bake']
g_hp=bpy.data.groups['highpoly']


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
                ch.append(o)
        if o.name not in g_lp:        
            tocheck.extend(o.children)
    return ch

def activate(o):
    c=bpy.context
    s=c.scene
    s.objects.active=o
    o.select=True

def sel(obs):
    for o in obs:
        o.select=True
    
def bpreset(type='normal'):
    c=bpy.context
    s=c.scene
    r=s.render
    r.engine='BLENDER_RENDER'
    if type=='normal':
        r.bake_type='NORMAL'
        r.bake_normal_space='TANGENT'
    elif type=='diffuse':
        r.bake_type='FULL'
    else:
        return False
    r.use_bake_selected_to_active=True
    r.use_bake_clear=False
    r.bake_margin=4
    return True

def showlayers(obs,activeob):
    layers=obs[0].layers
    s=bpy.context.scene
    for o in obs:
        for i in range(0,20):
            layers[i]= layers[i] or o.layers[i]
    for i in range(0,20):
        layers[i]=layers[i] and not activeob.layers[i]
    origlayers=[]
    for l in s.layers:
        origlayers.append(l)
    s.layers=layers   
    print(layers)   
    return layers

bobs=[]
for o in g_lp.objects:
    if o.select:
        bobs.append(o)
#bake   


def bake_cycles(o):
    c=bpy.context
    s=c.scene
    r=s.render
    res=512
    
    
    
    do_AA = False
    hres_multiplier = 2
    
    passes = [      'COMBINED' ]
#   
    
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
                    ch.append(o)
            if o.name not in g_lp:        
                tocheck.extend(o.children)
        return ch

    def activate(o):
        c=bpy.context
        s=c.scene
        s.objects.active=o
        o.select=True

    def sel(obs):
        for o in obs:
            o.select=True
        
    r.engine='CYCLES'
    
    scale_images=[]
    save_images=[]

    
    bpy.ops.object.select_all(action='DESELECT')

    ch=getBchildren(o)
    
    activate(o)
     
    #origlayers = showlayers(ch,o)
    
   
    sel(ch)
    
    
    m=o.data
    mat=o.material_slots[0].material
   
    restorelinks=[]#for cycles linked mats
    
    allimg=bpy.data.images
    
    for idx,bpass in enumerate(passes):
        
        t_name=mat.name+'_'+bpass
        
         #get image
        hres_name = t_name+'_hres'
        
        img=allimg.find(t_name)
        if img<0 or allimg[t_name].size[0]!=res:
            img=bpy.data.images.new(t_name,res,res, alpha=False)
            img.name=t_name
            img.name=t_name
        img= allimg[t_name]
        #ensure the name is really what it should be.
        print(img.name)
        baketarget = img
        
        
        #replace with higher res when doing AA.
        if do_AA:  
            if bpy.data.images.find(hres_name)==-1 or bpy.data.images[hres_name].size[0]!=res*hres_multiplier:
                i=bpy.data.images.new(hres_name,res*hres_multiplier,res*hres_multiplier, alpha=False)
                i.name = hres_name
                i.name = hres_name
                
            hres_t = bpy.data.images[hres_name]
            baketarget = hres_t
            simgs=(hres_t,baketarget)
            if simgs not in scale_images:
                scale_images.append(simgs)
                save_images.extend((hres_t,baketarget))
        else:
            save_images.append(img)
        #set images for correct baking
        #if r.engine == 'BLENDER_RENDER':
        
        
            
        for ms in o.material_slots:
            m=ms.material
            nt=m.node_tree
            
            fnode=False
            fn=None
            for n in nt.nodes:
                if n.type=='TEX_IMAGE' and (
                (
                n.outputs['Color'].links==() 
                and n.outputs['Alpha'].links==()
                )                        
                or n.image == baketarget):
                     
                    fnode=True
                    fn=n
                    continue
            if not fnode:
                print ('adding node')
                n=nt.nodes.new(type = 'ShaderNodeTexImage')
                nt.nodes.active = n
                fn=n
            fn.image=baketarget  
            nt.nodes.active=fn  
            fn.update()
            
            
        #setup baking            
       
        if o.get('distance')!=None:
            r.bake_distance = o['distance']
            r.bake_bias = o['bias']
            
       
        
        
        print('baking '+o.name + ' ' + baketarget.name)
         
        r.engine='CYCLES'
        
        
        #if bpass=='NORMAL':
        #    btype='NORMAL'
        #elif bpass=='diffuse':
         #   btype='COMBINED''
        btype = bpass
        seltoact = True    
        margin = 4
        #s.cycles.bake_type = btype
        #print(btype)
        #bpy.ops.object.bake(type= btype, use_selected_to_active = seltoact )
        print(baketarget.filepath)
        #if baketarget.filepath!='':
        #    baketarget.reload()
        baketarget.filepath = "//"+baketarget.name+'.png'
        baketarget.file_format = 'PNG'
        
        bpy.ops.object.bake(
                type= btype, 
                filepath="//"+baketarget.name+'.png',
                width=res, height=res, 
                margin=margin, 
                use_selected_to_active= seltoact, 
                cage_extrusion=0.1, 
                cage_object="", 
                normal_space='TANGENT', 
                normal_r='POS_X', 
                normal_g='POS_Y', 
                normal_b='POS_Z', 
                save_mode='INTERNAL', 
                use_clear=False, 
                use_cage=False, 
                use_split_materials=False, 
                use_automatic_name=False, uv_layer="")
        #baketarget.filepath = "//"+baketarget.name+'.png'
        #baketarget.file_format = 'PNG'
        baketarget.save()
        
        mat.use_textures[idx]=True
        print('done')
    #s.layers=origlayers   
    #scale down?

    if do_AA:  
        for d in scale_images:
            print(d)
            #d=(bpy.data.images['bk1_normal'],bpy.data.images['bk1_normal_hres']
            print('scaling for '+d[0].name)
            temp=d[1].copy()   
            temp.pixels[:] = d[1].pixels[:] 
            temp.scale(res,res)
            #d[0].pixels[:]=temp.pixels[:]

    for image in save_images:

        
        #image.filepath = "//"+image.name+'.png'
        #image.file_format = 'PNG'
        image.save()
        print(image.filepath)
    #r.engine='BLENDER_RENDER'


for o in bobs:
    if engine=='CYCLES':
        bake_cycles(o)
    '''
    else:
        bpy.ops.object.select_all(action='DESELECT')

        ch=getBchildren(o)
        
        activate(o)
         
       # origlayers = showlayers(ch,o)
        
       
        sel(ch)
        
        
        m=o.data
        mat=o.material_slots[0].material
       
        restorelinks=[]#for cycles linked mats
        
        for idx,ts in enumerate(o.material_slots[0].material.texture_slots):
            if ts!=None:
                t=ts.texture
                mat.use_textures[idx]=False
                #get image
                t_name=mat.name+'_'+ts.name
                hres_name = t_name+'_hres'
                
                
                if t.image==None or t.image.size[0]!=res:
                    i=bpy.data.images.new(t_name,res,res, alpha=False)
                    t.image=i
                t.image.name=t_name#ensure the name is really what it should be.
                
                baketarget = t.image 
                
                
                #replace with higher res when doing AA.
                if do_AA:  
                    if bpy.data.images.find(hres_name)==-1 or bpy.data.images[hres_name].size[0]!=res*hres_multiplier:
                        i=bpy.data.images.new(hres_name,res*hres_multiplier,res*hres_multiplier, alpha=False)
                        i.name = hres_name
                        
                    hres_t = bpy.data.images[hres_name]
                    baketarget = hres_t
                    simgs=(t.image,baketarget)
                    if simgs not in scale_images:
                        scale_images.append(simgs)
                        save_images.append(t.image,baketarget)
                else:
                    
                    save_images.append(t_name)
                
                for f in o.data.uv_textures[0].data:
                   f.image=baketarget
               
                #setup baking            
                do_bake = bpreset(t.name)
                if o.get('distance')!=None:
                    r.bake_distance = o['distance']
                    r.bake_bias = o['bias']
                    
               
                
                if do_bake:
                    print('baking '+o.name + ' ' + t.name)
                    if r.engine=='BLENDER_RENDER':
                        bpy.ops.object.bake_image()
                   
                mat.use_textures[idx]=True
                print('done')
        s.layers=origlayers   
    '''
