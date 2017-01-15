import bpy
def mpath_draw(self, context):
    # layout = self.layout

    ob = context.object
    avs = ob.animation_visualization
    mpath = ob.motion_path

    self.draw_settings(self, context, avs, mpath)

bpy.types.OBJECT_PT_motion_paths.draw = mpath_draw
    