import bpy
import math
# mesh arrays
verts = []  # the vertex array
faces = []  # the face array
 
# mesh variables
numX = 10  # number of quadrants in the x direction
numY = 10  # number of quadrants in the y direction
 
# wave variables
freq = 1  # the wave frequency
amp = 1  # the wave amplitude
scale = 1  #the scale of the mesh
#fill verts array
for i in range (0, numX):
    for j in range(0,numY):
 
        x = scale * i
        y = scale * j
        z = scale *((amp*math.cos(i*freq))+(amp*math.sin(j*freq)))
 
        vert = (x,y,z) 
        verts.append(vert)
 
#create mesh and object
mesh = bpy.data.meshes.new("wave")
object = bpy.data.objects.new("wave",mesh)

#fill faces array
count = 0
for i in range (0, numY *(numX-1)):
    if count < numY-1:
        A = i  # the first vertex
        B = i+1  # the second vertex
        C = (i+numY)+1 # the third vertex
        D = (i+numY) # the fourth vertex
 
        face = (A,B,C,D)
        faces.append(face)
        count = count + 1
    else:
        count = 0
        
#set mesh location
object.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(object)
 
#create mesh from python data
mesh.from_pydata(verts,[],faces)
mesh.update(calc_edges=True)
