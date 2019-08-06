#blender 2.80
import bpy
import mathutils
import numpy as np


print("start the script")
objdict = {}

def skip(f):
    print('skip the function: ', f.__name__)
    return

def newobj(name, location, vertices, edge, polygons):

    #set mesh name and objname the same
    newmesh = bpy.data.meshes.new(name) 
    newobject = bpy.data.objects.new(name, newmesh)
    # set mesh location: if =[] means local origin is at the world origin
    newobject.location = location 
    bpy.context.scene.collection.objects.link(newobject)
    # create mesh from python data
    #newmesh.from_pydata(vertices, edge, polygons.tolist())
    newmesh.from_pydata(vertices, edge, polygons)
    newmesh.update(calc_edges=True)
    return newobject

def getFaceNormals(vertices, facets):
    """ 
    Returns normals for each facet of mesh 
    Assuming right hand rule
    """
    u = vertices[facets[:,1],:] - vertices[facets[:,0],:]
    v = vertices[facets[:,2],:] - vertices[facets[:,0],:]
    normals = np.cross(u,v)
    norms = np.sqrt(np.sum(normals*normals, axis=1))
    return normals/norms[:, np.newaxis]

def getVertNormals(polygons, faceNorms):
    """ 
    Returns normals for each verts of mesh 
    based on norms of facets
    """

    normVectors = [] #[verticeNO, meansNOrm[n,3]numpyarray]
    for count, pol in enumerate(polygons):
        if count == 0:
            for ver in pol:
                normVectors.append([ver, faceNorms[count]])
        else:
            for ver in pol:
                #check if ver is in normVectors[0] if count >=1
                list0 = [x[0] for x in normVectors]
                if ver in list0: 
                    idx=list0.index(ver)
                    normVectors[idx][1] =  np.vstack(
                        [normVectors[idx][1], faceNorms[count]])
                else:
                    normVectors.append([ver, faceNorms[count]])

    normVectors = sorted(normVectors)
    #print(normVectors)

    #mean all normal vectors
    meanarray = []
    for ver in normVectors:
        norm = ver[1]
        if norm.ndim == 2:
            norm = np.mean(norm, axis=0) #some has 1 dim
        meanarray.append(norm)
    return meanarray

def getobjdata(obj):
    '''
    get vertice coords and polygons of obj
    '''
    #get active object
    objname = obj.name
    print("objname: ",objname)
    objdata = bpy.data.meshes[objname]
    objlocation = bpy.data.objects[objname].location
    #get matrix of polygon and vertices coords
    vertices=[]
    polygons=[]
    for ver in objdata.vertices:
        vertices.append(ver.co)
    for pol in objdata.polygons:
        vertindex_list=[]
        for verNo in range(0, len(pol.vertices)):
            vertindex_list.append(pol.vertices[verNo])
        polygons.append(vertindex_list)
    return vertices, polygons, objlocation #return list 


objdict['object1'] = bpy.context.active_object

vertices, polygons, objlocation = getobjdata(objdict['object1'])
vertices = np.array(vertices)
polygons = np.array(polygons)

faceNorms = getFaceNormals(vertices, polygons) #normal vector for faces
verNorms = getVertNormals(polygons, faceNorms) 
#print(faceNorms)
#print(verNorms) # list of numpy array --> need to fix 
#print(vertices)

new_vertices=np.zeros((len(vertices),3))
#print(type(vertices), len(vertices), type(verNorms), len(verNorms))
#print(vertices)
for i in range (0, len(vertices)):
    new_vertices[i] = vertices[i] + verNorms[i] 
print(new_vertices)

#objdict['verplane'] = newobj("verplane", objlocation, new_vertices,
                                   #[], [])
#objdict['object2'] = newobj("object2", objlocation, new_vertices, [], polygons)
#objdict['object2'] = newobj("object2", [], new_vertices, [], polygons)



def checknorm1(vertices, new_vertices):
    #draw arrow to check norm vector of vertices : 
    arr_vertices = np.vstack([vertices, new_vertices])
    print("arr_vertices:",arr_vertices)
    arr_edge = [] 
    no_ver = len(vertices)
    for c in range(0, no_ver):
        arr_edge.append([c, no_ver + c])
    #print(arr_edge)
    objdict['normarrows'] = newobj("normarrows2", objlocation, arr_vertices,
                                   arr_edge, [])
    return
#checknorm1(vertices, new_vertices)

def checknorm2(vertices, faceNorms):
    #draw arrow to check norm vector of pol:
    middleVertices = np.zeros((len(polygons),3))

    for count, pol in enumerate(polygons):
        polvertices = []
        for ver in pol:
            polvertices.append(vertices[ver])
        polvertice = np.array(polvertices)
        middleVer = np.mean(polvertices, axis=0)
        print(type(middleVer), middleVer)
        middleVertices[count] = middleVer

    new_vertices = middleVertices + faceNorms
    print(new_vertices)
    arr_vertices = np.vstack([middleVertices, new_vertices])
    arr_edge = [] 
    no_pol = len(polygons)
    for c in range(0, no_pol):
        arr_edge.append([c, no_pol + c])
    objdict['normFacearrows'] = newobj("normFacearrows", objlocation, arr_vertices,
                                   arr_edge, [])
    return
checknorm2(vertices, faceNorms)

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
