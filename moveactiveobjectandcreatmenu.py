import bpy  
  
class Move2Operator(bpy.types.Operator):  
    """Move2 Operator"""  
    bl_idname = "object.move2_operator"  
    bl_label = "Move2 Operator"  
  
    def execute(self, context):  
        context.active_object.location.x += 1.0  
        return {'FINISHED'}  
  
def add_object_button(self, context):  
    self.layout.operator(  
        Move2Operator.bl_idname,  
        text=Move2Operator.__doc__,  
        icon='PLUGIN')  
  
def register():  
    bpy.utils.register_class(Move2Operator)  
    bpy.types.VIEW3D_MT_object.append(add_object_button)  
if __name__ == "__main__":  
    register() 

 # The add_object_button argument is a function that takes a self argument that refers to 
 # the menu being displayed on screen and a context argument.  It adds the operator to the menu layout 
 # (more on layouts in the section on properties) by calling the operator() function of that layout.
 # The three arguments passed are the internal name of our operator,
 #  the text that should appear in the menu and the icon to use.