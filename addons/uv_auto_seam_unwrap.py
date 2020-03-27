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
    "version": (1, 1),
    "blender": (2, 80, 0),
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
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
import itertools
import time
import numpy as np
from copy import deepcopy, copy


# def getIslands(bm):
#     # bm = bmesh.from_edit_mesh(me)
#     print('reading original UV islands')
#     for f in bm.faces:
#         f.select = False
#     all = False
#     done = {}
#     islands = []
#     while not len(done) >= len(bm.faces):
#         island = Island()
#         for i, p in enumerate(bm.faces):
#
#             if done.get(p.index) == None:
#                 p.select = True
#                 done[p.index] = True
#                 island.faces.append(p)
#                 break
#         new_faces = [p]
#         while len(new_faces) > 0:
#             selected_faces = new_faces
#             new_faces = []
#
#             for f in selected_faces:
#                 for edge in f.edges:
#                     if edge.seam == False:
#                         linkede = edge.link_faces
#                         for face in linkede:
#                             if face != f and not face.select:# and done.get(face.index) == None:
#                                 done[face.index] = True
#                                 new_faces.append(face)
#                                 face.select = True
#
#                                 island.faces.append(face)
#                     else:
#                         island.seams.append(edge)
#         islands.append(island)
#         for f in island.faces:
#             f.select = False
#     return islands

# optimized version
# reduces access to bmesh - seems to do the trick.
def getIslands(bm):
    # bm = bmesh.from_edit_mesh(me)
    print('reading original UV islands')
    for f in bm.faces:
        f.select = False
    all = False
    done = {}
    islands_dict = {}
    island_index_dict = {}
    neighbours = {}
    for i, p in enumerate(bm.faces):
        islands_dict[i] = [p]  # faces and edges
        island_index_dict[i] = i
        n = []
        for e in p.edges:
            for f in e.link_faces:
                if f != p:
                    n.append((f.index, e.seam))
        neighbours[i] = n  # face index with seam info

    new_faces = [p]
    done_all = False

    totfaces = len(bm.faces)
    while not done_all:
        done_one = False
        for i in range(0, totfaces):
            if done.get(i) is None:
                had_neighbours = False
                island1i = island_index_dict[i]
                for n in neighbours[i]:
                    if not n[1]:
                        f2i = n[0]
                        island2i = island_index_dict[f2i]
                        if island1i != island2i:
                            done_one = True
                            islands_dict[island1i].extend(islands_dict[island2i])
                            for fmove in islands_dict[island2i]:
                                island_index_dict[fmove.index] = island1i
                            islands_dict.pop(island2i)
                if not had_neighbours:
                    done[i] = True
        print(done_one, len(islands_dict))
        if not done_one:
            done_all = True

    islands = list(islands_dict.values())
    islands_fin = []
    for i_faces in islands:
        island = Island()
        island.faces = i_faces
        # write seams, hope this isn't too slow.
        for f in i_faces:
            for e in f.edges:
                if e.seam:
                    island.seams.append(e)
        islands_fin.append(island)
    return islands_fin


# old version
# def testOverlap(bm,faces):
#     #print('test overlap')
#     uv_layer = bm.loops.layers.uv.verify()
#
#     # adjust UVs
#     edges=[]
#     ekeys={}
#     for f in faces:
#         i=0
#         for l in f.loops:
#             luv = l[uv_layer]
#             if i==len(f.loops)-1:
#                 uv1 = luv.uv
#                 uv2 = f.loops[0][uv_layer].uv
#
#             else:
#                 uv1 = luv.uv
#                 uv2 = f.loops[i+1][uv_layer].uv
#             add  = True
#             uv1=uv1.to_tuple()
#             uv2=uv2.to_tuple()
#             if ekeys.get(uv1)==None:
#                 ekeys[uv1]=[uv2]
#
#             elif uv2 in ekeys[uv1]:
#                 #print('repeating uv')
#                 add=False
#             else:
#                 ekeys[uv1].append(uv2)
#             if ekeys.get(uv2)==None:
#                 ekeys[uv2]=[uv1]
#             else:
#                 ekeys[uv2].append(uv1)
#             if add:
#                 edges.append((uv1,uv2))
#             i+=1
#             #print(luv.uv)
#     #print(len(edges),len(faces))
#     totiter=0
#     for i1,e in enumerate(edges):
#         for i2 in range(i1+1,len(edges)):
#             totiter+=1
#             #if i1!=i2:
#             e2=edges[i2]
#             if e[0]!=e2[0] and e[0]!=e2[1] and e[1]!=e2[0] and e[1]!=e2[1]:#no common vertex, since that's an intersection too.
#                 intersect = mathutils.geometry.intersect_line_line_2d(e[0],e[1],e2[0],e2[1])
#                 if intersect!=None:
#
#                     #print(intersect)
#                     return True
#     #print(totiter)
#     return False

# trying to optimize old version for larger meshes.
# only will test seams overlap!
def testOverlap(bm, islandfaces):
    # print('test overlap')
    uv_layer = bm.loops.layers.uv.verify()

    # adjust UVs
    edges = []
    ekeys = {}
    for f in islandfaces:
        # let's try to check only border faces:
        needed = False
        for i, e in enumerate(f.edges):
            if e.seam:
                needed = True

                l = f.loops[i]

                luv = l[uv_layer]
                if i == len(f.loops) - 1:
                    uv1 = luv.uv
                    uv2 = f.loops[0][uv_layer].uv

                else:
                    uv1 = luv.uv
                    uv2 = f.loops[i + 1][uv_layer].uv
                add = True
                uv1 = uv1.to_tuple()
                uv2 = uv2.to_tuple()
                if ekeys.get(uv1) == None:
                    ekeys[uv1] = [uv2]

                elif uv2 in ekeys[uv1]:
                    # print('repeating uv')
                    add = False
                else:
                    ekeys[uv1].append(uv2)
                if ekeys.get(uv2) == None:
                    ekeys[uv2] = [uv1]
                else:
                    ekeys[uv2].append(uv1)
                if add:
                    edges.append((uv1, uv2))
                # print(luv.uv)
    # print(len(edges),len(faces))
    totiter = 0
    for i1, e in enumerate(edges):
        for i2 in range(i1 + 1, len(edges)):
            totiter += 1
            # if i1!=i2:
            e2 = edges[i2]
            if e[0] != e2[0] and e[0] != e2[1] and e[1] != e2[0] and e[1] != e2[
                1]:  # no common vertex, since that's an intersection too.
                intersect = mathutils.geometry.intersect_line_line_2d(e[0], e[1], e2[0], e2[1])
                if intersect != None:
                    # print(intersect)
                    return True
    # print(totiter)
    return False


# new version, optimized with blender's  operator.
# def testOverlap(bm, faces):
#     # print('test overlap')
#     uv_layer = bm.loops.layers.uv.verify()
#     # t1 = time.time()
#     bpy.ops.uv.select_all(action='DESELECT')
#
#     bpy.ops.uv.select_overlap()
#
#     t = time.time()
#     for f in faces:
#         i = 0
#         for l in f.loops:
#             luv = l[uv_layer]
#
#             if luv.select:
#                 return True
#
#     return False


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


# old version of the function, does all angles - new v
# def testAngleRatio(bm, faces):
#     # print('test ratio')
#     uv_layer = bm.loops.layers.uv.verify()
#
#     # adjust UVs
#     edges = []
#     ekeys = {}
#     ratios = []
#     for f in faces:
#         i = 0
#         flen = 0
#         for i1 in range(0, len(f.verts)):
#             if i1 < len(f.verts) - 1:
#                 i2 = i1 + 1
#             else:
#                 i2 = 0
#             if i1 < len(f.verts) - 2:
#                 i3 = i1 + 2
#             else:
#                 i3 = i1 - len(f.verts) + 2
#             v1 = f.verts[i2].co - f.verts[i1].co
#             v2 = f.verts[i3].co - f.verts[i2].co
#
#             angle_mesh = v1.angle(v2)
#
#             l1 = f.loops[i1]
#             l2 = f.loops[i2]
#             l3 = f.loops[i3]
#             v1 = l2[uv_layer].uv - l1[uv_layer].uv
#             v2 = l3[uv_layer].uv - l2[uv_layer].uv
#             angle_uv = 0
#             if v1.length != 0 and v2.length != 0:
#                 angle_uv = v1.angle(v2)
#             ratio = abs(angle_mesh - angle_uv)
#             ratios.append(ratio)
#
#     finalratio = sum(ratios)
#     maxratio = max(ratios)
#     finalratio = finalratio / len(ratios) + 1
#
#     maxratio = max(finalratio, maxratio + 1)
#
#     return maxratio

# new version does only one angle per face, should make more sense in most cases.
def testAngleRatio(bm, faces):
    # print('test ratio')
    uv_layer = bm.loops.layers.uv.verify()

    # adjust UVs
    edges = []
    ekeys = {}
    ratios = np.zeros(len(faces))
    for fi, f in enumerate(faces):
        i1 = 0
        i2 = 1
        i3 = -1

        v1 = f.verts[i2].co - f.verts[i1].co
        v2 = f.verts[i3].co - f.verts[i2].co

        angle_mesh = 0
        if v1.length != 0 and v2.length != 0:
            angle_mesh = v1.angle(v2)

        l1 = f.loops[i1]
        l2 = f.loops[i2]
        l3 = f.loops[i3]
        v1 = l2[uv_layer].uv - l1[uv_layer].uv
        v2 = l3[uv_layer].uv - l2[uv_layer].uv

        angle_uv = 0
        if v1.length != 0 and v2.length != 0:
            angle_uv = v1.angle(v2)

        ratio = abs(angle_mesh - angle_uv)
        ratios[fi] = ratio

    # finalratio = ratios.mean()
    #
    # if finalratio == 0:
    #     finalratio = 0.0000000000000000001
    #
    # ratios = ratios / finalratio
    #
    # minsoft = 1 / ratios[ratios < 1].mean()
    # maxsoft = ratios[ratios > 1].mean()
    # # print('min %f minsoft %f max %f maxsoft %f' %(minratio, minsoft, maxratio, maxsoft))
    # maxratio = max(maxsoft, minsoft)

    finalratio = ratios.mean() + 1

    # maxratio = ratios.max()
    # print(finalratio, maxratio)
    # maxratio = max(finalratio, maxratio + 1)

    return finalratio


def testPerimeterRatio(bm, faces, by_seams=True):
    perimeter = 0

    totalarea = 0
    totseams = 0
    totedges = 0
    if len(faces) == 0:
        return 1

    for f in faces:
        totalarea += f.calc_area()
        for e in f.edges:
            if (by_seams and e.seam):
                perimeter += e.calc_length()
                totseams += 1
            if not by_seams:
                for f1 in e.link_faces:
                    if f1 not in faces or len(e.link_faces) == 1:
                        perimeter += e.calc_length()
                        totseams += 1
        totedges += len(f.edges)  # adds number of tris actually

    # fotak ad.faltus@gmail.com
    divider = totedges / len(faces)  #
    # print(len(faces), totalarea)
    if totalarea > 0:
        perimeter_length_ratio = (perimeter / divider) / math.sqrt(totalarea)
    else:
        # zero area faces are a problem of the mesh, not of unwrap.
        perimeter_length_ratio = 1

    perimeter_count_ratio = (totseams / divider) / math.sqrt(len(faces))
    # print(perimeter_length_ratio)
    perimeter_ratio = (2 * perimeter_length_ratio + perimeter_count_ratio) / 3
    # print(len(faces), perimeter_ratio)
    return perimeter_ratio


# old version
# def testAreaRatio(bm, faces):
#     # print('test ratio')
#     uv_layer = bm.loops.layers.uv.verify()
#
#     ratios = []
#     # totarea_mesh = 0
#     for f in faces:
#         i = 0
#         flen = 0
#         area_mesh = 0
#         area_uv = 0
#
#         for i1 in range(0, len(f.verts) - 2):
#
#             if i1 < len(f.verts) - 1:
#                 i2 = i1 + 1
#             else:
#                 i2 = 0
#             if i1 < len(f.verts) - 2:
#                 i3 = i1 + 2
#             else:
#                 i3 = i1 - len(f.verts) + 2
#             # print(f.verts[i1], f.verts[i2], f.edges[i1].verts[0], f.edges[i1].verts[1])
#             v1 = f.verts[i2].co - f.verts[i1].co
#             v2 = f.verts[i3].co - f.verts[i2].co
#
#             area_mesh += mathutils.geometry.area_tri(f.verts[i1].co, f.verts[i2].co, f.verts[i3].co)
#
#             l1 = f.loops[i1]
#             l2 = f.loops[i2]
#             l3 = f.loops[i3]
#             area_uv += mathutils.geometry.area_tri(l1[uv_layer].uv, l2[uv_layer].uv, l3[uv_layer].uv)
#             # totalarea_uv+=area_uv
#
#         # compensate for possible numeric errors
#         if area_uv == 0:
#             if area_mesh == 0:
#                 area_uv = 1
#             else:
#                 area_uv = 0.0000000000001
#
#         ratio = area_mesh / area_uv
#
#         ratios.append(1 + (ratio - 1))  # * area_mesh) #smaller faces become less important
#         # totarea_mesh += area_mesh
#     finalratio = 0
#     maxratio = -100000000
#     minratio = 1000000000000000
#     for r in ratios:
#         finalratio += r
#         minratio = min(r, minratio)
#         maxratio = max(r, maxratio)
#
#     finalratio = finalratio / len(ratios)  # get normal ratio
#     # now get ratio!
#     if finalratio == 0:
#         finalratio = 0.0000000000000000001
#     if minratio == 0:
#         minratio = .1
#     maxratio = math.sqrt(max(finalratio / minratio, maxratio / finalratio))
#     return maxratio

# new version, only 3 verts tested, could be potential problem for n-gons but provides a nice speedup.
def testAreaRatio(bm, faces):
    # print('test ratio')
    uv_layer = bm.loops.layers.uv.verify()

    ratios = np.zeros((len(faces)))
    # totarea_mesh = 0
    for fi, f in enumerate(faces):
        area_mesh = 0
        area_uv = 0

        for i1 in range(0, len(f.verts) - 2):
            i1 = 0
            i2 = 1
            i3 = -1

            v1 = f.verts[i2].co - f.verts[i1].co
            v2 = f.verts[i3].co - f.verts[i2].co

            area_mesh += mathutils.geometry.area_tri(f.verts[i1].co, f.verts[i2].co, f.verts[i3].co)

            l1 = f.loops[i1]
            l2 = f.loops[i2]
            l3 = f.loops[i3]
            area_uv += mathutils.geometry.area_tri(l1[uv_layer].uv, l2[uv_layer].uv, l3[uv_layer].uv)
            # totalarea_uv+=area_uv

        # compensate for possible numeric errors
        if area_uv == 0:
            if area_mesh == 0:
                area_uv = 1
            else:
                area_uv = 0.0000000000001

        ratio = area_mesh / area_uv

        ratios[fi] = 1 + (ratio - 1)  # * area_mesh) #smaller faces become less important
        # totarea_mesh += area_mesh

    finalratio = ratios.mean()

    if finalratio == 0:
        finalratio = 0.0000000000000000001

    ratios = ratios / finalratio

    maxratio = ratios.max()
    minratio = ratios.min()

    minsoft = 1 / ratios[ratios < 1].mean()
    maxsoft = ratios[ratios > 1].mean()

    maxdeviation = max(maxratio, 1 / minratio) - 1
    # print('min %f minsoft %f max %f maxsoft %f' %(minratio, minsoft, maxratio, maxsoft))
    maxratio = max(maxsoft, minsoft)

    finalratio = maxratio + maxdeviation / 5.0  # we add maxdeviation to avoid extreme cases.
    return finalratio


def unwrap(op):
    bpy.ops.uv.unwrap(method=op.unwrap_method, fill_holes=True, margin=op.island_margin)


def getFaceNormalRatio(face):
    maxn = 0
    maxn = max(maxn, abs(face.normal.x))
    maxn = max(maxn, abs(face.normal.y))
    maxn = max(maxn, abs(face.normal.z))
    # print(maxn)
    return maxn


def seedIslandsGrowth(context, bm, op):
    wm = bpy.context.window_manager

    ob = bpy.context.active_object
    # me=ob.data

    basenormal = Vector((0, 0, 1))
    normals = []
    anglelimit = 3.1415926 / 2

    done = {}

    normalsortfaces = bm.faces[:]
    normalsortfaces.sort(key=getFaceNormalRatio)
    # for a in range(0,grow_iterations):
    #   bpy.ops.mesh.select_more()
    # newsel = []
    # for

    nislands = 0
    islands = []

    all = False
    if 0:  # op.grow_iterations == 0 :# if the user sets 0 in this, it means 1 island = 1 face.
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
                # set first face
                if done.get(p.index) == None:
                    p.select = True
                    done[p.index] = True  # done[i]=True
                    break

            lensel = 1
            nf = [p]
            islandnormal = p.normal
            stop = False
            sfaces = [p]
            tempdone = {}

            if 0:  # op.sel_flat:
                bpy.ops.mesh.faces_select_linked_flat(sharpness=0.2)
                # if len(islands)==5:fal
                for f in bm.faces:
                    if done.get(f.index) == None and f.select:
                        nf.append(f)
                        tempdone[f.index] = True
                        sfaces.append(f)
                        # done[f.index]=True
                    else:
                        f.select = False
                    # f.select=False
                    #
                p.select = True

            # case when the selected face is allready isolated can lead to bad islands through single vertex.
            # allseam=True
            # for e in p.edges:
            #    if not e.seam:
            #        allseam=False
            # if not allseam:

            for a in range(0, op.grow_iterations):
                # if len(islands)==13 and a==2:
                #    fal
                tempdone = {}
                # print(len(selected_faces))
                selected_faces = nf
                nf = []

                if not stop:
                    for f in selected_faces:
                        for vert in f.verts:

                            linkedv = vert.link_faces
                            for face in linkedv:
                                if not face.select and tempdone.get(face.index) == None:
                                    tempdone[face.index] = True
                                    angle = face.normal.angle(islandnormal)
                                    # print(angle)

                                    if done.get(face.index) == None and angle < anglelimit:
                                        nf.append(face)
                                        lensel += 1
                                        # print(len(nf))
                if not stop:
                    for face in nf:
                        face.select = True

                    check = sfaces[:]
                    check.extend(nf)
                    # sometimes, neighbour faces are selected only through 1 vertex which is actually a separate island. This is here to avoid that.
                    f = check.pop(0)
                    finishcheck = False
                    # isolationgroup=sfaces[:]
                    isolationcheck = [f]
                    while len(isolationcheck) > 0:
                        f1 = isolationcheck.pop()
                        # print(len(isolationcheck), len(check))
                        for e in f1.edges:
                            for f2 in e.link_faces:
                                if f2 != f1 and f2 in check:
                                    # isolationgroup.append(f2)
                                    check.remove(f2)
                                    isolationcheck.append(f2)

                    if len(check) > 0:
                        # print(a,'separate islands selected', len(check), len(nf),nf,check)
                        # fal
                        for f in check:
                            f.select = False
                            # print(a)
                            if f in nf:
                                nf.remove(f)
                            else:
                                sfaces.remove(f)  # case where select linked does overflow
                            # nsum-=f.normal
                            lensel -= 1

                    testfaces = sfaces[:]
                    testfaces.extend(nf)

                    disqualify, quality = testIslandQuality(context, bm, testfaces, op, do_unwrap=True)
                    # print(disqualify, quality)

                    if disqualify:
                        stop = True
                    else:
                        sfaces = testfaces
                        for f in sfaces:
                            done[f.index] = True
                    for f in sfaces:
                        f.select = True
                else:
                    break;

            # mark seams here
            island = Island()
            island.faces = sfaces[:]
            for f in sfaces:
                for edge in f.edges:
                    linked = edge.link_faces
                    for face in linked:
                        if not face.select or len(linked) == 1:
                            edge.seam = True
                            island.seams.append(edge)
            # fal

            islands.append(island)

            for f in sfaces:
                # if f.index == 397:
                # fal
                # print('here heya hou')
                done[f.index] = True
                f.select = False

            if len(done) == len(bm.faces) or len(done) > 10000000:
                all = True
            nislands += 1
            wm.progress_update(nislands)
            print('seed island ', len(islands))

        return islands


def v_manifold(v):
    for e in v.link_edges:
        if not e.is_manifold:
            return False
    return True


def v_has_seams(v):
    for e in v.link_edges:
        if e.seam:
            return True
    return False


def v_weight_sorted_edges(v, weights=None):
    edges = []

    for e in v.link_edges:
        if weights is not None:
            v1 = e.other_vert(v)
            edges.append([e, weights[v1.index]])
        else:
            if len(e.link_faces) == 2:
                a = e.calc_face_angle_signed()
                edges.append([e, abs(a)])
            else:
                edges.append([e, 0])
    edges.sort(key=second)
    eds = []
    for l in edges:
        eds.append(l[0])
    return eds


def v_counter_edges(v, weights=None):
    vects = []
    weight_sorted_edges = v_weight_sorted_edges(v, weights)
    e1 = weight_sorted_edges[0]
    # e1 = v.link_edges[0]
    vect1 = e1.other_vert(v).co - v.co
    maxangle = -100
    other_edge = v.link_edges[1]
    for e2 in v.link_edges:
        vect2 = e2.other_vert(v).co - v.co
        a = 0
        if vect1.length > 0 and vect2.length > 0:
            a = vect1.angle(vect2)
        if a > maxangle:
            maxangle = a
            other_edge = e2

    return [e1, other_edge]


def continue_edges(v_last, v_new):
    vect1 = v_new.co - v_last.co
    edgesort = []
    for e2 in v_new.link_edges:
        v2 = e2.other_vert(v_new)
        if v2 != v_last:
            vect2 = v2.co - v_new.co
            a = vect1.angle(vect2)
            edgesort.append([e2, a])
    edgesort.sort(key=second)
    edges = []
    for es in edgesort:
        edges.append(es[0])
    # print(edgesort)
    return edges  # [:2]


def continue_path(v_path, weights, curvature_influence=0.5):
    '''find a suitable edge to continue the path. Usually tries to go straight.'''
    edges = continue_path_possibilities(v_path, weights, curvature_influence)
    return edges[0]


def continue_path_possibilities(v_path, weights, curvature_influence=0.5, threshold=1):
    '''find a suitable edge to continue the path. Usually tries to go straight.'''
    v_new = v_path.verts[-1]
    v_last = v_path.verts[-2]
    vect1 = v_new.co - v_last.co

    edges = []
    e_weights = []
    for e2 in v_new.link_edges:
        v2 = e2.other_vert(v_new)
        if v2 != v_last:
            vect2 = v2.co - v_new.co
            a = 0
            if vect2.length > 0 and v_path.direction.length > 0:
                a = v_path.direction.angle(vect2)
            # face angle
            # todo add precalculated curvature weights here!
            a2 = 0
            if len(e2.link_faces) == 2:
                #a2 += e2.calc_face_angle() * curvature_influence
                a2 += abs(weights[v2.index]) * curvature_influence
            else:
                a2 = abs(weights[v2.index]) * curvature_influence *2
            # print(a,a2)
            edges.append(e2)
            e_weights.append(a + a2)
            # edgesort.append([e2, a + a2])
    edgesort = np.argsort(e_weights)
    nedges = []
    for i in edgesort:
        if e_weights[i] < threshold or len(nedges) < 1:
            nedges.append(edges[i])
    # print(edgesort)
    return nedges


class connection():
    def __init__(self):
        self.v1 = -1
        self.v2 = -1
        self.length = 0


def second(n):
    return (n[1])
    # this array will store where did the seam come from, this will help to find shortest path back ;)


class VPath():

    def __init__(self):
        self.index = -1
        self.verts = []
        self.edges = []
        self.length = 0
        self.direction = None
        self.growing = True
        self.can_be_used = True
        self.meets = []  # which path the path meets
        self.siblings = []  # will be killed once successfull
        self.siblings_timeout = [-1]  # will be killed once successfull

    def copy(self):
        cp = VPath()
        cp.index = -1
        cp.verts = self.verts[:]
        cp.edges = self.edges[:]
        cp.length = self.length
        cp.direction = self.direction.copy()
        cp.growing = True
        cp.meets = []
        cp.siblings = self.siblings  # not a copy! shared!
        cp.siblings_timeout = self.siblings_timeout
        return cp


def getBBbmesh(bm):
    x = []
    y = []
    z = []
    for v in bm.verts:
        vx, vy, vz = v.co.to_tuple()
        x.append(vx)
        y.append(vy)
        z.append(vz)

    minx = min(x)
    miny = min(y)
    minz = min(z)
    maxx = max(x)
    maxy = max(y)
    maxz = max(z)
    # t1 = t - time.time()
    # print('bmesh conversion time', t1)
    return [Vector((minx, miny, minz)), Vector((maxx, maxy, maxz))]


def getBB(faces):
    # gets bb from faces - 
    # this should however calculate from verts directly
    # now it iterates over same verts several times

    minx = 1000000
    miny = 1000000
    minz = 1000000
    maxx = -1000000
    maxy = -1000000
    maxz = -1000000

    # t = time.time()
    # commented out versions are slower.
    # verts = {}
    # for f in faces:
    #     for v in f.verts:
    #         verts[str(v.co)] = v
    # for vk in verts:
    #     v = verts[vk]
    #     minx = min(minx, v.co.x)
    #     miny = min(miny, v.co.y)
    #     minz = min(minz, v.co.z)
    #
    #     maxx = max(maxx, v.co.x)
    #     maxy = max(maxy, v.co.y)
    #     maxz = max(maxz, v.co.z)

    # for f in faces:
    #     for v in f.verts:
    #         vx = v.co.x
    #         vy = v.co.y
    #         vz = v.co.z
    #         minx = min(minx, vx)
    #         miny = min(miny, vy)
    #         minz = min(minz, vz)
    #
    #         maxx = max(maxx, vx)
    #         maxy = max(maxy, vy)
    #         maxz = max(maxz, vz)

    # for f in faces:
    #     for v in f.verts:
    #         vx, vy, vz = v.co.to_tuple()
    #         minx = min(minx, vx)
    #         miny = min(miny, vy)
    #         minz = min(minz, vz)
    #
    #         maxx = max(maxx, vx)
    #         maxy = max(maxy, vy)
    #         maxz = max(maxz, vz)

    x = []
    y = []
    z = []
    for f in faces:
        for v in f.verts:
            vx, vy, vz = v.co.to_tuple()
            x.append(vx)
            y.append(vy)
            z.append(vz)

    minx = min(x)
    miny = min(y)
    minz = min(z)
    maxx = max(x)
    maxy = max(y)
    maxz = max(z)
    # t1 = t - time.time()
    # print('bmesh conversion time', t1)
    return [Vector((minx, miny, minz)), Vector((maxx, maxy, maxz))]


def getBBc(minv, maxv):
    # get bound box center
    c = (maxv + minv) / 2
    return c


def getSplitAxis(minv, maxv):
    bspan = maxv - minv

    chosen_axis = max(bspan.x, bspan.y, bspan.z)

    if chosen_axis == bspan.x:
        return 0
    if chosen_axis == bspan.y:
        return 1
    if chosen_axis == bspan.z:
        return 2


def getSplitData(minv, maxv):
    bbc = getBBc(minv, maxv)
    axis = getSplitAxis(minv, maxv)
    return axis, bbc


ntests = 0
donefaces = 0


class Island():
    def __init__(self):
        self.faces = []
        self.seams = []
        self.minv = None
        self.maxv = None
        self.splittable = True
        # border islands for merging:
        self.bislandsidx = []
        self.bislands = []

    def __len__(self):
        return len(self.faces)


def smooth_borders(island1, island2):
    # little heuristic attempt to make nicer islands
    # should remove teeth on border of islands

    # check which faces have longer border with neigbour than with self.
    # this makes more sense on larger islands,
    # smaller islands (more deformed areas) might benefit form being not so nice.

    remove = []

    # to acces which face belongs to which island really fast.
    findices = {}
    for f in island2.faces:
        findices[f.index] = 1
    #
    # for seam in island1.seams:
    #     border_self = 0
    #     border_island2 = 0
    #     is_border = True
    #     #only do this on border between these 2 islands
    #     for f in seam.link_faces:
    #         if findices.get(f.index) is None:
    #             is_border = False
    #         elif findices[f.index] == 0:
    #             island1face= f
    #         else:
    #             island2face = f
    #     if is_border:
    #         for e in island1face.edges:
    #             border_self += e.calc_length()
    #         for e in island2face.edges:
    #             border_island2 += e.calc_length()
    #         if border_island2>border_self:
    #             remove.append(f)
    #
    # for f in remove:
    #     island1.faces.remove(f)
    #     f.select = (False)
    # island2.faces.extend(remove)
    #
    # for seam in island2.seams:
    #     border_self = 0
    #     border_island2 = 0
    #     is_border = True
    #     # only do this on border between these 2 islands
    #     for f in seam.link_faces:
    #         if findices.get(f.index) is None:
    #             is_border = False
    #         elif findices[f.index] == 0:
    #             island1face = f
    #         else:
    #             island2face = f
    #     if is_border:
    #         for e in island1face.edges:
    #             border_self += e.calc_length()
    #         for e in island2face.edges:
    #             border_island2 += e.calc_length()
    #         if border_island2 > border_self:
    #             remove.append(f)
    #
    # for f in remove:
    #     island1.faces.remove(f)
    #     f.select = (False)
    # island2.faces.extend(remove)

    for f in island1.faces:
        border_self = 0
        border_island2 = 0
        for e in f.edges:
            border = False
            for f1 in e.link_faces:
                if not f1.select and findices.get(f1.index) is not None:
                    border = True
                    border_island2 += e.calc_length()
            if not border:
                border_self += e.calc_length()
        if border_island2 > border_self * 1.01:
            remove.append(f)
    for f in remove:
        island1.faces.remove(f)
        f.select = (False)
    island2.faces.extend(remove)

    remove = []
    for f in island2.faces:
        border_self = 0
        border_island1 = 0
        for e in f.edges:
            border = False
            for f1 in e.link_faces:
                if f1.select:
                    border = True
                    border_island1 += e.calc_length()
            if not border:
                border_self += e.calc_length()
        if border_island1 > border_self * 1.05:
            remove.append(f)

    for f in remove:
        island2.faces.remove(f)
        f.select = (True)
    island1.faces.extend(remove)


# 3 functions for sorting faces quickly
def xKey(f):
    return f.calc_center_median_weighted().x


def yKey(f):
    return f.calc_center_median_weighted().y


def zKey(f):
    return f.calc_center_median_weighted().z


def splitIslands(bm, island, op, axis_override=None):
    global ntests, donefaces
    islands = []

    # init boundbox on max, but don't calculate it in lower iters.
    if island.minv is None:
        island.minv, island.maxv = getBBbmesh(bm)

    axis, bbc = getSplitData(island.minv, island.maxv)

    # rint(axis)
    island1 = Island()
    island2 = Island()

    thres = bbc[axis]

    # split verts and also reassert bound box on the fly.
    for f in island.faces:
        c = f.calc_center_median_weighted()
        if c[axis] < thres:
            f.select = True
            island1.faces.append(f)
        else:
            f.select = False
            island2.faces.append(f)

    smooth_borders(island1, island2)

    must_calc_bb = False
    # todo check for if more islands have actually been created here, can happen quite often
    if len(island1.faces) == 0 or len(island2.faces) == 0 and len(island.faces) < 3:

        island1 = Island()
        island2 = Island()

        c = Vector()
        i = 0
        for f in island.faces:
            for v in f.verts:
                c += v.co
                i += 1
        bbc = c / i
        thres = bbc[axis]
        for f in island.faces:
            c = f.calc_center_median_weighted()
            if c[axis] < thres:
                f.select = True
                island1.faces.append(f)
            else:
                f.select = False
                island2.faces.append(f)
        # has to calculate bounding box because it could cause problems with splitting in lower iterations.
        must_calc_bb = True

    ntests += 1

    has_new_seams = False
    for f in island1.faces:
        for e in f.edges:
            for f1 in e.link_faces:
                if not f1.select and not e.seam:
                    # this marks a new seam.
                    e.seam = True
                    has_new_seams = True

    # this part sets new bound box for resulting islands.
    #  Should in the future also check for possible unconnected islands inside one island. This algo by now ignores it.
    if len(island1.faces) > 0 and (not has_new_seams or must_calc_bb):
        island1.minv, island1.maxv = getBB(island1.faces)
    else:
        # island1 hets lower half, island 2 upper in any axis, pass the boundbox so it is computed only once.
        island1.minv = island.minv.copy()
        island1.maxv = island.maxv.copy()
        island1.maxv[axis] = bbc[axis]

    if len(island2.faces) > 0 and (has_new_seams or must_calc_bb):
        island2.minv, island2.maxv = getBB(island2.faces)
    else:
        island2.minv = island.minv.copy()
        island2.maxv = island.maxv.copy()
        island2.minv[axis] = bbc[axis]

    # if ntests > 33:
    #     fal
    # deselect here, should be safely deselected for later...
    for f in island1.faces:
        f.select = False
    retislands = []
    for i in [island1, island2]:
        if len(i.faces) > 0:
            retislands.append(i)
    # if an island wasn't split, set it unsplittable, helps in heavy recursion problems
    if len(retislands) == 1:
        retislands[0].splittable = False

    return retislands


def write_weights(indices, weights, name):
    # write to group here:
    ob = bpy.context.active_object
    bpy.ops.object.mode_set(mode='OBJECT')

    if ob.vertex_groups.get(name) is None:
        bpy.ops.object.vertex_group_add()
        ob.vertex_groups[-1].name = name
    vgroup = ob.vertex_groups[name]

    for vi in indices:
        vgroup.add([vi], weights[vi], 'REPLACE')
    #
    bpy.ops.object.mode_set(mode='EDIT')


def getCurvature(bm, smooth_steps=3):
    print('getting curvature')
    vgroup_indices = range(0, len(bm.verts))
    vgroup_weights = np.zeros(len(bm.verts))

    for f in bm.faces:
        for e in f.edges:
            if len(e.link_faces) == 2:
                ea = e.calc_face_angle_signed() / 3.1415926
                for v in e.verts:
                    # print(v.index)
                    vgroup_weights[v.index] += ea
            else:
                for v in e.verts:
                    vgroup_weights[v.index] = 3.1415926  # give some bonus to non manifold areas

    print('smoothing curvature')
    # smoothing step
    for a in range(0, smooth_steps):
        vgroup_weights_smooth = vgroup_weights.copy()
        for v in bm.verts:
            for e in v.link_edges:
                for v1 in e.verts:
                    if v != v1:
                        coef = .2
                        if not v_manifold(v1):
                            coef *= 2
                        vgroup_weights_smooth[v1.index] += vgroup_weights[v.index] * (coef / len(v1.link_edges))
        vgroup_weights = vgroup_weights_smooth

    # write_weights(vgroup_indices,vgroup_weights,'curvature')

    return vgroup_weights


def seedIslandsCurvature(context, bm, op):
    bm.verts.ensure_lookup_table()
    # bm.faces.sort(key = xKey)
    totverts = len(bm.verts)
    vdists = []
    tops = []

    vgroup_weights = getCurvature(bm, smooth_steps=op.curvature_smooth_steps)

    # normalization to 0-1
    minw = vgroup_weights.min()
    maxw = vgroup_weights.max()

    normalized_weights = vgroup_weights - minw
    normalized_weights *= 1 / (maxw - minw)

    est_weights = abs(vgroup_weights)

    sorted_indices = np.argsort(vgroup_weights)

    # find top points. select the most curved, and if they don't have any selected neighbours yet,
    # these should be the extremities we are looking for. Same from bottom up.
    print('looking for feature points')
    i = 0
    topverts = []
    borderverts = []
    max_top_points = max(op.seed_points, totverts * .02)
    consider_percentage = .5  # less creates less topverts
    for vi in range(0, int(totverts * consider_percentage)):
        i = math.floor(vi / 2)
        if vi % 2 == 1:
            i = -i
        v = bm.verts[sorted_indices[i]]
        if not v_manifold(v):
            borderverts.append(v)
            continue;

        neighbour_selected = False
        for e in v.link_edges:

            for v1 in e.verts:
                if v != v1 and v1.select:
                    neighbour_selected = True
                    break;
            if neighbour_selected:
                break;
        if not neighbour_selected:
            topverts.append(v)
            if len(topverts) > max_top_points:
                break;
        v.select = True
        for f in v.link_faces:
            for v1 in f.verts:
                v1.select = True
    # border verts get added last to not be too active.

    # topverts.extend(borderverts)

    # test select top verts
    for v in bm.verts:
        v.select = False
    for i, v in enumerate(topverts):
        v.select = True
        # if i ==2:
        #    fal

    pathindex = 0
    done_verts = {}  # with indices of the path
    path_indices = {}  # so we can find the path that reached the point.
    topverts_meets = {}  # these are already connected.
    topverts_connected = {} # these store if verts have already connected through other verts.
    possible_paths = []
    dead_ends = {} #holds path that end on border of mesh.
    done_paths = []
    for v in topverts:
        for e in v.link_edges:
            p1 = VPath()
            p1.index = pathindex
            possible_paths.append(p1)
            pathindex += 1


            v2 = e.other_vert(v)
            p1.verts = [v, v2]
            p1.edges = [e]
            p1.length = e.calc_length()
            p1.direction = v2.co - v.co
            p1.siblings.append(p1)

            done_verts[v.index] = p1.index
            done_verts[v2.index] = p1.index
            # this stores all possible connecting paths:
            topverts_meets[v.index] = {}
            for vt in topverts:
                topverts_meets[v.index][vt.index] = []
            dead_ends[v.index] = []
    done = False
    while not done:
        # growth loop for paths - they simply grow into their respective direction, and hit with the others.
        # the trick is, they grow at the same time this achieves something similar to delaunay.
        i = 0
        print('growing island seams')
        grown = False

        for p1 in possible_paths:
            remove = []
            # print(p)
            # print(dir(p))
            if p1.growing:
                new_paths = 0

                edges = continue_path_possibilities(p1, vgroup_weights, curvature_influence=op.curvature_influence,
                                                    threshold=1)
                npaths = [p1]
                # we will branch out so get ready
                for ei in range(1, min(len(edges), 3)):
                    p_old = p1
                    p1 = p_old.copy()
                    p1.siblings.append(p1)
                    p1.index = pathindex
                    pathindex += 1
                    possible_paths.append(p1)
                    npaths.append(p1)
                # now do the branches.
                for ei in range(0, min(len(edges), 3)):
                    p1 = npaths[ei]
                    v1 = p1.verts[-1]

                    e = edges[ei]
                    v2 = e.other_vert(v1)
                    p1.verts.append(v2)
                    p1.edges.append(e)
                    p1.direction *= op.keep_direction  # enable direction bending
                    p1.direction += v2.co - v1.co
                    p1.length += e.calc_length()
                    grown = True
                    # if not v_manifold(v2):
                    tv1 = p1.verts[0]

                    if not done_verts.get(v2.index):
                        done_verts[v2.index] = p1.index
                        if not v_manifold(v2):
                            p1.growing = False
                            dead_ends[tv1.index].append(p1)
                    else:
                        p2i = done_verts[v2.index]  # path index
                        p2 = possible_paths[p2i]  # path we met
                        #get source toppoints
                        tv2 = possible_paths[p2i].verts[0]
                        if tv1 == tv2: #means paths from same source did meet, shorter wins.
                            if p1.length < p2.length:
                                done_verts[v2.index] = p1.index
                                p2.growing = False
                            else:
                                p1.growing = False
                        else:

                            topverts_meets[tv1.index][tv2.index].append((p1, p2, v2))
                            topverts_meets[tv2.index][tv1.index].append((p1, p2, v2))
                            p1.growing = False
                            p2.growing = False
                            for s in p1.siblings:
                                s.growing = False
                                if s != p1:
                                    s.can_be_used = False
                            for s in p2.siblings:
                               s.growing = False
                               if s != p2:
                                   s.can_be_used = False

                        # #stop all growth of siblings.
                        # if not p1.growing:

                    new_paths += 1

        if not grown:
            done = True

    # now let's check which were the shortest paths.
    i = 0
    for tv1 in topverts:
        for tv2 in topverts:
            if tv1 == tv2:
                continue
            meets = topverts_meets[tv1.index][tv2.index]
            # never met.
            if len(meets) == 0:
                continue

            lengths = []
            for m in meets:
                path_length = m[0].length + m[1].length
                lengths.append(path_length)
            msort = np.argsort(lengths)
            p1,p2,v_meet = meets[msort[0]]
            #create actual seams
            for vi,v in enumerate(p1.verts):
                if v == v_meet:
                    break
                e = p1.edges[vi]
                e.seam = True
            for vi, v in enumerate(p2.verts):
                if v == v_meet:
                    break
                e = p2.edges[vi]
                e.seam = True

        #paths towards border of non manifold mesh.
        sibling_groups = []
        for de in dead_ends[tv1.index]:
            if de.can_be_used:
                if de.siblings not in sibling_groups:
                    sibling_groups.append(de.siblings)
        for sg in sibling_groups:
            minlength = 1000000
            minlength_path = sg[0]
            for p in sg:
                if p in dead_ends[tv1.index]:
                    if minlength>p.length:
                        minlength = p.length
                        minlength_path = p
            for e in minlength_path.edges:
                e.seam = True
                e.select = True

    bm.faces.ensure_lookup_table()
    islands = getIslands(bm)
    return islands


def seedIslandsTiles(context, bm, op):
    # always split UV's perpendicular to longest axis in 3d space
    # only for profiling
    global ntests
    ntests = 0

    final_islands = []
    start_island = Island()
    start_island.faces = bm.faces
    islands_for_splitting = [start_island, ]

    islands_for_test = []
    donefaces = 0
    i = 0
    itest = 0
    while donefaces < len(bm.faces):
        # first split everything that can be split
        print('splitting islands ', end='\r')
        while len(islands_for_splitting) > 0:
            island = islands_for_splitting.pop()
            islands = splitIslands(bm, island, op)

            for island in islands:
                if len(island.faces) < 2000:
                    if island.splittable:
                        islands_for_test.append(island)
                    else:
                        # unsplittable island goes straight to finished, no chance to do anything with it anymore.
                        final_islands.append(island)
                        donefaces += len(island.faces)
                else:
                    islands_for_splitting.append(island)
            i += 1

            print('splitting islands %i' % i, end='\r')
            # if len(islands_for_test) == 20:
            #     return []
        # then unwrap all  at once and test and possibly send again to splitting queue.
        print('test islands')
        if len(islands_for_test) > 0:
            # unwrap
            print('unwrap')
            # for f in bm.faces:
            #    f.select = False
            for island in islands_for_test:
                for f in island.faces:
                    f.select = True

            unwrap(op)
            for island in islands_for_test:
                for f in island.faces:
                    f.select = False

            # todo do deselect here but add as parameter to testIslandQuality
            # for f in bm.faces:
            #     f.select = False
            # and test quality

            for island in islands_for_test:
                disqualified, quality = testIslandQuality(bpy.context, bm, island, op, do_unwrap=False)

                if not disqualified:
                    donefaces += len(island.faces)
                    itest += 1
                    print('testing islands %i, done faces %i ' % (itest, donefaces), end='\r')
                    # if itest > 20:
                    #     return
                    final_islands.append(island)
                else:
                    islands_for_splitting.append(island)
            islands_for_test = []
        print()
    return final_islands


def seedIslands(context, bm, op):
    if op.island_style == 'GROW':
        return seedIslandsGrowth(context, bm, op)

    elif op.island_style == 'CURVATURE':
        return seedIslandsCurvature(context, bm, op)

    elif op.island_style == 'TILES':
        return seedIslandsTiles(context, bm, op)


def anysel(e):
    for f in e.link_faces:
        if f.select:
            return True
    return False


def allsel(e):
    a = True
    for f in e.link_faces:
        if not f.select:
            a = False
    return a


def seedPerfectIslands(context, bm, op):
    wm = bpy.context.window_manager

    ob = bpy.context.active_object
    me = ob.data

    basenormal = Vector((0, 0, 1))
    normals = []

    done = {}

    # for a in range(0,grow_iterations):
    #   bpy.ops.mesh.select_more()
    # newsel = []
    # for

    nislands = 0
    islands = []

    all = False
    while not all:

        for i, p in enumerate(bm.faces):

            if done.get(i) == None:
                p.select = True
                # done[i]=True
                break

        lensel = 1
        nf = [p]
        stop = False
        sfaces = [p]
        '''
        if op.sel_flat:
            bpy.ops.mesh.faces_select_linked_flat(sharpness=0.0174533)
            for pdesel in bm.faces:
                if done.get(pdesel.index) == True and pdesel.select:
                    pdesel.select=False
                elif pdesel.select:
                    nf.append(pdesel)
                    sfaces.append(pdesel)
        '''
        tempdone = {}
        done[i] = True
        # todo optimize this, just get those edges and mark them!
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.mark_seam(clear=False)
        bpy.ops.mesh.loop_to_region()

        trygrowth = 30
        finished = False
        iters = 0
        while iters < trygrowth and not finished:
            testsets = [[], [], [], [], [], [], [], [], [], [], []]  # set of seams to erase/create each test step.

            initseams = []
            for f in sfaces:
                for e in f.edges:
                    if e.seam:
                        initseams.append((e.index, True))
                    else:
                        initseams.append((e.index, False))

            for f in sfaces:
                for e in f.edges:
                    lf = e.link_faces
                    for f in lf:
                        if not f.select and tempdone.get(f.index) == None:  # avoid more iterations on same
                            tempdone[f.index] = True
                        if done.get(f.index) == None:
                            seamset = [f, [], []]  # face, remove seams, add seams
                            for e1 in f.edges:  # back test how many common seams are there
                                a = anysel(e1)
                                if a:
                                    seamset[1].append(e1)
                                else:
                                    seamset[2].append(e1)
                            testsets[0].append(seamset)
                            if len(seamset[1]) > 1:  # add ALL iterations!!!!
                                for i in range(1, len(seamset[1])):
                                    c = itertools.combinations(seamset[1], i)
                                    for t in c:
                                        # print('wtf')
                                        # print(t)
                                        nseamset = [f, t, seamset[2].copy()]

                                        for testseam in seamset[1]:
                                            if testseam not in t:
                                                nseamset[2].append(testseam)
                                        testsets[i].append(nseamset)
            # print(len(testsets))
            # print(testsets)
            # fad
            qualityratios = []

            for testsetlayer in testsets:
                for testset in testsetlayer:
                    testset[0].select = True

                    for e in testset[1]:
                        e.seam = False
                        # print(e.index)
                    for e in testset[2]:
                        e.seam = True
                    islandfaces = [testset[0]]
                    islandfaces.extend(sfaces)
                    disqualified, quality = testIslandQuality(context, bm, islandfaces, op)
                    if not disqualified:
                        qualityratios.append((testset, quality))
                    # bring back orig seams - could be optimized, now does whole island.
                    for e in testset[2]:  # is this ok? am I not erasing some seams? I am I guess.
                        e.seam = False
                    testset[0].select = False
                    for ed in initseams:
                        bm.edges[ed[0]].seam = ed[1]
                    # if len(qualityratios)>=10:
                    #    break;
                if len(qualityratios) > 0:
                    break;
            bestqual = 100000000
            best = None
            for qt in qualityratios:
                if qt[1] < bestqual:
                    bestqual = qt[1]
                    best = qt[0]
            if best != None:
                sfaces.append(best[0])
                best[0].select = True
                done[best[0].index] = True
                for e in best[1]:
                    e.seam = False
                    # print(e.index)
                for e in best[2]:
                    e.seam = True
            iters += 1
            # print(iters)
        islands.append(sfaces.copy())
        for f in sfaces:
            done[f.index] = True
            f.select = False

        if len(done) == len(bm.faces) or len(done) > 100000:
            all = True
        nislands += 1
        wm.progress_update(nislands)
        print('seed island ', len(islands))

    return islands


def testIslandQuality(context, bm, island, op, pass_orig_perimeter_ratio=False, orig_perimeter_ratio=None,
                      do_unwrap=True):
    if type(island) != list:
        islandfaces = island.faces
    else:
        islandfaces = island
    qualityratio = 10
    disqualified = False

    area_ratio = -1  # -1 means it wasn't tested
    angle_ratio = -1  # -1 means it wasn't tested
    overlap = -1  # -1 means it wasn't tested

    perimeter_ratio = testPerimeterRatio(bm, islandfaces)
    if pass_orig_perimeter_ratio:
        if perimeter_ratio < orig_perimeter_ratio and perimeter_ratio > op.island_shape_threshold:
            perimeter_ratio = op.island_shape_threshold * .99
            # print('merge ugly islands.')

    if (perimeter_ratio > op.island_shape_threshold):
        disqualified = True
        # print('ditch ugly island!')
    else:

        if do_unwrap:
            for f in islandfaces:
                f.select = True
            # select the island for unwrap:
            unwrap(op)
            for f in islandfaces:
                f.select = False

        area_ratio = testAreaRatio(bm, islandfaces)

        angle_ratio = testAngleRatio(bm, islandfaces)

        # commonseam_ratio = min(i1seams,i2seams)/ (commonseams * 3)

        total_weight = op.area_weight + op.angle_weight + op.island_shape_weight  # + op.commonseam_weight

        qualityratio = (area_ratio * op.area_weight
                        + perimeter_ratio * op.island_shape_weight
                        + angle_ratio * op.angle_weight) / \
                       total_weight  # + commonseam_ratio * op.commonseam_weight

        # allow to pass island with bad parimeter,if perimeter improves.

        if area_ratio > op.area_deformation_ratio_threshold or angle_ratio > op.angle_deformation_ratio_threshold:
            disqualified = True
        else:
            for f in islandfaces:
                f.select = True
            overlap = testOverlap(bm, islandfaces)
            for f in islandfaces:
                f.select = False
            disqualified = overlap
    # print(
    #     'area limit %f; shape perimietr limit %f; angle limit %f' % (
    #         op.area_deformation_ratio_threshold, op.angle_deformation_ratio_threshold, op.island_shape_threshold))
    # print(
    #     'totalqual %f; area %f; perimeter %f; angle %f; overlap %i;disqualified %i' % (
    #         qualityratio, area_ratio, perimeter_ratio, angle_ratio, overlap, disqualified))
    # qualityratio = qualityratio / 3

    return disqualified, qualityratio;


def get_border_seamchunks(island, island2, islandindices):
    commonseams = 0
    i2seams = 0
    for f in island2.faces:
        f.select = True
        for e in f.edges:
            if e.seam:
                i2seams += 1

    edone = {}
    seamchunks = []
    for f in island.faces:
        for e in f.edges:
            if e.seam and edone.get(e.index) == None:
                allsel = True
                lf = e.link_faces

                for f1 in lf:
                    if not f1.select:
                        allsel = False

                if allsel:
                    allsame = True

                    edone[e.index] = True
                    iidx = islandindices[lf[0].index]
                    for f1 in lf:
                        if islandindices[f1.index] != iidx:
                            allsame = False

                    if not allsame:
                        seamchunk = [e]
                        check = [e]
                        commonseams += 1
                        while len(check) > 0:
                            le = []
                            e1 = check.pop()
                            # print(len(check),len(seamchunk))
                            v1 = e1.verts[
                                0]  # on crossings we have to split the seams into more segments
                            v2 = e1.verts[1]

                            for v in e1.verts:
                                vseams = 0
                                for e in v.link_edges:
                                    if e.select and e.seam:
                                        vseams += 1
                                if vseams < 3:
                                    le.extend(v.link_edges)

                            for e2 in le:
                                if e2.select and e2.seam and edone.get(e2.index) == None:
                                    allsel = True
                                    lf = e2.link_faces
                                    for f2 in lf:
                                        if not f2.select:
                                            allsel = False

                                    if allsel:
                                        allsame = True
                                        iidx = islandindices[lf[0].index]
                                        for f2 in lf:
                                            if islandindices[f2.index] != iidx:
                                                allsame = False
                                            # print(islandindices[f2.index],i1idx)
                                        if not allsame:
                                            check.append(e2)
                                            seamchunk.append(e2)
                                            commonseams += 1
                                    edone[e2.index] = True
                        seamchunks.append(seamchunk)
    for f in island2.faces:
        f.select = False
    seamchunks.sort(key=len)
    seamchunks.reverse()
    return seamchunks


def mergeIslands(context,
                 bm, islands,
                 op):
    '''merge UV islands.
    By now it checks all the small islands, tries to find one buddy which improves their perimeter ratio.
    all pairs are unwrapped and tested at once in the end, to save performance.
    '''
    nislands = len(islands)
    wm = bpy.context.window_manager

    ob = bpy.context.active_object
    me = ob.data

    all = False
    done = {}
    ####filter single-face islands and try to connect them with islands in an optimal way(longest edge gets merged). no overlap check so far.
    # island indices assign the island to the face, effective for knowing which face belongs where.

    # prepare data
    islandindices = {}
    islands.sort(key=len)
    islands_dict = {}
    tests_done = {}  # to track which was tested with which unsuccessfully

    for i, island1 in enumerate(islands):
        for f in island1.faces:
            # if i == 1:
            #    f.select=True
            f.select = False
            islandindices[f.index] = i
        islands_dict[i] = island1
        tests_done[i] = []
    print('try to merge small islands')

    totaltests = 0
    for a in range(0, op.merge_iterations):
        merged = 0

        tests_prepared = []
        ready_for_test = {}  # dict stores which islands were already touched and shouldn't be before next round
        print(a)
        i1idx = 0
        print('picking merge candidates')
        for i1idx in islands_dict.keys():
            island1 = islands_dict[i1idx]
            if ready_for_test.get(i1idx) == True:
                continue;

            # if len(f.edges)<5:
            # f.select=True
            if len(island1.faces) < op.small_island_threshold:

                # find all border islands
                bislandsidx = []  # just for checks
                bislands = []
                i1seams = 0

                for f in island1.faces:
                    f.select = True
                    for i, e in enumerate(f.edges):
                        if e.seam:
                            i1seams += 1
                            for f in e.link_faces:
                                if not f.select:
                                    island2idx = islandindices[f.index]

                                    if not island2idx in bislandsidx:
                                        bislandsidx.append(island2idx)
                                        bislands.append([island2idx, True, 1000, 0, 0,
                                                         []])  # index, overlap, ratio, common seams, total seams,erase seams

                # print(bislands)
                orig_perimeter_ratio = testPerimeterRatio(bm, island1.faces)

                perimeter_tests = []
                test_islands = []
                found_neighbour = False  # only if we find an untested island can we proceed
                # overzealous test for border islands
                for islandinfo in bislands:

                    island2idx = islandinfo[0]
                    # don't test islands already ready for test
                    island2 = islands_dict[island2idx]

                    if len(island2.faces) > op.small_island_threshold or ready_for_test.get(
                            island2idx) is True or island2idx in tests_done[i1idx]:
                        perimeter_tests.append(1000)
                        test_islands.append(([], []))
                        for f in island1.faces:
                            f.select = False
                        continue

                    seamchunks = get_border_seamchunks(island1, island2, islandindices)

                    if len(seamchunks) == 0:
                        perimeter_tests.append(1000)
                        test_islands.append(([], []))
                        for f in island1.faces:
                            f.select = False
                        continue;

                    # print('seamchunks',len(seamchunks))
                    eraseseam = seamchunks[0]
                    # print(seamchunks)
                    newislandfaces = []
                    newislandfaces.extend(island1.faces)
                    newislandfaces.extend(island2.faces)

                    perimeter_ratio = testPerimeterRatio(bm, newislandfaces)
                    perimeter_tests.append(perimeter_ratio)
                    test_islands.append({
                        'island2': island2,
                        'common seams': eraseseam,
                        'island2idx': island2idx,
                        'faces': newislandfaces,
                        'perimeter_ratio:': perimeter_ratio
                    })
                    found_neighbour = True
                for f in island1.faces:
                    f.select = False

                if len(perimeter_tests) == 0:
                    continue;
                if not found_neighbour:
                    continue

                bestratioindex = np.argsort(perimeter_tests)[0]
                test = test_islands[bestratioindex]

                ready_for_test[i1idx] = True
                ready_for_test[test['island2idx']] = True

                tests_prepared.append({'faces': test['faces'],
                                       'orig perimeter': orig_perimeter_ratio,
                                       'common seams': test['common seams'],
                                       'island1': island1,
                                       'island2': test['island2'],
                                       'island1idx': i1idx,
                                       'island2idx': test['island2idx'],
                                       })
        # todo this should be removed probably
        for f in bm.faces:
            f.select = False

        if len(tests_prepared) == 0:
            return;

        i = 0
        for t in tests_prepared:
            # print(t)
            for e in t['common seams']:
                e.seam = False
                # e.select = True
            for f in t['faces']:
                f.select = True
        # if a == 1:
        #     fal
        print('unwrap')
        unwrap(op)
        print('testing islands')
        # for t in tests_prepared:
        #     print(t['island1idx'], t['island2idx'])
        # fal
        for t in tests_prepared:
            # print(t)
            disqualify, quality = testIslandQuality(context, bm, t['faces'], op, pass_orig_perimeter_ratio=True,
                                                    orig_perimeter_ratio=t['orig perimeter'],
                                                    do_unwrap=False)

            if disqualify:
                for e in t['common seams']:
                    e.seam = True
                    continue
                tests_done[t['island1idx']].append(t['island2idx'])
                tests_done[t['island2idx']].append(t['island1idx'])
            # error debug
            if islands_dict.get(t['island2idx']) == None:
                print(islands_dict.keys())
                for f in bm.faces:
                    f.select = False
                for f in t['island2'].faces:
                    f.select = True
                for f in t['island1'].faces:
                    f.select = True
            # move island here:
            t['island1'].faces = t['faces']
            t['island1'].seams = []  # at leaste delete them now.
            for f in t['island2'].faces:
                islandindices[f.index] = t['island1idx']
            islands_dict.pop(t['island2idx'])
            # print('popped', t['island2idx'], ' with ', t['island1idx'])
        for f in bm.faces:
            f.select = False


def seed_with_merge(context, op):
    wm = bpy.context.window_manager

    tot = 20000
    wm.progress_begin(0, tot)

    ob = bpy.context.active_object

    me = ob.data
    if op.init_seams:
        bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()

        for f in bm.faces:
            f.select = False
        for e in bm.edges:
            e.seam = False
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

    if op.merge_iterations > 0:
        mergeIslands(context,
                     bm, islands,
                     op)

    # final unpack happens here, could be replaced with something better but this by now does pack
    print('performing final unwrap')
    # for f in bm.faces:
    #     f.select = True
    bpy.ops.mesh.select_all(action='SELECT')

    bpy.ops.uv.select_all(action='SELECT')
    unwrap(op)

    wm.progress_end()
    # bpy.ops.object.editmode_toggle()


class testIsland(Operator):
    bl_idname = "uv.auto_seams_testisland"
    bl_label = "Auto seams test island"
    bl_options = {'REGISTER', 'UNDO'}

    init_seams: BoolProperty(name="Create new seams",
                             description="If on, totally new seams will be created, otherwise UV island merge will be performed",
                             default=False)

    unwrap_method: EnumProperty(name="Unwrap method",
                                description='choose the UV unwrap algorithm',
                                items=[
                                    ('CONFORMAL', 'Conformal', 'Conformal algorithm'),
                                    ('ANGLE_BASED', 'Angle based', 'Angle based algorithm')
                                ],
                                default='ANGLE_BASED')

    grow_iterations: IntProperty(
        name="Initial island grow iterations",
        description="This determines initial size of islands",
        min=0, max=50,
        default=2,
    )

    seed_points: IntProperty(
        name="Minimum seed points count",
        description="Minimum seed points count",
        min=10, max=500,
        default=40,
    )
    curvature_smooth_steps: IntProperty(
        name="Curvature smooth steps",
        description="Smooth steps for curve calculation, takes long time but creates nicer islands.",
        min=0, max=20,
        default=10,
    )

    keep_direction: FloatProperty(
        name="Keep Direction",
        description="Keep direction.",
        min=0, max=2.0,
        default=1.0,
    )
    curvature_influence: FloatProperty(
        name="Curvature Influence",
        description="Curvature Influence.",
        min=0, max=2.0,
        default=1.0,
    )
    merge_iterations: IntProperty(
        name="Merging step iterations",
        description="more iterations means bigger, but sometimes more complex islands",
        min=0, max=50,
        default=0,
    )

    island_margin: FloatProperty(
        name="Island Margin",
        description="Margin to reduce bleed from adjacent islands",
        min=0.0, max=1.0,
        default=0.0002,
    )

    small_island_threshold: IntProperty(
        name="Small island size limit",
        description="only islands smaller than the size will be merged.",
        min=0, max=500,
        default=50,
    )
    angle_deformation_ratio_threshold: FloatProperty(
        name="Angle deformation threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=1.01, max=30,
        default=1.5,
    )
    area_deformation_ratio_threshold: FloatProperty(
        name="Area deformation threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=1.01, max=30.0,
        default=1.5,
    )
    island_shape_threshold: FloatProperty(
        name="Island shape threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=0.5, max=50,
        default=1.4,
    )

    area_weight: FloatProperty(
        name="Area weight",
        description="Importance of area in quality estimation",
        min=0, max=100,
        default=1.0,
    )
    angle_weight: FloatProperty(
        name="Angle weight",
        description="Importance of angles in quality estimation",
        min=0, max=100,
        default=1.0,
    )
    island_shape_weight: FloatProperty(
        name="Island shape weight",
        description="Importance of island shape in quality estimation",
        min=0, max=100,
        default=2.0,
    )
    commonseam_weight: FloatProperty(
        name="Common seam weight",
        description="Importance of common seams when merging",
        min=0, max=100,
        default=1.0,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # test(context,self)
        #
        bpy.context.tool_settings.use_uv_select_sync = False
        me = bpy.context.active_object.data
        island = []
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            if f.select:
                island.append(f)

        testIslandQuality(context, bm, island, self)

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
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    init_seams: BoolProperty(name="Create new seams",
                             description="If on, totally new seams will be created, otherwise UV island merge will be performed",
                             default=True)

    island_style: EnumProperty(name="Island style",
                               description='choose style of how UV islands get generated',
                               items=[
                                   ('GROW', 'Grow', 'grow'),
                                   ('TILES', 'Tiles', 'checkerboard style'),
                                   ('CURVATURE', 'Curvature', 'Derives seams from object shape style')
                               ],
                               default='TILES')

    unwrap_method: EnumProperty(name="Unwrap method",
                                description='choose the UV unwrap algorithm',
                                items=[
                                    ('CONFORMAL', 'Conformal', 'Conformal algorithm'),
                                    ('ANGLE_BASED', 'Angle based', 'Angle based algorithm')
                                ],
                                default='ANGLE_BASED')

    sel_flat: BoolProperty(
        name="Select coplanar faces",
        description="selects coplanar faces in first step of the process",

        default=True,
    )

    grow_iterations: IntProperty(
        name="Initial island grow iterations",
        description="This determines initial size of islands",
        min=0, max=50,
        default=2,
    )

    seed_points: IntProperty(
        name="Minimum seed points count",
        description="Minimum seed points count",
        min=0, max=500,
        default=40,
    )
    curvature_smooth_steps: IntProperty(
        name="Curvature smooth steps",
        description="Smooth steps for curve calculation, takes long time but creates nicer islands.",
        min=0, max=20,
        default=10,
    )
    keep_direction: FloatProperty(
        name="Keep Direction",
        description="Keep direction.",
        min=0, max=2.0,
        default=1.0,
    )
    curvature_influence: FloatProperty(
        name="Curvature Influence",
        description="Curvature Influence.",
        min=0, max=2.0,
        default=1.0,
    )
    merge_iterations: IntProperty(
        name="Merging step iterations",
        description="more iterations means bigger, but sometimes more complex islands",
        min=0, max=50,
        default=0,
    )
    small_island_threshold: IntProperty(
        name="Small island size limit",
        description="only islands smaller than the size will be merged.",
        min=0, max=500,
        default=50,
    )
    angle_deformation_ratio_threshold: FloatProperty(
        name="Angle deformation threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=1.01, max=3,
        default=1.5,
    )
    area_deformation_ratio_threshold: FloatProperty(
        name="Area deformation threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=1.01, max=3.0,
        default=1.5,
    )
    island_shape_threshold: FloatProperty(
        name="Island shape threshold",
        description="Amount of deformation tolerated in the unwrapped islands",
        min=0.5, max=5,
        default=1.4,
    )

    area_weight: FloatProperty(
        name="Area weight",
        description="Importance of area in quality estimation",
        min=0, max=100,
        default=1.0,
    )
    angle_weight: FloatProperty(
        name="Angle weight",
        description="Importance of angles in quality estimation",
        min=0, max=100,
        default=1.0,
    )
    island_shape_weight: FloatProperty(
        name="Island shape weight",
        description="Importance of island shape in quality estimation",
        min=0, max=100,
        default=2.0,
    )
    commonseam_weight: FloatProperty(
        name="Common seam weight",
        description="Importance of common seams when merging",
        min=0, max=100,
        default=1.0,
    )
    island_margin: FloatProperty(
        name="Island Margin",
        description="Margin to reduce bleed from adjacent islands",
        min=0.0, max=1.0,
        default=0.0002,
    )
    show_advanced: BoolProperty(
        name="Advanced quality settings",
        description="tweaks unwrapping process",

        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'init_seams')
        if self.init_seams:
            layout.label(text='New Islands Generation:')
            layout.prop(self, 'island_style')
            if self.island_style == 'GROW':
                layout.label(text='grow method is only for meshes up to 10k faces')
                layout.prop(self, 'grow_iterations', text='Grow iterations')
            elif self.island_style == 'TILES':
                layout.label(text='Tiles method is meant for meshes up to 1M faces')
            elif self.island_style == 'CURVATURE':
                layout.label(text='Curves method is fast for meshes up to 1M faces,'
                                  ' but can generate overlaps.')
                layout.prop(self, 'seed_points')
                layout.prop(self, 'curvature_smooth_steps')
                layout.prop(self, 'keep_direction')
                layout.prop(self, 'curvature_influence')

        layout.label(text='Island merging:')
        layout.prop(self, 'merge_iterations')
        if self.merge_iterations > 0:
            layout.prop(self, 'small_island_threshold')
        layout.prop(self, 'island_margin')
        layout.prop(self, 'show_advanced')
        if self.show_advanced:
            layout.prop(self, 'angle_deformation_ratio_threshold')
            layout.prop(self, 'area_deformation_ratio_threshold')
            layout.prop(self, 'island_shape_threshold')
            layout.prop(self, 'area_weight')
            layout.prop(self, 'island_shape_weight')
            layout.prop(self, 'commonseam_weight')

    def execute(self, context):
        # test(context,self)
        #
        bpy.context.tool_settings.use_uv_select_sync = False

        seed_with_merge(context, self
                        )

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def menu_func(self, context):
    self.layout.separator()
    self.layout.operator_context = 'INVOKE_DEFAULT'

    # here are four presets, to simplify usage cases
    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='AS Scan/dyntopo - Tiles')
    op.init_seams = True
    op.island_style = 'TILES'
    op.angle_deformation_ratio_threshold = 1.2
    op.area_deformation_ratio_threshold = 1.35
    op.island_shape_threshold = 4.0
    op.small_island_threshold = 200
    op.merge_iterations = 4

    # here are four presets, to simplify usage cases
    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='AS Scan/dyntopo - Curvature')
    op.init_seams = True
    op.island_style = 'CURVATURE'
    op.curvature_smooth_steps = 10
    op.seed_points = 10
    op.angle_deformation_ratio_threshold = 1.2
    op.area_deformation_ratio_threshold = 1.35
    op.island_shape_threshold = 4.0
    op.small_island_threshold = 200
    op.merge_iterations = 5

    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='AS Lowpoly hardsurface')
    op.init_seams = True
    op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 20
    op.angle_deformation_ratio_threshold = 1.05
    op.area_deformation_ratio_threshold = 1.05
    op.island_shape_threshold = 1.25
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='AS Lowpoly organic')
    op.init_seams = True
    op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 50
    op.angle_deformation_ratio_threshold = 1.25
    op.area_deformation_ratio_threshold = 1.35
    op.island_shape_threshold = 1.25
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='AS Merge Islands')
    op.init_seams = False
    op.merge_iterations = 5
    op.small_island_threshold = 300
    op.angle_deformation_ratio_threshold = 1.6
    op.area_deformation_ratio_threshold = 1.6
    op.island_shape_threshold = 1.8
    # self.layout.operator(MergeIslands.bl_idname)
    self.layout.separator()


def register():
    bpy.utils.register_class(AutoSeamUnwrap)
    bpy.utils.register_class(testIsland)
    # bpy.utils.register_class(MergeIslands)
    bpy.types.VIEW3D_MT_uv_map.append(menu_func)
    # bpy.utils.register_manual_map(add_object_manual_map)
    # bpy.types.INFO_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(AutoSeamUnwrap)
    bpy.utils.unregister_class(testIsland)
    # bpy.utils.unregister_class(MergeIslands)
    # bpy.utils.unregister_manual_map(add_object_manual_map)
    # bpy.types.INFO_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
