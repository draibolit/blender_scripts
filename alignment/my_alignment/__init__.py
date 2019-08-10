
bl_info = {
    "name": "Dental Model Alignment",
    "author": "Tuan Nguyen - Nagasaki University",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Toos > Alignment",
    "description": "To align 2 scanning models",
    "warning": "",
    "wiki_url": "",
    "category": "Transform Mesh"}


import numpy as np
from numpy.ma.core import fmod
import math
import time
import bpy
import blf #This module provides access to blenders text drawing functions.
import bgl #The Blender.BGL submodule (the OpenGL wrapper).
from bpy.types import Operator
from bpy.props import FloatVectorProperty, StringProperty, IntProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, AddonPreferences
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
from .utilities import *



# epsilon for testing whether a number is close to zero
_EPS = np.finfo(float).eps * 4.0
                 
class AlignmentAddonPreferences(AddonPreferences):  #store preferences permenent in addone menu setting
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    icp_iterations : IntProperty(
            name="ICP Iterations",
            default=50
            )
    
    redraw_frequency : IntProperty(
            name="Redraw Iterations",
            description = "Number of iterations between redraw, bigger = less redraw but faster completion",
            default=10)
    
    use_sample : BoolProperty(
            name = "Use Sample",
            description = "Use a sample of verts to align",
            default = False)
    
    sample_fraction : FloatProperty(
            name="Sample Fraction",
            description = "Only fraction of mesh verts for alignment. Less accurate, faster",
            default = 0.5,
            min = 0,
            max = 1)
    
    min_start : FloatProperty(
            name="Minimum Starting Dist",
            description = "Only verts closer than this distance will be used in each iteration",
            default = 0.5,
            min = 0,
            max = 20)
    
    target_d : FloatProperty(
            name="Target Translation",
            description = "If translation of 3 iterations is < target, ICP is considered sucessful",
            default = 0.01,
            min = 0,
            max = 10)
    
    use_target : BoolProperty(
            name="Use Target",
            description = "Calc alignment stats at each iteration to assess convergence. SLower per step, may result in less steps",
            default = False)
    
    align_methods =['RIGID','ROT_LOC_SCALE']#,'AFFINE']
    align_items = []
    for index, item in enumerate(align_methods):
        align_items.append((str(index), align_methods[index], str(index)))
        align_meth : EnumProperty(items = align_items, name="Alignment Method", description="Changes how picked points registration aligns object", default='0', options={'ANIMATABLE'}, update=None, get=None, set=None)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Alignment Preferences")
        layout.prop(self, "icp_iterations")
        layout.prop(self, "redraw_frequency")
        layout.prop(self, "use_sample")
        layout.prop(self, "sample_fraction")
        layout.prop(self, "min_start")
        layout.prop(self, "use_target")
        layout.prop(self, "target_d")
        layout.prop(self, "align_meth")
        #layout.prop(self, "align_areas")
        
#class ComplexAlignmentPanel(bpy.types.Panel): 
class OBJECT_PT_ComplexAlignmentPanel(bpy.types.Panel): 
    """UI for ICP Alignment"""
    #bl_category = "Alignment"
    bl_label = "OBJECT_PT_ICP_Object_Alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'


    def draw(self, context):
        settings = get_settings()
        layout = self.layout

        row = layout.row()
        row.label(text="Alignment Tools", icon='MOD_SHRINKWRAP')

        row = layout.row()
        row.prop(settings, "align_meth")

        align_obj = context.object
        if align_obj:
            row = layout.row()
            row.label(text="Align object is: " + align_obj.name)
        
        else:
            row = layout.row()
            row.label(text='No Alignment Object!')
        
        if len(context.selected_objects) == 2:
            
            base_obj = [obj for obj in context.selected_objects if obj != align_obj][0]
            row = layout.row()
            row.label(text="Base object is: " + base_obj.name)
        else:
            row = layout.row()
            row.label(text="No Base object!")
        
        row = layout.row()
        row.label(text = 'Pre Processing')
        
        row = layout.row()
        row.prop(context.scene, 'selection_prop')
        row.operator('object.area_selection')
        
        row = layout.row()
        row.prop(context.scene, 'ICP_area')

        # row = layout.row()    
        # row.operator('object.align_include')   
        
        # row = layout.row()    
        # row.operator('object.align_exclude')    
        
        row = layout.row()
        row.label(text = 'Initial Alignment')
        row = layout.row()
        row.operator('object.align_picked_points')
        row.operator('screen.area_dupli', icon = 'FULLSCREEN_ENTER', text = '')
     
        row = layout.row()
        row.label(text = 'Iterative Alignment')
        row = layout.row()
        row.operator('object.align_icp')
        
        row = layout.row()
        row.prop(settings, 'redraw_frequency')
        row = layout.row()
        row.prop(settings, 'icp_iterations')
        row = layout.row()
        row.prop(settings, 'use_sample')
        row.prop(settings, 'sample_fraction')
        row = layout.row()
        row.prop(settings, 'min_start')
        row = layout.row()
        row.prop(settings, 'use_target')
        row.prop(settings, 'target_d')


class MyPropertyGroup(bpy.types.PropertyGroup):

    bpy.types.Scene.selection_prop = bpy.props.StringProperty \
      (
        name = "Area_selection",
        description = "Area Selection Input",
        default = "Palate"
      )

    bpy.types.Scene.ICP_area = bpy.props.StringProperty \
      (
        name = "Area_for_ICP",
        description = "Selection area for ICP",
        default = "Palate"
      )

class OBJECT_OT_Area_selection(bpy.types.Operator): # Create select area in a separate group
    bl_idname = "object.area_selection"
    bl_label = "Area Selection/Finish"
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(cls, context):
        condition_1 = context.selected_objects[0].type == 'MESH'
        return condition_1



    def execute(self, context):
        settings = get_settings()
        sel_name = context.scene.selection_prop
        align_obj = context.object

        if sel_name not in align_obj.vertex_groups:
            new_group = align_obj.vertex_groups.new(name = sel_name)

        if sel_name in align_obj.vertex_groups:    
            bpy.ops.object.vertex_group_set_active(group = sel_name)

        if context.mode != 'PAINT_WEIGHT':
            bpy.ops.object.mode_set(mode = 'WEIGHT_PAINT')

        return {'FINISHED'}

class OJECT_OT_icp_align(bpy.types.Operator):
    """Uses ICP alignment to iteratevely aligne two objects"""
    bl_idname = "object.align_icp"
    bl_label = "ICP Align"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        condition_1 = len(context.selected_objects) == 2
        condition_2 = context.selected_objects[0].type == 'MESH' and \
                        context.selected_objects[0].type == 'MESH'
        return condition_1 and condition_2

    def execute(self, context):
        settings = get_settings()
        ICP_sel = context.scene.ICP_area
        align_meth = settings.align_meth
        start = time.time()
        align_obj = context.object
        base_obj = [obj for obj in context.selected_objects if obj != align_obj][0]

# **********************choose select vertexgroup in baseobj to ICP***********************
        # find polygons from vetex group
        # get list of vertex in selected vertex groups 
        sel_poly=[]
        base_vlist=[]
        base_vlist_co=[]
        base_group_lookup = {g.name: g.index for g in base_obj.vertex_groups} #create a dictionary
        base_group_vlist=[]

        if ICP_sel in base_obj.vertex_groups:
            group = base_group_lookup[ICP_sel]
            for v in base_obj.data.vertices: 
                for g in v.groups:
                    if g.group == group:
                        base_group_vlist.append(v.index) 
            #get list of polygon from selected vertex group
            b = set(base_group_vlist)
            for poly in base_obj.data.polygons:
                a = set(poly.vertices[:]) 
                anb = a & b
                if anb:
                    verts_in_poly = poly.vertices[:]
                    sel_poly.append(poly.index)             #selected polygons
                    base_vlist.append(poly.vertices[:])     #selected vertex from polygons
            #renumber polygons vertices
            # combine all vertice in polygons list
            sortlist = []
            for poly in base_vlist:
                for vert in poly:
                    sortlist.append(vert) 
            sortlist = sorted(set(sortlist)) # remove duplicate and sort the list
            # renumber base_vlist to index of found item in sortlist
            # for poly in base_vlist:
            #     for i, vert in enumerate(poly):
            #         for j, no in enumerate(sortlist):
            #             if vert==no:
            #                 # vert = j 
            #                poly[i] = j   --> error: 'tuple' object does not support item assignment
            temp = [[vert for vert in poly] for poly in base_vlist]  #need to copy to another list to be able to modified
            for poly in temp:
                for i, vert in enumerate(poly):
                    for j, no in enumerate(sortlist):
                        if vert==no:
                            poly[i] = j
            # Create list of vertex coordination from softlist
            for vert in sortlist:
                base_vlist_co.append(base_obj.data.vertices[vert].co)  #coord of selected vertex in selected polygons
                
            base_bvh = BVHTree.FromPolygons(base_vlist_co, temp) #choose selected vertices in baseobj

        else:    
            base_bvh = BVHTree.FromObject(base_obj, context.scene) #choose whole vertices in baseobj
        
# **********************choose select vertexgroup in alignobj to ICP***********************

        align_obj.rotation_mode = 'QUATERNION'
        vlist = []
        group_lookup = {g.name: g.index for g in align_obj.vertex_groups}
        if ICP_sel in align_obj.vertex_groups:
            group = group_lookup[ICP_sel]
            for v in align_obj.data.vertices: #copy selected area vertex to list of ICP action
                for g in v.groups:
                    if g.group == group:
                        vlist.append(v.index)

        else: #choose the whole align objects vertex if not choose the area
            vlist = [v.index for v in align_obj.data.vertices]
# ************************************************************************************        
        settings = get_settings()
        thresh = settings.min_start
        sample = settings.sample_fraction
        iters = settings.icp_iterations
        target_d = settings.target_d
        use_target = settings.use_target
        factor = round(1/sample)
        
        n = 0
        converged = False
        conv_t_list = [target_d * 2] * 5  #store last 5 translations
        conv_r_list = [None] * 5
        
        bematrixworld = align_obj.matrix_world.copy() #store the begining matrixworld
        while n < iters  and not converged:
            
            (A, B, d_stats) = make_pairs(align_obj, base_obj, base_bvh, vlist, thresh, factor, calc_stats = use_target)
            
            if align_meth == '0': #rigid transform
                M = affine_matrix_from_points(A, B, shear=False, scale=False, usesvd=True)
                # print (M)

            elif align_meth == '1': # rot, loc, scale
                M = affine_matrix_from_points(A, B, shear=False, scale=True, usesvd=True)

            new_mat = Matrix.Identity(4)

            for y in range(0,4):
                for z in range(0,4):
                    new_mat[y][z] = M[y][z]     #new_mat = affine transform matrix
                
            align_obj.matrix_world = align_obj.matrix_world * new_mat  #****This is for transformation every interations
            trans = new_mat.to_translation()
            quat = new_mat.to_quaternion()
            
            align_obj.update_tag()
            context.scene.update()
        
            if d_stats:
                i = fmod(n,5) #returns the floating-point remainder of x/y
                conv_t_list[i] = trans.length   #get the length of last 5 translation matrixs
                conv_r_list[i] = abs(quat.angle)
                
                if all(d < target_d for d in conv_t_list):
                    converged = True
                    
                    print('---------Summary-----------------')
                    print('Converged in %s iterations' % str(n+1))
                    print('Final Translation: %f ' % conv_t_list[i])
                    print('Final Avg Dist: %f' % d_stats[0])
                    print('Final St Dev %f' % d_stats[1])
                    print('Avg last 5 rotation angle: %f' % np.mean(conv_r_list))
            
            n += 1   
        time_taken = time.time() - start
        
        if use_target and not converged:
            print('Maxed out iterations')
            print('Final Translation: %f ' % conv_t_list[i])
            print('Final Avg Dist: %f' % d_stats[0])
            print('Final St Dev %f' % d_stats[1])
            print('Avg last 5 rotation angle: %f' % np.mean(conv_r_list))
            
        print('Aligned obj in %f sec' % time_taken)

        endmatrixworld = align_obj.matrix_world #store the last matrixworld
        ICPmatrix = endmatrixworld*bematrixworld.inverted()
        Initial_point = Vector([1.78237, 0.69558, 2.40553])
        point_transformed = ICPmatrix * Initial_point
 
        accessfile = bpy.path.abspath("//output.txt")
        with open(accessfile, 'a') as f:
            f.write('The begining world maxtrix:\n')
            f.write(str(bematrixworld)+'\n')
            f.write('The ended world matrix:\n')
            f.write(str(endmatrixworld)+'\n')
            f.write('The ICP transformation matrix is:\n')
            f.write(str(ICPmatrix)+'\n')
            f.write('The inverted ICP transformation matrix is:\n')
            f.write(str(ICPmatrix.inverted())+'\n')
            f.write('lefteye vertex coord:\n')
            f.write(str(Initial_point)+'\n')
            f.write("transform to:\n")
            f.write(str(point_transformed)+'\n')
            f.write('---------------------*************------------------------\n')

        return {'FINISHED'}

def draw_callback_px(self, context):
    
    font_id = 0  # XXX, need to find out how best to get this.

    # draw some text
    y = context.region.height
    dims = blf.dimensions(0, 'A')
    
    blf.position(font_id, 10, y - 20 - dims[1], 0)
    blf.size(font_id, 20, 72)  
        
    if context.area.x == self.area_align.x:
        blf.draw(font_id, "Align: "+ self.align_msg)
        points = [self.obj_align.matrix_world * p for p in self.align_points]
        color = (1,0,0,1)
    else:
        blf.draw(font_id, "Base: " + self.base_msg)
        points = [self.obj_align.matrix_world * p for p in self.base_points]
        color = (0,1,0,1)
    
    draw_3d_points_revised(context, points, color, 4)
    
    for i, vec in enumerate(points):
        ind = str(i)
        draw_3d_text(context, font_id, ind, vec)
    
class OBJECT_OT_align_pick_points(bpy.types.Operator):
    """Algin two objects with 3 or more pair of picked poitns"""
    bl_idname = "object.align_picked_points"
    bl_label = "Align: Picked Points"

    @classmethod
    def poll(cls, context):
        condition_1 = len(context.selected_objects) == 2
        condition_2 =  context.selected_objects[0].type == 'MESH' and \
                       context.selected_objects[1].type == 'MESH'
        return condition_1 and condition_2

    def modal(self, context, event):
        
        tag_redraw_all_view3d()
        
        if len(self.align_points) < 3:
            self.align_msg = "Pick at least %s more pts" % str(3 - len(self.align_points))
        else:
            self.align_msg = "More points optional"
                        
        if len(self.base_points) < 3:
            self.base_msg = "Pick at last %s more pts" % str(3 - len(self.base_points))
        else:
            self.base_msg = "More points optional"
            
        
        if len(self.base_points) > 3 and len(self.align_points) > 3 and len(self.base_points) != len(self.align_points):
            
            if len(self.align_points) < len(self.base_points):
                self.align_msg = "Pick %s more pts to match" % str(len(self.base_points) - len(self.align_points))
            else:
                self.base_msg = "Pick %s more pts to match" % str(len(self.align_points) - len(self.base_points))
                
        if len(self.base_points) == len(self.align_points) and len(self.base_points) >= 3:
            self.base_msg = "Hit Enter to Align"
            self.align_msg = "Hit Enter to Align"            
    
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            
            ray_max = 10000
            
            if event.mouse_x > self.area_align.x and event.mouse_x < self.area_align.x + self.area_align.width:
                
                for reg in self.area_align.regions:
                    if reg.type == 'WINDOW':
                        region = reg
                for spc in self.area_align.spaces:
                    if spc.type == 'VIEW_3D':
                        rv3d = spc.region_3d
                
                #just transform the mouse window coords into the region coords        
                coord = (event.mouse_x - region.x, event.mouse_y - region.y)
                
                #are the cords the problem
                print('align cords: ' + str(coord))
                print(str((event.mouse_region_x, event.mouse_region_y)))
                        
                view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                ray_target = ray_origin + (view_vector * ray_max)
            
                print('in the align object window')
                (d, (ok,hit, normal, face_index)) = ray_cast_region2d(region, rv3d, coord, self.obj_align)
                if hit:
                    print('hit! align_obj %s' % self.obj_align.name)
                    #local space of align object
                    self.align_points.append(hit)

            else:
                    
                for reg in self.area_base.regions:
                    if reg.type == 'WINDOW':
                        region = reg
                for spc in self.area_base.spaces:
                    if spc.type == 'VIEW_3D':
                        rv3d = spc.region_3d
                        
                coord = (event.mouse_x - region.x, event.mouse_y - region.y)        
                view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
                ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
                ray_target = ray_origin + (view_vector * ray_max)
                
                print('in the base object window')
                (d, (ok,hit, normal, face_index)) = ray_cast_region2d(region, rv3d, coord, self.obj_base)
                if ok:
                    print('hit! base_obj %s' % self.obj_base.name)
                    #points in local space of align object
                    self.base_points.append(self.obj_align.matrix_world.inverted() * self.obj_base.matrix_world * hit)    
            
                    
            return {'RUNNING_MODAL'}
            
        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            
            if event.mouse_x > self.area_align.x and event.mouse_x < self.area_align.x + self.area_align.width:
                self.align_points.pop()
            else:
                self.base_points.pop()
            
            return {'RUNNING_MODAL'}
            
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            
            return {'PASS_THROUGH'}
        
        if self.modal_state == 'NAVIGATING':
            
            if (event.type in {'MOUSEMOVE',
                               'MIDDLEMOUSE', 
                                'NUMPAD_2', 
                                'NUMPAD_4', 
                                'NUMPAD_6',
                                'NUMPAD_8', 
                                'NUMPAD_1', 
                                'NUMPAD_3', 
                                'NUMPAD_5', 
                                'NUMPAD_7',
                                'NUMPAD_9'} and event.value == 'RELEASE'):
            
                self.modal_state = 'WAITING'
                return {'PASS_THROUGH'}
            
        if (event.type in {'MIDDLEMOUSE', 
                                    'NUMPAD_2', 
                                    'NUMPAD_4', 
                                    'NUMPAD_6',
                                    'NUMPAD_8', 
                                    'NUMPAD_1', 
                                    'NUMPAD_3', 
                                    'NUMPAD_5', 
                                    'NUMPAD_7',
                                    'NUMPAD_9'} and event.value == 'PRESS'):
            
            self.modal_state = 'NAVIGATING'
                        
            return {'PASS_THROUGH'}
        
        elif event.type in {'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}
        
        elif event.type == 'RET':
            
            if len(self.align_points) >= 3 and len(self.base_points) >= 3 and len(self.align_points) == len(self.base_points):
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self.de_localize(context)
                self.align_obj(context)
                
                context.scene.objects.active = self.obj_align
                self.obj_align.select = True
                self.obj_base = True
                
                return {'FINISHED'}
            
        return {'RUNNING_MODAL'}
            
    def de_localize(self,context):
        
        override = context.copy()
        override['area'] = self.area_align
        bpy.ops.view3d.localview(override)
        bpy.ops.view3d.view_selected(override)
        
        override['area'] = self.area_base
        bpy.ops.view3d.localview(override)
        bpy.ops.view3d.view_selected(override)
        
        #Crash Blender?       
        bpy.ops.screen.area_join(min_x=self.area_align.x,min_y=self.area_align.y, max_x=self.area_base.x, max_y=self.area_base.y)
        bpy.ops.view3d.toolshelf()
        
        #ret = bpy.ops.screen.area_join(min_x=area_base.x,min_y=area_base.y, max_x=area_align.x, max_y=area_align.y)
    
    def align_obj(self,context):
        
        if len(self.align_points) != len(self.base_points):
            if len(self.align_points) < len(self.base_points):
                
                self.base_points = self.base_points[0:len(self.align_points)]
            else:
                self.align_points = self.align_points[0:len(self.base_points)]
                
        A = np.zeros(shape = [3,len(self.base_points)])
        B = np.zeros(shape = [3,len(self.base_points)])
        
        for i in range(0,len(self.base_points)):
            V1 = self.align_points[i]
            V2 = self.base_points[i]
    
            A[0][i], A[1][i], A[2][i] = V1[0], V1[1], V1[2]
            B[0][i], B[1][i], B[2][i] = V2[0], V2[1], V2[2]  

        #test new method
        settings = get_settings()
        align_meth = settings.align_meth
        
        if align_meth == '0': #rigid transform
            M = affine_matrix_from_points(A, B, shear=False, scale=False, usesvd=True)
        elif align_meth == '1': # rot, loc, scale
            M = affine_matrix_from_points(A, B, shear=False, scale=True, usesvd=True)
        #else: #affine
            #M = affine_matrix_from_points(A, B, shear=True, scale=True, usesvd=True)
            
        new_mat = Matrix.Identity(4)
        for n in range(0,4):
            for m in range(0,4):
                new_mat[n][m] = M[n][m]

        #because we calced transform in local space
        #it's this easy to update the obj...
        self.obj_align.matrix_world = self.obj_align.matrix_world * new_mat

        self.obj_align.update_tag()
        context.scene.update()
            
    def invoke(self, context, event):
        self.modal_state = 'WAITING'
 
        self.start_time = time.time()
        #capture some mouse info to pass to the draw handler
        self.winx = event.mouse_x
        self.winy = event.mouse_y
            
        self.regx = event.mouse_region_x
        self.regy = event.mouse_region_y
        
        self.base_msg = 'Select 3 or more points'
        self.align_msg = 'Select 3 or more points'
        
        obj1_name = context.selected_objects[0].name
        obj2_name = [obj for obj in context.selected_objects if obj != \
                     context.selected_objects][0].name
        
        for ob in context.scene.collection.objects:
            ob.select_set(status=False)
        
        context.view_layer.objects.active = None
        
        #I did this stupid method becuase I was unsure
        #if some things were being "sticky" and not
        #remembering where they were
        obj1 = bpy.data.objects[obj1_name]
        obj2 = bpy.data.objects[obj2_name]
        
        for ob in bpy.data.objects:
            if ob.select_get():
                print(ob.name)
                
        screen = context.window.screen
        areas = [area.as_pointer() for area in screen.areas]
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                break 
        
        #bpy.ops.view3d.toolshelf() #close the first toolshelf, not aval in 2.8
        override = context.copy()
        override['area'] = area
        
        self.area_align = area
        
        #bpy.ops.screen.area_split(override, direction='VERTICAL', factor=0.5, mouse_x=-100, mouse_y=-100)
        bpy.ops.screen.area_split(override, direction='VERTICAL', factor=0.5,
                                  cursor=(0, 0))
        #bpy.ops.view3d.toolshelf() #close the 2nd toolshelf
        
        context.view_layer.objects.active = obj1
        obj1.select_set(state=True)
        obj2.select_set(state= False)
        
        bpy.ops.view3d.localview(override)
        
        obj1.select_set(state=False)
        context.view_layer.objects.active = None
        override = context.copy()
        for area in screen.areas:
            if area.as_pointer() not in areas:
                override['area'] = area
                self.area_base = area
                bpy.ops.object.select_all(action = 'DESELECT')
                context.view_layer.objects.active = obj2
                obj2.select_set(state=True)
                override['selected_objects'] = [obj2]
                override['selected_editable_objects'] = [obj2]
                override['object'] = obj2
                override['active_object'] = obj2
                bpy.ops.view3d.localview(override)
                break
 
        self.obj_align = obj1
        self.obj_base = obj2
        
        #hooray, we will raycast in local view!
        self.align_points = []
        self.base_points = []
        
        context.window_manager.modal_handler_add(self)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'RUNNING_MODAL'}


classes = (AlignmentAddonPreferences, 
           OJECT_OT_icp_align,
           OBJECT_OT_align_pick_points, 
           OBJECT_PT_ComplexAlignmentPanel,
           OBJECT_OT_Area_selection, 
           MyPropertyGroup) 

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

#command to add to running addon:
#cp /mnt/linuxdisk/Dropbox/Tuan/Patran/skullremodelling/blenderscripts/alignment/my_alignment/__init__.py ~/.config/blender/2.80/scripts/addons/my_alignment/
#https://b3d.interplanety.org/en/porting-add-on-from-blender-2-7-to-blender-2-8/
