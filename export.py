#!BPY

"""
Name: 'Wikibooks'
Blender: 259
Group: 'Export'
Tooltip: 'Wikibooks sample exporter'
"""
import Blender
import bpy

def write(filename):
    out = open(filename, "w")
    sce= bpy.data.scenes.active
    for ob in sce.objects:
        out.write(ob.type + ": " + ob.name + "\n")
    out.close()

Blender.Window.FileSelector(write, "Export")