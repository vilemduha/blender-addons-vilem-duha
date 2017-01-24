import bpy
def mpath_draw(self, context):
    # layout = self.layout
    prefs = bpy.context.user_preferences.addons["tabs_interface"].preferences
    
    
    ob = context.object
    avs = ob.animation_visualization
    mpath = ob.motion_path
    
    if not prefs.original_panels:
        self.draw_settings(self, context, avs, mpath)
    else:
        self.draw_settings( context, avs, mpath)
def fixes():
    try:
        bpy.types.OBJECT_PT_motion_paths.draw = mpath_draw
    except:
        print("fixes couldn't be applied")