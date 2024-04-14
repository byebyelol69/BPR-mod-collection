#fuck your community niggers
#-*- coding:utf-8 -*-

## TO DO

# ok - export whole deformationspec
# ok - Remove "if in locals()"
# xx - Change default materialStates to doublesided
# ok - Change PS3 ported materialStates to doublesided
# ok - Fix empty propinstancedata
# ok - create an empty instance list if instances is empty (TRK_022) (line 1263)
# ok - IDs with - or space not packing (packer)
# ok - lod_distance
# ok - object_index
# xx - renderable_index
# xx - Export vertices in the same order (equal polygonsouplist)
# ok - export empty collision
# ok - export collision
# ok - AT - export sensors, tagpoints, drivenpoints
# xx - move other AT files (might bug)
# ok - pack file
# ok - ver wheels (ver traffic cars)
# ok - decode effect types
# ok - write mOffsetFromAAndWeightA, mOffsetFromBAndWeightB, mInitialPositionAndDetachThreshold
# ok - write body matrix
# ok - ver lights/effects
# ok - write GraphicsStub file
# ok - material with animation (sample on library 26_20_D3_89.dat, 9A_41_AD_7F.dat, 57_56_1A_DA.dat, E3_25_09_3B.dat, TRK114)
# ok - encode IDs
# ok - line 951: vertex desc not found in library gives an error
# ok - calculate wheel id
# ok - PropInstanceData - fix unks
# ok - write other TRK files (staticsoundmap)
# ok - verify duplicaded/repeated IDs
# ok - Add infos about exporter on IDsTable
# ok - ObjectIndex to object_index
# ok - vefiry renderable_index
# ok - verify small textures
# ok - calculate object center and radius   		https://b3d.interplanety.org/en/how-to-calculate-the-bounding-sphere-for-selected-objects/
# xx - Delete everything if returned canceled
# ok - try/except or if/else when reading the custom properties: is_shared_asset as False by default
# xx - upload a new library (one new materialstate added and three new vertex desc 4C_66_C2_A5, 95_E0_CC_BA, B2_3D_FC_26) - eles que arrumem

# Any object with .001 are treated as a duplicated and the original object is used

# ok - IDs get from object names
# ok - export folder name


bl_info = {
	"name": "Export to Burnout Paradise Remastered models format (.dat)",
	"description": "Save objects as Burnout Paradise Remastered files",
	"author": "DGIorio",
	"version": (2, 4),
	"blender": (3, 1, 0),
	"location": "File > Export > Burnout Paradise Remastered (.dat)",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"support": "COMMUNITY",
	"category": "Import-Export"}


import bpy
from bpy.types import Operator
from bpy.props import (
	StringProperty,
	BoolProperty
)
from bpy_extras.io_utils import (
	ExportHelper,
	axis_conversion
)
import bmesh
import binascii
import math
from mathutils import Matrix, Quaternion, Vector
import os
import time
import struct
import numpy as np
import shutil
import zlib
from bundle_packer_unpacker import pack_bundle


def main(context, export_path, pack_bundle_file,
		debug_shared_not_found, debug_search_for_swapped_ids, debug_use_shader_material_parameters,
		debug_use_default_vertexdescriptor, debug_use_default_materialstate, debug_add_missing_textures):
	
	#debug_shared_not_found = True
	#debug_search_for_swapped_ids = False
	#debug_use_shader_material_parameters = False
	#debug_use_default_vertexdescriptor = True
	#debug_use_default_materialstate = True
	#debug_add_missing_textures = True
	
	os.system('cls')
	start_time = time.time()
	
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')
	
	
	## INITIALIZING
	print("Initializing variables...")
	
	shared_dir = os.path.join(BurnoutLibraryGet(), "BPR_Library_PC")
	shared_model_dir = os.path.join(shared_dir, "Model")
	shared_renderable_dir = os.path.join(shared_dir, "Renderable")
	shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDesc")
	shared_vertex_descriptor_ported_x360_dir = os.path.join(shared_dir, "VertexDesc_port_X360")
	shared_vertex_descriptor_ported_ps3_dir = os.path.join(shared_dir, "VertexDesc_port_PS3")
	shared_material_dir = os.path.join(shared_dir, "Material")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	shared_materialstate_dir = os.path.join(shared_dir, "MaterialState")
	shared_materialstate_ported_x360_dir = os.path.join(shared_dir, "MaterialState_port_X360")
	shared_materialstate_ported_ps3_dir = os.path.join(shared_dir, "MaterialState_port_PS3")
	shared_texturestate_dir = os.path.join(shared_dir, "TextureState")
	shared_raster_dir = os.path.join(shared_dir, "Raster")
	shared_deformationspec_dir = os.path.join(shared_dir, "StreamedDeformationSpec")
	shared_attribsysvault_dir = os.path.join(shared_dir, "AttribSysVault")
	
	m = axis_conversion(from_forward='-Y', from_up='Z', to_forward='-Z', to_up='X').to_4x4()
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		main_directory_path = os.path.join(export_path, main_collection.name)
		
		directory_path = main_directory_path
			
		instancelist_dir = os.path.join(directory_path, "InstanceList")
		propinstancedata_dir = os.path.join(directory_path, "PropInstanceData")
		propgraphicslist_dir = os.path.join(directory_path, "PropGraphicsList")
		staticsoundmap_dir = os.path.join(directory_path, "StaticSoundMap")
		polygonsouplist_dir = os.path.join(directory_path, "PolygonSoupList")
		idlist_dir = os.path.join(directory_path, "IdList")
		
		graphicsstub_dir = os.path.join(directory_path, "GraphicsStub")
		graphicsspec_dir = os.path.join(directory_path, "GraphicsSpec")
		wheelgraphicsspec_dir = os.path.join(directory_path, "WheelGraphicsSpec")
		model_dir = os.path.join(directory_path, "Model")
		renderable_dir = os.path.join(directory_path, "Renderable")
		vertex_descriptor_dir = os.path.join(directory_path, "VertexDesc")
		material_dir = os.path.join(directory_path, "Material")
		materialstate_dir = os.path.join(directory_path, "MaterialState")
		texturestate_dir = os.path.join(directory_path, "TextureState")
		raster_dir = os.path.join(directory_path, "Raster")
		
		deformationspec_dir = os.path.join(directory_path, "StreamedDeformationSpec")
		attribsysvault_dir = os.path.join(directory_path, "AttribSysVault")
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
			
		# GraphicsSpec | InstanceList
		if "resource_type" in main_collection:
			resource_type = main_collection["resource_type"]
		else:
			print("ERROR: collection %s is missing parameter %s. Define one of the followings: 'InstanceList', 'GraphicsStub', 'GraphicsSpec', 'WheelGraphicsSpec', 'StreamedDeformationSpec', 'PolygonSoupList'." % (main_collection.name, '"resource_type"'))
			return {"CANCELLED"}
		
		try:
			collections_types = {collection["resource_type"] : collection for collection in main_collection.children}
		except:
			print("ERROR: some collection is missing parameter %s. Define one of the followings: 'InstanceList', 'PropInstanceData', 'StaticSoundMap_emitter', 'StaticSoundMap_passby', 'GraphicsSpec', 'WheelGraphicsSpec', 'StreamedDeformationSpec', 'PolygonSoupList'." % '"resource_type"')
			return {"CANCELLED"}
		
		if resource_type == "InstanceList":
			try:
				track_unit_number = int(main_collection.name.replace("TRK_UNIT", ""))
			except:
				print("ERROR: collection %s name is not in the proper formating. Define it as TRK_UNITXXX where XXX is a number" % main_collection.name)
				return {"CANCELLED"}
			mInstanceListId = calculate_resourceid("trk_unit" + str(track_unit_number) + "_list")
			instancelist_collection = collections_types["InstanceList"]
			collections = [instancelist_collection,]
			try:
				prop_collection = collections_types["PropInstanceData"]
				collections.append(prop_collection)
			except:
				print("WARNING: collection %s is missing. A empty one will be created." % '"PropInstanceData"')
			try:
				staticsoundmap_emitter_collection = collections_types["StaticSoundMap_emitter"]
				collections.append(staticsoundmap_emitter_collection)
			except:
				print("WARNING: collection %s is missing. A empty one will be created." % '"StaticSoundMap_emitter"')
			try:
				staticsoundmap_passby_collection = collections_types["StaticSoundMap_passby"]
				collections.append(staticsoundmap_passby_collection)
			except:
				print("WARNING: collection %s is missing. A empty one will be created." % '"StaticSoundMap_passby"')
			#collections = (instancelist_collection, prop_collection, staticsoundmap_emitter_collection, staticsoundmap_passby_collection)
		
		elif resource_type == "GraphicsSpec":
			vehicle_name = main_collection.name.replace("VEH", "").replace("GR", "").replace("AT", "").replace("CD", "").replace("_", "")
			mGraphicsSpecId = calculate_resourceid(vehicle_name.lower() + "_graphics")
			graphicsspec_collection = collections_types["GraphicsSpec"]
			collections = (graphicsspec_collection,)
		
		elif resource_type == "WheelGraphicsSpec":
			wheel_name = main_collection.name.replace("WHE", "").replace("GR", "").replace("_", "")
			mWheelGraphicsSpecId = calculate_resourceid(wheel_name.lower() + "_graphics")
			wheelgraphicsspec_collection = collections_types["WheelGraphicsSpec"]
			collections = (wheelgraphicsspec_collection,)
		
		elif resource_type == "GraphicsStub":
			vehicle_name = main_collection.name.replace("VEH", "").replace("GR", "").replace("AT", "").replace("CD", "").replace("_", "")
			mGraphicsStubId = calculate_resourceid(vehicle_name.lower() + "_trafficstub")
			mGraphicsSpecId = calculate_resourceid(vehicle_name.lower() + "_graphics")
			graphicsspec_collection = collections_types["GraphicsSpec"]
			wheelgraphicsspec_collection = collections_types["WheelGraphicsSpec"]
			wheel_name = wheelgraphicsspec_collection.name.replace("WHE", "").replace("GR", "").replace("_", "").replace("Graphics", "").split(".")[0]
			mWheelGraphicsSpecId = calculate_resourceid(wheel_name.lower() + "_graphics")
			
			try:
				mpVehicleGraphics_index = main_collection["VehicleGraphics_index"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as one." % (main_collection.name, '"VehicleGraphics_index"'))
				mpVehicleGraphics_index = 1
			
			try:
				mpWheelGraphics_index = main_collection["WheelGraphics_index"]
			except:
				mpWheelGraphics_index = 2
				if mpVehicleGraphics_index == 2:
					mpWheelGraphics_index = 1
				print("WARNING: collection %s is missing parameter %s. Assuming as %d." % (main_collection.name, '"WheelGraphics_index"', mpWheelGraphics_index))
			
			collections = (graphicsspec_collection, wheelgraphicsspec_collection)
		
		elif resource_type == "StreamedDeformationSpec":
			vehicle_name = main_collection.name.replace("VEH", "").replace("GR", "").replace("AT", "").replace("CD", "").replace("_", "")
			mStreamedDeformationSpecId = calculate_resourceid(vehicle_name.lower() + "deformationmodel")
			deformationspec_collection = collections_types["StreamedDeformationSpec"]
			
			try:
				mPosition_deformationspec = deformationspec_collection["position"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as None." % (deformationspec_collection.name, '"position"'))
				mPosition_deformationspec = None
			
			try:
				mQuaternion_deformationspec = Quaternion(deformationspec_collection["quaternion"])
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as None." % (deformationspec_collection.name, '"quaternion"'))
				mQuaternion_deformationspec = None
			
			try:
				mScale_deformationspec = deformationspec_collection["scale"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as None." % (deformationspec_collection.name, '"scale"'))
				mScale_deformationspec = None
			
			mCarModelSpaceToHandlingBodySpaceTransform = Matrix.LocRotScale(mPosition_deformationspec, mQuaternion_deformationspec, mScale_deformationspec)
			
			try:
				HandlingBodyDimensions = deformationspec_collection["HandlingBodyDimensions"]
			except:
				print("ERROR: collection %s is missing parameter %s." % (deformationspec_collection.name, '"HandlingBodyDimensions"'))
				return {"CANCELLED"}
			
			try:
				SpecID = deformationspec_collection["SpecID"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as zero." % (deformationspec_collection.name, '"SpecID"'))
				SpecID = 0
			
			try:
				NumVehicleBodies = deformationspec_collection["NumVehicleBodies"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as one." % (deformationspec_collection.name, '"NumVehicleBodies"'))
				NumVehicleBodies = 1
			
			try:
				NumGraphicsParts = deformationspec_collection["NumGraphicsParts"]
			except:
				print("ERROR: collection %s is missing parameter %s." % (deformationspec_collection.name, '"NumGraphicsParts"'))
				return {"CANCELLED"}
			
			try:
				CurrentCOMOffset = deformationspec_collection["CurrentCOMOffset"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as (0, 0, 0, 0)." % (deformationspec_collection.name, '"CurrentCOMOffset"'))
				CurrentCOMOffset = (0, 0, 0, 0)
			
			try:
				MeshOffset = deformationspec_collection["MeshOffset"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as -position." % (deformationspec_collection.name, '"MeshOffset"'))
				MeshOffset = list(-mCarModelSpaceToHandlingBodySpaceTransform.translation)
				MeshOffset.append(0)
			
			try:
				RigidBodyOffset = deformationspec_collection["RigidBodyOffset"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as -position." % (deformationspec_collection.name, '"RigidBodyOffset"'))
				RigidBodyOffset = list(-mCarModelSpaceToHandlingBodySpaceTransform.translation)
				RigidBodyOffset.append(0)
			
			try:
				CollisionOffset = deformationspec_collection["CollisionOffset"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as -position." % (deformationspec_collection.name, '"CollisionOffset"'))
				CollisionOffset = list(-mCarModelSpaceToHandlingBodySpaceTransform.translation)
				CollisionOffset.append(0)
			
			try:
				InertiaTensor = deformationspec_collection["InertiaTensor"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming as (0, 0, 0, 0)." % (deformationspec_collection.name, '"InertiaTensor"'))
				InertiaTensor = (0, 0, 0, 0)
			
			mNums = [NumVehicleBodies, NumGraphicsParts]
			mOffsetsAndTensor = [CurrentCOMOffset, MeshOffset, RigidBodyOffset, CollisionOffset, InertiaTensor]
			
			collections = (deformationspec_collection,)
		
		elif resource_type == "PolygonSoupList":
			collections = [collection for collection in main_collection.children if collection["resource_type"] == "PolygonSoupList"]
		
		else:
			print("ERROR: resource type %s not supported." % resource_type)
			return {"CANCELLED"}
		
		instances = []
		instances_wheel = []
		instances_props = []
		unk1s_props = []
		models = []
		renderables = []
		vextex_descriptors = []
		materials = []
		shaders = {}
		material_states = []
		texture_states = []
		rasters = []
		
		world_collision = []
		
		StaticSoundEntities_emitter = []
		StaticSoundEntities_passby = []
		
		WheelSpecs = []
		wheel_TagPointSpecs = []
		SensorSpecs = []
		TagPointSpecs = []
		DrivenPoints = []
		GenericTags = []
		CameraTags = []
		LightTags = []
		IKParts = []
		GlassPanes = []
		miNumberOfJointSpecs = 0
		
		muNumInstances = 0
		muNumberOfPropInstanceData = 0
		muPartsCount = 0
		muShatteredGlassPartsCount = 0
		num_unk1s_props = 0
		
		for collection in collections:
			is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).children.get(collection.name).hide_viewport
			is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).children.get(collection.name).exclude
			
			if is_hidden or is_excluded:
				print("WARNING: skipping collection %s since it is hidden or excluded." % (collection.name))
				print("")
				continue
			
			resource_type_child = collection["resource_type"]
			
			objects = collection.objects
			if resource_type_child == "StreamedDeformationSpec":
				objects = []
				for children in collection.children:
					objects += children.objects[:]
			
			PolygonSoups = []
			object_index = -1
			
			for object in objects:
				if object.type != "EMPTY":
					if resource_type_child == "StreamedDeformationSpec" and object.type == "CAMERA":
						pass
					else:
						continue
				
				is_hidden = object.hide_get()
				if is_hidden == True:
					continue
				
				# Model
				#mModelId = object["ModelId"]
				mModelId = object.name
				mModelId = mModelId.split(".")[0]
				
				if resource_type_child in ("InstanceList", "PropInstanceData", "GraphicsSpec", "WheelGraphicsSpec"):
					if is_valid_id(mModelId) == False:
						return {"CANCELLED"}
					
					try:
						is_model_shared_asset = object["is_shared_asset"]
					except:
						is_model_shared_asset = False
					
					if is_model_shared_asset == True:
						model_path = os.path.join(shared_model_dir, mModelId + ".dat")
						if not os.path.isfile(model_path):
							mModelId_swap = id_swap(mModelId)
							model_path = os.path.join(shared_model_dir, mModelId_swap + ".dat")
							if os.path.isfile(model_path) and debug_search_for_swapped_ids == True:
								mModelId = mModelId_swap
							else:
								print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("model", mModelId))
								if debug_shared_not_found == True:
									print("WARNING: setting %s %s is_shared_asset to False." % ("model", mModelId))
									is_model_shared_asset = False
				
				if resource_type_child == "InstanceList":
					try:
						object_index = object["object_index"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value." % (object.name, '"object_index"'))
						object_index = object_index + 1
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					
					try:
						mi16BackdropZoneID = object["BackdropZoneID"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"BackdropZoneID"'))
						mi16BackdropZoneID = -1
					
					try:
						mpModel = object["Model"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"Model"'))
						mpModel = 0
					
					try:
						mu16Pad = object["mu16Pad"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"mu16Pad"'))
						mu16Pad = 0
					
					try:
						mu32Pad = object["mu32Pad"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"mu32Pad"'))
						mu32Pad = 0
					
					try:
						mfMaxVisibleDistanceSquared = object["MaxVisibleDistanceSquared"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"MaxVisibleDistanceSquared"'))
						mfMaxVisibleDistanceSquared = 0
					
					try:
						is_always_loaded = object["is_always_loaded"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as True." % (object.name, '"is_always_loaded"'))
						is_always_loaded = True
					
					if is_always_loaded == True:
						muNumInstances += 1
					
					instances.append([object_index, [mModelId, [mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared, mTransform, is_always_loaded]]])
				
				elif resource_type_child == "PropInstanceData":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					
					try:
						muTypeId = object["TypeId"]
					except:
						print("ERROR: object %s is missing parameter %s." % (child.name, '"TypeId"'))
						return {"CANCELLED"}
					
					try:
						muInstanceID = object["InstanceID"]
					except:
						print("ERROR: object %s is missing parameter %s." % (child.name, '"InstanceID"'))
						return {"CANCELLED"}
					
					try:
						prop_type = object["prop_type"]
					except:
						print("ERROR: object %s is missing parameter %s." % (child.name, '"prop_type"'))
						return {"CANCELLED"}
					
					try:
						muFlags = object["Flags"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (child.name, '"Flags"'))
						muFlags = 0
					
					try:
						muAlternativeType = object["AlternativeType"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as 0xFFFF." % (child.name, '"AlternativeType"'))
						muAlternativeType = 0xFFFF
					
					try:
						mn8RotSpeed = object["RotSpeed"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as -64." % (child.name, '"RotSpeed"'))
						mn8RotSpeed = -64 #It was 0xC0, but it is a signed byte
					
					try:
						mn8MAngle = object["MAngle"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as default values [0, 0]." % (child.name, '"MAngle"'))
						mn8MAngle = [0, 0]
					
					if prop_type.lower() == "prop":
						try:
							muPartId = object["Parts"]
						except:
							print("ERROR: object %s is missing parameter %s." % (child.name, '"Parts"'))
							return {"CANCELLED"}
						muNumberOfPropInstanceData += 1
					elif prop_type.lower() == "prop_part":
						try:
							muPartId = object["PartId"]
						except:
							print("ERROR: object %s is missing parameter %s." % (child.name, '"PartId"'))
							return {"CANCELLED"}
					
					for child in object.children:
						if child.type != "MESH":
							continue
						try:
							renderable_index = child["renderable_index"]
						except:
							try:
								renderable_index = bpy.data.objects.get(child.name.split(".")[0])["renderable_index"]
							except:
								print("ERROR: object %s is missing parameter %s." % (child.name, '"renderable_index"'))
								return {"CANCELLED"}
						if renderable_index == 0:
							bbox_y = [point[1] for point in child.bound_box]
							mTransform[3][1] += min(bbox_y)
						
					instances_props.append([mModelId, [muTypeId, muFlags, muInstanceID, muAlternativeType, mn8RotSpeed, mn8MAngle, mTransform, prop_type, muPartId]])
				
				elif resource_type_child == "StaticSoundMap_emitter":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					try:
						unk_staticsoundmap = object["unk"]
					except:
						print("ERROR: static sound object %s is missing parameter %s." % (object.name, '"unk"'))
						return {"CANCELLED"}
					
					staticsound_object_int = int(object.name.replace("Sound", "").replace("Emitter", "").replace("Passby", "").replace("_", "").split(".")[0])
					StaticSoundEntities_emitter.append([staticsound_object_int, mTransform[3][:3], unk_staticsoundmap])
					continue
				
				elif resource_type_child == "StaticSoundMap_passby":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
					try:
						unk_staticsoundmap = object["unk"]
					except:
						print("ERROR: static sound object %s is missing parameter %s." % (object.name, '"unk"'))
						return {"CANCELLED"}
					
					staticsound_object_int = int(object.name.replace("Sound", "").replace("Emitter", "").replace("Passby", "").replace("_", "").split(".")[0])
					StaticSoundEntities_passby.append([staticsound_object_int, mTransform[3][:3], unk_staticsoundmap])
					continue
					
				elif resource_type_child == "GraphicsSpec":
					try:
						object_index = object["object_index"]
					except:
						print("ERROR: object %s is missing parameter %s." % (object.name, '"object_index"'))
						return {"CANCELLED"}
					
					try:
						is_shattered_glass = object["is_shattered_glass"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as False." % (object.name, '"is_shattered_glass"'))
						is_shattered_glass = False
					
					if is_shattered_glass == False:
						mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
						#mTransform = Matrix((object.matrix_world[1], object.matrix_world[2], object.matrix_world[0], object.matrix_world[3])).transposed()
						try:
							part_volume_id = object["part_volume_id"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as object_index." % (object.name, '"part_volume_id"'))
							part_volume_id = object_index
						instances.append([object_index, [mModelId, [mTransform, part_volume_id], is_shattered_glass]])
						muPartsCount += 1
					elif is_shattered_glass == True:
						try:
							mpModel = object["Model"]
							muBodyPartIndex = object["BodyPartIndex"]
							muBodyPartType = object["BodyPartType"]
						except:
							print("ERROR: shattered glass object %s is missing a parameter. Verify parameters %s, %s and %s." % (object.name, '"Model"', '"BodyPartIndex"', '"BodyPartType"'))
							return {"CANCELLED"}
						instances.append([object_index, [mModelId, [[mpModel, muBodyPartIndex, get_part_type_code(muBodyPartType)]], is_shattered_glass]])
						muShatteredGlassPartsCount += 1
				
				elif resource_type_child == "WheelGraphicsSpec":
					try:
						object_index = object["object_index"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"object_index"'))
						object_index = 0
					
					try:
						is_caliper = object["is_caliper"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as False." % (object.name, '"is_caliper"'))
						is_caliper = False
						#return {"CANCELLED"}
					
					instances_wheel.append([object_index, [mModelId, is_caliper]])
				
				elif resource_type_child == "StreamedDeformationSpec":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world)
					mTransform.translation += mCarModelSpaceToHandlingBodySpaceTransform.translation
					
					if "JointSpec" in object.name:
						continue
					
					object_index = object.name.replace("WheelSpec", "").replace("GenericTag", "").replace("CameraTag", "").replace("LightTag", "")
					object_index = object_index.replace("IKPart", "").replace("GlassPane", "")
					object_index = object_index.replace("SensorSpec", "").replace("TagPointSpec", "").replace("DrivenPoint", "").replace("_", "")
					object_index = int(object_index.split(".")[0])
					
					resource_type_collection = object.users_collection[0]["resource_type"]
					if resource_type_collection == "WheelSpecs":
						try:
							TagPointIndex = object["TagPointIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as the default value." % (object.name, '"TagPointIndex"'))
							TagPointIndex = -1
						
						try:
							WheelSide = object["WheelSide"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"WheelSide"'))
							return {"CANCELLED"}
						
						WheelSpecs.append([object_index, mTransform.translation, mTransform.to_scale(), TagPointIndex, WheelSide])
						
						try:
							mfWeightA = object["WeightA"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as 0.5" % (object.name, '"WeightA"'))
							mfWeightA = 0.5
						
						try:
							mfWeightB = object["WeightB"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming equal WeightA." % (object.name, '"WeightB"'))
							mfWeightB = mfWeightA
						
						try:
							mfDetachThresholdSquared = object["DetachThresholdSquared"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as 0.0625" % (object.name, '"DetachThresholdSquared"'))
							mfDetachThresholdSquared = 0.0625
						
						try:
							miDeformationSensorA = object["DeformationSensorA"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as one and nulling its weight" % (object.name, '"DeformationSensorA"'))
							miDeformationSensorA = 1
							mfWeightA = 0
						
						try:
							miDeformationSensorB = object["DeformationSensorB"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming equal the DeformationSensorA." % (object.name, '"DeformationSensorB"'))
							miDeformationSensorB = miDeformationSensorA
							if mfWeightA == 0:
								mfWeightB = 0
						
						try:
							miJointIndex = object["JointIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"JointIndex"'))
							miJointIndex = -1
						
						try:
							mbSkinnedPoint = object["SkinnedPoint"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"SkinnedPoint"'))
							mbSkinnedPoint = 0
						
						wheel_TagPointSpecs.append([TagPointIndex, mTransform.translation, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint])
					
					elif resource_type_collection == "SensorSpecs":
						mu8SceneIndex = object_index
						
						try:
							maDirectionParams = object["DirectionParams"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"DirectionParams"'))
							return {"CANCELLED"}
						
						try:
							mfRadius = object["Radius"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"Radius"'))
							return {"CANCELLED"}
						
						try:
							maNextSensor = object["NextSensor"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"NextSensor"'))
							return {"CANCELLED"}
						
						try:
							mu8AbsorbtionLevel = object["AbsorbtionLevel"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"AbsorbtionLevel"'))
							return {"CANCELLED"}
						
						try:
							mau8NextBoundarySensor = object["NextBoundarySensor"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"NextBoundarySensor"'))
							return {"CANCELLED"}
						
						SensorSpecs.append([mu8SceneIndex, mTransform.translation, maDirectionParams, mfRadius, maNextSensor, mu8AbsorbtionLevel, mau8NextBoundarySensor])
					
					elif resource_type_collection == "TagPointSpecs":
						try:
							mfWeightA = object["WeightA"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as one" % (object.name, '"WeightA"'))
							mfWeightA = 1
						
						try:
							mfWeightB = object["WeightB"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"WeightB"'))
							mfWeightB = 0
						
						try:
							mfDetachThresholdSquared = object["DetachThresholdSquared"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as 0.0625" % (object.name, '"DetachThresholdSquared"'))
							mfDetachThresholdSquared = 0.0625
						
						try:
							miDeformationSensorA = object["DeformationSensorA"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as one and nulling its weight" % (object.name, '"DeformationSensorA"'))
							miDeformationSensorA = 1
							mfWeightA = 0
						
						try:
							miDeformationSensorB = object["DeformationSensorB"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming equal the DeformationSensorA." % (object.name, '"DeformationSensorB"'))
							miDeformationSensorB = miDeformationSensorA
							if mfWeightA == 0:
								mfWeightB = 0
						
						try:
							miJointIndex = object["JointIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"JointIndex"'))
							miJointIndex = -1
						
						try:
							mbSkinnedPoint = object["SkinnedPoint"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as one." % (object.name, '"SkinnedPoint"'))
							mbSkinnedPoint = 1
						
						TagPointSpecs.append([object_index, mTransform.translation, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint])
					
					elif resource_type_collection == "DrivenPoints":
						try:
							miTagPointIndexA = object["TagPointIndexA"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointIndexA"'))
							return {"CANCELLED"}
						
						try:
							miTagPointIndexB = object["TagPointIndexB"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointIndexB"'))
							return {"CANCELLED"}
						
						DrivenPoints.append([object_index, mTransform.translation, miTagPointIndexA, miTagPointIndexB])
					
					elif resource_type_collection == "GenericTags":
						try:
							meTagPointType = object["TagPointType"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointType"'))
							return {"CANCELLED"}
						meTagPointType = get_tag_point_code(meTagPointType)
						try:
							int(meTagPointType)
						except ValueERROR:
							print("ERROR: Unrecognized TagPointType %s" % meTagPointType)
						
						try:
							miIkPartIndex = object["IkPartIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"IkPartIndex"'))
							miIkPartIndex = -1
						
						try:
							mu8SkinPoint = object["SkinPoint"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as default value zero." % (object.name, '"SkinPoint"'))
							mu8SkinPoint = 0
						
						mTransform = mTransform.transposed()
						GenericTags.append([object_index, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint])
					
					elif resource_type_collection == "CameraTags":
						try:
							meTagPointType = object["TagPointType"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointType"'))
							return {"CANCELLED"}
						meTagPointType = get_tag_point_code(meTagPointType)
						try:
							int(meTagPointType)
						except ValueERROR:
							print("ERROR: Unrecognized TagPointType %s" % meTagPointType)
						
						try:
							miIkPartIndex = object["IkPartIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"IkPartIndex"'))
							miIkPartIndex = -1
						
						try:
							mu8SkinPoint = object["SkinPoint"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as default value zero." % (object.name, '"SkinPoint"'))
							mu8SkinPoint = 0
						
						mTransform = mTransform.transposed()
						CameraTags.append([object_index, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint])
						
					elif resource_type_collection == "LightTags":
						try:
							meTagPointType = object["TagPointType"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointType"'))
							return {"CANCELLED"}
						meTagPointType = get_tag_point_code(meTagPointType)
						try:
							int(meTagPointType)
						except ValueERROR:
							print("ERROR: Unrecognized TagPointType %s" % meTagPointType)
						
						try:
							miIkPartIndex = object["IkPartIndex"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as -1." % (object.name, '"IkPartIndex"'))
							miIkPartIndex = -1
						
						try:
							mu8SkinPoint = object["SkinPoint"]
						except:
							print("WARNING: object %s is missing parameter %s. Assuming as default value zero." % (object.name, '"SkinPoint"'))
							mu8SkinPoint = 0
						
						mTransform = mTransform.transposed()
						LightTags.append([object_index, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint])
					
					elif resource_type_collection == "IKPart":
						try:
							mePartType = object["PartType"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"PartType"'))
							return {"CANCELLED"}
						
						mePartType = get_part_type_code(mePartType)
						try:
							int(mePartType)
						except ValueERROR:
							print("ERROR: Unrecognized PartType %s" % mePartType)
						
						try:
							miPartGraphics = object["PartGraphics"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"PartGraphics"'))
							return {"CANCELLED"}
						
						try:
							miStartIndexOfDrivenPoints = object["StartIndexOfDrivenPoints"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"StartIndexOfDrivenPoints"'))
							return {"CANCELLED"}
						
						try:
							miNumberOfDrivenPoints = object["NumberOfDrivenPoints"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"NumberOfDrivenPoints"'))
							return {"CANCELLED"}
						
						try:
							miStartIndexOfTagPoints = object["StartIndexOfTagPoints"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"StartIndexOfTagPoints"'))
							return {"CANCELLED"}
						
						try:
							miNumberOfTagPoints = object["NumberOfTagPoints"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"NumberOfTagPoints"'))
							return {"CANCELLED"}
						
						mGraphicsTransform = Matrix(np.linalg.inv(m) @ object.matrix_world).transposed()
						
						mBBoxSkinData = []
						mJointSpecs = []
						for child in object.children:
							if child.type == "MESH":
								try:
									mOrientation = [child["Orientation_0"], child["Orientation_1"], child["Orientation_2"], child["Orientation_3"]]
									mOrientation = Matrix(mOrientation)
									mOrientation = mOrientation.transposed()
								except:
									print("ERROR: object %s is missing a parameter. Verify the parameters %s, %s, %s and %s." % (child.name, '"Orientation_0"', '"Orientation_1"', '"Orientation_2"', '"Orientation_3"'))
									return {"CANCELLED"}
								
								status_bbox, maCornerSkinData, mCentreSkinData, mJointSkinData = read_bbox_object(child)
								if status_bbox == 1:
									return {"CANCELLED"}
								mBBoxSkinData = [mOrientation, maCornerSkinData, mCentreSkinData, mJointSkinData]
							
							elif child.type == "EMPTY":
								jointSpec_index = child.name.replace("IKPart", "").replace("JointSpec", "").replace("_", "").split(".")[0][:-1]
								jointSpec_index = int(jointSpec_index)
								
								mJointPosition = Matrix(np.linalg.inv(m) @ child.matrix_world).translation + mCarModelSpaceToHandlingBodySpaceTransform.translation
								
								try:
									mJointAxis = child["JointAxis"]
								except:
									print("WARNING: object %s is missing parameter %s. Assuming as (0, 1, 0, 0)." % (object.name, '"JointAxis"'))
									mJointAxis = [0, 1, 0, 0]
								
								try:
									mJointDefaultDirection = child["JointDefaultDirection"]
								except:
									print("WARNING: object %s is missing parameter %s. Assuming as (0, 1, 0, 0)." % (object.name, '"JointDefaultDirection"'))
									mJointDefaultDirection = [0, 1, 0, 0]
								
								try:
									mfMaxJointAngle = child["MaxJointAngle"]
								except:
									print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"MaxJointAngle"'))
									mfMaxJointAngle = 0.0
								
								try:
									mfJointDetachThreshold = child["JointDetachThreshold"]
								except:
									print("WARNING: object %s is missing parameter %s. Assuming as one." % (object.name, '"JointDetachThreshold"'))
									mfJointDetachThreshold = 1.0
								
								try:
									meJointType = child["JointType"]
								except:
									print("WARNING: object %s is missing parameter %s. Assuming as eNone." % (object.name, '"JointType"'))
									meJointType = 'eNone'
								
								meJointType = get_joint_type_code(meJointType)
								try:
									int(meJointType)
								except ValueERROR:
									print("ERROR: Unrecognized JointType %s" % meJointType)
								
								mJointSpec = [jointSpec_index, mJointPosition, mJointAxis, mJointDefaultDirection, mfMaxJointAngle, mfJointDetachThreshold, meJointType]
								mJointSpecs.append(mJointSpec)
								miNumberOfJointSpecs += 1
						
						if mBBoxSkinData == []:
							print("ERROR: IKPart object %s must have an BBoxSkin object (mesh type)." % object.name)
							return {"CANCELLED"}
						
						if len(mJointSpecs) != 0:
							mJointSpecs.sort(key=lambda x:x[0])
						
						IKParts.append([object_index, mGraphicsTransform, mBBoxSkinData, mJointSpecs, miPartGraphics, miStartIndexOfDrivenPoints, miNumberOfDrivenPoints, miStartIndexOfTagPoints, miNumberOfTagPoints, mePartType])
					
					elif resource_type_collection == "GlassPanes":
						try:
							mePartType = object["PartType"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"PartType"'))
							return {"CANCELLED"}
						
						mePartType = get_part_type_code(mePartType)
						try:
							int(mePartType)
						except ValueERROR:
							print("ERROR: Unrecognized PartType %s" % mePartType)
						
						try:
							glasspane_0x00 = object["glasspane_0x00"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"glasspane_0x00"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x10 = [object["glasspane_0x10"], object["glasspane_0x20"], object["glasspane_0x30"], object["glasspane_0x40"]]
						except:
							print("ERROR: object %s is missing parameters %s, %s, %s and %s." % (object.name, '"glasspane_0x10"', '"glasspane_0x20"', '"glasspane_0x30"', '"glasspane_0x40"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x50 = object["TagPointIndices"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"TagPointIndices"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x58 = object["glasspane_0x58"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"glasspane_0x58"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x5C = object["glasspane_0x5C"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"glasspane_0x5C"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x5E = object["DeformationSensorA"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"DeformationSensorA"'))
							return {"CANCELLED"}
						
						try:
							glasspane_0x60 = object["DeformationSensorB"]
						except:
							print("ERROR: object %s is missing parameter %s." % (object.name, '"DeformationSensorB"'))
							return {"CANCELLED"}
						
						GlassPanes.append([object_index, glasspane_0x00, glasspane_0x10, glasspane_0x50, glasspane_0x58, glasspane_0x5C, glasspane_0x5E, glasspane_0x60, mePartType])
					
					continue
				
				elif resource_type_child == "PolygonSoupList":
					mTransform = Matrix(np.linalg.inv(m) @ object.matrix_world)
					
					object_index = object.name.replace("PolygonSoup", "").replace("_", "")
					object_index = int(object_index.split(".")[0])
					child = object.children[0]
					
					#bbox = [list(point[:]) for point in child.bound_box]
					#bboxX, bboxY, bboxZ = zip(*bbox)
					
					mValidMasks = -1
					#PolySoupBox = [[min(bboxX), min(bboxY), min(bboxZ)], [max(bboxX), max(bboxY), max(bboxZ)], mValidMasks]
					maiVertexOffsets = mTransform.translation
					mfComprGranularity = mTransform.to_scale()[0]
					
					status, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads = read_polygonsoup_object(child)
					if status == 1:
						return {"CANCELLED"}
					
					bboxX, bboxY, bboxZ = zip(*PolygonSoupVertices)
					PolySoupBox = [[min(bboxX)*mfComprGranularity + maiVertexOffsets[0], min(bboxY)*mfComprGranularity + maiVertexOffsets[1], min(bboxZ)*mfComprGranularity + maiVertexOffsets[2]],
								   [max(bboxX)*mfComprGranularity + maiVertexOffsets[0], max(bboxY)*mfComprGranularity + maiVertexOffsets[1], max(bboxZ)*mfComprGranularity + maiVertexOffsets[2]], mValidMasks]
					
					maiVertexOffsets /= mfComprGranularity
					maiVertexOffsets = [int(vertex_offset) for vertex_offset in maiVertexOffsets]
					
					PolygonSoup = [object_index, PolySoupBox, maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads]
					
					PolygonSoups.append(PolygonSoup)
					
					continue
				
				if mModelId in (rows[0] for rows in models):
					continue
				
				try:
					is_model_shared_asset = object["is_shared_asset"]
				except:
					print("WARNING: object %s is missing parameter %s. Assuming as False." % (object.name, '"is_shared_asset"'))
					is_model_shared_asset = False
				
				if is_model_shared_asset == True:
					model_path = os.path.join(shared_model_dir, mModelId + ".dat")
					if not os.path.isfile(model_path):
						#print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("model", mModelId))
						if debug_shared_not_found == True:
							#print("WARNING: setting %s %s is_shared_asset to False." % ("model", mModelId))
							is_model_shared_asset = False
				
				if is_model_shared_asset == True:
					models.append([mModelId, [[], []], is_model_shared_asset])
					continue
				
				renderables_info = []
				
				num_objects = 0
				for child in object.children:
					if child.type != "MESH":
						continue
					num_objects += 1
				
				for child in object.children:
					if child.type != "MESH":
						continue
					
					#mRenderableId = child["RenderableId"]		# Using the object name
					mRenderableId = child.name
					mRenderableId = mRenderableId.split(".")[0]
					if is_valid_id(mRenderableId) == False:
						return {"CANCELLED"}
					
					try:
						is_shared_asset = child["is_shared_asset"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as False." % (child.name, '"is_shared_asset"'))
						is_shared_asset = False
					
					if is_shared_asset == True:
						renderable_path = os.path.join(shared_renderable_dir, mRenderableId + ".dat")
						if not os.path.isfile(renderable_path):
							mRenderableId_swap = id_swap(mRenderableId)
							renderable_path = os.path.join(shared_renderable_dir, mRenderableId_swap + ".dat")
							if os.path.isfile(renderable_path) and debug_search_for_swapped_ids == True:
								mRenderableId = mRenderableId_swap
							else:
								print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("renderable", mRenderableId))
								if debug_shared_not_found == True:
									print("WARNING: setting %s %s is_shared_asset to False." % ("renderable", mRenderableId))
									is_shared_asset = False
					
					try:
						renderable_index = child["renderable_index"]
					except:
						if num_objects == 1:
							renderable_index = 0
						else:
							print("ERROR: object %s is missing parameter %s." % (child.name, '"renderable_index"'))
							return {"CANCELLED"}
					
					try:
						lod_distance = child["lod_distance"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming default value." % (child.name, '"lod_distance"'))
						lod_distance = 200*(renderable_index + 1)
					renderables_info.append([mRenderableId, [renderable_index, lod_distance]])
					
					if mRenderableId in (rows[0] for rows in renderables):
						continue
					
					if is_shared_asset == True:
						renderables.append([mRenderableId, [[], [], [], []], is_shared_asset, ""])
						continue
					
					try:
						object_center = child["object_center"]
						object_radius = child["object_radius"]
					except:
						print("WARNING: object %s is missing parameter %s or %s. Calculating this values based on the object bounding box." % (child.name, '"object_center"', '"object_radius"'))
						bbox_x, bbox_y, bbox_z = [[point[i] for point in child.bound_box] for i in range(3)]
						object_center = [(max(bbox_x) + min(bbox_x))*0.5, (max(bbox_y) + min(bbox_y))*0.5, (max(bbox_z) + min(bbox_z))*0.5]
						object_radius = math.dist(object_center, child.bound_box[0])
					
					try:
						flags = child["flags"]
					except:
						print("WARNING: object %s is missing parameter %s. Assuming as default value 65280." % (child.name, '"flags"'))
						flags = 65280
					
					meshes_info, indices_buffer, vertices_buffer, status = read_object(child, resource_type_child, shared_dir, debug_use_default_vertexdescriptor, debug_search_for_swapped_ids)
					
					if status == 1:
						return {'CANCELLED'}
					
					num_meshes = len(meshes_info)
					renderable_properties = [object_center, object_radius, num_meshes, flags]
					
					renderables.append([mRenderableId, [meshes_info, renderable_properties, indices_buffer, vertices_buffer], is_shared_asset, ""])
					
					for mesh_info in meshes_info:
						mVertexDescriptorsId = mesh_info[3]
						for mVertexDescriptorId in mVertexDescriptorsId:
							if is_valid_id(mVertexDescriptorId) == False:
								return {"CANCELLED"}
							
							if mVertexDescriptorId not in vextex_descriptors:
								vextex_descriptors.append(mVertexDescriptorId)
						
						mMaterialId = mesh_info[2]
						if is_valid_id(mMaterialId) == False:
							return {"CANCELLED"}
						
						if mMaterialId in (rows[0] for rows in materials):
							continue
						
						mat = bpy.data.materials.get(mMaterialId) or bpy.data.materials.get(id_swap(mMaterialId))
						
						try:
							is_material_shared_asset = mat["is_shared_asset"]
						except:
							print("WARNING: material %s is missing parameter %s. Assuming as False." % (mat.name, '"is_shared_asset"'))
							is_material_shared_asset = False
						
						if is_material_shared_asset == True:
							material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
							if not os.path.isfile(material_path):
								mMaterialId_swap = id_swap(mMaterialId)
								material_path = os.path.join(shared_material_dir, mMaterialId_swap + ".dat")
								if os.path.isfile(material_path) and debug_search_for_swapped_ids == True:
									mMaterialId = mMaterialId_swap
								else:
									print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("material", mMaterialId))
									if debug_shared_not_found == True:
										print("WARNING: setting %s %s is_shared_asset to False." % ("material", mMaterialId))
										is_material_shared_asset = False
						
						if is_material_shared_asset == True:
							materials.append([mMaterialId, ["", [], [], [], []], is_material_shared_asset])
							continue
						
						mauVertexShaderNamesHash = []
						mafVertexShaderConstantsInstanceData = []
						mauPixelShaderNamesHash = []
						mafPixelShaderConstantsInstanceData = []
						anim_strings_3 = []
						parameters_3 = []
						
						#mMaterialId_ = mat["MaterialId"]
						try:
							shader_type = mat["shader_type"]
						except:
							print("ERROR: material %s is missing parameter %s." % (mat.name, '"shader_type"'))
							return {"CANCELLED"}
						
						mShaderId, shader_type = get_mShaderID(shader_type, resource_type)
						if mShaderId == "":
							if "_Damaged" in shader_type:
								mShaderId, shader_type = get_mShaderID(shader_type[:-8])
							elif "_Blurred" in shader_type:
								mShaderId, shader_type = get_mShaderID(shader_type[:-8])
							if mShaderId == "":
								print("ERROR: material %s is set to a nonexistent %s: %s." % (mat.name, '"shader_type"', shader_type))
								return {"CANCELLED"}
						
						# Reading shader for getting required raster types a number of unknowns 1 and 2
						if mShaderId in shaders:
							required_raster_types, num_material_states_shader, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash = shaders[mShaderId]
						else:
							shader_path = os.path.join(shared_shader_dir, mShaderId + ".dat")
							_, required_raster_types, num_material_states_shader, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash = read_shader(shader_path)
							shaders[mShaderId] = (required_raster_types, num_material_states_shader, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash)
						required_raster_types = dict((v,k) for k,v in required_raster_types.items())
						
						try:
							if debug_use_default_materialstate == True:
								raise Exception
							material_states_info = mat["MaterialStateIds"]
						except:
							if debug_use_default_materialstate == False:
								print("WARNING: material %s is missing parameter %s. Using default ones." % (mat.name, '"MaterialStateIds"'))
							#material_states_info = ["9B_9F_65_D4"]*num_material_states_shader
							if "doublesided" in shader_type.lower():
								material_states_info = ["F0_46_DA_CD"]*num_material_states_shader
								if shader_type == "Cruciform_1Bit_Doublesided" or shader_type == "Cruciform_1Bit_Doublesided_Instanced":
									material_states_info = ["FE_64_A3_0B", "62_15_71_78"]
								elif shader_type == "Glass_Specular_Transparent_Doublesided":
									material_states_info = ["B9_BE_2F_14", "9B_9F_65_D4"]
								elif shader_type == "MetalSheen_Opaque_Doublesided":
									material_states_info = ["F0_46_DA_CD", "9B_9F_65_D4"]
								elif shader_type == "Tunnel_Lightmapped_1Bit_Doublesided2":
									material_states_info = ["FE_64_A3_0B", "9B_9F_65_D4"]
								elif shader_type == "Foliage_1Bit_Doublesided":
									material_states_info = ["FE_64_A3_0B", "FE_64_A3_0B"]
								elif shader_type == "Diffuse_1Bit_Doublesided":
									material_states_info = ["FE_64_A3_0B", "FE_64_A3_0B"]
							elif shader_type == "Vehicle_Greyscale_Window_Textured":
								material_states_info = ["EC_4F_6F_B4", "EC_4F_6F_B4", "9B_9F_65_D4"]
							else:
								material_states_info = ["9B_9F_65_D4"]*num_material_states_shader
							
							#Cruciform_1Bit_Doublesided				double single FE_64_A3_0B 62_15_71_78
							#Cruciform_1Bit_Doublesided_Instanced 	double single FE_64_A3_0B 62_15_71_78
							#Glass_Specular_Transparent_Doublesided double single B9_BE_2F_14 9B_9F_65_D4
							#MetalSheen_Opaque_Doublesided			double single F0_46_DA_CD 9B_9F_65_D4
							#Tunnel_Lightmapped_1Bit_Doublesided2	double single FE_64_A3_0B 9B_9F_65_D4
							#Vehicle_Greyscale_Window_Textured 		double double single EC_4F_6F_B4 EC_4F_6F_B4 9B_9F_65_D4
							
						
						num_material_states = len(material_states_info)
						if num_material_states != num_material_states_shader:
							print("WARNING: number of material states (%d) on material %s is different from the %d required by the shader %s." % (num_material_states, mMaterialId, num_material_states_shader, mShaderId))
						
						if debug_use_shader_material_parameters == False:
							if muNumVertexShaderConstantsInstances > 0:
								try:
									mauVertexShaderNamesHash = mat["VertexShaderNamesHash"]
									if muNumVertexShaderConstantsInstances != len(mauVertexShaderNamesHash):
										print("WARNING: material %s has an incorrect amount of parameter %s. The correct amount is %d and it has %d." % (mat.name, '"VertexShaderNamesHash"', muNumVertexShaderConstantsInstances, len(mauVertexShaderNamesHash)))
										muNumVertexShaderConstantsInstances = len(mauVertexShaderNamesHash)
									
									mafVertexShaderConstantsInstanceData_material = []
									for i in range(0, muNumVertexShaderConstantsInstances):
										mafVertexShaderConstantsInstanceData_material.append(mat["VertexShaderConstantsInstanceData_entry_%d" % i])
									mafVertexShaderConstantsInstanceData = mafVertexShaderConstantsInstanceData_material[:]
								except:
									print("WARNING: material %s is missing a parameter or it has an incorrect amount of them. It must have the parameter %s with %d properties and %d %s. Using shader defined values." % (mat.name, '"VertexShaderNamesHash"', muNumVertexShaderConstantsInstances, muNumVertexShaderConstantsInstances, '"VertexShaderConstantsInstanceData_entry_i"'))
							
							if muNumPixelShaderConstantsInstances > 0:
								try:
									mauPixelShaderNamesHash = mat["PixelShaderNamesHash"]
									if muNumPixelShaderConstantsInstances != len(mauPixelShaderNamesHash):
										print("WARNING: material %s has an incorrect amount of parameter %s. The correct amount is %d and it has %d." % (mat.name, '"PixelShaderNamesHash"', muNumPixelShaderConstantsInstances, len(mauPixelShaderNamesHash)))
										muNumPixelShaderConstantsInstances = len(mauPixelShaderNamesHash)
									
									mafPixelShaderConstantsInstanceData_material = []
									for i in range(0, muNumPixelShaderConstantsInstances):
										mafPixelShaderConstantsInstanceData_material.append(mat["PixelShaderConstantsInstanceData_entry_%d" % i])
									mafPixelShaderConstantsInstanceData = mafPixelShaderConstantsInstanceData_material[:]
								except:
									print("WARNING: material %s is missing a parameter or it has an incorrect amount of them. It must have the parameter %s with %d properties and %d %s. Using shader defined values." % (mat.name, '"PixelShaderNamesHash"', muNumPixelShaderConstantsInstances, muNumPixelShaderConstantsInstances, '"PixelShaderConstantsInstanceData_entry_i"'))
						
						try:
							anim_strings_3 = mat["anim_strings_3"]
							num_parameters_3 = len(anim_strings_3)
							for i in range(0, num_parameters_3):
								parameters_3.append(mat["parameters_3_entry_%d" % i])
						except:
							anim_strings_3 = []
							num_parameters_3 = 0
							parameters_3 = []
						
						try:
							unk_0x6_relative = mat["property_0x2A"]
							if len(unk_0x6_relative) != num_material_states:
								raise Exception
						except:
							print("WARNING: material %s is missing a parameter or it has an incorrect amount of them. It must have the parameter %s with %d properties. Using default values. It might causes crashes" % (mat.name, '"property_0x2A"', num_material_states))
							unk_0x6_relative = []
							#property_0x6_relative = [0xAD60, 0x9A50, 0x8E76, 0xC70B]			# CRASH IF WRONG (SPECIALLY THE FIRST ONE)
							for i in range(0, num_material_states):
								unk_0x6_relative.append(material_constants[i])
						
						material_properties = [[mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash[:]], [mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash[:]], [parameters_3, anim_strings_3[:]], unk_0x6_relative]
						texture_states_info = []
						
						for i, mMaterialStateId in enumerate(material_states_info):
							if is_valid_id(mMaterialStateId) == False:
								return {"CANCELLED"}
							
							if mMaterialStateId not in material_states:
								material_states.append(mMaterialStateId)
							
							#material_state_path = os.path.join(shared_materialstate_dir, mMaterialStateId + ".dat")
							#edit_materialState(material_state_path, mMaterialStateId, i, shader_type)
						
						# Reading shader for getting required raster types
						# if mShaderId in shaders:
							# required_raster_types = shaders[mShaderId]
						# else:
							# shader_path = os.path.join(shared_shader_dir, mShaderId + ".dat")
							# _, required_raster_types, muNumVertexShaderConstantsInstances, muNumPixelShaderConstantsInstances = read_shader(shader_path)
							# shaders[mShaderId] = required_raster_types
						# required_raster_types = dict((v,k) for k,v in required_raster_types.items())
						
						#raster_types = []
						for node in mat.node_tree.nodes:
							if node.type == "TEX_IMAGE":
								#texture_states_info.append(mTextureStateId)
								raster_type = node.name.split(".")[0]
								mTextureStateId = node.label.split(".")[0]
								
								if mTextureStateId == "":
									print("ERROR: texture node %s is missing its ID in the %s field." % (node.name, '"label"'))
									return {"CANCELLED"}
								
								if is_valid_id(mTextureStateId) == False:
									return {"CANCELLED"}
								
								try:
									is_shared_asset = node.is_shared_asset
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as False." % (node.name, '"is_shared_asset"'))
									is_shared_asset = False
								
								if is_shared_asset == True:
									texture_state_path = os.path.join(shared_texturestate_dir, mTextureStateId + ".dat")
									if not os.path.isfile(texture_state_path):
										mTextureStateId_swap = id_swap(mTextureStateId)
										texture_state_path = os.path.join(shared_texturestate_dir, mTextureStateId_swap + ".dat")
										if os.path.isfile(texture_state_path) and debug_search_for_swapped_ids == True:
											mTextureStateId = mTextureStateId_swap
										else:
											print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("textureState", mTextureStateId))
											if debug_shared_not_found == True:
												print("WARNING: setting %s %s is_shared_asset to False." % ("textureState", mTextureStateId))
												is_shared_asset = False
								
								#raster_types.append(raster_type)
								
								try:
									texture_sampler_code = required_raster_types[raster_type]
								except:
									texture_sampler_code = 0xFF
								
								texture_states_info.append([mTextureStateId, texture_sampler_code])
								
								if mTextureStateId in (rows[0] for rows in texture_states):
									continue
								
								if is_shared_asset == True:
									texture_states.append([mTextureStateId, ["", [], raster_type], is_shared_asset])
									continue
								
								try:
									addressing_mode = node.addressing_mode
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as (1, 1, 1)." % (node.name, '"addressing_mode"'))
									addressing_mode = (1, 1, 1)
								
								try:
									filter_types = node.filter_types
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as (1, 1, 1)." % (node.name, '"filter_types"'))
									filter_types = (1, 1, 1)
								
								try:
									min_max_lod = node.min_max_lod
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming default value." % (node.name, '"min_max_lod"'))
									min_max_lod = struct.unpack("<ff", b'\xFF\xFF\x7F\xFF\xFF\xFF\x7F\x7F')
								
								try:
									max_anisotropy = node.max_anisotropy
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as 1." % (node.name, '"max_anisotropy"'))
									max_anisotropy = 1
								
								try:
									mipmap_lod_bias = node.mipmap_lod_bias
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as -0.9." % (node.name, '"mipmap_lod_bias"'))
									mipmap_lod_bias = -0.9
								
								try:
									comparison_function = node.comparison_function
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as -1." % (node.name, '"comparison_function"'))
									comparison_function = -1
								
								try:
									is_border_color_white = node.is_border_color_white
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as False." % (node.name, '"is_border_color_white"'))
									is_border_color_white = 0
								
								try:
									unk1 = node.unk1
								except:
									print("WARNING: texture node %s is missing parameter %s. Assuming as 1." % (node.name, '"unk1"'))
									unk1 = 1
								
								texture_state_properties = [addressing_mode, filter_types, min_max_lod, max_anisotropy, mipmap_lod_bias,
															comparison_function, is_border_color_white, unk1]
								
								raster = node.image
								if raster == None:
									print("WARNING: No image on texture node %s of the material %s. Ignoring it." % (mTextureStateId, mMaterialId))
									del texture_states_info[-1]
									continue
								
								width, height = raster.size
								if width <= 4 or height <= 4:
									print("ERROR: image %s resolution smaller than the supported by the game. It must be bigger than 4x4." % raster.name)
									return {"CANCELLED"}
								
								mRasterId = raster.name.split(".")[0]
								if is_valid_id(mRasterId) == False:
									return {"CANCELLED"}
								
								try:
									is_raster_shared_asset = raster.is_shared_asset
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as False." % (raster.name, '"is_shared_asset"'))
									is_raster_shared_asset = False
								
								if is_raster_shared_asset == True:
									raster_path = os.path.join(shared_raster_dir, mRasterId + ".dat")
									raster_dds_path = os.path.join(shared_raster_dir, mRasterId + ".dds")
									if os.path.isfile(raster_path) or os.path.isfile(raster_dds_path):
										mRasterId = mRasterId
									else:
										mRasterId_swap = id_swap(mRasterId)
										raster_path = os.path.join(shared_raster_dir, mRasterId_swap + ".dat")
										raster_dds_path = os.path.join(shared_raster_dir, mRasterId_swap + ".dds")
										if (os.path.isfile(raster_path) or os.path.isfile(raster_dds_path)) and debug_search_for_swapped_ids == True:
											mRasterId = mRasterId_swap
										else:
											print("WARNING: %s %s is set as a shared asset although it may not exist on BPR PC." % ("raster", mRasterId))
											if debug_shared_not_found == True:
												print("WARNING: setting %s %s is_shared_asset to False." % ("raster", mRasterId))
												is_raster_shared_asset = False
								
								texture_states.append([mTextureStateId, [mRasterId, texture_state_properties, raster_type], is_shared_asset])
								
								if mRasterId in (rows[0] for rows in rasters):
									continue
								
								if is_raster_shared_asset == True:
									rasters.append([mRasterId, [], is_raster_shared_asset, ""])
									continue
								
								try:
									dimension = raster.dimension
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as 1." % (raster.name, '"dimension"'))
									dimension = 1
								
								try:
									unk_0x34 = raster.unk_0x34
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as 0x5C0C0." % (raster.name, '"unk_0x34"'))
									unk_0x34 = 0x5C0C0
								
								try:
									unk_0x38 = raster.unk_0x38
								except:
									print("WARNING: image %s is missing parameter %s. Assuming as 0x7AFEE50." % (raster.name, '"unk_0x38"'))
									unk_0x38 = 0x7AFEE50
								
								raster_properties = [dimension, unk_0x34, unk_0x38]
								
								is_packed = False
								if len(raster.packed_files) > 0:
									is_packed = True
									raster.unpack(method='WRITE_LOCAL')	# Default method, it unpacks to the current .blend directory
								
								raster_path = bpy.path.abspath(raster.filepath)
								
								raster_source_extension = os.path.splitext(os.path.basename(raster_path))[-1]
								if raster_source_extension != ".dds":
									print("ERROR: texture format %s not supported. Please use .dds format." % raster_source_extension)
									return {"CANCELLED"}
								
								rasters.append([mRasterId, [raster_properties], is_raster_shared_asset, raster_path])
								
								if is_packed == True:
									raster.pack()
						
						
						if debug_add_missing_textures == True and mShaderId == "7B_7B_A2_8E":
							raster_type = "NormalTextureSampler"
							mTextureStateId = "EC_82_F7_A4"
							texture_sampler_code = required_raster_types[raster_type]
							if not texture_sampler_code in (rows[1] for rows in texture_states_info):
								texture_states_info.append([mTextureStateId, texture_sampler_code])
								if not mTextureStateId in (rows[0] for rows in texture_states):
									texture_state_properties = [[1, 1, 1], [1, 1, 1], struct.unpack("<ff", b'\xFF\xFF\x7F\xFF\xFF\xFF\x7F\x7F'), 1, 0, -1, False, 1]
									mRasterId = "88_79_A2_E0"
									texture_states.append([mTextureStateId, [mRasterId, texture_state_properties, raster_type], False])
									if mRasterId not in (rows[0] for rows in rasters):
										rasters.append([mRasterId, [], True, ""])
							
							raster_type = "NormalDetailTextureSampler"
							mTextureStateId = "A0_53_76_4C"
							texture_sampler_code = required_raster_types[raster_type]
							if not texture_sampler_code in (rows[1] for rows in texture_states_info):
								texture_states_info.append([mTextureStateId, texture_sampler_code])
								if not mTextureStateId in (rows[0] for rows in texture_states):
									texture_state_properties = [[1, 1, 1], [1, 1, 1], struct.unpack("<ff", b'\xFF\xFF\x7F\xFF\xFF\xFF\x7F\x7F'), 1, 0, -1, False, 1]
									mRasterId = "AE_7E_C6_7D"
									texture_states.append([mTextureStateId, [mRasterId, texture_state_properties, raster_type], False])
									if mRasterId not in (rows[0] for rows in rasters):
										rasters.append([mRasterId, [], True, ""])
						
						#for required_raster_type in required_raster_types:
						#	if required_raster_type not in raster_types:
						#		print("ERROR: required raster type %s for shader %s unavailable in material %s" % (required_raster_type, shader_type, mMaterialId))
						#		return {'CANCELLED'}
						
						#try:
						#	is_shared_asset = mat["is_shared_asset"]
						#except:
						#	is_shared_asset = False
						materials.append([mMaterialId, [mShaderId, material_states_info, texture_states_info, material_properties, required_raster_types], is_material_shared_asset])
				
				renderable_indices = [renderable_info[1][0] for renderable_info in renderables_info]
				indices_range = list(range(0, max(renderable_indices) + 1))
				if sorted(renderable_indices) != indices_range:
					print("ERROR: missing or duplicated renderable indices on object %s childs. Verify the %s parameters for skipped or duplicated entries." % (object.name, '"renderable_index"'))
					print("renderable_indices =", renderable_indices, indices_range)
					return {"CANCELLED"}
				
				mu8NumRenderables = len(renderables_info)
				try:
					miGameExplorerIndex = object["GameExplorerIndex"]
				except:
					print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"GameExplorerIndex"'))
					miGameExplorerIndex = 0
				try:
					mu8Flags = object["Flags"]
				except:
					print("WARNING: object %s is missing parameter %s. Assuming as zero." % (object.name, '"Flags"'))
					mu8Flags = 0
				try:
					mu8NumStates = object["NumStates"]
				except:
					print("WARNING: object %s is missing parameter %s. Assuming as NumRenderables." % (object.name, '"NumStates"'))
					mu8NumStates = mu8NumRenderables
				
				model_properties = [miGameExplorerIndex, mu8NumRenderables, mu8Flags, mu8NumStates]
				
				#try:
				#	is_shared_asset = object["is_shared_asset"]
				#except:
				#	is_shared_asset = False
				
				models.append([mModelId, [renderables_info, model_properties], is_model_shared_asset])
		
			if resource_type_child == "PolygonSoupList":
				try:
					track_unit_number = int(collection.name.replace("TRK_COL", "").replace("_", ""))
				except:
					print("ERROR: collection %s name is not in the proper formating. Define it as TRK_COL_XXX where XXX is a number" % collection.name)
					return {"CANCELLED"}
				mPolygonSoupList = "TRK_COL_" + str(track_unit_number)
				mPolygonSoupListId = calculate_resourceid(mPolygonSoupList.lower())
				mIdList = "TRK_CLIL" + str(track_unit_number)
				mIdListId = calculate_resourceid(mIdList.lower())
				PolygonSoups.sort(key=lambda x:x[0])
				world_collision.append([track_unit_number, mPolygonSoupListId, PolygonSoups, mIdListId])
		
		if resource_type == "InstanceList":
			try:
				num_unk1s_props = prop_collection["num_unk1s"]
				for i in range(0, num_unk1s_props):
					unk1s_props.append(prop_collection["unk1_%d" % i])
			except:
				print("WARNING: prop collection is missing a parameter or it has an incorrect amount of them. It must have the parameter %s and %s." % ('"num_unk1s"', '"unk1_i"'))
				num_unk1s_props = 0
			
			# StaticSoundMap emitter data
			try:
				mfSubRegionSize = staticsoundmap_emitter_collection["SubRegionSize"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"SubRegionSize"'))
				mfSubRegionSize = 50.0
			try:
				miNumSubRegionsX = staticsoundmap_emitter_collection["NumSubRegionsX"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"NumSubRegionsX"'))
				miNumSubRegionsX = 1
			try:
				miNumSubRegionsZ = staticsoundmap_emitter_collection["NumSubRegionsZ"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"NumSubRegionsZ"'))
				miNumSubRegionsZ = 1
			try:
				meRootType = staticsoundmap_emitter_collection["RootType"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"RootType"'))
				meRootType = 0
			try:
				mSubRegions_first = staticsoundmap_emitter_collection["SubRegions_first"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"SubRegions_first"'))
				mSubRegions_first = [-1]
			try:
				mSubRegions_count = staticsoundmap_emitter_collection["SubRegions_count"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_emitter"', '"SubRegions_count"'))
				mSubRegions_count = [0]
			
			staticsoundmap_info_emitter = [mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType]
			instances_emitter = [StaticSoundEntities_emitter, mSubRegions_first[:], mSubRegions_count[:]]
			emitter_data = [staticsoundmap_info_emitter, instances_emitter]
			
			# StaticSoundMap passby data
			try:
				mfSubRegionSize = staticsoundmap_passby_collection["SubRegionSize"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"SubRegionSize"'))
				mfSubRegionSize = 50.0
			try:
				miNumSubRegionsX = staticsoundmap_passby_collection["NumSubRegionsX"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"NumSubRegionsX"'))
				miNumSubRegionsX = 1
			try:
				miNumSubRegionsZ = staticsoundmap_passby_collection["NumSubRegionsZ"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"NumSubRegionsZ"'))
				miNumSubRegionsZ = 1
			try:
				meRootType = staticsoundmap_passby_collection["RootType"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"RootType"'))
				meRootType = 0
			try:
				mSubRegions_first = staticsoundmap_passby_collection["SubRegions_first"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"SubRegions_first"'))
				mSubRegions_first = [-1]
			try:
				mSubRegions_count = staticsoundmap_passby_collection["SubRegions_count"]
			except:
				print("WARNING: collection %s is missing parameter %s or the collection does not exist. Assuming default value." % ('"staticsoundmap_passby"', '"SubRegions_count"'))
				mSubRegions_count = [0]
			
			staticsoundmap_info_passby = [mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType]
			instances_passby = [StaticSoundEntities_passby, mSubRegions_first[:], mSubRegions_count[:]]
			passby_data = [staticsoundmap_info_passby, instances_passby]
		
		if len(instances) == 0 and len(instances_wheel) == 0 and resource_type != "InstanceList" and resource_type != "StreamedDeformationSpec" and resource_type != "PolygonSoupList":
			print("ERROR: no models in the proper structure. Nothing to export on this collection.")
			return {"CANCELLED"}
		
		if resource_type == "GraphicsSpec":
			object_indices = [instance[0] for instance in instances]
			indices_range = list(range(0, max(object_indices) + 1))
			if sorted(object_indices) != indices_range:
				print("ERROR: missing or duplicated object indices. Verify the %s parameters for skipped or duplicated entries." % '"ObjectIndex"')
				print("object_indices =", object_indices)
				return {"CANCELLED"}
		if resource_type == "StreamedDeformationSpec":
			TagPointSpecs.extend(wheel_TagPointSpecs)
			WheelSpecs.sort(key=lambda x:x[0])
			SensorSpecs.sort(key=lambda x:x[0])
			TagPointSpecs.sort(key=lambda x:x[0])
			DrivenPoints.sort(key=lambda x:x[0])
			GenericTags.sort(key=lambda x:x[0])
			CameraTags.sort(key=lambda x:x[0])
			LightTags.sort(key=lambda x:x[0])
			IKParts.sort(key=lambda x:x[0])
			GlassPanes.sort(key=lambda x:x[0])
		
		
		## Writing data
		print("\tWriting data...")
		writing_time = time.time()
		
		mResourceIds = []
		if resource_type == "InstanceList":
			instancelist_path = os.path.join(instancelist_dir, mInstanceListId + ".dat")
			write_instancelist(instancelist_path, instances, muNumInstances)
			mResourceIds.append([mInstanceListId, "InstanceList", id_to_int(mInstanceListId)])
			
			mPropGraphicsListId = calculate_resourceid("prp_gl__" + str(track_unit_number))
			propgraphicslist_path = os.path.join(propgraphicslist_dir, mPropGraphicsListId + ".dat")
			number_of_prop_parts = write_propgraphicslist(propgraphicslist_path, instances_props, track_unit_number)
			mResourceIds.append([mPropGraphicsListId, "PropGraphicsList", id_to_int(mPropGraphicsListId)])
			
			mPropInstanceDataId = calculate_resourceid("prp_inst_" + str(track_unit_number))
			propinstancedata_path = os.path.join(propinstancedata_dir, mPropInstanceDataId + ".dat")
			write_propinstancedata(propinstancedata_path, instances_props, track_unit_number, muNumberOfPropInstanceData, number_of_prop_parts, num_unk1s_props, unk1s_props)
			mResourceIds.append([mPropInstanceDataId, "PropInstanceData", id_to_int(mPropInstanceDataId)])
			
			mStaticSoundMapId_emitter = calculate_resourceid("trk_unit" + str(track_unit_number) + "_emitter")
			staticsoundmap_path_emitter = os.path.join(staticsoundmap_dir, mStaticSoundMapId_emitter + ".dat")
			write_staticsoundmap(staticsoundmap_path_emitter, emitter_data)
			mResourceIds.append([mStaticSoundMapId_emitter, "StaticSoundMap", id_to_int(mStaticSoundMapId_emitter)])
			
			mStaticSoundMapId_passby = calculate_resourceid("trk_unit" + str(track_unit_number) + "_passby")
			staticsoundmap_path_passby = os.path.join(staticsoundmap_dir, mStaticSoundMapId_passby + ".dat")
			write_staticsoundmap(staticsoundmap_path_passby, passby_data)
			mResourceIds.append([mStaticSoundMapId_passby, "StaticSoundMap", id_to_int(mStaticSoundMapId_passby)])
		elif resource_type == "GraphicsSpec":
			graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
			status = write_graphicsspec(graphicsspec_path, instances, muPartsCount, muShatteredGlassPartsCount)
			if status == 1:
				return {'CANCELLED'}
			mResourceIds.append([mGraphicsSpecId, "GraphicsSpec", id_to_int(mGraphicsSpecId)])
		elif resource_type == "WheelGraphicsSpec":
			wheelgraphicsspec_path = os.path.join(wheelgraphicsspec_dir, mWheelGraphicsSpecId + ".dat")
			write_wheelgraphicsspec(wheelgraphicsspec_path, instances_wheel)
			mResourceIds.append([mWheelGraphicsSpecId, "WheelGraphicsSpec", id_to_int(mWheelGraphicsSpecId)])
		elif resource_type == "GraphicsStub":
			graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
			status = write_graphicsspec(graphicsspec_path, instances, muPartsCount, muShatteredGlassPartsCount)
			if status == 1:
				return {'CANCELLED'}
			mResourceIds.append([mGraphicsSpecId, "GraphicsSpec", id_to_int(mGraphicsSpecId)])
			
			wheelgraphicsspec_path = os.path.join(wheelgraphicsspec_dir, mWheelGraphicsSpecId + ".dat")
			write_wheelgraphicsspec(wheelgraphicsspec_path, instances_wheel)
			mResourceIds.append([mWheelGraphicsSpecId, "WheelGraphicsSpec", id_to_int(mWheelGraphicsSpecId)])
			
			graphicsstub_path = os.path.join(graphicsstub_dir, mGraphicsStubId + ".dat")
			write_graphicsstub(graphicsstub_path, mGraphicsSpecId, mWheelGraphicsSpecId, mpVehicleGraphics_index, mpWheelGraphics_index)
			mResourceIds.append([mGraphicsStubId, "GraphicsStub", id_to_int(mGraphicsStubId)])
		elif resource_type == "StreamedDeformationSpec":
			deformationspec_path = os.path.join(deformationspec_dir, mStreamedDeformationSpecId + ".dat")
			#shared_deformationspec_path = os.path.join(shared_deformationspec_dir, mStreamedDeformationSpecId + ".dat")
			#if os.path.isfile(shared_deformationspec_path):
			#	os.makedirs(deformationspec_dir, exist_ok = True)
			#	shutil.copy2(shared_deformationspec_path, deformationspec_path)
			#	edit_deformationspec(deformationspec_path, WheelSpecs, SensorSpecs, TagPointSpecs, DrivenPoints, GenericTags, CameraTags, LightTags, IKParts, GlassPanes, mCarModelSpaceToHandlingBodySpaceTransform.transposed(), HandlingBodyDimensions, SpecID, mNums, mOffsetsAndTensor, miNumberOfJointSpecs)
			write_deformationspec(deformationspec_path, WheelSpecs, SensorSpecs, TagPointSpecs, DrivenPoints, GenericTags, CameraTags, LightTags, IKParts, GlassPanes, mCarModelSpaceToHandlingBodySpaceTransform.transposed(), HandlingBodyDimensions, SpecID, mNums, mOffsetsAndTensor, miNumberOfJointSpecs)
			mResourceIds.append([mStreamedDeformationSpecId, "StreamedDeformationSpec", id_to_int(mStreamedDeformationSpecId)])
			
			mAttribSysVaultId = calculate_resourceid(vehicle_name.lower() + "_attribsys")
			attribsysvault_path = os.path.join(attribsysvault_dir, mAttribSysVaultId + ".dat")
			shared_attribsysvault_path = os.path.join(shared_attribsysvault_dir, mAttribSysVaultId + ".dat")
			if os.path.isfile(shared_attribsysvault_path):
				os.makedirs(attribsysvault_dir, exist_ok = True)
				shutil.copy2(shared_attribsysvault_path, attribsysvault_path)
			mResourceIds.append([mAttribSysVaultId, "AttribSysVault", id_to_int(mAttribSysVaultId)])
		elif resource_type == "PolygonSoupList":
			for collision in world_collision:
				track_unit_number, mPolygonSoupListId, PolygonSoups, mIdListId = collision
				polygonsouplist_path = os.path.join(polygonsouplist_dir, mPolygonSoupListId + ".dat")
				write_polygonsouplist(polygonsouplist_path, PolygonSoups)
				mResourceIds.append([mPolygonSoupListId, "PolygonSoupList", id_to_int(mPolygonSoupListId)])
				
				idlist_path = os.path.join(idlist_dir, mIdListId + ".dat")
				write_idlist(idlist_path, mPolygonSoupListId)
				mResourceIds.append([mIdListId, "IdList", id_to_int(mIdListId)])
		
		
		for model in models:
			mModelId = model[0]
			is_shared_asset = model[2]
			if is_shared_asset == True:
				continue
			
			model_path = os.path.join(model_dir, mModelId + ".dat")
			write_model(model_path, model)
			mResourceIds.append([mModelId, "Model", id_to_int(mModelId)])
		
		
		for renderable in renderables:
			mRenderableId = renderable[0]
			is_shared_asset = renderable[2]
			if is_shared_asset == True:
				continue
			
			renderable_path = os.path.join(renderable_dir, mRenderableId + ".dat")
			write_renderable(renderable_path, renderable, resource_type)
			mResourceIds.append([mRenderableId, "Renderable", id_to_int(mRenderableId)])
		
		
		for material in materials:
			mMaterialId = material[0]
			is_shared_asset = material[2]
			if is_shared_asset == True:
				continue
			
			material_path = os.path.join(material_dir, mMaterialId + ".dat")
			write_material(material_path, material)
			mResourceIds.append([mMaterialId, "Material", id_to_int(mMaterialId)])
		
		
		for mVertexDescriptorId in vextex_descriptors:
			vertex_descriptor_path = os.path.join(shared_vertex_descriptor_dir, mVertexDescriptorId + ".dat")
			if not os.path.isfile(vertex_descriptor_path):
				vertex_descriptor_path = os.path.join(shared_vertex_descriptor_ported_x360_dir, mVertexDescriptorId + ".dat")
				if not os.path.isfile(vertex_descriptor_path):
					vertex_descriptor_path = os.path.join(shared_vertex_descriptor_ported_ps3_dir, mVertexDescriptorId + ".dat")
					if not os.path.isfile(vertex_descriptor_path):
						print("ERROR: required vertex descriptor %s not found in library folder %s, %s and %s" % (mVertexDescriptorId, shared_vertex_descriptor_dir, shared_vertex_descriptor_ported_x360_dir, shared_vertex_descriptor_ported_ps3_dir))
						return {'CANCELLED'}
			
			os.makedirs(vertex_descriptor_dir, exist_ok = True)
			shutil.copy2(vertex_descriptor_path, vertex_descriptor_dir)
			mResourceIds.append([mVertexDescriptorId, "VertexDesc", id_to_int(mVertexDescriptorId)])
		
		
		for mMaterialStateId in material_states:
			material_state_path = os.path.join(shared_materialstate_dir, mMaterialStateId + ".dat")
			if not os.path.isfile(material_state_path):
				material_state_path = os.path.join(shared_materialstate_ported_x360_dir, mMaterialStateId + ".dat")
				if not os.path.isfile(material_state_path):
					material_state_path = os.path.join(shared_materialstate_ported_ps3_dir, mMaterialStateId + ".dat")
					if not os.path.isfile(material_state_path):
						print("ERROR: required material state %s not found in library folder %s, %s and %s" % (mMaterialStateId, shared_materialstate_dir, shared_materialstate_ported_x360_dir, shared_materialstate_ported_ps3_dir))
						return {'CANCELLED'}
			
			os.makedirs(materialstate_dir, exist_ok = True)
			shutil.copy2(material_state_path, materialstate_dir)
			mResourceIds.append([mMaterialStateId, "MaterialState", id_to_int(mMaterialStateId)])
		
		
		for texture_state in texture_states:
			mTextureStateId = texture_state[0]
			is_shared_asset = texture_state[2]
			if is_shared_asset == True:
				continue
			
			texture_state_path = os.path.join(texturestate_dir, mTextureStateId + ".dat")
			write_texturestate(texture_state_path, texture_state)
			mResourceIds.append([mTextureStateId, "TextureState", id_to_int(mTextureStateId)])
		
		
		for raster in rasters:
			mRasterId = raster[0]
			is_shared_asset = raster[2]
			if is_shared_asset == True:
				continue
			
			raster_path = os.path.join(raster_dir, mRasterId + ".dat")
			write_raster(raster_path, raster)
			mResourceIds.append([mRasterId, "Raster", id_to_int(mRasterId)])
		
		mResourceIds_ = [mResourceId[0] for mResourceId in mResourceIds]
		if len(mResourceIds_) != len(set(mResourceIds_)):
			print("ERROR: duplicated resource IDs. Verify the list below for the duplicated IDs and do the proper fixes.")
			print(mResourceIds)
			return {'CANCELLED'}
		
		resources_table_path  = os.path.join(directory_path, "IDs.BIN")
		write_resources_table(resources_table_path, mResourceIds)
		
		if pack_bundle_file == True:
			status = pack_bundle(resources_table_path, directory_path, "OUTPUT.BIN")
		
		elapsed_time = time.time() - writing_time
		print("\t... %.4fs" % elapsed_time)
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def read_object(object, resource_type, shared_dir, debug_use_default_vertexdescriptor, debug_search_for_swapped_ids):
	# Definitions
	shared_material_dir = os.path.join(shared_dir, "Material")
	shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDesc")
	shared_vertex_descriptor_ported_x360_dir = os.path.join(shared_dir, "VertexDesc_port_X360")
	shared_vertex_descriptor_ported_ps3_dir = os.path.join(shared_dir, "VertexDesc_port_PS3")
	
	# Mesh data definitions
	num_meshes = len(object.material_slots)
	not_used_material_slots = [x for x in range(num_meshes)]
	indices_buffer = [[] for _ in range(num_meshes)]
	vertices_buffer = [[] for _ in range(num_meshes)]
	meshes_info = [[] for _ in range(num_meshes)]
	
	# Inits
	mesh = object.data
	mesh.calc_normals_split()
	loops = mesh.loops
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	has_uv = len(mesh.uv_layers) > 0
	if has_uv:
		uv_layers = bm.loops.layers.uv
	else:
		uv_layers = []
	
	if num_meshes == 0:
		print("ERROR: no materials applied on mesh %s." % mesh.name)
		return (meshes_info, indices_buffer, vertices_buffer, 1)
	
	if len(bm.verts) >= 0xFFF0:		# It is better to reduce from 0xFFFF as a safety measure
		print("ERROR: number of vertices higher than the supported by the game on mesh %s." % mesh.name)
		return (meshes_info, indices_buffer, vertices_buffer, 1)
	
	blend_index1 = bm.verts.layers.int.get("blend_index1")
	blend_index2 = bm.verts.layers.int.get("blend_index2")
	blend_index3 = bm.verts.layers.int.get("blend_index3")
	blend_index4 = bm.verts.layers.int.get("blend_index4")
	
	blend_weight1 = bm.verts.layers.float.get("blend_weight1")
	blend_weight2 = bm.verts.layers.float.get("blend_weight2")
	blend_weight3 = bm.verts.layers.float.get("blend_weight3")
	blend_weight4 = bm.verts.layers.float.get("blend_weight4")
	
	mesh_indices = [[] for _ in range(num_meshes)]
	mesh_vertices_buffer = [{} for _ in range(num_meshes)]
	vert_indices = [{} for _ in range(num_meshes)]
	
	ind = [0] * num_meshes
	
	mMaterialIds = [""] * num_meshes
	
	positions = [{} for _ in range(num_meshes)]
	normals = [{} for _ in range(num_meshes)]
	blends_indices = [{} for _ in range(num_meshes)]
	blends_weights = [{} for _ in range(num_meshes)]
	uv = [{} for _ in range(num_meshes)]
	
	for face in bm.faces:
		if face.hide == False:
			mesh_index = face.material_index
			indices = []
			
			if mMaterialIds[mesh_index] == "":
				if mesh.materials[mesh_index] == None:
					print("ERROR: face without material found on mesh %s." % mesh.name)
					return (meshes_info, indices_buffer, vertices_buffer, 1)
				mMaterialId = mesh.materials[mesh_index].name
				mMaterialIds[mesh_index] = mMaterialId.split(".")[0]
				not_used_material_slots.remove(mesh_index)
			
			if len(face.verts) > 3:
				print("ERROR: non triangular face on mesh %s." % mesh.name)
				return (meshes_info, indices_buffer, vertices_buffer, 1)
			
			for vert in face.verts:
				if vert.index not in vert_indices[mesh_index]:
					vert_indices[mesh_index][vert.index] = ind[mesh_index]
					ind[mesh_index] += 1
				vert_index = vert_indices[mesh_index][vert.index]
				indices.append(vert_index)
				if vert_index in positions[mesh_index]:
					continue
				positions[mesh_index][vert_index] = vert.co
				#normals[mesh_index][vert_index] = vert.normal
				#print(vert.normal)
				if None in [blend_index1, blend_index2, blend_index3, blend_index4]:
					blends_indices[mesh_index][vert_index] = [0, 0, 0, 0]
				else:
					blends_indices[mesh_index][vert_index] = [vert[blend_index1], vert[blend_index2], vert[blend_index3], vert[blend_index4]]
				if None in [blend_weight1, blend_weight2, blend_weight3, blend_weight4]:
					blends_weights[mesh_index][vert_index] = [0, 0, 0, 0]
				else:
					blends_weights[mesh_index][vert_index] = [int(round(vert[blend_weight1]*255.0/100.0)), int(round(vert[blend_weight2]*255.0/100.0)),
															  int(round(vert[blend_weight3]*255.0/100.0)), int(round(vert[blend_weight4]*255.0/100.0))]
			
			indices_buffer[mesh_index].append(indices)
			
			if has_uv:
				for loop in face.loops:
					uvs = []
					for layer in range(0, len(uv_layers)):
						uv_layer = bm.loops.layers.uv[layer]
						uvs.append(loop[uv_layer].uv)
					uv[mesh_index][vert_indices[mesh_index][loop.vert.index]] = uvs
			
			for index in indices:
				if index in mesh_indices[mesh_index]:
					continue
				mesh_indices[mesh_index].append(index)
				
				position = positions[mesh_index][index]
				#normal = normals[mesh_index][index]
				normal = [0.0, 0.0, 0.0]
				tangent = [0.0, 0.0, 0.0]
				color = [0, 0, 0, 0]
				if len(uv_layers) >= 3:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = uv[mesh_index][index][2]
				elif len(uv_layers) == 2:
					uv1 = uv[mesh_index][index][0]
					uv2 = uv[mesh_index][index][1]
					uv3 = [0.0, 0.0]
				elif len(uv_layers) == 1:
					uv1 = uv[mesh_index][index][0]
					uv2 = [0.0, 0.0]
					uv3 = [0.0, 0.0]
				else:
					uv1 = [0.0, 0.0]
					uv2 = [0.0, 0.0]
					uv3 = [0.0, 0.0]
				blend_indices = blends_indices[mesh_index][index]
				blend_weight = blends_weights[mesh_index][index]
				mesh_vertices_buffer[mesh_index][index] = [index, position[:], normal[:], tangent[:], color[:], uv1[:], uv2[:], uv3[:], blend_indices[:], blend_weight[:]]
	
	normals = [{} for _ in range(num_meshes)]
	for face in mesh.polygons:
		if face.hide == False:
			mesh_index = face.material_index
			for loop_ind in face.loop_indices:
				vert_index = vert_indices[mesh_index][loops[loop_ind].vertex_index]
				if vert_index in normals[mesh_index]:
					continue
				normals[mesh_index][vert_index] = loops[loop_ind].normal[:]
				mesh_vertices_buffer[mesh_index][vert_index][2] = normals[mesh_index][vert_index][:]
	
	bm.clear()
	bm.free()
	
	indices_buffer_size = 0
	indices_buffer_start = 0
	for mesh_index in range(0, num_meshes):
		try:
			if debug_use_default_vertexdescriptor == True:
				raise Exception
			mVertexDescriptorIds = mesh["VertexDescriptorIds"][mesh_index]
		except:
			if debug_use_default_vertexdescriptor == False:
				print("WARNING: mesh %s is missing parameter %s. Assuming default ones." % (mesh.name, '"VertexDescriptorIds"'))
			mVertexDescriptorIds = ["B8_23_13_0F", "7F_44_88_2B", "0E_46_97_8F", "9F_F0_42_9F"]
			if resource_type == "InstanceList" or resource_type == "PropInstanceData":
				mVertexDescriptorIds = ["4C_66_C2_A5", "A2_1F_12_2A"]	# it was 4C_66_C2_A5 and E1_74_B4_4A, but there was an issue with shadows on transparent parts
		if resource_type == "InstanceList" and len(mVertexDescriptorIds) == 1:
			mVertexDescriptorIds.append(mVertexDescriptorIds[0])
		mVertexDescriptorId_main = mVertexDescriptorIds[0]
		vertex_descriptor_path = os.path.join(shared_vertex_descriptor_dir, mVertexDescriptorId_main + ".dat")
		if not os.path.isfile(vertex_descriptor_path):
			vertex_descriptor_path = os.path.join(shared_vertex_descriptor_ported_x360_dir, mVertexDescriptorId_main + ".dat")
			if not os.path.isfile(vertex_descriptor_path):
				vertex_descriptor_path = os.path.join(shared_vertex_descriptor_ported_ps3_dir, mVertexDescriptorId_main + ".dat")
				if not os.path.isfile(vertex_descriptor_path):
					print("ERROR: failed to open vertex descriptor %s: no such file in '%s', '%s' and '%s'." % (mVertexDescriptorId_main, shared_vertex_descriptor_dir, shared_vertex_descriptor_ported_x360_dir, shared_vertex_descriptor_ported_ps3_dir))
					return (meshes_info, indices_buffer, vertices_buffer, 1)
		
		vertex_properties = read_vertex_descriptor(vertex_descriptor_path)
		
		vertex_size = vertex_properties[0]
		semantic_properties = vertex_properties[1][0]
		
		for semantic in semantic_properties:
			if semantic[0] == "TANGENT":
				calculate_tangents(indices_buffer[mesh_index], mesh_vertices_buffer[mesh_index])
		
		vertices_buffer[mesh_index] = [semantic_properties, mesh_vertices_buffer[mesh_index], mesh_indices[mesh_index], vertex_size]
		
		indices_buffer_start = indices_buffer_start + indices_buffer_size
		indices_buffer_start += calculate_padding(indices_buffer_start*2, 0x10) // 2
		indices_buffer_size = len(indices_buffer[mesh_index])*3
		num_vertex_descriptors = len(mVertexDescriptorIds)
		try:
			sub_part_code = mesh["sub_part_code"][mesh_index]
		except:
			print("WARNING: mesh %s is missing parameter %s. Assuming as zero." % (mesh.name, '"sub_part_code"'))
			sub_part_code = 0
		
		mMaterialId = mMaterialIds[mesh_index]
		mat = bpy.data.materials.get(mMaterialId)
		try:
			is_shared_asset = mat["is_shared_asset"]
		except:
			is_shared_asset = False
		
		if is_shared_asset == True:
			material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
			if not os.path.isfile(material_path):
				mMaterialId_swap = id_swap(mMaterialId)
				material_path = os.path.join(shared_material_dir, mMaterialId_swap + ".dat")
				if os.path.isfile(material_path) and debug_search_for_swapped_ids == True:
					mMaterialId = mMaterialId_swap
		
		meshes_info[mesh_index] = [mesh_index, [indices_buffer_start, indices_buffer_size, num_vertex_descriptors, sub_part_code], mMaterialId, mVertexDescriptorIds]
	
	# Verifying if some material is not used
	if len(not_used_material_slots) != 0:
		for material_index in reversed(not_used_material_slots):
			mesh_index = material_index
			del meshes_info[mesh_index]
			del indices_buffer[mesh_index]
			del vertices_buffer[mesh_index]
		
		num_meshes = num_meshes - len(not_used_material_slots)
		
		for mesh_index in range(0, num_meshes):
			meshes_info[mesh_index][0] = mesh_index
	
	return (meshes_info, indices_buffer, vertices_buffer, 0)


def read_polygonsoup_object(object):
	PolygonSoupVertices = []
	PolygonSoupPolygons = []
	PolygonSoupPolygons_triangles = []
	
	# Inits
	mesh = object.data
	loops = mesh.loops
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	edge_cosine1 = bm.faces.layers.int.get("edge_cosine1")
	edge_cosine2 = bm.faces.layers.int.get("edge_cosine2")
	edge_cosine3 = bm.faces.layers.int.get("edge_cosine3")
	edge_cosine4 = bm.faces.layers.int.get("edge_cosine4")
	collision_tag0 = bm.faces.layers.int.get("collision_tag0")
	
	for vert in bm.verts:
		if vert.hide == False:
			#PolygonSoupVertices.append(vert.co[:])
			PolygonSoupVertices.append([round(vert_co) for vert_co in vert.co])
			#if any(vert.co) > 0xFFFF or any(vert.co) < 0:
			#	print(vert.co, object.name)
			#for vert_co in vert.co:
			#	if vert_co > 0xFFFF or vert_co < 0:
			#		print(vert.co, object.name)
	
	if len(PolygonSoupVertices) >= 0xFF:
		print("ERROR: number of vertices higher than the supported by the game on collision mesh %s." % mesh.name)
		return (1, [], [], 0)
	
	for face in bm.faces:
		if face.hide == False:
			if len(face.verts) > 4 or len(face.verts) < 3:
				print("ERROR: non triangular or quad face on mesh %s." % mesh.name)
				return (1, [], [], 0)
			
			material_index = face.material_index
			#if mesh.materials[material_index] == None:
				#print("ERROR: face without material found on mesh %s." % mesh.name)
				#return (1, [], [], 0)
				#print("WARNING: face without material found on mesh %s." % mesh.name)
			
			has_material = True
			try:
				if mesh.materials[material_index] == None:
					print("WARNING: face without material found on mesh %s." % mesh.name)
					has_material = False
			except:
				print("WARNING: face without material found on mesh %s." % mesh.name)
				has_material = False
			
			if collision_tag0 == None:
				mu16CollisionTag_part0 = 0
			else:
				mu16CollisionTag_part0 = face[collision_tag0]
			#mu16CollisionTag_part1 = mesh.materials[material_index].name.split(".")[0]
			try:
				mu16CollisionTag_part1 = mesh.materials[material_index].name.split(".")[0]
				mu16CollisionTag_part1 = int(mu16CollisionTag_part1, 16)
			except:
				#print("ERROR: face material name %s (collision tag) is not in the proper formating." % mesh.materials[material_index].name)
				#return (1, [], [], 0)
				if has_material:
					print("WARNING: face material name %s (collision tag) is not in the proper formating. Setting it to 0xA010." % mesh.materials[material_index].name)
				else:
					print("WARNING: setting collision tag as 0xA010 to the face without material.")
				mu16CollisionTag_part1 = 0xA010
			
			mau8VertexIndices = []
			for vert in face.verts:
				vert_index = PolygonSoupVertices.index([round(vert_co) for vert_co in vert.co])
				mau8VertexIndices.append(vert_index)
			
			if None in [edge_cosine1, edge_cosine2, edge_cosine3, edge_cosine4]:
				mau8EdgeCosines = [0xFF, 0xFF, 0xFF, 0xFF]
			else:
				mau8EdgeCosines = [face[edge_cosine1], face[edge_cosine2], face[edge_cosine3], face[edge_cosine4]]
			
			if len(face.verts) == 4:
				mau8VertexIndices = [mau8VertexIndices[0], mau8VertexIndices[1], mau8VertexIndices[3], mau8VertexIndices[2]]
				PolygonSoupPolygons.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
			elif len(face.verts) == 3:
				PolygonSoupPolygons_triangles.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
	
	mu8NumQuads = len(PolygonSoupPolygons)
	PolygonSoupPolygons.extend(PolygonSoupPolygons_triangles)
	
	if len(PolygonSoupPolygons) >= 0xFF:
		print("ERROR: number of faces higher than the supported by the game on collision mesh %s." % mesh.name)
		return (1, [], [], 0)
	
	return (0, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads)


def read_bbox_object(object):
	maCornerSkinData = []
	
	# Inits
	mesh = object.data
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	if len(bm.verts) != 10:
		print("ERROR: number of vertices higher or lower than the necessary by a BBoxSkin object on mesh %s." % mesh.name)
		return (1, [], [], [])
	
	blend_index1 = bm.verts.layers.int.get("blend_index1")
	blend_index2 = bm.verts.layers.int.get("blend_index2")
	blend_index3 = bm.verts.layers.int.get("blend_index3")
	
	blend_weight1 = bm.verts.layers.float.get("blend_weight1")
	blend_weight2 = bm.verts.layers.float.get("blend_weight2")
	blend_weight3 = bm.verts.layers.float.get("blend_weight3")
	
	for i, vert in enumerate(bm.verts):
		if vert.hide == False:
			mVertex = [*vert.co[:], 0]
			
			if None in [blend_index1, blend_index2, blend_index3]:
				mauBoneIndices = [0, 0, 0]
			else:
				mauBoneIndices = [vert[blend_index1], vert[blend_index2], vert[blend_index3]]
			if None in [blend_weight1, blend_weight2, blend_weight3]:
				mafWeights = [0, 0, 0]
			else:
				mafWeights = [vert[blend_weight1]/100.0, vert[blend_weight2]/100.0, vert[blend_weight3]/100.0]
			
			mSkinData = [mVertex, mafWeights, mauBoneIndices]
			if i < 8:
				maCornerSkinData.append(mSkinData)
			elif i == 8:
				mCentreSkinData = mSkinData[:]
			elif i == 9:
				mJointSkinData = mSkinData[:]
	
	return (0, maCornerSkinData, mCentreSkinData, mJointSkinData)


def read_vertex_descriptor(vertex_descriptor_path):
	vertex_properties = []
	with open(vertex_descriptor_path, "rb") as f:
		unk1 = struct.unpack("<i", f.read(0x4))[0]
		attibutes_flags = struct.unpack("<i", f.read(0x4))[0]
		_ = struct.unpack("<i", f.read(0x4))[0] #null
		num_vertex_attibutes = struct.unpack("<i", f.read(0x4))[0]
		
		semantic_properties = []
		for i in range(0, num_vertex_attibutes):
			semantic_type = struct.unpack("<B", f.read(0x1))[0]
			semantic_index = struct.unpack("<B", f.read(0x1))[0]
			input_slot = struct.unpack("<B", f.read(0x1))[0]
			element_class = struct.unpack("<B", f.read(0x1))[0]
			data_type = struct.unpack("<i", f.read(0x4))[0]
			data_offset = struct.unpack("<i", f.read(0x4))[0]
			step_rate = struct.unpack("<i", f.read(0x4))[0] #null
			vertex_size = struct.unpack("<i", f.read(0x4))[0]
			
			semantic_type = get_vertex_semantic(semantic_type)
			data_type = get_vertex_data_type(data_type)
			
			semantic_properties.append([semantic_type, data_type, data_offset])
		
		vertex_properties = [vertex_size, [semantic_properties]]
		
	return vertex_properties


def read_shader(shader_path):
	ShaderType = ""
	raster_types = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		material_state_info_pointer = struct.unpack("<i", f.read(0x4))[0]
		num_material_states = struct.unpack("<B", f.read(0x1))[0]
		
		f.seek(0x8, 0)
		shader_description_offset = struct.unpack("<i", f.read(0x4))[0]
		f.seek(shader_description_offset, 0)
		shader_description = f.read(file_size-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		# Material constants
		material_constants = []
		f.seek(material_state_info_pointer, 0)
		for i in range(0, num_material_states):
			f.seek(material_state_info_pointer + 0x3C*i + 0x32, 0)
			material_constants.append(struct.unpack("<H", f.read(0x2))[0])
		
		# VertexShader
		f.seek(0x50, 0)
		muNumVertexShaderConstantsInstances = struct.unpack("<B", f.read(0x1))[0]
		
		
		# PixelShader
		f.seek(0x53, 0)
		muNumPixelShaderConstantsInstances = struct.unpack("<B", f.read(0x1))[0]
		
		
		f.seek(0x10, 0)
		mpauShaderConstantsInstanceSize = struct.unpack("<I", f.read(0x4))[0]
		mpafShaderConstantsInstanceData = struct.unpack("<I", f.read(0x4))[0]
		mpauShaderNamesHash = struct.unpack("<I", f.read(0x4))[0]
		
		f.seek(mpauShaderConstantsInstanceSize, 0)
		mauVertexShaderConstantsInstanceSize = struct.unpack("<%dB" % muNumVertexShaderConstantsInstances, f.read(0x1*muNumVertexShaderConstantsInstances))
		mauPixelShaderConstantsInstanceSize = struct.unpack("<%dB" % muNumPixelShaderConstantsInstances, f.read(0x1*muNumPixelShaderConstantsInstances))
		
		f.seek(mpafShaderConstantsInstanceData, 0)
		mafVertexShaderConstantsInstanceData = []
		mafPixelShaderConstantsInstanceData = []
		for i in range(0, muNumVertexShaderConstantsInstances):
			mafVertexShaderConstantsInstanceData.append(struct.unpack("<ffff", f.read(0x4*4)))
		for i in range(0, muNumPixelShaderConstantsInstances):
			mafPixelShaderConstantsInstanceData.append(struct.unpack("<ffff", f.read(0x4*4)))
		
		f.seek(mpauShaderNamesHash, 0)
		mauVertexShaderNamesHash = struct.unpack("<%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))
		mauPixelShaderNamesHash = struct.unpack("<%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))
		
		
		# Samplers
		f.seek(0x5C, 0)
		mpaSamplers = struct.unpack("<i", f.read(0x4))[0]
		miNumSamplers = struct.unpack("<B", f.read(0x1))[0]
		
		f.seek(0x68, 0)
		end_raster_types_offset = struct.unpack("<i", f.read(0x4))[0]
		
		raster_type_offsets = []
		miChannel = []
		for i in range(0, miNumSamplers):
			f.seek(mpaSamplers + i*0x8, 0)
			raster_type_offsets.append(struct.unpack("<i", f.read(0x4))[0])
			miChannel.append(struct.unpack("<B", f.read(0x1))[0])
		
		raster_type_offsets.append(end_raster_types_offset)
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			
			#if miChannel[i] == 15:
			#	continue
			#elif miChannel[i] == 13:
			#	continue
			raster_types.append([miChannel[i], raster_type])
		
		if shader_description == "Road_Night_Detailmap_Opaque_Singlesided":
			#This shader is missing the definition of two AoMaps
			raster_types.append([3, "AoMapSampler"])
			raster_types.append([4, "AoMapSampler2"])
		
		elif shader_description == "Tunnel_Road_Detailmap_Opaque_Singlesided":
			#This shader is missing the definition of two AoMaps
			raster_types.append([3, "AoMapSampler"])
			raster_types.append([4, "AoMapSampler2"])
		
		elif shader_description == "Cable_GreyScale_Doublesided":
			# This shader is used by a material (3A_47_5B_86) that has a different number of parameters 1
			# than the specified by the shader
			muNumVertexShaderConstantsInstances = 2
		
		#elif shader_description == "Vehicle_Greyscale_Window_Textured":
		#	#This shader has one extra map definition
		#	raster_types.remove([14, "GlassFractureSampler"])
		
		raster_types.sort(key=lambda x:x[0])
		
		#raster_types_splitted = []
		#for raster_type_data in raster_types:
		#	raster_types_splitted.append(raster_type_data[1])
		#
		#raster_types = raster_types_splitted[:]
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
	
	return (shader_description, raster_types_dict, num_material_states, material_constants, muNumVertexShaderConstantsInstances, mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash, muNumPixelShaderConstantsInstances, mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash)


def write_instancelist(instancelist_path, instances, muNumInstances):
	os.makedirs(os.path.dirname(instancelist_path), exist_ok = True)
	
	with open(instancelist_path, "wb") as f:
		mpaInstances = 0x10
		muArraySize = len(instances)
		if muArraySize == 0:
			mpaInstances = 0
		muVersionNumber = 0x1
		
		instances_properties = []
		instances_properties_backdrop = []
		
		for instance in instances:
			object_index = instance[0]
			mModelId = instance[1][0]
			instance_properties = instance[1][1]
			is_always_loaded = instance_properties[-1]
			
			if is_always_loaded:
				instances_properties.append([object_index, [mModelId, instance_properties]])
			else:
				instances_properties_backdrop.append([object_index, [mModelId, instance_properties]])
		
		instances_properties.sort(key=lambda x:x[0])
		instances_properties_backdrop.sort(key=lambda x:x[0])
		
		instances_properties.extend(instances_properties_backdrop)
		
		
		# Writing
		f.write(struct.pack('<I', mpaInstances))
		f.write(struct.pack('<I', muArraySize))
		f.write(struct.pack('<I', muNumInstances))
		f.write(struct.pack('<I', muVersionNumber))
		
		for i, instance in enumerate(instances_properties):
			mModelId = instance[1][0]
			mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared, mTransform, is_always_loaded = instance[1][1]
			
			f.seek(mpaInstances + 0x50*i, 0)
			f.write(struct.pack('<ihHIf', mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared))
			f.write(struct.pack('<4f', *mTransform[0]))
			f.write(struct.pack('<4f', *mTransform[1]))
			f.write(struct.pack('<4f', *mTransform[2]))
			f.write(struct.pack('<4f', *mTransform[3]))
			
			f.seek(mpaInstances + 0x50*muArraySize + 0x10*i, 0)
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack("<i", 0))
			f.write(struct.pack("<i", mpaInstances + 0x50*i))
			f.write(struct.pack("<i", 0))
	
	return 0


def write_propinstancedata(propinstancedata_path, instances, track_unit_number, muNumberOfPropInstanceData, number_of_prop_parts, num_unk1s, unk1s):
	os.makedirs(os.path.dirname(propinstancedata_path), exist_ok = True)
	
	with open(propinstancedata_path, "wb") as f:
		mpaPropInstanceData = 0x0 
		if muNumberOfPropInstanceData > 0:
			mpaPropInstanceData = 0x20
		unk1_pointer = mpaPropInstanceData + muNumberOfPropInstanceData*0x50
		data_length = 0x20 + muNumberOfPropInstanceData*0x50*2 + num_unk1s*0xC
		muNumberOfPropInstanceDataPlusPropParts = muNumberOfPropInstanceData
		muZoneNumber = track_unit_number
		
		data_length_write = data_length
		if muNumberOfPropInstanceData == 0 and num_unk1s == 0:
			data_length_write = 0
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0x20))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', muZoneNumber))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			return 0
		
		# Writing
		f.write(struct.pack('<I', unk1_pointer))
		f.write(struct.pack('<I', num_unk1s))
		f.write(struct.pack('<I', mpaPropInstanceData))
		f.write(struct.pack('<I', data_length_write))
		f.write(struct.pack('<I', muNumberOfPropInstanceDataPlusPropParts))
		f.write(struct.pack('<I', muNumberOfPropInstanceData))
		f.write(struct.pack('<I', muZoneNumber))
		
		f.seek(mpaPropInstanceData, 0)
		for instance in instances:
			mModelId = instance[0]
			muTypeId, muFlags, muInstanceID, muAlternativeType, mn8RotSpeed, mn8MAngle, mWorldTransform, prop_type, muPartId = instance[1]
			
			if prop_type.lower() == "prop_part" or prop_type.lower() == "prop_alternative":
				continue
			
			f.write(struct.pack('<4f', *mWorldTransform[0]))
			f.write(struct.pack('<4f', *mWorldTransform[1]))
			f.write(struct.pack('<4f', *mWorldTransform[2]))
			f.write(struct.pack('<4f', *mWorldTransform[3]))
			
			f.write(struct.pack("<H", muTypeId))
			f.write(struct.pack("<B", 0))
			f.write(struct.pack("<B", muFlags))
			f.write(struct.pack("<I", muInstanceID))
			f.write(struct.pack("<H", muAlternativeType))
			f.write(struct.pack("<b", mn8RotSpeed))
			f.write(struct.pack("<BB", *mn8MAngle))
			f.write(struct.pack("<BBB", 0, 0, 0))
			
			try:
				muNumberOfPropInstanceDataPlusPropParts += number_of_prop_parts[muTypeId]
			except:
				pass
		
		f.seek(unk1_pointer, 0)
		value = 0
		for i in range(0, num_unk1s):
			unk1 = unk1s[i]
			f.write(struct.pack('<HH', *unk1[:2]))
			f.write(struct.pack('<H', value))
			f.write(struct.pack('<HHH', *unk1[2:]))
			value += unk1[2]
		
		#f.seek(data_length + 0x20, 0)
		f.write(bytearray([0])*(int(data_length + 0x20 - f.tell())))
		padding = calculate_padding(data_length + 0x20, 0x10)
		#f.seek(padding, 1)
		
		f.write(bytearray([0])*padding)
		
		f.seek(0x10, 0)
		f.write(struct.pack('<I', muNumberOfPropInstanceDataPlusPropParts))
	
	return 0


def write_propgraphicslist(propgraphicslist_path, instances, track_unit_number):
	os.makedirs(os.path.dirname(propgraphicslist_path), exist_ok = True)
	
	with open(propgraphicslist_path, "wb") as f:
		props = []
		prop_parts = []
		for instance in instances:
			muTypeId = instance[1][0]
			prop_type = instance[1][7]
			
			if prop_type.lower() == "prop" or prop_type.lower() == "prop_alternative":
				if muTypeId in (rows[0] for rows in props):
					continue
				mModelId = instance[0]
				mParts = instance[1][8]
			
				#props.append([mModelId, muTypeId, 0])
				props.append([muTypeId, 0, mModelId])
			
			elif prop_type.lower() == "prop_part":
				mModelId = instance[0]
				muPartId = instance[1][8]
				#prop_data = [mModelId, muTypeId, muPartId]
				prop_data = [muTypeId, muPartId, mModelId]
				if prop_data in prop_parts:
					continue
				prop_parts.append(prop_data)
		
		prop_parts = sorted(prop_parts)
		
		list_a = [prop[0] for prop in props]
		d = {v:i for i, v in enumerate(list_a)}
		list_b = [[] for _ in range(len(d))]
		for prop in prop_parts:
			list_b[d[prop[0]]].append(prop)
		
		number_of_prop_parts = {prop_group[0][0]: len(prop_group) for prop_group in list_b if prop_group}
		flat_list = [item for sublist in list_b for item in sublist]
		
		prop_parts = flat_list[:]
		
		muSizeInBytes = 0x20
		muZoneNumber = track_unit_number
		muNumberOfPropModels = len(props)
		muNumberOfPropPartModels = len(prop_parts)
		mpaPropGraphics = 0x0
		mpaPropPartGraphics = 0x0
		if muNumberOfPropModels > 0:
			mpaPropGraphics = 0x20
			muSizeInBytes = mpaPropGraphics + muNumberOfPropModels*0xC
		if muNumberOfPropPartModels > 0:
			mpaPropPartGraphics = mpaPropGraphics + muNumberOfPropModels*0xC
			mpaPropPartGraphics += calculate_padding(mpaPropPartGraphics, 0x10)
			muSizeInBytes = mpaPropPartGraphics + muNumberOfPropPartModels*0xC
		
		
		# Writing
		f.write(struct.pack('<I', muSizeInBytes))
		f.write(struct.pack('<I', muZoneNumber))
		f.write(struct.pack('<I', muNumberOfPropModels))
		f.write(struct.pack('<I', muNumberOfPropPartModels))
		f.write(struct.pack('<I', mpaPropGraphics))
		f.write(struct.pack('<I', mpaPropPartGraphics))
		
		if muNumberOfPropModels > 0:
			f.seek(mpaPropGraphics, 0)
		mpParts = 0
		for prop in props:
			muTypeId, mpParts_, mModelId = prop
			mpPropModel = 0
			
			for i, prop_part in enumerate(prop_parts):
				if muTypeId == prop_part[0]:
					mpParts = mpaPropPartGraphics + i*0xC
					break
			
			f.write(struct.pack("<I", muTypeId))
			f.write(struct.pack("<i", mpPropModel))
			f.write(struct.pack("<i", mpParts))
		
		if muNumberOfPropPartModels > 0:
			f.seek(mpaPropPartGraphics, 0)
		for prop_part in prop_parts:
			muTypeId, muPartId, mModelId = prop_part
			mpPropModel = 0
			f.write(struct.pack("<I", muTypeId))
			f.write(struct.pack("<i", muPartId))
			f.write(struct.pack("<i", mpPropModel))
		
		padding = calculate_padding(f.tell(), 0x10)
		#f.seek(padding, 1)
		f.write(bytearray([0])*padding)
		
		for i in range(0, muNumberOfPropModels):
			mModelId = props[i][2]
			muOffset = mpaPropGraphics + i*0xC + 0x4
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
		
		for i in range(0, muNumberOfPropPartModels):
			mModelId = prop_parts[i][2]
			muOffset = mpaPropPartGraphics + i*0xC + 0x8
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
	
	return number_of_prop_parts


def write_staticsoundmap(staticsoundmap_path, sound_data):
	os.makedirs(os.path.dirname(staticsoundmap_path), exist_ok = True)
	
	with open(staticsoundmap_path, "wb") as f:
		staticsoundmap_info, instances = sound_data
		StaticSoundEntities, mSubRegions_first, mSubRegions_count = instances
		mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType = staticsoundmap_info
		
		miNumEntities = len(StaticSoundEntities)
		mMin = [0.0, 0.0]
		mMax = [50.0, 50.0]
		if miNumEntities > 0:
			mMin = [min(entity[1][0] for entity in StaticSoundEntities), min(entity[1][2] for entity in StaticSoundEntities)]
			mMax = [max(entity[1][0] for entity in StaticSoundEntities), max(entity[1][2] for entity in StaticSoundEntities)]
		mpEntities = 0x40
		mpSubRegions = mpEntities + miNumEntities*0x10
		
		miNumSubRegions = miNumSubRegionsX*miNumSubRegionsZ
		
		data_length = mpSubRegions + miNumSubRegions*0x4
		padding = calculate_padding(data_length, 0x10)
		
		# Writing
		f.write(struct.pack('<ff', *mMin))
		f.seek(0x8, 1)
		f.write(struct.pack('<ff', *mMax))
		f.seek(0x8, 1)
		f.write(struct.pack('<f', mfSubRegionSize))
		f.write(struct.pack('<I', mpSubRegions))
		f.write(struct.pack('<i', miNumSubRegionsX))
		f.write(struct.pack('<i', miNumSubRegionsZ))
		f.write(struct.pack('<I', mpEntities))
		f.write(struct.pack('<i', miNumEntities))
		f.write(struct.pack('<i', meRootType))
		
		f.seek(mpEntities, 0)
		for entity in StaticSoundEntities:
			index, mPosPlus, unk = entity
			
			f.write(struct.pack('<fff', *mPosPlus))
			f.write(struct.pack('<HH', *unk))
		
		f.seek(mpSubRegions, 0)
		for i in range(0, miNumSubRegions):
			f.write(struct.pack('<h', mSubRegions_first[i]))
			f.write(struct.pack('<h', mSubRegions_count[i]))
		
		f.write(bytearray([0])*padding)
	
	return 0


def write_polygonsouplist(polygonsouplist_path, PolygonSoups):
	os.makedirs(os.path.dirname(polygonsouplist_path), exist_ok = True)
	
	with open(polygonsouplist_path, "wb") as f:
		miNumPolySoups = len(PolygonSoups)
		if miNumPolySoups == 0:
			f.write(struct.pack('<3f', 0, 0, 0))
			f.write(struct.pack('<f', 0))
			f.write(struct.pack('<3f', 0, 0, 0))
			f.write(struct.pack('<f', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<I', 0))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0x30))
			return 0
		
		mMin_w = 0
		mMax_w = 0
		mpapPolySoups = 0x30
		miNumPolySoups = len(PolygonSoups)
		mpaPolySoupBoxes = mpapPolySoups + 0x4*miNumPolySoups
		padding = calculate_padding(mpaPolySoupBoxes, 0x10)
		mpaPolySoupBoxes += padding
		mpaPolySoupBoxesEnd = mpaPolySoupBoxes + math.ceil(miNumPolySoups/4.0)*0x70
		
		mpPolySoup_0 = calculate_mpPolySoup(miNumPolySoups, mpaPolySoupBoxesEnd)
		
		mpPolySoups = []
		PolySoupBoxes = []
		header_size = 0x20
		mpPolySoups.append(mpPolySoup_0)
		for i in range(0, miNumPolySoups):
			#mpPolySoups.append(cte)
			object_index, PolySoupBox, maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons, mu8NumQuads = PolygonSoups[i]
			
			PolySoupBoxes.append(PolySoupBox)
			
			mpaVertices = mpPolySoups[i] + header_size
			
			mu8TotalNumPolys = len(PolygonSoupPolygons)
			mu8NumQuads = mu8NumQuads
			mu8NumVertices = len(PolygonSoupVertices)
			
			mpaPolygons = mpaVertices + mu8NumVertices*0x6
			mpaPolygons += calculate_padding(mpaPolygons, 0x10)
			mu16DataSize = mpaPolygons + mu8TotalNumPolys*0xC - mpPolySoups[i]
			
			#Checking out of bounds coordinates
			coordinates = list(zip(*PolygonSoupVertices))
			translation = [0, 0, 0]
			for j in range(0, 3):
				if min(coordinates[j]) < 0:
					translation[j] = min(coordinates[j])
			
			if translation != [0, 0, 0]:
				print("WARNING: Negative value on PolygonSoupMesh %d. Translate your mesh origin and the empty coordinates. Trying to apply a solution." % object_index)
				maiVertexOffsets[0] += translation[0]
				maiVertexOffsets[1] += translation[1]
				maiVertexOffsets[2] += translation[2]
				for j in range(0, mu8NumVertices):
					PolygonSoupVertices[j][0] -= translation[0]
					PolygonSoupVertices[j][1] -= translation[1]
					PolygonSoupVertices[j][2] -= translation[2]
			
			coordinates = list(zip(*PolygonSoupVertices))
			min_coord = 0xFFFF
			max_coord = 0
			for j in range(0, 3):
				if max(coordinates[j]) > max_coord:
					max_coord = max(coordinates[j])
				if min(coordinates[j]) < min_coord:
					min_coord = min(coordinates[j])
			
			if max_coord > 0xFFFF:
				print("WARNING: Out of bounds (>0xFFFF) value on PolygonSoupMesh %d. Translate your mesh origin and the empty coordinates or modify the object scale. Trying to apply a solution." % object_index)
				for j in range(0, 3):
					translation[j] = min(coordinates[j])
				partial_mfComprGranularity = (0xFFFF*1.0)/((max_coord-min_coord)*1.0)
				mfComprGranularity /= partial_mfComprGranularity
				maiVertexOffsets[0] = round((maiVertexOffsets[0] + translation[0])*partial_mfComprGranularity)
				maiVertexOffsets[1] = round((maiVertexOffsets[1] + translation[1])*partial_mfComprGranularity)
				maiVertexOffsets[2] = round((maiVertexOffsets[2] + translation[2])*partial_mfComprGranularity)
				for j in range(0, mu8NumVertices):
					PolygonSoupVertices[j][0] = round((PolygonSoupVertices[j][0] - translation[0])*partial_mfComprGranularity)
					PolygonSoupVertices[j][1] = round((PolygonSoupVertices[j][1] - translation[1])*partial_mfComprGranularity)
					PolygonSoupVertices[j][2] = round((PolygonSoupVertices[j][2] - translation[2])*partial_mfComprGranularity)
			
			PolygonSoups[i] = [maiVertexOffsets, mfComprGranularity, mpaPolygons, mpaVertices, mu16DataSize, mu8TotalNumPolys, mu8NumQuads, mu8NumVertices, PolygonSoupVertices, PolygonSoupPolygons]
			
			mpPolySoup_next = mpaPolygons + mu8TotalNumPolys*0xC
			mpPolySoup_next += calculate_padding(mpPolySoup_next, 0x80)
			mpPolySoups.append(mpPolySoup_next)
		
		del mpPolySoups[-1]
		
		#mMin = [min([mAabbMin[0][0] for mAabbMin in PolySoupBoxes]), min([mAabbMin[0][1] for mAabbMin in PolySoupBoxes]), min([mAabbMin[0][2] for mAabbMin in PolySoupBoxes])]
		
		mMin = [min([mAabbMin[0][i] for mAabbMin in PolySoupBoxes]) for i in range(0, 3)]
		mMax = [max([mAabbMax[1][i] for mAabbMax in PolySoupBoxes]) for i in range(0, 3)]
		
		miDataSize = mpPolySoups[-1] + PolygonSoups[-1][4]
		miDataSize += 0x60
		
		
		#Writing
		f.write(struct.pack('<3f', *mMin))
		f.write(struct.pack('<f', mMin_w))
		f.write(struct.pack('<3f', *mMax))
		f.write(struct.pack('<f', mMax_w))
		f.write(struct.pack('<I', mpapPolySoups))
		f.write(struct.pack('<I', mpaPolySoupBoxes))
		f.write(struct.pack('<i', miNumPolySoups))
		f.write(struct.pack('<i', miDataSize))
		
		f.seek(mpapPolySoups, 0)
		f.write(struct.pack('<%dI' % miNumPolySoups, *mpPolySoups))
		
		f.seek(mpaPolySoupBoxes, 0)
		for i in range(0, miNumPolySoups):
			f.seek(int(mpaPolySoupBoxes + 0x70*(i//4) + 0x4*(i%4)), 0)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][0][2]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', PolySoupBoxes[i][1][2]))
			f.seek(0xC, 1)
			f.write(struct.pack('<i', PolySoupBoxes[i][2]))
		
		for i in range(0, miNumPolySoups):
			f.seek(mpPolySoups[i], 0)
			
			maiVertexOffsets, mfComprGranularity, mpaPolygons, mpaVertices, mu16DataSize, mu8TotalNumPolys, mu8NumQuads, mu8NumVertices, PolygonSoupVertices, PolygonSoupPolygons = PolygonSoups[i]
			f.write(struct.pack('<3i', *maiVertexOffsets))
			f.write(struct.pack('<f', mfComprGranularity))
			f.write(struct.pack('<I', mpaPolygons))
			f.write(struct.pack('<I', mpaVertices))
			f.write(struct.pack('<H', mu16DataSize))
			f.write(struct.pack('<B', mu8TotalNumPolys))
			f.write(struct.pack('<B', mu8NumQuads))
			f.write(struct.pack('<B', mu8NumVertices))
			
			f.seek(mpaVertices, 0)
			for j in range(0, mu8NumVertices):
				f.write(struct.pack('<3H', *PolygonSoupVertices[j]))
			
			f.seek(mpaPolygons, 0)
			for j in range(0, mu8NumQuads):
				mu16CollisionTag, mau8VertexIndices, mau8EdgeCosines = PolygonSoupPolygons[j]
				f.write(struct.pack('<H', mu16CollisionTag[0]))
				f.write(struct.pack('<H', mu16CollisionTag[1]))
				f.write(struct.pack('<4B', *mau8VertexIndices))
				f.write(struct.pack('<4B', *mau8EdgeCosines))
			
			for j in range(mu8NumQuads, mu8TotalNumPolys):
				mu16CollisionTag, mau8VertexIndices, mau8EdgeCosines = PolygonSoupPolygons[j]
				f.write(struct.pack('<H', mu16CollisionTag[0]))
				f.write(struct.pack('<H', mu16CollisionTag[1]))
				f.write(struct.pack('<3B', *mau8VertexIndices))
				f.write(struct.pack('<B', 0xFF))
				f.write(struct.pack('<4B', *mau8EdgeCosines))
		
		#f.seek(miDataSize, 0)
		f.write(bytearray([0])*0x60)
		padding = calculate_padding(miDataSize, 0x10)
		f.write(bytearray([0])*padding)
	
	return 0


def write_idlist(idlist_path, mPolygonSoupListId):
	os.makedirs(os.path.dirname(idlist_path), exist_ok = True)
	
	with open(idlist_path, "wb") as f:
		mpaIds = 0x10
		muNumIds = 1
		muPad = [0x80, 0x96]
		padding_1 = 0x6
		padding_2 = 0xC
		
		f.write(struct.pack('<I', mpaIds))
		f.write(struct.pack('<I', muNumIds))
		f.write(struct.pack('<2B', *muPad))
		f.write(bytearray([0])*padding_1)
		f.write(id_to_bytes(mPolygonSoupListId))
		f.write(bytearray([0])*padding_2)
		
	return 0


def write_graphicsstub(graphicsstub_path, mGraphicsSpecId, mWheelGraphicsSpecId, mpVehicleGraphics_index, mpWheelGraphics_index):
	os.makedirs(os.path.dirname(graphicsstub_path), exist_ok = True)
	
	with open(graphicsstub_path, "wb") as f:
		f.write(struct.pack('<i', mpVehicleGraphics_index))
		f.write(struct.pack('<i', mpWheelGraphics_index))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		
		if mpVehicleGraphics_index == 1:
			mResourceId_1 = mGraphicsSpecId
			mResourceId_2 = mWheelGraphicsSpecId
		else:
			mResourceId_1 = mWheelGraphicsSpecId
			mResourceId_2 = mGraphicsSpecId
		
		f.write(id_to_bytes(mResourceId_1))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<I', 0))
		f.write(struct.pack('<i', 0))
		
		f.write(id_to_bytes(mResourceId_2))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<I', 0x4))
		f.write(struct.pack('<i', 0))
	
	return 0


def write_wheelgraphicsspec(wheelgraphicsspec_path, instances):
	os.makedirs(os.path.dirname(wheelgraphicsspec_path), exist_ok = True)
	
	with open(wheelgraphicsspec_path, "wb") as f:
		muVersion = 1
		mpWheelModel = 0
		mpCaliperModel = -1
		
		for i, instance in enumerate(instances):
			if instance[1][1] == False:
				mWheelModel = i
			elif instance[1][1] == True:
				mpCaliperModel = 1
				mCaliperModel = i
		
		f.write(struct.pack('<I', muVersion))
		f.write(struct.pack('<ii', mpWheelModel, mpCaliperModel))
		f.write(struct.pack('<i', 0))
		
		f.write(id_to_bytes(instances[mWheelModel][1][0]))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<I', 0x4))
		f.write(struct.pack('<i', 0))
		
		if mpCaliperModel != -1:
			f.write(id_to_bytes(instances[mCaliperModel][1][0]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', 0x8))
			f.write(struct.pack('<i', 0))
	
	return 0
		

def write_graphicsspec(graphicsspec_path, instances, muPartsCount, muShatteredGlassPartsCount):
	os.makedirs(os.path.dirname(graphicsspec_path), exist_ok = True)
	
	with open(graphicsspec_path, "wb") as f:
		muVersion = 0x3
		mppPartModels = 0x30
		mpShatteredGlassParts = mppPartModels + muPartsCount*0x4
		mpShatteredGlassParts += calculate_padding(mpShatteredGlassParts, 0x10)
		
		mpPartLocators = mpShatteredGlassParts + muShatteredGlassPartsCount*0xC
		mpPartLocators += calculate_padding(mpPartLocators, 0x10)
		
		mpPartVolumeIDs = mpPartLocators + muPartsCount*0x40
		
		mpNumRigidBodiesForPart = mpPartVolumeIDs + muPartsCount*0x1
		mpNumRigidBodiesForPart += calculate_padding(mpNumRigidBodiesForPart, 0x10)
		
		mppRigidBodyToSkinMatrixTransforms = mpNumRigidBodiesForPart + muPartsCount*0x1
		mppRigidBodyToSkinMatrixTransforms += calculate_padding(mppRigidBodyToSkinMatrixTransforms, 0x10)
		
		model_indices = [x for x in range(muPartsCount)]
		
		shattered_glasses = [[] for _ in range(muShatteredGlassPartsCount)]
		mTransforms = [[] for _ in range(muPartsCount)]
		part_volume_ids = [0]*muPartsCount
		mModelIds = [None]*(muPartsCount + muShatteredGlassPartsCount)
		
		for instance in instances:
			object_index = instance[0]
			mModelId = instance[1][0]
			is_shattered_glass = instance[1][-1]
			
			mModelIds[object_index] = mModelId
			if is_shattered_glass == True:
				if object_index < muPartsCount:
					print("ERROR: shattered glass object %s's index is out of range. Make sure its object index is placed after the objects indices. It should start at %d" % (mModelId, muPartsCount))
					return 1
				mpModel, muBodyPartIndex, muBodyPartType = instance[1][1][0]
				shattered_glasses[object_index - muPartsCount] = [mpModel, muBodyPartIndex, muBodyPartType]
			else:
				if object_index >= muPartsCount:
					print("ERROR: object %s's index is out of range. Make sure its object index is placed before the shattered glasses objects indices. It should end at %d" % (mModelId, muPartsCount-1))
					return 1
				mTransform = instance[1][1][0]
				part_volume_id = instance[1][1][1]
				mTransforms[object_index] = mTransform
				part_volume_ids[object_index] = part_volume_id
		
		rigid_bodies_for_part = [1]*muPartsCount
		
		transforms_rigid_body_pointer = mppRigidBodyToSkinMatrixTransforms + 0x4*muPartsCount
		transforms_rigid_body_pointer += calculate_padding(transforms_rigid_body_pointer, 0x10)
		transforms_rigid_body_pointers = [transforms_rigid_body_pointer + 0x40*x for x in range(muPartsCount)]
		
		transform_rigid_body = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
		transforms_rigid_body = [transform_rigid_body]*muPartsCount
		
		muOffsets = [mppPartModels + 0x4*x for x in range(muPartsCount)]
		muOffsets_shattered_glass = [mpShatteredGlassParts + 0xC*x for x in range(muShatteredGlassPartsCount)]
		muOffsets += muOffsets_shattered_glass[:]
		
		# Writing
		f.write(struct.pack('<I', muVersion))
		f.write(struct.pack('<Ii', muPartsCount, mppPartModels))
		f.write(struct.pack('<Ii', muShatteredGlassPartsCount, mpShatteredGlassParts))
		f.write(struct.pack('<i', mpPartLocators))
		f.write(struct.pack('<i', mpPartVolumeIDs))
		f.write(struct.pack('<i', mpNumRigidBodiesForPart))
		f.write(struct.pack('<i', mppRigidBodyToSkinMatrixTransforms))
		
		f.seek(mppPartModels, 0)
		f.write(struct.pack('<%di' % muPartsCount, *model_indices))
		
		f.seek(mpShatteredGlassParts, 0)
		for shattered_glass in shattered_glasses:
			f.write(struct.pack('<iii', *shattered_glass))
		
		f.seek(mpPartLocators, 0)
		for mTransform in mTransforms:
			f.write(struct.pack('<4f', *mTransform[0]))
			f.write(struct.pack('<4f', *mTransform[1]))
			f.write(struct.pack('<4f', *mTransform[2]))
			f.write(struct.pack('<4f', *mTransform[3]))
		
		f.seek(mpPartVolumeIDs, 0)
		f.write(struct.pack('<%dB' % muPartsCount, *part_volume_ids))
		
		f.seek(mpNumRigidBodiesForPart, 0)
		f.write(struct.pack('<%dB' % muPartsCount, *rigid_bodies_for_part))
		
		f.seek(mppRigidBodyToSkinMatrixTransforms, 0)
		f.write(struct.pack('<%di' % muPartsCount, *transforms_rigid_body_pointers))
		
		f.seek(transforms_rigid_body_pointers[0], 0)
		for transform_rigid_body in transforms_rigid_body:
			f.write(struct.pack('<4f', *transform_rigid_body[0]))
			f.write(struct.pack('<4f', *transform_rigid_body[1]))
			f.write(struct.pack('<4f', *transform_rigid_body[2]))
			f.write(struct.pack('<4f', *transform_rigid_body[3]))
		
		for mModelId, muOffset in zip(mModelIds, muOffsets):
			f.write(id_to_bytes(mModelId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
	
	return 0


def write_model(model_path, model):
	os.makedirs(os.path.dirname(model_path), exist_ok = True)
	
	with open(model_path, "wb") as f:
		renderables_info = model[1][0]
		model_properties = model[1][1]
		
		mu8NumRenderables = model_properties[1]
		
		mppRenderables = 0x14
		mpu8StateRenderableIndices = mppRenderables + 0x4*mu8NumRenderables
		mpfLodDistances = mpu8StateRenderableIndices + 0x1*mu8NumRenderables
		mpfLodDistances += calculate_padding(mpfLodDistances, 0x4)
		miGameExplorerIndex = model_properties[0]
		mu8Flags = model_properties[2]
		mu8NumStates = model_properties[3]
		mu8VersionNumber = 0x2
		
		mppRenderables_ = [0]*mu8NumRenderables
		
		renderable_indices = [x for x in range(mu8NumRenderables)]
		lod_distances = [0.0]*mu8NumRenderables
		mResourceIds = [None]*mu8NumRenderables
		for renderable_info in renderables_info:
			mResourceId = renderable_info[0]
			renderable_index = renderable_info[1][0]
			lod_distance = renderable_info[1][1]
			
			renderable_indices[renderable_index] = renderable_index
			lod_distances[renderable_index] = lod_distance
			mResourceIds[renderable_index] = mResourceId
		
		muOffsets = [mppRenderables + 0x4*x for x in range(mu8NumRenderables)]
		
		# Writing
		f.write(struct.pack('<i', mppRenderables))
		f.write(struct.pack('<i', mpu8StateRenderableIndices))
		f.write(struct.pack('<i', mpfLodDistances))
		f.write(struct.pack('<i', miGameExplorerIndex))
		f.write(struct.pack('<B', mu8NumRenderables))
		f.write(struct.pack('<B', mu8Flags))
		f.write(struct.pack('<B', mu8NumStates))
		f.write(struct.pack('<B', mu8VersionNumber))
		
		f.seek(mppRenderables, 0)
		f.write(struct.pack('<%di' % mu8NumRenderables, *mppRenderables_))
		
		f.seek(mpu8StateRenderableIndices, 0)
		f.write(struct.pack('<%dB' % mu8NumRenderables, *renderable_indices))
		
		f.seek(mpfLodDistances, 0)
		f.write(struct.pack('<%df' % mu8NumRenderables, *lod_distances))
		
		padding = calculate_padding(mpfLodDistances + 0x4*mu8NumRenderables, 0x10)
		f.write(bytearray([0])*padding)
		
		for mResourceId, muOffset in zip(mResourceIds, muOffsets):
			f.write(id_to_bytes(mResourceId))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffset))
			f.write(struct.pack('<i', 0))
	
	return 0


def write_renderable(renderable_path, renderable, resource_type):
	os.makedirs(os.path.dirname(renderable_path), exist_ok = True)
	
	renderable_body_path = renderable_path[:-4] + "_model" + renderable_path[-4:]
	
	with open(renderable_path, "wb") as f, open(renderable_body_path, "wb") as g:
		mRenderableId = renderable[0]
		meshes_info = renderable[1][0]
		renderable_properties = renderable[1][1]
		indices_buffer = renderable[1][2]
		vertices_buffer = renderable[1][3]
		
		object_center = renderable_properties[0]
		object_radius = renderable_properties[1]
		mu16VersionNumber = 0xB
		num_meshes = renderable_properties[2]
		meshes_table_pointer = 0x30
		null0 = 0
		flags = renderable_properties[3]
		padding = 0
		unk1 = meshes_table_pointer + 0x4*num_meshes
		unk2 = unk1 + 0x18
		#padding2
		
		meshes_data_pointer = meshes_table_pointer + 0x4*num_meshes + 0x2C + 0x8
		meshes_data_pointer += calculate_padding(meshes_data_pointer, 0x10)
		
		mesh_header_size = 0x80
		if resource_type == "InstanceList":
			mesh_header_size = 0x70
		meshes_data_pointers = [meshes_data_pointer + mesh_header_size*x for x in range(num_meshes)]     # tem caso que eh 0x70
		
		null1 = 0
		unk3 = 0
		unk4 = 3
		indices_data_offset = 0
		
		indices_data_size = 10000	# Calculating later
		
		unk5 = 2
		null2 = 0
		unk6 = 0
		unk7 = 2
		
		vertex_data_offset = 10000	# Calculating later
		vertex_data_size = 10000	# Calculating later
		#padding3
		
		
		mesh_unk1 = 0x4
		mTransforms = [[] for _ in range(num_meshes)]
		indices_buffer_starts = [0]*num_meshes
		indices_buffer_sizes = [0]*num_meshes
		num_vertices_descriptors = [4]*num_meshes
		mesh_unk2 = 0
		mesh_unk3 = 1
		sub_part_codes = [0]*num_meshes
		mesh_unk4 = unk1
		mesh_unk5 = unk2
		mMaterialIds = [0]*num_meshes
		mVertexDescriptorIds = [[] for _ in range(num_meshes)]
		for mesh_info in meshes_info:
			mesh_index = mesh_info[0]
			mesh_properties = mesh_info[1]
			mTransform = Matrix([[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]).transposed()
			indices_buffer_start, indices_buffer_size, num_vertex_descriptors, sub_part_code = mesh_properties
			mMaterialId = mesh_info[2]
			mVertexDescriptorIds_ = mesh_info[3]
			
			mTransforms[mesh_index] = mTransform[:]
			indices_buffer_starts[mesh_index] = indices_buffer_start
			indices_buffer_sizes[mesh_index] = indices_buffer_size
			num_vertices_descriptors[mesh_index] = num_vertex_descriptors
			sub_part_codes[mesh_index] = sub_part_code
			mMaterialIds[mesh_index] = mMaterialId
			mVertexDescriptorIds[mesh_index] = mVertexDescriptorIds_
        
		indices_data_size = (indices_buffer_starts[-1] + indices_buffer_sizes[-1])*2
		indices_data_size += calculate_padding(indices_data_size, 0x10)
		
		vertex_data_offset = indices_data_size + calculate_padding(indices_data_size, 0x20)
		
		muOffsets_material = [x + 0x50 for x in meshes_data_pointers]
		muOffsets_vertexDescriptior_main = [x + 0x60 for x in meshes_data_pointers]
		
		
		# Writing header
		f.write(struct.pack('<fff', *object_center))
		f.write(struct.pack('<f', object_radius))
		f.write(struct.pack('<H', mu16VersionNumber))
		f.write(struct.pack('<H', num_meshes))
		f.write(struct.pack('<i', meshes_table_pointer))
		f.write(struct.pack('<i', null0))
		f.write(struct.pack('<H', flags))
		f.write(struct.pack('<H', padding))
		f.write(struct.pack('<i', unk1))
		f.write(struct.pack('<i', unk2))
		
		f.seek(meshes_table_pointer, 0)
		f.write(struct.pack('<%di' % num_meshes, *meshes_data_pointers))
		f.write(struct.pack('<i', null1))
		f.write(struct.pack('<i', unk3))
		f.write(struct.pack('<i', unk4))
		f.write(struct.pack('<i', indices_data_offset))
		f.write(struct.pack('<i', indices_data_size))
		f.write(struct.pack('<i', unk5))
		f.write(struct.pack('<i', null2))
		f.write(struct.pack('<i', unk6))
		f.write(struct.pack('<i', unk7))
		f.write(struct.pack('<i', vertex_data_offset))
		f.write(struct.pack('<i', vertex_data_size))
		
		for i in range(0, num_meshes):
			f.seek(meshes_data_pointers[i], 0)
			f.write(struct.pack('<4f', *mTransforms[i][0]))
			f.write(struct.pack('<4f', *mTransforms[i][1]))
			f.write(struct.pack('<4f', *mTransforms[i][2]))
			f.write(struct.pack('<4f', *mTransforms[i][3]))
			
			f.write(struct.pack('<i', mesh_unk1))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', indices_buffer_starts[i]))
			f.write(struct.pack('<i', indices_buffer_sizes[i]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<B', num_vertices_descriptors[i]))
			f.write(struct.pack('<B', mesh_unk2))
			f.write(struct.pack('<B', mesh_unk3))
			f.write(struct.pack('<B', sub_part_codes[i]))
			f.write(struct.pack('<i', mesh_unk4))
			f.write(struct.pack('<i', mesh_unk5))
		
		f.seek(meshes_data_pointers[-1] + mesh_header_size, 0)
		f.seek(0x40, 1)
		
		for i in range(0, num_meshes):
			f.write(id_to_bytes(mMaterialIds[i]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', muOffsets_material[i]))
			f.write(struct.pack('<i', 0))
			
			for j in range(0, num_vertices_descriptors[i]):
				f.write(id_to_bytes(mVertexDescriptorIds[i][j]))
				f.write(struct.pack('<i', 0))
				f.write(struct.pack('<I', muOffsets_vertexDescriptior_main[i] + 0x4*j))
				f.write(struct.pack('<i', 0))
		
		# Writing body
		vertex_data_size = 0
		indices_correction = [0]*num_meshes
		for mesh_index in range(1, num_meshes):
			vertex_size = vertices_buffer[mesh_index][3]
			mesh_indices = vertices_buffer[mesh_index][2]
			vertex_size_previous = vertices_buffer[mesh_index-1][3]
			vertex_count_previous = len(vertices_buffer[mesh_index-1][1])
			
			#vertex_data_size += vertex_size_previous * vertex_count_previous
			#print(vertex_count_previous, indices_correction[mesh_index-1])
			if mesh_index > 1:
				vertex_data_size = vertex_size_previous * indices_correction[mesh_index - 1] + vertex_size_previous * vertex_count_previous
			else:
				vertex_data_size = vertex_size_previous * vertex_count_previous
			#print(vertex_count_previous, indices_correction[mesh_index-1])
			
			index_correction = math.ceil(vertex_data_size / vertex_size)
			#print(index_correction, min(mesh_indices))
			#index_correction = index_correction - min(mesh_indices)
			#indices_correction[mesh_index] = index_correction + 1				#verify: 16*2 / 32 = 1 but it should be 2   ||||||   32*2 /16 = 4 and it's ok
			indices_correction[mesh_index] = index_correction + 0				#verify: 16*2 / 32 = 1 but it should be 2   ||||||   32*2 /16 = 4 and it's ok
			#print(index_correction)
		#print(indices_correction)
		#vertex_data_size += vertices_buffer[-1][3] * len(vertices_buffer[-1][1])
		vertex_data_size = vertices_buffer[-1][3] * (indices_correction[mesh_index] + len(vertices_buffer[-1][1]))
		
		for mesh_index in range(0, num_meshes):
			g.seek(indices_buffer_starts[mesh_index]*2, 0)
			indices_buffer_size = indices_buffer_sizes[mesh_index]
			for j in range(0, indices_buffer_size // 3):
				#g.write(struct.pack('<HHH', *indices_buffer[mesh_index][j]))
				g.write(struct.pack('<H', indices_buffer[mesh_index][j][0] + indices_correction[mesh_index]))
				g.write(struct.pack('<H', indices_buffer[mesh_index][j][1] + indices_correction[mesh_index]))
				g.write(struct.pack('<H', indices_buffer[mesh_index][j][2] + indices_correction[mesh_index]))
			
			padding = calculate_padding(indices_buffer_size*2, 0x10)
			if padding == 0:
				padding = 0x10
			padding_buffer = padding // 2
			
			min_mesh_index = min(min(l) for l in indices_buffer[mesh_index]) + indices_correction[mesh_index]
			g.write(struct.pack("<%sH" % (padding_buffer), *[min_mesh_index]*(padding_buffer)))
		
		g.seek(vertex_data_offset, 0)
		
		for mesh_index in range(0, num_meshes):
			semantic_properties, mesh_vertices_buffer, mesh_indices, vertex_size = vertices_buffer[mesh_index]
			for index in sorted(mesh_indices):
				index_, position, normal, tangent, color, uv1, uv2, uv3, blend_indices, blend_weight = mesh_vertices_buffer[index]
				
				for semantic in semantic_properties:
					g.seek(vertex_data_offset + (index + indices_correction[mesh_index]) * vertex_size, 0)
					
					semantic_type = semantic[0]
					data_type = semantic[1]
					data_offset = semantic[2]
					
					g.seek(data_offset, 1)
					
					if semantic_type == "POSITION":
						values = position
					elif semantic_type == "POSITIONT":
						pass
					elif semantic_type == "NORMAL":
						values = normal
					elif semantic_type == "COLOR":
						values = color
					elif semantic_type == "TEXCOORD1":
						values = [uv1[0], -uv1[1]]
					elif semantic_type == "TEXCOORD2":
						values = [uv2[0], -uv2[1]]
					elif semantic_type == "TEXCOORD3":
						values = [uv3[0], -uv3[1]]
					elif semantic_type == "TEXCOORD4":
						pass
					elif semantic_type == "TEXCOORD5":
						pass
					elif semantic_type == "TEXCOORD6":
						pass
					elif semantic_type == "TEXCOORD7":
						pass
					elif semantic_type == "TEXCOORD8":
						pass
					elif semantic_type == "BLENDINDICES":
						values = blend_indices
					elif semantic_type == "BLENDWEIGHT":
						values = blend_weight
					elif semantic_type == "TANGENT":
						values = tangent
					elif semantic_type == "BINORMAL":
						pass
					elif semantic_type == "COLOR2":
						pass
					elif semantic_type == "PSIZE":
						pass
					
					if data_type[0][-1] == "e":
						g.write(struct.pack("<%s" % data_type[0], *values))
					else:
						g.write(struct.pack("<%s" % data_type[0], *values))
		
		
		f.seek(meshes_table_pointer + 0x4*num_meshes + 0x28, 0)
		f.write(struct.pack('<i', vertex_data_size + calculate_padding(vertex_data_size, 0x10)))
		
		padding = calculate_padding(vertex_data_offset + vertex_data_size, 0x80)
		#if padding == 0:
		#	padding = 0x80
		g.write(bytearray([0])*padding)
	
	return 0


def write_material(material_path, material):
	os.makedirs(os.path.dirname(material_path), exist_ok = True)
	
	with open(material_path, "wb") as f:
		mMaterialId = material[0]
		mShaderId = material[1][0]
		material_states_info = material[1][1]
		texture_states_info = material[1][2]
		material_properties = material[1][3]
		required_raster_types = material[1][4]
		unk_0x4_relative = []
		mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash = material_properties[0]
		mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash = material_properties[1]
		parameters_3, anim_strings_3 = material_properties[2]
		unk_0x6_relative = material_properties[3]
		
		muNumVertexShaderConstantsInstances = len(mauVertexShaderNamesHash)
		muNumPixelShaderConstantsInstances = len(mauPixelShaderNamesHash)
		num_parameters_3 = len(anim_strings_3)
		
		cd_space = 0xC	#was 0x8
		cs_string_size = cd_space - 0x3	#was 0x6
		
		unk_0x0_pointer = 0x24
		num_material_states = len(material_states_info)
		num_texture_states = len(texture_states_info)
		unk_0xA = num_texture_states	#verify
		null_0xB = 0
		unk_0xC_pointer = unk_0x0_pointer + num_material_states*0x20
		null_0x10 = 0
		
		#property_0x4_relative = [0xAD60, 0x9A50, 0x8E76, 0xC70B]
		#for i in range(0, num_material_states):
		#	unk_0x4_relative.append([0xFF00, property_0x4_relative[i]])
		
		unk_0x8_CD_pointer = unk_0xC_pointer + num_texture_states*0x14
		unk_0x8_pointer_relative = [unk_0x8_CD_pointer]*num_material_states
		unk_0x14_pointer_relative = [unk_0x8_CD_pointer]*num_material_states
		padding = 0
		for i in range(num_material_states):
			if i == 0:
				unk_0x8_pointer_relative[i] = unk_0x8_CD_pointer
			else:
				unk_0x8_pointer_relative[i] = unk_0x14_pointer_relative[i-1] + num_texture_states + padding
			unk_0x14_pointer_relative[i] = unk_0x8_pointer_relative[i] + (muNumVertexShaderConstantsInstances + muNumPixelShaderConstantsInstances)*2
			
			_ = unk_0x14_pointer_relative[i] + num_texture_states
			padding = calculate_padding(_, 0x4)
		
		#mpVertexShaderConstants = unk_0xC_pointer + num_texture_states*0x14 + cd_space*num_material_states     # was 0x8*num_material_states- 0x1
		mpVertexShaderConstants = unk_0x14_pointer_relative[-1] + num_texture_states
		unk_0x0_pointer_relative2 = [mpVertexShaderConstants + 0x5*i for i in range(num_texture_states)]		# era 4
		maiChannels = [texture_states_info[i][1] for i in range(num_texture_states)]
		unk_0x10_relative2 = 0xDAD0BEEF
		mpVertexShaderConstants += 0x5*num_texture_states														# era 4
		padding_nones = calculate_padding(mpVertexShaderConstants, 0x4)
		mpVertexShaderConstants += padding_nones
		
		#mpPixelShaderConstants = mpVertexShaderConstants + 0x10 + 0x4*muNumVertexShaderConstantsInstances + 0x4*muNumVertexShaderConstantsInstances
		if muNumVertexShaderConstantsInstances > 0:
			mpauVertexShaderConstantsInstanceSize = mpVertexShaderConstants + 0x10
			mppaVertexShaderConstantsInstanceData = mpauVertexShaderConstantsInstanceSize + 0x4*muNumVertexShaderConstantsInstances
			mpauVertexShaderNamesHash = mppaVertexShaderConstantsInstanceData + 0x4*muNumVertexShaderConstantsInstances
			padding_parameters1 = calculate_padding(mpauVertexShaderNamesHash, 0x10)
			mpauVertexShaderNamesHash += padding_parameters1
			mpafVertexShaderConstantsInstanceData = [mpauVertexShaderNamesHash + 0x10*i for i in range(muNumVertexShaderConstantsInstances)]
			mpauVertexShaderNamesHash += 0x10*muNumVertexShaderConstantsInstances
			mpPixelShaderConstants = mpauVertexShaderNamesHash + 0x4*muNumVertexShaderConstantsInstances
		else:
			mpauVertexShaderConstantsInstanceSize = 0
			mppaVertexShaderConstantsInstanceData = 0
			mpauVertexShaderNamesHash = 0
			mpPixelShaderConstants = mpVertexShaderConstants + 0x4*4
		
		if muNumPixelShaderConstantsInstances > 0:
			mpauPixelShaderConstantsInstanceSize = mpPixelShaderConstants + 0x10
			mppaPixelShaderConstantsInstanceData = mpauPixelShaderConstantsInstanceSize + 0x4*muNumPixelShaderConstantsInstances
			mpauPixelShaderNamesHash = mppaPixelShaderConstantsInstanceData + 0x4*muNumPixelShaderConstantsInstances
			padding_parameters2 = calculate_padding(mpauPixelShaderNamesHash, 0x10)
			mpauPixelShaderNamesHash += padding_parameters2
			mpafPixelShaderConstantsInstanceData = [mpauPixelShaderNamesHash + 0x10*i for i in range(muNumPixelShaderConstantsInstances)]
			mpauPixelShaderNamesHash += 0x10*muNumPixelShaderConstantsInstances
			padding = calculate_padding(mpauPixelShaderNamesHash + 0x4*muNumPixelShaderConstantsInstances, 0x10)
		else:
			mpauPixelShaderConstantsInstanceSize = 0
			mppaPixelShaderConstantsInstanceData = 0
			mpauPixelShaderNamesHash = 0
			padding = calculate_padding(mpPixelShaderConstants + 0x4*4, 0x10)
		
		if num_parameters_3 > 0:
			if muNumPixelShaderConstantsInstances > 0:
				unk_0x1C_pointer = mpauPixelShaderNamesHash + 0x4*muNumPixelShaderConstantsInstances
			else:
				unk_0x1C_pointer = mpPixelShaderConstants + 0x4*4
			
			pointer_to_parameters_pointers_3 = unk_0x1C_pointer + 0x10
			padding_parameters3 = calculate_padding(pointer_to_parameters_pointers_3 + 0x4*num_parameters_3, 0x10)
			pointer_to_parameters_3 = [pointer_to_parameters_pointers_3 + 0x4*num_parameters_3 + padding_parameters3 + 0x10*i for i in range(num_parameters_3)]
			pointer_to_anim_strings_pointers_3 = pointer_to_parameters_3[-1] + 0x10
			string_len = 0
			pointer_to_anim_strings_3 = [0]*num_parameters_3
			for i in range(0, num_parameters_3):
				pointer_to_anim_strings_3[i] = pointer_to_anim_strings_pointers_3 + 0x4*num_parameters_3 + string_len
				string_len += len(anim_strings_3[i]) + 1
			
			padding = calculate_padding(pointer_to_anim_strings_3[-1] + len(anim_strings_3[-1]) + 1, 0x10)
		else:
			unk_0x1C_pointer = 0	#usually null, except with animation
		
		null_0x20 = 0
		
		
		#unk_0x8_CD_pointer = unk_0xC_pointer + num_texture_states*0x14
		#unk_0x8_pointer_relative = [unk_0x8_CD_pointer + cd_space*i for i in range(num_material_states)]
		##unk_0x14_pointer_relative = [unk_0x8_pointer_relative[i] + cs_string_size -0x1 for i in range(num_material_states)]			# not always 0x6
		
		#if num_texture_states != 0:
		#	unk_0x14_pointer_relative = [*unk_0x8_pointer_relative[1:], unk_0x0_pointer_relative2[0]]
		#else:
		#	unk_0x14_pointer_relative = [*unk_0x8_pointer_relative[1:], mpVertexShaderConstants]
		
		
		# Writing header
		f.write(struct.pack('<i', unk_0x0_pointer))
		f.write(id_to_bytes(mMaterialId))
		f.write(struct.pack('<B', num_material_states))
		f.write(struct.pack('<B', num_texture_states))
		f.write(struct.pack('<B', unk_0xA))
		f.write(struct.pack('<B', null_0xB))
		f.write(struct.pack('<i', unk_0xC_pointer))
		f.write(struct.pack('<i', null_0x10))
		f.write(struct.pack('<i', mpVertexShaderConstants))
		f.write(struct.pack('<i', mpPixelShaderConstants))
		f.write(struct.pack('<i', unk_0x1C_pointer))
		f.write(struct.pack('<i', null_0x20))
		
		f.seek(unk_0x0_pointer, 0)
		for i in range(0, num_material_states):	#0x20
			f.write(struct.pack('<i', 0))
			#f.write(struct.pack('<HH', *unk_0x4_relative[i]))
			f.write(struct.pack('<H', 0xFF00))
			f.write(struct.pack('<H', unk_0x6_relative[i]))
			f.write(struct.pack('<i', unk_0x8_pointer_relative[i]))
			f.write(struct.pack('<B', muNumVertexShaderConstantsInstances))
			f.write(struct.pack('<B', muNumPixelShaderConstantsInstances))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<B', 0))
			f.write(struct.pack('<i', num_texture_states))				#Verify
			f.write(struct.pack('<i', unk_0x14_pointer_relative[i]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', 0))
		
		f.seek(unk_0xC_pointer, 0)
		for i in range(0, num_texture_states):	#0x14 | num_texture_states or unk_0xA
			f.write(struct.pack('<i', unk_0x0_pointer_relative2[i]))
			f.write(struct.pack('<i', 0))								#maybe important
			f.write(struct.pack('<H', maiChannels[i]))
			f.write(struct.pack('<H', 0))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', unk_0x10_relative2))				#maybe important
		
		f.seek(unk_0x8_CD_pointer, 0)
		cd = b'\xCD'
		for i in range(0, num_material_states):	#CDs | num_texture_states or unk_0xA
			f.seek(unk_0x8_pointer_relative[i], 0)
			#cd = b'\xCD' * (unk_0x14_pointer_relative[i] - unk_0x8_pointer_relative[i])
			cd = b'\xCD' * ((muNumVertexShaderConstantsInstances + muNumPixelShaderConstantsInstances)*2 + num_texture_states)
			f.write(cd)
		
		for i in range(0, num_texture_states):	#nones
			f.seek(unk_0x0_pointer_relative2[i], 0)
			f.write(b'none\x00')
		
		
		f.seek(mpVertexShaderConstants, 0)
		f.write(struct.pack('<i', muNumVertexShaderConstantsInstances))
		f.write(struct.pack('<i', mpauVertexShaderConstantsInstanceSize))
		f.write(struct.pack('<i', mppaVertexShaderConstantsInstanceData))
		f.write(struct.pack('<i', mpauVertexShaderNamesHash))
		
		if muNumVertexShaderConstantsInstances > 0:
			f.seek(mpauVertexShaderConstantsInstanceSize, 0)
			f.write(struct.pack('<%di' % muNumVertexShaderConstantsInstances, *[1]*muNumVertexShaderConstantsInstances))
			
			f.seek(mppaVertexShaderConstantsInstanceData, 0)
			f.write(struct.pack('<%di' % muNumVertexShaderConstantsInstances, *mpafVertexShaderConstantsInstanceData))
			
			for i in range(0, muNumVertexShaderConstantsInstances):
				f.seek(mpafVertexShaderConstantsInstanceData[i], 0)
				f.write(struct.pack('<ffff', *mafVertexShaderConstantsInstanceData[i]))
			
			f.seek(mpauVertexShaderNamesHash, 0)
			f.write(struct.pack('<%di' % muNumVertexShaderConstantsInstances, *mauVertexShaderNamesHash))
			
		f.seek(mpPixelShaderConstants, 0)
		f.write(struct.pack('<i', muNumPixelShaderConstantsInstances))
		f.write(struct.pack('<i', mpauPixelShaderConstantsInstanceSize))
		f.write(struct.pack('<i', mppaPixelShaderConstantsInstanceData))
		f.write(struct.pack('<i', mpauPixelShaderNamesHash))
		if muNumPixelShaderConstantsInstances > 0:
			f.seek(mpauPixelShaderConstantsInstanceSize, 0)
			f.write(struct.pack('<%di' % muNumPixelShaderConstantsInstances, *[1]*muNumPixelShaderConstantsInstances))
			
			f.seek(mppaPixelShaderConstantsInstanceData, 0)
			f.write(struct.pack('<%di' % muNumPixelShaderConstantsInstances, *mpafPixelShaderConstantsInstanceData))
			
			for i in range(0, muNumPixelShaderConstantsInstances):
				f.seek(mpafPixelShaderConstantsInstanceData[i], 0)
				f.write(struct.pack('<ffff', *mafPixelShaderConstantsInstanceData[i]))
			
			f.seek(mpauPixelShaderNamesHash, 0)
			f.write(struct.pack('<%di' % muNumPixelShaderConstantsInstances, *mauPixelShaderNamesHash))
		
		if num_parameters_3 > 0:
			f.seek(unk_0x1C_pointer, 0)
			f.write(struct.pack('<i', 0))	#null
			f.write(struct.pack('<i', num_parameters_3))
			f.write(struct.pack('<i', pointer_to_parameters_pointers_3))
			f.write(struct.pack('<i', pointer_to_anim_strings_pointers_3))
			f.seek(pointer_to_parameters_pointers_3, 0)
			f.write(struct.pack('<%di' % num_parameters_3, *pointer_to_parameters_3))
			
			for i in range(0, num_parameters_3):
				f.seek(pointer_to_parameters_3[i], 0)
				f.write(struct.pack('<ffff', *parameters_3[i]))
			
			f.seek(pointer_to_anim_strings_pointers_3, 0)
			f.write(struct.pack('<%di' % num_parameters_3, *pointer_to_anim_strings_3))
			
			for i in range(0, num_parameters_3):
				f.seek(pointer_to_anim_strings_3[i], 0)
				string = anim_strings_3[i].encode('utf-8')
				string += b'\x00'
				f.write(string)
		
		
		f.write(bytearray([0])*padding)
		
		# mResourceIds
		f.write(id_to_bytes(mShaderId))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<I', 0x10))
		f.write(struct.pack('<i', 0))
		
		for i in range(0, num_material_states):
			f.write(id_to_bytes(material_states_info[i]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', unk_0x0_pointer + 0x20*i))
			f.write(struct.pack('<i', 0))
		
		# Verify order
		for i in range(0, num_texture_states):
			f.write(id_to_bytes(texture_states_info[i][0]))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<I', unk_0xC_pointer + 0x14*i + 0x10))
			f.write(struct.pack('<i', 0))
			
	return 0


def write_texturestate(texture_state_path, texture_state):
	os.makedirs(os.path.dirname(texture_state_path), exist_ok = True)
	
	with open(texture_state_path, "wb") as f:
		mRasterId = texture_state[1][0]
		texture_state_properties = texture_state[1][1]
		muOffset = 0x38
		
		addressing_mode, filter_types, min_max_lod, max_anisotropy, mipmap_lod_bias, comparison_function, is_border_color_white, unk1 = texture_state_properties
		padding0 = 3
		sampler_state = 0
		texture_resource = 0
		padding1 = 4
		
		f.write(struct.pack('<iii', *addressing_mode))
		f.write(struct.pack('<iii', *filter_types))
		f.write(struct.pack('<ff', *min_max_lod))
		f.write(struct.pack('<I', max_anisotropy))
		f.write(struct.pack('<f', mipmap_lod_bias))
		f.write(struct.pack('<i', comparison_function))
		f.write(struct.pack('<B', is_border_color_white))
		f.write(bytearray([0])*padding0)
		f.write(struct.pack('<i', unk1))
		f.write(struct.pack('<i', sampler_state))
		f.write(struct.pack('<i', texture_resource))
		f.write(bytearray([0])*padding1)
		
		f.write(id_to_bytes(mRasterId))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', muOffset))
		f.write(struct.pack('<i', 0))
	
	return 0


def write_raster(raster_path, raster):
	os.makedirs(os.path.dirname(raster_path), exist_ok = True)
	
	raster_body_path = raster_path[:-4] + "_texture" + raster_path[-4:]
	raster_source_path = raster[3]
	
	with open(raster_source_path, "rb") as f:
		DDS_MAGIC = struct.unpack("<I", f.read(0x4))[0]
		header_size = struct.unpack("<I", f.read(0x4))[0]
		flags = struct.unpack("<I", f.read(0x4))[0]
		height = struct.unpack("<I", f.read(0x4))[0]
		width = struct.unpack("<I", f.read(0x4))[0]
		pitchOrLinearSize = struct.unpack("<I", f.read(0x4))[0]
		depth = struct.unpack("<I", f.read(0x4))[0]
		mipMapCount = struct.unpack("<I", f.read(0x4))[0]
		reserved1 = struct.unpack("<11I", f.read(0x4*11))
		
		# DDS_PIXELFORMAT
		dwSize = struct.unpack("<I", f.read(0x4))[0]
		dwFlags = struct.unpack("<I", f.read(0x4))[0]
		dwFourCC = f.read(0x4).decode()
		dwRGBBitCount = struct.unpack("<I", f.read(0x4))[0]
		dwRBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwGBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwBBitMask = struct.unpack("<I", f.read(0x4))[0]
		dwABitMask = struct.unpack("<I", f.read(0x4))[0]
		
		caps = struct.unpack("<I", f.read(0x4))[0]
		caps2 = struct.unpack("<I", f.read(0x4))[0]
		caps3 = struct.unpack("<I", f.read(0x4))[0]
		caps4 = struct.unpack("<I", f.read(0x4))[0]
		reserved2 = struct.unpack("<I", f.read(0x4))[0]
		
		data = f.read()
	
	if depth == 0:
		depth = 1
	
	with open(raster_path, "wb") as f, open(raster_body_path, "wb") as g:
		mu32VersionNumber = 0x7
		format = get_raster_format(dwFourCC)
		dimension = raster[1][0][0]
		main_mipmap = 0
		mipmap = mipMapCount
		unk_0x34 = raster[1][0][1]
		unk_0x38 = raster[1][0][2]
		padding_texture = calculate_padding(len(data), 0x80)
		
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', mu32VersionNumber))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', format))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<HHH', width, height, depth))
		f.write(struct.pack('<H', dimension))
		f.write(struct.pack('<BB', main_mipmap, mipmap))
		f.write(struct.pack('<H', 0))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<i', unk_0x34))
		f.write(struct.pack('<i', unk_0x38))
		f.write(struct.pack('<i', 0))
		
		g.write(data)
		g.write(bytearray([0])*padding_texture)
	
	return 0


def write_deformationspec(deformationspec_path, WheelSpecs, SensorSpecs, TagPointSpecs, DrivenPoints, GenericTags, CameraTags, LightTags, IKParts, GlassPanes, mCarModelSpaceToHandlingBodySpaceTransform, mHandlingBodyDimensions, mu8SpecID, mNums, mOffsetsAndTensor, miNumberOfJointSpecs):
	os.makedirs(os.path.dirname(deformationspec_path), exist_ok = True)
	
	# with open(deformationspec_path, "rb") as f:
		# wheel_spec_offset = {}
		# f.seek(0x70, 0)
		# TagPointIndex_WheelFR = struct.unpack("<i", f.read(0x4))[0]
		# wheel_spec_offset["FR"] = (0x50, TagPointIndex_WheelFR)
		# f.seek(0xA0, 0)
		# TagPointIndex_WheelFL = struct.unpack("<i", f.read(0x4))[0]
		# wheel_spec_offset["FL"] = (0x80, TagPointIndex_WheelFL)
		# f.seek(0xD0, 0)
		# TagPointIndex_WheelRR = struct.unpack("<i", f.read(0x4))[0]
		# wheel_spec_offset["RR"] = (0xB0, TagPointIndex_WheelRR)
		# f.seek(0x100, 0)
		# TagPointIndex_WheelRL = struct.unpack("<i", f.read(0x4))[0]
		# wheel_spec_offset["RL"] = (0xE0, TagPointIndex_WheelRL)
	
	wheel_spec_offset = {}
	wheel_spec_offset["FR"] = 0x50
	wheel_spec_offset["FL"] = 0x80
	wheel_spec_offset["RR"] = 0xB0
	wheel_spec_offset["RL"] = 0xE0
	
	with open(deformationspec_path, "wb") as f:
		mu8NumVehicleBodies, mu8NumGraphicsParts = mNums
		mCurrentCOMOffset, mMeshOffset, mRigidBodyOffset, mCollisionOffset, mInertiaTensor = mOffsetsAndTensor
		
		miVersionNumber = 1
		mu8NumDeformationSensors = len(SensorSpecs)
		maTagPointData = 0x40 + 0x10 + 0x30*4 + mu8NumDeformationSensors*0x40 + 0xA0
		miNumberOfTagPoints = len(TagPointSpecs)
		maDrivenPointData = maTagPointData + miNumberOfTagPoints*0x50
		miNumberOfDrivenPoints = len(DrivenPoints)
		maIKPartData = maDrivenPointData + miNumberOfDrivenPoints*0x20
		miNumberOfIKParts = len(IKParts)
		maJointSpecsData = maIKPartData + miNumberOfIKParts*0x1E0
		maGlassPaneData = maJointSpecsData + miNumberOfJointSpecs*0x40
		miNumGlassPanes = len(GlassPanes)
		muNumGenericTags = len(GenericTags)
		mpaGenericTagPoints = maGlassPaneData + miNumGlassPanes*0x70
		muNumCameraTags = len(CameraTags)
		mpaCameraTagPoints = mpaGenericTagPoints + muNumGenericTags*0x50
		muNumLightTags = len(LightTags)
		mpaLightTagPoints = mpaCameraTagPoints + muNumCameraTags*0x50
		
		f.write(struct.pack('<i', miVersionNumber))
		f.write(struct.pack('<i', maTagPointData))
		f.write(struct.pack('<i', miNumberOfTagPoints))
		f.write(struct.pack('<i', maDrivenPointData))
		f.write(struct.pack('<i', miNumberOfDrivenPoints))
		f.write(struct.pack('<i', maIKPartData))
		f.write(struct.pack('<i', miNumberOfIKParts))
		f.write(struct.pack('<i', maGlassPaneData))
		f.write(struct.pack('<i', miNumGlassPanes))
		f.write(struct.pack('<I', muNumGenericTags))
		f.write(struct.pack('<i', mpaGenericTagPoints))
		f.write(struct.pack('<I', muNumCameraTags))
		f.write(struct.pack('<i', mpaCameraTagPoints))
		f.write(struct.pack('<I', muNumLightTags))
		f.write(struct.pack('<i', mpaLightTagPoints))
		f.write(bytearray([0])*0x4)
		f.write(struct.pack('<4f', *mHandlingBodyDimensions))
		
		for i, WheelSpec in enumerate(WheelSpecs):
			_, mPosition, mScale, TagPointIndex, WheelSide = WheelSpec
			
			f.seek(wheel_spec_offset[WheelSide], 0)
			f.write(struct.pack('<4f', *mPosition, 0))
			f.write(struct.pack('<4f', *mScale, 0))
			f.write(struct.pack('<i', TagPointIndex))
			#if TagPointIndex != -1 and TagPointIndex < miNumberOfTagPoints:
			#	f.write(struct.pack('<i', TagPointIndex))
			#else:
			#	f.write(struct.pack('<i', wheel_spec_offset[WheelSide][1]))
			f.write(bytearray([0])*0xC)
			
		for sensor in SensorSpecs:
			mu8SceneIndex, mInitialOffset, maDirectionParams, mfRadius, maNextSensor, mu8AbsorbtionLevel, mau8NextBoundarySensor = sensor
			
			f.write(struct.pack('<fff', *mInitialOffset))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<6f', *maDirectionParams))
			f.write(struct.pack('<f', mfRadius))
			f.write(struct.pack('<6B', *maNextSensor))
			f.write(struct.pack('<B', mu8SceneIndex + 1))
			f.write(struct.pack('<B', mu8AbsorbtionLevel))
			f.write(struct.pack('<2B', *mau8NextBoundarySensor))
			f.write(bytearray([0])*0xA)
		
		f.write(struct.pack('<4f', *mCarModelSpaceToHandlingBodySpaceTransform[0]))
		f.write(struct.pack('<4f', *mCarModelSpaceToHandlingBodySpaceTransform[1]))
		f.write(struct.pack('<4f', *mCarModelSpaceToHandlingBodySpaceTransform[2]))
		f.write(struct.pack('<4f', *mCarModelSpaceToHandlingBodySpaceTransform[3]))
		
		f.write(struct.pack('<B', mu8SpecID))
		f.write(struct.pack('<B', mu8NumVehicleBodies))
		f.write(struct.pack('<B', mu8NumDeformationSensors))
		f.write(struct.pack('<B', mu8NumGraphicsParts))
		f.write(bytearray([0])*0xC)
		
		f.write(struct.pack('<4f', *mCurrentCOMOffset))
		f.write(struct.pack('<4f', *mMeshOffset))
		f.write(struct.pack('<4f', *mRigidBodyOffset))
		f.write(struct.pack('<4f', *mCollisionOffset))
		f.write(struct.pack('<4f', *mInertiaTensor))
		
		for tag in TagPointSpecs:
			_, mInitialPosition, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint = tag
			
			mOffsetFromA = Vector(mInitialPosition) - Vector(SensorSpecs[miDeformationSensorA][1])
			mOffsetFromB = Vector(mInitialPosition) - Vector(SensorSpecs[miDeformationSensorB][1])
			
			f.write(struct.pack('<3f', *mOffsetFromA))
			f.write(struct.pack('<f', mfWeightA))
			f.write(struct.pack('<3f', *mOffsetFromB))
			f.write(struct.pack('<f', mfWeightB))
			f.write(struct.pack('<3f', *mInitialPosition))
			f.write(struct.pack('<f', mfDetachThresholdSquared))
			f.write(struct.pack('<f', mfWeightA))
			f.write(struct.pack('<f', mfWeightB))
			f.write(struct.pack('<f', mfDetachThresholdSquared))
			f.write(struct.pack('<h', miDeformationSensorA))
			f.write(struct.pack('<h', miDeformationSensorB))
			f.write(struct.pack('<b', miJointIndex))
			f.write(struct.pack('<B', mbSkinnedPoint))
			f.write(bytearray([0])*0xE)
		
		for driven in DrivenPoints:
			_, mInitialPos, miTagPointIndexA, miTagPointIndexB = driven
			
			mfDistanceFromA = (Vector(mInitialPos) - Vector(TagPointSpecs[miTagPointIndexA][1])).length
			mfDistanceFromB = (Vector(mInitialPos) - Vector(TagPointSpecs[miTagPointIndexB][1])).length
			
			f.write(struct.pack('<3f', *mInitialPos))
			f.write(struct.pack('<i', 0))
			f.write(struct.pack('<f', mfDistanceFromA))
			f.write(struct.pack('<f', mfDistanceFromB))
			f.write(struct.pack('<h', miTagPointIndexA))
			f.write(struct.pack('<h', miTagPointIndexB))
			f.write(bytearray([0])*0x4)
		
		#f.write(IKPart_data)
		#f.seek(maIKPartData, 0)
		mJointSpecsData = []
		mpaJointSpecs = maJointSpecsData
		for IKPart in IKParts:
			object_index, mGraphicsTransform, mBBoxSkinData, mJointSpecs, miPartGraphics, miStartIndexOfDrivenPoints, miNumberOfDrivenPoints, miStartIndexOfTagPoints, miNumberOfTagPoints, mePartType = IKPart
			miNumJoints = len(mJointSpecs)
			mJointSpecsData.extend(mJointSpecs)
			
			f.write(struct.pack('<4f', *mGraphicsTransform[0]))
			f.write(struct.pack('<4f', *mGraphicsTransform[1]))
			f.write(struct.pack('<4f', *mGraphicsTransform[2]))
			f.write(struct.pack('<4f', *mGraphicsTransform[3]))
			
			##mBBoxSkinData
			mOrientation, maCornerSkinData, mCentreSkinData, mJointSkinData = mBBoxSkinData
			
			f.write(struct.pack('<4f', *mOrientation[0]))
			f.write(struct.pack('<4f', *mOrientation[1]))
			f.write(struct.pack('<4f', *mOrientation[2]))
			f.write(struct.pack('<4f', *mOrientation[3]))
			
			#maCornerSkinData
			for mCornerSkinData in maCornerSkinData:
				maCornerSkinData_mVertex, maCornerSkinData_mafWeights, maCornerSkinData_mauBoneIndices = mCornerSkinData
				f.write(struct.pack('<4f', *maCornerSkinData_mVertex))
				f.write(struct.pack('<3f', *maCornerSkinData_mafWeights))
				f.write(struct.pack('<3B', *maCornerSkinData_mauBoneIndices))
				f.write(struct.pack('<B', 0))
			
			#mCentreSkinData
			mCentreSkinData_mVertex, mCentreSkinData_mafWeights, mCentreSkinData_mauBoneIndices = mCentreSkinData
			f.write(struct.pack('<4f', *mCentreSkinData_mVertex))
			f.write(struct.pack('<3f', *mCentreSkinData_mafWeights))
			f.write(struct.pack('<3B', *mCentreSkinData_mauBoneIndices))
			f.write(struct.pack('<B', 0))
			
			#mJointSkinData
			mJointSkinData_mVertex, mJointSkinData_mafWeights, mJointSkinData_mauBoneIndices = mJointSkinData
			f.write(struct.pack('<4f', *mJointSkinData_mVertex))
			f.write(struct.pack('<3f', *mJointSkinData_mafWeights))
			f.write(struct.pack('<3B', *mJointSkinData_mauBoneIndices))
			f.write(struct.pack('<B', 0))
			
			if miNumJoints > 0:
				f.write(struct.pack('<i', mpaJointSpecs))
			else:
				f.write(struct.pack('<i', 0))
			f.write(struct.pack('<i', miNumJoints))
			f.write(struct.pack('<i', miPartGraphics))
			f.write(struct.pack('<i', miStartIndexOfDrivenPoints))
			f.write(struct.pack('<i', miNumberOfDrivenPoints))
			f.write(struct.pack('<i', miStartIndexOfTagPoints))
			f.write(struct.pack('<i', miNumberOfTagPoints))
			f.write(struct.pack('<i', mePartType))
			
			mpaJointSpecs += miNumJoints*0x40
		
		#f.write(DeformationJointSpec_data)
		#f.seek(maJointSpecsData, 0)
		for mJointSpecs in mJointSpecsData:
			jointSpec_index, mJointPosition, mJointAxis, mJointDefaultDirection, mfMaxJointAngle, mfJointDetachThreshold, meJointType = mJointSpecs
			f.write(struct.pack('<4f', *mJointPosition, 0.0))
			f.write(struct.pack('<4f', *mJointAxis))
			f.write(struct.pack('<4f', *mJointDefaultDirection))
			f.write(struct.pack('<f', mfMaxJointAngle))
			f.write(struct.pack('<f', mfJointDetachThreshold))
			f.write(struct.pack('<i', meJointType))
			f.write(struct.pack('<i', 0))
		
		if miNumGlassPanes > 0:
			for GlassPane in GlassPanes:
				_, glasspane_0x00, glasspane_0x10, glasspane_0x50, glasspane_0x58, glasspane_0x5C, glasspane_0x5E, glasspane_0x60, mePartType = GlassPane
				f.write(struct.pack('<4f', *glasspane_0x00))
				f.write(struct.pack('<4f', *glasspane_0x10[0]))
				f.write(struct.pack('<4f', *glasspane_0x10[1]))
				f.write(struct.pack('<4f', *glasspane_0x10[2]))
				f.write(struct.pack('<4f', *glasspane_0x10[3]))
				f.write(struct.pack('<4h', *glasspane_0x50))
				f.write(struct.pack('<4B', *glasspane_0x58))
				f.write(struct.pack('<h', glasspane_0x5C))
				f.write(struct.pack('<h', glasspane_0x5E))
				f.write(struct.pack('<h', glasspane_0x60))
				f.write(bytearray([0])*0x2)
				f.write(struct.pack('<i', mePartType))
				f.write(bytearray([0])*0x8)
		
		for tag in GenericTags:
			_, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			
			f.write(struct.pack('<4f', *mTransform[0]))
			f.write(struct.pack('<4f', *mTransform[1]))
			f.write(struct.pack('<4f', *mTransform[2]))
			f.write(struct.pack('<4f', *mTransform[3]))
			f.write(struct.pack('<i', meTagPointType))
			f.write(struct.pack('<h', miIkPartIndex))
			f.write(struct.pack('<B', mu8SkinPoint))
			f.write(bytearray([0])*0x9)
		
		for tag in CameraTags:
			_, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			
			mTransform[2][2] = -mTransform[2][2]
			
			f.write(struct.pack('<4f', *mTransform[0]))
			f.write(struct.pack('<4f', *mTransform[1]))
			f.write(struct.pack('<4f', *mTransform[2]))
			f.write(struct.pack('<4f', *mTransform[3]))
			f.write(struct.pack('<i', meTagPointType))
			f.write(struct.pack('<h', miIkPartIndex))
			f.write(struct.pack('<B', mu8SkinPoint))
			f.write(bytearray([0])*0x9)
		
		for tag in LightTags:
			_, mTransform, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			
			f.write(struct.pack('<4f', *mTransform[0]))
			f.write(struct.pack('<4f', *mTransform[1]))
			f.write(struct.pack('<4f', *mTransform[2]))
			f.write(struct.pack('<4f', *mTransform[3]))
			f.write(struct.pack('<i', meTagPointType))
			f.write(struct.pack('<h', miIkPartIndex))
			f.write(struct.pack('<B', mu8SkinPoint))
			f.write(bytearray([0])*0x9)
		
	return 0


def write_resources_table(resources_table_path, mResourceIds):
	with open(resources_table_path, "wb") as f:
		macMagicNumber = b'bnd2'
		muVersion = 2
		muPlatform = 1
		muHeaderOffset = 0x30
		muDebugDataOffset = 0xA0
		muResourceEntriesCount = len(mResourceIds)
		muResourceEntriesOffset = 0xA0
		mauResourceDataOffset = [muResourceEntriesCount*0x40 + muResourceEntriesOffset, muResourceEntriesCount*0x40 + muResourceEntriesOffset, muResourceEntriesCount*0x40 + muResourceEntriesOffset]
		muFlags = 0x7
		
		f.write(macMagicNumber)
		f.write(struct.pack('<I', muVersion))
		f.write(struct.pack('<I', muPlatform))
		f.write(struct.pack('<I', muDebugDataOffset))
		f.write(struct.pack('<I', muResourceEntriesCount))
		f.write(struct.pack('<I', muResourceEntriesOffset))
		f.write(struct.pack('<III', *mauResourceDataOffset))
		f.write(struct.pack('<I', muFlags))
		
		f.seek(muHeaderOffset)
		f.write(b'Resources generated by BPR Exporter 2.4 for Blender by DGIorio')
		f.write(b'..................Hash:.6dce831a')
		
		mResourceIds.sort(key=lambda x:x[2])
		f.seek(muResourceEntriesOffset)
		for mResourceId, muResourceType, _ in mResourceIds:
			f.write(id_to_bytes(mResourceId))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			f.write(struct.pack("<I", 0))
			muResourceTypeId = resourcetype_to_type_id(muResourceType)
			f.write(id_to_bytes(muResourceTypeId))
			f.write(struct.pack("<H", 0))
			f.write(struct.pack("<B", 0))
			f.write(struct.pack("<B", 0))
    
	return 0


def edit_materialState(material_state_path, mMaterialStateId, index, shader_type):
	with open(material_state_path, "rb") as f:
		f.seek(0x8C, 0)
		D3D11_CULL_MODE = struct.unpack("<B", f.read(0x1))[0]
		print("shader:", shader_type, D3D11_CULL_MODE, mMaterialStateId, "index:", index)
	return 0


def calculate_tangents(indices_buffer, mesh_vertices_buffer):
	tan1 = {}
	tan2 = {}
	
	for face in indices_buffer:
		i1 = face[0]
		i2 = face[1]
		i3 = face[2]
		
		v1 = mesh_vertices_buffer[i1][1]
		v2 = mesh_vertices_buffer[i2][1]
		v3 = mesh_vertices_buffer[i3][1]
		
		w1 = mesh_vertices_buffer[i1][5]
		w2 = mesh_vertices_buffer[i2][5]
		w3 = mesh_vertices_buffer[i3][5]
		
		x1 = v2[0] - v1[0]
		x2 = v3[0] - v1[0]
		y1 = v2[1] - v1[1]
		y2 = v3[1] - v1[1]
		z1 = v2[2] - v1[2]
		z2 = v3[2] - v1[2]
		
		s1 = w2[0] - w1[0]
		s2 = w3[0] - w1[0]
		t1 = w2[1] - w1[1]
		t2 = w3[1] - w1[1]
		
		try:
			r = 1.0/(s1*t2 - s2*t1)
		except:
			#r = 0.0
			r = 1.0
		
		sdir = [(t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r, (t2 * z1 - t1 * z2) * r]
		tdir = [(s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r, (s1 * z2 - s2 * z1) * r]
		
		try:
			_ = tan1[i1]
			_ = tan2[i1]
		except:
			tan1[i1] = [0.0, 0.0, 0.0]
			tan2[i1] = [0.0, 0.0, 0.0]
		
		try:
			_ = tan1[i2]
			_ = tan2[i2]
		except:
			tan1[i2] = [0.0, 0.0, 0.0]
			tan2[i2] = [0.0, 0.0, 0.0]
		
		try:
			_ = tan1[i3]
			_ = tan2[i3]
		except:
			tan1[i3] = [0.0, 0.0, 0.0]
			tan2[i3] = [0.0, 0.0, 0.0]
		
		
		tan1[i1] = list(map(float.__add__, tan1[i1], sdir))
		tan1[i2] = list(map(float.__add__, tan1[i2], sdir))
		tan1[i3] = list(map(float.__add__, tan1[i3], sdir))
		
		tan2[i1] = list(map(float.__add__, tan2[i1], tdir))
		tan2[i2] = list(map(float.__add__, tan2[i2], tdir))
		tan2[i3] = list(map(float.__add__, tan2[i3], tdir))
	
	import warnings
	with warnings.catch_warnings():
		warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
		for index, vertex in mesh_vertices_buffer.items():
			n = np.asarray(vertex[2])
			t = np.asarray(tan1[index])
			
			#if use_Rotation:
			#	n = np.asarray([n[0], n[2], -n[1]])
			
			# Gram-Schmidt orthogonalize
			tmp = t - n* np.dot(n, t)
			tmp = tmp/np.linalg.norm(tmp)
			
			if np.any(np.isnan(tmp)):
				tmp = [0.0, 0.0, 1.0]
			
			# Calculate handedness
			t_2 = np.asarray(tan2[index])
			signal = -1.0 if (np.dot(np.cross(n, t), t_2) < 0.0) else 1.0
			
			mesh_vertices_buffer[index][3] = tmp[:]
			
			#tangents[a][0] = signal*tmp[0]
			#tangents[a][1] = signal*tmp[1]
			#tangents[a][2] = signal*tmp[2]
			
			#tangents[a][0] =  tmp[0]
			#tangents[a][1] =  tmp[2]
			#tangents[a][2] = -tmp[1]
	
	return 0


def calculate_mpPolySoup(miNumPolySoups, mpaPolySoupBoxesEnd):
	mpPolySoup = mpaPolySoupBoxesEnd + calculate_padding(mpaPolySoupBoxesEnd, 0x80)
	for i in range(0, math.ceil(miNumPolySoups/4)):
		if ((i % 8) % 3 == 0):
			mpPolySoup += 256
		else:
			mpPolySoup += 384
	return int(mpPolySoup)


def get_vertex_semantic(semantic_type):
	semantics = ["", "POSITION", "POSITIONT", "NORMAL", "COLOR",
				 "TEXCOORD1", "TEXCOORD2", "TEXCOORD3", "TEXCOORD4", "TEXCOORD5", "TEXCOORD6", "TEXCOORD7", "TEXCOORD8",
				 "BLENDINDICES", "BLENDWEIGHT", "TANGENT", "BINORMAL", "COLOR2", "PSIZE"]
	
	return semantics[semantic_type]


def get_vertex_data_type(data_type):
	data_types = {2 : ["4f", 0x10],
				  3 : ["4I", 0x10],
				  4 : ["4i", 0x10],
				  6 : ["3f", 0xC],
				  7 : ["3I", 0xC],
				  8 : ["3i", 0xC],
				  10 : ["4e", 0x8], # numpy
				  11 : ["4H", 0x8], #normalized
				  12 : ["4I", 0x10],
				  13 : ["4h", 0x8], #normalized
				  14 : ["4i", 0x10],
				  16 : ["2f", 0x8],
				  17 : ["2I", 0x8],
				  18 : ["2i", 0x8],
				  28 : ["4B", 0x4], #normalized
				  30 : ["4B", 0x4],
				  32 : ["4b", 0x4],
				  34 : ["2e", 0x4],
				  35 : ["2H", 0x4], #normalized
				  36 : ["2H", 0x4],
				  37 : ["2h", 0x4], #normalized
				  38 : ["2h", 0x4],
				  40 : ["1f", 0x4],
				  41 : ["1f", 0x4],
				  42 : ["1I", 0x4],
				  43 : ["1i", 0x4],
				  49 : ["2B", 0x2], #normalized
				  50 : ["2B", 0x2],
				  51 : ["2b", 0x2], #normalized
				  52 : ["2b", 0x2],
				  54 : ["1e", 0x2],
				  57 : ["1H", 0x2],
				  59 : ["1h", 0x2],
				  61 : ["1B", 0x1], #normalized
				  62 : ["1B", 0x1],
				  63 : ["1b", 0x1], #normalized
				  64 : ["1b", 0x1]}
	
	return data_types[data_type]


def get_raster_format(fourcc):
	format_from_fourcc = {	"B8G8R8A8" : 21,
							"R8G8B8A8" : 28,
							"A8R8G8B8" : 255,
							"DXT1" : 71,
							"DXT3" : 73,
							"DXT5" : 77}
	
	return format_from_fourcc[fourcc]


def get_mShaderID(shader_description, resource_type):
	shaders = {	'VideoWall_Diffuse_Opaque_Singlesided': '19_6E_C7_0F',
				'Chevron_Illuminated_Greyscale_Singlesided': '1A_06_FF_0F',
				'Tunnel_DriveableSurface_Detailmap_Opaque_Singlesided': '1B_D8_B8_27',
				'Cruciform_1Bit_Doublesided_Instanced': '1F_DA_DF_6E',
				'Vehicle_Opaque_BodypartsSkin_EnvMapped': '21_6D_2C_08',
				'Vehicle_1Bit_Tyre_Textured': '2D_40_9E_05',
				'Vehicle_Livery_Alpha_CarGuts': '31_8E_3B_9E',
				'Vehicle_Greyscale_Window_Textured': '33_0B_A4_5E',
				'Vehicle_Greyscale_Headlight_Doublesided': '34_11_6F_C8',
				'BuildingGlass_Transparent_Doublesided': '35_91_5B_CA',
				'Diffuse_Greyscale_Singlesided': '36_9A_6B_40',
				'Diffuse_Opaque_Singlesided': '37_C2_9A_C3',
				'Cruciform_1Bit_Doublesided': '37_E7_77_6B',
				'Diffuse_1Bit_Doublesided': '3C_A3_99_3E',
				'Tunnel_Lightmapped_1Bit_Doublesided2': '3D_C9_A3_7B',
				'Gold_Illuminated_Reflective_Opaque_Singlesided': '3F_28_A4_93',
				'Diffuse_Greyscale_Doublesided': '42_73_1A_D2',
				'Sign_Illuminance_Diffuse_Opaque_Singlesided': '46_FB_C2_67',
				'Tint_Specular_1Bit_Doublesided': '49_3C_26_F6',
				'Sign_Diffuse_Opaque_Singlesided': '49_A7_17_A0',
				'Specular_Opaque_Singlesided': '4B_D9_70_EA',
				'Grass_Specular_Opaque_Singlesided': '4D_7F_80_14',
				'Tint_Building_Opaque_Singlesided': '4E_83_F2_D0',
				'Vehicle_GreyScale_Decal_Textured_UVAnim': '51_80_C9_2F',
				'Vehicle_Livery_Alpha_CarGuts_Skin': '56_60_98_39',
				'Building_Opaque_Singlesided': '57_0B_99_65',
				'Vehicle_Opaque_Decal_Textured_EnvMapped_PoliceLights': '5D_1F_A9_50',
				'Tunnel_Road_Detailmap_Opaque_Singlesided': '5D_C3_BE_4F',
				'Tunnel_Lightmapped_1Bit_Singlesided2': '65_25_EA_21',
				'Vehicle_Opaque_CarbonFibre_Textured': '66_30_78_11',
				'ShoreLine_Diffuse_Greyscale_Singlesided': '66_63_5A_26',
				'Specular_Greyscale_Singlesided': '6B_A8_27_CA',
				'Vehicle_Opaque_Metal_Textured_Skin': '6F_53_CC_FA',
				'Terrain_Diffuse_Opaque_Singlesided': '71_12_EC_98',
				'Water_Specular_Opaque_Singlesided': '73_B0_DA_EC',
				'Vehicle_Opaque_PlasticMatt_Textured': '78_CE_40_2C',
				'Vehicle_Opaque_WheelChrome_Textured_Illuminance': '79_7D_2F_76',
				'Road_Detailmap_Opaque_Singlesided': '7B_7B_A2_8E',
				'Illuminance_Diffuse_1Bit_Doublesided': '7C_C6_D3_1D',
				'MetalSheen_Opaque_Doublesided': '7F_B8_3B_1A',
				'Vehicle_Opaque_PaintGloss_Textured_NormalMapped': '82_DE_22_8E',
				'FlashingNeon_Diffuse_1Bit_Doublesided': '86_6F_8D_FC',
				'Building_Night_Opaque_Singlesided': '89_41_8E_7B',
				'Foliage_1Bit_Doublesided': '8A_88_2A_56',
				'Vehicle_Opaque_PaintGloss_Textured': '8A_A0_FC_56',
				'Vehicle_Opaque_PlasticMatt': '8B_4D_5D_01',
				'Cable_GreyScale_Doublesided': '93_5F_33_58',
				'Diffuse_Opaque_Doublesided': '94_B4_DB_B5',
				'Tunnel_Lightmapped_Opaque_Singlesided2': '95_66_1E_23',
				'Vehicle_GreyScale_WheelChrome_Textured_Illuminance': '98_98_75_56',
				'Road_Night_Detailmap_Opaque_Singlesided': '9E_FB_32_8E',
				'Diffuse_1Bit_Singlesided': '9F_D5_D8_48',
				'Vehicle_1Bit_MetalFaded_Textured_EnvMapped': 'A2_14_84_00',
				'Specular_DetailMap_Opaque_Singlesided': 'A2_62_24_FC',
				'Tunnel_Lightmapped_Reflective_Opaque_Singlesided2': 'A6_28_0B_CF',
				'Tint_Specular_Opaque_Singlesided': 'AD_08_F1_AA',
				'Vehicle_Opaque_Chrome_Damaged': 'AD_23_5C_6B',
				'Specular_1Bit_Doublesided': 'AD_57_BF_E3',
				'Specular_Opaque_Doublesided': 'AE_B3_92_62',
				'Illuminance_Diffuse_Opaque_Singlesided': 'B0_1D_35_C6',
				'Terrain_Specular_Opaque_Singlesided': 'B1_2C_80_67',
				'DriveableSurface_Night_Detailmap_Opaque_Singlesided': 'B4_56_99_82',
				'Vehicle_Opaque_Metal_Textured': 'B4_A6_ED_D7',
				'Sign_Lightmap_Diffuse_Opaque_Singlesided': 'B6_7A_FA_60',
				'Glass_Specular_Transparent_Doublesided': 'B8_A1_8A_50',
				'Specular_1Bit_Singlesided': 'B8_A5_9E_01',
				'Lightmap_Diffuse_Opaque_Singlesided': 'B9_E2_4F_D0',
				'Sign_Specular_Opaque_Singlesided': 'BA_1F_F8_AC',
				'DriveableSurface_DetailMap_Diffuse_Opaque_Singlesided': 'BA_2E_9B_81',
				'DriveableSurface_Detailmap_Opaque_Singlesided': 'BD_2E_A8_C4',
				'FlashingNeon_Diffuse_Opaque_Singlesided': 'C0_04_1A_37',
				'Vehicle_GreyScale_WheelChrome_Textured_Damaged': 'C4_E3_58_7A',
				'Vehicle_GreyScale_Light_Textured_EnvMapped': 'C4_E4_B3_99',
				'Sign_Diffuse_1Bit_Singlesided': 'C5_1D_C5_57',
				'Specular_Greyscale_Doublesided': 'C7_1B_BF_08',
				'Illuminance_Diffuse_1Bit_Singlesided': 'D0_75_4B_DF',
				'Vehicle_Opaque_SimpleMetal_Textured': 'D2_CE_2F_51',
				'Tunnel_Lightmapped_Opaque_Doublesided2': 'D2_FB_F8_AB',
				'Tunnel_Lightmapped_Road_Detailmap_Opaque_Singlesided2': 'D4_90_D6_B8',
				'Vehicle_Opaque_NormalMap_SpecMap_Skin': 'D9_7E_0C_84',
				'Vehicle_Opaque_PaintGloss_Textured_Traffic': 'DB_62_6A_AE',
				'Vehicle_Opaque_Decal_Textured_EnvMapped': 'E1_C4_7C_19',
				'Vehicle_GreyScale_Decal_Textured': 'EA_27_69_B4',
				'CarStudio_DoNotShipWithThisInTheGame': 'EB_BF_C4_9D',
				'Tunnel_Diffuse_Opaque_Doublesided': 'F7_30_97_BD',
				'Tunnel_Diffuse_Opaque_Singlesided': 'FF_3B_D3_06'}
	
	try:
		mShaderId = shaders[shader_description]
	except:
		mShaderId = ""
		try:
			from difflib import get_close_matches
			shader_description_ = shader_description
			close_shaders = get_close_matches(shader_description, shaders.keys())
			for i in range(0, len(close_shaders)):
				if resource_type == "InstanceList":
					if not close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
				else:
					if close_shaders[i].startswith("Vehicle"):
						shader_description = close_shaders[i]
						mShaderId = shaders[shader_description]
						print("WARNING: getting similar shader type for shader %s: %s" % (shader_description_, shader_description))
						break
		except:
			mShaderId = ""
	if shader_description == "Godray_Additive_Doublesided_Default":
		shader_description = "Diffuse_1Bit_Doublesided"
		mShaderId = shaders[shader_description]
		#mShaderId = '57_0B_99_65'
	#mShaderId = '57_0B_99_65'
	return (mShaderId, shader_description)


def get_tag_point_code(TagPointType):
	TagPointTypes = {'E_TAGPOINT_PHYSICS_CENTREOFMASS': 0x0,
				'E_TAGPOINT_LIGHTS_FRONTRUNNINGLEFT': 0x1,
				'E_TAGPOINT_LIGHTS_FRONTRUNNINGRIGHT': 0x2,
				'E_TAGPOINT_LIGHTS_REARRUNNINGLEFT': 0x3,
				'E_TAGPOINT_LIGHTS_REARRUNNINGRIGHT': 0x4,
				'E_TAGPOINT_LIGHTS_FRONTSPOTLEFT': 0x5,
				'E_TAGPOINT_LIGHTS_FRONTSPOTRIGHT': 0x6,
				'E_TAGPOINT_LIGHTS_INDICATORFRONTLEFT': 0x7,
				'E_TAGPOINT_LIGHTS_INDICATORFRONTRIGHT': 0x8,
				'E_TAGPOINT_LIGHTS_INDICATORREARLEFT': 0x9,
				'E_TAGPOINT_LIGHTS_INDICATORREARRIGHT': 0xA,
				'E_TAGPOINT_LIGHTS_BRAKELEFT': 0xB,
				'E_TAGPOINT_LIGHTS_BRAKERIGHT': 0xC,
				'E_TAGPOINT_LIGHTS_BRAKECENTRE': 0xD,
				'E_TAGPOINT_LIGHTS_REVERSELEFT': 0xE,
				'E_TAGPOINT_LIGHTS_REVERSERIGHT': 0xF,
				'E_TAGPOINT_LIGHTS_SPOTLIGHT1': 0x10,
				'E_TAGPOINT_LIGHTS_SPOTLIGHT2': 0x11,
				'E_TAGPOINT_LIGHTS_BLUESTWOS1': 0x12,
				'E_TAGPOINT_LIGHTS_BLUESTWOS2': 0x13,
				'E_TAGPOINT_TYREWELL_FRONTLEFT': 0x14,
				'E_TAGPOINT_TYREWELL_FRONTRIGHT': 0x15,
				'E_TAGPOINT_TYREWELL_REARLEFT': 0x16,
				'E_TAGPOINT_TYREWELL_REARRIGHT': 0x17,
				'E_TAGPOINT_TYREWELL_ADDITIONALLEFT': 0x18,
				'E_TAGPOINT_TYREWELL_ADDITIONALRIGHT': 0x19,
				'E_TAGPOINT_AXLEPOINT_FRONT': 0x1A,
				'E_TAGPOINT_AXLEPOINT_REAR': 0x1B,
				'E_TAGPOINT_ARTICULATIONPOINT_FRONT': 0x1C,
				'E_TAGPOINT_ARTICULATIONPOINT_REAR': 0x1D,
				'E_TAGPOINT_ATTACHPOINT': 0x1E,
				'E_TAGPOINT_FXGLASSSMASHPOINT1': 0x1F,
				'E_TAGPOINT_FXGLASSSMASHPOINT2': 0x20,
				'E_TAGPOINT_FXGLASSSMASHPOINT3': 0x21,
				'E_TAGPOINT_FXGLASSSMASHPOINT4': 0x22,
				'E_TAGPOINT_FXGLASSSMASHPOINT5': 0x23,
				'E_TAGPOINT_FXGLASSSMASHPOINT6': 0x24,
				'E_TAGPOINT_FXGLASSSMASHPOINT7': 0x25,
				'E_TAGPOINT_FXGLASSSMASHPOINT8': 0x26,
				'E_TAGPOINT_FXGLASSSMASHPOINT9': 0x27,
				'E_TAGPOINT_FXGLASSSMASHPOINT10': 0x28,
				'E_TAGPOINT_FXBOOSTPOINT1': 0x29,
				'E_TAGPOINT_FXBOOSTPOINT2': 0x2A,
				'E_TAGPOINT_FXBOOSTPOINT3': 0x2B,
				'E_TAGPOINT_FXBOOSTPOINT4': 0x2C,
				'E_TAGPOINT_FXFIREPOINT': 0x2D,
				'E_TAGPOINT_FXSTEAMPOINT': 0x2E,
				'E_TAGPOINT_FXPOV_FRONTLEFT': 0x2F,
				'E_TAGPOINT_FXPOV_FRONTRIGHT': 0x30,
				'E_TAGPOINT_FXPOV_REARLEFT': 0x31,
				'E_TAGPOINT_FXPOV_REARRIGHT': 0x32,
				'E_TAGPOINT_FXDASHBOARD': 0x33,
				'E_TAGPOINT_FXENGINE': 0x34,
				'E_TAGPOINT_FXTRUNK': 0x35,
				'E_TAGPOINT_FXPETROL_TANK': 0x36,
				'E_TAGPOINT_FXPELVIS_FRONTLEFT': 0x37,
				'E_TAGPOINT_PAYLOAD': 0x38,
				'E_TAGPOINT_COUNT': 0x39}
	
	if TagPointType in TagPointTypes:
		return TagPointTypes[TagPointType]
	
	return TagPointType


def get_part_type_code(PartType):
	PartTypes = {'eBody_Roof_PLAYERONLY': 0x0,
				 'eBody_BumperFront': 0x1,
				 'eBody_BumperRear': 0x2,
				 'eBody_Bonnet': 0x3,
				 'eBody_Boot': 0x4,
				 'eBody_Spoiler': 0x5,
				 'eBody_GrillFront': 0x6,
				 'eBody_GrillRear': 0x7,
				 'eBody_DoorLeft': 0x8,
				 'eBody_DoorLeftMirror': 0x9,
				 'eBody_DoorRight': 0xA,
				 'eBody_DoorRightMirror': 0xB,
				 'eBody_DoorRearLeft': 0xC,
				 'eBody_DoorRearRight': 0xD,
				 'eBody_DoorBackLeft': 0xE,
				 'eBody_DoorBackRight': 0xF,
				 'eBody_GlassDoorFrontLeft': 0x10,
				 'eBody_GlassDoorFrontRight': 0x11,
				 'eBody_GlassDoorRearLeft': 0x12,
				 'eBody_GlassDoorRearRight': 0x13,
				 'eBody_GlassWindscreenFront': 0x14,
				 'eBody_GlassWindscreenRear': 0x15,
				 'eBody_GlassPanelLeft_bus': 0x16,
				 'eBody_GlassPanelRight_bus': 0x17,
				 'eBody_SkirtLeft': 0x18,
				 'eBody_SkirtRight': 0x19,
				 'eBody_WingFrontLeft': 0x1A,
				 'eBody_WingFrontRight': 0x1B,
				 'eBody_WingRearRight': 0x1C,
				 'eBody_WingRearLeft': 0x1D,
				 'eBody_Wiper1': 0x1E,
				 'eBody_Wiper2': 0x1F,
				 'eBody_Wiper3': 0x20,
				 'eBody_MudFlapFrontLeft': 0x21,
				 'eBody_MudFlapFrontRight': 0x22,
				 'eBody_MudFlapRearLeft': 0x23,
				 'eBody_MudFlapRearRight': 0x24,
				 'eBody_Aerial': 0x25,
				 'eBody_NumberPlateRear': 0x26,
				 'eBody_NumberPlateFront': 0x27,
				 'eLights_FrontLeft': 0x28,
				 'eLights_FrontRight': 0x29,
				 'eLights_RearLeft': 0x2A,
				 'eLights_RearRight': 0x2B,
				 'eLights_SpecialSiren': 0x2C,
				 'eChassis_FrontEnd': 0x2D,
				 'eChassis_PassengerCell': 0x2E,
				 'eChassis_RearEnd': 0x2F,
				 'eChassis_ArmFrontRight': 0x30,
				 'eChassis_ArmFrontLeft': 0x31,
				 'eChassis_ArmRearRight': 0x32,
				 'eChassis_ArmRearLeft': 0x33,
				 'eChassis_ArmAdditionalR_Truck': 0x34,
				 'eChassis_ArmAdditionalL_Truck': 0x35,
				 'eChassis_WheelArchFrontLeft': 0x36,
				 'eChassis_WheelArchFrontRight': 0x37,
				 'eChassis_WheelArchRearLeft': 0x38,
				 'eChassis_WheelArchRearRight': 0x39,
				 'eChassis_DiscFrontLeft': 0x3A,
				 'eChassis_DiscFrontRight': 0x3B,
				 'eChassis_DiscRearLeft': 0x3C,
				 'eChassis_DiscRearRight': 0x3D,
				 'eChassis_DiscAdditionalRight_Truck': 0x3E,
				 'eChassis_DiscAdditionalLeft_Truck': 0x3F,
				 'eChassis_DiscCaliperFrontLeft': 0x40,
				 'eChassis_DiscCaliperFrontRight': 0x41,
				 'eChassis_DiscCaliperRearLeft': 0x42,
				 'eChassis_DiscCaliperRearRight': 0x43,
				 'eAncillaries_Block': 0x44,
				 'eAncillaries_Intercooler': 0x45,
				 'eAncillaries_Radiator': 0x46,
				 'eAncillaries_Battery': 0x47,
				 'eAncillaries_Fan': 0x48,
				 'eAncillaries_AirFilter': 0x49,
				 'eAncillaries_Distributor': 0x4A,
				 'eAncillaries_InletManifold': 0x4B,
				 'eAncillaries_BrakeServo': 0x4C,
				 'eAncillaries_PlasticBox1': 0x4D,
				 'eAncillaries_PlasticBox2': 0x4E,
				 'eAncillaries_PlasticBox3': 0x4F,
				 'eAncillaries_FluidResevoir1': 0x50,
				 'eAncillaries_FluidResevoir2': 0x51,
				 'eAncillaries_Pipe1': 0x52,
				 'eAncillaries_Pipe2': 0x53,
				 'eAncillaries_ExhaustSystem1': 0x54,
				 'eAncillaries_ExhaustSystem2': 0x55,
				 'eAncillaries_PetrolTank_Truck': 0x56,
				 'eWheels_FrontLeft': 0x57,
				 'eWheels_FrontRight': 0x58,
				 'eWheels_RearLeft': 0x59,
				 'eWheels_RearRight': 0x5A,
				 'eWHEEL': 0x5B,
				 'eDISC': 0x5C,
				 'eCALIPER': 0x5D,
				 'eWheels_AdditionalRight_Truck': 0x5E,
				 'eWheels_AdditionalLeft_Truck': 0x5F,
				 'eInterior_SeatFrontLeft': 0x60,
				 'eInterior_SeatFrontRight': 0x61,
				 'eInterior_SeatRearLeft': 0x62,
				 'eInterior_SeatRearRight': 0x63,
				 'eInterior_SeatRearBench': 0x64,
				 'eInterior_SeatAdditional_bus': 0x65,
				 'eInterior_SteeringWheel': 0x66,
				 'eInterior_InteriorMirror': 0x67,
				 'eInterior_SunVisorLeft': 0x68,
				 'eInterior_SunVisorRight': 0x69,
				 'eInterior_Extinguisher': 0x6A,
				 'eVariation_RoofRacks': 0x6B,
				 'eVariation_BumperFrontAttachment1': 0x6C,
				 'eVariation_BumperFrontAttachment2': 0x6D,
				 'eVariation_BumperFrontAttachment3': 0x6E,
				 'eVariation_BumperFrontAttachment4': 0x6F,
				 'eVariation_BumperRearAttachment1': 0x70,
				 'eVariation_BumperRearAttachment2': 0x71,
				 'eVariation_BumperRearAttachment3': 0x72,
				 'eVariation_BumperRearAttachment4': 0x73,
				 'eVariation_Luggage1': 0x74,
				 'eVariation_Luggage2': 0x75,
				 'eVariation_SpareWheel': 0x76,
				 'eVariation_Aerial': 0x77,
				 'eVariation_Ladder': 0x78,
				 'eVariation_Spotlights1': 0x79,
				 'eVariation_SpotLights2': 0x7A,
				 'eVariation_AttachmentLeftSide1': 0x7B,
				 'eVariation_AttachmentLeftSide2': 0x7C,
				 'eVariation_AttachmentRightSide1': 0x7D,
				 'eVariation_AttachmentRightSide2': 0x7E,
				 'eVariation_Crane': 0x7F,
				 'eVariation_Mixer': 0x80,
				 'eVariation_Tipper': 0x81,
				 'eVariation_Additional1': 0x82,
				 'eVariation_Additional2': 0x83,
				 'eWHEEL_BLURRED': 0x84,
				 'eBodyPartCount': 0x85}
	
	if PartType in PartTypes:
		return PartTypes[PartType]
	
	return PartType


def get_joint_type_code(JointType):
	JointTypes = {'eNone': 0x0,
				 'eHinge': 0x1,
				 'eBallAndSocket': 0x2,
				 'eJointTypeCount': 0x3}
	
	if JointType in JointTypes:
		return JointTypes[JointType]
	
	return JointType


def resourcetype_to_type_id(resource_type):
	resources_types = {'Raster' : '00_00_00_00',
					   'Material' : '01_00_00_00',
					   'RenderableMesh' : '02_00_00_00',
					   'TextFile' : '03_00_00_00',
					   'DrawIndexParams' : '04_00_00_00',
					   'IndexBuffer' : '05_00_00_00',
					   'MeshState' : '06_00_00_00',
					   'VertexBuffer' : '09_00_00_00',
					   'VertexDesc' : '0A_00_00_00',
					   'RwMaterialCRC32' : '0B_00_00_00',
					   'Renderable' : '0C_00_00_00',
					   'MaterialTechnique' : '0D_00_00_00',
					   'TextureState' : '0E_00_00_00',
					   'MaterialState' : '0F_00_00_00',
					   'DepthStencilState' : '10_00_00_00',
					   'RasterizerState' : '11_00_00_00',
					   'ShaderProgramBuffer' : '12_00_00_00',
					   'ShaderParameter' : '14_00_00_00',
					   'RenderableAssembly' : '15_00_00_00',
					   'Debug' : '16_00_00_00',
					   'KdTree' : '17_00_00_00',
					   'VoiceHierarchy' : '18_00_00_00',
					   'Snr' : '19_00_00_00',
					   'InterpreterData' : '1A_00_00_00',
					   'AttribSysSchema' : '1B_00_00_00',
					   'AttribSysVault' : '1C_00_00_00',
					   'EntryList' : '1D_00_00_00',
					   'AptDataHeaderType' : '1E_00_00_00',
					   'GuiPopup' : '1F_00_00_00',
					   'Font' : '21_00_00_00',
					   'LuaCode' : '22_00_00_00',
					   'InstanceList' : '23_00_00_00',
					   'CollisionMeshData' : '24_00_00_00',
					   'IdList' : '25_00_00_00',
					   'InstanceCollisionList' : '26_00_00_00',
					   'Language' : '27_00_00_00',
					   'SatNavTile' : '28_00_00_00',
					   'SatNavTileDirectory' : '29_00_00_00',
					   'Model' : '2A_00_00_00',
					   'ColourCube' : '2B_00_00_00',
					   'HudMessage' : '2C_00_00_00',
					   'HudMessageList' : '2D_00_00_00',
					   'HudMessageSequence' : '2E_00_00_00',
					   'HudMessageSequenceDictionary' : '2F_00_00_00',
					   'WorldPainter2D' : '30_00_00_00',
					   'PFXHookBundle' : '31_00_00_00',
					   'Shader' : '32_00_00_00',
					   'RawFile' : '40_00_00_00',
					   'ICETakeDictionary' : '41_00_00_00',
					   'VideoData' : '42_00_00_00',
					   'PolygonSoupList' : '43_00_00_00',
					   'CommsToolListDefinition' : '45_00_00_00',
					   'CommsToolList' : '46_00_00_00',
					   'BinaryFile' : '50_00_00_00',
					   'AnimationCollection' : '51_00_00_00',
					   'CharAnimBankFile' : '27_10_00_00',
					   'WeaponFile' : '27_11_00_00',
					   'VFXFile' : '3E_34_00_00',
					   'BearFile' : '3F_34_00_00',
					   'BkPropInstanceList' : '98_3A_00_00',
					   'Registry' : '00_A0_00_00',
					   'GenericRwacWaveContent' : '20_A0_00_00',
					   'GinsuWaveContent' : '21_A0_00_00',
					   'AemsBank' : '22_A0_00_00',
					   'Csis' : '23_A0_00_00',
					   'Nicotine' : '24_A0_00_00',
					   'Splicer' : '25_A0_00_00',
					   'FreqContent' : '26_A0_00_00',
					   'VoiceHierarchyCollection' : '27_A0_00_00',
					   'GenericRwacReverbIRContent' : '28_A0_00_00',
					   'SnapshotData' : '29_A0_00_00',
					   'ZoneList' : '00_B0_00_00',
					   'LoopModel' : '00_00_01_00',
					   'AISections' : '01_00_01_00',
					   'TrafficData' : '02_00_01_00',
					   'Trigger' : '03_00_01_00',
					   'DeformationModel' : '04_00_01_00',
					   'VehicleList' : '05_00_01_00',
					   'GraphicsSpec' : '06_00_01_00',
					   'PhysicsSpec' : '07_00_01_00',
					   'ParticleDescriptionCollection' : '08_00_01_00',
					   'WheelList' : '09_00_01_00',
					   'WheelGraphicsSpec' : '0A_00_01_00',
					   'TextureNameMap' : '0B_00_01_00',
					   'ICEList' : '0C_00_01_00',
					   'ICEData' : '0D_00_01_00',
					   'Progression' : '0E_00_01_00',
					   'PropPhysics' : '0F_00_01_00',
					   'PropGraphicsList' : '10_00_01_00',
					   'PropInstanceData' : '11_00_01_00',
					   'EnvironmentKeyframe' : '12_00_01_00',
					   'EnvironmentTimeLine' : '13_00_01_00',
					   'EnvironmentDictionary' : '14_00_01_00',
					   'GraphicsStub' : '15_00_01_00',
					   'StaticSoundMap' : '16_00_01_00',
					   'StreetData' : '18_00_01_00',
					   'VFXMeshCollection' : '19_00_01_00',
					   'MassiveLookupTable' : '1A_00_01_00',
					   'VFXPropCollection' : '1B_00_01_00',
					   'StreamedDeformationSpec' : '1C_00_01_00',
					   'ParticleDescription' : '1D_00_01_00',
					   'PlayerCarColours' : '1E_00_01_00',
					   'ChallengeList' : '1F_00_01_00',
					   'FlaptFile' : '20_00_01_00',
					   'ProfileUpgrade' : '21_00_01_00',
					   'VehicleAnimation' : '23_00_01_00',
					   'BodypartRemapping' : '24_00_01_00',
					   'LUAList' : '25_00_01_00',
					   'LUAScript' : '26_00_01_00',
					   'BkSoundWeapon' : '00_10_01_00',
					   'BkSoundGunsu' : '01_10_01_00',
					   'BkSoundBulletImpact' : '02_10_01_00',
					   'BkSoundBulletImpactList' : '03_10_01_00',
					   'BkSoundBulletImpactStream' : '04_10_01_00'}
	
	return resources_types[resource_type]


def calculate_resourceid(resource_name):
	ID = hex(zlib.crc32(resource_name.lower().encode()) & 0xffffffff)
	ID = ID[2:].upper().zfill(8)
	ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)])
	return ID


def is_valid_id(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	if len(id) != 8:
		print("ERROR: ResourceId not in the proper format: %s. The format should be like AA_BB_CC_DD." % id_old)
		return False
	try:
		int(id, 16)
	except ValueERROR:
		print("ERROR: ResourceId is not a valid hexadecimal string: %s" % id_old)
		return False
	
	return True


def id_to_bytes(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	if len(id) != 8:
		print("ERROR: ResourceId not in the proper format: %s" % id_old)
	try:
		int(id, 16)
	except ValueERROR:
		print("ERROR: ResourceId is not a valid hexadecimal string: %s" % id_old)
	return bytearray.fromhex(id)


def id_to_int(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = ''.join(id[::-1][x:x+2][::-1] for x in range(0, len(id), 2))
	return int(id, 16)


def id_swap(id):
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = '_'.join([id[::-1][x:x+2][::-1] for x in range(0, len(id), 2)])
	return id

def calculate_padding(length, alignment):
	division1 = (length/alignment)
	division2 = math.ceil(length/alignment)
	padding = int((division2 - division1)*alignment)
	return padding


def BurnoutLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\BurnoutParadise'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None


def nvidiaGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\nvidia-texture-tools-2.1.1-win64\\bin64\\nvcompress.exe'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return npath
	return None


class ExportBPR(Operator, ExportHelper):
	"""Export as a Burnout Paradise Remastered Model file"""
	bl_idname = "export_bpr.data"
	bl_label = "Export to folder"

	filename_ext = ""
	use_filter_folder = True

	filter_glob: StringProperty(
			options={'HIDDEN'},
			default="*.dat",
			maxlen=255,
			)
	
	pack_bundle_file: BoolProperty(
			name="Pack bundle",
			description="Check in order to pack the exported files in a bundle",
			default=True,
			)
	
	if bpy.context.preferences.view.show_developer_ui == True:
		debug_shared_not_found: BoolProperty(
			name="Resolve is_shared_asset not found",
			description="Check in order to allow setting is_shared_asset as False if an asset is not found in the default library",
			default=False,
			)
		
		debug_search_for_swapped_ids: BoolProperty(
			name="Search for swapped resource IDs",
			description="Check in order to also search shared assets using swapped resource id",
			default=True,
			)
		
		debug_use_shader_material_parameters: BoolProperty(
			name="Use default shader parameters",
			description="Check in order to apply the default shader parameters on materials",
			default=False,
			)
		
		debug_use_default_vertexdescriptor: BoolProperty(
			name="Use default vertexDescriptors",
			description="Check in order to use the default vertexDescriptors on all instances",
			default=False,
			)
		
		debug_use_default_materialstate: BoolProperty(
			name="Use default materialStates",
			description="Check in order to use the default materialStates on all materials",
			default=False,
			)
		
		debug_add_missing_textures: BoolProperty(
			name="Add missing textures",
			description="Check in order to add to add missing textures to a material. Only for shader Road_Detailmap_Opaque_Singlesided, since the console version does not require some textures",
			default=False,
			)
	else:
		debug_shared_not_found = False
		debug_search_for_swapped_ids = True
		debug_use_shader_material_parameters = False
		debug_use_default_vertexdescriptor = False
		debug_use_default_materialstate = False
		debug_add_missing_textures = False
	
	def execute(self, context):
		userpath = self.properties.filepath
		if os.path.isfile(userpath):
			self.report({"ERROR"}, "Please select a directory not a file\n" + userpath)
			return {"CANCELLED"}
		if BurnoutLibraryGet() == None:
			self.report({"ERROR"}, "Game library not found, please check if you installed it correctly.")
			return {"CANCELLED"}
		#if nvidiaGet() == None:
		#	self.report({"ERROR"}, "Nvidia texture tools v2.1.1 not found, please check if you installed it correctly.")
		#	return {"CANCELLED"}
		#return main(context, self.filepath)
		
		status = main(context, self.filepath, self.pack_bundle_file,
					  self.debug_shared_not_found, self.debug_search_for_swapped_ids, self.debug_use_shader_material_parameters,
					  self.debug_use_default_vertexdescriptor, self.debug_use_default_materialstate, self.debug_add_missing_textures)
		if status == {"CANCELLED"}:
			self.report({"ERROR"}, "Exporting has been cancelled. Check the system console for information.")
		return status


def menu_func_export(self, context):
	self.layout.operator(ExportBPR.bl_idname, text="Burnout Paradise Remastered (.dat)")


def register():
	bpy.utils.register_class(ExportBPR)
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
	bpy.utils.unregister_class(ExportBPR)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
	register()
