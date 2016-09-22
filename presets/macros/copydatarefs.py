import bpy
ob1=bpy.context.active_object

drfs=[]
for ob2 in bpy.context.selected_objects:
    if ob1!=ob2:
        drfs1=ob1.xplane.datarefs
        drfs2=ob2.xplane.datarefs
        drfs2.clear()
        for d1 in drfs1:
            
            d2=drfs2.add()
        #for di in  range(0,len(drfs1)):
            d2.path=d1.path
            d2.anim_type=d1.anim_type
            d2.show_hide_v1=d1.show_hide_v1
            d2.show_hide_v2=d1.show_hide_v2