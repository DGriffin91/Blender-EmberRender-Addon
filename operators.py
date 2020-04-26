import bpy
from pathlib import Path
import os
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras.io_utils import ImportHelper


from . import flameio


def addon_path():
    return Path(os.path.dirname(os.path.realpath(__file__)))


class ExportFlameAnimationOperator(bpy.types.Operator):
    """Tooltip"""

    bl_idname = "object.export_flame_animation_operator"
    bl_label = "Export Flame Animation"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        flameio.export_flame_animation(context)

        return {"FINISHED"}


class ImportFlameData(bpy.types.Operator, ImportHelper):
    """Import Flame File"""

    bl_idname = "import.flame_data"
    bl_label = "Import Flame Data"

    filename_ext = ".flame"

    filter_glob: bpy.props.StringProperty(
        default="*.flame", options={"HIDDEN"}, maxlen=255,
    )

    def execute(self, context):
        flameio.import_flame(context, self.filepath)
        return {"FINISHED"}


def menu_func_flame_import(self, context):
    self.layout.operator(ImportFlameData.bl_idname, text="Import Flame Data")


class OBJECT_OT_add_flame_object(bpy.types.Operator, AddObjectHelper):
    """Create a new Flame Object"""

    bl_idname = "mesh.add_flame_object"
    bl_label = "Add Flame Object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        flameio.import_flame(context, addon_path() / "template.flame")

        return {"FINISHED"}


# Registration


def add_flame_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_flame_object.bl_idname, text="Add Flame Object", icon="PLUGIN"
    )


def register():
    bpy.utils.register_class(OBJECT_OT_add_flame_object)
    bpy.types.VIEW3D_MT_mesh_add.append(add_flame_object_button)

    bpy.utils.register_class(ImportFlameData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_flame_import)

    bpy.utils.register_class(ExportFlameAnimationOperator)

    bpy.types.Object.flame_object_type = bpy.props.StringProperty()


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_flame_object)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_flame_object_button)

    bpy.utils.unregister_class(ImportFlameData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_flame_import)

    bpy.utils.unregister_class(ExportFlameAnimationOperator)


if __name__ == "__main__":
    register()
