# parametric sphere: not finised, something wrong

import bpy
import math
import mathutils
import numpy as np
import transformations


r = 1
vertices = np.ndarray((64800,3))

for u in range (0,180):
	ur=math.radians(u)
	for v in range (0,360):
		vr=math.radians(v)
		x = r*math.sin(ur)*math.cos(vr) 
		y = r*math.sin(ur)*math.sin(vr) 
		z = r*math.cos(vr) 
		vertices[u*360+v] = [x,y,z]


R = transformations.rotation_matrix(math.pi/2, [0, 0, 1], [0, 0, 0])

for i in range (0, len(vertices)):
	vertices[i] = np.dot(R,np.append(vertices[i],[1]))[:3]

print(vertices)


# S(u,v)=[rsinucosv,rsinusinv,rcosv]


# vertices = np.ndarray((v,3))
# polygons = np.ndarray((n,m), dtype = int)


# # #creat newobject from vertice and polygons
newmesh = bpy.data.meshes.new("mymesh")
myobject = bpy.data.objects.new("mymesh", newmesh)

# # #set mesh location
myobject.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(myobject)

# # #create mesh from python data
newmesh.from_pydata(vertices,[],[])
newmesh.update(calc_edges=True)

