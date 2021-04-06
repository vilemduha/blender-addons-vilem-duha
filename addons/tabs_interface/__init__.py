bl_info = {
    "name": "Tabs interface",
    "author": "Vilem Duha",
    "version": (1, 6),
    "blender": (2, 80, 0),
    "location": "Everywhere(almost)",
    "description": "Blender tabbed.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "All"}

import bpy, os, math, string, random, time
import inspect
import bpy, bpy_types
from bpy.app.handlers import persistent
from tabs_interface import panel_order
import copy  # for deepcopy dicts
import inspect

DEBUG = True

_update_tabs = []
# _update_pdata = []
_update_categories = []
_extra_activations = []
USE_DEFAULT_POLL = False  # Pie menu editor compatibility
_counter = 0

IGNORE_SPACES = ('TOPBAR', 'INFO', 'PREFERENCES')
IGNORE_REGIONS = ('HEADER', 'NAVIGATION_BAR', 'TOOLS')


@classmethod
def noPoll(cls, context):
    return False


@classmethod
def yesPoll(cls, context):
    return True


@classmethod
def smartPoll(cls, context):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    polled = cls.opoll(context)

    if USE_DEFAULT_POLL:
        return polled
    # print( ' smart poll', cls.realID)
    item = bpy.context.scene.panelData.get(cls.realID)
    # if item == None:
    #    _update_pdata.append(cls.realID)
    #    return polled
    if prefs.enable_disabling:
        if prefs.disable_PROPERTIES and context.area.type == 'PROPERTIES':
            return polled
        if prefs.disable_TOOLBAR and context.region.type == 'TOOLS':
            return polled
        if prefs.disable_UI and context.region.type == 'UI':
            return polled
    if item == None:
        return False

    if hasattr(cls, 'bl_parent_id'):
        # TODO the parent should be written on initialization
        parent = eval('bpy.types.' + cls.bl_parent_id)
        polled = parent.poll(context) and polled

    return ((item.activated and item.activated_category) or item.pin) and polled and item.show and (
        prefs.original_panels)


def drawHeaderPin(cls, context):
    layout = cls.layout
    if hasattr(bpy.context.scene, 'panelData') and bpy.context.scene.panelData.get(cls.realID) is not None:
        pd = bpy.context.scene.panelData[cls.realID]
        if pd.pin:
            icon = 'PINNED'
        else:
            icon = 'UNPINNED'
        layout.prop(bpy.context.scene.panelData[cls.realID], 'pin', icon_only=True, icon=icon, emboss=False)
    if hasattr(cls, 'orig_draw_header'):
        cls.orig_draw_header(context)


def processPanelForTabs(panel):
    if not hasattr(panel, 'realID'):
        panel.had_category = False
        panel.realID = panel.bl_rna.identifier
        if hasattr(panel, 'bl_category'):
            panel.had_category = True
            # if panel.bl_category == 'Archimesh':
            # print ('ARCHISHIT')
            if not hasattr(panel, 'orig_category'):
                panel.orig_category = panel.bl_category
            panel.bl_category = 'Tools'
        # elif panel.bl_space_type == 'VIEW_3D' and panel.bl_region_type == 'TOOLS':
        #     panel.bl_category = 'Tools'
        #     panel.orig_category = 'Misc'
        else:
            panel.bl_category = 'Tools'
            panel.orig_category = 'Tools'

            #
        if not hasattr(panel, 'opoll'):
            if not hasattr(panel, 'poll'):
                panel.poll = yesPoll
            panel.opoll = panel.poll
            panel.poll = smartPoll

        if hasattr(panel, 'draw_header'):
            panel.orig_draw_header = panel.draw_header

        panel.draw_header = drawHeaderPin

        bpy.utils.unregister_class(panel)
        if hasattr(panel, 'bl_options'):
            if 'DEFAULT_CLOSED' in panel.bl_options:
                panel.bl_options.remove('DEFAULT_CLOSED')
        try:
            bpy.utils.register_class(panel)
        except Exception as e:
            print(e)


def fixOriginalPanel(tp_name):
    ''' brings panel to state before tabs'''

    tp = getattr(bpy.types, tp_name)
    bpy.utils.unregister_class(tp)
    if hasattr(tp, 'opoll'):
        tp.poll = tp.opoll
        del tp.opoll
    if hasattr(tp, 'orig_draw_header'):
        tp.draw_header = tp.orig_draw_header
        del tp.orig_draw_header
    else:
        del tp.draw_header
    if hasattr(tp, 'orig_category'):
        tp.bl_category = tp.orig_category
        if not tp.had_category:
            del tp.bl_category

        del tp.orig_category
    if hasattr(tp, 'realID'):
        del tp.realID
    bpy.utils.register_class(tp)
    # s = bpy.context.scene
    # del bpy.types.Scene.panelIDs[tp]


DEFAULT_PANEL_PROPS = ['__class__', '__contains__', '__delattr__', '__delitem__', '__dict__', '__dir__', '__doc__',
                       '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__',
                       '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__',
                       '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__slots__', '__str__',
                       '__subclasshook__', '__weakref__', '_dyn_ui_initialize', 'append', 'as_pointer', 'bl_category',
                       'bl_context', 'bl_description', 'bl_idname', 'bl_label', 'bl_options', 'bl_region_type',
                       'bl_rna', 'bl_space_type', 'COMPAT_ENGINES', 'draw', 'draw_header', 'driver_add',
                       'driver_remove', 'get', 'id_data', 'is_property_hidden', 'is_property_readonly',
                       'is_property_set', 'items', 'keyframe_delete', 'keyframe_insert', 'keys', 'orig_category',
                       'path_from_id', 'path_resolve', 'poll', 'opoll', 'prepend', 'property_unset', 'remove',
                       'type_recast', 'values']

NOCOPY_PANEL_PROPS = ['__class__', '__contains__', '__delattr__', '__delitem__', '__dict__', '__dir__', '__doc__',
                      '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__',
                      '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__',
                      '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__slots__', '__str__',
                      '__subclasshook__', '__weakref__', '_dyn_ui_initialize', 'append', 'as_pointer', 'bl_category',
                      'bl_context', 'bl_description', 'bl_idname', 'bl_label', 'bl_options', 'bl_region_type', 'bl_rna',
                      'bl_space_type', 'COMPAT_ENGINES', 'driver_add', 'driver_remove', 'get', 'id_data',
                      'is_property_hidden', 'is_property_readonly', 'is_property_set', 'items', 'keyframe_delete',
                      'keyframe_insert', 'keys', 'orig_category', 'path_from_id', 'path_resolve', 'poll', 'prepend',
                      'property_unset', 'remove', 'type_recast', 'values']


class tabSetups(bpy.types.PropertyGroup):
    '''stores data for tabs'''
    tabsenum: bpy.props.EnumProperty(name='Post processor',
                                     items=[('tabID', 'tabb', 'tabbiiiieeee')])
    show: bpy.props.BoolProperty(name="show", default=True)  # , update = updatePin)
    active_tab: bpy.props.StringProperty(name="Active tab", default="Machine")
    active_category: bpy.props.StringProperty(name="Active category", default="None")


class tabCategoryData(bpy.types.PropertyGroup):
    # ''stores data for categories''
    show: bpy.props.BoolProperty(name="show", default=True)


class panelData(bpy.types.PropertyGroup):
    '''stores data for panels'''

    pin: bpy.props.BoolProperty(name="pin", default=False)  # , update = updatePin)
    show: bpy.props.BoolProperty(name="show", default=True)
    activated: bpy.props.BoolProperty(name="activated", default=False)
    activated_category: bpy.props.BoolProperty(name="activated category", default=True)
    category: bpy.props.StringProperty(name="category", default='Tools')
    parent: bpy.props.StringProperty(name="parent", default='')
    space: bpy.props.StringProperty(name="space", default="")
    region: bpy.props.StringProperty(name="region", default="")
    context: bpy.props.StringProperty(name="context", default="")


def getlabel(panel):
    return panel.bl_label


DONT_USE = ['DATA_PT_modifiers', 'OBJECT_PT_constraints', 'BONE_PT_constraints', '__dir__']


def getPanelIDs():
    ''' rebuilds panel ID's dictionary '''
    s = bpy.types.Scene
    if not hasattr(s, 'panelIDs'):
        s.panelIDs = {}

    newIDs = []
    panel_tp = bpy.types.Panel
    typedir = dir(bpy.types)
    btypeslen = len(typedir)

    for tp_name in typedir:
        if tp_name.find('_tabs') == -1 and tp_name not in DONT_USE:  # and tp_name.find('NODE_PT_category_')==-1
            tp = getattr(bpy.types, tp_name)
            # if hasattr(tp, 'bl_region_type'):
            #     print('region type', tp.bl_region_type, tp.bl_space_type)
            # print(' co to je tp?')
            # print(tp)
            # print(dir(tp))
            if tp == panel_tp or not inspect.isclass(tp) or \
                    not issubclass(tp, panel_tp) or tp.bl_space_type == 'PREFERENCES' or \
                    hasattr(tp, 'bl_region_type') and tp.bl_region_type == 'HEADER':
                # if hasattr(tp, 'bl_region_type'):
                #     print('ignored region type', tp.bl_region_type, tp.bl_space_type)
                continue

            # if not (hasattr(tp, 'bl_options') and 'HIDE_HEADER' in tp.bl_options):
            if s.panelIDs.get(tp.bl_rna.identifier) == None:
                newIDs.append(tp)
            s.panelIDs[tp.bl_rna.identifier] = tp
            if tp.is_registered != True:
                print('not registered', tp.bl_label)
            # else:
            #    print( 'hide header ###########################', tp.bl_label, tp.bl_rna.identifier)
        # else:
        # print('SOMETHING ELSE            ',tp_name)

    # print(tp)

    return newIDs


def buildTabDir(panels):
    if DEBUG:
        print('rebuild tabs ', len(panels))
    # disabled reading from scene,
    if hasattr(bpy.types.Scene, 'panelSpaces'):
        spaces = bpy.types.Scene.panelSpaces
    else:
        spaces = copy.deepcopy(panel_order.spaces)
        for sname in spaces:
            if sname not in IGNORE_SPACES:
                space = spaces[sname]

                for rname in space:
                    if rname not in IGNORE_REGIONS and not (rname == 'WINDOW' and sname == 'VIEW_3D'):
                        nregion = []
                        region = space[rname]

                        for p in region:
                            if type(p) == str:
                                panel = getattr(bpy_types.bpy_types, p, None)
                                if panel:
                                    processPanelForTabs(panel)
                                    nregion.append(panel)
                                else:
                                    if DEBUG:
                                        print('non existing panel ' + str(p))
                                    # nregion.append(panel)
                        space[rname] = nregion

    # print('called buildtabdir')
    for panel in panels:

        if hasattr(panel, 'bl_space_type'):
            st = panel.bl_space_type
            if st not in IGNORE_SPACES:
                # print((st))
                # if panel.bl_label == 'Collision':
                # print('collision in tabdir')
                if spaces.get(st) == None:
                    spaces[st] = {}  # [panel]

                if hasattr(panel, 'bl_region_type'):

                    rt = panel.bl_region_type
                    if rt not in IGNORE_REGIONS and not (rt == 'WINDOW' and st == 'VIEW_3D'):
                        # print(rt)
                        if spaces[st].get(rt) == None:
                            spaces[st][rt] = []

                        # if not hasattr(panel, 'realID'):
                        processPanelForTabs(panel)
                        # if len(panels)<10:
                        #    print('newly found panel' , panel)
                        if panel not in spaces[st][rt]:
                            spaces[st][rt].append(panel)
                            # print(panel)
                        # print(panel.bl_rna.identifier)
    for sname in spaces:
        space = spaces[sname]
        for rname in space:
            region = space[rname]
            for p in region:
                # print(p)
                # print(p.bl_rna.identifier , p.is_registered)
                if not p.is_registered:
                    print('non registered', p)
                    region.remove(p)
    return spaces


def updatePanels():
    newIDs = getPanelIDs()  # bpy.types.Scene.panels =
    bpy.types.Scene.panelSpaces = buildTabDir(newIDs)
    createSceneTabData()


def getPanels(getspace, getregion):
    if not hasattr(bpy.types.Scene, 'panelIDs'):
        updatePanels()
    panels = bpy.types.Scene.panelSpaces[getspace][getregion]
    # print(getspace,getregion,len(panels))
    return panels


def drawEnable(self, context):
    layout = self.layout
    row = layout.row()
    row.label(text='Enable:')


def layoutActive(self, context):
    layout = self.layout
    layout.active = True
    layout.enabled = True
    # layout.label('\n\n\n\n\n\n\n\n\n')
    # for a in range(0,90):
    #    r = layout.separator()


def layoutSeparator(self, context):
    layout = self.layout
    layout.separator()


class CarryLayout:
    def __init__(self, layout):
        self.layout = layout


def drawNone(self, context):
    pass;


def tabRow(layout):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    row = layout.row(align=prefs.fixed_width)  # not prefs.fixed_width)
    if not prefs.fixed_width:
        row.scale_y = prefs.scale_y
    if not prefs.fixed_width:
        row.alignment = 'LEFT'
    return row


def nextSplit(regwidth=100, width=None, ratio=None, last=0):  # 6 11 27
    if width != None:
        restw = regwidth - (regwidth * last)
        if width > 0:
            neww = regwidth * last + width
            nextsplit = width / restw

        else:
            neww = regwidth - width
            nextsplit = 1 - (-width / regwidth) / (1 - last)
            # print(-width/regwidth, 1-last, nextsplit)
        newtotalsplit = neww / regwidth
    if ratio != None:
        if last < ratio:
            nextsplit = (ratio - last) / (1 - last)
            newtotalsplit = ratio
        else:
            nextsplit = 0
            newtotalsplit = last
            # print('wrong split')
    return nextsplit, newtotalsplit


def getApproximateFontStringWidth(st):
    size = 10
    for s in st:
        if s in 'i|':
            size += 2
        elif s in ' ':
            size += 4
        elif s in 'sfrt':
            size += 5
        elif s in 'ceghkou':
            size += 6
        elif s in 'PadnBCST3E':
            size += 7
        elif s in 'GMODVXYZ':
            size += 8
        elif s in 'w':
            size += 9
        elif s in 'm':
            size += 10
        else:
            size += 7
    # print(size)
    return size  # Convert to picas


def drawTabsLayout(self, context, layout, tabpanel=None, operator_name='wm.activate_panel', texts=[], ids=[], tdata=[],
                   active='', enable_hiding=False):  # tdata=[],
    '''Creates and draws actual layout of tabs'''
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    w = context.region.width
    margin = 18
    if prefs.box:
        margin += 10
    iconwidth = 20
    oplist = []

    if prefs.box:
        layout = layout.box()
    layout = layout.column(align=True)
    # layout.prop(prefs,'hiding' , icon_only = True, icon='RESTRICT_VIEW_OFF')
    '''
    if icons == []:
        for t in texts:
            icons.append('NONE')
    '''
    # bpy.props.BoolProperty(name="show", default=True)#, update = updatePin)
    restpercent = 1
    # COLLAPSEMENU

    if not prefs.fixed_width:  # variable width layout <3
        baserest = w - margin
        restspace = baserest

        tw = 0
        splitalign = True
        row = tabRow(layout)
        split = row

        rows = 0
        i = 0
        lastsplit = None
        for t, id in zip(texts, ids):

            last_tw = tw
            if prefs.emboss and restspace != baserest:
                drawtext = '| ' + t
            else:
                drawtext = t
            tw = getApproximateFontStringWidth(drawtext)
            if enable_hiding and prefs.hiding: tw += iconwidth
            if i == 0 and tabpanel != None and prefs.enable_folding:
                tw += iconwidth
                split.prop(tabpanel, 'show', icon_only=True, icon='DOWNARROW_HLT', emboss=False)

            if context.space_data.type == 'VIEW_3D' and context.region.type == 'TOOLS':  # TOOLBAR draws differnt buttons...
                tw += 10

            if enable_hiding and not prefs.hiding and not tdata[i].show:
                tw = 0

            oldrestspace = restspace
            restspace = restspace - tw
            if restspace > 0:

                split = split.split(factor=tw / oldrestspace, align=splitalign)

            else:
                drawtext = t
                tw = getApproximateFontStringWidth(drawtext)
                if rows == 0 and enable_hiding and prefs.show_hiding_icon:  # draw hiding mode icon here
                    if prefs.hiding:
                        tw += iconwidth
                if context.space_data.type == 'VIEW_3D' and context.region.type == 'TOOLS':  # TOOLBAR draws differnt buttons...
                    tw += 10  # tw +=15
                rows += 1
                oldrestspace = baserest
                restspace = baserest - tw
                row = tabRow(layout)
                split = row.split(factor=tw / oldrestspace, align=splitalign)

            if enable_hiding and prefs.hiding:
                split.prop(tdata[i], 'show', text=drawtext)
                oplist.append(None)
            else:
                if not enable_hiding or tdata[i].show:

                    if active[i]:
                        op = split.operator(operator_name, text=drawtext, emboss=prefs.emboss)
                    else:
                        op = split.operator(operator_name, text=drawtext, emboss=not prefs.emboss)
                    oplist.append(op)
                else:
                    oplist.append(None)

            i += 1
            if rows == 0 and enable_hiding:
                lastsplit = split
                firstrow = row
                lastsplit_restspace = restspace
        if lastsplit != None:
            # split = lastsplit
            # if lastsplit_restspace-iconwidth>0:
            # split = lastsplit.split( factor = (lastsplit_restspace - iconwidth)/lastsplit_restspace, align = False)
            # split = split.split()
            if prefs.show_hiding_icon:
                if prefs.hiding:
                    icon = 'HIDE_ON'
                else:
                    icon = 'HIDE_OFF'
                firstrow.prop(prefs, 'hiding', icon_only=True, icon=icon, emboss=not prefs.emboss)

    else:  # GRID  layout
        w = w - margin
        wtabcount = math.floor(w / 80)
        if wtabcount == 0:
            wtabcount = 1
        if prefs.fixed_columns:

            space = context.area.type

            if space == 'PROPERTIES':
                wtabcount = prefs.columns_properties

                # print(self.bl_context)
                if self.bl_context == 'modifier' or self.bl_context == 'constraint' or self.bl_context == 'bone_constraint':
                    wtabcount = prefs.columns_modifiers
            else:
                wtabcount = prefs.columns_rest
        ti = 0
        rows = 0
        row = tabRow(layout)

        lastsplit = 0
        # hiding
        i = 0

        for t, id in zip(texts, ids):
            if tabpanel != None and i == 0 and prefs.enable_folding:
                ratio, lastsplit = nextSplit(regwidth=w, width=iconwidth, last=0)
                split = row.split(factor=ratio, align=True)

                split.prop(tabpanel, 'show', icon_only=True, icon='DOWNARROW_HLT', emboss=False)
                row = split.split(align=True)

            if (enable_hiding and prefs.hiding) or (not enable_hiding or tdata[i].show):
                # nextSplit( regwidth = 100,width = none, percent = None, lasttotalsplit = 0)

                splitratio = (ti + 1) / (wtabcount)
                if splitratio == 1 and rows == 0 and enable_hiding:
                    ratio, lastsplit = nextSplit(regwidth=w, width=-iconwidth, last=lastsplit)
                else:
                    ratio, lastsplit = nextSplit(regwidth=w, ratio=splitratio, last=lastsplit)
                # split = row

                if ratio == 1:
                    split = row
                else:
                    split = row.split(factor=ratio, align=True)

                drawn = False

                if enable_hiding and prefs.hiding:
                    split.prop(tdata[i], 'show', text=t)
                    drawn = True
                else:
                    if not enable_hiding or tdata[i].show:

                        if active[i]:
                            op = split.operator(operator_name, text=t, icon='NONE', emboss=prefs.emboss)
                        else:
                            op = split.operator(operator_name, text=t, icon='NONE', emboss=not prefs.emboss)
                        oplist.append(op)
                        drawn = True
                if ratio != 1:
                    row = split.split(align=True)
                ti += 1
            else:
                oplist.append(None)
            i += 1
            if ti == wtabcount or i == len(texts):

                if enable_hiding and rows == 0:
                    if ti != wtabcount:  # this doesn't work, it's single tab eye drawing. not sure why!!!
                        # print('last eye')
                        ratio, lastsplit = nextSplit(regwidth=w, width=-iconwidth, last=lastsplit)
                        # print(ratio, lastsplit)
                        split = row.split(factor=ratio, align=True)
                        row = split.split(align=True)
                    if prefs.show_hiding_icon:
                        if prefs.hiding:
                            icon = 'HIDE_ON'
                        else:
                            icon = 'HIDE_OFF'
                        row.prop(prefs, 'hiding', icon_only=True, icon=icon, emboss=not prefs.emboss)
                ti = 0
                rows += 1
                lastsplit = 0
                row = tabRow(layout)

        if ti != 0:
            while ti < wtabcount:
                row.label(text='')
                ti += 1
    return oplist


def drawUpDown(self, context, tabID):
    layout = self.layout
    s = bpy.context.scene
    # r = bpy.context.region
    tabpanel_data = s.panelTabData.get(tabID)
    active_tab = tabpanel_data.active_tab
    op = layout.operator("wm.panel_up", text='up', emboss=True)
    op.panel_id = active_tab
    op.tabpanel_id = tabID
    op = layout.operator("wm.panel_down", text='down', emboss=True)
    op.panel_id = active_tab
    op.tabpanel_id = tabID


def mySeparator(layout):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences

    if not prefs.box:
        layout.separator()
    if prefs.emboss and not prefs.box:
        b = layout.box()
        b.scale_y = 0


def drawFoldHeader(self, context, tabpanel_data):
    layout = self.layout
    row = layout.row()
    if tabpanel_data.show:
        icon = 'DOWNARROW_HLT'
    else:
        icon = 'RIGHTARROW'
    row.prop(tabpanel_data, 'show', icon_only=True, icon=icon, emboss=False)
    row.label(text=self.bl_label)


def drawTabs(self, context, plist, tabID):
    space = context.space_data.type
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    s = bpy.context.scene
    # r = bpy.context.region
    if not hasattr(s, 'panelTabData'):
        return []
    tabpanel_data = s.panelTabData.get(tabID)
    panel_data = s.panelData
    if tabpanel_data == None:
        _update_tabs.append(self)
        return []

    if prefs.reorder_panels:
        drawUpDown(self, context, tabID)
    emboss = prefs.emboss

    # print('au')
    draw_panels = []
    categories = {}
    categories_list = []  # this because it can be sorted, not like dict.

    active_tab = tabpanel_data.active_tab  #
    active_category = tabpanel_data.active_category
    hasactivetab = False
    hasactivecategory = False

    if not tabpanel_data.show:
        drawFoldHeader(self, context, tabpanel_data)

    top_panel = None
    for p in plist:
        pdata = panel_data[p.realID]

        if hasattr(p, 'bl_options'):
            if 'HIDE_HEADER' in p.bl_options and not (
                    p.bl_region_type == 'TOOLS' and p.bl_space_type == 'VIEW_3D'):  # further exceptions only for GroupPro addon :(
                # print( ' extra draw', p)
                top_panel = p  # draw_panels.append(p)
                plist.remove(p)

    for p in plist:
        if hasattr(p,
                   'bl_category'):  # and not (p.bl_region_type == 'UI' and p.bl_space_type == 'VIEW_3D'):#additional checks for Archimesh only!
            if categories.get(p.orig_category) == None:
                categories[p.orig_category] = [p]
                categories_list.append(p.orig_category)
            else:
                categories[p.orig_category].append(p)
        if tabpanel_data.active_tab == p.realID:
            hasactivetab = True

    for p in plist:
        pdata = panel_data[p.realID]
        if p not in draw_panels and pdata.pin or (
                pdata.activated and (len(categories) == 1 or p.orig_category == active_category)):
            draw_panels.append(p)

    if len(categories) > 0:
        # print('hascategories')
        catorder = panel_order.categories

        sorted_categories = []
        cdata = []
        categories_ok = True
        for c in categories:
            if s.categories.get(c) == None:
                _update_tabs.append(self)
                print('categories problem ', categories)
                categories_ok = False
        if not categories_ok:
            return []

        for c1 in catorder:
            for c in categories:
                if c == c1:
                    sorted_categories.append(c)

                    cdata.append(s.categories[c])
        for c in categories:
            if c not in sorted_categories:
                sorted_categories.append(c)
                cdata.append(s.categories[c])
        for c in categories:
            if c == active_category:
                hasactivecategory = True

        if not hasactivecategory:
            active_category = sorted_categories[0]
        active = []
        for cname in sorted_categories:
            if cname == active_category:
                active.append(True)
            else:
                active.append(False)

    if top_panel != None:
        top_panel.draw(self, context)

    preview = None

    layout = self.layout
    maincol = layout.column(align=True)

    if len(categories) > 1:  # EVIL TOOL PANELS!
        # row=tabRow(maincol)
        if len(categories) > 1:
            if tabpanel_data.show:
                catops = drawTabsLayout(self, context, maincol, tabpanel=tabpanel_data,
                                        operator_name='wm.activate_category', texts=sorted_categories,
                                        ids=sorted_categories, tdata=cdata, active=active, enable_hiding=True)
                for cat, cname in zip(catops, sorted_categories):
                    if cat != None:
                        cplist = categories[cname]
                        cat.category = cname
                        cat.tabpanel_id = tabID
                        # print('catlen ',cname , len(cplist), cplist)
                        if len(cplist) == 1:
                            cat.single_panel = cplist[0].realID

        plist = categories[active_category]
        if len(plist) > 1:
            mySeparator(maincol)

        category_active_tab = tabpanel_data.get('active_tab_' + active_category)
        if category_active_tab != None:
            active_tab = category_active_tab
            hasactivetab = True

    if len(plist) > 1:  # property windows
        # Draw panels here.
        # these are levels of subpanels(2.8 madness)
        texts = [[], [], [], []]
        ids = [[], [], [], []]
        tdata = [[], [], [], []]
        tabpanels = [[], [], [], []]
        active = [[], [], [], []]

        # row=tabRow(maincol)
        maxlevel = 0
        for p in plist:

            if p.bl_label == 'Preview':
                preview = p
            else:
                visible = True

                if not hasattr(p, 'bl_parent_id'):
                    level = 0
                    print(level, p)

                else:
                    ppanel = eval('bpy.types.' + p.bl_parent_id)
                    print('source', p)
                    print(level, ppanel)
                    level = 1
                    visible = visible and panel_data[ppanel.realID].activated
                    while visible and hasattr(ppanel, 'bl_parent_id'):
                        level += 1
                        #print( panel_data[ppanel.parent])
                        ppanel = eval('bpy.types.' + ppanel.bl_parent_id)
                        # if hasattr(ppanel, 'bl_parent_id'):
                        visible = visible and panel_data[ppanel.realID].activated

                maxlevel = max(maxlevel, level)
                if visible:
                    texts[level].append(p.bl_label)
                    ids[level].append(p.realID)
                    tabpanels[level].append(p)
                    tdata[level].append(panel_data[p.realID])
                    active[level].append(panel_data[p.realID].activated)
        print(texts)
        # Draw all tabs including subtabs. Maaaadneeeesss.
        if tabpanel_data.show:
            if len(categories) == 1:
                tabpanel = tabpanel_data
            else:
                tabpanel = None
            for level in range(0, maxlevel + 1):
                print(f'drawing level {level} from {maxlevel}')
                tabops = drawTabsLayout(self, context, maincol, tabpanel=tabpanel, operator_name='wm.activate_panel',
                                        texts=texts[level], ids=ids[level], tdata=tdata[level], active=active[level],
                                        enable_hiding=False)
                for op, p in zip(tabops, tabpanels[level]):
                    if op != None:
                        op.panel_id = p.realID
                        op.tabpanel_id = tabID
                        op.category = active_category

    if len(draw_panels) == 0 and len(
            plist) > 0:  # and len(categories)== 1)or (len(categories)=>1 and len ) :# or (len(draw_panels == 0) and len(plist)>0):
        # if len(categories)>0:
        # print('ujoj')
        p = plist[0]
        # print(draw_panels)
        if p not in draw_panels:
            draw_panels.append(p)
            _extra_activations.append(p)

    # print(plist)
    layout.active = True

    if preview != None:
        preview.draw(self, context)
    return draw_panels


def modifiersDraw(self, context):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    ob = context.object
    layout = self.layout
    layout.operator_menu_enum("object.modifier_add", "type")
    if len(ob.modifiers) > 0:
        if not prefs.enable_disabling or not (prefs.enable_disabling and prefs.disable_MODIFIERS):
            maincol = layout.column(align=True)

            hasactive = False
            for am in ob.active_modifiers:
                if am in ob.modifiers:
                    hasactive = True
                else:
                    ob.active_modifiers.remove(am)
            active_modifiers = ob.active_modifiers
            if not hasactive:
                active_modifiers = [ob.modifiers[0].name]

            if len(ob.modifiers) > 1:
                names = ob.modifiers.keys()
                active = []
                for m in ob.modifiers:
                    if m.name in active_modifiers:
                        active.append(True)
                    else:
                        active.append(False)

                tabops = drawTabsLayout(self, context, maincol, operator_name='object.activate_modifier', texts=names,
                                        ids=names, active=active)
                for op, mname in zip(tabops, names):
                    op.modifier_name = mname

                mySeparator(maincol)
            for md in ob.modifiers:
                if md.name in active_modifiers:
                    box = layout.template_modifier(md)
                    if box:
                        getattr(self, md.type)(box, ob, md)
        else:
            for md in ob.modifiers:
                box = layout.template_modifier(md)
                if box:
                    getattr(self, md.type)(box, ob, md)


def constraintsDraw(self, context):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences

    ob = context.object

    layout = self.layout
    if ob.type == 'ARMATURE' and ob.mode == 'POSE':
        box = layout.box()
        box.alert = True  # XXX: this should apply to the box background
        box.label(icon='INFO', text="Constraints for active bone do not live here")
        box.operator("wm.properties_context_change", icon='CONSTRAINT_BONE',
                     text="Go to Bone Constraints tab...").context = 'BONE_CONSTRAINT'
    else:
        layout.operator_menu_enum("object.constraint_add", "type", text="Add Object Constraint")
    if len(ob.constraints) > 0:
        if not prefs.enable_disabling or not (prefs.enable_disabling and prefs.disable_MODIFIERS):
            maincol = layout.column(align=True)

            hasactive = False
            for con in ob.active_constraints:
                if con in ob.constraints:
                    hasactive = True

            active_constraints = ob.active_constraints
            if not hasactive:
                active_constraints = [ob.constraints[0].name]

            if len(ob.constraints) > 1:

                active = []
                for con in ob.constraints:
                    if con.name in active_constraints:
                        active.append(True)
                    else:
                        active.append(False)

                names = ob.constraints.keys()
                tabops = drawTabsLayout(self, context, maincol, operator_name='object.activate_constraint', texts=names,
                                        ids=names, active=active)
                for op, cname in zip(tabops, names):
                    op.constraint_name = cname
            for con in ob.constraints:
                if con.name in active_constraints:
                    self.draw_constraint(context, con)
        else:
            for con in ob.constraints:
                self.draw_constraint(context, con)


def boneConstraintsDraw(self, context):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences

    pb = context.pose_bone
    layout = self.layout
    layout.operator_menu_enum("pose.constraint_add", "type", text="Add Bone Constraint")

    if len(pb.constraints) > 0:
        if not prefs.enable_disabling or not (prefs.enable_disabling and prefs.disable_MODIFIERS):
            maincol = layout.column(align=True)
            # active_constraint = pb.active_constraint
            # if not pb.active_constraint in pb.constraints:
            #    active_constraints = [pb.constraints[0].name]

            hasactive = False
            for con in pb.active_constraints:
                if con in pb.constraints:
                    hasactive = True

            active_constraints = pb.active_constraints
            if not hasactive:
                active_constraints = [pb.constraints[0].name]

            if len(pb.constraints) > 1:
                maincol = layout.column(align=True)

                active = []
                for c in pb.constraints:
                    if c.name in active_constraints:
                        active.append(True)
                    else:
                        active.append(False)

                if len(pb.constraints) > 1:
                    names = pb.constraints.keys()
                    # tabops= drawTabsLayout(maincol, context,  operator_name = 'object.activate_constraint', texts = names, ids = names, active = active_constraint)
                    tabops = drawTabsLayout(self, context, maincol, operator_name='object.activate_posebone_constraint',
                                            texts=names, ids=names, active=active)
                    for op, cname in zip(tabops, names):
                        op.constraint_name = cname
            for con in pb.constraints:
                if con.name in active_constraints:
                    self.draw_constraint(context, con)
        else:
            for con in pb.constraints:
                self.draw_constraint(context, con)


def drawPanels(self, context, draw_panels):
    layout = self.layout
    # print(draw_panels)
    for drawPanel in draw_panels:
        # not needed anymore, new drawing from instance ;)
        # for var in dir(drawPanel):
        #    if var not in DEFAULT_PANEL_PROPS:
        #        exec('self.'+var +' = drawPanel.' + var)
        if drawPanel.bl_label != '':
            box = layout.box()
            box.scale_y = 1

            row = box.row()
            row.scale_y = .8

            if hasattr(drawPanel, "draw_header"):
                fakeself = CarryLayout(row)
                if hasattr(drawPanel, 'orig_draw_header'):
                    drawPanel.orig_draw_header(fakeself, context)
                # else:
                #    drawPanel.draw_header(fakeself,context)

            row.label(text=drawPanel.bl_label)

            pd = bpy.context.scene.panelData[drawPanel.realID]
            if pd.pin:
                icon = 'PINNED'
            else:
                icon = 'UNPINNED'
            row.prop(bpy.context.scene.panelData[drawPanel.realID], 'pin', icon_only=True, icon=icon, emboss=False)
        # these are various functions defined all around blender for panels. We need them to draw the panel inside the tab panel

        if hasattr(drawPanel, "draw"):
            # layoutActive(self,context) bpy.types.VIEW3D_PT_weight_palette(bpy.context.window_manager)
            pInstance = drawPanel(bpy.context.window_manager)

            # arg_spec = inspect.getargspec(pInstance.draw)
            # print(arg_spec.args)
            pInstance.layout = layout
            # p.draw(bpy.context)
            drawPanel.draw(pInstance, context)
        layoutActive(self, context)

        layout.separator()
        b = layout.box()
        b.scale_y = 0


def pollTabs(panels, context):
    draw_plist = []
    for p in panels:
        polled = True
        if hasattr(p, "poll"):
            try:
                if hasattr(p, 'opoll'):
                    polled = p.opoll(context)
            except:
                pass  # print ("Unexpected error:", sys.exc_info()[0])
            # polled = p.opoll(context)

        if polled:
            draw_plist.append(p)
            # print('polled', len(panels), len(draw_plist))
    return draw_plist


def getFilteredTabs(self, context):
    # getspace = self.bl_space_type
    getspace = context.area.type
    # getregion = self.bl_region_type
    getregion = context.region.type
    tab_panel_category = ''
    if hasattr(self, 'bl_category'):
        tab_panel_category = self.bl_category
    panellist = getPanels(getspace, getregion)
    # print (panellist)
    tabpanel = self  # eval('bpy.types.' + tabID)
    # print (bpy.types.PHYSICS_PT_collision in panellist)

    possible_tabs = []
    possible_tabs_wider = []
    categories = []
    # print(panellist)
    for panel in panellist:
        # if panel.bl_label =='Options' and hasattr(panel, 'bl_context'):
        #    print('got hrere')
        #   print(panel.bl_context, panel.bl_category)
        # if panel.realID =='VIEW3D_PT_tools_mask_texture':
        #    print('its here!!!! before filter')
        # if panel.bl_label == 'Collision':
        # print('collision in filterfunc')
        # print(getspace, getregion, panellist)
        if not hasattr(panel, 'bl_label'):
            print('not a panel', panel)

        else:  # panel.bl_label!= '':# and panel.bl_label!= 'Influence' and panel.bl_label!= 'Mapping': #these were crashing. not anymore.
            polled = True
            if not panel.is_registered:  # somehow it can happen between updates, so putting this here too.
                polled = False
            # first  filter context and category before doing eval and getting actual panel object. still using  fo data.
            if hasattr(panel, 'bl_context'):
                pctx = panel.bl_context.upper()
                if panel.bl_context == 'particle':  # property particle panels
                    pctx = 'PARTICLES'

                if hasattr(context.space_data, 'context'):
                    if not pctx == context.space_data.context:
                        polled = False

                elif hasattr(context, 'mode'):
                    # TOOLS NEED DIFFERENT APPROACH!!! THS IS JUST AN UGLY UGLY HACK....
                    if panel.bl_context == 'mesh_edit':
                        pctx = 'EDIT_MESH'
                    elif panel.bl_context == 'curve_edit':
                        pctx = 'EDIT_CURVE'
                    elif panel.bl_context == 'surface_edit':
                        pctx = 'EDIT_SURFACE'
                    elif panel.bl_context == 'text_edit':
                        pctx = 'EDIT_TEXT'
                    elif panel.bl_context == 'armature_edit':
                        pctx = 'EDIT_ARMATURE'
                    elif panel.bl_context == 'mball_edit':
                        pctx = 'EDIT_METABALL'
                    elif panel.bl_context == 'lattice_edit':
                        pctx = 'EDIT_LATTICE'
                    elif panel.bl_context == 'posemode':
                        pctx = 'POSE'
                    elif panel.bl_context == 'mesh_edit':
                        pctx = 'SCULPT'
                    elif panel.bl_context == 'weightpaint':
                        pctx = 'PAINT_WEIGHT'
                    elif panel.bl_context == 'vertexpaint':
                        pctx = 'PAINT_VERTEX'
                    elif panel.bl_context == 'imagepaint':
                        pctx = 'PAINT_TEXTURE'
                    elif panel.bl_context == 'objectmode':
                        pctx = 'OBJECT'
                    if panel.bl_context == 'particlemode':  # Tools particle panels
                        pctx = 'PARTICLE'

                    if not pctx == context.mode:
                        polled = False

                    if panel.bl_context == 'scene':  # openGL lights addon problem
                        polled = True
                # print((context.space_data.context))
            if polled:
                possible_tabs_wider.append(panel)
            if hasattr(panel, 'bl_category'):
                if panel.bl_category != tab_panel_category:
                    polled = False
            # print(polled)
            if polled:
                possible_tabs.append(panel)
    # print('possible', len(possible_tabs))
    draw_tabs_list = pollTabs(possible_tabs, context)
    self.tabcount = len(draw_tabs_list)
    return draw_tabs_list


def drawRegionUI(self, context):  # , getspace, getregion, tabID):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    # print(dir(self))

    tabID = self.bl_idname

    draw_tabs_list = getFilteredTabs(self, context)
    # print('pre',self.tabcount)
    # print('filtered',len(draw_tabs_list))
    draw_panels = drawTabs(self, context, draw_tabs_list, tabID)
    if not prefs.original_panels:
        # print(draw_panels)
        drawPanels(self, context, draw_panels)


class PanelUp(bpy.types.Operator):
    """ panel order utility"""
    bl_idname = 'wm.panel_up'
    bl_label = 'panel up'
    bl_options = {'REGISTER'}

    tabpanel_id: bpy.props.StringProperty(name="tab panel name",
                                          default='you didnt assign panel to the operator in ui def')
    panel_id: bpy.props.StringProperty(name="panel name",
                                       default='')

    def execute(self, context):
        # unhide_panel(self.tabpanel_id)
        tabpanel = getattr(bpy.types, self.tabpanel_id, None)
        panel_id = self.panel_id

        ps = bpy.types.Scene.panelSpaces

        # print('up1')
        for s in ps:
            space = ps[s]

            for r in space:

                # print('up2')
                region = space[r]
                swapped = False
                for i, p in enumerate(region):
                    if p.realID == panel_id and i > 0:
                        for i1 in range(i - 1, 0, -1):
                            p1 = region[i1]
                            family = False
                            if hasattr(p, 'bl_context') and hasattr(p1, 'bl_context') and p.bl_context == p1.bl_context:
                                family = True
                            if hasattr(p, 'orig_category') and hasattr(p1,
                                                                       'orig_category') and p.orig_category == p1.orig_category:
                                family = True
                            # print(family, p.bl_context)
                            if family:
                                swapped = True
                                region[i] = p1
                                region[i1] = p

                                break;
                        if not swapped:
                            region[i] = region[i - 1]
                            region[i - 1] = p

        return {'FINISHED'}


class PanelDown(bpy.types.Operator):
    """ panel order utility"""
    bl_idname = 'wm.panel_down'
    bl_label = 'panel down'
    bl_options = {'REGISTER'}

    tabpanel_id: bpy.props.StringProperty(name="tab panel name",
                                          default=' you didnt assign panel to the operator in ui def')
    panel_id: bpy.props.StringProperty(name="panel name",
                                       default='')

    def execute(self, context):
        # unhide_panel(self.tabpanel_id)
        tabpanel = getattr(bpy.types, self.tabpanel_id, None)
        panel_id = self.panel_id

        ps = bpy.types.Scene.panelSpaces

        # print('up1')
        for s in ps:
            space = ps[s]

            for r in space:

                # print('up2')
                region = space[r]
                swapped = False
                for i, p in enumerate(region):
                    if p.realID == panel_id and i < len(region) - 1:
                        for i1 in range(i + 1, len(region)):
                            p1 = region[i1]
                            family = False
                            if hasattr(p, 'bl_context') and hasattr(p1, 'bl_context') and p.bl_context == p1.bl_context:
                                family = True
                            if hasattr(p, 'orig_category') and hasattr(p1,
                                                                       'orig_category') and p.orig_category == p1.orig_category:
                                family = True
                            # print(family, p.bl_context)
                            if family:
                                swapped = True
                                region[i] = p1
                                region[i1] = p

                                break;

                        if not swapped:
                            region[i] = region[i + 1]
                            region[i + 1] = p
                            break;

        return {'FINISHED'}


class WritePanelOrder(bpy.types.Operator):
    """write panel order utility"""
    bl_idname = 'wm.write_panel_order'
    bl_label = 'write panel order'
    bl_options = {'REGISTER'}

    def execute(self, context):
        state_before = {}  # copy.deepcopy(panel_order.spaces)
        ps = bpy.types.Scene.panelSpaces
        f = open('panelSpaces.py', 'w')
        nps = {}
        for s in ps:
            if s not in IGNORE_SPACES:
                space = ps[s]
                nps[s] = {}
                for r in space:
                    if r not in IGNORE_REGIONS and not (r == 'WINDOW' and s == 'VIEW_3D'):

                        nps[s][r] = []
                        nregion = nps[s][r]
                        region = space[r]

                        for p in region:
                            # nregion.append('bpy.types.'+p.realID)
                            nregion.append(p.realID)
                        # nregion.sort()
                        # space[r] = nregion
        # try to append panels that were not open(addons e.t.c.) so we can save sorting for ALL addons :)
        # print(state_before)
        lastp = ''
        for s in state_before:

            space = state_before[s]
            if s not in IGNORE_SPACES:
                for r in space:
                    # ignore horizontal regions:
                    if r not in IGNORE_REGIONS and not (r == 'WINDOW' and s == 'VIEW_3D'):
                        region = space[r]
                        for p in region:
                            if p not in nps[s][r]:
                                if nps[s][r].count(lastp) > 0:
                                    idx = nps[s][r].index(lastp)
                                    nps[s][r].insert(idx + 1, p)
                                    # print('insert', p)
                                    # print(region)
                                else:
                                    # print('write',p)
                                    nps[s][r].append(p)
                                    # print('append', p)
                                    # print(region)
                            lastp = p

        ddef = str(nps)
        ddef = ddef.replace('},', '},\n    ')
        ddef = ddef.replace("],", '],\n    ')
        ddef = ddef.replace("[", "[\n    ")
        ddef = ddef.replace(", ", ",\n    ")
        ddef = ddef.replace("]},", "]},\n    ")
        ddef = ddef.replace("]}}", "]}}")

        # ddef.replace(',',']ahoj' )
        f.write(ddef)
        f.close()
        return {'FINISHED'}


class ActivatePanel(bpy.types.Operator):
    """activate panel"""
    bl_idname = 'wm.activate_panel'
    bl_label = 'activate panel'
    bl_options = {'REGISTER'}

    tabpanel_id: bpy.props.StringProperty(name="tab panel name",
                                          default='PROPERTIES_PT_tabs')
    panel_id: bpy.props.StringProperty(name="panel name",
                                       default='')
    category: bpy.props.StringProperty(name="panel name",
                                       default='')
    shift: bpy.props.BoolProperty(name="shift",
                                  default=False)

    def execute(self, context):
        prefs = bpy.context.preferences.addons["tabs_interface"].preferences
        tabpanel = getattr(bpy.types, self.tabpanel_id, None)
        s = bpy.context.scene
        s.panelTabData[self.tabpanel_id].active_tab = self.panel_id

        panel = tabpanel
        item = s.panelData.get(self.panel_id)
        apanel = getattr(bpy.types, self.panel_id)
        # print(context.area.type, context.region.type)
        plist = s.panelSpaces[panel.bl_space_type][panel.bl_region_type]

        if not self.shift:
            for p in plist:
                c1 = hasattr(apanel, 'bl_context')
                c2 = hasattr(p, 'bl_context')
                if c1 and c2:
                    context_same = p.bl_context == apanel.bl_context
                else:
                    context_same = True

                parent1 = hasattr(apanel, 'bl_parent_id')
                parent2 = hasattr(p, 'bl_parent_id')
                if parent1 and parent2:
                    parents_same = p.bl_parent_id == apanel.bl_parent_id
                elif parent1 or parent2:
                    parents_same = False
                else:
                    parents_same = True

                if p.bl_region_type == panel.bl_region_type and p.bl_space_type == panel.bl_space_type and context_same and (
                        p.orig_category == apanel.orig_category) and parents_same:
                    # this condition does : check region, space
                    #                        same context - mainly property window
                    #                       same category - mainly toolbar. This makes it possible to have active tabs inside categories and not having them all display panels. magic!
                    pdata = s.panelData[p.realID]
                    pdata.activated = False

        # if prefs.original_panels:
        if self.shift and item.activated:
            item.activated = False
        else:
            item.activated = True
            # this is also allready obsolete? not yet so much?
            # if self.category!= '':
            #    s.panelTabData[self.tabpanel_id]['active_tab_'+self.category] = self.panel_id
        # reactivate the category, this is when category wasn't initialized so active category is first category.

        s.panelTabData[self.tabpanel_id].active_category = self.category

        scene_update_handler()
        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift:  # for Multi-selection self.obj = context.selected_objects
            self.shift = True
            # print('shift')
        else:
            self.shift = False
        return self.execute(context)


class ActivateCategory(bpy.types.Operator):
    """activate category"""
    bl_idname = 'wm.activate_category'
    bl_label = 'activate panel category'
    bl_options = {'REGISTER'}

    tabpanel_id: bpy.props.StringProperty(name="tab panel name",
                                          default='PROPERTIES_PT_tabs')
    category: bpy.props.StringProperty(name="category",
                                       default='ahoj')
    single_panel: bpy.props.StringProperty(name="category",
                                           default='')
    shift: bpy.props.BoolProperty(name="shift",
                                  default=False)

    def execute(self, context):
        prefs = bpy.context.preferences.addons["tabs_interface"].preferences
        # unhide_panel(self.tabpanel_id)
        tabpanel = getattr(bpy.types, self.tabpanel_id)
        s = bpy.context.scene
        s.panelTabData[self.tabpanel_id].active_category = self.category

        return {'FINISHED'}

    def invoke(self, context, event):
        prefs = bpy.context.preferences.addons["tabs_interface"].preferences
        if event.shift:  # for Multi-selection self.obj = context.selected_objects
            self.shift = True
            # print('shift')
        else:
            self.shift = False
        if self.single_panel != '':
            bpy.ops.wm.activate_panel(tabpanel_id=self.tabpanel_id, panel_id=self.single_panel, category=self.category,
                                      shift=self.shift)

        s = bpy.context.scene
        tabpanel = getattr(bpy.types, self.tabpanel_id)
        plist = s.panelSpaces[tabpanel.bl_space_type][tabpanel.bl_region_type]

        # if not self.shift:
        for p in plist:
            pdata = s.panelData[p.realID]
            if (p.orig_category == self.category):
                pdata.activated_category = True
            else:
                pdata.activated_category = False
        return self.execute(context)


'''        
class PopupPanel(bpy.types.Operator):
    bl_idname = 'wm.popup_panel'
    bl_label = 'popup_panel'
    bl_options = {'REGISTER'}
    
    
    tabpanel_id : bpy.props.StringProperty(name="tab panel name",
                default='PROPERTIES_PT_tabs')
    panel_id : bpy.props.StringProperty(name="panel name",
                default='')
    
     
    def draw_panel(self, layout, pt):
        try:
            if hasattr(pt, "poll") and not pt.poll(bpy.context):
                print("POLL")
                return
        except:
            print("POLL")
            return
        
        p = pt(bpy.context.window_manager)
        p.layout = layout.box()
        p.draw(bpy.context)
       
 
    def draw(self, context):
        layout = self.layout
        self.draw_panel(layout, tp)
 
    def execute(self, context):
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
 '''


class ActivateModifier(bpy.types.Operator):
    """activate modifier"""
    bl_idname = 'object.activate_modifier'
    bl_label = 'activate modifier'
    bl_options = {'REGISTER'}

    modifier_name: bpy.props.StringProperty(name="Modifier name",
                                            default='')
    shift: bpy.props.BoolProperty(name="shift",
                                  default=False)

    def execute(self, context):
        ob = bpy.context.active_object
        if not self.shift:
            ob.active_modifiers.clear()

        if self.shift and self.modifier_name in ob.active_modifiers:
            ob.active_modifiers.remove(self.modifier_name)
        elif self.modifier_name not in ob.active_modifiers:
            ob.active_modifiers.append(self.modifier_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift:  # for Multi-selection self.obj = context.selected_objects
            self.shift = True
            # print('shift')
        else:
            self.shift = False
        return self.execute(context)


class ActivateConstraint(bpy.types.Operator):
    """activate constraint"""
    bl_idname = 'object.activate_constraint'
    bl_label = 'activate constraint'
    bl_options = {'REGISTER'}

    constraint_name: bpy.props.StringProperty(name="Constraint name", default='')

    def execute(self, context):
        ob = bpy.context.active_object
        if not self.shift:
            ob.active_constraints.clear()

        if self.shift and self.constraint_name in ob.active_constraints:
            ob.active_constraints.remove(self.constraint_name)
        elif self.constraint_name not in ob.active_constraints:
            ob.active_constraints.append(self.constraint_name)
        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift:  # for Multi-selection self.obj = context.selected_objects
            self.shift = True
            # print('shift')
        else:
            self.shift = False
        return self.execute(context)


class ActivatePoseBoneConstraint(bpy.types.Operator):
    """activate constraint"""
    bl_idname = 'object.activate_posebone_constraint'
    bl_label = 'activate constraint'
    bl_options = {'REGISTER'}

    constraint_name: bpy.props.StringProperty(name="Constraint name",
                                              default='')

    def execute(self, context):
        pb = bpy.context.pose_bone
        if not self.shift:
            pb.active_constraints.clear()

        if self.shift and self.constraint_name in pb.active_constraints:
            pb.active_constraints.remove(self.constraint_name)
        elif self.constraint_name not in pb.active_constraints:
            pb.active_constraints.append(self.constraint_name)

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift:  # for Multi-selection self.obj = context.selected_objects
            self.shift = True
            # print('shift')
        else:
            self.shift = False
        return self.execute(context)


class TabsPanel:
    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons["tabs_interface"].preferences
        if prefs.enable_disabling:
            if prefs.disable_PROPERTIES and context.area.type == 'PROPERTIES':
                return False
            if prefs.disable_TOOLBAR and context.region.type == 'TOOLS':
                return False
            if prefs.disable_UI and context.region.type == 'UI':
                return False
        return True  # tabspanel_info==None or len(draw_tabs_list) >1


# THIS FUNCTION DEFINES ALL THE TABS PANELS.!!!
def createPanels():
    spaces = bpy.types.Scene.panelSpaces
    s = bpy.types.Scene
    definitions = []
    panelIDs = []
    pdef = "class %s(TabsPanel,bpy.types.Panel):\n    bl_space_type = '%s'\n    bl_region_type = '%s'\n    bl_options = {'HIDE_HEADER'}\n    %s\n    bl_label = 'Tabs'\n    bl_idname = '%s'\n    draw = drawRegionUI\n"
    for sname in spaces:
        space = spaces[sname]
        for rname in space:
            region = space[rname]

            categories = {}
            contexts = {}
            for panel in region:
                if hasattr(panel,
                           'bl_context') and panel.bl_context != 'scene':  # scene context because of opengl lights addon
                    contexts[panel.bl_context] = 1
                if hasattr(panel, 'bl_category'):
                    categories[panel.bl_category] = True

            # categories['nothing'] = True#nonsense to debug condition now.

            if len(categories) > 0:
                # for cname in categories:
                # if panel.bl_space_type == 'VIEW_3D' and panel.bl_region_type == 'TOOLS':
                #   cname = 'Tools'
                # else:
                #    cname = 'Default'
                cname = 'Tools'  # tools
                cnamefixed = cname.upper();
                cnamefixed = cnamefixed.replace(' ', '_')
                cnamefixed = cnamefixed.replace('/', '_')
                pname = '%s_PT_%s_%s_tabs' % (sname.upper(), rname.upper(), cnamefixed.upper())

                cstring = pdef % (pname, sname.upper(), rname.upper(), "bl_category = '%s'" % cname, pname)

                definitions.append(cstring)
                panelIDs.append(pname)
            elif len(contexts) > 0:
                for cname in contexts:
                    cnamefixed = cname.upper();
                    cnamefixed = cnamefixed.replace(' ', '_')
                    cnamefixed = cnamefixed.replace('/', '_')
                    pname = '%s_PT_%s_%s_tabs' % (sname.upper(), rname.upper(), cnamefixed.upper())

                    cstring = pdef % (pname, sname.upper(), rname.upper(), "bl_context = '%s'" % cname, pname)

                    definitions.append(cstring)
                    panelIDs.append(pname)
            else:
                pname = '%s_PT_%s_tabs' % (sname.upper(), rname.upper())
                cstring = pdef % (pname, sname.upper(), rname.upper(), "", pname)
                definitions.append(cstring)
                panelIDs.append(pname)

    return definitions, panelIDs


class VIEW3D_PT_transform(bpy.types.Panel):
    bl_label = "Transform"
    bl_idname = "VIEW3D_PT_transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return False

    def draw(self, context):
        pass;


class VIEW3D_PT_Transform(bpy.types.Panel):
    bl_label = "Transform"
    bl_idname = "VIEW3D_PT_Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object != None

    def draw(self, context):
        layout = self.layout

        ob = context.object
        layout.alignment = 'RIGHT'
        row = layout.row()

        row.column(align=True).prop(ob, "location")
        # align=False);
        row.column(align=True).prop(ob, "lock_location")
        row = layout.row()
        if ob.rotation_mode == 'QUATERNION':
            row.column().prop(ob, "rotation_quaternion", text="Rotation")

        elif ob.rotation_mode == 'AXIS_ANGLE':
            # row.column().label(text="Rotation")
            # row.column().prop(pchan, "rotation_angle", text="Angle")
            # row.column().prop(pchan, "rotation_axis", text="Axis")
            row.column().prop(ob, "rotation_axis_angle", text="Rotation")

        else:
            row.column().prop(ob, "rotation_euler", text="Rotation")
        row.column(align=True).prop(ob, "lock_rotation")
        layout.prop(ob, "rotation_mode", text='')
        row = layout.row()
        row.column().prop(ob, "scale")
        row.column(align=True).prop(ob, "lock_scale")
        row = layout.row()
        row.column(align=True).prop(ob, "dimensions")


def updateDisabling(self, context):
    prefs = bpy.context.preferences.addons["tabs_interface"].preferences
    s = bpy.context.scene
    spaces = s.panelSpaces
    panel_data = s.panelData
    if prefs.enable_disabling and prefs.disable_TOOLBAR:

        for sname in spaces:
            space = spaces[sname]
            for rname in space:
                if rname == 'TOOLS':
                    region = space[rname]
                    for p in region:
                        # pdata = panel_data[p.realID]

                        if hasattr(p, 'bl_category'):
                            p.bl_category = p.orig_category
                            bpy.utils.unregister_class(p)
                            bpy.utils.register_class(p)

    if not prefs.enable_disabling or not prefs.disable_TOOLBAR:
        for sname in spaces:
            space = spaces[sname]
            for rname in space:
                region = space[rname]
                for p in region:
                    if hasattr(p, 'orig_category'):
                        # p.bl_category = 'Tools'
                        # try:# TODO fix this
                        bpy.utils.unregister_class(p)
                        bpy.utils.register_class(p)
                        # except:
                        #     print('fail enable disable ',p)


class TabInterfacePreferences(bpy.types.AddonPreferences):
    bl_idname = "tabs_interface"
    # here you define the addons customizable props
    original_panels: bpy.props.BoolProperty(name='Default blender panels', description='', default=False)
    fixed_width: bpy.props.BoolProperty(name='Grid layout', default=True)
    fixed_columns: bpy.props.BoolProperty(name='Fixed number of colums', default=True)
    columns_properties: bpy.props.IntProperty(name='Columns in property window', default=3, min=1)
    columns_modifiers: bpy.props.IntProperty(name='Columns in modifiers and constraints', default=3, min=1)
    columns_rest: bpy.props.IntProperty(name='Columns in side panels', default=2, min=1)
    emboss: bpy.props.BoolProperty(name='Invert tabs drawing', default=True)
    # align_rows : bpy.props.BoolProperty(name = 'Align tabs in rows', default=True)
    box: bpy.props.BoolProperty(name='Draw box around tabs', default=True)
    scale_y: bpy.props.FloatProperty(name='vertical scale of tabs', default=1)
    reorder_panels: bpy.props.BoolProperty(name='allow reordering panels (developer tool only)', default=False)
    hiding: bpy.props.BoolProperty(name='Enable panel hiding', description='switch to/from hiding mode', default=False)
    show_hiding_icon: bpy.props.BoolProperty(name='Enable hiding icon',
                                             description="Disable this if you just don't want that little eye in each window tab area.",
                                             default=True)
    enable_folding: bpy.props.BoolProperty(name='Enable tab panel folding icon',
                                           description='switch to/from hiding mode', default=False)

    enable_disabling: bpy.props.BoolProperty(name='Enable tab panel disable for areas',
                                             description='switch to/from hiding mode', default=True,
                                             update=updateDisabling)
    disable_TOOLBAR: bpy.props.BoolProperty(name='Disable tabs in toolbar regions',
                                            description='switch to/from hiding mode', default=True,
                                            update=updateDisabling)
    disable_UI: bpy.props.BoolProperty(name='Disable tabs in UI regions', description='switch to/from hiding mode',
                                       default=False, update=updateDisabling)
    disable_PROPERTIES: bpy.props.BoolProperty(name='Disable properties area',
                                               description='switch to/from hiding mode', default=False,
                                               update=updateDisabling)
    disable_MODIFIERS: bpy.props.BoolProperty(name='Disable for modifiers and constraints',
                                              description='switch to/from hiding mode', default=True,
                                              update=updateDisabling)

    panelData: bpy.props.CollectionProperty(type=panelData)
    panelTabData: bpy.props.CollectionProperty(type=tabSetups)
    categories: bpy.props.CollectionProperty(type=tabCategoryData)

    # here you specify how they are drawn
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "emboss")
        layout.prop(self, "box")

        layout.prop(self, "fixed_width")
        if self.fixed_width:
            layout.prop(self, "fixed_columns")
            if self.fixed_columns:
                layout.prop(self, "columns_properties")
                layout.prop(self, "columns_modifiers")
                layout.prop(self, "columns_rest")
        # layout.prop(self, "align_rows")
        if not self.fixed_width:
            layout.prop(self, "scale_y")
        layout.prop(self, "original_panels")
        layout.prop(self, "enable_folding")
        layout.prop(self, "show_hiding_icon")
        layout.prop(self, "enable_disabling")
        if self.enable_disabling:
            b = layout.box()
            b.prop(self, "disable_TOOLBAR")
            b.prop(self, "disable_UI")
            b.prop(self, "disable_PROPERTIES")
            # b.prop(self, "disable_MODIFIERS")
        layout.prop(self, "reorder_panels")


def createSceneTabData():
    if DEBUG:
        print('create tab panel data')
    s = bpy.context.scene
    # print('handler')
    processpanels = []

    removepanels = []
    for pname in bpy.types.Scene.panelIDs:
        if hasattr(bpy.types, pname):
            p = getattr(bpy.types, pname)
            if not hasattr(p, 'realID') or s.panelData.get(p.realID) == None or p not in s.panelSpaces[p.bl_space_type][
                p.bl_region_type]:
                processpanels.append(p)

        else:
            removepanels.append(pname)

    for pname in removepanels:  # can't pop during iteration, doing afterwards.
        bpy.types.Scene.panelIDs.pop(pname)

    if len(processpanels) > 0:
        buildTabDir(processpanels)
    # print('create scene tab data')
    for pname in bpy.types.Scene.panelIDs:
        # print('pname')
        if hasattr(bpy.types, pname):
            # print('go on ')
            # print(p.realID)
            p = getattr(bpy.types, pname)
            # TODO following condition should not check for realID...this should be there allready
            if hasattr(p, 'realID'):
                if not p.realID in bpy.context.scene.panelData:

                    item = bpy.context.scene.panelData.add()
                    item.name = p.realID
                    item.space = p.bl_space_type
                    item.region = p.bl_region_type
                    if hasattr(p, 'bl_context'):
                        item.context = p.bl_context
                    if hasattr(p, 'orig_category'):
                        item.category = p.orig_category
                    if hasattr(p, 'bl_parent_id'):
                        item.parent = p.bl_parent_id

                    # item.context = p.bl_region_type

                if hasattr(p,
                           'bl_category'):  # and not (p.bl_region_type == 'UI' and p.bl_space_type == 'VIEW_3D'): #additional checks for Archimesh only!
                    c = s.categories.get(p.orig_category)
                    if c == None:
                        # print(p.orig_category)
                        c = s.categories.add();
                        c.name = p.orig_category
            else:
                print('unprocessed without realID', p)

    while len(_update_tabs) > 0:
        pt = _update_tabs.pop()
        print('updating  ', pt)
        # print( r.panelTabData)
        # print( s.panelTabData.get(pt.bl_rna.identifier))
        pname = pt.bl_rna.identifier

        if s.panelTabData.get(pname) == None:
            item = s.panelTabData.add()
            item.name = pname

    while len(_update_categories) > 0:
        cname = _update_categories.pop()
        c = s.categories.get(p.bl_category)
        if c == None:
            c = s.categories.add();
            c.name = cname

    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type != 'INFO':
                for r in a.regions:
                    override = {'window': w, 'screen': w.screen, 'area': a, 'region': r}
                    bpy.ops.view2d.scroll_up(override, deltax=0, deltay=5000)

                    # print(r.type)
                    r.tag_redraw()
                a.tag_redraw()


def overrideDrawFunctions():
    s = bpy.context.scene
    if s.get('functions_overwrite_success') == None:
        s['functions_overwrite_success'] = False
    if not s['functions_overwrite_success']:
        try:
            # Modifiers and constraints are reorderable and were disabled by now.
            # bpy.types.DATA_PT_modifiers.draw = modifiersDraw
            # bpy.types.OBJECT_PT_constraints.draw = constraintsDraw
            # bpy.types.BONE_PT_constraints.draw = boneConstraintsDraw
            s['functions_overwrite_success'] = True
        except:
            pass


@persistent
def scene_load_handler(scene):
    s = bpy.context.scene

    allpanels = getPanelIDs()
    bpy.types.Scene.panelSpaces = buildTabDir(allpanels)

    btypeslen = len(dir(bpy.types))
    if btypeslen != s.get('bpy_types_len'):
        updatePanels()
    s['bpy_types_len'] = btypeslen
    createSceneTabData()
    # fixes.fixes() #fixes not needed at all since new release
    s['functions_overwrite_success'] = False
    overrideDrawFunctions()
    updateDisabling(None, bpy.context)  # needs to be called to register back panels!


@persistent
def scene_update_handler():
    s = bpy.context.scene

    s = bpy.context.scene
    sc = s.get('tabs_update_counter')
    first = False
    if sc == None:
        first = True
        sc = s['tabs_update_counter'] = 0

    s['tabs_update_counter'] += 1
    # if sc > 5 or first:  # this should be replaced by better detecting if registrations might have changed.
    s['tabs_update_counter'] = 0
    # t = time.time()

    btypeslen = len(dir(bpy.types))
    if btypeslen != s.get('bpy_types_len') or first:
        updatePanels()
    s['bpy_types_len'] = btypeslen

    overrideDrawFunctions()

    if len(_update_tabs) > 0 or first:
        createSceneTabData()

    while len(_extra_activations) > 0:
        p = _extra_activations.pop()
        bpy.context.scene.panelData[p.realID].activated = True

    return 1


def every_2_seconds():
    while not tasks_queue.empty():
        print('as a task:   ')
        fstring = tasks_queue.get()
        eval(fstring)
    return 2.0


def register():
    # bpy.utils.register_class(VIEW3D_PT_Transform)#we need this panel :()
    # bpy.utils.register_class(VIEW3D_PT_transform)#we need this panel :()

    bpy.utils.register_class(PanelUp)
    bpy.utils.register_class(PanelDown)
    bpy.utils.register_class(WritePanelOrder)
    bpy.utils.register_class(ActivatePanel)
    bpy.utils.register_class(ActivateCategory)
    # bpy.utils.register_class(PopupPanel)
    bpy.utils.register_class(ActivateModifier)
    bpy.utils.register_class(ActivateConstraint)
    bpy.utils.register_class(ActivatePoseBoneConstraint)
    bpy.utils.register_class(tabSetups)
    bpy.utils.register_class(panelData)
    bpy.utils.register_class(tabCategoryData)
    bpy.utils.register_class(TabInterfacePreferences)

    bpy.types.Object.active_modifiers = []  # bpy.props.StringProperty(name = 'active modifier', default = '')
    bpy.types.Object.active_constraints = []  # bpy.props.StringProperty(name = 'active constraint', default = '')
    bpy.types.PoseBone.active_constraints = []  # bpy.props.StringProperty(name = 'active constraint', default = '')

    bpy.types.Scene.panelData = bpy.props.CollectionProperty(type=panelData)
    bpy.types.Scene.panelTabData = bpy.props.CollectionProperty(type=tabSetups)
    bpy.types.Scene.categories = bpy.props.CollectionProperty(type=tabCategoryData)

    bpy.app.handlers.load_post.append(scene_load_handler)
    bpy.app.handlers.load_post.append(scene_update_handler)
    bpy.app.timers.register(scene_update_handler)

    allpanels = getPanelIDs()
    bpy.types.Scene.panelSpaces = buildTabDir(allpanels)

    # build the classess here!!
    definitions, panelIDs = createPanels()
    for d in definitions:
        # print(d)
        exec(d)
    for pname in panelIDs:
        # print('register ', pname)
        # print(pname)
        p = eval(pname)
        # print(dir(p))
        bpy.utils.register_class(eval(pname))

        # pt = eval('bpy.types.'+pname)


def unregister():
    # first, fix the panels:
    for panel in bpy.types.Scene.panelIDs:

        if hasattr(panel, 'bl_category'):
            if hasattr(panel, 'orig_category'):
                panel.bl_category = panel.orig_category

        fixOriginalPanel(panel)

    # bpy.utils.unregister_class(VIEW3D_PT_Transform)
    # bpy.utils.unregister_class(VIEW3D_PT_transform)

    definitions, panelIDs = createPanels()
    for d in definitions:
        # print(d)
        exec(d)
    for pname in panelIDs:
        # print('unregister ', pname)
        if hasattr(bpy.types, pname):
            bpy.utils.unregister_class(getattr(bpy.types, pname))

    bpy.utils.unregister_class(PanelUp)
    bpy.utils.unregister_class(PanelDown)
    bpy.utils.unregister_class(WritePanelOrder)
    bpy.utils.unregister_class(ActivatePanel)
    bpy.utils.unregister_class(ActivateCategory)
    # bpy.utils.unregister_class(PopupPanel)
    bpy.utils.unregister_class(ActivateModifier)
    bpy.utils.unregister_class(ActivateConstraint)
    bpy.utils.unregister_class(ActivatePoseBoneConstraint)
    bpy.utils.unregister_class(tabSetups)
    bpy.utils.unregister_class(panelData)
    bpy.utils.unregister_class(tabCategoryData)
    bpy.utils.unregister_class(TabInterfacePreferences)

    bpy.app.handlers.load_post.remove(scene_load_handler)
    bpy.app.handlers.load_post.remove(scene_update_handler)
    bpy.app.timers.unregister(scene_update_handler)

    del bpy.types.Scene.panelSpaces
    del bpy.types.Scene.panelIDs


if __name__ == "__main__":
    register()

    # https://github.com/meta-androcto/blenderpython/tree/master/scripts/addons_extern/AF_view3d_mod https://github.com/meta-androcto/blenderpython/tree/master/scripts/addons_extern/AF_view3d_toolbar_mod
