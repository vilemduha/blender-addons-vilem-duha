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

# <pep8 compliant>


bl_info = {
    "name": "Function Profiling",
    "description": "Profile your python code conveniently",
    "author": "Vilem Duha",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Text Editor > Dev Tab > Function Profiling",
    #    "doc_url": "{BLENDER_MANUAL_URL}/addons/development/icon_viewer.html",
    "category": "Development",
}

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, BoolProperty

import bpy
import time
import cProfile
import blenderkit
import queue
import inspect
import io
import pstats
from pstats import SortKey

profiler = cProfile.Profile()

profiler_step = 0
profiler_step_total = 0
profiler_start_time = 0
orig_function = None
fpath = fpath = []

read_queue = queue.Queue()


def replace_function(function_name, args='', output_step=10, max_steps=100, sort_key='CUMULATIVE', limit_type='COUNT',
                     limit_time=10):
    global orig_function, profiler, profiler_step, profiler_step_total, fpath
    fpath = function_name.split('.')
    if len(fpath) > 1:
        exec (f"import {fpath[0]}")

    exec (f"orig_fdef = inspect.getsource({function_name}).splitlines()[0]")
    args = locals()['orig_fdef'].split('(')[1]
    args = args.split(')')[0]
    print(args)

    fdef = f'''

orig_function = {function_name}
print(orig_function)
def function_profiled({args}):
    global profiler,profiler_step, profiler_step_total, orig_function, steps, fpath, read_queue,profiler_start_time
    if len(fpath)>1:
        exec(f"import {fpath[0]}")
        
    result = profiler.runcall(orig_function,{args})
    
    profiler_step+=1
    profiler_step_total+=1
    t = time.time()
    tot_time = t-profiler_start_time
    print("profiling {function_name} {profiler_step}")
    
    
    print(tot_time, '{limit_type}')
    if ('{limit_type}' == 'COUNT' and profiler_step_total>={max_steps}) or \
        profiler_step >= {output_step} or \
        ('{limit_type}' == 'TIME' and tot_time >= {limit_time}):
        
        if ('{limit_type}' == 'COUNT' and profiler_step_total>={max_steps}) or \
                ('{limit_type}' == 'TIME' and tot_time > {limit_time}):
            profiler.disable() 
            {function_name}= orig_function
            
        profiler_step = 0
        
        s = io.StringIO()
        sortby = SortKey.{sort_key}
        ps = pstats.Stats(profiler, stream=s).strip_dirs().sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        read_queue.put(s.getvalue())
        
    return result
    '''
    print(fdef)
    exec (fdef)
    frewrite = f'''{function_name} = function_profiled
    '''
    exec (frewrite)




class ProfilingOperator(bpy.types.Operator):
    """Move an object with the mouse, example"""
    bl_idname = "scene.function_profiling"
    bl_label = "Profile function"

    function_path: StringProperty(
        name="Function path",
        description="url",
        default="yourmodule.submodule.function")

    max_steps: IntProperty(name="Cycles",
                           description="How many runs of the function should be profiled",
                           default=1,
                           min=0,
                           max=1000000)
    output_step: IntProperty(name="Output step",
                             description="How often to copy stats to Blender text",
                             default=1,
                             min=0,
                             max=1000000)

    sort_key: EnumProperty(
        items=(
            ('CALLS', 'call count', ''),
            ('CUMULATIVE', 'cumulative time', ''),
            ('PCALLS', 'primitive call count', ''),
            ('TIME', 'internal time', '')

        ),
        default='CUMULATIVE',
        description=''
    )

    limit_type: EnumProperty(
        items=(
            ('COUNT', 'Count calls', ''),
            ('TIME', 'Limit time', ''),
        ),
        default='COUNT',
        description='Either count function calls or measure all calls in a timeframe from the start of the profiler.'
    )
    limit_time : IntProperty(name="Time limit",
                             description="Time limit in seconds",
                             default=10,
                             min=1,
                             max=1000000)

    def modal(self, context, event):
        global read_queue, profiler_step_total

        if not read_queue.empty():
            text = read_queue.get()
            t = bpy.data.texts.get('profiling')
            if t is None:
                t = bpy.data.texts.new(name='profiling')
            t.from_string(text)
            if profiler_step_total >= self.max_steps:
                profiler_step_total = 0
                t.write('\n\nFinished')
                return {'FINISHED'}

        if event.type == 'ESC':
            profiler_step_total = self.max_steps

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global profiler_step, profiler, profiler_start_time
        profiler = cProfile.Profile()
        profiler_step = 0
        profiler_start_time = time.time()
        replace_function(function_name=self.function_path, output_step=self.output_step, max_steps=self.max_steps,
                         sort_key=self.sort_key, limit_time=self.limit_time, limit_type=self.limit_type)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class TEXT_EDITOR_PT_function_profiling(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "Function Profiling"
    bl_category = "Dev"

    #    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        # draw asset properties here
        layout = self.layout
        s = bpy.context.scene
        layout.prop(s, 'profiling_function')
        layout.prop(s, 'profiling_limit_type')
        if s.profiling_limit_type == 'COUNT':
            layout.prop(s, 'profiling_max_steps')
        else:
            layout.prop(s, 'profiling_limit_time')
        layout.prop(s, 'profiling_output_step')
        layout.prop(s, 'profiling_sort_key')

        op = layout.operator('scene.function_profiling')
        op.function_path = s.profiling_function
        op.max_steps = s.profiling_max_steps
        op.output_step = s.profiling_output_step
        op.sort_key = s.profiling_sort_key
        op.limit_type = s.profiling_limit_type
        op.limit_time = s.profiling_limit_time


def register():
    bpy.types.Scene.profiling_function = StringProperty(
        name="Function path",
        description="url",
        default="yourmodule.submodule.function")
    bpy.types.Scene.profiling_max_steps = IntProperty(name="Total Cycles",
                                                      description="How many runs of the function should be profiled",
                                                      default=1,
                                                      min=0,
                                                      max=1000000)
    bpy.types.Scene.profiling_output_step = IntProperty(name="Output step",
                                                        description="How often to copy stats to Blender text",
                                                        default=1,
                                                        min=0,
                                                        max=1000000)

    bpy.types.Scene.profiling_sort_key = EnumProperty(
        items=(
            ('CALLS', 'call count', ''),
            ('CUMULATIVE', 'cumulative time', ''),
            ('PCALLS', 'primitive call count', ''),
            ('TIME', 'internal time', ''),
        ),
        default='CUMULATIVE',
        description=''
    )

    bpy.types.Scene.profiling_limit_type = EnumProperty(
        name='Limit',
        items=(
            ('COUNT', 'Count', ''),
            ('TIME', 'Time', ''),
        ),
        default='COUNT',
        description='Either count function calls or measure all calls in a timeframe from the start of the profiler.'
    )
    bpy.types.Scene.profiling_limit_time = IntProperty(name="Time limit",
                                                       description="Time limit in seconds",
                                                       default=10,
                                                       min=1,
                                                       max=1000000)
    bpy.utils.register_class(ProfilingOperator)
    bpy.utils.register_class(TEXT_EDITOR_PT_function_profiling)


def unregister():
    bpy.utils.unregister_class(ProfilingOperator)
    bpy.utils.unregister_class(TEXT_EDITOR_PT_function_profiling)

    del bpy.types.Scene.profiling_function
    del bpy.types.Scene.profiling_max_steps
    del bpy.types.Scene.profiling_output_step
    del bpy.types.Scene.profiling_sort_key
    del bpy.types.Scene.profiling_limit_type
    del bpy.types.Scene.profiling_limit_time


if __name__ == "__main__":
    register()
