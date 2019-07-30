# duplicate a mesh
import os
import bpy
import math
import mathutils
import numpy as np
import csv
from fastnumbers import fast_float, float as fnfloat


import bmesh
import mathutils
from mathutils import Vector

def resultantforce(x, y, z):
    return math.sqrt(x**2 + y**2 + z**2)

# Cut input dat file to coordinates file
def cutfile(inputfile, str1, str2, distance, outputfile): 
    with open(dir+'\\'+ inputfile, 'r', newline='\n') as ifile: #\n error in python 27
        csvfile = csv.reader(ifile)
        with open(dir+'\\'+'temp.csv', "w+", newline='\n') as ofile:
        # cant use wb+--> cause error: a bytes-like object is required, not 'str'; put \n for prevent blank line
            csvwrite = csv.writer(ofile)
            # csvwrite = csv.writer(ofile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            for row in csvfile:
                if str2 in row: # chuoi geometry nam trong row ---> stop writting file
                    break
                csvwrite.writerow(row)

    with open(dir+'\\'+'temp.csv', "r+", newline='\n') as ofile:
        csvfile2 = csv.reader(ofile)
        with open(dir+'\\'+outputfile, "w+", newline='\n') as ofile2:
            csvwrite2 = csv.writer(ofile2)
            n = 0
            for row in csvfile2:
                if str1 not in row:
                    if n >= 1 and n<=distance: 
                        n +=1
                        continue
                    elif n == distance + 1: 
                        csvwrite2.writerow(row)
                    continue
                if str1 in row:
                    n = 1
                    continue #csvwrite2.writerow(row) (pass by the line which includes str1)

# def getcoordlist(filename):
#     with open (dir + '\\' + filename, 'r' ) as coord:
#         coordlist = list(csv.reader(coord, delimiter = ','))
#     # Delete column
#         for sublist in coordlist:
#             del sublist [0]
#             del sublist [3]
#     #convert to float an then numpy array
#         for i in range(len(coordlist)):
#             coordlist[i][0] = fast_float(coordlist[i][0])
#             coordlist[i][1] = fast_float(coordlist[i][1])
#             coordlist[i][2] = fast_float(coordlist[i][2])
#             # print(coordlist[i][0],coordlist[i][1],coordlist[i][2])
#             # print(type(coordlist[i][0]),type(coordlist[i][1]),type(coordlist[i][2]))
#         coordlist = np.array(coordlist)
#     return coordlist

def getcoordlist(file):
    with open (file, 'r' ) as coord:
        coordlist = list(csv.reader(coord, delimiter = ','))
    # Delete column
        for sublist in coordlist:
            del sublist [0]
            del sublist [3]
    #convert to float an then numpy array
        for i in range(len(coordlist)):
            coordlist[i][0] = fast_float(coordlist[i][0])
            coordlist[i][1] = fast_float(coordlist[i][1])
            coordlist[i][2] = fast_float(coordlist[i][2])
            # print(coordlist[i][0],coordlist[i][1],coordlist[i][2])
            # print(type(coordlist[i][0]),type(coordlist[i][1]),type(coordlist[i][2]))
        coordlist = np.array(coordlist)
    return coordlist

def getconnectivity(file):
    with open (file, 'r' ) as coord:
        conn = list(csv.reader(coord, delimiter = ','))
    # convert to int --> not successful
        # for row  in conn:
        #     del row[-1] #del the last column of row since cant int
        #     for column in row:
        #         column = int(column)
        face = []
        # Delete column
        for row in conn:
            # i=i+1
            if int(row[1]) == 134:
                # print ('found element 134')
                del row[-1]
                del row[1] #should delete from higher id first as id will change after del
                del row[0] 
                face.append( [int(row[0])-1,int(row[1])-1,int(row[2])-1]) 
                face.append( [int(row[0])-1,int(row[3])-1,int(row[1])-1]) 
                face.append( [int(row[0])-1,int(row[2])-1,int(row[3])-1]) 
                face.append( [int(row[2])-1,int(row[1])-1,int(row[3])-1]) 

            elif int(row[1]) == 7:
                # print ('found element 7')
                del row[-1]
                del row[6] 
                del row[2] 
                del row[1] 
                del row[0] 
                face.append( [int(row[2])-1,int(row[5])-1,int(row[3])-1,int(row[0])-1]) 
                face.append( [int(row[3])-1,int(row[4])-1,int(row[1])-1,int(row[0])-1]) 
                face.append( [int(row[4])-1,int(row[5])-1,int(row[2])-1,int(row[1])-1]) 
                face.append( [int(row[5])-1,int(row[4])-1,int(row[3])-1]) 
                face.append( [int(row[2])-1,int(row[1])-1,int(row[0])-1]) 
            else:
                print ('No defined element')
    return face

def createobj (name, nodelist, facelist): #create obj from nodes and faces
    #create mesh from python data
    newmesh = bpy.data.meshes.new("mymesh")
    myobject = bpy.data.objects.new("mymesh", newmesh)
    myobject.show_name = True
    bpy.context.scene.objects.link(myobject)
    newmesh.from_pydata(nodelist,[],facelist)   #If equivalent was condcuct --> error in display elements
    # newmesh.from_pydata(nodelist,[],[])
    newmesh.update()
    #Can show the surface model by unique the face list
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.unique.html

# *******************-------Display arrow----------************************
def force_arrow(positioner_vector, force_vector, offset_original, arrow_length):

    scene = bpy.context.scene
    objects = bpy.data.objects
    arrow_stem_mesh = objects['Arrow_stem'].data
    arrow_cone_mesh = objects['Arrow_cone'].data

    head=[0,0,0]
    tail = positioner_vector
    head = mathutils.Vector(head) 
    tail = mathutils.Vector(tail) 

    #normalize vector
    len_vector = math.sqrt(force_vector[0]**2 + force_vector[1]**2 + force_vector[2]**2)
    dx = force_vector[0] / len_vector
    dy = force_vector[1] / len_vector
    dz = force_vector[2] / len_vector

    #move the tail along the vector. Input the distance offset from positioner vector
    tail[0] = tail[0] + offset_original * dx
    tail[1] = tail[1] + offset_original * dy
    tail[2] = tail[2] + offset_original * dz

    #find the end point
    head[0] = tail[0] + arrow_length * dx
    head[1] = tail[1] + arrow_length * dy
    head[2] = tail[2] + arrow_length * dz

    # Scale the Stem, and add to scene
    obj = bpy.data.objects.new("Arrow_duplicate", arrow_stem_mesh)
    obj.location = tail
    obj.scale = (1, 1, (head-tail).length)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = (head-tail).to_track_quat('Z','Y')
    scene.objects.link(obj)

    # orient Cone, and add to scene
    obj2 = bpy.data.objects.new("Arrow_duplicate", arrow_cone_mesh)
    obj2.location = head   # start at tail and work back
    obj2.scale = (1.5, 1.5, 1.5)
    obj2.rotation_mode = 'QUATERNION'
    #to_track_quat(track, up) Return a quaternion rotation from the vector and the track and up axis.
    obj2.rotation_quaternion = (head-tail).to_track_quat('Z','Y') 
    scene.objects.link(obj2)

def moment_arrow(loc, axis, momentname): #displace moment arrow as its location and axis (moment vector)
    loc = mathutils.Vector(loc)
    axis = mathutils.Vector(axis)
    
    scene = bpy.context.scene
    objects = bpy.data.objects
    Helix_mesh = objects['Helix'].data
    obj = bpy.data.objects.new(momentname, Helix_mesh)
    obj.location = loc
    obj.scale = (3, 3, 3)
    
    obj.rotation_mode = 'QUATERNION'
    #to_track_quat(track, up)
    #Return a quaternion rotation from the vector and the track and up axis.
    obj.rotation_quaternion = axis.to_track_quat('-Z','Y') # positive axis--> CW rotation
    scene.objects.link(obj)

def moment_to_point(location, force, forcepoint): # calculate moment vector to a Point base on Force and force location
    location = mathutils.Vector(location)
    forcepoint = mathutils.Vector(forcepoint)
    rAB = forcepoint - location
    m = np.cross(force, rAB)
    return m


def main():
    dir = 'd:\Blender\WIOC2017\\'

    #***************Cut file*******************************************
    
    # cutfile("model.dat", "COORDINATES", "END OPTION", 1, "coordinates.dat")
    # cutfile("model.dat", "CONNECTIVITY", "NO PRINT", 1, "connectivity.dat")


    #**************--------End display mesh------------************************
    # node = getcoordlist(dir + 'coordinates.dat')
    # face = getconnectivity(dir + 'connectivity.dat')
    # createobj('newmesh', node, face)

    positioner_vector = ([ -2.25531435,   0.38953869,  21.31139493])
    force_vector = (0.0005453119520097971, 3.442968354385812, -0.06287432374483615)
    # force_vector = (0-force_vector[0], 0-force_vector[1], 0-force_vector[2]) #use to calculate oppsite vector
    force_scalar = resultantforce(force_vector[0], force_vector[1], force_vector [2])

    offset_original = 12 #position of the vector from the original place
    arrow_length = 10
    curloc = bpy.context.scene.cursor_location

    # force_arrow(positioner_vector, force_vector, offset_original , arrow_length) #display force without moment
    # force_arrow(curloc, force_vector, 0, arrow_length) #display arrow at cursor position

    moment_vector = moment_to_point(curloc, force_vector, positioner_vector)
    momentscalar = resultantforce(moment_vector[0], moment_vector[1], moment_vector[2]) #convert magnitude to moment name
    MF = momentscalar / force_scalar    #calculate M/F at the cursor point
    momentname = repr(round(momentscalar,4)) + '-' + 'M/F:' + repr(round(MF,4))
    moment_arrow(curloc, moment_vector, momentname)	#display moment at cursor_location
 

if __name__ == '__main__':
    main()
