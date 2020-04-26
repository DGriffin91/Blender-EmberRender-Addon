import bpy
import json
import threading
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import os
import sys


"""
Note: imported flames wont match exactly as 
the order of the variations apparently, actually matters

TODO:
Batch render from blender
File dialog and progressbar for export flame animation
Export single flame
Maintain variations order
Disable variations
Progressive Quality Steps 1, 10, 100?
"""


# Tried to make this not global, the issue is
# these are accessed on the callback of the render
# thread and it can't access bpy.context.scene
global render_status
render_status = {
    "currently_rendering": False,
    "que_render": False,
    "exporting_all": False,
}


def addon_path():
    return Path(os.path.dirname(os.path.realpath(__file__)))


def popen_and_call(on_exit, popen_args, obj):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    on_exit when the subprocess completes.
    on_exit is a callable object, and popen_args is a list/tuple of args that 
    would give to subprocess.Popen.
    """

    def run_in_thread(on_exit, popen_args):
        # try:
        proc = subprocess.Popen(popen_args, bufsize=0)
        proc.wait()
        on_exit(obj)
        # except:
        # print("Render failed", sys.exc_info()[0])
        return

    thread = threading.Thread(target=run_in_thread, args=(on_exit, popen_args))
    thread.start()
    # returns immediately after the thread starts
    return thread


def load_variations():

    with open(addon_path() / "variations_list.json") as f:
        variations = json.load(f)

    mainv = {}
    prev = {}
    postv = {}

    for k, v in variations.items():
        if k.startswith("pre"):
            prev[k] = v
        elif k.startswith("post"):
            postv[k] = v
        else:
            mainv[k] = v

    mainv.update(prev)
    mainv.update(postv)

    variations = mainv

    main_variations = []

    for k in variations.keys():
        if variations[k] == "9":
            variations[k] = 0.0
            main_variations.append(k)
        else:
            variations[k] = float(variations[k])
    vdata = {}
    vdata["main_variations"] = main_variations
    vdata["variations"] = variations
    vdata["normal_vars"] = {
        "weight": 1,
        "color": 1,
        "opacity": 1,
        "var_color": 0,
        "color_speed": 0.5,
        "symmetry": 0,
        "name": 0,
    }

    vdata["flame_settings"] = {
        "version": "EMBER-WIN-1.0.0.19",
        "time": "0",
        "name": "Flame",
        "size": "1920 1080",
        "center": "0 0",
        "scale": "240",
        "rotate": "0",
        "supersample": "2",
        "filter": "1",
        "filter_shape": "gaussian",
        "temporal_filter_type": "gaussian",
        "temporal_filter_width": "1",
        "quality": "1000",
        "temporal_samples": "100",
        "sub_batch_size": "10240",
        "fuse": "15",
        "rand_range": "1",
        "background": "0 0 0",
        "brightness": "4",
        "gamma": "4",
        "highlight_power": "1",
        "logscale_k2": "0",
        "vibrancy": "1",
        "estimator_radius": "0",
        "estimator_minimum": "0",
        "estimator_curve": "0.4",
        "gamma_threshold": "0.1",
        "cam_zpos": "0",
        "cam_persp": "0",
        "cam_yaw": "0",
        "cam_pitch": "0",
        "cam_dof": "0",
        "blur_curve": "0",
        "palette_mode": "linear",
        "interpolation": "smooth",
        "interpolation_type": "log",
        "plugins": "linear",
        "new_linear": "1",
        "curves": "0 0 1 0.25 0.25 1 0.5 0.5 1 0.75 0.75 1 0 0 1 0.25 0.25 1 0.5 0.5 1 0.75 0.75 1 0 0 1 0.25 0.25 1 0.5 0.5 1 0.75 0.75 1 0 0 1 0.25 0.25 1 0.5 0.5 1 0.75 0.75 1 ",
        "overall_curve": "0 0 0.25 0.25 0.5 0.5 0.75 0.75 1 1 ",
        "red_curve": "0 0 0.25 0.25 0.5 0.5 0.75 0.75 1 1 ",
        "green_curve": "0 0 0.25 0.25 0.5 0.5 0.75 0.75 1 1 ",
        "blue_curve": "0 0 0.25 0.25 0.5 0.5 0.75 0.75 1 1 ",
    }

    for k, v in vdata["flame_settings"].items():
        try:
            vdata["flame_settings"][k] = float(v)
        except ValueError:
            pass

    vdata["affine_vars"] = {
        "coef_x1": 1,
        "coef_x2": 0,
        "coef_y1": 0,
        "coef_y2": 1,
        "coef_o1": 0,
        "coef_o2": 0,
    }

    return vdata


def get_children(context, ob):
    return [ob_child for ob_child in context.scene.objects if ob_child.parent == ob]


def export_flame_animation(context):
    scn = context.scene
    render_status["exporting_all"] = True
    current_frame = scn.frame_current
    start = scn.frame_start
    end = scn.frame_end

    root_path = Path(bpy.path.abspath("//"))
    for i in range(start, end):
        scn.frame_set(i)
        export(context.object, root_path / f"output{i}.flame")

    scn.frame_current = current_frame
    render_status["exporting_all"] = False


def export(flame_obj, file_path):
    if flame_obj is None:
        return
    if flame_obj.flame_object_type == "xform":
        flame_obj = flame_obj.parent
    if flame_obj.flame_object_type != "flame":
        return
    import_path = flame_obj.flame.get("import_path")
    import_path = Path(import_path) if import_path else Path("")
    if flame_obj.flame.get("custom_flame_as_base") and import_path.is_file():
        tree = ET.parse(import_path)
    else:
        tree = ET.parse(addon_path() / "template.flame")

    root = tree.getroot()
    for child in root:
        if child.tag == "flame":
            root = child
            break

    to_be_removed = []
    for child in root:
        if child.tag == "xform":
            to_be_removed.append(child)
    for child in to_be_removed:
        root.remove(child)

    for name, default in flame_obj["vdata"]["flame_settings"].items():
        if name in flame_obj.flame:
            root.attrib[name] = str(flame_obj.flame[name])
        else:
            root.attrib[name] = str(default)

    xforms = []
    for obj in get_children(bpy.context, flame_obj):
        if obj.flame_object_type != "xform":
            continue
        if not obj.xform.get("enable_xform"):
            continue
        items = {}
        for name, default in flame_obj["vdata"]["normal_vars"].items():
            if name in obj.xform_var:
                items[name] = str(obj.xform_var[name])
            else:
                items[name] = str(default)

        current_v = ""
        current_exists = False
        for name in flame_obj["vdata"]["variations"]:
            if name not in flame_obj["vdata"]["main_variations"] and current_exists:
                s = name[len(current_v) + 1 :]
                if name in obj.xform_var:
                    items[name] = str(obj.xform_var[name])
                else:
                    items[name] = str(flame_obj["vdata"]["variations"][name])

            else:
                current_exists = name in obj.xform_var
                if current_exists:
                    items[name] = str(obj.xform_var[name])
                current_v = name

        coefs = []
        for name, default in flame_obj["vdata"]["affine_vars"].items():
            coef = default
            if name in obj.xform_var:
                coef = obj.xform_var[name]
            coefs.append(str(coef))
        items["coefs"] = " ".join(coefs)

        xforms.append(items)

    for xform in xforms:
        ET.SubElement(root, "xform", attrib=xform)

    myfile = open(file_path, "w")
    myfile.write(ET.tostring(root, method="xml", encoding="unicode"))


def import_flame(context, file_path):
    scn = bpy.context.scene
    tree = ET.parse(file_path)
    root = tree.getroot()
    flame = root
    for child in root:
        if child.tag == "flame":
            flame = child

    flame_obj = bpy.data.objects.new("flame", None)
    scn.collection.objects.link(flame_obj)
    flame_obj.empty_display_size = 2
    flame_obj.empty_display_type = "PLAIN_AXES"
    flame_obj.flame_object_type = "flame"
    flame_obj.flame.import_path = str(file_path)
    flame_obj["vdata"] = load_variations()

    for name, default in flame_obj["vdata"]["flame_settings"].items():
        if name in flame.attrib:
            val = flame.attrib[name]
        else:
            val = default
        try:
            val = float(val)
        except ValueError:
            pass
        flame_obj.flame[name] = val

    for child in flame:
        if child.tag == "xform":
            obj = bpy.data.objects.new("xform", None)
            scn.collection.objects.link(obj)
            obj.empty_display_size = 2
            obj.empty_display_type = "PLAIN_AXES"
            obj.flame_object_type = "xform"
            obj.parent = flame_obj
            for name, val in child.attrib.items():
                try:
                    val = float(val)
                except ValueError:
                    pass
                if name in flame_obj["vdata"]["normal_vars"].keys():
                    obj.xform_var[name] = val
                elif name in flame_obj["vdata"]["variations"].keys():
                    obj.xform_var[name] = val
                elif name == "coefs":
                    coords = val.split(" ")
                    coords = [float(c) for c in coords]
                    print(coords)
                    obj.xform_var["coef_x1"] = coords[0]
                    obj.xform_var["coef_x2"] = coords[1]
                    obj.xform_var["coef_y1"] = coords[2]
                    obj.xform_var["coef_y2"] = coords[3]
                    obj.xform_var["coef_o1"] = coords[4]
                    obj.xform_var["coef_o2"] = coords[5]
            obj.xform["enable_xform"] = True

    update_image(flame_obj)


def refresh_views():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            # for area in bpy.context.screen.areas:
            if area.type in ["IMAGE_EDITOR", "VIEW_3D"]:
                area.tag_redraw()


def refresh_image(obj):
    if bpy.path.abspath("//") == "":
        return
    root_path = Path(bpy.path.abspath("//"))
    temp_image_name = f"flame_temp_view_image{obj.name}.exr"
    temp_image_path = root_path / temp_image_name

    if not temp_image_path.is_file():
        print(f"No file {temp_image_path} found")
        return
    if temp_image_name not in bpy.data.images:
        bpy.data.images.load(str(temp_image_path), check_existing=True)
    else:
        bpy.data.images[temp_image_name].reload()

    if temp_image_name not in bpy.data.textures:
        ui_tex = bpy.data.textures.new(temp_image_name, "IMAGE")
        ui_tex.extension = "CLIP"
    else:
        ui_tex = bpy.data.textures[temp_image_name]

    try:
        ui_tex.image = bpy.data.images[temp_image_name]
    except AttributeError:
        print("Incorrect context", sys.exc_info())

    scn = bpy.context.scene
    refresh_views()
    render_status["currently_rendering"] = False
    if render_status["que_render"]:
        render_status["que_render"] = False
        update_image(obj)


def update_image(obj):
    scn = bpy.context.scene
    if not obj.flame.auto_update_preview:
        return
    if bpy.path.abspath("//") == "" or render_status["exporting_all"]:
        return
    if render_status["currently_rendering"]:
        render_status["que_render"] = True
        return
    root_path = Path(bpy.path.abspath("//"))
    temp_flame_path = root_path / f"flame_temp_view{obj.name}.flame"
    temp_image_name = f"flame_temp_view_image{obj.name}.exr"
    temp_image_path = root_path / temp_image_name
    export(obj, temp_flame_path)
    scale = 0.5
    renderer_path = str(addon_path() / "Fractorium/EmberRender.exe")
    # cmd = f"--in={temp_flame_path} --out={temp_image_path} --opencl --quality=0.3 --supersample=1  --demax=2 --ss=0.5 --sp --format=exr"

    fp = scn.flame_preview

    cmd = (
        f"--in={temp_flame_path}",
        f" --ss={fp.scale}",
        f" --out={temp_image_path}",
        f" --demax={fp.demax}",
        f" --supersample={fp.supersample}",
        " --sp",
        " --opencl" if fp.opencl else "",
        f" --quality={fp.quality}",
        f" --ss={fp.scale}",
        " --format=exr",
    )
    popen_and_call(refresh_image, (renderer_path, cmd), obj)
    render_status["currently_rendering"] = True
