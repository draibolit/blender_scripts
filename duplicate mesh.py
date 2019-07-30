# duplicate a mesh

import bpy
import math
import mathutils
import numpy as np

#get active object name
objname = bpy.context.active_object.name
objdata = bpy.data.meshes[objname]

#get matrix of polygons and their vertices coord
n = len(objdata.polygons)
m = len(objdata.polygons[0].vertices)
v = m*n

vertices = np.ndarray((v,3))
polygons = np.ndarray((n,m), dtype = int)

for i in range (0, len(objdata.polygons)):
	k = 0
	for j in objdata.polygons[i].vertices:
		vertices[j]=objdata.vertices[j].co #---> same vertice in different polygons
		polygons[i,k]=j
		k += 1
		# print("polygon", i,"have vertice no",j )


print (polygons.tolist())


# # #creat newobject from vertice and polygons
newmesh = bpy.data.meshes.new("mymesh")
myobject = bpy.data.objects.new("mymesh", newmesh)

# # #set mesh location
myobject.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(myobject)

# # #create mesh from python data
newmesh.from_pydata(vertices,[],polygons.tolist())
newmesh.update(calc_edges=True)

