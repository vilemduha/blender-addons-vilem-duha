# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Auto seam unwrap",
    "author": "Vilem Duha",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Mesh > UV Unwrap > Auto Seam Unwrap",
    "description": "Iteratively finds seams, and unwraps selected object. ",
    "warning": "",
    "wiki_url": "",
    "category": "UV",
    }


import bpy
import bmesh
import mathutils
from mathutils import *
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty,BoolProperty

def testoverlap(bm,faces):
    #print('test overlap')
    uv_layer = bm.loops.layers.uv.verify()
    
    # adjust UVs
    edges=[]
    ekeys={}
    for f in faces:
        i=0
        for l in f.loops:
            luv = l[uv_layer]
            if i==len(f.loops):
                uv1 = luv.uv
                uv2 = f.loops[0][uv_layer].uv
                
            else:
                uv1 = luv.uv
                uv2 = f.loops[i+1][uv_layer].uv
            add  = True
            uv1=uv1.to_tuple()
            uv2=uv2.to_tuple()
            if ekeys.get(uv1)==None:
                ekeys[uv1]=[uv2]
             
            elif uv2 in ekeys[uv1]:
                add=False
            else:
                ekeys[uv1].append(uv2)
            if ekeys.get(uv2)==None:
                ekeys[uv2]=[uv1]
            else:
                ekeys[uv2].append(uv1)
            if add:
                edges.append((uv1,uv2))
            #print(luv.uv)   
    #print(len(edges),len(faces))
    totiter=0
    for i1,e in enumerate(edges):
        for i2 in range(i1,len(edges)):
            totiter+=1
            if i1!=i2:
                e2=edges[i2]
                if e[0]!=e2[0] and e[0]!=e2[1] and e[1]!=e2[0] and e[1]!=e2[1]:
                    intersect = mathutils.geometry.intersect_line_line_2d(e[0],e[1],e2[0],e2[1])
                    if intersect!=None:
                        
                        #print(intersect)
                        return True
    #print(totiter)
    return False

def testratio(bm,faces):
    #print('test ratio')
    uv_layer = bm.loops.layers.uv.verify()
    
    # adjust UVs
    edges=[]
    ekeys={}
    ratios=[]
    for f in faces:
        i=0
        flen=0
        for e in f.edges:
            
            v=e.verts[0].co-e.verts[1].co
            flen+=v.length
        uvlen=0
        for l in f.loops:
            luv = l[uv_layer]
            if i==len(f.loops):
                uv1 = luv.uv
                uv2 = f.loops[0][uv_layer].uv
                
            else:
                uv1 = luv.uv
                uv2 = f.loops[i+1][uv_layer].uv
            v=uv2-uv1
            uvlen+=v.length
        if uvlen!=0:
            ratio=flen/uvlen
        else:
            ratio=flen/0.0000000000000000001
          
        ratios.append(ratio)
    finalratio=0
    maxratio=-100000000
    minratio = 1000000000000000
    for r in ratios:
        finalratio+=r
        minratio = min(r,minratio)
        maxratio = max(r,maxratio)
    finalratio = finalratio / len(ratios)
    maxratio=max(finalratio/minratio,maxratio/finalratio)
    return maxratio
    
#def getCommonSeamChunks(island):
    
def main(context,
         grow_iterations,
         merge_iterations,
         small_island_threshold,
         deformation_ratio_threshold,
         island_margin):


    wm = bpy.context.window_manager

    tot=20000
    wm.progress_begin(0, tot)
    

    ob = bpy.context.active_object

    all = False

    me = ob.data
    me.show_edge_seams = True

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True,  margin=island_margin)
    bpy.ops.mesh.mark_seam(clear=True)
    
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.editmode_toggle()
    basenormal = Vector((0,0,1))
    normals = []

    done={}
     
    bpy.ops.object.editmode_toggle()

    #for a in range(0,grow_iterations):
     #   bpy.ops.mesh.select_more()
        #newsel = []
        #for 

    nislands = 0
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    islands=[]
    islandindices={}

    while not all:
        
       
        
        for i,p in enumerate(bm.faces):
            
            if done.get(i) == None:
                p.select=True
                done[i]=True
                break
        
        basenormal = p.normal.copy()
        lensel = 1
        nf = [p]
        stop=False
        normals=[basenormal]
        nsum=basenormal.copy()
        sfaces=[p]
        tempdone={}
        
        #case when the selected face is allready isolated can lead to bad islands through single vertex.
        #allseam=True
        #for e in p.edges:
        #    if not e.seam:
        #        allseam=False
        #if not allseam:
        
        for a in range(0,grow_iterations):
           # if len(islands)==13 and a==2:
            #    fal
            selected_faces = nf
            #print(len(selected_faces))
            nf = []
            if not stop:
                for f in selected_faces:
                    for vert in f.verts:
                        
                        linkedv = vert.link_faces
                        for face in linkedv:
                            if not face.select and tempdone.get(face.index)==None:
                                if len(sfaces)>5:
                                    angle = face.normal.angle(basenormal)
                                else:
                                    angle = 0
                                #print(angle)
                                tempdone[face.index]=True
                                if done.get(face.index)==None :#and angle<anglelimit :
                                    
                                    nf.append(face)
                                    normals.append(face.normal)
                                    nsum+=face.normal
                                    basenormal = nsum.normalized()
                                    #basenormal=(basenormal+face.normal*(1/lensel)).normalized()
                                    lensel+=1 
                                #else:
                                   # stop=True
                
                if not stop:
                    for face in nf:
                        face.select = True 
                    check=nf[:]
                    while len(check)>0:#sometimes, neighbour faces are selected only through 1 vertex which is actually a separate island. This is here to avoid that.
                        f=check.pop()
                        finishcheck=False
                        isolationgroup=[f]
                        isolationcheck=[f]
                        while len(isolationcheck)>0:
                            f1=isolationcheck.pop()
                            for e in f1.edges:
                                for f2 in e.link_faces:
                                    if f2!=f1 and f2 in check:
                                        isolationgroup.append(f2)
                                        check.remove(f2)
                                        isolationcheck.append(f2)
                                    elif f2 in sfaces:
                                        isolationgroup=[]
                                        isolationcheck=[]
                        if len(isolationgroup)>0:
                            for f in isolationgroup:
                                f.select=False
                                nf.remove(f)
                                nsum-=f.normal
                                lensel-=1
                                
                        '''
                        neighbour=False
                        for e in f.edges:
                            allsel=True
                            for lf in e.link_faces:
                                if not lf.select or (lf!=f and lf in nf):
                                    allsel=False
                            if allsel:
                                neighbour=True
                        
                        if not neighbour:
                            
                            f.select=False
                            nf.remove(f)
                            nsum-=f.normal
                            lensel-=1
                            '''
                    for face in nf:
                              
                        sfaces.append(face)
                    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True,  margin=island_margin)
                    
                    overlap = testoverlap(bm,sfaces)
                    #overlap = False
                    ratio = testratio(bm,sfaces)
                    
                    if overlap or ratio>deformation_ratio_threshold:
                        stop=True
                        for f in nf:
                            f.select = False
                            #sfaces.remove(f)
                        nsfaces=[]
                        for f in sfaces:
                            if f.select:
                                nsfaces.append(f)
                        sfaces=nsfaces
                        break
                else:
                    break;
                    
            

        #averaged normal
        #normal = Vector((0,0,0))
        #for n in normals:
         #  normal+=n
            
        #normal.normalize()
        #removed = 0
        #for f in sfaces:
        #    if f.select:
        #        angle = f.normal.angle(normal) 
         #       if angle>anglelimit:
         #           f.select=False  
         #           removed += 1
        #if removed == len(sfaces):# at keast 2 faces
        #    sfaces[0].select = True
        #    sfaces[1].select=True
        
                                  
        for f in sfaces:
            for edge in f.edges:
                linked = edge.link_faces
                for face in linked:
                    if not face.select:
                        edge.seam=True
        #if len(islands)==17:
        #   fal

        islands.append(sfaces[:])
        
        #print(lensel)
        for f in sfaces:
            
            done[f.index]=True
            f.select=False
                
        if len(done) == len(bm.faces) or len(done)>100000:
            all = True
        nislands+=1
        wm.progress_update(nislands)
        print('seed island ' ,len(islands))
               

    all = False
    done = {}
    ####filter single-face islands and try to connect them with islands in an optimal way(longest edge gets merged). no overlap check so far.
    #fal
    islands.sort(key=len)
    for i,island in enumerate(islands):
        for f in island:
            #if i == 1:
            #    f.select=True
            islandindices[f.index]=i

    print('try to merge small islands')
    print(len(islands))
    #fal
    #for f in bm.faces:
        #print(islandindices[f.index])
    #fal
    #done = False
    #while not done:
    totaltests=0
    for a in range(0,merge_iterations):
        merged=0
        
        print(a)    
        i1idx=0
        while i1idx<len(islands):    
            island = islands[i1idx]
            #if len(f.edges)<5:
            #f.select=True
            if len(island)<small_island_threshold:
                
                
                #find all border islands
                bislandsidx=[]#just for checks 
                bislands=[]
                i1seams=0
                
                for f in island:
                    f.select=True
                    for i,e in enumerate(f.edges):
                        if e.seam:
                            i1seams+=1
                            for f in e.link_faces:
                                if not f.select:
                                    island2idx = islandindices[f.index]
                                    
                                    if not island2idx in bislandsidx:
                                        bislandsidx.append(island2idx)
                                        bislands.append([island2idx,True,1000,0,0,[]]) # index, overlap, ratio, common seams, total seams,erase seams
                #print(bislands)
                for islandinfo in bislands:
                    island2idx = islandinfo[0]
                    island2 = islands[island2idx]
                    
                    commonseams = 0
                    i2seams = 0
                    for f in island2:
                        f.select=True
                        for e in f.edges:
                            if e.seam:
                                i2seams+=1
                    
                    '''
                    #clean inner seams
                    for f in island:
                        for e in f.edges:
                            if e.seam:
                                i2seams += 1
                                lf = e.link_faces
                                if len(lf)>1:
                                    allsel=True
                                    for f1 in e.link_faces:
                                        if not f1.select:
                                            allsel=False
                                    if allsel: #remove border seams!
                                        e.seam=False
                                        commonseams+=1
                      '''
                    #get connecting seam rows
                    seamchunks=[]
                    edone={}
                   
                        
                    for f in island:
                        for e in f.edges:
                            if e.seam and edone.get(e.index)==None:
                                allsel=True
                                lf=e.link_faces
                                
                                
                                for f1 in lf:
                                    if not f1.select :
                                        allsel=False
                                 
                                if allsel:
                                    allsame=True
                                    
                                    edone[e.index]=True
                                    iidx = islandindices[lf[0].index]
                                    for f1 in lf:
                                        if islandindices[f1.index]!=iidx:
                                             allsame=False
                                             
                                    if not allsame: 
                                        seamchunk=[e]
                                        check=[e]
                                        commonseams+=1
                                        while len(check)>0:
                                            le=[]
                                            e1 = check.pop()
                                            #print(len(check),len(seamchunk))
                                            v1=e1.verts[0]# on crossings we have to split the seams into more segments
                                            v2=e1.verts[1]
                                            
                                            
                                            for v in e1.verts:
                                                vseams=0
                                                for e in v.link_edges:
                                                    if e.select and e.seam:
                                                        vseams+=1
                                                if vseams<3:
                                                    le.extend(v.link_edges)
                                            
                                            
                                            for e2 in le:
                                                if e2.select and e2.seam and edone.get(e2.index)==None:
                                                    allsel=True
                                                    lf = e2.link_faces
                                                    for f2 in lf:
                                                        if not f2.select:
                                                            allsel=False
                                                        
                                                    if allsel: 
                                                        allsame=True
                                                        iidx  = islandindices[lf[0].index]
                                                        for f2 in lf:
                                                            if islandindices[f2.index]!=iidx:
                                                                 allsame=False
                                                            #print(islandindices[f2.index],i1idx)
                                                        if not allsame: 
                                                            check.append(e2)
                                                            seamchunk.append(e2)
                                                            commonseams+=1
                                                    edone[e2.index]=True
                                        seamchunks.append(seamchunk)
                    
                    if len(seamchunks)>0:
                       # print('seamchunks',len(seamchunks))
                        eraseseam=seamchunks[0]
                        #break
                        maxlen=0
                        if len(seamchunks)>1:
                            #print(seamchunks)
                            
                            for sch in seamchunks:
                                if len(sch)>maxlen:
                                    eraseseam=sch
                                    maxlen=len(sch)
                                 
                        for e in eraseseam:
                            #e.select=True
                            e.seam=False
                        newislandfaces = []
                        newislandfaces.extend(island)
                        newislandfaces.extend(island2)
                        
                            #now 
                        #f.edges[maxlenidx].seam=False
                        if 0:#len(island2)>2 and commonseams/i1seams<.08 or commonseams/i2seams<0.08:#just not to unwrap unnecessarily
                            overlap=True
                            qualityratio=10
                        else:
                            bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True,  margin=island_margin)
                                    
                            overlap = testoverlap(bm,newislandfaces)
                            qualityratio = testratio(bm,newislandfaces)
                        islandinfo[1]=overlap
                        islandinfo[2]=qualityratio
                        islandinfo[3]=commonseams
                        islandinfo[4]=i2seams
                        islandinfo[5]=eraseseam
                        #print(islandinfo)
                        #print(qualityratio)
                        for f in island2:
                            f.select = False
                        for f in island:
                            f.select=True
                        for f in island:#returning seams here , we are testing several merge options.
                            for e in f.edges:
                                lfaces = e.link_faces
                                if len(lfaces)>1:    
                                    for lf in lfaces:
                                        if lf.select==False:
                                            e.seam=True
                        
                                    
                besti=-1
                bestratio=10000
                bestseamcount =-100
                #print(bislands)
                for i,islandinfo in enumerate(bislands):# comparison of quality, currently the longest seam gets preference, so islands are not too snake-y
                    
                    if not islandinfo[1] and islandinfo[2]<deformation_ratio_threshold:
                        #if bestratio>islandinfo[2]:
                        #    bestratio=islandinfo[2]
                        #    besti = i
                        
                        if bestseamcount<islandinfo[3]:
                            besti=i
                            bestseamcount=islandinfo[3]
                        
                #print(bestratio,islandinfo)
                totaltests+=1
                #if len(bislands)==1:
                    #print(seamchunks)  
                    #besti=0
                if besti>-1 :#or en(bislands)==1:
                    
                    #if len(island)==1:
                    #    print(seamchunks)  
                    iinfo = bislands[besti]
                    island2idx = iinfo[0]
                    island2 = islands[island2idx]
                    for f in island2:
                        f.select=True
                        
                    for e in iinfo[5]:
                        e.seam=False
                    
                    island.extend(island2)
                    #islands[i1idx]=island.extend(island2)
                    
                    for f in island2:
                        islandindices[f.index] = i1idx
                    for dkey in islandindices.keys():
                       if islandindices[dkey]>island2idx:
                           islandindices[dkey]-=1
                    islands.pop(island2idx)
                    
                    nislands-=1
                    print('merge islands ', nislands, 'cycle ', a)
                    merged+=1
                    wm.progress_update(nislands)
                for f in island:
                    f.select=False
                   
            i1idx +=1
        if merged==0:
           break
            
    for f in bm.faces:
        f.select=True
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=island_margin)
    for f in bm.faces:
        f.select=False        
    print('total tests', totaltests)             
    print('nislands')
    print(nislands,len(islands))
    bmesh.update_edit_mesh(me, True)  
   
        
    wm.progress_end()
    #bpy.ops.object.editmode_toggle()

class AutoSeamUnwrap(Operator):
    """iteratively finds seams, and unwraps selected object. """ \
    """can take a long time to compute""" \
    """doesn't produce 'pretty' islands but works good for getting low number of islands on complex meshes."""
    bl_idname = "uv.auto_seams_unwrap"
    bl_label = "Auto seams unwrap"
    bl_options = {'REGISTER', 'UNDO'}





    grow_iterations = IntProperty(
            name="Initial island grow iterations",
            description="This determines initial size of islands",
            min=0, max=50,
            default=2,
            )
    merge_iterations = IntProperty(
            name="Merging step iterations",
            description="more iterations means bigger, but sometimes more complex islands",
            min=0, max=50,
            default=2,
            )
    small_island_threshold = IntProperty(
            name="Small island size limit",
            description="only islands smaller than the size will be merged.",
            min=0, max=500,
            default=50,
            )
    deformation_ratio_threshold = FloatProperty(
            name="Deformation ratio threshold",
            description="What deformation is tollerated in the unwrapped islands",
            min=1.01, max=10,
            default=1.8,
            )
       
    island_margin = FloatProperty(
            name="Island Margin",
            description="Margin to reduce bleed from adjacent islands",
            min=0.0, max=1.0,
            default=0.0002,
            )
    '''
    grow = 2
    merge_iterations = 6
    anglelimit = .1
    smallislandthreshold = 50
    deformation_ratio_threshold = 2
    '''

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(context,
             self.grow_iterations,
             self.merge_iterations,
             self.small_island_threshold,
             self.deformation_ratio_threshold,
             self.island_margin
             )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(AutoSeamUnwrap.bl_idname)
    self.layout.separator()

    
def register():
    bpy.utils.register_class(AutoSeamUnwrap)
    bpy.types.VIEW3D_MT_uv_map.append(menu_func)
    #bpy.utils.register_manual_map(add_object_manual_map)
    #bpy.types.INFO_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(AutoSeamUnwrap)
    #bpy.utils.unregister_manual_map(add_object_manual_map)
    #bpy.types.INFO_MT_mesh_add.remove(add_object_button)



if __name__ == "__main__":
    register()
