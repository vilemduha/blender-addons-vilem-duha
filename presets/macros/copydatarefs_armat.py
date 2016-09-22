import bpy
ob1=bpy.context.active_object
b1=ob1.data.bones.active
drfs=[]
for b2 in ob1.data.bones:
    if b2!=ob1 and b2.select:
        print(b2.name)
        drfs1=b1.xplane.datarefs
        drfs2=b2.xplane.datarefs
        drfs2.clear()
        for d1 in drfs1:
            
            d2=drfs2.add()
        #for di in  range(0,len(drfs1)):
            d2.path=d1.path
            d2.anim_type=d1.anim_type
            d2.show_hide_v1=d1.show_hide_v1
            d2.show_hide_v2=d1.show_hide_v2