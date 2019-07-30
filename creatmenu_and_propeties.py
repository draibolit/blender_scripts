# http://michelanders.blogspot.jp/p/creating-blender-26-python-add-on.html

import bpy  
from bpy.types import Operator  
from bpy.props import FloatVectorProperty, FloatProperty

# To provide Blender and the user with relevant information about our add-on  
bl_info = {  
 "name": "Move4 Object",  
 "author": "Michel Anders (varkenvarken)",  
 "version": (1, 0),  
 "blender": (2, 6, 4),  
 "location": "View3D > Object > Move4 Object",  
 "description": "Moves the active Object",  
 "warning": "",  
 "wiki_url": "",  
 "tracker_url": "",  
 "category": "Object"}  

class Move3Operator(bpy.types.Operator):  
 """Move3 Operator"""  
 bl_idname = "object.move3_operator"  
 bl_label = "Move3 Operator"  
 bl_options = {'REGISTER', 'UNDO'}  # to make it appear in the toolbar area need to a set containing the string 'REGISTER',add 'UNDO' to provide a rest button 
  
 direction = FloatVectorProperty(  
   name="direction",  
   default=(1.0, 1.0, 1.0),  
   subtype='XYZ',  
   description="move direction"  
   )  
   
 distance = FloatProperty(  
   name="distance",  
   default=1.0,  
   subtype='DISTANCE',  
   unit='LENGTH',  
   description="distance"  
   )  
  
   # execute() function retrieves the distance and the direction and 
   # after normalizing the direction changes the active object's location. 
 def execute(self, context):  
  dir = self.direction.normalized()  
  context.active_object.location += self.distance * dir  
  return {'FINISHED'}  
 
  # to check if there is an active object at all and if so if it is in object mode.
   # If not we return False. If an operator provides a poll() function and it returns False,
   #  any menu entry for this operator will be grayed out.
 @classmethod  
 def poll(cls, context):  
  ob = context.active_object  
  return ob is not None and ob.mode == 'OBJECT'  
  
def add_object_button(self, context):  
 self.layout.operator(  
  Move3Operator.bl_idname,  
  text=Move3Operator.__doc__,  
  icon='PLUGIN')  
  
def register():  
 bpy.utils.register_class(Move3Operator)  
 bpy.types.VIEW3D_MT_object.append(add_object_button)  
  
if __name__ == "__main__":  
 register()  


# If we now save our script to the add-ons directory and restart Blender,
#  the add-on can be enabled from File->User Preferences by ticking the check box
# Because we defined the category to be 'Object' it shows up in the Object section of the add-ons. 