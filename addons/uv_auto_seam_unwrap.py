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

def getIslands(bm):
    # bm = bmesh.from_edit_mesh(me)
    for f in bm.faces:
        f.select = False
    all = False
    done = {}
    islands = []
    while not len(done) >= len(bm.faces):
        island = Island()
        for i, p in enumerate(bm.faces):

            if done.get(i) == None:
                p.select = True
                done[i] = True
                island.faces.append(p)
                break
        new_faces = [p]
        while len(new_faces) > 0:
            selected_faces = new_faces
            new_faces = []

            for f in selected_faces:
                for edge in f.edges:
                    if edge.seam == False:
                        linkede = edge.link_faces
                        for face in linkede:
                            if not face.select and done.get(face.index) == None:
                                done[face.index] = True
                                new_faces.append(face)
                                face.select = True
                                island.faces.append(face)
                    else:
                        island.seams.append(edge)
        islands.append(island)
        for f in island.faces:
            f.select = False
    return islands


def testOverlap(bm, faces):
    # print('test overlap')
    uv_layer = bm.loops.layers.uv.verify()
    # t1 = time.time()
    bpy.ops.uv.select_all(action='DESELECT')

    bpy.ops.uv.select_overlap()
    # t2 = time.time()
    # print('overlap select overlap took ', t2 - t1)
    # read and restructure UVs into arrays of edges and dicts
    edges = []
    ekeys = {}
    t = time.time()
    for f in faces:
        i = 0
        for l in f.loops:
            luv = l[uv_layer]

            if luv.select:
                # t2 = time.time()
                # print('overlap intersect check for ill island took ', t2 - t)
                return True
            # if i == len(f.loops) - 1:
            #     uv1 = luv.uv
            #     uv2 = f.loops[0][uv_layer].uv
            #
            # else:
            #     uv1 = luv.uv
            #     uv2 = f.loops[i + 1][uv_layer].uv
            # add = True
            # uv1 = uv1.to_tuple()
            # uv2 = uv2.to_tuple()
            # # here write each edge only once
            # if ekeys.get(uv1) == None:
            #     ekeys[uv1] = [uv2]
            #
            # elif uv2 in ekeys[uv1]:
            #     add = False
            # else:
            #     ekeys[uv1].append(uv2)
            #
            # if ekeys.get(uv2) == None:
            #     ekeys[uv2] = [uv1]
            # else:
            #     ekeys[uv2].append(uv1)
            # if add:
            #     edges.append((uv1, uv2))
            # i += 1

    # t1 = time.time()
    # print('preparation of overlap check took ', t1 - t)
    return False
    # print(len(edges),len(faces))
    # using select overlap now, much faster, kept here this to not try again.
    # totiter = 0
    # for i1, e in enumerate(edges):
    #     for i2 in range(i1 + 1, len(edges)):
    #         totiter += 1
    #         # if i1!=i2:
    #         e2 = edges[i2]
    #         if e[0] != e2[0] and e[0] != e2[1] and e[1] != e2[0] and e[1] != e2[
    #             1]:  # no common vertex, since that's an intersection too.
    #             intersect = mathutils.geometry.intersect_line_line_2d(e[0], e[1], e2[0], e2[1])
    #             if intersect != None:
    #                 # cancel on first intersection found
    #                 t2 = time.time()
    #                 print('overlap intersect check for ill island took ', t2 - t1)
    #
    #                 return True
    # t2 = time.time()
    # print('overlap intersect check for healthy island took ', t2 - t1)
    #
    # # print(totiter)
    # return False


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
    for fi,f in enumerate(faces):
        i1 = 0
        i2 = 1
        i3 = -1

        v1 = f.verts[i2].co - f.verts[i1].co
        v2 = f.verts[i3].co - f.verts[i2].co

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



    finalratio = ratios.mean()

    #maxratio = ratios.max()
    #print(finalratio, maxratio)
    #maxratio = max(finalratio, maxratio + 1)

    return finalratio


def testPerimeterRatio(bm, faces, by_seams=True):
    perimeter = 0

    totalarea = 0
    totseams = 0
    totedges = 0

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
    perimeter_length_ratio = (perimeter / divider) / math.sqrt(totalarea)

    perimeter_count_ratio = (totseams / divider) / math.sqrt(len(faces))
    # print(perimeter_length_ratio)
    perimeter_ratio = (2 * perimeter_length_ratio + perimeter_count_ratio) / 3

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
    for fi,f in enumerate(faces):
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


    minsoft = 1/ratios[ratios < 1 ].mean()
    maxsoft = ratios[ratios > 1 ].mean()
    #print('min %f minsoft %f max %f maxsoft %f' %(minratio, minsoft, maxratio, maxsoft))
    maxratio = max(maxsoft, minsoft)
    return maxratio


def unwrap(op):
    bpy.ops.uv.unwrap(method='CONFORMAL', fill_holes=True, margin=op.island_margin)


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
                    #print(disqualify, quality)

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
    remove = []
    for f in island1.faces:
        border_self = 0
        border_island2 = 0
        for e in f.edges:
            border = False
            for f1 in e.link_faces:
                if not f1.select:
                    border = True
                    if f1 in island2.faces:
                        border_island2 += e.calc_length()
            if not border:
                border_self += e.calc_length()
        if border_island2 > border_self * 1.05:
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
                    if f1 in island1.faces:
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

    # island1 hets lower half, island 2 upper in any axis, pass the boundbox so it is computed only once.
    island1.minv = island.minv.copy()
    island1.maxv = island.maxv.copy()
    island1.maxv[axis] = bbc[axis]

    island2.minv = island.minv.copy()
    island2.maxv = island.maxv.copy()
    island2.minv[axis] = bbc[axis]

    thres = bbc[axis]

    for f in island.faces:
        c = f.calc_center_median_weighted()
        if c[axis] < thres:
            f.select = True
            island1.faces.append(f)
        else:
            f.select = False
            island2.faces.append(f)

    smooth_borders(island1, island2)
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


        if len(island1.faces) > 0:
            island1.minv, island1.maxv = getBB(island1.faces)
        if len(island2.faces) > 0:
            island2.minv, island2.maxv = getBB(island2.faces)

    ntests += 1

    for f in island1.faces:
        for e in f.edges:
            for f in e.link_faces:
                if not f.select:
                    e.seam = True
    # if ntests > 33:
    #     fal
    # deselect here, should be safely deselected for later...
    for f in island1.faces:
        f.select = False
    retislands = []
    for i in [island1, island2]:
        if len(i.faces) > 0:
            retislands.append(i)
    #if an island wasn't split, set it unsplittable, helps in heavy recursion problems
    if len(retislands) == 1:

        retislands[0].splittable = False

    return retislands


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
        print('splitting islands ', end = '\r')
        while len(islands_for_splitting) > 0:
            island = islands_for_splitting.pop()
            islands = splitIslands(bm, island, op)

            for island in islands:
                if len(island.faces) < 2000:
                    if island.splittable:
                        islands_for_test.append(island)
                    else:
                        #unsplittable island goes straight to finished, no chance to do anything with it anymore.
                        final_islands.append(island)
                        donefaces += len(island.faces)
                else:
                    islands_for_splitting.append(island)
            i+=1

            print('splitting islands %i' % i, end = '\r')
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
                disqualified, quality = testIslandQuality(bpy.context, bm, island.faces, op, do_unwrap=False)

                if not disqualified:
                    donefaces += len(island.faces)
                    itest+=1
                    print('testing islands %i, done faces %i ' % (itest, donefaces), end='\r')
                    final_islands.append(island)
                else:
                    islands_for_splitting.append(island)
            islands_for_test = []
        print()
    return final_islands


def seedIslands(context, bm, op):
    if op.island_style == 'GROW':
        return seedIslandsGrowth(context, bm, op)
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


def testIslandQuality(context, bm, islandfaces, op, pass_orig_perimeter_ratio=False, orig_perimeter_ratio=None,
                      do_unwrap=True):
    qualityratio = 10
    disqualified = False

    area_ratio = -1  # -1 means it wasn't tested
    angle_ratio = -1  # -1 means it wasn't tested
    overlap = -1  # -1 means it wasn't tested

    perimeter_ratio = testPerimeterRatio(bm, islandfaces)
    if pass_orig_perimeter_ratio:
        if perimeter_ratio < orig_perimeter_ratio and perimeter_ratio > op.island_shape_threshold:
            perimeter_ratio = op.island_shape_threshold * .99
            print('merge ugly islands!')

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
                        + angle_ratio * op.angle_weight)/\
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


def mergeIslands(context,
                 bm, islands,
                 op):
    nislands = len(islands)
    wm = bpy.context.window_manager

    # idea
    # kazdy s kazdym test(vzdy jen jednou), ma svou kvalitu.
    # island uz musi byt objekt
    # dvojice do listu, seradit podle kvality?
    # vsechny zamergovat podle poradi, ty ktere jsou spojeny musi byt preskoceny (done nebo neco podobneho)
    # !!!! uspora vykonu, rovnomernejsi velikost vysledku.

    ob = bpy.context.active_object
    me = ob.data

    all = False
    done = {}
    ####filter single-face islands and try to connect them with islands in an optimal way(longest edge gets merged). no overlap check so far.
    # fal
    islandindices = {}
    islands.sort(key=len)
    for i, island in enumerate(islands):
        for f in island.faces:
            # if i == 1:
            #    f.select=True
            islandindices[f.index] = i

    # for f in bm.faces:
    #    if islandindices.get(f.index) == None:
    #        print('bad face', f.index)
    #        f.select=True
    # fal
    print('try to merge small islands')

    totaltests = 0
    for a in range(0, op.merge_iterations):
        merged = 0

        print(a)
        i1idx = 0
        while i1idx < len(islands):
            island = islands[i1idx]
            # if len(f.edges)<5:
            # f.select=True
            if len(island.faces) < op.small_island_threshold:

                # find all border islands
                bislandsidx = []  # just for checks
                bislands = []
                i1seams = 0

                for f in island.faces:
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
                orig_perimeter_ratio = testPerimeterRatio(bm, island.faces)

                for islandinfo in bislands:
                    island2idx = islandinfo[0]
                    island2 = islands[island2idx]

                    commonseams = 0
                    i2seams = 0
                    for f in island2.faces:
                        f.select = True
                        for e in f.edges:
                            if e.seam:
                                i2seams += 1

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
                    # get connecting seam rows
                    seamchunks = []
                    edone = {}

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

                    if len(seamchunks) > 0:
                        # print('seamchunks',len(seamchunks))
                        eraseseam = seamchunks[0]
                        # break
                        maxlen = 0
                        if len(seamchunks) > 1:
                            # print(seamchunks)

                            for sch in seamchunks:
                                if len(sch) > maxlen:
                                    eraseseam = sch
                                    maxlen = len(sch)
                        commonlength = 0
                        for e in eraseseam:
                            # e.select=True
                            e.seam = False
                            commonlength += e.calc_length()
                        newislandfaces = []
                        newislandfaces.extend(island.faces)
                        newislandfaces.extend(island2.faces)

                        # now
                        # f.edges[maxlenidx].seam=False

                        overlap, qualityratio = testIslandQuality(context, bm, newislandfaces, op,
                                                                  pass_orig_perimeter_ratio=True,
                                                                  orig_perimeter_ratio=orig_perimeter_ratio)
                        islandinfo[1] = overlap
                        islandinfo[2] = qualityratio
                        islandinfo[3] = commonlength  # commonseams
                        islandinfo[4] = i2seams
                        islandinfo[5] = eraseseam

                        # print(islandinfo)
                        # print(qualityratio)
                        for f in island2.faces:
                            f.select = False
                        for f in island.faces:
                            f.select = True
                        for f in island.faces:  # returning seams here , we are testing several merge options.
                            for e in f.edges:
                                lfaces = e.link_faces
                                if len(lfaces) > 1:
                                    for lf in lfaces:
                                        if lf.select == False:
                                            e.seam = True

                besti = -1
                bestratio = 10000
                bestseamcount = -100
                # print(bislands)
                for i, islandinfo in enumerate(
                        bislands):  # comparison of quality, currently the longest seam gets preference, so islands are not too snake-y

                    if not islandinfo[1]:  # and islandinfo[2]<deformation_ratio_threshold:
                        # if bestratio>islandinfo[2]:
                        #    bestratio=islandinfo[2]
                        #    besti = i

                        if bestseamcount < islandinfo[3]:
                            besti = i
                            bestseamcount = islandinfo[3]

                # print(bestratio,islandinfo)
                totaltests += 1
                # if len(bislands)==1:
                # print(seamchunks)
                # besti=0
                if besti > -1:  # or en(bislands)==1:

                    # if len(island)==1:
                    #    print(seamchunks)  
                    iinfo = bislands[besti]
                    island2idx = iinfo[0]
                    island2 = islands[island2idx]
                    for f in island2.faces:
                        f.select = True

                    for e in iinfo[5]:
                        e.seam = False

                    island.faces.extend(island2.faces)
                    # islands[i1idx]=island.extend(island2)

                    for f in island2.faces:
                        islandindices[f.index] = i1idx
                    for dkey in islandindices.keys():
                        if islandindices[dkey] > island2idx:
                            islandindices[dkey] -= 1
                    islands.pop(island2idx)

                    nislands -= 1
                    print('merge islands %i cycle %i' %(nislands, a), end = '\r')
                    merged += 1
                    wm.progress_update(nislands)
                for f in island.faces:
                    f.select = False

            i1idx += 1
        if merged == 0:
            break

    for f in bm.faces:
        f.select = True
    unwrap(op)
    for f in bm.faces:
        f.select = False
    print('total tests', totaltests)
    print('nislands')
    print(nislands, len(islands))
    # me = bpy.context.active_object.data
    # bmesh.update_edit_mesh( True)
    pass;


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
    for f in bm.faces:
        f.select = True
    unwrap(op)

    wm.progress_end()
    # bpy.ops.object.editmode_toggle()


class testIsland(Operator):
    bl_idname = "uv.auto_seams_testisland"
    bl_label = "Auto seams test island"
    bl_options = {'REGISTER', 'UNDO'}

    init_seams: BoolProperty(name="Create new seams",
                             description="If on, totally new seams will be created, otherwise UV island merge will be performed",
                             default=True)

    grow_iterations: IntProperty(
        name="Initial island grow iterations",
        description="This determines initial size of islands",
        min=0, max=50,
        default=2,
    )
    merge_iterations: IntProperty(
        name="Merging step iterations",
        description="more iterations means bigger, but sometimes more complex islands",
        min=0, max=50,
        default=3,
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
                                   ('TILES', 'Tiles', 'checkerboard style')
                               ],
                               default='TILES')

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
    merge_iterations: IntProperty(
        name="Merging step iterations",
        description="more iterations means bigger, but sometimes more complex islands",
        min=0, max=50,
        default=3,
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
            else:
                layout.label(text='Tiles method is meant for meshes up to 1M faces')

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
    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='Autoseam Scan/dyntopo')
    op.init_seams = True
    op.island_style = 'TILES'
    op.angle_deformation_ratio_threshold = 1.2
    op.area_deformation_ratio_threshold = 1.8
    op.island_shape_threshold = 4.0
    op.small_island_threshold = 50
    op.merge_iterations = 0

    op = self.layout.operator(AutoSeamUnwrap.bl_idname, text='Autoseam Lowpoly hardsurface')
    op.init_seams = True
    op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 120
    op.angle_deformation_ratio_threshold = 1.05
    op.area_deformation_ratio_threshold = 1.05
    op.island_shape_threshold = 1.25
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='Autoseam lowpoly organic')
    op.init_seams = True
    op.grow_iterations = 6
    op.merge_iterations = 5
    op.small_island_threshold = 120
    op.angle_deformation_ratio_threshold = 1.4
    op.area_deformation_ratio_threshold = 1.4
    op.island_shape_threshold = 1.25
    op.island_style = 'GROW'

    op = self.layout.operator(AutoSeamUnwrap.bl_idname,
                              text='Autoseam merge islands only')
    op.init_seams = False
    op.merge_iterations = 5
    op.small_island_threshold = 1000
    op.angle_deformation_ratio_threshold = 1.4
    op.area_deformation_ratio_threshold = 1.3
    op.island_shape_threshold = 1.5
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
