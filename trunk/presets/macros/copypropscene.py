import bpy
s=bpy.context.scene

p=s.render.use_placeholder
p1=s.render.use_overwrite

for s in bpy.data.scenes:
    s.render.use_placeholder=p
    s.render.use_overwrite=p1
