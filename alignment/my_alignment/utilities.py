'''
Created on Jun 28, 2016

@author: Patrick
'''
import math
import os
import numpy as np
import bpy
import bgl
import blf

from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d, \
                                     region_2d_to_vector_3d
from bpy_extras.view3d_utils import region_2d_to_origin_3d

# Borrowed from retopoflow @CGCookie
# Jonathan Wiliamson, Jon Denning, Patrick Moore

mylist = []


def get_settings():
    if not get_settings.cached_settings:
        addons = bpy.context.preferences.addons
        # addons = bpy.context.user_preferences.addons
        # frame = inspect.currentframe()
        # frame.f_code.co_filename
        folderpath = os.path.dirname(os.path.abspath(__file__))
        while folderpath:
            folderpath, foldername = os.path.split(folderpath)
            if foldername in {'lib', 'addons'}:
                continue
            if foldername in addons:
                break
        else:
            assert False, 'Could not find non-"lib" folder'

        get_settings.cached_settings = addons[foldername].preferences

    return get_settings.cached_settings


get_settings.cached_settings = None


def bversion():
    bversion = '%03d.%03d.%03d' % (bpy.app.version[0], bpy.app.version[1],
                                   bpy.app.version[2])
    return bversion


#  DRAWING UTILITIES


def tag_redraw_all_view3d():
    context = bpy.context

    # Py cant access notifers
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()


def draw_3d_points(context, points, color, size):
    '''
    draw a bunch of dots
    args:
        points: a list of tuples representing x,y SCREEN coordinatei
                 eg [(10,30),(11,31),...]
        color: tuple (r,g,b,a)
        size: integer? maybe a float
    '''
    points_2d = [location_3d_to_region_2d(context.region, \
                                          context.space_data.region_3d, loc) \
                 for loc in points]

    if None in points_2d:
        points_2d = filter(None, points_2d)
    bgl.glColor4f(*color)
    bgl.glPointSize(size)
    bgl.glBegin(bgl.GL_POINTS)
    for coord in points_2d:
        # TODO:  Debug this problem....perhaps loc_3d is
        # returning points off of the screen.
        if coord:
            bgl.glVertex2f(*coord)

    bgl.glEnd()
    return

'''
#using this one
def draw_3d_points_revised(context, points, color, size):
    region = context.region
    region3d = context.space_data.region_3d

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    perspective_matrix = region3d.perspective_matrix.copy()

    bgl.glColor4f(*color)
    bgl.glPointSize(size)
    bgl.glBegin(bgl.GL_POINTS)

    for vec in points:
        vec_4d = perspective_matrix * vec.to_4d()
        if vec_4d.w > 0.0:
            x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
            y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)
            bgl.glVertex3f(x, y, 0)
    bgl.glEnd()
'''

#https://devtalk.blender.org/t/opengl-drawing-size-in-2-80/5178/3
def draw_3d_points_revised(context, points, color, size):

    import bpy
    import gpu
    import bgl
    from random import random
    from gpu_extras import batch

    def draw():
        shader.bind()
        bgl.glPointSize(5)
        batch.draw(shader)

#
    #positions = [(random(), random(), random()) for i in range(500)]
    #colors = [(random(), random(), random(), random()) for i in range(500)]
    positions = points
    nopoint = len(positions)
    colors = [(random(), random(), random(), random()) for i in range(nopoint)]

    shader = gpu.shader.from_builtin("3D_FLAT_COLOR")
    batch = batch.batch_for_shader(shader, "POINTS", {"pos": positions, "color": colors})

    bpy.types.SpaceView3D.draw_handler_add(draw, (), "WINDOW", "POST_VIEW")


def draw_3d_text(context, font_id, text, vec):
    region = context.region
    region3d = context.space_data.region_3d

    region_mid_width = region.width / 2.0
    region_mid_height = region.height / 2.0

    perspective_matrix = region3d.perspective_matrix.copy()
    vec_4d = perspective_matrix @ vec.to_4d()
    if vec_4d.w > 0.0:
        x = region_mid_width + region_mid_width * (vec_4d.x / vec_4d.w)
        y = region_mid_height + region_mid_height * (vec_4d.y / vec_4d.w)

        blf.position(font_id, x + 3.0, y - 4.0, 0.0)
        blf.draw(font_id, text)

# RAYCASTING AND SNAPPING


# Jon Denning for Retopoflow
def get_ray_plane_intersection(ray_origin, ray_direction, plane_point, plane_normal):
    d = ray_direction.dot(plane_normal)
    if abs(ray_direction.dot(plane_normal)) <= 0.00000001: return float('inf')
    return (plane_point-ray_origin).dot(plane_normal) / d
# Jon Denning for Retopoflow

def get_ray_origin(ray_origin, ray_direction, ob):
    mx = ob.matrix_world
    q  = ob.rotation_quaternion
    bbox = [Vector(v) for v in ob.bound_box]
    bm = Vector((min(v.x for v in bbox),min(v.y for v in bbox),min(v.z for v in bbox)))
    bM = Vector((max(v.x for v in bbox),max(v.y for v in bbox),max(v.z for v in bbox)))
    x,y,z = Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))
    planes = []
    if abs(ray_direction.x)>0.0001: planes += [(bm,x), (bM,-x)]
    if abs(ray_direction.y)>0.0001: planes += [(bm,y), (bM,-y)]
    if abs(ray_direction.z)>0.0001: planes += [(bm,z), (bM,-z)]
    dists = [get_ray_plane_intersection(ray_origin,ray_direction,mx*p0,q*no) for p0,no in planes]
    return ray_origin + ray_direction * min(dists)

#Jon Denning for Retopoflow    
def ray_cast_region2d(region, rv3d, screen_coord, obj):
    '''
    performs ray casting on object given region, rv3d, and coords wrt region.
    returns tuple of ray vector (from coords of region) and hit info
    '''
    mx = obj.matrix_world
    rgn = region
    imx = mx.inverted()
    
    r2d_origin = region_2d_to_origin_3d
    r2d_vector = region_2d_to_vector_3d
    
    o, d = r2d_origin(rgn, rv3d, screen_coord), r2d_vector(rgn, rv3d, screen_coord).normalized()
    back = 0 if rv3d.is_perspective else 1
    mult = 100 #* (1 if rv3d.is_perspective else -1)
    bver = '%03d.%03d.%03d' % (bpy.app.version[0],bpy.app.version[1],bpy.app.version[2])
    if (bver < '002.072.000') and not rv3d.is_perspective: mult *= -1
    
    #st, en = imx*(o-mult*back*d), imx*(o+mult*d)
    st, en = imx@(o-mult*back*d), imx@(o+mult*d)
    
    if bversion() < '002.077.000':
        hit = obj.ray_cast(st,en)
    else:
        hit = obj.ray_cast(st, en-st)
    return (d, hit)


def obj_ray_cast(obj, matrix, ray_origin, ray_target):
    """Wrapper for ray casting that moves the ray into object space"""

    # get the ray relative to the object
    matrix_inv = matrix.inverted()
    ray_origin_obj = matrix_inv @ ray_origin
    ray_target_obj = matrix_inv @ ray_target

    # cast the ray
    hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)

    if face_index != -1:
        return hit, normal, face_index
    else:
        return None, None, None


#http://www.lfd.uci.edu/~gohlke/code/transformations.py        
def affine_matrix_from_points(v0, v1, shear=True, scale=True, usesvd=True):
#create an affine matrix from 2 point clouds
    v0 = np.array(v0, dtype=np.float64, copy=True)
    v1 = np.array(v1, dtype=np.float64, copy=True)

    ndims = v0.shape[0]
    if ndims < 2 or v0.shape[1] < ndims or v0.shape != v1.shape:
        print(ndims < 2)
        print(v0.shape[1] < ndims)
        print(v0.shape != v1.shape)
        print(ndims)
        raise ValueError("input arrays are of wrong shape or type")

    # move centroids to origin
    t0 = -np.mean(v0, axis=1)
    M0 = np.identity(ndims+1)
    M0[:ndims, ndims] = t0
    v0 += t0.reshape(ndims, 1)
    t1 = -np.mean(v1, axis=1)
    M1 = np.identity(ndims+1)
    M1[:ndims, ndims] = t1
    v1 += t1.reshape(ndims, 1)

    if shear:
        # Affine transformation
        A = np.concatenate((v0, v1), axis=0)
        u, s, vh = np.linalg.svd(A.T)
        vh = vh[:ndims].T
        B = vh[:ndims]
        C = vh[ndims:2*ndims]
        t = np.dot(C, np.linalg.pinv(B))
        t = np.concatenate((t, np.zeros((ndims, 1))), axis=1)
        M = np.vstack((t, ((0.0,)*ndims) + (1.0,)))
    elif usesvd or ndims != 3:
        # Rigid transformation via SVD of covariance matrix
        u, s, vh = np.linalg.svd(np.dot(v1, v0.T))
        # rotation matrix from SVD orthonormal bases
        R = np.dot(u, vh)
        if np.linalg.det(R) < 0.0:
            # R does not constitute right handed system
            R -= np.outer(u[:, ndims-1], vh[ndims-1, :]*2.0)
            s[-1] *= -1.0
        # homogeneous transformation matrix
        M = np.identity(ndims+1)
        M[:ndims, :ndims] = R
    else:
        # Rigid transformation matrix via quaternion
        # compute symmetric matrix N
        xx, yy, zz = np.sum(v0 * v1, axis=1)
        xy, yz, zx = np.sum(v0 * np.roll(v1, -1, axis=0), axis=1)
        xz, yx, zy = np.sum(v0 * np.roll(v1, -2, axis=0), axis=1)
        N = [[xx+yy+zz, 0.0,      0.0,      0.0],
             [yz-zy,    xx-yy-zz, 0.0,      0.0],
             [zx-xz,    xy+yx,    yy-xx-zz, 0.0],
             [xy-yx,    zx+xz,    yz+zy,    zz-xx-yy]]
        # quaternion: eigenvector corresponding to most positive eigenvalue
        w, V = np.linalg.eigh(N)
        q = V[:, np.argmax(w)]
        q /= vector_norm(q)  # unit quaternion
        # homogeneous transformation matrix
        M = quaternion_matrix(q)

    if scale and not shear:
        # Affine transformation; scale is ratio of RMS deviations from centroid
        v0 *= v0
        v1 *= v1
        M[:ndims, :ndims] *= math.sqrt(np.sum(v1) / np.sum(v0))

    # move centroids back
    M = np.dot(np.linalg.inv(M1), np.dot(M, M0))
    M /= M[ndims, ndims]
    return M


#http://www.lfd.uci.edu/~gohlke/code/transformations.py
def quaternion_matrix(quaternion):
    q = np.array(quaternion, dtype=np.float64, copy=True)
    n = np.dot(q, q)
    if n < _EPS:
        return np.identity(4)
    q *= math.sqrt(2.0 / n)
    q = np.outer(q, q)
    return np.array([
        [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
        [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
        [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
        [                0.0,                 0.0,                 0.0, 1.0]])
    
#http://www.lfd.uci.edu/~gohlke/code/transformations.py    
def vector_norm(data, axis=None, out=None):
    data = np.array(data, dtype=np.float64, copy=True)
    if out is None:
        if data.ndim == 1:
            return math.sqrt(np.dot(data, data))
        data *= data
        out = np.atleast_1d(np.sum(data, axis=axis))
        np.sqrt(out, out)
        return out
    else:
        data *= data
        np.sum(data, axis=axis, out=out)
        np.sqrt(out, out)

def make_pairs(align_obj, base_obj, base_bvh, vlist, thresh, sample = 0, calc_stats = False):
    # just for select point cloud of align and base object base on parameters
    '''
    vlist is a list of vertex indices in the align object to use
    for alignment.  Will be in align_obj local space!
    '''
    mx1 = align_obj.matrix_world
    mx2 = base_obj.matrix_world
    
    imx1 = mx1.inverted()
    imx2 = mx2.inverted()
    
    verts1 = []
    verts2 = [] 
    if calc_stats:  #calc_stats is using the target
        dists = []
    
    #downsample if needed
    if sample > 1:
        vlist = vlist[0::sample] #double colon to index a space of sample 
        
    if thresh > 0:  #thresh: minimal start distance, if 0 --> error; always run this command under this if
        #filter data based on an initial starting dist
        #eacg time in the routine..the limit should go down
        for vert_ind in vlist:
            
            vert = align_obj.data.vertices[vert_ind]
            #closest point for point clouds.  Local space of base obj
            co_find = imx2 * (mx1 * vert.co)
            
            #closest surface point for triangle mesh
            #this is set up for a  well modeled aligning object with
            #with a noisy or scanned base object
            if bversion() <= '002.076.00':
                #co1, normal, face_index = base_obj.closest_point_on_mesh(co_find)
                co1, n, face_index, d = base_bvh.find(co_find)
            else:
                #res, co1, normal, face_index = base_obj.closest_point_on_mesh(co_find)
                co1, n, face_index, d = base_bvh.find_nearest(co_find) #Returns (Vector location, Vector normal, int index, float distance)
            
            dist = (mx2 * co_find - mx2 * co1).length 
            #d is now returned by bvh.find
            #dist = mx2.to_scale() * d
            if face_index != -1 and dist < thresh:
                verts1.append(vert.co)
                verts2.append(imx1 * (mx2 * co1))
                if calc_stats:
                    dists.append(dist)
        
        #later we will pre-process data to get nice data sets
        #eg...closest points after initial guess within a certain threshold
        #for now, take the verts and make them a numpy array
        A = np.zeros(shape = [3,len(verts1)])
        B = np.zeros(shape = [3,len(verts1)])
        
        for i in range(0,len(verts1)):
            V1 = verts1[i]
            V2 = verts2[i]
    
            A[0][i], A[1][i], A[2][i] = V1[0], V1[1], V1[2]
            B[0][i], B[1][i], B[2][i] = V2[0], V2[1], V2[2]
        
        if calc_stats:
            avg_dist = np.mean(dists)
            dev = np.std(dists)
            d_stats = [avg_dist, dev]
        else:
            d_stats = None
        return A, B, d_stats # A relate to align_obj, B to base_obj
