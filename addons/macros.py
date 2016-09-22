

# mesh_relax.py Copyright (C) 2010, Fabian Fricke
#
# Relaxes selected vertices while retaining the shape as much as possible
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Macro menu",
    "author": "Vilem Novak",
    "version": (1, 0),
    "blender": (2, 70, 0),
    "location": "View3D > Toolshelf ",
    "description": "Run your snipletts as operators",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "All"}

import bpy,os

def preset_path():
    target_path = os.path.join("presets", 'macros')
    target_path = bpy.utils.user_resource('SCRIPTS',
                                                  target_path,
                                                  create=True)
    return target_path     
 
def load_presets():
    l=[]
    target_path=preset_path()
    #print(target_path,os.listdir(target_path))
    for fn in os.listdir(target_path):
        if fn[-3:]=='.py':
            l.append((fn,target_path+'\\'+fn))
    return(l)
        
def save_preset(text):
    textblock=bpy.data.texts[text]
    t=textblock.as_string()
    target_path=preset_path()
    if textblock.filepath!='':
        filepath= textblock.filepath
    else:
        filename=bpy.path.clean_name(text)
        filepath = os.path.join(target_path, filename) + '.py'
    f=open(filepath,'w')
    f.write(t)
    f.close()
    textblock.name=bpy.path.basename(filepath)
    textblock.filepath=filepath
    
class VIEW3D_PT_tools_macro(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Macro"
    #bl_context = "objectmode"
    bl_label = "macros"
    
    mlist=[]
    
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        if self.mlist==[]:
            #print( 'reload' )
            self.mlist=load_presets() 
            
        for t in bpy.data.texts:
              
            row=col.row(align=True)
            row.operator("text.run_macro", text=t.name).text=t.name
            row.operator("text.save_macro", text='', icon='SAVE_COPY').text=t.name
            row.operator("text.unlink_macro", text='', icon='X').text=t.name
            
         
        col.separator()
        for t in self.mlist:
            dupli=False
            for t1 in bpy.data.texts:
                if t[0]==t1.name:
                    dupli=True
                    #continue
            if not dupli: 
                row=col.row(align=True)
                row.operator("text.run_macro", text=t[0]).text=t[1]
                row.operator("text.open", text='', icon='FILE_TEXT').filepath=t[1]
            
class RunMacro(bpy.types.Operator):
    """run macro"""
    bl_idname = 'text.run_macro'
    bl_label = 'run macro'
    bl_options = {'REGISTER', 'UNDO'}

    text = bpy.props.StringProperty(name="text block",
                default='')
    i1 = bpy.props.IntProperty(name="int1", default=0)
    i2 = bpy.props.IntProperty(name="int2", default=0)
    i3 = bpy.props.IntProperty(name="int3", default=0)
    i4 = bpy.props.IntProperty(name="int4", default=0)
    i5 = bpy.props.IntProperty(name="int5", default=0)
    f1 = bpy.props.FloatProperty(name="float1",default=0.0)
    f2 = bpy.props.FloatProperty(name="float2",default=0.0)
    f3 = bpy.props.FloatProperty(name="float3",default=0.0)
    f4 = bpy.props.FloatProperty(name="float4",default=0.0)
    f5 = bpy.props.FloatProperty(name="float5",default=0.0)
    s1 = bpy.props.StringProperty(name="string1",default='')
    s2 = bpy.props.StringProperty(name="string2",default='')
    s3 = bpy.props.StringProperty(name="string3",default='')
    s4 = bpy.props.StringProperty(name="string4",default='')
    s5 = bpy.props.StringProperty(name="string5",default='')
    b1 = bpy.props.BoolProperty(name="bool1",default=False)
    b2 = bpy.props.BoolProperty(name="bool2",default=False)
    b3 = bpy.props.BoolProperty(name="bool3",default=False)
    b4 = bpy.props.BoolProperty(name="bool4",default=False)
    b5 = bpy.props.BoolProperty(name="bool5",default=False)
    ptemplates=[['i1','i2','i3','i4','i5'],['f1','f2','f3','f4','f5'],['s1','s2','s3','s4','s5'],['b1','b2','b3','b4','b5']]
    
    script=''
    lasttext=''
    propvals=[[0,0,0,0,0],[0,0,0,0,0],['','','','',''],[False,False,False,False,False]]
    props=[[],[],[],[]]
       
        
    def execute(self, context):
        if self.script=='':
            if bpy.data.texts.get(self.text)!=None:
                t=bpy.data.texts[self.text].as_string()
                
            else:
                f=open(self.text,'r')
                t=f.read()
                f.close()
            self.extractProperties(t)
            self.lasttext=self.text
            self.assignProperties()
        t=self.reinitProperties()
        exec(t+self.script)
        load_presets()
        return {'FINISHED'}
    
    def draw(self, context):
        l=self.layout
        l.label('autogenerated properties:')
        for pi,p in enumerate(self.props[0]):
            l.prop(self,self.ptemplates[0][pi],text=p[0])   
        for pi,p in enumerate(self.props[1]):
            l.prop(self,self.ptemplates[1][pi],text=p[0])   
        for pi,p in enumerate(self.props[2]):
            l.prop(self,self.ptemplates[2][pi],text=p[0])   
        for pi,p in enumerate(self.props[3]):
            l.prop(self,self.ptemplates[3][pi],text=p[0])
 
    '''
    def run_macro(self,text):
        if bpy.data.texts.get(text)==None:
            return
        t=bpy.data.texts[text].as_string()
        exec(t)
    '''
    def extractProperties(self,text):
        defmore=True
        end=False
        li=0
        scriptonly=''
        self.props=[[],[],[],[]]
        text=text.split('\n')
        while not end:
            
            l=text[li]
            
            if l.find('=')>-1 and defmore:
                i=l.find('=')
                #print(l[:i],l[i+1:])
                propname=l[:i]
                propvalue=eval(l[i+1:])
                
                ptype=type(propvalue)
                #print(propname,propvalue,ptype)
                #print(dir(ptype))
                
                if ptype==int:
                    self.props[0].append((propname,propvalue,ptype))
                    self.propvals[0][len(self.props[0])-1]=propvalue
                elif ptype==float:
                    self.props[1].append((propname,propvalue,ptype))
                    self.propvals[1][len(self.props[1])-1]=propvalue
                elif ptype==str:
                    self.props[2].append((propname,propvalue,ptype))
                    self.propvals[2][len(self.props[2])-1]=propvalue
                elif ptype==bool:
                    self.props[3].append((propname,propvalue,ptype))
                    self.propvals[3][len(self.props[3])-1]=propvalue
                else:
                    scriptonly+=l+'\n'
                    defmore=False
                
                #if defmore:
                    
            elif l.find('import')>-1 or len(l)==0:
                scriptonly+=l+'\n'
            else:
                defmore=False
                scriptonly+=l+'\n'
            li+=1
            if len(text)<=li:
                end=True
        #self.i1
       
        self.script=scriptonly
        
    def assignProperties(self):
        self.i1 = self.propvals[0][0]
        self.i2 = self.propvals[0][1]
        self.i3 = self.propvals[0][2]
        self.i4 = self.propvals[0][3]
        self.i5 = self.propvals[0][4]
        self.f1 = self.propvals[1][0]
        self.f2 = self.propvals[1][1]
        self.f3 = self.propvals[1][2]
        self.f4 = self.propvals[1][3]
        self.f5 = self.propvals[1][4]
        self.s1 = self.propvals[2][0]
        self.s2 = self.propvals[2][1]
        self.s3 = self.propvals[2][2]
        self.s4 = self.propvals[2][3]
        self.s5 = self.propvals[2][4]
        self.b1 = self.propvals[3][0]
        self.b2 = self.propvals[3][1]
        self.b3 = self.propvals[3][2]
        self.b4 = self.propvals[3][3]
        self.b5 = self.propvals[3][4]
    def reinitProperties(self):
        t=''
        self.propvals[0][0] = self.i1 
        self.propvals[0][1] = self.i2 
        self.propvals[0][2] = self.i3
        self.propvals[0][3] = self.i4 
        self.propvals[0][4] = self.i5 
        self.propvals[1][0] = self.f1 
        self.propvals[1][1] = self.f2 
        self.propvals[1][2] = self.f3
        self.propvals[1][3] = self.f4 
        self.propvals[1][4] = self.f5 
        self.propvals[2][0] = self.s1 
        self.propvals[2][1] = self.s2 
        self.propvals[2][2] = self.s3
        self.propvals[2][3] = self.s4 
        self.propvals[2][4] = self.s5 
        self.propvals[3][0] = self.b1 
        self.propvals[3][1] = self.b2 
        self.propvals[3][2] = self.b3
        self.propvals[3][3] = self.b4 
        self.propvals[3][4] = self.b5 
        
        for li,plist in enumerate(self.props):
            for i,p in enumerate(plist):
                if li!=2:
                    t+=p[0]+'='+str(self.propvals[li][i])+'\n'
                else:#string case
                     t+=p[0]+'="'+str(self.propvals[li][i])+'"\n'
                    
        return(t)
    
class SaveMacro(bpy.types.Operator):
    """save macro"""
    bl_idname = 'text.save_macro'
    bl_label = 'save_macro'
    bl_options = {'REGISTER', 'UNDO'}

    text = bpy.props.StringProperty(name="text block",
                default='')

    def execute(self, context):
        save_preset(self.text)
        return {'FINISHED'}
    
class EditMacro(bpy.types.Operator):
    """edit macro"""
    bl_idname = 'text.edit_macro'
    bl_label = 'edit_macro'
    bl_options = {'REGISTER', 'UNDO'}

    text = bpy.props.StringProperty(name="text block",
                default='')

    def execute(self, context):
        save_preset(self.text)
        return {'FINISHED'}
    
class UnlinkMacro(bpy.types.Operator):
    """save macro"""
    bl_idname = 'text.unlink_macro'
    bl_label = 'unlink_macro'
    bl_options = {'REGISTER', 'UNDO'}

    text = bpy.props.StringProperty(name="text block",
                default='')

    def execute(self, context):
        bpy.data.texts.remove(bpy.data.texts[self.text])
        
        return {'FINISHED'} 
    
def register():
    
    bpy.utils.register_module(__name__)
    #
    
    
    
def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()



