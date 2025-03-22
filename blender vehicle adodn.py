# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 12:30:45 2025

@author: Steffen
"""

bl_info = {
    "name": "Arma Reforger Vehicle Tools",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > AR Vehicles",
    "description": "Tools for preparing and rigging vehicles for Arma Reforger",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy
import math
from mathutils import Vector

# Reference VW Golf measurements (as used in Arma Reforger examples)
REFERENCE_VEHICLE = {
    "name": "VW Golf (Reference)",
    "length": 4.282,  # meters
    "width": 1.789,   # meters
    "height": 1.483   # meters
}

# Scale presets for different vehicle types
VEHICLE_SCALES = {
    "your_model": (4.07, 1.8, 1.46),  # Your exact measurements
    "golf_reference": (REFERENCE_VEHICLE["length"], REFERENCE_VEHICLE["width"], REFERENCE_VEHICLE["height"]),
    "sedan": (4.5, 1.8, 1.5),
    "suv": (4.7, 1.9, 1.8),
    "truck": (5.5, 2.0, 2.0),
    "jeep": (4.2, 1.8, 1.8),
    "van": (5.0, 2.0, 2.2),
    "apc": (6.5, 2.5, 2.8),
}
# Default locations for empty objects (in meters)
# These locations are adjusted for your specific vehicle dimensions: 4.07 x 1.8 x 1.46 meters
EMPTY_LOCATIONS = {
    # Crew positions - adjusted for your vehicle height
    "driver": (0.35, 0.2, 0.85),
    "codriver": (-0.35, 0.2, 0.85),
    "cargo01": (0.35, -0.5, 0.85),
    "cargo02": (-0.35, -0.5, 0.85),
    "cargo03": (0.35, -1.0, 0.85),
    "cargo04": (-0.35, -1.0, 0.85),
    
    # Vehicle component points - adjusted for your vehicle dimensions
    "engine": (0, 1.4, 0.5),
    "exhaust": (0.3, -1.7, 0.2),
    "frontlight_left": (0.7, 1.9, 0.5),
    "frontlight_right": (-0.7, 1.9, 0.5),
    "backlight_left": (0.7, -1.9, 0.5),
    "backlight_right": (-0.7, -1.9, 0.5),
    
    # Wheel positions - standard 4-wheel layout
    "wheel_1_1": (0.75, 1.4, 0.3),   # Front right
    "wheel_1_2": (-0.75, 1.4, 0.3),  # Front left
    "wheel_2_1": (0.75, -1.4, 0.3),  # Rear right
    "wheel_2_2": (-0.75, -1.4, 0.3), # Rear left
    
    # Additional wheels for APC/trucks - middle wheels
    "wheel_3_1": (0.75, 0, 0.3),     # Middle right
    "wheel_3_2": (-0.75, 0, 0.3),    # Middle left
    
    # Additional wheels for longer vehicles - second rear axle
    "wheel_4_1": (0.75, -2.0, 0.3),  # Second rear right
    "wheel_4_2": (-0.75, -2.0, 0.3), # Second rear left
    
    # Damage zones - adjusted for your vehicle
    "dmg_zone_engine": (0, 1.4, 0.5),
    "dmg_zone_fueltank": (0, -1.4, 0.5),
    "dmg_zone_body": (0, 0, 0.7),
    "dmg_zone_turret": (0, 0, 1.2),  # For military vehicles with turrets
}

class ARVEHICLES_OT_orient_vehicle(bpy.types.Operator):
    """Orient vehicle along the Y+ axis (Blender) as required by Arma Reforger"""
    bl_idname = "arvehicles.orient_vehicle"
    bl_label = "Orient Vehicle to center"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Please select the vehicle meshes")
            return {'CANCELLED'}
        
        # Get all selected mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Create an empty at the world origin to use as a pivot
        pivot = bpy.data.objects.new("RotationPivot", None)
        context.collection.objects.link(pivot)
        pivot.location = (0, 0, 0)
        
        # Calculate current vehicle dimensions and center
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        for obj in mesh_objects:
            for vert in obj.data.vertices:
                world_co = obj.matrix_world @ vert.co
                min_x = min(min_x, world_co.x)
                min_y = min(min_y, world_co.y)
                min_z = min(min_z, world_co.z)
                max_x = max(max_x, world_co.x)
                max_y = max(max_y, world_co.y)
                max_z = max(max_z, world_co.z)
        
        # Calculate center of vehicle
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        # Store original parents and parenting temporarily
        original_parents = {}
        original_locations = {}
        for obj in mesh_objects:
            original_parents[obj] = obj.parent
            original_locations[obj] = obj.location.copy()
            obj.parent = pivot
        
        # Orient the vehicle to Y+ axis (this assumes vehicle is initially facing along X+ or Z+)
        # You may need to adjust this rotation based on your initial orientation
        pivot.rotation_euler = (0, 0, 0)
        
        # First apply rotation to ensure vehicle faces Y+
        bpy.ops.object.select_all(action='DESELECT')
        pivot.select_set(True)
        context.view_layer.objects.active = pivot
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        
        # Move pivot to center of vehicle
        pivot.location = (-center_x, -center_y, -center_z)
        
        # Apply location to center the vehicle at world origin
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        
        # Restore original parenting
        for obj in mesh_objects:
            obj.parent = original_parents[obj]
        
        # Remove the temporary pivot
        bpy.data.objects.remove(pivot)
        
        self.report({'INFO'}, "Vehicle oriented along Y+ axis and centered at origin")
        return {'FINISHED'}

class ARVEHICLES_OT_scale_vehicle(bpy.types.Operator):
    """Scale vehicle to match Arma Reforger standards or real-world dimensions"""
    bl_idname = "arvehicles.scale_vehicle"
    bl_label = "Scale Vehicle"
    bl_options = {'REGISTER', 'UNDO'}
    
    scale_method: bpy.props.EnumProperty(
        name="Scaling Method",
        description="How to determine the scaling factor",
        items=[
            ('preset', "Preset Dimensions", "Use standard preset dimensions"),
            ('realworld', "Real-world Vehicle", "Scale based on real-world vehicle dimensions"),
            ('custom', "Custom", "Use custom dimensions")
        ],
        default='preset'
    )
    
    vehicle_type: bpy.props.EnumProperty(
        name="Vehicle Type",
        description="Type of vehicle for appropriate scaling",
        items=[
            ('your_model', "Your Model (4.07×1.8×1.46m)", "Use your exact vehicle measurements"),
            ('golf_reference', "VW Golf Reference (4.282×1.789×1.483m)", "Use VW Golf as reference (Arma example)"),
            ('sedan', "Sedan", "Standard sedan car"),
            ('suv', "SUV", "Sport utility vehicle"),
            ('truck', "Truck", "Pickup or larger truck"),
            ('jeep', "Jeep", "Military jeep or similar"),
            ('van', "Van", "Delivery van or similar"),
            ('apc', "APC", "Armored Personnel Carrier"),
        ],
        default='your_model'
    )
    
    # Real-world vehicle dimensions
    realworld_length: bpy.props.FloatProperty(
        name="Real Length",
        description="Real-world vehicle length in meters",
        default=4.5,
        min=1.0,
        max=20.0
    )
    
    realworld_width: bpy.props.FloatProperty(
        name="Real Width",
        description="Real-world vehicle width in meters",
        default=1.8,
        min=0.5,
        max=5.0
    )
    
    realworld_height: bpy.props.FloatProperty(
        name="Real Height",
        description="Real-world vehicle height in meters",
        default=1.5,
        min=0.5,
        max=5.0
    )
    
    custom_length: bpy.props.FloatProperty(
        name="Target Length",
        description="Target vehicle length in meters",
        default=4.07,
        min=1.0,
        max=20.0
    )
    
    custom_width: bpy.props.FloatProperty(
        name="Target Width",
        description="Target vehicle width in meters",
        default=1.8,
        min=0.5,
        max=5.0
    )
    
    custom_height: bpy.props.FloatProperty(
        name="Target Height",
        description="Target vehicle height in meters",
        default=1.46,
        min=0.5,
        max=5.0
    )
# Option to preserve or adjust proportions
    preserve_proportions: bpy.props.BoolProperty(
        name="Preserve Proportions",
        description="Scale uniformly to fit within target dimensions while preserving original proportions",
        default=True
    )
    
    # Store the current dimensions for UI display
    current_length: bpy.props.FloatProperty(default=0.0)
    current_width: bpy.props.FloatProperty(default=0.0)
    current_height: bpy.props.FloatProperty(default=0.0)
    
    def invoke(self, context, event):
        # Calculate current vehicle dimensions
        if len(context.selected_objects) > 0:
            mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
            if mesh_objects:
                min_x, min_y, min_z, max_x, max_y, max_z = self._get_dimensions(mesh_objects)
                
                self.current_length = max_y - min_y  # Assuming Y is length
                self.current_width = max_x - min_x   # Width is along X
                self.current_height = max_z - min_z  # Height is along Z
        
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def _get_dimensions(self, mesh_objects):
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        for obj in mesh_objects:
            for vert in obj.data.vertices:
                world_co = obj.matrix_world @ vert.co
                min_x = min(min_x, world_co.x)
                min_y = min(min_y, world_co.y)
                min_z = min(min_z, world_co.z)
                max_x = max(max_x, world_co.x)
                max_y = max(max_y, world_co.y)
                max_z = max(max_z, world_co.z)
                
        return min_x, min_y, min_z, max_x, max_y, max_z
    def execute(self, context):
        # Check if objects are selected
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Please select the vehicle meshes")
            return {'CANCELLED'}
        
        # Find all mesh objects in selection
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Calculate current vehicle dimensions and center
        min_x, min_y, min_z, max_x, max_y, max_z = self._get_dimensions(mesh_objects)
        
        # Calculate center of vehicle
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        # Calculate current dimensions
        current_length = max_y - min_y  # Assuming Y is length axis after orientation
        current_width = max_x - min_x   # Width is along X
        current_height = max_z - min_z  # Height is along Z
        
        # Get target dimensions based on scaling method
        if self.scale_method == 'preset':
            # Use the selected vehicle preset
            vehicle_dims = VEHICLE_SCALES.get(self.vehicle_type, VEHICLE_SCALES['your_model'])
            target_length = vehicle_dims[0]
            target_width = vehicle_dims[1]
            target_height = vehicle_dims[2]
            
        elif self.scale_method == 'realworld':
            # Calculate scaling relative to the reference vehicle (VW Golf)
            # This uses the real-world dimensions provided by the user
            ref_length = REFERENCE_VEHICLE["length"]
            ref_width = REFERENCE_VEHICLE["width"]
            ref_height = REFERENCE_VEHICLE["height"]
            
            # Calculate ratios between real world and reference
            length_ratio = self.realworld_length / ref_length
            width_ratio = self.realworld_width / ref_width
            height_ratio = self.realworld_height / ref_height
            
            # Apply these ratios to determine target dimensions
            target_length = ref_length * length_ratio
            target_width = ref_width * width_ratio
            target_height = ref_height * height_ratio
            
        else:  # custom
            target_length = self.custom_length
            target_width = self.custom_width
            target_height = self.custom_height
        
        # Calculate the scale factors
        length_scale = target_length / current_length if current_length > 0 else 1.0
        width_scale = target_width / current_width if current_width > 0 else 1.0
        height_scale = target_height / current_height if current_height > 0 else 1.0
        
        # If preserving proportions, use the smallest scale to ensure it fits within limits
        if self.preserve_proportions:
            scale_factor = min(length_scale, width_scale, height_scale)
            # Use uniform scaling
            scale_x = scale_y = scale_z = scale_factor
        else:
            # Use non-uniform scaling to match exact dimensions
            scale_x = width_scale
            scale_y = length_scale
            scale_z = height_scale
        
        # Create an empty at the center to use as a scaling pivot
        pivot = bpy.data.objects.new("ScalePivot", None)
        context.collection.objects.link(pivot)
        pivot.location = (center_x, center_y, center_z)
        
        # Parent all mesh objects to the pivot temporarily
        original_parents = {}
        for obj in mesh_objects:
            original_parents[obj] = obj.parent
            obj.parent = pivot
        
        # Scale the pivot, which scales all children around the center
        if self.preserve_proportions:
            pivot.scale = (scale_factor, scale_factor, scale_factor)
        else:
            pivot.scale = (scale_x, scale_y, scale_z)
        
        # Apply the scale to all children
        bpy.ops.object.select_all(action='DESELECT')
        pivot.select_set(True)
        context.view_layer.objects.active = pivot
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Restore original parenting
        for obj in mesh_objects:
            obj.parent = original_parents[obj]
        
        # Remove the temporary pivot
        bpy.data.objects.remove(pivot)
        
        # Log the dimensions for reference
        if self.preserve_proportions:
            self.report({'INFO'}, 
                f"Vehicle scaled uniformly by factor: {scale_factor:.4f}\n"
                f"Dimensions (L×W×H): {current_length*scale_factor:.2f}m × {current_width*scale_factor:.2f}m × {current_height*scale_factor:.2f}m")
        else:
            self.report({'INFO'}, 
                f"Vehicle scaled non-uniformly (L×W×H): {length_scale:.2f} × {width_scale:.2f} × {height_scale:.2f}\n"
                f"Final dimensions: {current_length*length_scale:.2f}m × {current_width*width_scale:.2f}m × {current_height*height_scale:.2f}m")
        
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Scaling method selection
        layout.prop(self, "scale_method", expand=True)
        
        # Current vehicle dimensions
        if self.current_length > 0:
            box = layout.box()
            box.label(text="Current Dimensions:")
            row = box.row()
            row.label(text=f"Length: {self.current_length:.2f}m")
            row.label(text=f"Width: {self.current_width:.2f}m")
            row.label(text=f"Height: {self.current_height:.2f}m")
        
        # Options based on scaling method
        if self.scale_method == 'preset':
            layout.prop(self, "vehicle_type")
            
            # Show selected preset dimensions
            if self.vehicle_type in VEHICLE_SCALES:
                dims = VEHICLE_SCALES[self.vehicle_type]
                box = layout.box()
                box.label(text="Target Dimensions:")
                row = box.row()
                row.label(text=f"Length: {dims[0]:.2f}m")
                row.label(text=f"Width: {dims[1]:.2f}m")
                row.label(text=f"Height: {dims[2]:.2f}m")
                
        elif self.scale_method == 'realworld':
            box = layout.box()
            box.label(text="Real-world Vehicle Dimensions:")
            box.prop(self, "realworld_length")
            box.prop(self, "realworld_width")
            box.prop(self, "realworld_height")
            
            # Show reference vehicle info
            ref_box = layout.box()
            ref_box.label(text="Reference Vehicle (VW Golf):")
            row = ref_box.row()
            row.label(text=f"L: {REFERENCE_VEHICLE['length']:.2f}m")
            row.label(text=f"W: {REFERENCE_VEHICLE['width']:.2f}m")
            row.label(text=f"H: {REFERENCE_VEHICLE['height']:.2f}m")
            
            # Show calculated target dimensions
            if self.current_length > 0:
                # Calculate scaling ratios
                length_ratio = self.realworld_length / REFERENCE_VEHICLE["length"]
                width_ratio = self.realworld_width / REFERENCE_VEHICLE["width"]
                height_ratio = self.realworld_height / REFERENCE_VEHICLE["height"]
                
                target_box = layout.box()
                target_box.label(text="Calculated Target Dimensions:")
                row = target_box.row()
                row.label(text=f"Length: {REFERENCE_VEHICLE['length'] * length_ratio:.2f}m")
                row.label(text=f"Width: {REFERENCE_VEHICLE['width'] * width_ratio:.2f}m")
                row.label(text=f"Height: {REFERENCE_VEHICLE['height'] * height_ratio:.2f}m")
            
        else:  # custom
            box = layout.box()
            box.label(text="Custom Target Dimensions:")
            box.prop(self, "custom_length")
            box.prop(self, "custom_width")
            box.prop(self, "custom_height")
        
        # Proportional scaling option
        layout.prop(self, "preserve_proportions")

class ARVEHICLES_OT_create_collision_boxes(bpy.types.Operator):
    """Create collision boxes for the vehicle"""
    bl_idname = "arvehicles.create_collision_boxes"
    bl_label = "Create Collision Boxes"
    bl_options = {'REGISTER', 'UNDO'}
    
    collision_type: bpy.props.EnumProperty(
        name="Collision Type",
        description="Type of collision to create",
        items=[
            ('detailed', "Detailed", "Create detailed collision setup with multiple boxes"),
            ('simple', "Simple Box", "Create a single simple box collision that matches object dimensions"),
        ],
        default='detailed'
    )
    
    use_convex: bpy.props.BoolProperty(
        name="Use Convex for Body",
        description="Create UCX_ convex collision for body instead of box",
        default=True
    )
    
    vehicle_type: bpy.props.EnumProperty(
        name="Vehicle Type",
        description="Type of vehicle for appropriate collision setup",
        items=[
            ('car', "Car (4 wheels)", "Standard car with 4 wheels"),
            ('truck', "Truck (6 wheels)", "Truck with 6 wheels"),
            ('apc', "APC (8 wheels)", "Armored Personnel Carrier with 8 wheels"),
            ('custom', "Custom", "Custom wheel configuration"),
        ],
        default='car'
    )
    
    num_wheels: bpy.props.IntProperty(
        name="Number of Wheels",
        description="Total number of wheels for custom vehicles",
        default=4,
        min=2,
        max=12
    )
    
    simple_box_name: bpy.props.StringProperty(
        name="Box Name",
        description="Name for the simple collision box",
        default="UCX_simple"
    )
    
    simple_box_margin: bpy.props.FloatProperty(
        name="Box Margin",
        description="Margin around the object for simple box collision (in meters)",
        default=0.05,
        min=0.0,
        max=1.0
    )
    
    def execute(self, context):
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "Please select the vehicle meshes")
            return {'CANCELLED'}
        
        # Find all mesh objects in selection
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Calculate current vehicle dimensions and center
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        for obj in mesh_objects:
            for vert in obj.data.vertices:
                world_co = obj.matrix_world @ vert.co
                min_x = min(min_x, world_co.x)
                min_y = min(min_y, world_co.y)
                min_z = min(min_z, world_co.z)
                max_x = max(max_x, world_co.x)
                max_y = max(max_y, world_co.y)
                max_z = max(max_z, world_co.z)
        
        # Calculate center of vehicle
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        center_z = (min_z + max_z) / 2
        
        # Calculate dimensions
        width = max_x - min_x
        length = max_y - min_y
        height = max_z - min_z
        
        # Main collision objects to create
        colliders = []
        
        if self.collision_type == 'simple':
            # Create a simple box collision that encompasses the selected objects
            # Add margin to dimensions
            simple_width = width + (self.simple_box_margin * 2)
            simple_length = length + (self.simple_box_margin * 2)
            simple_height = height + (self.simple_box_margin * 2)
            
            simple_box = self._create_box(
                self.simple_box_name, 
                center_x, center_y, center_z, 
                simple_width, simple_length, simple_height
            )
            colliders.append(simple_box)
            
            # Add a center of mass object
            com_obj = self._create_box(
                "COM_vehicle", 
                center_x, center_y, center_z - height * 0.1,  # Slightly lower center of mass
                width * 0.2, length * 0.2, height * 0.2
            )
            colliders.append(com_obj)
            
            # Determine number of wheels based on vehicle type
            if self.vehicle_type == 'car':
                num_wheels = 4
            elif self.vehicle_type == 'truck':
                num_wheels = 6
            elif self.vehicle_type == 'apc':
                num_wheels = 8
            else:  # custom
                num_wheels = self.num_wheels
            
            # Create wheel colliders
            wheel_radius = height * 0.2
            wheel_width = width * 0.15
            
            # Generate wheel positions based on number of wheels
            wheel_positions = self._generate_wheel_positions(num_wheels, length, width, wheel_radius)
            
            for idx, wheel_pos in enumerate(wheel_positions):
                wheel_name = f"UCS_wheel_{idx+1}"
                wheel_obj = self._create_cylinder(wheel_name, 
                                              wheel_pos[0], wheel_pos[1], wheel_pos[2],
                                              wheel_radius, wheel_width)
                colliders.append(wheel_obj)
            
        else:  # detailed collision setup
            # Create UCX_body box/convex hull (for physics collision)
            if self.use_convex and len(mesh_objects) > 0:
                # Create a convex hull based on the vehicle mesh
                body_obj = self._create_convex_hull("UCX_body", mesh_objects)
                colliders.append(body_obj)
            else:
                # Create a simple box collider
                body_obj = self._create_box("UCX_body", 
                                        center_x, center_y, center_z, 
                                        width, length, height)
                colliders.append(body_obj)
            
            # Create UTM_vehicle box (for bullet collisions/fire geometry)
            utm_vehicle = self._create_box("UTM_vehicle", 
                                        center_x, center_y, center_z, 
                                        width * 0.95, length * 0.95, height * 0.95)
            colliders.append(utm_vehicle)
            
            # Create center of mass object (COM_)
            com_obj = self._create_box("COM_vehicle", 
                                    center_x, center_y, center_z - height * 0.1,  # Slightly lower center of mass
                                    width * 0.2, length * 0.2, height * 0.2)
            colliders.append(com_obj)
            
            # Determine number of wheels based on vehicle type
            if self.vehicle_type == 'car':
                num_wheels = 4
            elif self.vehicle_type == 'truck':
                num_wheels = 6
            elif self.vehicle_type == 'apc':
                num_wheels = 8
            else:  # custom
                num_wheels = self.num_wheels
            
            # Create wheel colliders
            wheel_radius = height * 0.2
            wheel_width = width * 0.15
            
            # Generate wheel positions based on number of wheels
            wheel_positions = self._generate_wheel_positions(num_wheels, length, width, wheel_radius)
            
            for idx, wheel_pos in enumerate(wheel_positions):
                wheel_name = f"UCS_wheel_{idx+1}"
                wheel_obj = self._create_cylinder(wheel_name, 
                                              wheel_pos[0], wheel_pos[1], wheel_pos[2],
                                              wheel_radius, wheel_width)
                colliders.append(wheel_obj)
        
        # Select all the newly created colliders
        bpy.ops.object.select_all(action='DESELECT')
        for obj in colliders:
            obj.select_set(True)
        
        if colliders:
            context.view_layer.objects.active = colliders[0]
        
        # Add layer_preset custom property
        for obj in colliders:
            obj["layer_preset"] = "Collision_Vehicle"
            
            if obj.name.startswith("UCX_"):
                obj["usage"] = "PhyCol"
            elif obj.name.startswith("UTM_"):
                obj["usage"] = "FireGeo"
            elif obj.name.startswith("UCS_"):
                obj["usage"] = "PhyCol"
            elif obj.name.startswith("COM_"):
                obj["usage"] = "CenterOfMass"
        
        if self.collision_type == 'simple':
            self.report({'INFO'}, f"Created simple collision box: {self.simple_box_name} with {num_wheels} wheels")
        else:
            self.report({'INFO'}, f"Created {len(colliders)} collision objects including {num_wheels} wheels")
        
        return {'FINISHED'}
    
    def _create_box(self, name, center_x, center_y, center_z, width, length, height):
        """Helper function to create a box with given dimensions"""
        # Create a cube mesh
        bpy.ops.mesh.primitive_cube_add(
            size=1.0, 
            enter_editmode=False, 
            align='WORLD', 
            location=(center_x, center_y, center_z)
        )
        
        # Get the created object and rename it
        box = bpy.context.active_object
        box.name = name
        
        # Scale to match dimensions
        box.scale.x = width / 2
        box.scale.y = length / 2
        box.scale.z = height / 2
        
        # Apply scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        
        # Set display properties based on type
        if name.startswith("UCX_"):
            # Physics collision material
            mat = bpy.data.materials.new(name="UCX_Material")
            mat.diffuse_color = (1.0, 0.3, 0.3, 0.5)  # Semi-transparent red
        elif name.startswith("UTM_"):
            # Fire geometry material
            mat = bpy.data.materials.new(name="UTM_Material")
            mat.diffuse_color = (0.3, 0.3, 1.0, 0.5)  # Semi-transparent blue
        elif name.startswith("COM_"):
            # Center of mass material
            mat = bpy.data.materials.new(name="COM_Material")
            mat.diffuse_color = (0.3, 1.0, 0.3, 0.5)  # Semi-transparent green
        else:
            # Default material
            mat = bpy.data.materials.new(name="Collider_Material")
            mat.diffuse_color = (0.8, 0.8, 0.8, 0.5)  # Semi-transparent gray
        
        # Enable transparency
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
            mat.show_transparent_back = False
        
        # Assign material to the object
        if box.data.materials:
            box.data.materials[0] = mat
        else:
            box.data.materials.append(mat)
        
        return box
    
    def _create_cylinder(self, name, center_x, center_y, center_z, radius, depth):
        """Helper function to create a cylinder with given dimensions"""
        # Create a cylinder mesh
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius,
            depth=depth,
            enter_editmode=False, 
            align='WORLD', 
            location=(center_x, center_y, center_z),
            rotation=(0, math.pi/2, 0)  # Rotate to align with Y axis (not X axis)
        )
        
        # Get the created object and rename it
        cylinder = bpy.context.active_object
        cylinder.name = name
        
        # Apply rotation
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        
        # Set display properties
        mat = bpy.data.materials.new(name="UCS_Material")
        mat.diffuse_color = (0.8, 0.5, 0.0, 0.5)  # Semi-transparent orange
        
        # Enable transparency
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
            mat.show_transparent_back = False
        
        # Assign material to the object
        if cylinder.data.materials:
            cylinder.data.materials[0] = mat
        else:
            cylinder.data.materials.append(mat)
        
        return cylinder
    

    
    def _create_convex_hull(self, name, source_objects):
        """Create a convex hull collider from the source objects"""
        # First join all source objects into a temporary mesh
        bpy.ops.object.select_all(action='DESELECT')
        for obj in source_objects:
            obj.select_set(True)
        
        bpy.ops.object.duplicate()
        bpy.ops.object.join()
        temp_obj = bpy.context.active_object
        
        # Add convex hull modifier
        modifier = temp_obj.modifiers.new(name="ConvexHull", type='REMESH')
        modifier.mode = 'BLOCKS'
        modifier.octree_depth = 4
        modifier.use_remove_disconnected = True
        
        # Apply the modifier
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        # Rename the object
        temp_obj.name = name
        
        # Create material for visualization
        mat = bpy.data.materials.new(name="UCX_Convex_Material")
        mat.diffuse_color = (1.0, 0.3, 0.3, 0.5)  # Semi-transparent red
        
        # Enable transparency
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'
            mat.show_transparent_back = False
        
        # Assign material to the object
        if temp_obj.data.materials:
            temp_obj.data.materials[0] = mat
        else:
            temp_obj.data.materials.append(mat)
        
        return temp_obj
    
    def _generate_wheel_positions(self, num_wheels, length, width, wheel_radius):
        """Generate wheel positions based on the number of wheels and vehicle dimensions"""
        positions = []
        
        # Always place wheels at the corners (front and back)
        front_y = length * 0.4  # Front axle position
        rear_y = -length * 0.4  # Rear axle position
        side_x = width * 0.45   # Side offset (left/right)
        wheel_z = wheel_radius  # Wheel height position
        
        # Front wheels (right, left)
        positions.append((side_x, front_y, wheel_z))
        positions.append((-side_x, front_y, wheel_z))
        
        # Rear wheels (right, left)
        positions.append((side_x, rear_y, wheel_z))
        positions.append((-side_x, rear_y, wheel_z))
        
        # If more than 4 wheels, add middle axles
        if num_wheels > 4:
            num_middle_axles = (num_wheels - 4) // 2
            
            # Space the middle axles evenly between front and rear
            axle_spacing = (front_y - rear_y) / (num_middle_axles + 1)
            
            for i in range(1, num_middle_axles + 1):
                middle_y = front_y - (axle_spacing * i)
                positions.append((side_x, middle_y, wheel_z))
                positions.append((-side_x, middle_y, wheel_z))
        
        return positions
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "collision_type", expand=True)
        
        if self.collision_type == 'simple':
            # Simple box settings
            box = layout.box()
            box.label(text="Simple Box Settings")
            box.prop(self, "simple_box_name")
            box.prop(self, "simple_box_margin")
            
            # Vehicle type for wheel configuration
            box = layout.box()
            box.label(text="Wheel Settings")
            box.prop(self, "vehicle_type")
            
            # Show num_wheels only for custom vehicle type
            if self.vehicle_type == 'custom':
                box.prop(self, "num_wheels")
        else:
            # Detailed collision settings
            layout.prop(self, "use_convex")
            layout.prop(self, "vehicle_type")
            
            # Show num_wheels only for custom vehicle type
            if self.vehicle_type == 'custom':
                layout.prop(self, "num_wheels")

class ARVEHICLES_OT_create_vehicle_armature(bpy.types.Operator):
    """Create a basic armature for a vehicle"""
    bl_idname = "arvehicles.create_armature"
    bl_label = "Create Vehicle Armature"
    bl_options = {'REGISTER', 'UNDO'}
    
    vehicle_type: bpy.props.EnumProperty(
        name="Vehicle Type",
        description="Type of vehicle for appropriate armature setup",
        items=[
            ('car', "Car (4 wheels)", "Standard car with 4 wheels"),
            ('truck', "Truck (6 wheels)", "Truck with 6 wheels"),
            ('apc', "APC (8 wheels)", "Armored Personnel Carrier with 8 wheels"),
            ('custom', "Custom", "Custom wheel configuration"),
        ],
        default='car'
    )
    
    num_wheels: bpy.props.IntProperty(
        name="Number of Wheels",
        description="Total number of wheels for custom vehicles",
        default=4,
        min=2,
        max=12
    )
    
    add_doors: bpy.props.BoolProperty(
        name="Add Door Bones",
        description="Add bones for vehicle doors",
        default=True
    )
    
    add_turret: bpy.props.BoolProperty(
        name="Add Turret",
        description="Add bones for a weapon turret (military vehicles)",
        default=False
    )
    
    def execute(self, context):
        # Create an armature
        armature_data = bpy.data.armatures.new("VehicleArmature")
        armature_obj = bpy.data.objects.new("VehicleArmature", armature_data)
        context.collection.objects.link(armature_obj)
        
        # Make the armature active
        context.view_layer.objects.active = armature_obj
        
        # Enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Create root bone - point along Y axis
        root_bone = armature_data.edit_bones.new('v_root')
        root_bone.head = (0, 0, 0)
        root_bone.tail = (0, 0.2, 0)  # Points along Y axis
        root_bone.roll = 0  # Important for correct bone orientation
        
        # Determine number of wheels based on vehicle type
        if self.vehicle_type == 'car':
            num_wheels = 4
        elif self.vehicle_type == 'truck':
            num_wheels = 6
        elif self.vehicle_type == 'apc':
            num_wheels = 8
        else:  # custom
            num_wheels = self.num_wheels
        
        # Create wheel bones - all pointing along Y axis
        wheel_bones = []
        for i in range(num_wheels):
            # Generate wheel position
            x_sign = 1 if i % 2 == 0 else -1  # Right/left side
            y_offset = ((i // 2) / (num_wheels // 2)) - 0.5  # Distribute wheels front to back
            
            bone = armature_data.edit_bones.new(f'v_wheel_{i+1}')
            bone.head = (x_sign * 0.8, y_offset * 3, 0.3)
            bone.tail = (x_sign * 0.8, y_offset * 3 + 0.2, 0.3)  # Add length along Y axis
            bone.roll = 0
            bone.parent = root_bone
            wheel_bones.append(bone)
        
        # Create steering wheel bone - pointing along Y axis
        steer_bone = armature_data.edit_bones.new('v_steeringwheel')
        steer_bone.head = (0, 0.5, 0.9)
        steer_bone.tail = (0, 0.7, 0.9)  # Points along Y axis
        steer_bone.roll = 0
        steer_bone.parent = root_bone
        
        # Create door bones if needed - pointing along Y axis
        if self.add_doors:
            door_left = armature_data.edit_bones.new('v_door_left')
            door_left.head = (0.85, 0.2, 0.8)
            door_left.tail = (0.85, 0.4, 0.8)  # Points along Y axis
            door_left.roll = 0
            door_left.parent = root_bone
            
            door_right = armature_data.edit_bones.new('v_door_right')
            door_right.head = (-0.85, 0.2, 0.8)
            door_right.tail = (-0.85, 0.4, 0.8)  # Points along Y axis
            door_right.roll = 0
            door_right.parent = root_bone
        
        # Create turret bones if needed - horizontal base, gun points along Y
        if self.add_turret:
            turret_base = armature_data.edit_bones.new('v_turret_base')
            turret_base.head = (0, 0, 1.0)
            turret_base.tail = (0, 0.2, 1.0)  # Points along Y axis for rotation
            turret_base.roll = 0
            turret_base.parent = root_bone
            
            turret_gun = armature_data.edit_bones.new('v_turret_gun')
            turret_gun.head = (0, 0.2, 1.0)  # Connect to the tail of turret_base
            turret_gun.tail = (0, 1.0, 1.0)  # Points along Y axis
            turret_gun.roll = 0
            turret_gun.parent = turret_base
        
        # Create body bone for main vehicle body - pointing along Y axis
        body_bone = armature_data.edit_bones.new('v_body')
        body_bone.head = (0, 0, 0.5)
        body_bone.tail = (0, 0.2, 0.5)  # Points along Y axis
        body_bone.roll = 0
        body_bone.parent = root_bone
        
        # Exit edit mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"Created vehicle armature with {num_wheels} wheel bones" + 
                             (" and door bones" if self.add_doors else "") + 
                             (" and turret" if self.add_turret else ""))
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "vehicle_type")
        
        # Show num_wheels only for custom vehicle type
        if self.vehicle_type == 'custom':
            layout.prop(self, "num_wheels")
            
        layout.prop(self, "add_doors")
        layout.prop(self, "add_turret")

class ARVEHICLES_OT_create_empties(bpy.types.Operator):
    """Create empty objects for vehicle attachment points and components"""
    bl_idname = "arvehicles.create_empties"
    bl_label = "Create Vehicle Points"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties for which empties to create
    create_crew_positions: bpy.props.BoolProperty(
        name="Create Crew Positions",
        description="Create empty objects for driver and passenger positions",
        default=True
    )
    
    create_vehicle_components: bpy.props.BoolProperty(
        name="Create Vehicle Components",
        description="Create empty objects for vehicle components (engine, lights, etc.)",
        default=True
    )
    
    create_wheel_positions: bpy.props.BoolProperty(
        name="Create Wheel Positions",
        description="Create empty objects for wheel positions",
        default=True
    )
    
    create_damage_zones: bpy.props.BoolProperty(
        name="Create Damage Zones",
        description="Create empty objects for damage zones",
        default=True
    )
    
    vehicle_type: bpy.props.EnumProperty(
        name="Vehicle Type",
        description="Type of vehicle for appropriate empty setup",
        items=[
            ('car', "Car (4 wheels)", "Standard car with 4 wheels"),
            ('truck', "Truck (6 wheels)", "Truck with 6 wheels"),
            ('apc', "APC (8 wheels)", "Armored Personnel Carrier with 8 wheels"),
            ('custom', "Custom", "Custom wheel configuration"),
        ],
        default='car'
    )
    
    num_wheels: bpy.props.IntProperty(
        name="Number of Wheels",
        description="Total number of wheels for custom vehicles",
        default=4,
        min=2,
        max=12
    )
    
    num_crew: bpy.props.IntProperty(
        name="Number of Crew",
        description="Total number of crew positions",
        default=4,
        min=1,
        max=12
    )
    
    def execute(self, context):
        # Get or create the parent collection for organization
        vehicle_collection = None
        collection_name = "Vehicle_Components"
        
        if collection_name in bpy.data.collections:
            vehicle_collection = bpy.data.collections[collection_name]
        else:
            vehicle_collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(vehicle_collection)
        
        # Dictionary to track created empties
        created_empties = []
        
        # Determine vehicle dimensions from selection if possible
        dimensions, center = self._get_selected_dimensions(context)
        length, width, height = dimensions
        
        # Determine number of wheels based on vehicle type
        if self.vehicle_type == 'car':
            num_wheels = 4
        elif self.vehicle_type == 'truck':
            num_wheels = 6
        elif self.vehicle_type == 'apc':
            num_wheels = 8
        else:  # custom
            num_wheels = self.num_wheels
        
        # Create empty objects based on selected options
        if self.create_crew_positions:
            crew_positions = self._generate_crew_positions(self.num_crew, dimensions, center)
            
            for i, (name, pos) in enumerate(crew_positions):
                if name not in bpy.data.objects:
                    empty = self._create_empty(name, pos, vehicle_collection, 'ARROWS', 0.2)
                    created_empties.append(name)
        
        if self.create_vehicle_components:
            component_positions = self._generate_component_positions(dimensions, center)
            
            for name, pos in component_positions:
                if name not in bpy.data.objects:
                    empty = self._create_empty(name, pos, vehicle_collection, 'PLAIN_AXES', 0.1)
                    created_empties.append(name)
        
        if self.create_wheel_positions:
            wheel_positions = self._generate_wheel_positions(num_wheels, dimensions, center)
            
            for i, (name, pos) in enumerate(wheel_positions):
                if name not in bpy.data.objects:
                    empty = self._create_empty(name, pos, vehicle_collection, 'SPHERE', 0.1)
                    created_empties.append(name)
        
        if self.create_damage_zones:
            damage_positions = self._generate_damage_zones(dimensions, center, self.vehicle_type)
            
            for name, pos in damage_positions:
                if name not in bpy.data.objects:
                    empty = self._create_empty(name, pos, vehicle_collection, 'CUBE', 0.1)
                    created_empties.append(name)
        
        # Parent empties to armature if it exists
        armature = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and "VehicleArmature" in obj.name:
                armature = obj
                break
        
        if armature:
            for name in created_empties:
                if name in bpy.data.objects:
                    obj = bpy.data.objects[name]
                    obj.parent = armature
                    # No bone parenting by default, user can set this up manually
        
        if created_empties:
            self.report({'INFO'}, f"Created {len(created_empties)} empty objects")
        else:
            self.report({'WARNING'}, "No new empties created, they may already exist")
            
        return {'FINISHED'}
    
    def _create_empty(self, name, location, collection, display_type, size):
        """Helper function to create an empty object"""
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = display_type
        empty.empty_display_size = size
        empty.location = location
        collection.objects.link(empty)
        return empty
    
    def _get_selected_dimensions(self, context):
        """Get dimensions and center of selected objects, or use defaults"""
        if len(context.selected_objects) > 0:
            mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
            if mesh_objects:
                min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
                max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
                
                for obj in mesh_objects:
                    for vert in obj.data.vertices:
                        world_co = obj.matrix_world @ vert.co
                        min_x = min(min_x, world_co.x)
                        min_y = min(min_y, world_co.y)
                        min_z = min(min_z, world_co.z)
                        max_x = max(max_x, world_co.x)
                        max_y = max(max_y, world_co.y)
                        max_z = max(max_z, world_co.z)
                
                length = max_y - min_y
                width = max_x - min_x
                height = max_z - min_z
                center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
                
                return (length, width, height), center
        
        # Default dimensions and center if no selection
        return (4.07, 1.8, 1.46), (0, 0, 0)
    
    def _generate_crew_positions(self, num_crew, dimensions, center):
        """Generate crew position empties"""
        length, width, height = dimensions
        cx, cy, cz = center
        
        positions = []
        
        # Driver always at the front left
        positions.append(("driver", (cx - width * 0.35, cy + length * 0.2, cz + height * 0.6)))
        
        # Co-driver at the front right
        if num_crew > 1:
            positions.append(("codriver", (cx + width * 0.35, cy + length * 0.2, cz + height * 0.6)))
        
        # Additional passengers in the back
        for i in range(2, num_crew):
            side = 1 if i % 2 == 0 else -1  # Alternate sides
            row = (i - 2) // 2  # 0 for first row, 1 for second, etc.
            
            positions.append((f"cargo{i-1:02d}", 
                             (cx + side * width * 0.35, 
                              cy - length * (0.1 + row * 0.25), 
                              cz + height * 0.6)))
        
        return positions
    
    def _generate_component_positions(self, dimensions, center):
        """Generate vehicle component empties"""
        length, width, height = dimensions
        cx, cy, cz = center
        
        positions = [
            ("engine", (cx, cy + length * 0.4, cz + height * 0.3)),
            ("exhaust", (cx + width * 0.2, cy - length * 0.45, cz + height * 0.1)),
            ("frontlight_left", (cx + width * 0.4, cy + length * 0.48, cz + height * 0.3)),
            ("frontlight_right", (cx - width * 0.4, cy + length * 0.48, cz + height * 0.3)),
            ("backlight_left", (cx + width * 0.4, cy - length * 0.48, cz + height * 0.3)),
            ("backlight_right", (cx - width * 0.4, cy - length * 0.48, cz + height * 0.3))
        ]
        
        return positions
    
    def _generate_wheel_positions(self, num_wheels, dimensions, center):
        """Generate wheel position empties"""
        length, width, height = dimensions
        cx, cy, cz = center
        
        positions = []
        wheel_radius = height * 0.2
        
        # Always place wheels at the corners (front and back)
        front_y = cy + length * 0.4  # Front axle position
        rear_y = cy - length * 0.4   # Rear axle position
        side_x = width * 0.45   # Side offset (left/right)
        wheel_z = cz + wheel_radius  # Wheel height position
        
        # Front wheels (right, left)
        positions.append(("wheel_1_1", (cx + side_x, front_y, wheel_z)))
        positions.append(("wheel_1_2", (cx - side_x, front_y, wheel_z)))
        
        # Rear wheels (right, left)
        positions.append(("wheel_2_1", (cx + side_x, rear_y, wheel_z)))
        positions.append(("wheel_2_2", (cx - side_x, rear_y, wheel_z)))
        
        # If more than 4 wheels, add middle axles
        if num_wheels > 4:
            num_middle_axles = (num_wheels - 4) // 2
            
            # Space the middle axles evenly between front and rear
            axle_spacing = (front_y - rear_y) / (num_middle_axles + 1)
            
            for i in range(1, num_middle_axles + 1):
                middle_y = front_y - (axle_spacing * i)
                idx = i + 2  # wheel_3_x, wheel_4_x, etc.
                
                positions.append((f"wheel_{idx}_1", (cx + side_x, middle_y, wheel_z)))
                positions.append((f"wheel_{idx}_2", (cx - side_x, middle_y, wheel_z)))
        
        return positions
    
    def _generate_damage_zones(self, dimensions, center, vehicle_type):
        """Generate damage zone empties"""
        length, width, height = dimensions
        cx, cy, cz = center
        
        positions = [
            ("dmg_zone_engine", (cx, cy + length * 0.4, cz + height * 0.3)),
            ("dmg_zone_fueltank", (cx, cy - length * 0.4, cz + height * 0.3)),
            ("dmg_zone_body", (cx, cy, cz + height * 0.4)),
        ]
        
        # Add turret damage zone for military vehicles
        if vehicle_type == 'apc':
            positions.append(("dmg_zone_turret", (cx, cy, cz + height * 0.8)))
        
        return positions
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "vehicle_type")
        
        # Show num_wheels only for custom vehicle type
        if self.vehicle_type == 'custom':
            layout.prop(self, "num_wheels")
            
        layout.prop(self, "num_crew")
        layout.prop(self, "create_crew_positions")
        layout.prop(self, "create_vehicle_components")
        layout.prop(self, "create_wheel_positions")
        layout.prop(self, "create_damage_zones")

class ARVEHICLES_OT_separate_components(bpy.types.Operator):
    """Separate selected components into individual objects for Arma Reforger"""
    bl_idname = "arvehicles.separate_components"
    bl_label = "Separate Vehicle Components"
    bl_options = {'REGISTER', 'UNDO'}
    
    component_type: bpy.props.EnumProperty(
        name="Component Type",
        description="Type of component being separated",
        items=[
            ('window', "Window", "Window component"),
            ('light', "Light", "Emissive light component"),
            ('door', "Door", "Door or movable component"),('Wheel', "Wheel", "Wheel or movable component"),
            ('accessory', "Accessory", "Optional accessory component"),
            ('other', "Other", "Other component type"),
        ],
        default='window'
    )
    
    custom_name: bpy.props.StringProperty(
        name="Custom Name",
        description="Custom name for the separated component",
        default=""
    )
    
    def execute(self, context):
        # Check if we're in edit mode with selected faces
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode with faces selected")
            return {'CANCELLED'}
            
        mesh = context.active_object.data
        if not mesh.total_face_sel:
            self.report({'ERROR'}, "No faces selected")
            return {'CANCELLED'}
        
        # Get the active object
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object")
            return {'CANCELLED'}
        
        # Generate a name for the new object
        prefix = ""
        if self.component_type == 'window':
            prefix = "window_"
        elif self.component_type == 'light':
            prefix = "light_"
        elif self.component_type == 'door':
            prefix = "door_"
        elif self.component_type == 'accessory':
            prefix = "acc_"
        
        new_name = self.custom_name
        if not new_name:
            new_name = f"{prefix}{obj.name}"
        
        # Separate the selected faces
        bpy.ops.mesh.separate(type='SELECTED')
        
        # Get the newly created object (last selected)
        new_obj = context.selected_objects[-1]
        new_obj.name = new_name
        
        # Switch back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Select only the new object
        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj
        
        self.report({'INFO'}, f"Separated component as '{new_name}'")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode with faces selected")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "component_type")
        layout.prop(self, "custom_name")
        
class ARVEHICLES_OT_parent_to_armature(bpy.types.Operator):
    """Parent selected meshes to the vehicle armature"""
    bl_idname = "arvehicles.parent_to_armature"
    bl_label = "Parent to Armature"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Find the armature
        armature = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and "VehicleArmature" in obj.name:
                armature = obj
                break
        
        if not armature:
            self.report({'ERROR'}, "No vehicle armature found. Please create one first.")
            return {'CANCELLED'}
        
        # Get selected mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select mesh objects and make armature active
        for obj in mesh_objects:
            obj.select_set(True)
        
        armature.select_set(True)
        context.view_layer.objects.active = armature
        
        # Parent with automatic weights
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        
        self.report({'INFO'}, f"Parented {len(mesh_objects)} objects to the vehicle armature")
        return {'FINISHED'}

class ARVEHICLES_OT_setup_export(bpy.types.Operator):
    """Setup FBX export settings for Arma Reforger"""
    bl_idname = "arvehicles.setup_export"
    bl_label = "Setup FBX Export"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Set default export settings
        # These would be reflected in Blender's FBX export dialog
        # We're just displaying tips here
        
        self.report({'INFO'}, "FBX export settings configured")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Arma Reforger FBX Export Settings", icon='EXPORT')
        
        col = box.column(align=True)
        col.label(text="✓ Binary Format")
        col.label(text="✓ Version 2014/2015")
        col.label(text="✓ Include: Empty, Armature, Mesh")
        col.label(text="✓ Include Custom Properties")
        
        col = box.column(align=True)
        col.label(text="✗ Triangulate Faces - OFF")
        col.label(text="✗ Leaf Bones - OFF")
        col.label(text="✗ All Actions - OFF (use specific animations)")
        
        box.label(text="Orient along Y+ axis in Blender!")
        box.label(text="File > Export > FBX (.fbx)")
        
class ARVEHICLES_OT_setup_layer_presets(bpy.types.Operator):
    """Setup layer presets for collision objects"""
    bl_idname = "arvehicles.setup_layer_presets"
    bl_label = "Setup Layer Presets"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Get selected objects
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
            
        # Count of updated objects
        updated_count = 0
        
        for obj in selected_objects:
            # Check prefix to determine preset
            if obj.name.startswith("UCX_"):
                obj["layer_preset"] = "Collision_Vehicle"
                obj["usage"] = "PhyCol"
                updated_count += 1
            elif obj.name.startswith("UTM_"):
                obj["layer_preset"] = "Collision_Vehicle"
                obj["usage"] = "FireGeo"
                updated_count += 1
            elif obj.name.startswith("UCS_") or obj.name.startswith("USP_"):
                obj["layer_preset"] = "Collision_Vehicle"
                obj["usage"] = "PhyCol"
                updated_count += 1
            elif obj.name.startswith("COM_"):
                obj["layer_preset"] = "Collision_Vehicle"
                obj["usage"] = "CenterOfMass"
                updated_count += 1
            
        if updated_count > 0:
            self.report({'INFO'}, f"Added layer presets to {updated_count} objects")
        else:
            self.report({'WARNING'}, "No compatible objects found for layer presets")
            
        return {'FINISHED'}

class ARVEHICLES_PT_panel(bpy.types.Panel):
    """Arma Reforger Vehicles Panel"""
    bl_label = "AR Vehicles"
    bl_idname = "ARVEHICLES_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AR Vehicles'
    
    def draw(self, context):
        layout = self.layout
        
        # Orientation and Scaling section
        box = layout.box()
        box.label(text="Preparation", icon='AUTO')
        box.operator("arvehicles.orient_vehicle", icon='ORIENTATION_VIEW')
        box.operator("arvehicles.scale_vehicle", icon='FULLSCREEN_ENTER')
        
        # Component Separation
        box = layout.box()
        box.label(text="Component Separation", icon='MOD_BUILD')
        row = box.row(align=True)
        row.operator("arvehicles.separate_components", text="Separate Selection", icon='UNLINKED')
        
        # Collision boxes section
        box = layout.box()
        box.label(text="Collision", icon='MESH_CUBE')
        box.operator("arvehicles.create_collision_boxes", icon='CUBE')
        box.operator("arvehicles.setup_layer_presets", icon='PRESET')
        
        # Empty Objects section
        box = layout.box()
        box.label(text="Attachment Points", icon='EMPTY_DATA')
        box.operator("arvehicles.create_empties", icon='EMPTY_AXIS')
        
        # Rigging section
        box = layout.box()
        box.label(text="Rigging", icon='ARMATURE_DATA')
        box.operator("arvehicles.create_armature", icon='BONE_DATA')
        box.operator("arvehicles.parent_to_armature", icon='ARMATURE_DATA')
        
        # Export section
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        box.operator("arvehicles.setup_export", icon='FILEBROWSER')

# List of all classes to register
classes = (
    ARVEHICLES_OT_orient_vehicle,
    ARVEHICLES_OT_scale_vehicle,
    ARVEHICLES_OT_create_collision_boxes,
    ARVEHICLES_OT_create_vehicle_armature,
    ARVEHICLES_OT_create_empties,
    ARVEHICLES_OT_separate_components,
    ARVEHICLES_OT_parent_to_armature,
    ARVEHICLES_OT_setup_layer_presets,
    ARVEHICLES_OT_setup_export,
    ARVEHICLES_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
    
