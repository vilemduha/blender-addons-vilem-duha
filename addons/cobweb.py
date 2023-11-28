bl_info = {
    "name": "Cobweb",
    "author": "Vilem Duha",
    "version": (2, 2),
    "blender": (2, 93, 0),
    "location": "View3D > Add > Mesh > Cobweb",
    "description": "Adds a generative cobweb",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
}

import bmesh
import bpy
import bpy_extras
import gpu
import math
import mathutils
import random
import time
from bpy.props import *
from bpy_extras import object_utils, mesh_utils
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader


def testConnectible(obj, v1, v2):
    # ob = bpy.data.objects[obj.name]
    # print(obj.name)
    # print(obj.data)
    # obj.update
    vec = v2.co - v1.co

    v1hit, v1loc, v1norm, v1face_index = obj.closest_point_on_mesh(v1.co)

    # norm = obj.data.polygons[face_index].normal
    # print(v1norm.angle(vec))
    if v1norm.angle(vec) > 1.57:
        return False
    v2hit, v2loc, v2norm, v2face_index = obj.closest_point_on_mesh(v2.co)
    # vec1 = v1.co-v2.co
    # print(v2norm.angle(-vec))
    if v2norm.angle(-vec) > 1.57:
        return False

    hit, loc, norm, face = obj.ray_cast(v1.co + v1norm * 0.001, v2.co - v1.co)
    hitvec = loc - v1.co
    # print(hitvec.length, vec.length)
    return hitvec.length * 1.01 >= vec.length


def testConnectibleConnection(obj, v1, v2):
    # ob = bpy.data.objects[obj.name]
    # print(obj.name)
    # print(obj.data)
    # obj.update
    vec = v2.co - v1.co

    hit, loc, norm, face = obj.ray_cast(v1.co, v2.co - v1.co)
    hitvec = loc - v1.co

    return not hit or hitvec.length * 1.01 >= vec.length


def mindist(v1, testvarray, maxdist):
    mindist = 100000000000000
    minv = None
    for v2 in testvarray:
        vec = v2.co - v1.co
        d = vec.length
        if d < mindist:
            minv = v2
            mindist = d
    return minv


def addhits(self, context, event, ray_max=100000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + (view_vector * ray_max)

    vec = ray_target - ray_origin

    result, hit, normal, face_index, object, matrix = scene.ray_cast(bpy.context.view_layer.depsgraph, ray_origin, vec)

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj = None

    if hit != None:
        # scene.cursor_location = hit
        self.hits.append((hit, normal))
        n = mathutils.Vector((0, 0, 0))
    return False


def createmesh(points):
    s = bpy.context.scene
    mesh = bpy.data.meshes.new("points")

    bm = bmesh.new()
    for v_co, normal in points:
        offset = normal * .005
        rv1 = mathutils.Euler((0, 1, 0))
        rv2 = mathutils.Euler((1, 0, 0))
        rnor = mathutils.Euler(normal)
        offset1 = offset.orthogonal()
        # offset1.rotate(rv1)
        offset2 = offset1.copy()
        offset2.rotate(rnor)
        v = bm.verts.new(v_co)
        v1 = bm.verts.new(v_co + offset1)
        v2 = bm.verts.new(v_co + offset2)
        f = bm.faces.new((v, v1, v2))
        f.select = True
        # v = bm.verts.new(v_co)

    bm.to_mesh(mesh)
    mesh.update()
    name = 'cobweb source points'
    if name in s.collection.objects:
        ob = s.collection.objects[name]
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ao
        ob.data = mesh
    else:
        object_utils.object_data_add(bpy.context, mesh)
    ob = bpy.context.view_layer.objects.active
    ob.location = 0, 0, 0

    ob.name = name
    ob.hide_render = True
    ob.hide_viewport = True


def draw_lines(vertices, indices, color):
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def draw_callback_3d(self, context):
    coords = []
    lines = []
    for i, pp in enumerate(self.hits):
        # print('draw',pp)
        if i > 0:
            d = pp[0] - self.hits[i - 1][0]
            if d.length < .5:
                lines.append([i - 1, i])
        coords.append(pp[0])
    draw_lines(coords, lines, (0.5, 1, 0.5, 1))


class CobwebPaint(bpy.types.Operator):
    """paint cobweb source"""
    bl_idname = "object.cobweb_paint"
    bl_label = "Cobweb paint"
    bl_description = "Paint into the scene and press Enter to finish creating a cobweb"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True  # context.active_object is not None

    def modal(self, context, event):
        context.area.tag_redraw()
        # self.report({'OPERATOR'}, "Select 3 or more points on the floor, Esc exits")
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self.drawing = True
            else:
                self.drawing = False
            # print(dir(event))
            # print(event.value)
        elif event.type == 'MOUSEMOVE':
            if self.drawing:
                addhits(self, context, event)

                return {'RUNNING_MODAL'}
            else:
                return {'PASS_THROUGH'}
        elif event.type in {'RET', 'SPACE'}:
            # self.hits=[]
            # if bpy.context.active_object.name[:6] == 'cobweb':
            #    bpy.ops.ed.undo()
            createmesh(self.hits)
            origmesh = bpy.context.view_layer.objects.active

            dim = origmesh.dimensions
            s = max(dim.x, dim.y, dim.z)
            settings = bpy.context.scene.cobweb_settings

            bpy.ops.object.cobweb_add(pointcount=settings.pointcount,
                                      connections=settings.connections,
                                      radius=settings.radius,
                                      pick_close_tries=settings.pick_close_tries,
                                      condist2=settings.condist2,
                                      subdivision=settings.subdivision,
                                      smooth_iterations=settings.smooth_iterations,
                                      enable_viewport_rendering=settings.enable_viewport_rendering,
                                      add_cloth=settings.add_cloth,
                                      drop_amount=settings.drop_amount)
            # if event.type in { 'RET', 'SPACE'}:
            # bpy.context.scene.objects.unlink(origmesh)
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set(text=None)
            msg = self.bl_label + ' (modal)'

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # self.hits=[]
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set(text=None)
            return {'CANCELLED'}
        else:
            return {'PASS_THROUGH'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # bpy.context.scene.update()
        if context.space_data.type == 'VIEW_3D':
            args = (self, context)
            self.hits = []
            self.drawing = False
            # context.window_manager.modal_handler_add(self)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, args, 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            context.area.header_text_set(text='Paint source points, SPACE/ENTER to confirm, ESC/RIGHTCLICK to cancel')
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def generate_cobweb(pointcount, pick_close_tries, condist2, subdivision1, connections, radius, add_cloth,
                    smooth_iterations, enable_viewport_rendering, drop_amount):
    # pointcount = 100
    # closedist = .5
    # subdivision1 = 20
    # connections = 10

    source_obj = bpy.context.view_layer.objects.active  # Gets the object
    hide = source_obj.hide_viewport
    if hide:
        source_obj.hide_viewport = False
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    me = source_obj.data
    me.calc_loop_triangles()
    # recalculate tessfaces

    tessfaces_select = [f for f in me.loop_triangles if me.polygons[f.polygon_index].select]
    # TODO BRING SELECTION BACK

    # print(pointgroups,tessface_groups)
    points = []
    totarea = 0
    for f in tessfaces_select:
        totarea += f.area
    for f in tessfaces_select:

        ratio = f.area * pointcount / totarea
        minp = math.floor(ratio)
        prob = ratio - minp
        add = random.random() < prob
        if add:
            minp += 1
        if minp > 0:
            points.extend(mesh_utils.triangle_random_points(minp, [f]))
    # pointgroups.append(bpy_extras.mesh_utils.face_random_points(1, tessfaces_select))

    mesh = bpy.data.meshes.new("cobweb")

    bm = bmesh.new()

    tobedone = []

    for v_co in points:
        v = bm.verts.new(v_co)
        # print(v)

        tobedone.append(v)

    do_tries = len(tobedone)
    vdone = []
    print('initial connections')

    num_connections = 0
    falseattempts = 0
    # for a in range(0,5):
    size = len(bm.verts)
    kd = mathutils.kdtree.KDTree(size)

    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)

    kd.balance()
    bm.verts.ensure_lookup_table()
    # Find points within a radius of the 3d curso

    tkd = 0
    tray = 0
    while len(tobedone) > 1 and falseattempts < do_tries:
        v1 = random.choice(tobedone)
        testvlist = []
        t = time.time()

        for a in range(0, pick_close_tries):
            vtest = random.choice(tobedone)
            if vtest != v1:
                testvlist.append(vtest)
        if len(testvlist) > 0:
            v2 = mindist(v1, testvlist, 1)
            '''
            
            closepoints = []
            for (co, index, dist) in kd.find_range(v1.co, condist1):
                if index!=v1.index:
                    cp = bm.verts[index]
                    if len(cp.link_edges) >=2 or len(cp.link_edges)==0:
                        closepoints.append(cp)
            v2 = random.choice(closepoints)
            '''
            tkd += time.time() - t
            t = time.time()
            #

            # v1 = random.choice(tobedone)
            if v2 != v1:
                connectible = testConnectible(source_obj, v1, v2)
                if connectible:
                    vdone.append(v1)
                    vdone.append(v2)
                    tobedone.remove(v1)
                    tobedone.remove(v2)
                    bm.edges.new((v1, v2))
                    num_connections += 1
                else:
                    falseattempts += 1
            tray += time.time() - t
            t = time.time()

    print('times', tkd, tray)

    bm.to_mesh(mesh)
    mesh.update()

    # add the mesh as an object into the scene with this utility module

    object_utils.object_data_add(bpy.context, mesh)
    # fal
    bpy.ops.object.editmode_toggle()

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=subdivision1, smoothness=0)
    '''
    #connections to connections:
    size = len(bm.verts)
    kd = mathutils.kdtree.KDTree(size)

    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)

    kd.balance()
       
    edges = []
    bm.verts.ensure_lookup_table()
    for v1 in bm.verts:
        closepoints = []
        if len(v1.link_edges)==0:
            co_find = v1.co
            for (co, index, dist) in kd.find_range(co_find, closedist*3):
                if index!=v1.index:
                    cp = bm.verts[index]
                    if len(cp.link_edges) >=2:
                        closepoints.append(bm.verts[index])   
            if len(closepoints)>0:     
                v2 = random.choice(closepoints)
                edges.append(bm.edges.new((v1,v2)))
    for e in edges:
        e.select = True
    bpy.ops.mesh.subdivide(number_cuts=3, smoothness=0)
    bpy.ops.mesh.select_all(action='DESELECT')
    '''

    bpy.ops.mesh.select_all(action='DESELECT')
    obj = bpy.context.active_object
    # obj.location = source_obj.location
    # obj.rotation_euler = source_obj.rotation_euler
    # obj.scale = source_obj.scale
    obj.matrix_world = source_obj.matrix_world
    me = bpy.context.active_object.data
    bm = bmesh.from_edit_mesh(me)

    bm.verts.ensure_lookup_table()
    print('connecting')
    t = time.time()

    condist = condist2

    for a in range(0, connections):
        print(a, connections)
        # me = obj.data
        size = len(bm.verts)
        kd = mathutils.kdtree.KDTree(size)

        for i, v in enumerate(bm.verts):
            kd.insert(v.co, i)

        kd.balance()

        edges = []
        for b in range(num_connections):
            v1 = random.choice(bm.verts)

            if len(v1.link_edges) >= 2 or len(v1.link_edges) == 0:
                closepoints = []
                # closedist = .5

                co_find = v1.co
                for (co, index, dist) in kd.find_range(co_find, condist):
                    if index != v1.index:
                        cp = bm.verts[index]
                        if len(cp.link_edges) >= 2 or len(cp.link_edges) == 0:
                            closepoints.append(cp)

                if len(closepoints) > 0:

                    v2 = random.choice(closepoints)
                    if bm.edges.get((v1, v2)) == None and testConnectibleConnection(source_obj, v1, v2):
                        edges.append(bm.edges.new((v1, v2)))

        for e in edges:
            e.select = True
        bpy.ops.mesh.subdivide(number_cuts=3, smoothness=0)
        bpy.ops.mesh.select_all(action='DESELECT')
        bm.verts.ensure_lookup_table()
        # condist *= 1-(1/connections)
    # create pingroup
    pinindices = []
    print('smoothing time ', time.time() - t)
    for v in bm.verts:
        if len(v.link_edges) == 1:
            v.select = True
            pinindices.append(True)
        pinindices.append(False)

    bpy.ops.object.vertex_group_assign_new()

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete_loose(use_edges=False)
    bpy.ops.mesh.select_all(action='DESELECT')

    print('smooth')

    # '''
    if 1:
        for a in range(0, 10):
            bpy.ops.mesh.select_all(action='DESELECT')
            for v in bm.verts:
                # bring verts closest to ends back to ends, to avoid movement towards center too much
                if len(v.link_edges) == 1:
                    e = v.link_edges[0]
                    for v1 in e.verts:
                        if v1 != v:
                            v1.co = v.co
            if a < 4:
                # Gravity effect
                for v in bm.verts:
                    if len(v.link_edges) > 1:
                        v.co.z -= drop_amount * .1
                        v.select = True
            bmesh.update_edit_mesh(me)

            if a < 9:
                bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=int(smooth_iterations / 10))

            else:
                bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=1)
    else:
        for v in bm.verts:
            if len(v.link_edges) > 1:
                v.select = True
        bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=98)
    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me)

    bpy.ops.object.editmode_toggle()
    obj = bpy.context.active_object
    # add cloth
    if add_cloth:
        bpy.ops.object.modifier_add(type='CLOTH')
        bpy.context.object.modifiers["Cloth"].settings.bending_model = 'LINEAR'
        bpy.context.object.modifiers["Cloth"].settings.vertex_group_mass = "Group"
    # make renderable

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    empty = bpy.context.active_object
    # empty.parent = obj
    empty.name = 'cobweb_helper'

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    loc = obj.location.copy()
    loc.y += 10
    empty.location = loc
    empty.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

    empty.hide_viewport = True
    bpy.ops.object.modifier_add(type='SCREW')
    bpy.context.object.modifiers["Screw"].object = empty
    angle = 2 * math.pi * radius / (10 * 2 * math.pi)
    bpy.context.object.modifiers["Screw"].angle = angle
    bpy.context.object.modifiers["Screw"].angle = angle
    bpy.context.object.modifiers["Screw"].steps = 2
    bpy.context.object.modifiers["Screw"].render_steps = 2
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = radius
    if not enable_viewport_rendering:
        bpy.context.object.modifiers["Screw"].show_viewport = False
        bpy.context.object.modifiers["Solidify"].show_viewport = False

    if bpy.data.materials.get('cobweb') == None:
        m = bpy.data.materials.new('cobweb')
        m.use_nodes = True
        nt = m.node_tree
        glossy = nt.nodes.new(type='ShaderNodeBsdfGlossy')
        glossy.location = (-400, 300)
        translucent = nt.nodes.new(type='ShaderNodeBsdfTranslucent')
        translucent.location = (-400, 200)
        transparent = nt.nodes.new(type='ShaderNodeBsdfTransparent')
        transparent.location = (-400, 100)

        mix1 = nt.nodes.new(type='ShaderNodeMixShader')
        mix1.location = (-200, 300)
        mix2 = nt.nodes.new(type='ShaderNodeMixShader')
        mix2.location = (100, 300)

        material_output = nt.nodes.get('Material Output')
        diffuse = nt.nodes.get('Principled BSDF')
        print(diffuse)
        nt.nodes.remove(diffuse)
        nt.links.clear()
        nt.links.new(mix1.inputs[1], glossy.outputs[0])
        nt.links.new(mix1.inputs[2], translucent.outputs[0])
        nt.links.new(mix2.inputs[1], mix1.outputs[0])
        nt.links.new(mix2.inputs[2], transparent.outputs[0])
        nt.links.new(material_output.inputs[0], mix2.outputs[0])

    m = bpy.data.materials.get('cobweb')
    bpy.ops.object.material_slot_add()
    obj.material_slots[0].material = m
    if hide:
        source_obj.hide_viewport = True
    # delete unused cobweb helpers:
    s = bpy.context.scene
    helpers = []
    usedhelpers = []
    for ob in s.collection.objects:
        if ob.name[:6] == 'cobweb':
            if ob.modifiers.get('Screw') != None:
                usedhelpers.append(ob.modifiers['Screw'].object)
        if ob.name[:13] == 'cobweb_helper':
            # print(ob.name)
            helpers.append(ob)
    for h in helpers:
        # print(h)
        if not h in usedhelpers:
            # print('remove' , h.name)
            s.collection.objects.unlink(h)


'''
def finish_cobweb(rtype,radius):
    obj = bpy.context.active_object
    if rtype =='CURVE':
        bpy.ops.object.convert(target='CURVE')
        bpy.context.object.data.fill_mode = 'FULL'
        bpy.context.object.data.bevel_resolution = 1
        bpy.context.object.data.bevel_depth = radius
    else:
        cw = bpy.context.active_object
        if len(cw.modifiers)==0:
            bpy.ops.object.modifier_add(type='CLOTH')
            bpy.context.object.modifiers["Cloth"].settings.use_pin_cloth = True
            bpy.context.object.modifiers["Cloth"].settings.vertex_group_mass = "Group"
        loc = cw.location.copy()
        loc.y+=10
        bpy.ops.object.empty_add(type='PLAIN_AXES',  location=loc)
        empty = bpy.context.active_object
        empty.parent = cw
        cw.select = True
        bpy.context.scene.objects.active = cw
        bpy.ops.object.modifier_add(type='SCREW')
        bpy.context.object.modifiers["Screw"].object = empty
        angle = 2*math.pi*radius / (10*2*math.pi)
        bpy.context.object.modifiers["Screw"].angle = angle
        bpy.context.object.modifiers["Screw"].steps = 2
        bpy.context.object.modifiers["Screw"].render_steps = 2
        bpy.ops.object.modifier_add(type='SOLIDIFY')
        bpy.context.object.modifiers["Solidify"].thickness = radius

'''


class RegenerateCobweb(bpy.types.Operator):
    """Regenerate cobweb"""
    bl_idname = "object.cobweb_regenerate_painted"
    bl_label = "Regenerate last painted cobweb"
    bl_description = "Find last painted cobweb and regenerate it."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = bpy.context.scene
        bpy.context.view_layer.update()
        ob = bpy.context.active_object
        if ob.name[:6] == 'cobweb':
            bpy.context.collection.objects.unlink(ob)
            sob = bpy.context.collection.objects['cobweb source points']
            sob.select_set(True)
            bpy.context.view_layer.objects.active = sob

            settings = bpy.context.scene.cobweb_settings

            bpy.ops.object.cobweb_add(pointcount=settings.pointcount,
                                      connections=settings.connections,
                                      radius=settings.radius,
                                      pick_close_tries=settings.pick_close_tries,
                                      condist2=settings.condist2,
                                      subdivision=settings.subdivision,
                                      smooth_iterations=settings.smooth_iterations,
                                      enable_viewport_rendering=settings.enable_viewport_rendering,
                                      add_cloth=settings.add_cloth,
                                      drop_amount=settings.drop_amount)

        return {'FINISHED'}


class AddCobweb(bpy.types.Operator):
    """Add a cobweb"""
    bl_idname = "object.cobweb_add"
    bl_label = "Add cobweb"
    bl_description = "Create a new cobweb from the selected faces of the active mesh."
    bl_options = {'REGISTER', 'UNDO'}

    pointcount = 100
    closedist = .5
    subdivision1 = 20
    connections = 10
    radius = 0.001

    pointcount: IntProperty(
        name="init point count",
        description="number of seedpoints on each face",
        min=1, max=50000,
        default=150,
    )
    pick_close_tries: IntProperty(
        name="shorter connection attempts",
        description="first round connections try to get closer this amount of times",
        min=1, max=100,
        default=10,
    )
    condist2: FloatProperty(
        name="secondary connection distance",
        description="how far strands can be connected",
        min=0.00001, max=100.0,
        default=0.2,
    )
    subdivision: IntProperty(
        name="strand subdivision",
        description="subdivision amount during modelling",
        min=1, max=100,
        default=8,
    )
    connections: IntProperty(
        name="connections per strand",
        description="number of connections(multiplied with pointcount!)",
        min=1, max=300,
        default=5,
    )
    drop_amount: FloatProperty(
        name="Gravity",
        description="",
        min=0.000001, max=1.00000,
        default=0.01,
        precision=6,
    )
    smooth_iterations: IntProperty(
        name="smooth steps",
        description="",
        min=1, max=500,
        default=200,
    )
    radius: FloatProperty(
        name="strings radius",
        description="",
        min=0.000001, max=1.00000,
        default=0.0003,
        precision=6,
    )
    add_cloth: BoolProperty(
        name="add simulation",
        description="add cloth simulation for animation, more hanginess or tearing.",
        default=False,
    )
    enable_viewport_rendering: BoolProperty(
        name="enable viewport rendering",
        description="enable meshing modifiers in viewport(otherwise only in render).",
        default=False,
    )

    def execute(self, context):
        bpy.context.view_layer.update()
        if bpy.context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        generate_cobweb(self.pointcount,
                        self.pick_close_tries,
                        self.condist2,
                        self.subdivision1,
                        self.connections,
                        self.radius,
                        self.add_cloth,
                        self.smooth_iterations,
                        self.enable_viewport_rendering,
                        self.drop_amount
                        )
        return {'FINISHED'}

    def invoke(self, context, event):
        settings = bpy.context.scene.cobweb_settings

        self.pointcount = settings.pointcount
        self.connections = settings.connections
        self.radius = settings.radius
        self.pick_close_tries = settings.pick_close_tries
        self.condist2 = settings.condist2
        self.subdivision = settings.subdivision
        self.smooth_iterations = settings.smooth_iterations
        self.enable_viewport_rendering = settings.enable_viewport_rendering
        self.add_cloth = settings.add_cloth
        self.drop_amount = settings.drop_amount
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        # col = layout.column()
        # col.label(text="Custom Interface!")

        # row = col.row()
        layout.prop(self, "pointcount")
        layout.prop(self, "pick_close_tries")
        layout.prop(self, "condist2")
        layout.prop(self, "connections")
        layout.prop(self, "subdivision")
        layout.prop(self, "drop_amount")
        layout.prop(self, "smooth_iterations")
        layout.prop(self, "radius")
        layout.prop(self, "enable_viewport_rendering")
        layout.prop(self, "add_cloth")
        # col.prop(self, "my_bool")

        # col.prop(self, "my_string")


def menu_func(self, context):
    o = self.layout.operator(AddCobweb.bl_idname, icon='MESH_CUBE')
    o.pointcount = 100
    o.connections = 5


class CobwebSettings(bpy.types.PropertyGroup):
    pointcount: IntProperty(
        name="init point count",
        description="number of seedpoints on each face",
        min=1, max=50000,
        default=150,
    )
    pick_close_tries: IntProperty(
        name="shorter connection attempts",
        description="first round connections try to get closer this amount of times",
        min=1, max=100,
        default=1,
    )
    condist2: FloatProperty(
        name="secondary connection distance",
        description="how far strands can be connected",
        min=0.00001, max=100.0,
        default=0.05,
    )
    subdivision: IntProperty(
        name="strand subdivision",
        description="subdivision amount during modelling",
        min=1, max=100,
        default=12,
    )
    connections: IntProperty(
        name="connections per strand",
        description="number of connections(multiplied with pointcount!)",
        min=1, max=300,
        default=5,
    )
    drop_amount: FloatProperty(
        name="Gravity",
        description="",
        min=0.000001, max=1.00000,
        default=0.01,
        precision=6,
    )
    smooth_iterations: IntProperty(
        name="smooth steps",
        description="",
        min=1, max=500,
        default=200,
    )
    radius: FloatProperty(
        name="strings radius",
        description="",
        min=0.000001, max=1.00000,
        default=0.0003,
        precision=6,
    )
    add_cloth: BoolProperty(
        name="add simulation",
        description="add cloth simulation for animation, more hanginess or tearing.",
        default=False,
    )
    enable_viewport_rendering: BoolProperty(
        name="enable viewport rendering",
        description="enable meshing modifiers in viewport(otherwise only in render).",
        default=False,
    )


class COBWEB_Panel(bpy.types.Panel):
    """Cobweb panel"""
    bl_label = "Cob webs"
    bl_idname = "WORLD_PT_COBWEB"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Create"

    # bl_context = "object"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        # print(dir(layout))
        s = bpy.context.scene

        cs = s.cobweb_settings

        # if br:
        # cutter preset
        # layout.operator("object.cobweb_add", text="From face selection")
        # layout.separator()
        # layout.separator()
        layout.operator("object.cobweb_paint", text="Paint")
        layout.operator("object.cobweb_regenerate_painted", text="Regenerate last painted")

        # row = col.row()
        layout.separator()
        layout.separator()
        layout.prop(cs, "pointcount")
        layout.prop(cs, "pick_close_tries")
        layout.prop(cs, "condist2")
        layout.prop(cs, "connections")
        layout.prop(cs, "drop_amount")
        layout.prop(cs, "subdivision")
        layout.prop(cs, "smooth_iterations")
        layout.prop(cs, "radius")
        layout.prop(cs, "enable_viewport_rendering")
        layout.prop(cs, "add_cloth")


def register():
    bpy.utils.register_class(AddCobweb)
    bpy.utils.register_class(CobwebPaint)
    bpy.utils.register_class(RegenerateCobweb)
    bpy.utils.register_class(CobwebSettings)
    bpy.utils.register_class(COBWEB_Panel)
    # bpy.utils.register_class(FinishCobweb)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

    s = bpy.types.Scene
    s.cobweb_settings = bpy.props.PointerProperty(type=CobwebSettings)


def unregister():
    bpy.utils.unregister_class(AddCobweb)
    bpy.utils.unregister_class(CobwebPaint)
    bpy.utils.unregister_class(RegenerateCobweb)
    bpy.utils.unregister_class(CobwebSettings)
    bpy.utils.unregister_class(COBWEB_Panel)
    # bpy.utils.unregister_class(FinishCobweb)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    s = bpy.types.Scene
    del s.cobweb_settings


if __name__ == "__main__":
    register()

    # test call
    # bpy.ops.mesh.primitive_box_add()
