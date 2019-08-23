#blender 2.80
import bpy
import mathutils
import numpy as np
import blfuncs

print("start the script")
objdict = {}

def skip(f):
    print('skip the function: ', f.__name__)
    return



objdict['actObj'] = bpy.context.active_object
vertices, polygons, objlocation = getobjdata(objdict['actObj'], glo=False)
objdict["normsVerArr"] = drawsemiArrowsVer("normsVerArr", objlocation, vertices, polygons)
objdict["normVerPlane"] = extrudeVertsToplane("normVerPlane",
                                              objdict['actObj'], 0.2)
objdict["normVerPlane"] = extrudeVertsToplane("normVerPlane",
                                              objdict['actObj'], -0.2)

#objdict["normsPolArr"] = drawsemiArrowsPol("normsPol", objlocation, vertices, polygons)
print(objdict)

#Refs
#https://sinestesia.co/blog/tutorials/extruding-meshes-with-bmesh/
#https://stackoverflow.com/questions/54006078/selection-of-face-of-a-stl-by-face-normal-value-threshold/54029819#54029819

#for debuging
#bpy.app.debug_wm = True
#https://docs.blender.org/api/blender_python_api_2_77_1/info_tips_and_tricks.html
#import code
#code.interact(local=locals())
#global debuging
#__import__('code').interact(local=dict(globals(), **locals()))
