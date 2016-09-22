import bpy
import time,os

end=False


while not end:
    #bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
    
    for ob in bpy.data.objects:
        bpy.data.objects.remove(ob)
    for m in bpy.data.meshes:
        bpy.data.meshes.remove(m)

    s=bpy.context.scene
    s.name='nothing'
    
    path=bpy.data.filepath[:-len(bpy.path.basename(bpy.data.filepath))]+'//queue.txt'
    f=open(path,'r')
    list=f.readlines()
    f.close()
    
    if len(list)>0:
        
        

        data=list.pop(0)
        d=eval(data)
        
        fpath=d[0]
        sname=d[1]
        oname=d[2]
        ch=d[3]
        
        opath = fpath +"\\Scene\\" + sname
        s = os.sep
        dpath = fpath +"\\Scene\\"

        # DEBUG
        #print('import_object: ' + opath)

        bpy.ops.wm.link(
                filepath=opath,
                filename=sname,
                directory=dpath,
                filemode=1,
                link=False,
                autoselect=True,
                active_layer=True,
                instance_groups=True,
                relative_path=True)
        
        bpy.data.screens['Default'].scene = bpy.data.scenes[sname]
        print(d)
        
        for l in list:
            if l =='\n':
                list.remove(l)
        #f=open(path,'w')
        #for l in list:
        #    f.write(l)
        #f.close()
        
        ob=bpy.data.objects[oname]
        s=bpy.context.scene
        s.objects.active=ob
        
        ob.select=True
        bpy.data.groups['bake'].objects.link(ob)
        for child in ch:
            bpy.data.groups['highpoly'].objects.link(bpy.data.objects[child])
        
        
        
        bpy.ops.object.hierarchy_bake()
        end=True
        #bpy.ops.scene.delete()
    else:
        
        time.sleep(1)