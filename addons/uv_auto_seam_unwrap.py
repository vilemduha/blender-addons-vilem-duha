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
import math
import mathutils
from mathutils import *
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty,BoolProperty
import itertools


def getIslands(bm):
	
	#bm = bmesh.from_edit_mesh(me)
	for f in bm.faces:
		f.select=False
	all=False
	done={}
	islands=[]
	while not len(done)>=len(bm.faces):
		island=[]
		for i,p in enumerate(bm.faces):
				
			if done.get(i) == None:
				p.select=True
				done[i]=True
				island.append(p)
				break
		nf = [p]
		while len(nf)>0:
			selected_faces = nf
			nf = []
			
			for f in selected_faces:
				for edge in f.edges:
					if edge.seam==False:
						linkede = edge.link_faces
						for face in linkede:
							if not face.select and done.get(face.index)==None:
								done[face.index]=True
								nf.append(face)
								face.select=True
								island.append(face)
		islands.append(island)
		for f in island:
			f.select=False
	return islands

def testOverlap(bm,faces):
    #print('test overlap')
    uv_layer = bm.loops.layers.uv.verify()
    
    # adjust UVs
    edges=[]
    ekeys={}
    for f in faces:
        i=0
        for l in f.loops:
            luv = l[uv_layer]
            if i==len(f.loops)-1:
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
                #print('repeating uv')
                add=False
            else:
                ekeys[uv1].append(uv2)
            if ekeys.get(uv2)==None:
                ekeys[uv2]=[uv1]
            else:
                ekeys[uv2].append(uv1)
            if add:
                edges.append((uv1,uv2))
            i+=1
            #print(luv.uv)   
    #print(len(edges),len(faces))
    totiter=0
    for i1,e in enumerate(edges):
        for i2 in range(i1+1,len(edges)):
            totiter+=1
            #if i1!=i2:
            e2=edges[i2]
            if e[0]!=e2[0] and e[0]!=e2[1] and e[1]!=e2[0] and e[1]!=e2[1]:#no common vertex, since that's an intersection too.
                intersect = mathutils.geometry.intersect_line_line_2d(e[0],e[1],e2[0],e2[1])
                if intersect!=None:
                    
                    #print(intersect)
                    return True
    #print(totiter)
    return False
'''
def testRatio(bm,faces):
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
 '''
def testAngleRatio(bm,faces):
    #print('test ratio')
    uv_layer = bm.loops.layers.uv.verify()
    
    # adjust UVs
    edges=[]
    ekeys={}
    ratios=[]
    for f in faces:
        i=0
        flen=0
        for i1 in range (0,len(f.verts)):
            if i1<len(f.verts)-1:
                i2 = i1+1
            else:
                i2 = 0
            if i1<len(f.verts)-2:
                i3 = i1+2
            else:
                i3 = i1-len(f.verts)+2
            v1 = f.verts[i2].co - f.verts[i1].co
            v2=f.verts[i3].co-f.verts[i2].co
            
            angle_mesh = v1.angle(v2)
            
            l1 = f.loops[i1]
            l2 = f.loops[i2]
            l3 = f.loops[i3]
            v1 = l2[uv_layer].uv - l1[uv_layer].uv
            v2 = l3[uv_layer].uv - l2[uv_layer].uv
            angle_uv=0
            if v1.length!=0 and v2.length!=0:
                angle_uv = v1.angle(v2)
            ratio = abs(angle_mesh-angle_uv)
            ratios.append(ratio)
    finalratio=0
    maxratio=-100000000
    minratio = 1000000000000000
    for r in ratios:
        finalratio+=r
        maxratio = max(r,maxratio)
    finalratio = finalratio / len(ratios) + 1
    
    maxratio=max(finalratio,maxratio+1) 
   # print(finalratio,maxratio)

    return maxratio

def testPerimeterRatio(bm, faces, by_seams = True): 
    
    perimeter=0
    
    totalarea = 0
    totseams = 0
    totedges=0
    
    
    
    
    for f in faces:
        totalarea += f.calc_area()
        for e in f.edges:
            if (by_seams and e.seam):
                perimeter+=e.calc_length()
                totseams+=1
            if not by_seams:
                for f1 in e.link_faces:
                    if f1 not in faces or len(e.link_faces) == 1:
                        perimeter+=e.calc_length()
                        totseams+=1
        totedges+=len(f.edges)#adds number of tris actually
    
    #fotak ad.faltus@gmail.com
    
    divider = totedges / len(faces) #
    perimeter_length_ratio = (perimeter/divider)/ math.sqrt(totalarea)
    
    perimeter_count_ratio = (totseams/divider) / math.sqrt(len(faces))
    #print(perimeter_length_ratio)
    perimeter_ratio = (2*perimeter_length_ratio + perimeter_count_ratio)/3
    return  perimeter_ratio
    
def testAreaRatio(bm,faces):
    #print('test ratio')
    uv_layer = bm.loops.layers.uv.verify()
    
    ratios=[]
    #totarea_mesh = 0
    for f in faces:
        i=0
        flen=0
        area_mesh=0
        area_uv = 0
        
        for i1 in range (0,len(f.verts)-2):
           
            if i1<len(f.verts)-1:
                i2 = i1+1
            else:
                i2 = 0
            if i1<len(f.verts)-2:
                i3 = i1+2
            else:
                i3 = i1-len(f.verts)+2
            #print(f.verts[i1], f.verts[i2], f.edges[i1].verts[0], f.edges[i1].verts[1])
            v1 = f.verts[i2].co - f.verts[i1].co
            v2=f.verts[i3].co-f.verts[i2].co
            
            area_mesh += mathutils.geometry.area_tri(f.verts[i1].co,f.verts[i2].co,f.verts[i3].co)
            
            l1 = f.loops[i1]
            l2 = f.loops[i2]
            l3 = f.loops[i3]
            area_uv += mathutils.geometry.area_tri(l1[uv_layer].uv,l2[uv_layer].uv,l3[uv_layer].uv)
            #totalarea_uv+=area_uv
            
        if area_uv==0:
            if area_mesh ==0:
                area_uv = 1
            else:    
                area_uv = 0.0000000000001
            
        ratio = area_mesh/area_uv
            
        ratios.append(1+ (ratio-1))#  * area_mesh) #smaller faces become less important
        #totarea_mesh += area_mesh
    finalratio=0
    maxratio=-100000000
    minratio = 1000000000000000
    for r in ratios:
        finalratio+=r
        minratio = min(r,minratio)
        maxratio = max(r,maxratio)

    finalratio = finalratio / len(ratios)# get normal ratio
    #now get ratio!
    if finalratio==0:
        finalratio = 0.0000000000000000001
    if minratio==0:
        minratio = .1
    maxratio=math.sqrt(max(finalratio/minratio,maxratio/finalratio))
    return maxratio
    
def unwrap(op):
    bpy.ops.uv.unwrap(method='CONFORMAL', fill_holes=True,  margin=op.island_margin)

def getFaceNormalRatio(face):
    maxn = 0
    maxn = max(maxn,abs(face.normal.x))
    maxn = max(maxn,abs(face.normal.y))
    maxn = max(maxn,abs(face.normal.z))
    #print(maxn)
    return maxn
    
def seedIslands(context, bm,  op):
    wm = bpy.context.window_manager
    
    ob=bpy.context.active_object
    #me=ob.data
    
    basenormal = Vector((0,0,1))
    normals = []

    done={}
     
    normalsortfaces = bm.faces[:]
    normalsortfaces.sort(key = getFaceNormalRatio)
    #for a in range(0,grow_iterations):
     #   bpy.ops.mesh.select_more()
        #newsel = []
        #for 

    nislands = 0
    islands=[]
    
    all = False
    if 0:#op.grow_iterations == 0 :# if the user sets 0 in this, it means 1 island = 1 face.
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        print('islands to faces')
        for f in bm.faces:
            islands.append([f])
        return islands
    else:
        while not all:
            
           
            
            for p in normalsortfaces:
                
                if done.get(p.index) == None:
                    p.select=True
                    done[p.index]=True  #done[i]=True
                    break
            
            
                        
            
            lensel = 1
            nf = [p]
            stop=False
            sfaces=[p]
            tempdone={}
            
            
            sel_flat = True
            if sel_flat:
                bpy.ops.mesh.faces_select_linked_flat(sharpness=0.0174533)
                #if len(islands)==5:fal
                for f in bm.faces:
                    if done.get(f.index) == None and f.select:
                        nf.append(f)
                        tempdone[f.index]=True
                        sfaces.append(f)
                        #done[f.index]=True
                    else:
                        f.select=False
                    #f.select=False
                    #
                p.select = True
            #fal
                     
            
            
            #case when the selected face is allready isolated can lead to bad islands through single vertex.
            #allseam=True
            #for e in p.edges:
            #    if not e.seam:
            #        allseam=False
            #if not allseam:
            
            for a in range(0,op.grow_iterations):
               # if len(islands)==13 and a==2:
                #    fal
                tempdone={}
                #print(len(selected_faces))
                selected_faces = nf
                nf = []
                
                   
                
                if not stop:
                    for f in selected_faces:
                        for vert in f.verts:
                            
                            linkedv = vert.link_faces
                            for face in linkedv:
                                if not face.select and tempdone.get(face.index)==None:
                                    tempdone[face.index]=True
                                    if done.get(face.index)==None :#and angle<anglelimit :
                                        
                                        nf.append(face)
                                        lensel+=1 
                #print(len(nf))                    
                if not stop:
                    #if a ==1:
                    #    fal
                    for face in nf:
                        face.select = True 
                    #if len(islands)==20:
                        #fal
                    
                    #fals
                    #if a ==1:
                    #    fal
                    #if not sel_flat or a > 0:
                    check=sfaces[:]
                    check.extend(nf)
                    #sometimes, neighbour faces are selected only through 1 vertex which is actually a separate island. This is here to avoid that.
                    f=check.pop(0)
                    finishcheck=False
                    # isolationgroup=sfaces[:]
                    isolationcheck=[f]
                    while len(isolationcheck)>0:
                        f1=isolationcheck.pop()
                        #print(len(isolationcheck), len(check))
                        for e in f1.edges:
                            for f2 in e.link_faces:
                                if f2!=f1 and f2 in check:
                                    #isolationgroup.append(f2)
                                    check.remove(f2)
                                    isolationcheck.append(f2)
                               
                                    
                    if len(check)>0:
                        #print(a,'separate islands selected', len(check), len(nf),nf,check)
                        #fal
                        for f in check:
                            f.select=False
                            #print(a)
                            if f in nf:
                                nf.remove(f)
                            else:
                                sfaces.remove(f) # case where select linked does overflow
                            #nsum-=f.normal
                            lensel-=1
                        #fal     
                    #if a == 1:
                    #    fal
                    #fal
                    
                    
                    #fal
                    testfaces = sfaces[:]
                    testfaces.extend(nf)
                    
                    disqualify = False
                    # perimeter doesn't need unwrap, so it helps to disqualify some islands allready before the heaviest operation.
                    perimeter_ratio = testPerimeterRatio(bm,testfaces, by_seams = False)
                    if perimeter_ratio>op.island_shape_threshold:
                        disqualify = True
                        #print('disqual')
                    else:
                        unwrap(op)
                        #print(dir(bm))
                        
                        overlap = testOverlap(bm,testfaces)
                        #overlap = False
                        area_ratio = testAreaRatio(bm,testfaces)
                        
                        angle_ratio = testAngleRatio(bm,testfaces)
                       # print(overlap,area_ratio,perimeter_ratio,angle_ratio)
                        #fal
                        if overlap or area_ratio>op.area_deformation_ratio_threshold or angle_ratio>op.angle_deformation_ratio_threshold :
                            disqualify = True
                    if disqualify:
                        stop=True
                        for f in nf:
                            f.select = False
                            #sfaces.remove(f)
                            
                        
                        break
                    else:
                        sfaces = testfaces
                        for f in sfaces:
                            done[f.index]=True
                            
                else:
                    break;
                        
                                      
            for f in sfaces:
                for edge in f.edges:
                    linked = edge.link_faces
                    for face in linked:
                        if not face.select or len(linked)==1:
                            edge.seam=True
            #fal
           

            islands.append(sfaces[:])
            
            #if len(islands)==20:
              # fal  
            #print(lensel)
            #sfal
            for f in sfaces:
                #if f.index == 397:
                    #fal
                    #print('here heya hou')
                done[f.index]=True
                f.select=False
                 
            if len(done) == len(bm.faces) or len(done)>10000000:
                all = True
            nislands+=1
            wm.progress_update(nislands)
            print('seed island ' ,len(islands))
        #print(done[397 ])  
        
        return islands

def anysel(e):
    for f in e.link_faces:
        if f.select:
            return True
    return False
    
def allsel(e):
    a=True
    for f in e.link_faces:
        if not f.select:
            a=False
    return a    
    
def seedPerfectIslands(context, bm,  op):
    wm = bpy.context.window_manager
    
    ob=bpy.context.active_object
    me=ob.data
    
    basenormal = Vector((0,0,1))
    normals = []

    done={}
     
    
    #for a in range(0,grow_iterations):
     #   bpy.ops.mesh.select_more()
        #newsel = []
        #for 

    nislands = 0
    islands=[]
    
    all = False
    while not all:
        
       
        
        for i,p in enumerate(bm.faces):
            
            if done.get(i) == None:
                p.select=True
                #done[i]=True
                break
        
        
                    
        
        lensel = 1
        nf = [p]
        stop=False
        sfaces=[p]
        '''
        sel_flat = True
        if sel_flat:
            bpy.ops.mesh.faces_select_linked_flat(sharpness=0.0174533)
            for pdesel in bm.faces:
                if done.get(pdesel.index) == True and pdesel.select:
                    pdesel.select=False
                elif pdesel.select:
                    nf.append(pdesel)
                    sfaces.append(pdesel)
        '''            
        tempdone={}
        done[i]=True
        #todo optimize this, just get those edges and mark them!
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.loop_to_region()

        trygrowth = 30
        finished = False
        iters = 0
        while iters <trygrowth and not finished:
            testsets=[[],[],[],[],[],[],[],[],[],[],[]]#set of seams to erase/create each test step.
            
            
            initseams=[]
            for f in sfaces:
                for e in f.edges:
                    if e.seam:
                        initseams.append((e.index,True))
                    else:
                        initseams.append((e.index,False))
            
            for f in sfaces:
                for e in f.edges:
                    lf = e.link_faces
                    for f in lf:
                        if not f.select and tempdone.get(f.index)== None:#avoid more iterations on same 
                            tempdone[f.index] = True
                        if done.get(f.index) == None:
                            seamset = [f,[],[]]#face, remove seams, add seams
                            for e1 in f.edges:#back test how many common seams are there
                                a = anysel(e1)
                                if a:
                                    seamset[1].append(e1)
                                else:
                                    seamset[2].append(e1)
                            testsets[0].append(seamset)
                            if len(seamset[1])>1:# add ALL iterations!!!!
                                for i in range(1,len(seamset[1])):
                                    c = itertools.combinations(seamset[1], i)
                                    for t in c:
                                        #print('wtf')
                                        #print(t)
                                        nseamset=[f,t,seamset[2].copy()]
                                        
                                        for testseam in seamset[1]:
                                            if testseam not in t:
                                                nseamset[2].append(testseam)
                                        testsets[i].append(nseamset)
            #print(len(testsets))
            #print(testsets)
            #fad
            qualityratios=[]
            
            for testsetlayer in testsets:
                for testset in testsetlayer:
                    testset[0].select=True
                    
                    for e in testset[1]:
                        e.seam=False
                        #print(e.index)
                    for e in testset[2]:
                        e.seam = True
                    islandfaces = [testset[0]]
                    islandfaces.extend(sfaces)
                    disqualified, quality = testIslandQuality(context,bm,  islandfaces, op)
                    if not disqualified:
                        qualityratios.append((testset,quality))
                    #bring back orig seams - could be optimized, now does whole island.
                    for e in testset[2]:# is this ok? am I not erasing some seams? I am I guess.
                        e.seam=False
                    testset[0].select = False
                    for ed in initseams:
                        bm.edges[ed[0]].seam = ed[1]
                    #if len(qualityratios)>=10:
                    #    break;
                if len(qualityratios)>0:
                    break;
            bestqual=100000000
            best = None
            for qt in qualityratios:
                if qt[1]<bestqual:
                    bestqual = qt[1]
                    best = qt[0]
            if best != None:
                sfaces.append(best[0])
                best[0].select=True
                done[best[0].index]=True
                for e in best[1]:
                    e.seam=False
                    #print(e.index)
                for e in best[2]:
                    e.seam = True
            iters+=1
            #print(iters)
        islands.append(sfaces.copy())
        for f in sfaces:
            
            done[f.index]=True
            f.select=False
                
        if len(done) == len(bm.faces) or len(done)>100000:
            all = True
        nislands+=1
        wm.progress_update(nislands)
        print('seed island ' ,len(islands))
        
    return islands             

   
    
def testIslandQuality(context,bm,  islandfaces, op, pass_orig_perimeter_ratio = False, orig_perimeter_ratio = None):
    qualityratio = 10
    disqualified = False
    
    perimeter_ratio = testPerimeterRatio(bm,islandfaces)
    if pass_orig_perimeter_ratio:
        if perimeter_ratio<orig_perimeter_ratio and perimeter_ratio>op.island_shape_threshold:
            perimeter_ratio = op.island_shape_threshold*.99
            print ('merge ugly islands!')
            
    if (perimeter_ratio>op.island_shape_threshold ):
        disqualified = True
        #print('ditch ugly island!')
    else:
        unwrap(op)
        
        
        area_ratio = testAreaRatio(bm,islandfaces)
        
                            
        angle_ratio = testAngleRatio(bm,islandfaces)
        
        #commonseam_ratio = min(i1seams,i2seams)/ (commonseams * 3)
        
        total_weight = op.area_weight + op.angle_weight + op.island_shape_weight# + op.commonseam_weight

        qualityratio = (area_ratio * op.area_weight+ perimeter_ratio *op.island_shape_weight  + angle_ratio * op.angle_weight) /total_weight #+ commonseam_ratio * op.commonseam_weight
        
        #allow to pass island with bad parimeter,if perimeter improves.
        
        
        if area_ratio> op.area_deformation_ratio_threshold or angle_ratio> op.angle_deformation_ratio_threshold :
            #some zipping conditions could start here.
            #if 
            #else:
            
            disqualified = True
        else:
            disqualified = testOverlap(bm,islandfaces)
    
        print('totalqual %f; area %f; perimeter %f; angle %f;' % (qualityratio, area_ratio, perimeter_ratio,angle_ratio))
    #qualityratio = qualityratio / 3
    
    return disqualified, qualityratio;
    
    
def mergeIslands(context,
             bm, islands,
             op):
    nislands = len(islands)
    wm = bpy.context.window_manager

   #idea
   #kazdy s kazdym test(vzdy jen jednou), ma svou kvalitu. 
   #island uz musi byt objekt
   #dvojice do listu, seradit podle kvality?
   #vsechny zamergovat podle poradi, ty ktere jsou spojeny musi byt preskoceny (done nebo neco podobneho)
   #!!!! uspora vykonu, rovnomernejsi velikost vysledku.
    
    ob=bpy.context.active_object
    me=ob.data
    
    all = False
    done = {}
    ####filter single-face islands and try to connect them with islands in an optimal way(longest edge gets merged). no overlap check so far.
    #fal
    islandindices={}
    islands.sort(key=len)
    for i,island in enumerate(islands):
        for f in island:
            #if i == 1:
            #    f.select=True
            islandindices[f.index]=i
            #if len(island)!=1:
            #    print(len(island))
    #for f in bm.faces:
    #    if islandindices.get(f.index) == None:
    #        print('bad face', f.index)
    #        f.select=True
    #fal
    print('try to merge small islands')
    #print(len(islands))
    #print(islands)
    #fal
    #for f in bm.faces:
        #print(islandindices[f.index])
    #fal
    #done = False
    #while not done:
    totaltests=0
    for a in range(0,op.merge_iterations):
        merged=0
        
        print(a)    
        i1idx=0
        while i1idx<len(islands):    
            island = islands[i1idx]
            #if len(f.edges)<5:
            #f.select=True
            if len(island)<op.small_island_threshold:
                
                
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
                orig_perimeter_ratio =  testPerimeterRatio(bm,island)
                        
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
                        commonlength = 0
                        for e in eraseseam:
                            #e.select=True
                            e.seam=False
                            commonlength+= e.calc_length()
                        newislandfaces = []
                        newislandfaces.extend(island)
                        newislandfaces.extend(island2)
                        
                            #now 
                        #f.edges[maxlenidx].seam=False
                        
                        overlap, qualityratio = testIslandQuality(context,bm,  newislandfaces, op, pass_orig_perimeter_ratio = True, orig_perimeter_ratio = orig_perimeter_ratio)
                        islandinfo[1]=overlap
                        islandinfo[2]=qualityratio
                        islandinfo[3]=commonlength#commonseams
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
                    
                    if not islandinfo[1]:# and islandinfo[2]<deformation_ratio_threshold:
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
    unwrap(op)
    for f in bm.faces:
        f.select=False        
    print('total tests', totaltests)             
    print('nislands')
    print(nislands,len(islands))
    #me = bpy.context.active_object.data
    #bmesh.update_edit_mesh( True)  
    pass;
    
def seed_with_merge(context, op):

    wm = bpy.context.window_manager

    tot=20000
    wm.progress_begin(0, tot)
    
    ob = bpy.context.active_object

    me = ob.data
    me.show_edge_seams = True
    if op.init_seams:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        unwrap(op)
        bpy.ops.mesh.mark_seam(clear=True)
        
        bpy.ops.mesh.select_all(action='DESELECT')
        
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table() 
       # seedPerfectIslands(context, bm,  op)
        islands = seedIslands(context, 
                bm, op)
    else:   
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.mark_seam(clear=True)
        bpy.ops.uv.seams_from_islands()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()    
        islands = getIslands(bm)
        
        
    mergeIslands(context,
        bm, islands,
        op)
    
   
        
    wm.progress_end()
    #bpy.ops.object.editmode_toggle()

class testIsland(Operator):
    bl_idname = "uv.auto_seams_testisland"
    bl_label = "Auto seams test island"
    bl_options = {'REGISTER', 'UNDO'}
    
    init_seams = BoolProperty( name="Start with own seams",
            description="If on, totally new seams will be created, otherwise UV island merge will be performed",default=True)



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
            default=3,
            )
            
    island_margin = FloatProperty(
            name="Island Margin",
            description="Margin to reduce bleed from adjacent islands",
            min=0.0, max=1.0,
            default=0.0002,
            )
            
    small_island_threshold = IntProperty(
            name="Small island size limit",
            description="only islands smaller than the size will be merged.",
            min=0, max=500,
            default=150,
            )
    angle_deformation_ratio_threshold = FloatProperty(
            name="Angle deformation threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=1.01, max=10,
            default=1.5,
            )
    area_deformation_ratio_threshold =  FloatProperty(
            name="Area deformation threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=1.01, max=10,
            default=1.8,
            )
    island_shape_threshold  = FloatProperty(
            name="Island shape threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=0.5, max=10,
            default=1.4,
            )
            
    area_weight  = FloatProperty(
            name="Area weight",
            description="Importance of area in quality estimation",
            min=0, max=100,
            default=1.0,
            )
    angle_weight  = FloatProperty(
            name="Angle weight",
            description="Importance of angles in quality estimation",
            min=0, max=100,
            default=1.0,
            )
    island_shape_weight  = FloatProperty(
            name="Island shape weight",
            description="Importance of island shape in quality estimation",
            min=0, max=100,
            default=2.0,
            )
    commonseam_weight  = FloatProperty(
            name="Common seam weight",
            description="Importance of common seams when merging",
            min=0, max=100,
            default=1.0,
            )
   

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        #test(context,self)
        #
        bpy.context.tool_settings.use_uv_select_sync = False
        me=bpy.context.active_object.data
        island = []
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()  
        for f in bm.faces:
            if f.select:
                island.append(f)
        
        testIslandQuality(context,bm,  island, self)
        
        
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
       
class AutoSeamUnwrap(Operator):
    """iteratively finds seams, and unwraps selected object. """ \
    """can take a long time to compute""" \
    """doesn't produce 'pretty' islands but works good for getting low number of islands on complex meshes."""
    bl_idname = "uv.auto_seams_unwrap"
    bl_label = "Auto seams unwrap"
    bl_options = {'REGISTER', 'UNDO'}


    init_seams = BoolProperty( name="Start with own seams",
            description="If on, totally new seams will be created, otherwise UV island merge will be performed",default=True)



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
            default=3,
            )
    small_island_threshold = IntProperty(
            name="Small island size limit",
            description="only islands smaller than the size will be merged.",
            min=0, max=500,
            default=150,
            )
    angle_deformation_ratio_threshold = FloatProperty(
            name="Angle deformation threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=1.01, max=10,
            default=1.5,
            )
    area_deformation_ratio_threshold =  FloatProperty(
            name="Area deformation threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=1.01, max=10,
            default=1.8,
            )
    island_shape_threshold  = FloatProperty(
            name="Island shape threshold",
            description="Amount of deformation tolerated in the unwrapped islands",
            min=0.5, max=10,
            default=1.4,
            )
            
    area_weight  = FloatProperty(
            name="Area weight",
            description="Importance of area in quality estimation",
            min=0, max=100,
            default=1.0,
            )
    angle_weight  = FloatProperty(
            name="Angle weight",
            description="Importance of angles in quality estimation",
            min=0, max=100,
            default=1.0,
            )
    island_shape_weight  = FloatProperty(
            name="Island shape weight",
            description="Importance of island shape in quality estimation",
            min=0, max=100,
            default=2.0,
            )
    commonseam_weight  = FloatProperty(
            name="Common seam weight",
            description="Importance of common seams when merging",
            min=0, max=100,
            default=1.0,
            )
    island_margin = FloatProperty(
            name="Island Margin",
            description="Margin to reduce bleed from adjacent islands",
            min=0.0, max=1.0,
            default=0.0002,
            )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        #test(context,self)
        #
        bpy.context.tool_settings.use_uv_select_sync = False
        
        seed_with_merge(context,self
             )
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(AutoSeamUnwrap.bl_idname, text = 'Autoseam hardsurface'). angle_deformation_ratio_threshold = 1.1
    self.layout.operator(AutoSeamUnwrap.bl_idname, text = 'Autoseam organic shape'). angle_deformation_ratio_threshold = 1.8
    #self.layout.operator(MergeIslands.bl_idname)
    self.layout.separator()

    
def register():
    bpy.utils.register_class(AutoSeamUnwrap)
    bpy.utils.register_class(testIsland)
    #bpy.utils.register_class(MergeIslands)
    bpy.types.VIEW3D_MT_uv_map.append(menu_func)
    #bpy.utils.register_manual_map(add_object_manual_map)
    #bpy.types.INFO_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(AutoSeamUnwrap)
    bpy.utils.unregister_class(testIsland)
    #bpy.utils.unregister_class(MergeIslands)
    #bpy.utils.unregister_manual_map(add_object_manual_map)
    #bpy.types.INFO_MT_mesh_add.remove(add_object_button)



if __name__ == "__main__":
    register()
