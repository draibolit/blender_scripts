# creat normal mesh

import bpy
import math
import mathutils
import numpy as np

vertices = [(1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
			(1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)]

# edges = [(0, 1),(0, 3),	(0, 4),	(2, 1),	(2, 3),	(2, 7),
# 	(6, 3),	(6, 4),	(6, 7),	(5, 1),	(5, 4),	(5, 7)]

polygons = [(0,1,2,3), (3,2,7,6), (6,7,5,4), (4,5,1,0), (1,5,7,2), (4,0,3,6)]


# #creat newobject from vertice and polygons
newmesh = bpy.data.meshes.new("mymesh")
myobject = bpy.data.objects.new("mymesh", newmesh)

# #set mesh location
myobject.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(myobject)

# #create mesh from python data
newmesh.from_pydata(vertices,[],polygons)
newmesh.update(calc_edges=True)

