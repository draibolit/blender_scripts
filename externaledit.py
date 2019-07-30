import bpy  
import os  
  
#filename = os.path.join(os.path.dirname(bpy.data.filepath), "moveactiveobject.py")  
filename = "g:/Dropbox/Python scripts/blenderscripts/current.py" 
exec(compile(open(filename).read(), filename, 'exec')) 

# Blender's bpy.data module contains a number of useful attributes
# and her we use filepath to get the full filename of the .blend file we are using.
# We use Python's platform neutral filename manipulation functions get at the directory part 
# and append the name of the script we want to run. 