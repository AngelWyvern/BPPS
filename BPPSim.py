bl_info = {
    "name": "Pen Pressure Simulator",
    "description": "Basic pen pressure simulator for texture painting",
    "author": "Angel Bot",
    "version": (1, 0),
    "blender": (2, 80, 0)
}

import bpy
from bpy.props import *
from bpy.app.handlers import persistent
import math

class BPPS_States(bpy.types.PropertyGroup):
    modActive : BoolProperty(name = "Tool Active")
    
    framerate : IntProperty(
        name = "Updates Per Second",
        description = "How many times the brush size updates in a second (higher is smoother, but takes more processing power)",
        default = 50,
        min = 1,
        soft_max = 120
    )
    
    sensitivity : FloatProperty(
        name = "Mouse Sensitivity",
        description = "Sets how sensitive the tool is to the pointer speed (larger values yield larger strokes)",
        default = 5.0,
        soft_min = 0.01,
        soft_max = 100.0
    )
    
    samples : IntProperty(
        name = "Sample Length",
        description = "The amount of samples saved for average pointer speed calculation",
        default = 4,
        min = 1,
        soft_max = 16
    )
    
    strokeMin : IntProperty(
        name = "Min Radius", 
        description = "The minimum stroke radius of the brush",
        default = 10,
        soft_min = 1, 
        soft_max = 500
    )

    strokeMax : IntProperty(
        name = "Max Radius", 
        description = "The maximum stroke radius of the brush",
        default = 50,
        soft_min = 1, 
        soft_max = 500
    )
    
    easing : EnumProperty(
        name = "Easing",
        description = "The easing curve of the stroke radius",
        items = [('Linear', "Linear", ""),
                 ('InCubic', "Cubic In", ""),
                 ('OutCubic', "Cubic Out", ""),
                 ('InCirc', "Circ In", ""),
                 ('OutCirc', "Circ Out", ""),
                 ('InQuart', "Quart In", ""),
                 ('OutQuart', "Quart Out", "")
        ],
        default = "Linear"
    )
    
    fixedBounds : BoolProperty(name = "Fixed Bounds", default = True)

class BPPS_Main_Panel(bpy.types.Panel):
    bl_label = "Pressure Simulator"
    bl_idname = "BPPS_Main_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    
    def draw(self, context):
        layout = self.layout
        
        states = context.scene.bpps_states
        
        row = layout.row()
        row.prop(states, "easing")
        
        row = layout.row()
        row.prop(states, "sensitivity", slider=True)
        row.prop(states, "samples", slider=True)
        
        row = layout.row()
        row.prop(states, "strokeMin", slider=True)
        row.prop(states, "strokeMax", slider=True)
        
        row = layout.row()
        row.prop(states, "fixedBounds")
        
        layout.separator()
        
        row = layout.row()
        row.prop(states, "framerate", emboss=states.modActive is False)
        
        row = layout.row()
        if context.scene.bpps_states.modActive is False:
            row.operator("bpps.start_tool")
        else:
            row.operator("bpps.stop_tool", depress=True)

class BPPS_Start_Tool(bpy.types.Operator):
    bl_label = "Enable Simulator"
    bl_idname = "bpps.start_tool"
    
    def execute(self, context):
        context.scene.bpps_states.modActive = True
        bpy.ops.wm.bpps_modal_operator()
        return {'FINISHED'}

class BPPS_Stop_Tool(bpy.types.Operator):
    bl_label = "Disable Simulator"
    bl_idname = "bpps.stop_tool"
    
    def execute(self, context):
        context.scene.bpps_states.modActive = False
        return {'FINISHED'}

class BPPS_Modal_Timer(bpy.types.Operator):
    bl_label = "Pressure Simulator Timer Operator"
    bl_idname = "wm.bpps_modal_operator"
    
    oldX = 0
    oldY = 0
    samples = []
    
    _timer = None
    
    def modal(self, context, event):
        if context.scene.bpps_states.modActive is False:
            self.cancel(context)
            return {'CANCELLED'}
        if event.type == 'TIMER':
            # bpy.context.scene.tool_settings.unified_paint_settings.size = random.randint(1, context.scene.bpps_states.strokeMax)
            
            # print("x:", event.mouse_x, "y:", event.mouse_y)
            
            # factor = 96 / 25.4
            self.samples.append(math.sqrt((event.mouse_x - self.oldX)**2 + (event.mouse_y - self.oldY)**2) / 100 * context.scene.bpps_states.sensitivity)
            while len(self.samples) > context.scene.bpps_states.samples:
                self.samples.pop(0)
            
            avgSpeed = sum(self.samples) / len(self.samples)
            if context.scene.bpps_states.fixedBounds is True and avgSpeed > 1.0:
                avgSpeed = 1.0
            
            # if avgSpeed > 0.0:
            #     print("BPPS avg mouse speed:", avgSpeed)
            
            bpy.context.scene.tool_settings.unified_paint_settings.size = round(context.scene.bpps_states.strokeMin + ease(avgSpeed, context.scene.bpps_states.easing) * (context.scene.bpps_states.strokeMax - context.scene.bpps_states.strokeMin))
            
            self.oldX = event.mouse_x
            self.oldY = event.mouse_y
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        interval = 1/context.scene.bpps_states.framerate
        print("Interval:", interval)
        self._timer = context.window_manager.event_timer_add(interval, window=context.window)
        context.window_manager.modal_handler_add(self)
        print("BPPS timer started")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("BPPS timer stopped")

def ease(v, easing):
    if easing == 'InCubic':
        return math.pow(v, 3)
    elif easing == 'OutCubic':
        return 1 - math.pow(1 - v, 3)
    elif easing == 'InCirc':
        return 1 - math.sqrt(1 - math.pow(v, 2))
    elif easing == 'OutCirc':
        return math.sqrt(1 - math.pow(v - 1, 2))
    elif easing == 'InQuart':
        return math.pow(v, 4)
    elif easing == 'OutQuart':
        return 1 - math.pow(1 - v, 4)
    return v

def register():
    bpy.utils.register_class(BPPS_States)
    bpy.utils.register_class(BPPS_Main_Panel)
    bpy.utils.register_class(BPPS_Start_Tool)
    bpy.utils.register_class(BPPS_Stop_Tool)
    bpy.utils.register_class(BPPS_Modal_Timer)
    
    bpy.types.Scene.bpps_states = bpy.props.PointerProperty(type = BPPS_States)
    
    print("BPPS loaded")

def unregister():
    bpy.utils.unregister_class(BPPS_States)
    bpy.utils.unregister_class(BPPS_Main_Panel)
    bpy.utils.unregister_class(BPPS_Start_Tool)
    bpy.utils.unregister_class(BPPS_Stop_Tool)
    bpy.utils.unregister_class(BPPS_Modal_Timer)
    
    del bpy.types.Scene.bpps_states
    
    print("BPPS unloaded")

if __name__ == "__main__":
    register()