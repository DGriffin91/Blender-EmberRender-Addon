import bpy
from . import flameio


class FlamePreviewPanel(bpy.types.Panel):
    bl_label = "Flame Preview"
    bl_idname = "OBJECT_PT_flamepreview"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        row = layout.row()
        row.label(text="Flame Editor", icon="WORLD_DATA")

        row = layout.row()
        row.label(text="Preview Settings")
        row = layout.row()
        row.prop(scn.flame_preview, "demax", text="demax")
        row = layout.row()
        row.prop(scn.flame_preview, "supersample", text="supersample")
        row = layout.row()
        row.prop(scn.flame_preview, "opencl", text="opencl")
        row = layout.row()
        row.prop(scn.flame_preview, "quality", text="quality")
        row = layout.row()
        row.prop(scn.flame_preview, "scale", text="resolution scale")

        layout.row()
        layout.row()
        layout.row()
        row = layout.row()


class FlameMainPanel(bpy.types.Panel):
    bl_label = "Flame"
    bl_idname = "OBJECT_PT_flamemain"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        obj = context.object

        if "flame_object_type" not in obj:
            return

        layout = self.layout

        row = layout.row()
        row.label(text="Main Settings")

        child_selected = False
        flame_obj = obj
        if obj.flame_object_type != "flame":
            if obj.flame_object_type == "xform":
                child_selected = True
                flame_obj = obj.parent
            else:
                return

        row = layout.row()
        row.prop(flame_obj.flame, "auto_update_preview", text="Auto Update Preview")

        tex_name = f"flame_temp_view_image{flame_obj.name}.exr"
        if tex_name in bpy.data.textures:
            tex = bpy.data.textures[tex_name]
            col = layout.box().column()
            col.template_preview(tex)

        if child_selected:
            return

        row = layout.row()
        row.prop(flame_obj.flame, "custom_flame_as_base", text="Use custom flame as base")
        row = layout.row()
        row.prop(flame_obj.flame, "import_path", text="Flame Path")
        for name in obj["vdata"]["flame_settings"]:
            row = layout.row()
            row.prop(flame_obj.flame, name, text=name.replace("_", " "))


def draw_variations_ui_list(layout, obj, only_existing, use_filter):
    filter_string = obj.xform.get("filter_string", "")
    vdata = obj.parent["vdata"]
    if only_existing:
        for name in vdata["variations"]:
            if only_existing and not name in obj.xform_var:
                continue
            row = layout.row()
            if name in vdata["main_variations"]:
                row.prop(obj.xform_var, name, text=name.replace("_", " "))
            else:
                row.prop(obj.xform_var, name, text=f" |     {name.replace('_', ' ')}")

    else:
        for name in vdata["main_variations"]:
            pre_post_mode = obj.xform.get("show_prepost")
            startswith_pre = name.startswith("pre_")
            startswith_post = name.startswith("post_")
            if pre_post_mode == 0 and (startswith_pre or startswith_post):
                continue
            if pre_post_mode == 1 and not startswith_pre:
                continue
            if pre_post_mode == 2 and not startswith_post:
                continue
            if name not in obj.xform_var and (filter_string == "" or filter_string in name):
                row = layout.row()
                row.prop(obj.xform_var, name, text=name.replace("_", " "))


class XformPanel(bpy.types.Panel):
    bl_label = "XForm"
    bl_idname = "OBJECT_PT_flamexform"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        obj = context.object
        if "flame_object_type" not in obj:
            return

        layout = self.layout

        row = layout.row()
        row.label(text="XForm Editor", icon="WORLD_DATA")

        if obj.flame_object_type != "xform":
            return

        row = layout.row()
        row.label(text="Active object is: " + obj.name)

        row = layout.row()
        row.prop(obj.xform, "enable_xform", text="enable_xform")

        layout.row()
        layout.row()

        row = layout.row()
        row.label(text="Affine Transforms")
        row = layout.row()
        row.prop(obj.xform_var, "coef_x1", text="x1")
        row.prop(obj.xform_var, "coef_x2", text="x2")
        row = layout.row()
        row.prop(obj.xform_var, "coef_y1", text="y1")
        row.prop(obj.xform_var, "coef_y2", text="y2")
        row = layout.row()
        row.prop(obj.xform_var, "coef_o1", text="o1")
        row.prop(obj.xform_var, "coef_o2", text="o2")

        layout.row()
        layout.row()

        row = layout.row()
        row.label(text="Standard Options")

        if not obj.parent or "vdata" not in obj.parent:
            return

        for name in obj.parent["vdata"]["normal_vars"]:
            row = layout.row()
            row.prop(obj.xform_var, name, text=name)

        layout.row()
        layout.row()
        row = layout.row()

        row.label(text="Variations in use")

        draw_variations_ui_list(layout, obj, True, False)
        layout.row()
        layout.row()
        layout.row()
        layout.row()
        row = layout.row()
        row.label(text="Available Variations")
        row.prop(obj.xform, "filter_string", text=f"Filter")
        row = layout.row()
        row.prop(obj.xform, "show_prepost", expand=True)

        draw_variations_ui_list(layout, obj, False, True)


def register():
    bpy.utils.register_class(FlamePreviewPanel)
    bpy.utils.register_class(FlameMainPanel)
    bpy.utils.register_class(XformPanel)


def unregister():
    bpy.utils.unregister_class(FlamePreviewPanel)
    bpy.utils.unregister_class(FlameMainPanel)
    bpy.utils.unregister_class(XformPanel)


if __name__ == "__main__":
    register()
