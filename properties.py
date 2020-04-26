import bpy
from . import flameio


def update_image_handler(self, obj):
    obj = bpy.context.active_object
    if obj is None:
        return
    if obj.flame_object_type == "flame":
        flameio.update_image(obj)
    elif obj.flame_object_type == "xform":
        flameio.update_image(obj.parent)


class XFormProperties(bpy.types.PropertyGroup):
    enable_xform: bpy.props.BoolProperty(update=update_image_handler)
    filter_string: bpy.props.StringProperty()
    show_prepost: bpy.props.EnumProperty(
        items=(("0", "Normal", "Normal"), ("1", "Pre", "Pre"), ("1", "Post", "Post"))
    )


class XFormVariations(bpy.types.PropertyGroup):
    place_holder: bpy.props.BoolProperty()


vdata = flameio.load_variations()
for name, default in vdata["affine_vars"].items():
    XFormVariations.__annotations__[name] = bpy.props.FloatProperty(
        default=default, update=update_image_handler
    )

for name, default in vdata["normal_vars"].items():
    XFormVariations.__annotations__[name] = bpy.props.FloatProperty(
        default=default, update=update_image_handler
    )

for name, default in vdata["variations"].items():
    XFormVariations.__annotations__[name] = bpy.props.FloatProperty(
        default=default, update=update_image_handler
    )


class FlameProperties(bpy.types.PropertyGroup):
    import_path: bpy.props.StringProperty()
    custom_flame_as_base: bpy.props.BoolProperty(default=True, update=update_image_handler)
    auto_update_preview: bpy.props.BoolProperty(default=True, update=update_image_handler)


for name, default in vdata["flame_settings"].items():
    if type(default) == type(0.0):
        FlameProperties.__annotations__[name] = bpy.props.FloatProperty(
            default=default, update=update_image_handler
        )
    else:
        FlameProperties.__annotations__[name] = bpy.props.StringProperty(
            default=default, update=update_image_handler
        )


class FlamePreviewSettings(bpy.types.PropertyGroup):
    demax: bpy.props.FloatProperty(default=2, update=update_image_handler)
    supersample: bpy.props.FloatProperty(default=1, update=update_image_handler)
    opencl: bpy.props.BoolProperty(default=True, update=update_image_handler)
    quality: bpy.props.FloatProperty(default=10, update=update_image_handler)
    scale: bpy.props.FloatProperty(default=0.5, update=update_image_handler)
    import_path: bpy.props.StringProperty(default="")


def register():

    bpy.utils.register_class(XFormProperties)
    bpy.utils.register_class(FlamePreviewSettings)
    bpy.utils.register_class(XFormVariations)
    bpy.utils.register_class(FlameProperties)

    bpy.types.Object.xform = bpy.props.PointerProperty(type=XFormProperties)
    bpy.types.Object.xform_var = bpy.props.PointerProperty(type=XFormVariations)
    bpy.types.Object.flame = bpy.props.PointerProperty(type=FlameProperties)
    bpy.types.Object.flame_object_type = bpy.props.StringProperty()

    bpy.types.Scene.flame_preview = bpy.props.PointerProperty(type=FlamePreviewSettings)


def unregister():

    bpy.utils.unregister_class(XFormProperties)
    bpy.utils.unregister_class(FlamePreviewSettings)
    bpy.utils.unregister_class(XFormVariations)
    bpy.utils.unregister_class(FlameProperties)


if __name__ == "__main__":
    register()
