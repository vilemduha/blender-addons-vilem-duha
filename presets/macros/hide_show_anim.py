import bpy
show=1
hide=1
do_blend=0
b_type='PASS'
blendtime=10
timed=1
s=bpy.context.scene
curfr=s.frame_current


    
    
for ob in bpy.context.selected_objects:
    scale=ob.scale.copy()#save this because of changes later
    if timed:
        curvestweak=['location','scale','rotation_euler']
                
        ac=ob.animation_data.action
        minframe=1000000
        maxframe=-10000000
        for curve in ac.fcurves:
            if curve.data_path in curvestweak:
                if curve.keyframe_points[0].co.x<minframe:
                    minframe=curve.keyframe_points[0].co.x
                if curve.keyframe_points[-1].co.x>maxframe:
                    maxframe=curve.keyframe_points[-1].co.x
        
        if maxframe==-10000000:
            maxframe=curfr
            minframe=curfr
        
    else:
        maxframe=curfr
        minframe=curfr
    
    do=[]
    if show:
        do.append([minframe-1-do_blend*blendtime,minframe-do_blend*blendtime,minframe])
    if hide:
        do.append([maxframe+1+do_blend*blendtime,maxframe+do_blend*blendtime,maxframe])
    
    for d in do:    
        if do_blend:
            if b_type=='PASS':
                ob.pass_index=0
                ob.keyframe_insert('pass_index',frame=d[2])
                ob.pass_index=100
                ob.keyframe_insert('pass_index',frame=d[1])
            else:
                
                #ob.pass_index=0
                s.frame_current=d[2]
                s.update()
                #if ob.scale.x==0.01 and ob.scale.y==0.01 and ob.scale.z==0.01:
                ob.scale=scale
                    
                ob.keyframe_insert('scale',frame=d[2])
                s.frame_current=d[1]
                ob.scale=(0.01,0.01,0.01)
               
                ob.keyframe_insert('scale',frame=d[1])
                    
        
        ob.hide_render=True
        #bob.hide=True
        ob.keyframe_insert('hide_render',frame=d[0])
        #bob.keyframe_insert('hide',frame=g.curframe-1)

        ob.hide_render=False
        #bob.hide=False
        ob.keyframe_insert('hide_render',frame=d[1])
        