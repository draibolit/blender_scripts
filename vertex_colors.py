#http://blenderscripting.blogspot.jp/search?updated-max=2013-04-09T13:09:00-07:00&max-results=7&start=56&by-date=false

import bpy
import random

# start in object mode
 
my_object = bpy.data.objects['Cube'].data
 
color_map_collection = my_object.vertex_colors
if len(color_map_collection) == 0:
    color_map_collection.new()
 
"""
let us assume for sake of brevity that there is now 
a vertex color map called  'Col'    
"""
 
color_map = color_map_collection['Col']

# or you could avoid using the vertex color map name
# color_map = color_map_collection.active  
 
i = 0
for poly in my_object.polygons:
    for idx in poly.loop_indices:
        rgb = [random.random() for i in range(3)]
        color_map.data[i].color = rgb
        i += 1

# set to vertex paint mode to see the result
bpy.ops.object.mode_set(mode='VERTEX_PAINT')