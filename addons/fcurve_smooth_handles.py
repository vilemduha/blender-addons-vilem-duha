import bpy

import bpy, mathutils,math
from mathutils import *
from math import *


from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        )

bl_info = {
    "name": "Fcurve smooth handles",
    "author": "Vilem Duha",
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "Animation > smooth fcurve handles",
    "description": "Smooths fcurve handles",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
    }






def lookup_prev_extrema(c,i):
    hasprev=False
    prev = None
    
    
    a=1
    while not hasprev:
        
       iprev = i-a 
       p=c.keyframe_points[iprev]
       if iprev>0:
           
           pp=c.keyframe_points[iprev-1]
           pn=c.keyframe_points[iprev+1]
           if (pp.co.y>=p.co.y and pn.co.y>=p.co.y) or (pp.co.y<=p.co.y and pn.co.y<=p.co.y):
               prev = p.co.y
               hasprev = True
       else:
           hasprev = True
           prev = p.co.y
       a+=1
    return prev
      
def lookup_next_extrema(c,i):           
    hasnext = False
    next = None
    a=1
    while not hasnext:
        inext = i+a 
        if inext<len(c.keyframe_points):
            p=c.keyframe_points[inext]
            if inext<len(c.keyframe_points)-1:
               
               pp=c.keyframe_points[inext-1]
               pn=c.keyframe_points[inext+1]
               if (pp.co.y>=p.co.y and pn.co.y>=p.co.y) or (pp.co.y<=p.co.y and pn.co.y<=p.co.y):
                   next = p.co.y
                   hasnext = True
                   #print(next, ' output')
            else:
                
               hasnext = True
               next = p.co.y
        else:
           hasnext = True
           next = c.keyframe_points[-1].co.y
        a+=1 
    
    return next

def main(context, autoclamp, iterations, autoclamp_handle_ratio):
    '''
    fare = bpy.context.area  #loop through areas
    editor = area.spaces[0]
    if area.type == 'DOPESHEET_EDITOR':
        
        if editor.mode == 'ACTION'
        if editor.mode == 'DOPESHEET'
        
    if area_type == 'GRAPH_EDITOR':   
        
        action = dopesheet.action
        
        for fcurve in action.fcurves :
            for p in fcurve.keyframe_points :
                print(p.[0],p.select_control_point)  

    #autoclamp_handle_ratio = 2/3
    '''
    curves = []
    ob = bpy.context.active_object
    a=ob.animation_data.action
    is_armature = ob.type == 'ARMATURE'
    for c in a.fcurves:
        
        if is_armature:
            selected = False
            for b in bpy.context.selected_pose_bones:
                
                if c.data_path.find("\"%s\"" % b.name) >-1:
                    selected = True
        else:
            selected = True
        if selected:
            for a in range(0,iterations):
                i=0
                for p in c.keyframe_points:
                    #if i>0 and i<len(c.keyframe_points):
                    
                    if p.select_control_point:
                        is_pp = False
                        is_np = False
                        if i>0:
                            prevp = c.keyframe_points[i-1]
                            is_pp = True
                        if i<len(c.keyframe_points)-1:
                            nextp = c.keyframe_points[i+1]
                            is_np = True
                            
                        is_autoclamp =  autoclamp and (is_pp and is_np and ((prevp.co.y>= p.co.y and nextp.co.y>=p.co.y) or  (prevp.co.y<=p.co.y and nextp.co.y<=p.co.y) )) 
                        if not is_autoclamp:
                            is_autoclamp  = autoclamp and (not is_np or not is_pp)
                        #evaldist = 
                        
                        
                            
                        vhl=(p.handle_left-p.co)
                        vhp=(p.handle_right-p.co)
                        
                        evaldist = min(abs(vhl.x),abs(vhp.x))
                        
                        #print(p.co)
                        #print(c.data_path)
                        if vhl.x ==0:
                            return
                        scale_vhl = abs(evaldist / vhl.x)
                        scale_vhp = abs(evaldist / vhp.x)
                        vhl *= scale_vhl
                        vhp *= scale_vhp
                        
                        hl = vhl.y
                        hp = vhp.y
                        
                        vcl = c.evaluate(p.co.x-evaldist)#c.evaluate(p.co.x-0.5) - p.co.y
                        vcp = c.evaluate(p.co.x+evaldist)#c.evaluate(p.co.x+0.5) - p.co.y
                        dl= hl - vcl
                        dp = hp - vcp
                        xl = p.handle_left.x
                        xp = p.handle_right.x
                        if is_autoclamp:
                                #print('autoclamp')
                                p.handle_left.y = p.co.y
                        else:
                            if abs(dl-dp)>0.000001:# and ((dl<0 and dp<0) or (dl>0 and dp>0)):#
                                median =  (dp-dl)/20
                                p.handle_left.y+=vhl.length * median
                            
                        
                        #scale handles to 1/3 + scale handles next to autoclamped verts
                        
                        if is_pp:
                            #is_pp_autoclamp = prevp.co.y == prevp.handle_left.y
                         
                            
                            
                            
                                
                            vec = (p.handle_left - p.co)
                            scale_handle = abs(((p.co.x - prevp.co.x) / 3) / vec.x)
                            #print( ' scale tu handlu jo?' , scale_handle)
                            vec *= scale_handle
                            #if vec.x < prevp.co.x:#extreme motion cases, where big handles happen
                                
                            vecfin=vec+p.co
                            
                            #if is_pp_autoclamp and ((vecfin.y>prevp.co.y and prevp.co.y>p.co.y)or (vecfin.y<prevp.co.y and prevp.co.y<p.co.y)):
                            
                            if autoclamp:
                                
                                prevextrema = lookup_prev_extrema(c,i)  
                                if prevextrema > p.co.y:
                                    handle_left_max = autoclamp_handle_ratio *(min( prevextrema, prevp.co.y) - p.co.y) 
                                    if vec.y> handle_left_max:
                                        ratio = handle_left_max / vec.y
                                        vec *= ratio
                                        #height_diff = vecfin.y - handle_left_max
                                        vecfin = vec+p.co
                                if prevextrema < p.co.y:
                                    handle_left_min = autoclamp_handle_ratio *(max( prevextrema, prevp.co.y) - p.co.y) 
                                    if vec.y < handle_left_min:
                                        ratio = handle_left_min / vec.y
                                        vec *= ratio
                                        #height_diff = vecfin.y - handle_left_max
                                        vecfin = vec+p.co
                              
                            p.handle_left.x = vecfin.x
                            p.handle_left.y = vecfin.y
                            #print(scale_handle)
                        if is_np:
                            vec = (p.handle_right - p.co)
                            scale_handle = abs(((nextp.co.x- p.co.x) / 3) / vec.x)
                            vec *= scale_handle
                            
                            #is_np_autoclamp = nextp.co.y == nextp.handle_left.y
                            
                            
                            
                            vecfin = vec + p.co
                            
                            #if is_np_autoclamp and ((vecfin.y>nextp.co.y and nextp.co.y>p.co.y)or (vecfin.y<nextp.co.y and nextp.co.y<p.co.y)):
                            if autoclamp:
                                nextextrema = lookup_next_extrema(c,i)  
                                #print('next extreme', nextextrema,p.co.y,i)
                                if nextextrema > p.co.y:
                                    handle_right_max = autoclamp_handle_ratio *(min( nextextrema, nextp.co.y) - p.co.y) 
                                    #print('next extreme', handle_right_max,i)
                                    if vec.y> handle_right_max:
                                        ratio = handle_right_max / vec.y
                                        vec *= ratio
                                        #height_diff = vecfin.y - handle_left_max
                                        vecfin = vec+p.co
                                if nextextrema < p.co.y:
                                    handle_right_min = autoclamp_handle_ratio *(max( nextextrema, nextp.co.y) - p.co.y) 
                                    if vec.y < handle_right_min:
                                        ratio = handle_right_min / vec.y
                                        vec *= ratio
                                        #height_diff = vecfin.y - handle_left_max
                                        vecfin = vec+p.co
                                
                                
                            
                            p.handle_right.x = vecfin.x
                            p.handle_right.y = vecfin.y
                            #print(scale_handle)
                            p.handle_left_type = 'ALIGNED'
                            p.handle_right_type = 'ALIGNED'
                    i+=1
                    c.update()




class SmoothKeys(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "anim.fcurve_handle_smooth"
    bl_label = "Smooth fcurve handles"
    bl_description = "Auto adjust handles (with or without clamping)"
    bl_options = {'REGISTER', 'UNDO'}
    
    auto_clamp = BoolProperty(
            name="Auto clamped",
            default=True,
            )
    iterations = IntProperty(
            name="Iterations",
            description="Iterations of smoothing",
            min=1, max=10000,
            default=50,
            )
    
    autoclamp_handle_ratio = FloatProperty(
            name="autoclamp Ratio",
            description="autoclamp ratio",
            min=0.001, max=1.0,
            default=2/3,
            )   
      
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context, self.auto_clamp, self.iterations, self.autoclamp_handle_ratio)
        return {'FINISHED'}
    
def SmoothKeysDraw(self,context):
    row = self.layout.row(align=True)
    ac_on = row.operator(
        "anim.fcurve_handle_smooth",
        text = '',
        icon='IPO_BEZIER')   
    ac_on.auto_clamp = True 
    ac_off = row.operator(
        "anim.fcurve_handle_smooth",
        text = '',
        icon='IPO_EASE_IN_OUT')
    ac_off.auto_clamp = False  
    
    
def register():
    bpy.utils.register_class(SmoothKeys)
    bpy.types.GRAPH_HT_header.append(SmoothKeysDraw)
    bpy.types.DOPESHEET_HT_header.append(SmoothKeysDraw)


def unregister():
    bpy.utils.unregister_class(SmoothKeys)
    bpy.types.GRAPH_HT_header.remove(SmoothKeysDraw)
    bpy.types.DOPESHEET_HT_header.remove(SmoothKeysDraw)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.anim.fcurve_handle_smooth()
