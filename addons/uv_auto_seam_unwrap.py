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
#     uv_layer = bm.loops.layers.uv.active
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
    uv_layer = bm.loops.layers.uv.active

    # adjust UVs
    edges = []
    ekeys = {}
    for f in islandfaces:
        # let's try to check only border faces:
        needed = False
        for i, e in enumerate(f.edges):
            if e.seam or not e.is_manifold:
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
#     uv_layer = bm.loops.layers.uv.active
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
    uv_layer = bm.loops.layers.uv.active
    
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
#     uv_layer = bm.loops.layers.uv.active
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
    uv_layer = bm.loops.layers.uv.active

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


def testPerimeterRatio(bm, faces, by_seams=True, seams=None):
    perimeter = 0

    totalarea = 0
    totseams = 0
    totedges = 0
    if len(faces) == 0:
        return 1

    for f in faces:
        totalarea += f.calc_area()
        totedges += len(f.edges)  # adds number of tris actually

        if seams is None:
            for e in f.edges:
                if (by_seams and e.seam):
                    perimeter += e.calc_length()
                    totseams += 1
                if not by_seams:
                    for f1 in e.link_faces:
                        if f1 not in faces or len(e.link_faces) == 1:
                            perimeter += e.calc_length()
                            totseams += 1
    if seams is not None:
        for e in seams:
            perimeter += e.calc_length()
            totseams += 1

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


# old version, tests full face area.
# def testAreaRatio(bm, faces):
#     # print('test ratio')
#     uv_layer = bm.loops.layers.uv.active
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
    uv_layer = bm.loops.layers.uv.active

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


def unwrap_islands(op, islands):
    for island in islands:
        for f in island.faces:
            f.select = True
    unwrap(op)
    for island in islands:
        for f in island.faces:
            f.select = False


def getFaceNormalRatio(face):
    maxn = 0
    maxn = max(maxn, abs(face.normal.x))
    maxn = max(maxn, abs(face.normal.y))
    maxn = max(maxn, abs(face.normal.z))
    # print(maxn)
    return maxn


def grow_islands_limited(islands, islandindices, anglelimit_face2face=10, anglelimit_island=3.14 / 2,
                         perimeter_limit=4):
    all = False
    while not all:
        grown = False
        for i, island in enumerate(islands):
            if island.can_grow:
                island.can_grow = False
                new_grown = []
                i_normal = island.faces[0].normal
                # todo optimize this - check only border faces. otherwise it's crazy iteration inside the island.
                for f in island.last_grown:

                    for e in f.edges:
                        for f1 in e.link_faces:
                            # for f1 in e.link_faces:
                            i2 = islandindices[f1.index]  # potential index of neigbour island or own.
                            if i2 == -1:
                                f_angle = face_angle(e)
                                if i_normal.length > 0 and f1.normal.length > 0:
                                    i_angle = i_normal.angle(f1.normal)
                                else:
                                    i_angle = 0
                                perimeter_ratio = f1.calc_perimeter() / e.calc_length()
                                # print('fangle', f_angle, anglelimit_face2face, 'iangle', i_angle, anglelimit_island, 'peri', perimeter_ratio, perimeter_limit)

                                if f_angle < anglelimit_face2face and i_angle < anglelimit_island and perimeter_ratio < perimeter_limit:
                                    islandindices[f1.index] = i
                                    island.faces.append(f1)
                                    new_grown.append(f1)
                                    grown = True  # todo optimize this - can have island.growing per island not to check their respective seams.
                                # island can potentially grow whether or not a new face was added, because later iterations can have higher angle tolerance.
                                island.can_grow = True
                                continue

                            if i2 != i:
                                if islands[i2] not in island.neighbours:
                                    island.neighbours.append(islands[i2])

                island.last_grown = new_grown
        if not grown:
            all = True


def select_islands(bm, islands):
    for f in bm.faces:
        f.select = False
    for i in islands:
        for f in i.faces:
            f.select = True
    fal


def seedIslandsGrowth(context, bm, bm_dict, op):
    wm = bpy.context.window_manager

    ob = bpy.context.active_object

    anglelimit_island = 3.1415926 / 2.0  # 180 deg span in total
    anglelimit_face2face = op.growth_limit_angle  # crawling face jump limit.

    done = {}
    vgroup_weights = getCurvature(bm, bm_dict=bm_dict, smooth_steps=op.curvature_smooth_steps)
    print('growing UV islands')

    # sort faces by smallest curvature first, will start as centers of potential islands.

    # first, create face - weights array.
    fweights = np.zeros(len(bm.faces))
    for f in bm.faces:
        for v in f.verts:
            fweights[f.index] += abs(vgroup_weights[v.index]) / f.calc_area()

    face_order = np.argsort(fweights)

    topfaces = get_seed_faces(bm, fweights, seed_faces=op.seed_points)
    nislands = 0
    islands = []
    islandindices = {}
    for i in range(0, len(bm.faces)):
        islandindices[i] = -1

    # define initial islands
    for i, f in enumerate(topfaces):
        island = Island()
        island.faces = [f]
        # island.seams= f.edges[:]#carefull seams aren't yet defined!
        islands.append(island)
        islandindices[f.index] = i
        island.index = i
        island.last_grown = [f]

    perimeter_limit = 6
    print('first growth round')
    grow_islands_limited(islands, islandindices, anglelimit_face2face=anglelimit_face2face,
                         anglelimit_island=anglelimit_island, perimeter_limit=perimeter_limit)
    # select_islands(bm,islands)
    iters = 10
    for g in range(0, iters):
        donefaces = 0
        for island in islands:
            donefaces += len(island.faces)
            if island.can_grow:
                island.last_grown = island.faces[:]
        if donefaces == len(bm.faces):
            break

        anglelimit_face2face = anglelimit_face2face * 1.25
        perimeter_limit *= 1.25

        if g == iters -1 :
            anglelimit_face2face = 10
            perimeter_limit = 100
            anglelimit_island = 100
        # print(g, donefaces, perimeter_limit, anglelimit_island, anglelimit_face2face)
        grow_islands_limited(islands, islandindices, anglelimit_face2face=anglelimit_face2face,
                             anglelimit_island=anglelimit_island * 1.2, perimeter_limit=perimeter_limit)
        # select_islands((bm,islands))
    # select_islands(bm,islands)
    # try to smooth borders between islands.
    print('smooth borders')
    for i in islands:
        for n in i.neighbours:
            # print('smooth',i,n)
            smooth_borders(bm_dict, i, n, islandindices)


    # find island seams
    for i, island in enumerate(islands):
        for f in island.faces:
            for e in f.edges:
                for f1 in e.link_faces:
                    if f == f1:
                        continue
                    if islandindices[f1.index] != i:
                        e.seam = True
                        island.seams.append(e)


    # can't get steps directly because of uncertainity if the growth algo did reach all faces.
    # There might be possible unconnected parts or areas not reached from the seed points.
    # islands_for_test = islands
    islands_for_test = getIslands(bm)
    # select_islands(bm, islands)

    # tests initial island quality
    good_islands, disqalified_islands = testIslandsQuality(bm, op, islands_for_test)
    print(len(good_islands), len(disqalified_islands))
    split_result_islands = split_until_done(bm, bm_dict, op, disqalified_islands)
    good_islands.extend(split_result_islands)

    return good_islands


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
            w = face_angle_signed(e)
            edges.append([e, abs(w)])

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
                # a2 += e2.calc_face_angle() * curvature_influence
                a2 += abs(weights[v2.index]) * curvature_influence
            else:
                a2 = abs(weights[v2.index]) * curvature_influence * 2 - 5  # border faces should be prioritized.
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


def face_angle_signed(edge):
    '''helper function that does same as bmedge.calc_edge_signed(),
     but checks if edge isn't non manifold and returns 0 in such cases.'''
    if len(edge.link_faces) == 2:
        return edge.calc_face_angle_signed()
    else:
        return 0


def face_angle(edge):
    '''helper function that does same as bmedge.calc_edge_signed(),
     but checks if edge isn't non manifold and returns 0 in such cases.'''
    if len(edge.link_faces) == 2:
        return edge.calc_face_angle()
    else:
        return 0


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
        self.hit_seam = False
        self.can_be_used = True
        # self.meets = []  # which path the path meets
        self.siblings = []  # will be killed once successfull
        self.siblings_timeout = -1  # will be killed once successfull it's a

    def copy(self):
        cp = VPath()
        cp.index = -1
        cp.verts = self.verts[:]
        cp.edges = self.edges[:]
        cp.length = self.length
        cp.direction = self.direction.copy()
        cp.growing = True
        cp.hit_seam = self.hit_seam
        # cp.meets = []
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


def getBB_face_centers(faces):
    '''bounding box from face centers, may help with unsplittable islands.'''
    minx = 1000000
    miny = 1000000
    minz = 1000000
    maxx = -1000000
    maxy = -1000000
    maxz = -1000000
    x = []
    y = []
    z = []
    for f in faces:
        c = f.calc_center_median_weighted()
        vx, vy, vz = c.to_tuple()
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
        self.neighbours = []
        self.growing = False  # growth algorithm uses this.
        self.last_grown = []
        self.can_grow = True  # can grow if any of surrounding face isn't in another island yet. Mainly for growth algo.
        self.index = -1  # some algos use indices, some don't?

    def __len__(self):
        return len(self.faces)


class BMeshDict():
    def __init__(self):
        self.faces = {}
        self.neighbours_faces_edge = {}
        self.f_edges = {}
        self.neighbour_faces_vert = {}

        self.verts = {}
        self.v_neigbour_verts = {}

        self.edges = {}
        self.e_angles = {}
        self.e_lengths = {}
        self.e_angles_signed = {}
        self.e_verts = {}


def bm_to_dicts(bm):
    '''attempt to hugely speedup any analysis by using dicts instead of bmesh'''
    print('create optimisation data')
    bm_dict = BMeshDict()
    for f in bm.faces:
        fi = f.index
        bm_dict.faces[fi] = f
        neighbours_faces_edge = []
        neighbour_faces_vert = []
        edges = []
        for e in f.edges:
            edges.append(e.index)
            for f1 in e.link_faces:
                if f != f1:
                    neighbours_faces_edge.append(f1.index)
        bm_dict.neighbours_faces_edge[fi] = neighbours_faces_edge
        bm_dict.f_edges[fi] = edges

        for v in f.verts:
            for f1 in v.link_faces:
                if f1 != f and f1 not in neighbour_faces_vert:
                    neighbour_faces_vert.append(f1.index)

        bm_dict.neighbour_faces_vert[fi] = neighbour_faces_vert

    for e in bm.edges:
        ei = e.index
        bm_dict.edges[ei] = e
        bm_dict.e_angles[ei] = face_angle(e)
        bm_dict.e_angles_signed[ei] = face_angle_signed(e)
        bm_dict.e_verts[ei] = [e.verts[0].index, e.verts[1].index]
        bm_dict.e_lengths[ei] = e.calc_length()

    for v in bm.verts:
        vi = v.index
        neighbour_verts = []
        for e in v.link_edges:
            v1 = e.other_vert(v)
            neighbour_verts.append(v1.index)
        # bm_dict.verts[v.index] = v
        bm_dict.v_neigbour_verts[v.index] = neighbour_verts
    return bm_dict


def smooth_borders(bm_dict, island1, island2, islandindices={}):
    # little heuristic attempt to make nicer islands
    # should remove teeth on border of islands

    # check which faces have longer border with neigbour than with self.
    # this makes more sense on larger islands,
    # smaller islands (more deformed areas) might benefit form being not so nice.
    # tried to optimize this in many different ways, still quite slow. Bmesh iteration is what is slow!

    if len(island1) == 0 or len(island2) == 0:
        return

    # to acces which face belongs to which island really fast.
    findices1 = {}
    findices2 = {}
    fedges1 = {}
    fedges2 = {}
    for f in island1.faces:
        findices1[f.index] = 1

    for f in island2.faces:
        findices2[f.index] = 1

    # make 2 iterations - gives better results, but takes 2x time.
    for a in range(0, 2):
        remove1 = []

        for f in island1.faces:
            border_self = 0
            border_island2 = 0
            for ei, f1i in zip(bm_dict.f_edges[f.index], bm_dict.neighbours_faces_edge[f.index]):
                border = False
                if findices2.get(f1i) is not None:
                    border = True
                    border_island2 += bm_dict.e_lengths[ei]
                if not border:
                    border_self += bm_dict.e_lengths[ei]
            if border_island2 > border_self * 1.01:
                remove1.append(f)
        # never create 0 faces islands.
        if len(remove1) < len(island1):
            # island1.faces[:] = [face for face in island1.faces if face not in remove1]

            for f in remove1:
                island1.faces.remove(f)
                findices1[f.index] = None
                findices2[f.index] = 1
                islandindices[f.index] = island2.index
            island2.faces.extend(remove1)

        remove2 = []
        for f in island2.faces:
            border_self = 0
            border_island1 = 0
            for ei, f1i in zip(bm_dict.f_edges[f.index], bm_dict.neighbours_faces_edge[f.index]):
                border = False
                if findices1.get(f1i) is not None:
                    border = True
                    border_island1 += bm_dict.e_lengths[ei]
                if not border:
                    border_self += bm_dict.e_lengths[ei]
            if border_island1 > border_self * 1.01:
                remove2.append(f)

        # never create 0 faces islands.
        if len(remove2) < len(island2):
            # island2.faces[:] = [face for face in island2.faces if face not in remove2]
            for f in remove2:
                island2.faces.remove(f)
                islandindices[f.index] = island1.index

            island1.faces.extend(remove2)


# 3 functions for sorting faces quickly
def xKey(f):
    return f.calc_center_median_weighted().x


def yKey(f):
    return f.calc_center_median_weighted().y


def zKey(f):
    return f.calc_center_median_weighted().z


def split_island(bm, bm_dict, op, island, axis_override=None):
    islands = []
    # init boundbox on max, but don't calculate it in lower iters.
    if island.minv is None:
        if len(island) == len(bm.faces):
            island.minv, island.maxv = getBBbmesh(bm)
        else:
            island.minv, island.maxv = getBB(island.faces)

    axis, bbc = getSplitData(island.minv, island.maxv)

    # rint(axis)
    island1 = Island()
    island2 = Island()

    thres = bbc[axis]

    # split verts and also reassert bound box on the fly.
    for f in island.faces:
        c = f.calc_center_median_weighted()
        if c[axis] < thres:
            island1.faces.append(f)
        else:
            island2.faces.append(f)

    must_calc_bb = False
    # todo check for if more islands have actually been created here, can happen quite often
    if len(island1.faces) == 0 or len(island2.faces) == 0:

        island1 = Island()
        island2 = Island()

        # get new type of center and new axis. this may change results a lot on cylinders e.t.c.
        minv, maxv = getBB_face_centers(island.faces)
        c = (minv + maxv) / 2
        axis = getSplitAxis(minv, maxv)

        axis_coord = []
        for f in island.faces:
            axis_coord.append(f.calc_center_median_weighted()[axis])
        sorted = np.argsort(axis_coord)

        half = int(len(island.faces) / 2)
        for i in sorted[:half]:
            f = island.faces[i]
            island1.faces.append(f)
        for i in sorted[half:]:
            f = island.faces[i]
            island2.faces.append(f)

        # has to calculate bounding box because it could cause problems with splitting in lower iterations.
        must_calc_bb = True

    smooth_borders(bm_dict, island1, island2)

    has_new_seams = False
    island1.seams = []
    i1indices = {}
    for f in island1.faces:
        i1indices[f.index] = True

    for f in island1.faces:
        for e in f.edges:
            for f1 in e.link_faces:
                if i1indices.get(f1.index) is None and not e.seam:  # f1 not in island1.faces and not e.seam:#
                    # this marks a new seam.
                    e.seam = True
                    has_new_seams = True
                if e.seam:
                    island1.seams.append(e)

    island2.seams = []
    for f in island2.faces:
        for e in f.edges:
            if e.seam:
                island2.seams.append(e)
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


def split_islands(bm, bm_dict, op, islands_for_splitting, max_size=2000):
    '''split all islands into halves, now by their bound box.
        returns islands that can't be split anymore and
        islands that are ready for testing
        This function could be extended to split with the curvature algo
        or a new algo using unwrap deform results for splitting
    '''
    print('splitting islands')
    force_final_islands = []
    islands_for_test = []
    while len(islands_for_splitting) > 0:
        island = islands_for_splitting.pop()
        islands = split_island(bm, bm_dict, op, island)
        for island in islands:
            if len(island.faces) < max_size:
                if island.splittable:
                    islands_for_test.append(island)
                else:
                    # unsplittable island goes straight to finished, no chance to do anything with it anymore.
                    # todo - fix this. An unsplittable island shouldn't get here at all.
                    if len(island) > 1:
                        print('unsplittable island!', len(island))
                    force_final_islands.append(island)
            else:
                islands_for_splitting.append(island)
    return force_final_islands, islands_for_test


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


# def getCurvature(bm, smooth_steps=3):
# print('getting curvature')
# vgroup_weights = np.zeros(len(bm.verts))
#
# for f in bm.faces:
#     for e in f.edges:
#         ea = face_angle_signed(e) / 3.1415926
#         for v in e.verts:
#             # print(v.index)
#             vgroup_weights[v.index] += ea
#
# # no need to do calculation below if no smoothing happens, return.
# if smooth_steps == 0:
#     return vgroup_weights
# # optimization structure, not to access repeatedly
# elinks = []
# for v in bm.verts:
#     v_elinks = []
#     elinks.append(v_elinks)
#     for e in v.link_edges:
#         v2 = e.other_vert(v)
#         v_elinks.append(v2.index)
#
# print('smoothing curvature')
# # smoothing step
# for a in range(0, smooth_steps):
#     vgroup_weights_smooth = vgroup_weights.copy()
#     for v1i, v_elinks in enumerate(elinks):
#         for v2i in v_elinks:
#             vgroup_weights_smooth[v2i] += vgroup_weights[v1i] * (0.2 / len(v_elinks))
#
#     vgroup_weights = vgroup_weights_smooth
#
# # write_weights(vgroup_indices,vgroup_weights,'curvature')
#
# return vgroup_weights


def getCurvature(bm, smooth_steps=3, bm_dict=None):
    print('getting curvature')
    vgroup_weights = np.zeros(len(bm.verts))

    for ei in range(0, len(bm_dict.edges)):
        ea = bm_dict.e_angles_signed[ei]
        for vi in bm_dict.e_verts[ei]:
            vgroup_weights[vi] += ea

    # no need to do calculation below if no smoothing happens, return.
    if smooth_steps == 0:
        return vgroup_weights
    # optimization structure, not to access repeatedly

    print('smoothing curvature')
    # smoothing step
    for a in range(0, smooth_steps):
        vgroup_weights_smooth = vgroup_weights.copy()
        # print(bm_dict.v_neigbour_verts)

        # for item in bm_dict.v_neigbour_verts.items():
        #     for v2i in item[1]:
        #         vgroup_weights_smooth[v2i] += vgroup_weights[item[0]] * (0.2 / len(item[1]))

        for v1i in range(0, len(bm.verts)):
            neighbours = bm_dict.v_neigbour_verts[v1i]
            w = vgroup_weights[v1i] * (0.2 / len(neighbours))
            for v2i in neighbours:
                vgroup_weights_smooth[v2i] += w
        vgroup_weights = vgroup_weights_smooth

    # write_weights(vgroup_indices,vgroup_weights,'curvature')
    print('curvature done')
    return vgroup_weights


def get_top_verts(bm, vgroup_weights, seed_points=10):
    '''takes weights and returns it's local maxima points,  peaks and valleys'''
    topverts = []
    borderverts = []

    totverts = len(bm.verts)
    sorted_indices = np.argsort(vgroup_weights)

    max_top_points = max(seed_points, totverts * .015)
    consider_percentage = .5  # less creates less topverts
    # iterate verts sorted from highest possible weights.
    for vi in range(0, int(totverts * consider_percentage)):
        i = math.floor(vi / 2)
        if vi % 2 == 1:
            i = -i
        v = bm.verts[sorted_indices[i]]

        neighbour_selected = False
        for e in v.link_edges:
            for v1 in e.verts:
                if v != v1 and v1.select:
                    neighbour_selected = True

                    break
            if neighbour_selected:
                break
        if not neighbour_selected:
            topverts.append(v)
            if len(topverts) > max_top_points:
                break
        v.select = True
        for f in v.link_faces:
            for v1 in f.verts:
                v1.select = True
    return topverts


def get_seed_faces(bm, face_weights, seed_faces=10):
    '''takes weights and returns it's local maxima points,  peaks and valleys'''
    topfaces = []

    totfaces = len(bm.faces)
    sorted_indices = np.argsort(abs(face_weights))

    # max_seed_faces = max(seed_faces, totfaces * .015)
    consider_percentage = 1.0  # less creates less topverts
    # iterate faces sorted from lowest absolute possible weights. = should be the most flat areas on the mesh.
    for i in range(0, totfaces):
        f = bm.faces[sorted_indices[i]]

        neighbour_selected = False
        for v in f.verts:
            for f1 in v.link_faces:
                if f != f1 and f1.select:
                    # if neighbour is selected, it's not the extremity we are looking for.
                    neighbour_selected = True
                    break
            if neighbour_selected:
                break
        if not neighbour_selected:
            topfaces.append(f)
            # if len(topfaces) > max_seed_faces:
            #     break
        f.select = True
        # select direct neighbours, to increase distance a bit.
        if totfaces > 10000:
            for v in f.verts:
                for f1 in v.link_faces:
                    f1.select = True
    # for f in bm.faces:
    #     f.select = False
    # for f in topfaces:
    #     f.select = True
    # fal
    return topfaces


def seedIslandsCurvature(context, bm, bm_dict, op):
    bm.verts.ensure_lookup_table()
    # bm.faces.sort(key = xKey)

    vdists = []
    tops = []

    vgroup_weights = getCurvature(bm, bm_dict=bm_dict, smooth_steps=op.curvature_smooth_steps)

    # normalization to 0-1
    minw = vgroup_weights.min()
    maxw = vgroup_weights.max()

    normalized_weights = vgroup_weights - minw
    normalized_weights *= 1 / (maxw - minw)

    est_weights = abs(vgroup_weights)
    vgroup_indices = range(0, len(bm.verts))

    # find top points. select the most curved, and if they don't have any selected neighbours yet,
    # these should be the extremities we are looking for. Same from bottom up.
    print('looking for feature points')
    i = 0
    topverts = get_top_verts(bm, vgroup_weights, seed_points=op.seed_points)

    # test select top verts
    for v in bm.verts:
        v.select = False
    for i, v in enumerate(topverts):
        v.select = True
        # if i ==2:
        #    fal
    # write_weights(vgroup_indices, vgroup_weights, 'curvature')

    pathindex = 0
    done_verts = {}  # with indices of the path
    path_indices = {}  # so we can find the path that reached the point.
    topverts_meets = {}  # these are already connected.
    topverts_connected = {}  # these store if verts have already connected through other verts.
    possible_paths = []
    dead_ends = {}  # holds path that end on border of mesh.
    done_paths = []
    for v in topverts:
        # this stores all possible connecting paths:

        topverts_meets[v.index] = {}
        for vt in topverts:
            topverts_meets[v.index][vt.index] = []
        dead_ends[v.index] = []
        # if op.seed_points>(len(topverts)):
        #     seed_edges = v.link_edges
        # else:
        #     seed_edges = v_counter_edges(v)
        # print('topverts', len(topverts))
        seed_edges = v.link_edges
        for e in seed_edges:
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

            if not v_manifold(v2):
                p1.growing = False
                p1.hit_seam = True
                dead_ends[v.index].append(p1)

    done = False
    print('growing island seams')

    while not done:
        # growth loop for paths - they simply grow into their respective direction, and hit with the others.
        # the trick is, they grow at the same time this achieves something similar to delaunay.
        i = 0
        grown = False

        for p1 in possible_paths:
            remove = []
            # print(p)
            # print(dir(p))
            if p1.growing:
                if p1.siblings_timeout > 0:
                    p1.siblings_timeout -= 1
                    if p1.siblings_timeout == 0:
                        p1.growing = False

                new_paths = 0

                edges = continue_path_possibilities(p1, vgroup_weights, curvature_influence=op.curvature_influence,
                                                    threshold=1)
                npaths = [p1]
                # we will branch out so get ready by copying paths first.
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
                            p1.hit_seam = True
                            dead_ends[tv1.index].append(p1)
                            for s in p1.siblings:
                                s.siblings_timeout = 1
                    else:
                        p2i = done_verts[v2.index]  # path index
                        p2 = possible_paths[p2i]  # path we met
                        # get source toppoints
                        tv2 = possible_paths[p2i].verts[0]
                        if tv1 == tv2:  # means paths from same source did meet, shorter wins.
                            if p1.length < p2.length:
                                done_verts[v2.index] = p1.index
                                p2.growing = False
                            else:
                                p1.growing = False
                        else:

                            topverts_meets[tv1.index][tv2.index].append((p1, p2, v2))
                            topverts_meets[tv2.index][tv1.index].append((p1, p2, v2))
                            p1.growing = False
                            # if 1:#len(p1.verts)<=p2.verts.index(v2):
                            p2.growing = False
                            # originally this killed the siblings, but the fact that all paths hith their end relatively soon made it
                            for s in p2.siblings:
                                s.siblings_timeout = 1

                            for s in p1.siblings:
                                s.siblings_timeout = 1

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
            p1, p2, v_meet = meets[msort[0]]
            # create actual seams
            for vi, v in enumerate(p1.verts):
                if v == v_meet:
                    break
                e = p1.edges[vi]
                e.seam = True
            for vi, v in enumerate(p2.verts):
                if v == v_meet:
                    break
                e = p2.edges[vi]
                e.seam = True

        # paths towards border of non manifold mesh.
        sibling_groups = []
        # print(dead_ends)
        for de in dead_ends[tv1.index]:
            if de.can_be_used:
                if de.siblings not in sibling_groups:
                    sibling_groups.append(de.siblings)

        minlength = 1000000
        minlength_path = None

        for sg in sibling_groups:
            # if len(sibling_groups)>0:
            for p in sg:
                if p in dead_ends[tv1.index]:
                    if minlength > p.length:
                        minlength = p.length
                        minlength_path = p
        if minlength_path is not None:
            for e in minlength_path.edges:
                e.seam = True
                e.select = True
    # bm.faces.ensure_lookup_table()

    islands_for_test = getIslands(bm)
    # tests initial island quality
    good_islands, disqalified_islands = testIslandsQuality(bm, op, islands_for_test)
    print(len(good_islands), len(disqalified_islands))
    split_result_islands = split_until_done(bm, bm_dict, op, disqalified_islands)
    good_islands.extend(split_result_islands)

    return good_islands


def testIslandsQuality(bm, op, islands_for_test, do_perimeter=True):
    good_islands = []
    disqualified_islands = []

    unwrap_islands(op, islands_for_test)

    # final_islands_new, islands_for_splitting = testIslandsQuality()
    for island in islands_for_test:
        disqualified, quality = testIslandQuality(bm, island, op, do_unwrap=False, do_perimeter=do_perimeter)
        if not disqualified:
            good_islands.append(island)
        else:
            disqualified_islands.append(island)
    return good_islands, disqualified_islands


def split_until_done(bm, bm_dict, op, islands_for_splitting):
    # always split UV's perpendicular to longest axis in 3d space
    # do it in batches - split and get ready for test -> test -> do it again until done.

    totfaces = 0
    for i in islands_for_splitting:
        totfaces += len(i.faces)

    islands_for_test = []
    final_islands = []
    donefaces = 0
    i = 0
    itest = 0
    while len(islands_for_splitting) > 0 or len(islands_for_test) > 0:
        # first split everything that can be split
        print('splitting islands ', end='\r')

        finished_islands, islands_for_test = split_islands(bm, bm_dict, op, islands_for_splitting)

        # these islands are unsplittable islands from split_islands.
        final_islands.extend(finished_islands)

        # then unwrap all  at once and test and possibly send again to splitting queue.
        print('test islands')
        if len(islands_for_test) > 0:
            good_islands, disqualified_islands = testIslandsQuality(bm, op, islands_for_test, do_perimeter=False)
            final_islands.extend(good_islands)
            # print(len(final_islands, disqualified_islands))
            islands_for_splitting = disqualified_islands
            islands_for_test = []
        print()

    return final_islands


def seedIslandsTiles(context, bm, bm_dict, op):
    # always split UV's perpendicular to longest axis in 3d space

    start_island = Island()
    start_island.faces = bm.faces
    islands_for_splitting = [start_island, ]
    final_islands = split_until_done(bm, bm_dict, op, islands_for_splitting)
    return final_islands


def seedIslands(context, bm, bm_dict, op):
    if op.island_style == 'GROW':
        return seedIslandsGrowth(context, bm, bm_dict, op)

    elif op.island_style == 'CURVATURE':
        return seedIslandsCurvature(context, bm, bm_dict, op)

    elif op.island_style == 'TILES':
        return seedIslandsTiles(context, bm, bm_dict, op)


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


quality_logs = {
    'quality': 0,
    'area_ratio': 0,
    'perimeter': 0,
    'angle_ratio': 0,
    'overlap': 0,
    #     'totalqual %f; area %f; perimeter %f; angle %f; overlap %i;disqualified %i' % (
    #         qualityratio, area_ratio, perimeter_ratio, angle_ratio, overlap, disqualified))
}


def testIslandQuality(bm, island, op, pass_orig_perimeter_ratio=False, orig_perimeter_ratio=None,
                      do_unwrap=True, do_perimeter=True):
    if type(island) != list:
        islandfaces = island.faces
    else:
        islandfaces = island
    qualityratio = 10
    disqualified = False

    area_ratio = -1  # -1 means it wasn't tested
    angle_ratio = -1  # -1 means it wasn't tested
    overlap = -1  # -1 means it wasn't tested
    if do_perimeter:
        if type(island) != list:
            perimeter_ratio = testPerimeterRatio(bm, islandfaces, seams=island.seams)
        else:
            perimeter_ratio = testPerimeterRatio(bm, islandfaces)
    else:
        perimeter_ratio = op.island_shape_threshold * .99

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

        total_weight = op.area_weight + op.angle_weight + op.island_shape_weight  # + op.commonseam_weight

        qualityratio = (area_ratio * op.area_weight
                        + perimeter_ratio * op.island_shape_weight
                        + angle_ratio * op.angle_weight) / \
                       total_weight  # + commonseam_ratio * op.commonseam_weight

        # allow to pass island with bad parimeter,if perimeter improves.

        if area_ratio > op.area_deformation_ratio_threshold or angle_ratio > op.angle_deformation_ratio_threshold:
            disqualified = True
        else:
            overlap = testOverlap(bm, islandfaces)
            disqualified = overlap

    # global quality_logs

    # debug_output = {
    #     'shape perimietr limit': op.island_shape_threshold,
    #     'area limit':op.area_deformation_ratio_threshold,
    #     'angle limit':op.angle_deformation_ratio_threshold,
    #     'total quality':qualityratio,
    #     'perimeter quality': perimeter_ratio,
    #     'area quality': area_ratio,
    #     'angle quality': angle_ratio,
    #     'overlap': overlap,
    #     'disqualified': disqualified
    # }
    # print(debug_output)

    # print(
    #     f'perimeter limit {op.island_shape_threshold} {perimeter_ratio} {perimeter_ratio>op.island_shape_threshold}\n'
    #     f'area limit {op.area_deformation_ratio_threshold} {area_ratio} {area_ratio>op.area_deformation_ratio_threshold}\n'
    #     f'angle limit {op.angle_deformation_ratio_threshold} {angle_ratio} {angle_ratio>op.angle_deformation_ratio_threshold}\n'
    #     f'overlap {overlap} \n'
    #     f'#################################################################### passed the test {not disqualified} '
    # )

    # qualityratio = qualityratio / 3

    return disqualified, qualityratio


def get_border_seamchunks(island, island2, islandindices):
    '''gets common seams between 2 islands, can be more chunks.'''
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


def neglen(x):
    return -len(x)


def get_ratio(test):
    return test['ratio']


def mergeIslands(context,
                 bm, bm_dict, islands,
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
    # islands.sort(key=neglen)
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

                for f in island1.faces:
                    f.select = True

                for e in island1.seams:
                    for f in e.link_faces:
                        idx = islandindices[f.index]
                        if idx != i1idx:
                            island2idx = idx
                            if not island2idx in bislandsidx:
                                # store some info about the other island
                                bislandsidx.append(island2idx)
                                bislands.append([island2idx, True, 1000, 0, 0,
                                                 []])  # index, overlap, ratio, common seams, total seams,erase seams

                # print(bislands)
                orig_perimeter_ratio = testPerimeterRatio(bm, island1.faces, seams=island1.seams)

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
                        continue

                    seamchunks = get_border_seamchunks(island1, island2, islandindices)

                    if len(seamchunks) == 0:
                        continue;

                    # print('seamchunks',len(seamchunks))
                    eraseseam = seamchunks[0]
                    # print(seamchunks)
                    newislandfaces = []
                    newislandfaces.extend(island1.faces)
                    newislandfaces.extend(island2.faces)

                    perimeter_ratio = testPerimeterRatio(bm, newislandfaces, by_seams=False)

                    # test angle with the island
                    angle_ratio = 0
                    for e in seamchunks[0]:
                        angle_ratio += face_angle(e)
                    angle_ratio /= len(seamchunks[0])

                    # common_seams_ratio
                    i1seams = len(island1.seams)
                    i2seams = len(island2.seams)

                    i1seams_length = 0
                    for edge in island1.seams:
                        i1seams_length += e.calc_length()
                    i2seams_length = 0
                    for edge in island2.seams:
                        i2seams_length += e.calc_length()
                    commonseam_length = 0
                    for e in eraseseam:
                        commonseam_length += e.calc_length()

                    # commonseam_ratio = min(i1seams,i2seams)/ (len(eraseseam) * 3)

                    commonseam_ratio = min(i1seams_length, i2seams_length) / commonseam_length

                    # print(i1seams_length,i2seams_length,commonseam_length, commonseam_ratio)
                    # print('angle     peri     commonseam     facecounts')
                    # print(angle_ratio, perimeter_ratio, commonseam_ratio, len(island1), len(island2))
                    ratio = perimeter_ratio + angle_ratio * 3 + commonseam_ratio * 2

                    # drop the tests if not pass
                    if perimeter_ratio > op.island_shape_threshold:
                        continue

                    if commonseam_ratio > 6:  # this could be added to parameters, but hell... there are so many already.
                        # print(commonseam_ratio)
                        continue

                    perimeter_tests.append(ratio)
                    test_islands.append({
                        'island1': island1,
                        'island2': island2,
                        'orig perimeter': orig_perimeter_ratio,
                        'common seams': eraseseam,
                        'island1idx': i1idx,
                        'island2idx': island2idx,
                        'faces': newislandfaces,
                        'perimeter_ratio': perimeter_ratio,
                        'commonseam_ratio': commonseam_ratio,
                        'angle_ratio': angle_ratio,
                        'ratio': ratio
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
                # print(test)
                if test['perimeter_ratio'] < op.island_shape_threshold:  # orig_perimeter_ratio *1.2:

                    ready_for_test[i1idx] = True
                    ready_for_test[test['island2idx']] = True

                    tests_prepared.append(test)

        # todo this should be removed probably
        for f in bm.faces:
            f.select = False

        if len(tests_prepared) == 0:
            return;

        # sort by quality and then reduce number of tests per iteration further.
        tests_prepared.sort(key=get_ratio)
        if len(tests_prepared) > 5:
            tests_prepared = tests_prepared[:int(len(tests_prepared) / 2)]

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
            # dont unwrap and test perimeter - already done.
            disqualify, quality = testIslandQuality(bm, t['faces'], op, pass_orig_perimeter_ratio=True,
                                                    orig_perimeter_ratio=t['orig perimeter'],
                                                    do_unwrap=False, do_perimeter=False)

            if disqualify:
                for e in t['common seams']:
                    e.seam = True
                    continue
                tests_done[t['island1idx']].append(t['island2idx'])
                tests_done[t['island2idx']].append(t['island1idx'])
            else:
                # successfull merge
                merged += 1
                tests_done[t['island1idx']] = []  # zero out tests done since it's a new island now.
            # error debug
            if islands_dict.get(t['island2idx']) == None:
                print(islands_dict.keys())
                for f in bm.faces:
                    f.select = False
                for f in t['island2'].faces:
                    f.select = True
                for f in t['island1'].faces:
                    f.select = True
            # move island2 into island1 here, and delete island2.
            t['island1'].faces = t['faces']
            # merging seams - careful here ;)
            for e in t['common seams']:
                t['island1'].seams.remove(e)
                t['island2'].seams.remove(e)
            t['island1'].seams.extend(t['island2'].seams)  #
            for f in t['island2'].faces:
                islandindices[f.index] = t['island1idx']
            islands_dict.pop(t['island2idx'])
            # print('popped', t['island2idx'], ' with ', t['island1idx'])
        for f in bm.faces:
            f.select = False
        print('merged ', merged)
        if merged == 0:
            break;


def seed_with_merge(context, op):
    wm = bpy.context.window_manager

    tot = 20000
    wm.progress_begin(0, tot)

    # get bmesh
    ob = bpy.context.active_object
    me = ob.data
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    bm_dict = bm_to_dicts(bm)

    if op.init_seams:

        for f in bm.faces:
            f.select = False
        for e in bm.edges:
            e.seam = False
        # seedPerfectIslands(context, bm,  op)
        islands = seedIslands(context,
                              bm, bm_dict, op)
    else:

        islands = getIslands(bm)

    if op.merge_iterations > 0:
        mergeIslands(context,
                     bm, bm_dict, islands,
                     op)

    # here was originally unwrap of everything, but we want to avoid it
    #  - large meshes can take ages and the unwrap is already done during all the testing.
    #
    #using unwrap , by now some algos obviously don't unwrap all islands, have to check it , when all algorithms unwrap,
    # then only packing can be used from here on.
    print('packing islands')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    unwrap(op)
    # bpy.ops.uv.average_islands_scale()
    # bpy.ops.uv.pack_islands(margin=op.island_margin)

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
    growth_limit_angle: FloatProperty(
        name="Growth limit angle",
        description="",
        min=0, max=3.14,
        default=3.14 / 4.0,
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
        default=1,
    )
    curvature_influence: FloatProperty(
        name="Curvature Influence",
        description="Curvature Influence.",
        min=0, max=2.0,
        default=1,
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
        min=0, max=1000,
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

        testIslandQuality(bm, island, self)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class AutoSeamUnwrap(Operator):
    """iteratively finds seams, and unwraps selected object. """ \
    """can take a long time to compute""" \
    """doesn't produce 'pretty' islands but works good for getting low number of islands on complex meshes, 
    and works good with any UV packing.
    """
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
    growth_limit_angle: FloatProperty(
        name="Growth limit angle",
        description="",
        min=0, max=3.14,
        default=3.14 / 4.0,
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
        default=1,
    )
    curvature_influence: FloatProperty(
        name="Curvature Influence",
        description="Curvature Influence.",
        min=0, max=2.0,
        default=1,
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
        min=0, max=1000,
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
                layout.label(text='grow method is recommended for meshes up to 200k faces')
                # layout.prop(self, 'grow_iterations', text='Grow iterations')
            elif self.island_style == 'TILES':
                layout.label(text='Tiles method is recommended for meshes up to 1M faces')
            elif self.island_style == 'CURVATURE':
                layout.label(text='Curves method is recommended for meshes up to 1M faces')
        layout.prop(self, 'unwrap_method')

        layout.label(text='Island merging:')
        layout.prop(self, 'merge_iterations')
        if self.merge_iterations > 0:
            layout.prop(self, 'small_island_threshold')
        layout.prop(self, 'island_margin')
        layout.prop(self, 'show_advanced')
        if self.show_advanced:
            layout.prop(self, 'seed_points')
            layout.prop(self, 'curvature_smooth_steps')
            if self.island_style == 'CURVATURE':
                layout.prop(self, 'keep_direction')
                layout.prop(self, 'curvature_influence')
            layout.separator()
            layout.prop(self, 'angle_deformation_ratio_threshold')
            layout.prop(self, 'area_deformation_ratio_threshold')
            layout.prop(self, 'island_shape_threshold')
            layout.prop(self, 'area_weight')
            layout.prop(self, 'island_shape_weight')
            layout.prop(self, 'commonseam_weight')
            layout.prop(self, 'growth_limit_angle')

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
    op.unwrap_method = 'CONFORMAL'

    op.angle_deformation_ratio_threshold = 1.4
    op.area_deformation_ratio_threshold = 1.4
    op.island_shape_threshold = 2.0
    op.small_island_threshold = 400
    op.merge_iterations = 4

    # here are four presets, to simplify usage cases
    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='AS Scan/dyntopo - Curvature')
    op.init_seams = True
    op.island_style = 'CURVATURE'
    op.unwrap_method = 'ANGLE_BASED'

    op.curvature_smooth_steps = 10
    op.seed_points = 30
    op.angle_deformation_ratio_threshold = 1.2
    op.area_deformation_ratio_threshold = 1.35
    op.island_shape_threshold = 1.8
    op.small_island_threshold = 400
    op.merge_iterations = 5

    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='AS Growth - Hardsurface')
    op.init_seams = True
    op.unwrap_method = 'CONFORMAL'
    op.growth_limit_angle = 3.14 / 8.0
    # op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 150
    op.curvature_smooth_steps = 1
    op.angle_deformation_ratio_threshold = 1.05
    op.area_deformation_ratio_threshold = 1.05
    op.island_shape_threshold = 1.8
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='AS Growth - Organic')
    op.init_seams = True
    op.unwrap_method = 'ANGLE_BASED'
    # op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 300
    op.curvature_smooth_steps = 3
    op.angle_deformation_ratio_threshold = 1.3
    op.area_deformation_ratio_threshold = 1.4
    op.island_shape_threshold = 1.8
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='AS Merge Islands Only')
    op.init_seams = False
    op.unwrap_method = 'COMFORMAL'

    op.merge_iterations = 5
    op.small_island_threshold = 800
    op.angle_deformation_ratio_threshold = 1.6
    op.area_deformation_ratio_threshold = 1.6
    op.island_shape_threshold = 1.4
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
