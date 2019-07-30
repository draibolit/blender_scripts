import bpy
import random
 
# mesh arrays
verts = []
faces = []
 
# mesh variables
numX = 20
numY = 20
 
# wave variables
amp = 0.5
scale = 1
 
#fill verts array
for i in range (0, numX):
    for j in range(0,numY):
 
        x = scale * i
        y = scale * j
        z = (i*random.random())*amp
 
        vert = (x,y,z) 
        verts.append(vert)
 
#fill faces array
count = 0
for i in range (0, numY *(numX-1)):
    if count < numY-1:
        A = i
        B = i+1
        C = (i+numY)+1
        D = (i+numY)
 
        face = (A,B,C,D)
        faces.append(face)
        count = count + 1
    else:
        count = 0
 
#create mesh and object
mymesh = bpy.data.meshes.new("random mesh")
myobject = bpy.data.objects.new("random mesh",mymesh)
 
#set mesh location
myobject.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(myobject)
 
#create mesh from python data
mymesh.from_pydata(verts,[],faces)
mymesh.update(calc_edges=True)
 
# subdivide modifier
myobject.modifiers.new("subd", type='SUBSURF')
myobject.modifiers['subd'].levels = 3
 
# show mesh as smooth
mypolys = mymesh.polygons
for p in mypolys:
    p.use_smooth = True