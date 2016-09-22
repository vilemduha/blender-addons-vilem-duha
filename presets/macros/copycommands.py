import bpy
ob1=bpy.context.active_object

drfs=[]
for ob2 in bpy.context.selected_objects:
    if ob1!=ob2:
        m1=ob1.xplane.manip
        m2=ob2.xplane.manip
        m2.enabled=m1.enabled
        m2.dataref1=m1.dataref1
        m2.cursor=m1.cursor
        m2.type=m1.type
        m2.v_on=m1.v_on
        
        m2.v_off=m1.v_off
        m2.v_down=m1.v_down
        m2.v_up=m1.v_up
  