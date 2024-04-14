#leaked by _t38, fuck your shitty community lol
bl_info = {
    "name": "Export to Burnout Paradise format",
    "description": "Save models and textures as Burnout Paradise files.",
    "author": "DGIorio",
    "version": (1, 6),
    "blender": (2, 79, 0),
    "location": "File > Export > Burnout Paradise (.dat)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export"}
	
#  Save models and textures as Burnout Paradise Remastered or
#  The Ultimate Box files.
#
#  This program is free software; you can redistribute it and/or
#  modify it.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
import bpy
import bmesh
import math
import os
import shutil
import struct
import time
import zlib
import numpy as np		# Test calc_tangents from internet
import io
from contextlib import redirect_stdout
from collections import defaultdict
try:
	from lxml import etree as et	#used for "decoding" IDs
	decodedIDsOption = True
except: 
	try:
		import xml.etree.ElementTree as et
		decodedIDsOption = True
	except: decodedIDsOption = False
from math import radians
from mathutils import Matrix
import array
import copy
import binascii

def CreateIDsTable(srcPath, IDsList, Name):
	IDsTableDir = srcPath
	IDsTablePath = IDsTableDir + "\\" + Name + ".BIN"
	if IDsTablePath is None:
		return 0
	if not os.path.exists(IDsTableDir):
		return 0
	with open(IDsTablePath, "wb") as idt:
		idt.write(b'\x62\x6E\x64\x32')
		idt.write(struct.pack("<i", 2))
		idt.write(struct.pack("<i", 1))
		idt.write(struct.pack("<i", 48))
		idt.write(struct.pack("<i", len(IDsList)))
		idt.write(struct.pack("<i", 48))
		idt.write(struct.pack("<i", len(IDsList)*0x40 + 0x30))
		idt.write(struct.pack("<i", 0))
		idt.write(struct.pack("<i", 0))
		idt.write(struct.pack("<i", 7))
		idt.write(struct.pack("<i", 0))
		idt.write(struct.pack("<i", 0))
		for ID, type in IDsList.items():
			ID = bytearray.fromhex(ID.replace('_', ''))
			idt.write(ID)
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			idt.write(struct.pack("<i", 0))
			type = type2id(type)
			type = type[6]+type[7]+type[4]+type[5]+type[2]+type[3]+type[0]+type[1]
			type = bytearray.fromhex(type)
			idt.write(type)
			idt.write(struct.pack("<i", 0))

def CreateGraphicsSpec(srcPath, ReplacedVehicle, ModelNames, CoordinatesList, DummyHelperList, Transform, SubPart_ModelNames, SubPart_Info, use_Rotation, use_UniqueIDs):
	GraphicsSpecID = StringToID(ReplacedVehicle + "_graphics")
	GraphicSpecPath = srcPath + "\\" + "GraphicsSpec" + "\\" + GraphicsSpecID + ".dat"
	if GraphicSpecPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "GraphicsSpec"):
		os.makedirs(srcPath + "\\" + "GraphicsSpec")
	NumParts = len(ModelNames)
	NumSubParts = len(SubPart_ModelNames)
	#print("Len model names in GraphicsSpec",len(ModelNames))
	#print("Len CoordinatesList in GraphicsSpec",len(CoordinatesList))
	with open(GraphicSpecPath, "wb") as gs:
		gs.write(struct.pack("<i", 3))
		gs.write(struct.pack("<i", NumParts))
		gs.write(struct.pack("<i", 0x30))
		gs.write(struct.pack("<i", NumSubParts))
		IndexSize = NumParts*0x4
		division1 = IndexSize/0x10
		division2 = math.ceil(IndexSize/0x10)
		padComp = int((division2 - division1)*0x10)
		if padComp != 0:
			padCompLen1 = padComp
		else:
			padCompLen1 = 0
		Position1 = 0x30 + IndexSize + padCompLen1
		gs.write(struct.pack("<i", Position1))
		
		#Position2 = Position1
		IndexSize = NumSubParts*0xC
		division1 = IndexSize/0x10
		division2 = math.ceil(IndexSize/0x10)
		padComp = int((division2 - division1)*0x10)
		if padComp != 0:
			padCompLen2 = padComp
		else:
			padCompLen2 = 0
		Position2 = Position1 + IndexSize + padCompLen2
		
		gs.write(struct.pack("<i", Position2))
		Position3 = Position2 + NumParts*0x40
		gs.write(struct.pack("<i", Position3))
		division1 = NumParts/0x10
		division2 = math.ceil(NumParts/0x10)
		padComp = int((division2 - division1)*0x10)
		if padComp != 0:
			padCompLen4 = padComp
		else:
			padCompLen4 = 0
		Position4 = Position3 + NumParts + padCompLen4
		gs.write(struct.pack("<i", Position4))
		division1 = NumParts/0x10
		division2 = math.ceil(NumParts/0x10)
		padComp = int((division2 - division1)*0x10)
		if padComp != 0:
			padCompLen5 = padComp
		else:
			padCompLen5 = 0
		Position5 = Position4 + NumParts + padCompLen5
		gs.write(struct.pack("<i", Position5))
		gs.write(struct.pack("<i", 0))
		gs.write(struct.pack("<i", 0))
		gs.write(struct.pack("<i", 0))
		for i in range(0, NumParts):
			gs.write(struct.pack("<i", i))
		gs.write(bytearray([0])*padCompLen1)
		j = NumParts
		for i in range(NumSubParts-1, -1, -1):
			gs.write(struct.pack("<i", j))
			gs.write(struct.pack("<i", SubPart_Info[i][0]))
			gs.write(struct.pack("<i", SubPart_Info[i][1]))
			j += 1
		gs.write(bytearray([0])*padCompLen2)
		
		#for i in range(0, NumParts):
		for i in range(NumParts-1, -1, -1):
			x = 0
			y = 0.46875
			z = 0
			#x = CoordinatesList[i][0]
			#y = CoordinatesList[i][2]
			#z = -CoordinatesList[i][1]
			#x = CoordinatesList[ModelNames[i]][0]
			#y = CoordinatesList[ModelNames[i]][2]
			#z = -CoordinatesList[ModelNames[i]][1]
			x=0
			y=0
			z=0
			
			if use_Rotation:
				matrix_world = Transform[i]
				matrix_world = Matrix(matrix_world)
				matrix_world = matrix_world.transposed()
				gs.write(struct.pack("<4f", *matrix_world[0]))
				gs.write(struct.pack("<4f", *matrix_world[1]))
				gs.write(struct.pack("<4f", *matrix_world[2]))
				gs.write(struct.pack("<4f", *matrix_world[3]))
			else:
				ModelInfo = ModelNames[i].split("_")
				for j in range (0, len(DummyHelperList)):
					if ModelInfo[0] == DummyHelperList[j][0] and ModelInfo[1] == DummyHelperList[j][1]:
						#x = DummyHelperList[j][2]
						#y = DummyHelperList[j][4]		#z = y
						#z = DummyHelperList[j][3]
						x = DummyHelperList[j][2]
						y = DummyHelperList[j][4]		#z = y
						z = -DummyHelperList[j][3]
				#for j in range(0,len(Transform[i])-1):
					#for k in range(0,len(Transform[i][j])):
					#	gs.write(struct.pack("<f", Transform[i][j][k]))
					#gs.write(struct.pack("<ffff", *[Transform[i][j][0], Transform[i][j][2], Transform[i][j][1], Transform[i][j][3]]))
					#gs.write(struct.pack("<ffff", *[Transform[i][j][0], -Transform[i][j][2], Transform[i][j][1], Transform[i][j][3]]))
				#gs.write(struct.pack("<ffff", *[x, y, z, 1]))
				#gs.write(struct.pack("<ffff", *[Transform[i][0][0], 0, 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, Transform[i][1][2], 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, 0, -Transform[i][2][1], 0]))
				#gs.write(struct.pack("<ffff", *[abs(Transform[i][0][0]), 0, 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, abs(Transform[i][2][1]), 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, 0, abs(-Transform[i][1][2]), 0]))
				#gs.write(struct.pack("<ffff", *[x, y, z, 1]))
				#scale = Transform[i].to_scale()
				#gs.write(struct.pack("<ffff", *[scale[0], 0, 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, scale[1], 0, 0]))
				#gs.write(struct.pack("<ffff", *[0, 0, scale[2], 0]))
				#gs.write(struct.pack("<ffff", *[x, y, z, 1]))
				
				gs.write(struct.pack("<ffff", *[1, 0, 0, 0]))
				gs.write(struct.pack("<ffff", *[0, 1, 0, 0]))
				gs.write(struct.pack("<ffff", *[0, 0, 1, 0]))
				gs.write(struct.pack("<ffff", *[x, y, z, 1]))
			
		if NumParts <= 0xFF:
			for i in range(0, NumParts):
				gs.write(struct.pack("<B", i))
		elif NumParts > 0xFF:
			gs.write(bytearray([0])*NumParts)
		gs.write(bytearray([0])*padCompLen4)
		gs.write(bytearray([1])*NumParts)
		gs.write(bytearray([0])*padCompLen5)
		IndexSize = NumParts*0x4
		division1 = IndexSize/0x10
		division2 = math.ceil(IndexSize/0x10)
		padComp = int((division2 - division1)*0x10)
		if padComp != 0:
			padCompLen6 = padComp
		else:
			padCompLen6 = 0
		Position6 = Position5 + IndexSize + padCompLen6
		for i in range(0, NumParts):
			gs.write(struct.pack("<i", Position6 + 0x40*i))
		gs.write(bytearray([0])*padCompLen6)
		for i in range(0, NumParts):
			gs.write(struct.pack("<f", 1))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 1))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 1))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 0))
			gs.write(struct.pack("<f", 1))
		#for i in range(0, NumParts):
		j = 0
		for i in range(NumParts-1, -1, -1):
			gs.write(bytearray.fromhex(StringToID(ModelNames[i], use_UniqueIDs, ReplacedVehicle).replace('_', '')))
			gs.write(struct.pack("<i", 0))
			gs.write(struct.pack("<i", 0x30 + 0x4*j))
			gs.write(struct.pack("<i", 0))
			j += 1
		j = 0
		for i in range(NumSubParts-1, -1, -1):
			gs.write(bytearray.fromhex(StringToID(SubPart_ModelNames[i], use_UniqueIDs, ReplacedVehicle).replace('_', '')))
			gs.write(struct.pack("<i", 0))
			gs.write(struct.pack("<i", Position1 + 0xC*j))
			gs.write(struct.pack("<i", 0))
			j += 1

def CreateModel_withlods(srcPath, ModelID, RenderableList, world):
	ModelPath = srcPath + "\\" + "Model" + "\\" + ModelID + ".dat"
	if ModelPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "Model"):
		os.makedirs(srcPath + "\\" + "Model")
	with open(ModelPath, "wb") as md:
		NumIDs = len(RenderableList)
		if world == "trk" or world == "track":	
			lod_view_distance = [600.0, 800.0, 1000.0, 1200.0, 1400.0, 1600.0]
			if NumIDs == 1:
				lod_view_distance = [2000.0]	# There are some 10000.0
		else:
			lod_view_distance = [200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0]
			if NumIDs == 1:
				lod_view_distance = [10000.0]
		
		md.write(struct.pack("<i", 0x14))
		md.write(struct.pack("<i", 0x14 + NumIDs*0x4))
		if NumIDs <= 4:
			pointer = 0x14 + NumIDs*0x4 + 0x4
		elif NumIDs <= 8:
			pointer = 0x14 + NumIDs*0x4 + 0x8
		else:
			pointer = 0x14 + NumIDs*0x4 + 0xC
		md.write(struct.pack("<i", pointer))
		md.write(struct.pack("<i", 0))
		
		md.write(struct.pack("<B", NumIDs))
		md.write(struct.pack("<B", 0))
		if world == "trk" or world == "track":
			md.write(struct.pack("<B", 1))
		else:
			md.write(struct.pack("<B", 255))	# NumIDs
		md.write(struct.pack("<B", 2))
		
		for i in range(0, NumIDs):
			md.write(struct.pack("<i", 0))
		for i in range(0, NumIDs):
			md.write(struct.pack("<B", i))
		
		# Padding
		if NumIDs <= 4:
			for i in range(NumIDs, 0x4):
				md.write(struct.pack("<B", 0))
		elif NumIDs <= 8:
			for i in range(NumIDs, 0x8):
				md.write(struct.pack("<B", 0))
		else:
			for i in range(NumIDs, 0xC):
				md.write(struct.pack("<B", 0))
		
		for i in range(0, NumIDs):
			md.write(struct.pack("<f", lod_view_distance[(len(lod_view_distance) - NumIDs) + i]))
		
		padding = PaddingLenght(pointer + 0x4*NumIDs, 0x10)
		md.write(bytearray([0])*padding)
		
		for i, RenderableID in enumerate(RenderableList):
			md.write(bytearray.fromhex(RenderableID.replace('_', '')))
			md.write(struct.pack("<i", 0))
			md.write(struct.pack("<i", 0x10 + 0x4*(i+1)))
			md.write(struct.pack("<i", 0))

def CreateModel(srcPath, ModelID, RenderableID, world):
	ModelPath = srcPath + "\\" + "Model" + "\\" + ModelID + ".dat"
	if ModelPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "Model"):
		os.makedirs(srcPath + "\\" + "Model")
	with open(ModelPath, "wb") as md:
		md.write(struct.pack("<i", 20))
		md.write(struct.pack("<i", 24))
		md.write(struct.pack("<i", 28))
		md.write(struct.pack("<i", 0))
		md.write(struct.pack("<B", 1))
		md.write(struct.pack("<B", 0))
		if world == "trk" or world == "track":
			md.write(struct.pack("<B", 1))
		else:
			md.write(struct.pack("<B", 255))
		md.write(struct.pack("<B", 2))
		md.write(struct.pack("<i", 0))
		md.write(struct.pack("<i", 0))
		if world == "trk" or world == "track":				# TESTE
			md.write(struct.pack("<f", 2000.0))		#1201 seen in normal map, 2000 seen in BSI
		else:
			md.write(b'\x00\x40\x1C\x46')	# 10000
		md.write(bytearray.fromhex(RenderableID.replace('_', '')))
		md.write(struct.pack("<i", 0))
		md.write(struct.pack("<i", 20))
		md.write(struct.pack("<i", 0))

def CreateRenderableHeader(OutRenderablePath, centerX, centerY, centerZ, viewableDiameter, NumMeshes, VertexOffset, VertexBlockLen, IndexStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world):
	HeaderPath = OutRenderablePath + ".dat"
	header = open(HeaderPath, "wb")
	#header.write(struct.pack("<ffff", 0, 0, 0, 1))
	header.write(struct.pack("<ffff", centerX, centerY, centerZ, viewableDiameter))
	header.write(b'\x0B\x00')
	header.write(struct.pack("<H", NumMeshes))
	header.write(b'\x30\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x00\x00')
	header.write(struct.pack("<i", 0x30 + 0x4*NumMeshes))
	header.write(struct.pack("<i", 0x48 + 0x4*NumMeshes))
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
	cte = 0x80
	if world.name.lower() == "trk" or world.name.lower() == "track":
		cte = 0x70
	for j in range(0, NumMeshes):
		header.write(struct.pack("<i", 0x70 + (int((NumMeshes-2)/4))*0x10 + cte*j))
	header.write(struct.pack("<i", 0))
	header.write(struct.pack("<i", 0))
	header.write(b'\x03\x00\x00\x00\x00\x00\x00\x00')
	header.write(struct.pack("<i", VertexOffset))		#Almost Vextex start
	header.write(b'\x02\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x02\x00\x00\x00')
	header.write(struct.pack("<i", VertexOffset))		#Vextex start
	header.write(struct.pack("<i", VertexBlockLen))		#Vertex block size
	Head_size = header.tell()
	division1 = (Head_size/0x10)
	division2 = math.ceil(Head_size/0x10)
	padComp = int((division2 - division1)*0x10)
	header.write(bytearray([0])*padComp)
	if NumMeshes == 1:
		header.write(bytearray([0])*0x10)
	for j in range(0, NumMeshes):
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 4))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", IndexStart[j]))
		header.write(struct.pack("<i", PolyCount[j]*0x3))
		header.write(struct.pack("<f", 0))
		#header.write(b'\x04\x00\x01\x00')
		header.write(struct.pack("<H", NumVertexDesc[j]))
		header.write(struct.pack("<B", 1))
		if SubPartCode != []:
			try:
				header.write(struct.pack("<B", SubPartCode[j]))
			except:
				header.write(struct.pack("<B", 0))
		else:
			header.write(struct.pack("<B", 0))
		header.write(struct.pack("<i", 0x30 + 0x4*NumMeshes))
		header.write(struct.pack("<i", 0x48 + 0x4*NumMeshes))
		header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		if world.name.lower() != "trk" and world.name.lower() != "track":
			header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	
	# IDs
	for j in range(0, NumMeshes):
		#IDsList[VertexDesc1IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc2IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc3IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc4IDs[j]] = 'VertexDesc'
		header.write(bytearray.fromhex(MaterialIDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x68 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x58))
		header.write(struct.pack("<f", 0))
		header.write(bytearray.fromhex(VertexDesc1IDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x68 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x68))
		header.write(struct.pack("<f", 0))
		header.write(bytearray.fromhex(VertexDesc2IDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x68 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x6C))
		header.write(struct.pack("<f", 0))
		if NumVertexDesc[j] >= 3:
			header.write(bytearray.fromhex(VertexDesc3IDs[j].replace('_', '')))
			header.write(struct.pack("<f", 0))
			header.write(struct.pack("<i", 0x68 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x70))
			header.write(struct.pack("<f", 0))
			if NumVertexDesc[j] >= 4:
				header.write(bytearray.fromhex(VertexDesc4IDs[j].replace('_', '')))
				header.write(struct.pack("<f", 0))
				header.write(struct.pack("<i", 0x68 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x74))
				header.write(struct.pack("<f", 0))
	header.close()

def CreateRenderableHeader_BP(OutRenderablePath, centerX, centerY, centerZ, viewableDiameter, NumMeshes, VertexOffset, VertexBlockLen, IndexStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world, IndexCount, VertexSize):
	HeaderPath = OutRenderablePath + ".dat"
	header = open(HeaderPath, "wb")
	#header.write(struct.pack("<ffff", 0, 0, 0, 1))
	header.write(struct.pack("<ffff", centerX, centerY, centerZ, viewableDiameter))
	header.write(b'\x0B\x00')
	header.write(struct.pack("<H", NumMeshes))
	header.write(b'\x30\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x00\x00')
	header.write(struct.pack("<i", 0x30 + 0x4*NumMeshes))
	header.write(struct.pack("<i", 0x40 + 0x4*NumMeshes))
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
	cte = 0x80
	#if world.name.lower() == "trk" or world.name.lower() == "track":
	#	cte = 0x70
	for j in range(0, NumMeshes):
		header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j))
	header.write(struct.pack("<i", IndexCount))
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x65\x00\x00\x00')
	header.write(struct.pack("<i", VertexOffset))
	header.write(b'\x00\x00\x00\x00')
	header.write(struct.pack("<i", VertexBlockLen))		#Vertex block size
	Head_size = header.tell()
	division1 = (Head_size/0x10)
	division2 = math.ceil(Head_size/0x10)
	padComp = int((division2 - division1)*0x10)
	header.write(bytearray([0])*padComp)
	if NumMeshes == 1:
		header.write(bytearray([0])*0x10)
	for j in range(0, NumMeshes):
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		
		header.write(struct.pack("<i", 4))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", IndexStart[j]))
		header.write(struct.pack("<i", int(VertexBlockLen/VertexSize)))					# VerticesCount
		header.write(struct.pack("<i", 0))												# VerticesStart
		
		header.write(struct.pack("<i", PolyCount[j]))
		header.write(struct.pack("<f", 0))
		#header.write(b'\x04\x00\x01\x00')
		header.write(struct.pack("<H", NumVertexDesc[j]))
		header.write(struct.pack("<B", 1))
		if SubPartCode != []:
			try:
				header.write(struct.pack("<B", SubPartCode[j]))
			except:
				header.write(struct.pack("<B", 0))
		else:
			header.write(struct.pack("<B", 0))
		header.write(struct.pack("<i", 0x30 + 0x4*NumMeshes))
		header.write(struct.pack("<i", 0x40 + 0x4*NumMeshes))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<f", 0))
		header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		#if world.name.lower() != "trk" and world.name.lower() != "track":
		#	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	header.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	
	# IDs
	for j in range(0, NumMeshes):
		#IDsList[VertexDesc1IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc2IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc3IDs[j]] = 'VertexDesc'
		#IDsList[VertexDesc4IDs[j]] = 'VertexDesc'
		header.write(bytearray.fromhex(MaterialIDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x58))
		header.write(struct.pack("<f", 0))
		header.write(bytearray.fromhex(VertexDesc1IDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x68))
		header.write(struct.pack("<f", 0))
		header.write(bytearray.fromhex(VertexDesc2IDs[j].replace('_', '')))
		header.write(struct.pack("<f", 0))
		header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x6C))
		header.write(struct.pack("<f", 0))
		if NumVertexDesc[j] >= 3:
			header.write(bytearray.fromhex(VertexDesc3IDs[j].replace('_', '')))
			header.write(struct.pack("<f", 0))
			header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x70))
			header.write(struct.pack("<f", 0))
			if NumVertexDesc[j] >= 4:
				header.write(bytearray.fromhex(VertexDesc4IDs[j].replace('_', '')))
				header.write(struct.pack("<f", 0))
				header.write(struct.pack("<i", 0x60 + (int((NumMeshes-2)/4))*0x10 + cte*j + 0x74))
				header.write(struct.pack("<f", 0))
	header.close()

def CreateRenderableBody(srcPath, obj, CoordinatesList, TransformMat, DummyHelperList, BoneCoordsList, ModelDict, MaterialDict, IDsList, world, vehicleName, verify_genericIDs, reuse_Object, use_Rotation, use_Accurate_split, use_Damage, use_UniqueIDs, recalculate_bones, game_version):
	mesh = obj.data
	if reuse_Object:
		RenderableName = obj.name.split(".")[0]
		RenderableName_lod0 = RenderableName
		try:
			LOD = obj['LOD']
			if LOD > 0:
				#RenderableName_lod0 = RenderableName
				RenderableName += "_LOD" + str(LOD)
		except: pass
	elif not reuse_Object:
		RenderableName = obj.name
		RenderableName_lod0 = RenderableName
	RenderableID = StringToID(RenderableName, use_UniqueIDs, vehicleName)
	RenderableID_lod0 = StringToID(RenderableName_lod0, use_UniqueIDs, vehicleName)
	OutRenderablePath = srcPath + "\\" + "Renderable" + "\\" + RenderableID
	BodyPath = OutRenderablePath + "_model.dat"
	if len(obj.data.vertices) == 0:
		return (-1, '')
	if not os.path.exists(srcPath + "\\" + "Renderable"):
		os.makedirs(srcPath + "\\" + "Renderable")
	if os.path.isfile(BodyPath):
		# issue if same mesh but change modelID, or different meshes but same obj.name.split
		try:
			ModelID = StringToID(obj['ModelID'], use_UniqueIDs, vehicleName)
			if ModelID == RenderableID or ModelID == RenderableID_lod0:
				ModelID = StringToID(obj['ModelID'] + "_model", use_UniqueIDs, vehicleName)
		except: ModelID = StringToID(RenderableName_lod0 + "_model", use_UniqueIDs, vehicleName)			# trocado para o LOD0 12/06/2021
		#ModelID = StringToID(RenderableName + "_model", use_UniqueIDs, vehicleName)
		try: LOD = obj['LOD']
		except: LOD = 0
		
		# Same renderable name but the obj['ModelID'] is different (same renderable being called to other model),
		# so we verify if the modelID is in the dict for creating the file
		try: ModelDict[ModelID]
		except:
			ModelDict[ModelID] = [None]*6
			ModelDict[ModelID].insert(LOD, RenderableID)	# Dict containing a list of RenderableIDs of each ModelID
		IDsList[ModelID] = 'Model'
		
		return (LOD, ModelID)
	with open(BodyPath, "wb") as Body:
		TriangleList,VerticesList,NormalList,TangentList,UV1List,UV2List,BoneIndicesList,BoneWeightsList = ReadObject(obj, use_Rotation, use_Accurate_split, recalculate_bones)
		minX = min([sublist[0] for sublist in VerticesList])
		minY = min([sublist[1] for sublist in VerticesList])
		minZ = min([sublist[2] for sublist in VerticesList])
		maxX = max([sublist[0] for sublist in VerticesList])
		maxY = max([sublist[1] for sublist in VerticesList])
		maxZ = max([sublist[2] for sublist in VerticesList])
		avgX = (minX+maxX)/2.0
		avgY = (minY+maxY)/2.0
		avgZ = (minZ+maxZ)/2.0
		centerX = avgX
		centerY = avgY
		centerZ = avgZ
		#viewableDiameter = ((maxX**2+maxY**2+maxZ**2)**0.5 - (minX**2+minY**2+minZ**2)**0.5)
		viewableDiameter = (((maxY-minY)**2.0+(maxZ-minZ)**2.0+(maxX-minX)**2.0)**0.5)*5.0		# 5.0 is just for safety (old was 1.2)
		for IndexList in TriangleList:
			for i in range(0,len(IndexList)):
				Body.write(struct.pack('<HHH', *IndexList[i]))
		Body.flush()
		padComp1 = Padding(BodyPath,0x10)
		Body.write(bytearray([0])*padComp1)
		#for i in range(0, len(mesh.vertices)):
		for i in range(0, len(VerticesList)):
			Body.write(struct.pack('<fff', *VerticesList[i]))
			Body.write(struct.pack('<fff', *NormalList[i]))
			#if world.name.lower() != "trk" and world.name.lower() != "track":			# 03-06-2021: using tangents also on TRKs (bsi roads require tangents)
			Body.write(struct.pack('<fff', *TangentList[i]))
			Body.write(struct.pack('<ff', *UV1List[i]))
			Body.write(struct.pack('<ff', *UV2List[i]))
			if world.name.lower() != "trk" and world.name.lower() != "track":
				if BoneIndicesList != [] and BoneWeightsList != []:
					Body.write(struct.pack('<BBBB', *BoneIndicesList[i]))
					if use_Damage == False:
						BoneWeights = [0,0,0,0]
						Body.write(struct.pack('<BBBB', *BoneWeights))
					else:
						Body.write(struct.pack('<BBBB', *BoneWeightsList[i]))
				else:
					Wheel = False
					if BoneCoordsList != []:
						ModelInfo = RenderableName.split("_")
						if len(ModelInfo) >= 2:
							for j in range(0,len(DummyHelperList)):
								if ModelInfo[0] == DummyHelperList[j][0] and ModelInfo[1] == DummyHelperList[j][1]:
									Wheel = True
									CoordinatesList[0] = DummyHelperList[j][2]
									CoordinatesList[1] = DummyHelperList[j][3]
									CoordinatesList[2] = DummyHelperList[j][4]
									BoneIndex1, BoneIndex2, BoneIndex3, BoneWeight1, BoneWeight2, BoneWeight3 = NearestPoints(VerticesList[i][0],VerticesList[i][1],VerticesList[i][2],CoordinatesList,TransformMat,BoneCoordsList[-4:])
									BoneIndex1 = BoneIndex1 + len(BoneCoordsList)-4
									BoneIndex2 = 0
									BoneWeight1 = 0xFF
									BoneWeight2 = 0
									break
							if Wheel == False:
								BoneIndex1, BoneIndex2, BoneIndex3, BoneWeight1, BoneWeight2, BoneWeight3 = NearestPoints(VerticesList[i][0],VerticesList[i][1],VerticesList[i][2],CoordinatesList,TransformMat,BoneCoordsList[:-4])
						else:
							BoneIndex1, BoneIndex2, BoneIndex3, BoneWeight1, BoneWeight2, BoneWeight3 = NearestPoints(VerticesList[i][0],VerticesList[i][1],VerticesList[i][2],CoordinatesList,TransformMat,BoneCoordsList[:-4])
						BoneIndex3 = 0
						BoneIndex4 = 0
						BoneWeight3 = 0
						BoneWeight4 = 0
						BoneIndices = [BoneIndex1,BoneIndex2,BoneIndex3,BoneIndex4]
						BoneWeights = [int(BoneWeight1),int(BoneWeight2),int(BoneWeight3),int(BoneWeight4)]
					else:
						BoneIndices = [0,0,0,0]
						BoneWeights = [0,0,0,0]
					if use_Damage == False and Wheel == False:
						BoneWeights = [0,0,0,0]
					Body.write(struct.pack('<BBBB', *BoneIndices))
					Body.write(struct.pack('<BBBB', *BoneWeights))
		Body.flush()
		padComp2 = Padding(BodyPath, 0x80)
		Body.write(bytearray([0])*padComp2)
	#NumMeshes = 1
	NumMeshes = len(TriangleList)
	if world.name.lower() == "trk" or world.name.lower() == "track":
		#VertexSize = 0x34
		VertexSize = 0x34
		NumVertexDesc = [2]*NumMeshes
	else:
		VertexSize = 0x3C
		NumVertexDesc = [4]*NumMeshes
	#VertexOffset = len(TriangleList)*3*2 + padComp1
	#VertexBlockLen = VertexSize*len(VerticesList)
	#IndexStart = [0]*NumMeshes
	#PolyCount = [len(TriangleList)]*NumMeshes
	IndexStart = []
	PolyCount = []
	PCount = 0
	for IndexList in TriangleList:
		IndexStart.append(PCount*3)
		PolyCount.append(len(IndexList))
		PCount += len(IndexList)
	IndexCount = PCount*3			# Used in BP (original)
	VertexOffset = PCount*3*2 + padComp1
	VertexBlockLen = VertexSize*len(VerticesList)
	MaterialIDs = []
	MaterialName = ''
	RasterPath = ''
	RasterName = ''
	isEmpty = False
	
	# SubPart codes
	try:
		SubPartCode = obj['SubPartCodes'].split("_")
		SubPartCode = list(map(int, SubPartCode))
	except: SubPartCode = []
	
	# Checking if the material is used in the mesh (making a list of material indices and later checking them)
	material_indeces = []
	for face in obj.data.polygons:
		if face.material_index not in material_indeces:
			material_indeces.append(face.material_index)
	
	cte_subpart = 0
	for index, mat_slot in enumerate(obj.material_slots):		
		if index not in material_indeces:
			try:
				del SubPartCode[index - cte_subpart]
				cte_subpart += 1
			except: pass
			continue
			
		RasterDict = {}
		MaterialName = mat_slot.name + "_material"
		isEmpty = True
		#if mat_slot.material.texture_slots[0] == None:
		#	isEmpty = True
		try: shaderDescription = mat_slot.material['Shader']
		except: shaderDescription = 'None'
		for mtex_slot in mat_slot.material.texture_slots:
			if mtex_slot:
				if hasattr(mtex_slot.texture , 'image'): pass
				#if hasattr(mtex_slot.texture , 'image') != 'None':
				if hasattr(mtex_slot.texture , 'image'):
					if mtex_slot.texture.image is None:
						isEmpty = True
					elif mtex_slot.texture.image.size[0] == 0 or mtex_slot.texture.image.size[1] == 0:
						isEmpty = True
					else:
						#RasterName = mtex_slot.texture.image.name + "_raster"				#Maybe it's good to create an array containing all the textures per material
						RasterName = mtex_slot.texture.image.name
						if verify_genericIDs == True:
							RName = mtex_slot.texture.name
							if RName[:2] != 'Kd' and RName[:2] != 'Ka' and len(RName) > 6: RasterName = RName
						RasterPath = bpy.path.abspath(mtex_slot.texture.image.filepath)
						isEmpty = False
						if not os.path.isfile(RasterPath):
							isEmpty = True
						#break
						try: MapType = mtex_slot.texture['MapType']
						except: 
							if mtex_slot.use_map_normal:
								MapType = 'Normal'
							elif mtex_slot.use_map_emit:
								MapType = 'Emissive'
							elif mtex_slot.use_map_hardness:
								MapType = 'Specular'
							else:
								if not 'Diffuse' in RasterDict:
									MapType = 'Diffuse'
								else:
									MapType = 'NotUsed'
						RasterDict[MapType] = [RasterName, RasterPath]
		color = [mat_slot.material.diffuse_color.r, mat_slot.material.diffuse_color.g, mat_slot.material.diffuse_color.b, mat_slot.material.alpha]
		if isEmpty:
			RasterName, RasterPath = CreateImage(srcPath, MaterialName, color)
			MapType = 'Diffuse'
			RasterDict[MapType] = [RasterName, RasterPath]
		if not 'Diffuse' in RasterDict:
			if 'BaseMap' in RasterDict: MapType = 'BaseMap'
			elif 'DetailMap' in RasterDict: MapType = 'DetailMap'
			elif 'SlantedFace' in RasterDict: MapType = 'SlantedFace'
			elif 'RiverFloor' in RasterDict: MapType = 'RiverFloor'
			elif 'Overlay' in RasterDict: MapType = 'Overlay'
			else:
				#MapType = list(RasterDict.keys())[0]
				NotDiffuseList = ['Crumple', 'Scratch', 'Normal', 'AoMap', 'Reflection', 'Emissive', 'LightMap', 'lightMap', 'Lightmap', 'NormalDetail', 'BlurNormal', 'Effects', 'BlurEffects', 'InternalNormal', 'ExternalNormal', 'Displacement', 'CrackedGlassNormal', 'DustTexture', 'ScorchTexture']
				MapType = ""
				for item in list(RasterDict.keys()):
					if item not in NotDiffuseList:
						MapType = item
						break
			if MapType == "":
				RasterName, RasterPath = CreateImage(srcPath, MaterialName, color)
			else:
				RasterName, RasterPath = RasterDict[MapType]
			MapType = 'Diffuse'
			RasterDict[MapType] = [RasterName, RasterPath]
		#MaterialIDs.append(StringToID(MaterialName, use_UniqueIDs, vehicleName), use_UniqueIDs, vehicleName)
		#IDsList[StringToID(MaterialName, use_UniqueIDs, vehicleName)] = 'Material'
		#CreateMaterial(srcPath,RenderableName,MaterialName,RasterName,RasterPath,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs)
		MaterialName = CreateMaterial(srcPath,RenderableName,MaterialName,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version)
		MaterialID = StringToID(MaterialName, use_UniqueIDs, vehicleName)
		MaterialIDs.append(MaterialID)
		IDsList[MaterialID] = 'Material'
	#ModelID = StringToID(obj.name + "_model", use_UniqueIDs, vehicleName)
	try:
		ModelID = StringToID(obj['ModelID'], use_UniqueIDs, vehicleName)
		if ModelID == RenderableID or ModelID == RenderableID_lod0:
			ModelID = StringToID(obj['ModelID'] + "_model", use_UniqueIDs, vehicleName)
	except: ModelID = StringToID(RenderableName_lod0 + "_model", use_UniqueIDs, vehicleName)				# trocado para o LOD0 12/06/2021
	#ModelID = StringToID(RenderableName + "_model", use_UniqueIDs, vehicleName)	# commented
	#MaterialIDs = [StringToID(MaterialName, use_UniqueIDs, vehicleName)]*NumMeshes
	IDsList[ModelID] = 'Model'
	IDsList[RenderableID] = 'Renderable'
	#IDsList[StringToID(MaterialName, use_UniqueIDs, vehicleName)] = 'Material'
	if world.name.lower() == "trk" or world.name.lower() == "track":
		VertexDesc1IDs = ["4C_66_C2_A5"]*NumMeshes		#0x34
		VertexDesc2IDs = ["E1_74_B4_4A"]*NumMeshes
		#VertexDesc1IDs = ["5B_96_3F_E2"]*NumMeshes		#0x28
		#VertexDesc2IDs = ["8C_24_A1_BD"]*NumMeshes
		VertexDesc3IDs = ["0E_46_97_8F"]*NumMeshes
		VertexDesc4IDs = ["9F_F0_42_9F"]*NumMeshes
		IDsList["4C_66_C2_A5"] = 'VertexDesc'			#0x34
		IDsList["E1_74_B4_4A"] = 'VertexDesc'
		IDsList["5B_96_3F_E2"] = 'VertexDesc'			#0x28
		IDsList["8C_24_A1_BD"] = 'VertexDesc'
		if game_version == "BPR":
			CreateVertexDescTRK(srcPath)
		elif game_version == "BP":
			CreateVertexDescTRK_BP(srcPath)
	else:
		VertexDesc1IDs = ["B8_23_13_0F"]*NumMeshes
		VertexDesc2IDs = ["7F_44_88_2B"]*NumMeshes
		VertexDesc3IDs = ["0E_46_97_8F"]*NumMeshes
		VertexDesc4IDs = ["9F_F0_42_9F"]*NumMeshes
		IDsList["B8_23_13_0F"] = 'VertexDesc'
		IDsList["7F_44_88_2B"] = 'VertexDesc'
		IDsList["0E_46_97_8F"] = 'VertexDesc'
		IDsList["9F_F0_42_9F"] = 'VertexDesc'
		if game_version == "BPR":
			CreateVertexDesc(srcPath)
		elif game_version == "BP":
			CreateVertexDesc_BP(srcPath)
	
	if game_version == "BPR":
		CreateRenderableHeader(OutRenderablePath, centerX, centerY, centerZ, viewableDiameter, NumMeshes, VertexOffset, VertexBlockLen, IndexStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world)
	elif game_version == "BP":
		CreateRenderableHeader_BP(OutRenderablePath, centerX, centerY, centerZ, viewableDiameter, NumMeshes, VertexOffset, VertexBlockLen, IndexStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world, IndexCount, VertexSize)
	
	LOD = 0
	try:
		LOD = obj['LOD']
	except:
		# obj.name = LeftDoor_LOD0 or LeftDoor.LOD0 or LeftDoor.0, but many edits would be necessary in the code
		LOD = 0
	try: ModelDict[ModelID]
	except: ModelDict[ModelID] = [None]*6
	ModelDict[ModelID].insert(LOD, RenderableID)	# Dict containing a list of RenderableIDs of each ModelID
	#CreateModel(srcPath, ModelID, RenderableID, world.name.lower())
	#if MaterialName != '':
	#	CreateMaterial(srcPath,RenderableName,MaterialName,shaderDescription,RasterDict,IDsList,world,verify_genericIDs)
	if game_version == "BPR":
		CreateMaterialState(srcPath)
	elif game_version == "BP":
		CreateMaterialState_BP(srcPath)
	return (LOD, ModelID)

def CreateMaterial(srcPath,RenderableName,MaterialName,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version):
	MaterialName_in = MaterialName
	if not os.path.exists(srcPath + "\\" + "Material"):
		os.makedirs(srcPath + "\\" + "Material")
	MaterialType = MaterialName.split("_")[0].lower()
	try: RasterName = RasterDict['Diffuse'][0]
	except: RasterName = ''
	
	if shaderDescription == 'None' or shaderDescription == "":
		if world.name.lower() == "trk" or world.name.lower() == "track":
			if MaterialType == "default":
				shaderDescription = "default_TRK_DGI"
			else: 
				if shaderDescription == "":
					shaderDescription = "else_TRK_DGI"
		elif MaterialType == "default":
			shaderDescription = "default_DGI"
		elif MaterialType == "emissive":
			shaderDescription = "emissive_DGI"
		elif MaterialType == "shiny":
			shaderDescription = "shiny_DGI"
		elif MaterialType == "matte":
			shaderDescription = "matte_DGI"
		elif MaterialType == "chrome":
			shaderDescription = "chrome_DGI"
		elif MaterialType == "tyre" or MaterialType == "tire":
			shaderDescription = "tyre_DGI"
		elif MaterialType == "tread":
			shaderDescription = "tyre_DGI"
		elif MaterialType == "rubber":
			shaderDescription = "tyre_DGI"
		elif MaterialType == "glass-traffic" or MaterialType == "traffic-glass":
			shaderDescription = "glass_traffic"
		elif MaterialType == "glass":
			shaderDescription = "glass_DGI"
		elif MaterialType == "transparent":
			shaderDescription = "transparent_DGI"
		elif MaterialType == "mirror":
			shaderDescription = "mirror_DGI"
		elif "emissive" in RenderableName.lower() or "emissive" in MaterialName.lower() or "emissive" in RasterName.lower():
			shaderDescription = "emissive_DGI"
		elif "shiny" in RenderableName.lower() or "shiny" in MaterialName.lower() or "shiny" in RasterName.lower():
			shaderDescription = "shiny_DGI"
		elif "matte" in RenderableName.lower() or "matte" in MaterialName.lower() or "matte" in RasterName.lower():
			shaderDescription = "matte_DGI"
		elif "opaque" in RenderableName.lower() or "opaque" in MaterialName.lower() or "opaque" in RasterName.lower():
			shaderDescription = "matte_DGI"
		#elif "opac" in RenderableName.lower() or "opac" in MaterialName.lower() or "opac" in RasterName.lower():
		#	shaderDescription = "matte_DGI"
		elif "glass" in RenderableName.lower() or "glass" in MaterialName.lower() or "glass" in RasterName.lower():
			shaderDescription = "glass_DGI"
		elif "window" in RenderableName.lower() or "window" in MaterialName.lower() or "window" in RasterName.lower():
			shaderDescription = "glass_DGI"
		elif "gls" in RenderableName.lower() or "gls" in MaterialName.lower() or "gls" in RasterName.lower():
			shaderDescription = "glass_DGI"
		elif "interior" in RenderableName.lower() or "interior" in MaterialName.lower() or "interior" in RasterName.lower():
			shaderDescription = "matte_DGI"
		elif "under" in RenderableName.lower() or "under" in MaterialName.lower() or "under" in RasterName.lower():
			shaderDescription = "matte_DGI"
		elif "chrome" in RenderableName.lower() or "chrome" in MaterialName.lower() or "chrome" in RasterName.lower():
			shaderDescription = "chrome_DGI"
		elif "tyre" in RenderableName.lower() or "tyre" in MaterialName.lower() or "tyre" in RasterName.lower():
			shaderDescription = "tyre_DGI"
		elif "tire" in RenderableName.lower() or "tire" in MaterialName.lower() or "tire" in RasterName.lower():
			shaderDescription = "tyre_DGI"
		elif "tread" in RenderableName.lower() or "tread" in MaterialName.lower() or "tread" in RasterName.lower():
			shaderDescription = "tyre_DGI"
		elif "rubber" in RenderableName.lower() or "rubber" in MaterialName.lower() or "rubber" in RasterName.lower():
			shaderDescription = "tyre_DGI"
		elif "transparent" in RenderableName.lower() or "transparent" in MaterialName.lower() or "transparent" in RasterName.lower():
			shaderDescription = "transparent_DGI"
		elif "grill" in RenderableName.lower() or "grill" in MaterialName.lower() or "grill" in RasterName.lower():
			shaderDescription = "transparent_DGI"
		elif "badge" in RenderableName.lower() or "badge" in MaterialName.lower() or "badge" in RasterName.lower():
			shaderDescription = "transparent_DGI"
		elif "emblem" in RenderableName.lower() or "emblem" in MaterialName.lower() or "emblem" in RasterName.lower():
			shaderDescription = "transparent_DGI"
		elif "symbol" in RenderableName.lower() or "symbol" in MaterialName.lower() or "symbol" in RasterName.lower():
			shaderDescription = "transparent_DGI"
		elif "mirror" in RenderableName.lower() or "mirror" in MaterialName.lower() or "mirror" in RasterName.lower():
			shaderDescription = "mirror_DGI"
		else:
			if shaderDescription == "":
				shaderDescription = "else_DGI"
	
	#MaterialName = mat_slot.name + "_material"
	MaterialName_ = MaterialName + "_" + shaderDescription
	add_to_dict = False
	if MaterialName not in MaterialDict:
		# Add to the material/shader dict and also to the material list
		#MaterialDict[MaterialName] = shaderDescription
		add_to_dict = True
	elif MaterialDict[MaterialName] == shaderDescription:
		# Add only to the material list
		pass
	#elif MaterialDict[MaterialName + "_" + shaderDescription] == shaderDescription:
	elif MaterialName_ in MaterialDict:
		# Add only to the material list
		MaterialName += "_" + shaderDescription
	elif MaterialDict[MaterialName] != shaderDescription:
		# Edit the new material name, add to the material/shader dict and also to the material list
		MaterialName += "_" + shaderDescription
		#MaterialDict[MaterialName] = shaderDescription
		add_to_dict = True
	
	if world.name.lower() == "trk" or world.name.lower() == "track":
		#if world.name.lower() == "trk" or world.name.lower() == "track": CreateMaterialTRK(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		if shaderDescription == "default_TRK_DGI": CreateMaterialTRK(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "VideoWall_Diffuse_Opaque_Singlesided": CreateMaterial_19_6E_C7_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Chevron_Illuminated_Greyscale_Singlesided": CreateMaterial_1A_06_FF_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_DriveableSurface_Detailmap_Opaque_Singlesided": CreateMaterial_1B_D8_B8_27(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Cruciform_1Bit_Doublesided_Instanced": CreateMaterial_1F_DA_DF_6E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_BodypartsSkin_EnvMapped": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_1Bit_Tyre_Textured": CreateMaterial_2D_40_9E_05(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Livery_Alpha_CarGuts": CreateMaterial_31_8E_3B_9E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Greyscale_Window_Textured": CreateMaterial_33_0B_A4_5E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		#Glass material without blue tint used in traffic cars (by Piotrek)
		elif shaderDescription == "Vehicle_Greyscale_Window_Textured_Traffic": CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Vehicle_Greyscale_Headlight_Doublesided": CreateMaterial_34_11_6F_C8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "BuildingGlass_Transparent_Doublesided": CreateMaterial_35_91_5B_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Diffuse_Greyscale_Singlesided": CreateMaterial_36_9A_6B_40(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Diffuse_Opaque_Singlesided": CreateMaterial_37_C2_9A_C3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Cruciform_1Bit_Doublesided": CreateMaterial_37_E7_77_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Diffuse_1Bit_Doublesided": CreateMaterial_3C_A3_99_3E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_1Bit_Doublesided2": CreateMaterial_3D_C9_A3_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Gold_Illuminated_Reflective_Opaque_Singlesided": CreateMaterial_3F_28_A4_93(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Diffuse_Greyscale_Doublesided": CreateMaterial_42_73_1A_D2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Sign_Illuminance_Diffuse_Opaque_Singlesided": CreateMaterial_46_FB_C2_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tint_Specular_1Bit_Doublesided": CreateMaterial_49_3C_26_F6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Sign_Diffuse_Opaque_Singlesided": CreateMaterial_49_A7_17_A0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_Opaque_Singlesided": CreateMaterial_4B_D9_70_EA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Grass_Specular_Opaque_Singlesided": CreateMaterial_4D_7F_80_14(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tint_Building_Opaque_Singlesided": CreateMaterial_4E_83_F2_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_Decal_Textured_UVAnim": CreateMaterial_51_80_C9_2F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Livery_Alpha_CarGuts_Skin": CreateMaterial_56_60_98_39(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Building_Opaque_Singlesided": CreateMaterial_57_0B_99_65(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Decal_Textured_EnvMapped_PoliceLights": CreateMaterial_5D_1F_A9_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Road_Detailmap_Opaque_Singlesided": CreateMaterial_5D_C3_BE_4F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_1Bit_Singlesided2": CreateMaterial_65_25_EA_21(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_CarbonFibre_Textured": CreateMaterial_66_30_78_11(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "ShoreLine_Diffuse_Greyscale_Singlesided": CreateMaterial_66_63_5A_26(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_Greyscale_Singlesided": CreateMaterial_6B_A8_27_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Metal_Textured_Skin": CreateMaterial_6F_53_CC_FA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Terrain_Diffuse_Opaque_Singlesided": CreateMaterial_71_12_EC_98(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Water_Specular_Opaque_Singlesided": CreateMaterial_73_B0_DA_EC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PlasticMatt_Textured": CreateMaterial_78_CE_40_2C(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_WheelChrome_Textured_Illuminance": CreateMaterial_79_7D_2F_76(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Road_Detailmap_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Illuminance_Diffuse_1Bit_Doublesided": CreateMaterial_7C_C6_D3_1D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "MetalSheen_Opaque_Doublesided": CreateMaterial_7F_B8_3B_1A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_NormalMapped": CreateMaterial_82_DE_22_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "FlashingNeon_Diffuse_1Bit_Doublesided": CreateMaterial_86_6F_8D_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Building_Night_Opaque_Singlesided": CreateMaterial_89_41_8E_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BP"  and shaderDescription == "Building_Night_Opaque_Singlesided": CreateMaterial_57_0B_99_65(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			#"Building_Opaque_Singlesided"
		elif shaderDescription == "Foliage_1Bit_Doublesided": CreateMaterial_8A_88_2A_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PlasticMatt": CreateMaterial_8B_4D_5D_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Cable_GreyScale_Doublesided": CreateMaterial_93_5F_33_58(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Diffuse_Opaque_Doublesided": CreateMaterial_94_B4_DB_B5(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_Opaque_Singlesided2": CreateMaterial_95_66_1E_23(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured_Illuminance": CreateMaterial_98_98_75_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "Road_Night_Detailmap_Opaque_Singlesided": CreateMaterial_9E_FB_32_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BP"  and shaderDescription == "Road_Night_Detailmap_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			# "Road_Detailmap_Opaque_Singlesided"
		elif shaderDescription == "Diffuse_1Bit_Singlesided": CreateMaterial_9F_D5_D8_48(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_1Bit_MetalFaded_Textured_EnvMapped": CreateMaterial_A2_14_84_00(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_DetailMap_Opaque_Singlesided": CreateMaterial_A2_62_24_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_Reflective_Opaque_Singlesided2": CreateMaterial_A6_28_0B_CF(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tint_Specular_Opaque_Singlesided": CreateMaterial_AD_08_F1_AA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Chrome_Damaged": CreateMaterial_AD_23_5C_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_1Bit_Doublesided": CreateMaterial_AD_57_BF_E3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_Opaque_Doublesided": CreateMaterial_AE_B3_92_62(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Illuminance_Diffuse_Opaque_Singlesided": CreateMaterial_B0_1D_35_C6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Terrain_Specular_Opaque_Singlesided": CreateMaterial_B1_2C_80_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "DriveableSurface_Night_Detailmap_Opaque_Singlesided": CreateMaterial_B4_56_99_82(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BP"  and shaderDescription == "DriveableSurface_Night_Detailmap_Opaque_Singlesided": CreateMaterial_BD_2E_A8_C4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)									# "DriveableSurface_Detailmap_Opaque_Singlesided"
		elif shaderDescription == "Vehicle_Opaque_Metal_Textured": CreateMaterial_B4_A6_ED_D7(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Sign_Lightmap_Diffuse_Opaque_Singlesided": CreateMaterial_B6_7A_FA_60(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Glass_Specular_Transparent_Doublesided": CreateMaterial_B8_A1_8A_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_1Bit_Singlesided": CreateMaterial_B8_A5_9E_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Lightmap_Diffuse_Opaque_Singlesided": CreateMaterial_B9_E2_4F_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Sign_Specular_Opaque_Singlesided": CreateMaterial_BA_1F_F8_AC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "DriveableSurface_DetailMap_Diffuse_Opaque_Singlesided": CreateMaterial_BA_2E_9B_81(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "DriveableSurface_Detailmap_Opaque_Singlesided": CreateMaterial_BD_2E_A8_C4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BPR" and shaderDescription == "FlashingNeon_Diffuse_Opaque_Singlesided": CreateMaterial_C0_04_1A_37(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif game_version == "BP"  and shaderDescription == "FlashingNeon_Diffuse_Opaque_Singlesided": CreateMaterial_86_6F_8D_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			# "FlashingNeon_Diffuse_1Bit_Doublesided"
		elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured_Damaged": CreateMaterial_C4_E3_58_7A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_Light_Textured_EnvMapped": CreateMaterial_C4_E4_B3_99(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Sign_Diffuse_1Bit_Singlesided": CreateMaterial_C5_1D_C5_57(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Specular_Greyscale_Doublesided": CreateMaterial_C7_1B_BF_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Illuminance_Diffuse_1Bit_Singlesided": CreateMaterial_D0_75_4B_DF(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_SimpleMetal_Textured": CreateMaterial_D2_CE_2F_51(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_Opaque_Doublesided2": CreateMaterial_D2_FB_F8_AB(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Lightmapped_Road_Detailmap_Opaque_Singlesided2": CreateMaterial_D4_90_D6_B8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_NormalMap_SpecMap_Skin": CreateMaterial_D9_7E_0C_84(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_Traffic": CreateMaterial_DB_62_6A_AE(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Decal_Textured_EnvMapped": CreateMaterial_E1_C4_7C_19(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_Decal_Textured": CreateMaterial_EA_27_69_B4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "CarStudio_DoNotShipWithThisInTheGame": CreateMaterial_EB_BF_C4_9D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Diffuse_Opaque_Doublesided": CreateMaterial_F7_30_97_BD(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Tunnel_Diffuse_Opaque_Singlesided": CreateMaterial_FF_3B_D3_06(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		#beta
		elif shaderDescription == "Road_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E_beta(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		#elif shaderDescription == "Road_Opaque_Singlesided": CreateMaterial_5D_C3_BE_4F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		#elif shaderDescription == "Road_Opaque_Singlesided": CreateMaterial_D4_90_D6_B8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Road_Opaque_Singlesided_Shadow": CreateMaterial_7B_7B_A2_8E_beta(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Building_1Bit_Singlesided": CreateMaterial_9F_D5_D8_48(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_FullyDamaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_FullyDamaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_PaintGloss_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_MetalFaded_Textured_EnvMapped":  CreateMaterial_A2_14_84_00(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_BodypartsSkin": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured": CreateMaterial_C4_E3_58_7A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Chrome": CreateMaterial_AD_23_5C_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_GreyScale_LightCover_Textured": CreateMaterial_33_0B_A4_5E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		#Glass material without blue tint used in traffic cars (by Piotrek)
		elif shaderDescription == "Vehicle_Greyscale_Window_Textured_Traffic": CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_WheelChrome_Textured": CreateMaterial_B4_A6_ED_D7(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_BackPanel": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		elif shaderDescription == "Vehicle_Opaque_Numberplate_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		else:
			if shaderDescription != "":
				#print("Material for Shader ", shaderDescription, " does not exist! Using a generic one.")
				logfile = os.path.join(os.path.dirname(srcPath),'log.txt')
				if not os.path.isfile(logfile):
					open(logfile, 'a').close()
				with open(logfile, 'r+') as log:
					text = "Missing material for Shader %s (TRK).\n" % shaderDescription
					if not any(text == line for line in log):
						log.write(text)
						log.write('[')
						for key in RasterDict:
							log.write(key + '  ')
						log.write(']\n')
				if shaderDescription.endswith("_Damaged"):
					shaderDescription = shaderDescription[:-8]
					MaterialName = CreateMaterial(srcPath,RenderableName,MaterialName_in,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version)
					return MaterialName
				elif shaderDescription.endswith("_Default"):
					shaderDescription = shaderDescription[:-8]
					MaterialName = CreateMaterial(srcPath,RenderableName,MaterialName_in,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version)
					return MaterialName
			CreateMaterialTRK(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "default":
		# CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "emissive":
		# CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "shiny":
		# CreateMaterialShiny(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "matte":
		# CreateMaterialMatte(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "chrome":
		# CreateMaterialChrome(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "tyre" or MaterialType == "tire":
		# CreateMaterialTyre(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "glass":
		# CreateMaterialGlass(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "transparent":
		# CreateMaterialTransparent(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	# elif MaterialType == "mirror":
		# CreateMaterialMirror(srcPath, MaterialName, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName)
	elif shaderDescription == "VideoWall_Diffuse_Opaque_Singlesided": CreateMaterial_19_6E_C7_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Chevron_Illuminated_Greyscale_Singlesided": CreateMaterial_1A_06_FF_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_DriveableSurface_Detailmap_Opaque_Singlesided": CreateMaterial_1B_D8_B8_27(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Cruciform_1Bit_Doublesided_Instanced": CreateMaterial_1F_DA_DF_6E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_BodypartsSkin_EnvMapped": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_1Bit_Tyre_Textured": CreateMaterial_2D_40_9E_05(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Livery_Alpha_CarGuts": CreateMaterial_31_8E_3B_9E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Greyscale_Window_Textured": CreateMaterial_33_0B_A4_5E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	#Glass material without blue tint used in traffic cars (by Piotrek)
	elif shaderDescription == "Vehicle_Greyscale_Window_Textured_Traffic": CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Vehicle_Greyscale_Headlight_Doublesided": CreateMaterial_34_11_6F_C8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "BuildingGlass_Transparent_Doublesided": CreateMaterial_35_91_5B_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Diffuse_Greyscale_Singlesided": CreateMaterial_36_9A_6B_40(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Diffuse_Opaque_Singlesided": CreateMaterial_37_C2_9A_C3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Cruciform_1Bit_Doublesided": CreateMaterial_37_E7_77_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Diffuse_1Bit_Doublesided": CreateMaterial_3C_A3_99_3E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_1Bit_Doublesided2": CreateMaterial_3D_C9_A3_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Gold_Illuminated_Reflective_Opaque_Singlesided": CreateMaterial_3F_28_A4_93(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Diffuse_Greyscale_Doublesided": CreateMaterial_42_73_1A_D2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Sign_Illuminance_Diffuse_Opaque_Singlesided": CreateMaterial_46_FB_C2_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tint_Specular_1Bit_Doublesided": CreateMaterial_49_3C_26_F6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Sign_Diffuse_Opaque_Singlesided": CreateMaterial_49_A7_17_A0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_Opaque_Singlesided": CreateMaterial_4B_D9_70_EA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Grass_Specular_Opaque_Singlesided": CreateMaterial_4D_7F_80_14(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tint_Building_Opaque_Singlesided": CreateMaterial_4E_83_F2_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_Decal_Textured_UVAnim": CreateMaterial_51_80_C9_2F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Livery_Alpha_CarGuts_Skin": CreateMaterial_56_60_98_39(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Building_Opaque_Singlesided": CreateMaterial_57_0B_99_65(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Decal_Textured_EnvMapped_PoliceLights": CreateMaterial_5D_1F_A9_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Road_Detailmap_Opaque_Singlesided": CreateMaterial_5D_C3_BE_4F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_1Bit_Singlesided2": CreateMaterial_65_25_EA_21(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_CarbonFibre_Textured": CreateMaterial_66_30_78_11(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "ShoreLine_Diffuse_Greyscale_Singlesided": CreateMaterial_66_63_5A_26(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_Greyscale_Singlesided": CreateMaterial_6B_A8_27_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Metal_Textured_Skin": CreateMaterial_6F_53_CC_FA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Terrain_Diffuse_Opaque_Singlesided": CreateMaterial_71_12_EC_98(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Water_Specular_Opaque_Singlesided": CreateMaterial_73_B0_DA_EC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PlasticMatt_Textured": CreateMaterial_78_CE_40_2C(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_WheelChrome_Textured_Illuminance": CreateMaterial_79_7D_2F_76(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Road_Detailmap_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Illuminance_Diffuse_1Bit_Doublesided": CreateMaterial_7C_C6_D3_1D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "MetalSheen_Opaque_Doublesided": CreateMaterial_7F_B8_3B_1A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_NormalMapped": CreateMaterial_82_DE_22_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "FlashingNeon_Diffuse_1Bit_Doublesided": CreateMaterial_86_6F_8D_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Building_Night_Opaque_Singlesided": CreateMaterial_89_41_8E_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BP"  and shaderDescription == "Building_Night_Opaque_Singlesided": CreateMaterial_57_0B_99_65(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			#"Building_Opaque_Singlesided"
	elif shaderDescription == "Foliage_1Bit_Doublesided": CreateMaterial_8A_88_2A_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PlasticMatt": CreateMaterial_8B_4D_5D_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Cable_GreyScale_Doublesided": CreateMaterial_93_5F_33_58(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Diffuse_Opaque_Doublesided": CreateMaterial_94_B4_DB_B5(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_Opaque_Singlesided2": CreateMaterial_95_66_1E_23(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured_Illuminance": CreateMaterial_98_98_75_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "Road_Night_Detailmap_Opaque_Singlesided": CreateMaterial_9E_FB_32_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BP"  and shaderDescription == "Road_Night_Detailmap_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			# "Road_Detailmap_Opaque_Singlesided"
	elif shaderDescription == "Diffuse_1Bit_Singlesided": CreateMaterial_9F_D5_D8_48(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_1Bit_MetalFaded_Textured_EnvMapped": CreateMaterial_A2_14_84_00(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_DetailMap_Opaque_Singlesided": CreateMaterial_A2_62_24_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_Reflective_Opaque_Singlesided2": CreateMaterial_A6_28_0B_CF(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tint_Specular_Opaque_Singlesided": CreateMaterial_AD_08_F1_AA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Chrome_Damaged": CreateMaterial_AD_23_5C_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_1Bit_Doublesided": CreateMaterial_AD_57_BF_E3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_Opaque_Doublesided": CreateMaterial_AE_B3_92_62(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Illuminance_Diffuse_Opaque_Singlesided": CreateMaterial_B0_1D_35_C6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Terrain_Specular_Opaque_Singlesided": CreateMaterial_B1_2C_80_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "DriveableSurface_Night_Detailmap_Opaque_Singlesided": CreateMaterial_B4_56_99_82(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BP"  and shaderDescription == "DriveableSurface_Night_Detailmap_Opaque_Singlesided": CreateMaterial_BD_2E_A8_C4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)									# "DriveableSurface_Detailmap_Opaque_Singlesided"
	elif shaderDescription == "Vehicle_Opaque_Metal_Textured": CreateMaterial_B4_A6_ED_D7(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Sign_Lightmap_Diffuse_Opaque_Singlesided": CreateMaterial_B6_7A_FA_60(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Glass_Specular_Transparent_Doublesided": CreateMaterial_B8_A1_8A_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_1Bit_Singlesided": CreateMaterial_B8_A5_9E_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Lightmap_Diffuse_Opaque_Singlesided": CreateMaterial_B9_E2_4F_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Sign_Specular_Opaque_Singlesided": CreateMaterial_BA_1F_F8_AC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "DriveableSurface_DetailMap_Diffuse_Opaque_Singlesided": CreateMaterial_BA_2E_9B_81(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "DriveableSurface_Detailmap_Opaque_Singlesided": CreateMaterial_BD_2E_A8_C4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BPR" and shaderDescription == "FlashingNeon_Diffuse_Opaque_Singlesided": CreateMaterial_C0_04_1A_37(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif game_version == "BP"  and shaderDescription == "FlashingNeon_Diffuse_Opaque_Singlesided": CreateMaterial_86_6F_8D_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)			# "FlashingNeon_Diffuse_1Bit_Doublesided"
	elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured_Damaged": CreateMaterial_C4_E3_58_7A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_Light_Textured_EnvMapped": CreateMaterial_C4_E4_B3_99(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Sign_Diffuse_1Bit_Singlesided": CreateMaterial_C5_1D_C5_57(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Specular_Greyscale_Doublesided": CreateMaterial_C7_1B_BF_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Illuminance_Diffuse_1Bit_Singlesided": CreateMaterial_D0_75_4B_DF(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_SimpleMetal_Textured": CreateMaterial_D2_CE_2F_51(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_Opaque_Doublesided2": CreateMaterial_D2_FB_F8_AB(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Lightmapped_Road_Detailmap_Opaque_Singlesided2": CreateMaterial_D4_90_D6_B8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_NormalMap_SpecMap_Skin": CreateMaterial_D9_7E_0C_84(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_Traffic": CreateMaterial_DB_62_6A_AE(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Decal_Textured_EnvMapped": CreateMaterial_E1_C4_7C_19(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_Decal_Textured": CreateMaterial_EA_27_69_B4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "CarStudio_DoNotShipWithThisInTheGame": CreateMaterial_EB_BF_C4_9D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Diffuse_Opaque_Doublesided": CreateMaterial_F7_30_97_BD(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Tunnel_Diffuse_Opaque_Singlesided": CreateMaterial_FF_3B_D3_06(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	#beta
	elif shaderDescription == "Road_Opaque_Singlesided": CreateMaterial_7B_7B_A2_8E_beta(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Road_Opaque_Singlesided_Shadow": CreateMaterial_7B_7B_A2_8E_beta(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Building_1Bit_Singlesided": CreateMaterial_9F_D5_D8_48(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_FullyDamaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Textured_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_FullyDamaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_PaintGloss_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_MetalFaded_Textured_EnvMapped":  CreateMaterial_A2_14_84_00(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_BodypartsSkin": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_WheelChrome_Textured": CreateMaterial_C4_E3_58_7A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Chrome": CreateMaterial_AD_23_5C_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_GreyScale_LightCover_Textured": CreateMaterial_33_0B_A4_5E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	#Glass material without blue tint used in traffic cars (by Piotrek)
	elif shaderDescription == "Vehicle_Greyscale_Window_Textured_Traffic": CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_WheelChrome_Textured": CreateMaterial_B4_A6_ED_D7(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_BackPanel": CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "Vehicle_Opaque_Numberplate_Damaged": CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "default_DGI" or MaterialType == "default":
		CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "emissive_DGI" or MaterialType == "emissive":
		CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "shiny_DGI" or MaterialType == "shiny":
		CreateMaterialShiny(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "matte_DGI" or MaterialType == "matte":
		CreateMaterialMatte(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "chrome_DGI" or MaterialType == "chrome":
		CreateMaterialChrome(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "tyre_DGI" or MaterialType == "tyre" or MaterialType == "tire":
		CreateMaterialTyre(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "glass_DGI" or MaterialType == "glass":
		CreateMaterialGlass(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "glass_traffic" or MaterialType == "glass-traffic" or MaterialType == "traffic-glass":
		CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "transparent_DGI" or MaterialType == "transparent":
		CreateMaterialTransparent(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	elif shaderDescription == "mirror_DGI" or MaterialType == "mirror":
		CreateMaterialMirror(srcPath, MaterialName, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName)
	else:
		#CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
		if shaderDescription != "":
			logfile = os.path.join(os.path.dirname(srcPath),'log.txt')
			if not os.path.isfile(logfile):
				open(logfile, 'a').close()
			with open(logfile, 'r+') as log:
				text = "Missing material for Shader %s (VEH).\n" % shaderDescription
				if not any(text == line for line in log):
					log.write(text)
					log.write('[')
					for key in RasterDict:
						log.write(key + '  ')
					log.write(']\n')
			if shaderDescription.endswith("_Damaged"):
				shaderDescription = shaderDescription[:-8]
				MaterialName = CreateMaterial(srcPath,RenderableName,MaterialName_in,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version)
				return MaterialName
			elif shaderDescription.endswith("_Default"):
				shaderDescription = shaderDescription[:-8]
				MaterialName = CreateMaterial(srcPath,RenderableName,MaterialName_in,shaderDescription,MaterialDict,RasterDict,IDsList,world,vehicleName,verify_genericIDs,use_UniqueIDs,game_version)
				return MaterialName
		CreateMaterialShiny(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version)
	if add_to_dict == True:
		MaterialDict[MaterialName] = shaderDescription
	return MaterialName

def CreateMaterialDefaultEmissive(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDNormal = ''
	RasterIDSpecular = ''
	RasterIDEmissive = ''
	RasterIDAoMap = ''
	RasterIDCrumple = ''
	RasterIDScratch = ''
	RasterIDLineMap = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'Normal' in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict['Normal']
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	if 'Specular' in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict['Specular']
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	if 'Emissive' in RasterDict:
		RasterIDEmissive, RasterPathEmissive = RasterDict['Emissive']
		RasterIDEmissive, isEmissiveGeneric = VerifyGenericIDs(game_version,RasterIDEmissive,verify_genericIDs)
	if 'AoMap' in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict['AoMap']
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	if 'Crumple' in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict['Crumple']
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	if 'Scratch' in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict['Scratch']
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	if 'LineMap' in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict['LineMap']
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x03\x03\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xE8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x04\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x09\x01\x00\x00')
		OutMaterial.write(b'\xF3\x84\x27\xA7\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x02\x00\x00\x00\x30\x01\x00\x00\x38\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3E\x00\x00\x80\x3E')
		OutMaterial.write(b'\x00\x00\x00\x43\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xE1\xC4\x7C\x19\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(b'\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(b'\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict['Normal'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDEmissive != '' and RasterIDEmissive != '00_00_00_00':
			TexStateEmissive = StringToID(RasterDict['Emissive'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			IDsList[TexStateEmissive] = 'TextureState'
			CreateTextureState(game_version, srcPath, TexStateEmissive, RasterIDEmissive)
			if isEmissiveGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDEmissive, RasterPathEmissive)
				IDsList[RasterIDEmissive] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateEmissive.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialShiny(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDAoMap = ''
	RasterIDCrumple = ''
	RasterIDScratch = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'AoMap' in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict['AoMap']
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	if 'Crumple' in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict['Crumple']
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	if 'Scratch' in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict['Scratch']
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x04\x04\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x38\x01\x00\x00\x48\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xF4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x18\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x29\x01\x00\x00\x32\x7E\x2A\x8F')
		OutMaterial.write(b'\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2E\x01\x00\x00')
		OutMaterial.write(b'\xE2\xC4\x97\x00\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x33\x01\x00\x00\xD5\x86\xF9\x99\x05\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x58\x01\x00\x00')
		OutMaterial.write(b'\x68\x01\x00\x00\xC0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\xB0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3F\x33\x33\x93\x3F\x0A\xD7\x23\x3E\x00\x00\x40\x3F')
		OutMaterial.write(b'\x66\x66\xA6\x3F\x66\x66\xA6\x3F\x00\x00\x00\x00\xCD\xCC\xCC\x3D')
		OutMaterial.write(b'\x00\x00\xC0\x40\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xD7\xA3\x70\x3F\x00\x00\x80\x41\x00\x00\x40\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xF5\x43\x09\x11')
		OutMaterial.write(b'\x8A\xA0\xFC\x56\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict['AoMap'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			OutMaterial.write(b'\x57\x48\x54\x45')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict['Crumple'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict['Scratch'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialMatte(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDNormal = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'Normal' in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict['Normal']
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x33\x33\x3F\x33\x33\x33\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\xC8\x41\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xC3\x4E\x6C\x3E\x4D\xF1\x5D\x3E\xDF\xAE\x3A\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xB4\xA6\xED\xD7\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict['Normal'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialChrome(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDCrumple = ''
	RasterIDScratch = ''
	if 'Crumple' in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict['Crumple']
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	if 'Scratch' in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict['Scratch']
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x08\x01\x00\x00\x18\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xD6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xE2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xEE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xFA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFC\x00\x00\x00\xE2\xC4\x97\x00\x02\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x01\x01\x00\x00\xD5\x86\xF9\x99')
		OutMaterial.write(b'\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x28\x01\x00\x00')
		OutMaterial.write(b'\x3C\x01\x00\x00\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x80\x3E\x33\x33\xB3\x3F')
		OutMaterial.write(b'\x66\x66\xE6\x3F\x00\x00\x00\x40\x00\x00\x00\x00\xCD\xCC\x4C\x3E')
		OutMaterial.write(b'\x00\x00\xF0\x42\x00\x00\x00\x40\xCD\xCC\xCC\x3E\x00\x00\x00\x40')
		OutMaterial.write(b'\x33\x33\x73\x3F\x00\x00\x20\x41\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x65\xCD\xE6\x3E\x65\xCD\xE6\x3E\x65\xCD\xE6\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xF5\x43\x09\x11')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xAD\x23\x5C\x6B\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict['Crumple'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict['Scratch'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialTyre(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDNormal = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'Normal' in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict['Normal']
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x03\x03\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x1C\x01\x00\x00\x2C\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xE6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xEC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xF2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xF8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xFE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x04\x01\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\x0A\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x0D\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x12\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x17\x01\x00\x00')
		OutMaterial.write(b'\xF3\x84\x27\xA7\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		OutMaterial.write(b'\x3C\x01\x00\x00\x48\x01\x00\x00\x90\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9A\x99\x99\x3D\x00\x00\xA0\x3E\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\xE1\xC4\x7C\x19')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0x10))
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0x24))
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0x44))
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0x64))
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0x84))
		OutMaterial.write(struct.pack("<i", 0))
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict['Normal'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(struct.pack("<i", 0))
		OutMaterial.write(struct.pack("<i", 0xDC))
		OutMaterial.write(struct.pack("<i", 0))

def CreateMaterialGlass(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x01\x01\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\x98\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\x9E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xA8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x33\x33\x33\x3E\x66\x66\x66\x3F')
		OutMaterial.write(b'\x00\x00\x96\x43\x00\x00\x80\x40\x00\x00\x00\x3F\x66\x66\xA6\x3F')
		OutMaterial.write(b'\x00\x00\x00\x00\xDE\xF8\x90\x3E\x89\x18\x78\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x0B\xA4\x5E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4')
		OutMaterial.write(b'\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4')
		OutMaterial.write(b'\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialTransparent(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDNormal = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'Normal' in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict['Normal']
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xEA\x27\x69\xB4\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict['Normal'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialMirror(srcPath, MaterialName, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName):
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x01\x01\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\x98\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\x9E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xA8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x00\x43\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x70\xF9\x16\x3E\xEB\xC4\x6E\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x0B\xA4\x5E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x52\x76\xAE\x90\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialTRK(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	RasterIDSpecular = ''
	if 'Diffuse' in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict['Diffuse']
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	if 'Specular' in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict['Specular']
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	#RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	#RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x17\xD9\x4E\x3F\xC1\x1F\x3E\x3F\x64\x79\x37\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x4B\xD9\x70\xEA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict['Diffuse'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')		#Diffuse
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict['Specular'][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')		#Specular

## VEHICLE MATERIALS FOR EACH VEHICLE SHADER

def CreateMaterial_2D_40_9E_05(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDBlurDiffuse = ''
	if "BlurDiffuse" in RasterDict:
		RasterIDBlurDiffuse, RasterPathBlurDiffuse = RasterDict["BlurDiffuse"]
		RasterIDBlurDiffuse, isBlurDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDBlurDiffuse,verify_genericIDs)
	RasterIDBlurDiffuse = StringToID(RasterIDBlurDiffuse, use_UniqueIDs, vehicleName)
	RasterIDBlurNormal = ''
	if "BlurNormal" in RasterDict:
		RasterIDBlurNormal, RasterPathBlurNormal = RasterDict["BlurNormal"]
		RasterIDBlurNormal, isBlurNormalGeneric = VerifyGenericIDs(game_version,RasterIDBlurNormal,verify_genericIDs)
	RasterIDBlurNormal = StringToID(RasterIDBlurNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x04\x04\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x0C\x01\x00\x00\x1C\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA9\xBB\xD4\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x04\x00\x00\x00\xDA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x04\x00\x00\x00\xE6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xEC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x04\x00\x00\x00\xF2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xF6\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFB\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x00\x01\x00\x00')
		OutMaterial.write(b'\xCB\x53\x4D\xA6\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x05\x01\x00\x00\xDB\x28\x38\x1B\x04\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00')
		OutMaterial.write(b'\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		OutMaterial.write(b'\x2C\x01\x00\x00\x38\x01\x00\x00\x80\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x00\x42\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x2D\x40\x9E\x05\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurDiffuse != '' and RasterIDBlurDiffuse != '00_00_00_00':
			TexStateBlurDiffuse = StringToID(RasterDict["BlurDiffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurDiffuse, RasterIDBlurDiffuse)
			IDsList[TexStateBlurDiffuse] = 'TextureState'
			if isBlurDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurDiffuse, RasterPathBlurDiffuse)
				IDsList[RasterIDBlurDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurNormal != '' and RasterIDBlurNormal != '00_00_00_00':
			TexStateBlurNormal = StringToID(RasterDict["BlurNormal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurNormal, RasterIDBlurNormal)
			IDsList[TexStateBlurNormal] = 'TextureState'
			if isBlurNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurNormal, RasterPathBlurNormal)
				IDsList[RasterIDBlurNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurNormal.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_66_30_78_11(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xF8\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\xD2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD4\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\xDA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xDC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\xE2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\xEA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEC\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xF1\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x18\x01\x00\x00')
		OutMaterial.write(b'\x24\x01\x00\x00\x60\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x66\x66\x26\x3F\x00\x00\x80\x3F\xCD\xCC\x4C\x3D\xCD\xCC\xCC\x3E')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x66\x30\x78\x11\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_31_8E_3B_9E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x01\x01\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xB8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xBE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xC6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xC8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xCE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xD0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xD6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD7\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		OutMaterial.write(b'\xFC\x00\x00\x00\x08\x01\x00\x00\x50\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x20\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x40\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x00\x42\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xF9\x96\x6F\x3F\x00\x00\x80\x3F\xB9\xA2\x75\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x31\x8E\x3B\x9E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_5D_1F_A9_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDEmissive = ''
	if "Emissive" in RasterDict:
		RasterIDEmissive, RasterPathEmissive = RasterDict["Emissive"]
		RasterIDEmissive, isEmissiveGeneric = VerifyGenericIDs(game_version,RasterIDEmissive,verify_genericIDs)
	RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x03\x03\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xE8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x04\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x09\x01\x00\x00')
		OutMaterial.write(b'\xF3\x84\x27\xA7\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x02\x00\x00\x00\x30\x01\x00\x00\x38\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x43\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x5D\x1F\xA9\x50\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			#  if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDEmissive != '' and RasterIDEmissive != '00_00_00_00':
			TexStateEmissive = StringToID(RasterDict["Emissive"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateEmissive, RasterIDEmissive)
			IDsList[TexStateEmissive] = 'TextureState'
			if isEmissiveGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDEmissive, RasterPathEmissive)
				IDsList[RasterIDEmissive] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateEmissive.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_A2_14_84_00(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x33\x33\x3F\x33\x33\x33\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\xC8\x41\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xC3\x4E\x6C\x3E\x4D\xF1\x5D\x3E\xDF\xAE\x3A\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xA2\x14\x84\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_78_CE_40_2C(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDAoMap = ''
	if "AoMap" in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict["AoMap"]
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDCrumple = ''
	if "Crumple" in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict["Crumple"]
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = ''
	if "Scratch" in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict["Scratch"]
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x04\x04\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x38\x01\x00\x00\x48\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xF4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x18\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x29\x01\x00\x00\x32\x7E\x2A\x8F')
		OutMaterial.write(b'\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2E\x01\x00\x00')
		OutMaterial.write(b'\xE2\xC4\x97\x00\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x33\x01\x00\x00\xD5\x86\xF9\x99\x05\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x58\x01\x00\x00')
		OutMaterial.write(b'\x68\x01\x00\x00\xC0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\xB0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x78\xCE\x40\x2C\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			OutMaterial.write(b'\x57\x48\x54\x45')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict["Crumple"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict["Scratch"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_C4_E3_58_7A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDBlurDiffuse = ''
	if "BlurDiffuse" in RasterDict:
		RasterIDBlurDiffuse, RasterPathBlurDiffuse = RasterDict["BlurDiffuse"]
		RasterIDBlurDiffuse, isBlurDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDBlurDiffuse,verify_genericIDs)
	RasterIDBlurDiffuse = StringToID(RasterIDBlurDiffuse, use_UniqueIDs, vehicleName)
	RasterIDBlurNormal = ''
	if "BlurNormal" in RasterDict:
		RasterIDBlurNormal, RasterPathBlurNormal = RasterDict["BlurNormal"]
		RasterIDBlurNormal, isBlurNormalGeneric = VerifyGenericIDs(game_version,RasterIDBlurNormal,verify_genericIDs)
	RasterIDBlurNormal = StringToID(RasterIDBlurNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x04\x04\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x0C\x01\x00\x00\x1C\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA9\xBB\xD4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xE8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xEC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xF8\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFD\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x02\x01\x00\x00')
		OutMaterial.write(b'\xCB\x53\x4D\xA6\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x07\x01\x00\x00\xDB\x28\x38\x1B\x04\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00')
		OutMaterial.write(b'\x2C\x01\x00\x00\x3C\x01\x00\x00\x90\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\xC0\x3F\x00\x00\x00\x00\xCD\xCC\x4C\x3E')
		OutMaterial.write(b'\x00\x00\x34\x42\x9A\x99\x99\x3F\x33\x33\x33\x3F\x00\x00\x00\x40')
		OutMaterial.write(b'\xEE\x7C\x7F\x3F\x00\x00\x20\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xC4\xE3\x58\x7A\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurDiffuse != '' and RasterIDBlurDiffuse != '00_00_00_00':
			TexStateBlurDiffuse = StringToID(RasterDict["BlurDiffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurDiffuse, RasterIDBlurDiffuse)
			IDsList[TexStateBlurDiffuse] = 'TextureState'
			if isBlurDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurDiffuse, RasterPathBlurDiffuse)
				IDsList[RasterIDBlurDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurNormal != '' and RasterIDBlurNormal != '00_00_00_00':
			TexStateBlurNormal = StringToID(RasterDict["BlurNormal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurNormal, RasterIDBlurNormal)
			IDsList[TexStateBlurNormal] = 'TextureState'
			if isBlurNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurNormal, RasterPathBlurNormal)
				IDsList[RasterIDBlurNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurNormal.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_33_0B_A4_5E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x01\x01\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\x98\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\x9E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xA8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x33\x33\x33\x3E\x66\x66\x66\x3F')
		OutMaterial.write(b'\x00\x00\x96\x43\x00\x00\x80\x40\x00\x00\x00\x3F\x66\x66\xA6\x3F')
		OutMaterial.write(b'\x00\x00\x00\x00\xDE\xF8\x90\x3E\x89\x18\x78\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x0B\xA4\x5E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')

#Glass material without blue tint used in traffic cars
def CreateMaterial_33_0B_A4_5E_v2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x01\x01\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\x98\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\x9E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xA8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x33\x33\x33\x3E\x66\x66\x66\x3F')
		OutMaterial.write(b'\x00\x00\x96\x43\x00\x00\x80\x40\x9A\x99\x99\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x1B\x5D\xEA\x3D\x10\x8F\x19\x3E\x32\xAB\x1F\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x0B\xA4\x5E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEC\x4F\x6F\xB4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_56_60_98_39(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x01\x01\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\x98\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\x9E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA1\x40\xA8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\xCC\x3D\x9A\x99\x99\x3E\x00\x00\x40\x3F\xCD\xCC\x4C\x3F')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\x56\x60\x98\x39\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_D2_CE_2F_51(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x01\x01\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xB8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xBE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xC6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xC8\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xCE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xD0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x01\x00\x00\x00\xD6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD7\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		OutMaterial.write(b'\xFC\x00\x00\x00\x08\x01\x00\x00\x50\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x20\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x40\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x70\x41\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xAA\x7C\xE2\xF6\x00\x00\x00\x00')
		OutMaterial.write(b'\xD2\xCE\x2F\x51\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_DB_62_6A_AE(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDAoMap = ''
	if "AoMap" in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict["AoMap"]
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDCrumple = ''
	if "Crumple" in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict["Crumple"]
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = ''
	if "Scratch" in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict["Scratch"]
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x04\x04\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x38\x01\x00\x00\x48\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xF4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x18\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x29\x01\x00\x00\x32\x7E\x2A\x8F')
		OutMaterial.write(b'\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2E\x01\x00\x00')
		OutMaterial.write(b'\xE2\xC4\x97\x00\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x33\x01\x00\x00\xD5\x86\xF9\x99\x05\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x58\x01\x00\x00')
		OutMaterial.write(b'\x68\x01\x00\x00\xC0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\xB0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3F\x33\x33\x93\x3F\xCD\xCC\x4C\x3D\x00\x00\x80\x3E')
		OutMaterial.write(b'\x66\x66\xA6\x3F\x66\x66\xA6\x3F\x00\x00\x00\x00\xCD\xCC\xCC\x3D')
		OutMaterial.write(b'\x00\x00\x88\x42\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xD7\xA3\x70\x3F\x00\x00\x80\x41\xCD\xCC\xCC\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xF5\x43\x09\x11')
		OutMaterial.write(b'\xDB\x62\x6A\xAE\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			#  if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			OutMaterial.write(b'\x57\x48\x54\x45')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict["Crumple"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict["Scratch"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_21_6D_2C_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x01\x01\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xB8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x01\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x01\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xC8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x01\x00\x00\x00\xCC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xD0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x01\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD5\x00\x00\x00\x6F\x74\x15\x3E\x02\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00')
		OutMaterial.write(b'\xFC\x00\x00\x00\x04\x01\x00\x00\x30\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x00\x3F\xCD\xCC\xCC\x3D\xCD\xCC\xCC\x3D')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x21\x6D\x2C\x08\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_D9_7E_0C_84(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDSpecularMap = ''
	if "SpecularMap" in RasterDict:
		RasterIDSpecularMap, RasterPathSpecularMap = RasterDict["SpecularMap"]
		RasterIDSpecularMap, isSpecularMapGeneric = VerifyGenericIDs(game_version,RasterIDSpecularMap,verify_genericIDs)
	RasterIDSpecularMap = StringToID(RasterIDSpecularMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x03\x03\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE8\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xC0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xCC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA1\x40\xD0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD7\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xDC\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xE1\x00\x00\x00')
		OutMaterial.write(b'\xFB\xC4\xB9\xE8\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x08\x01\x00\x00')
		OutMaterial.write(b'\x10\x01\x00\x00\x40\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x30\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\xC0\x3F\x00\x00\x40\x3F\xCD\xCC\x4C\x3F')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x00\x40')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xD9\x7E\x0C\x84\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecularMap != '' and RasterIDSpecularMap != '00_00_00_00':
			TexStateSpecularMap = StringToID(RasterDict["SpecularMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecularMap, RasterIDSpecularMap)
			IDsList[TexStateSpecularMap] = 'TextureState'
			if isSpecularMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecularMap, RasterPathSpecularMap)
				IDsList[RasterIDSpecularMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecularMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_C4_E4_B3_99(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x40\x3F\x00\x00\x00\x40\xCD\xCC\x4C\x3D\x9A\x99\x19\x3F')
		OutMaterial.write(b'\x00\x00\x00\x43\x9A\x99\xD9\x3F\x33\x33\x33\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xC9\x76\x7E\x3F\x00\x00\x20\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xC4\xE4\xB3\x99\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_51_80_C9_2F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3E\x33\x33\xB3\x3E\xCD\xCC\x4C\x3D\x29\x5C\x8F\x3D')
		OutMaterial.write(b'\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F\xCD\xCC\xCC\x3E')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x9A\x99\x19\x3E\x9A\x99\x19\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x51\x80\xC9\x2F\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_EA_27_69_B4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xEA\x27\x69\xB4\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_6F_53_CC_FA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDSpecularMap = ''
	if "SpecularMap" in RasterDict:
		RasterIDSpecularMap, RasterPathSpecularMap = RasterDict["SpecularMap"]
		RasterIDSpecularMap, isSpecularMapGeneric = VerifyGenericIDs(game_version,RasterIDSpecularMap,verify_genericIDs)
	RasterIDSpecularMap = StringToID(RasterIDSpecularMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x03\x03\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xF4\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xC0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA1\x40\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE3\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xE8\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xED\x00\x00\x00')
		OutMaterial.write(b'\xFB\xC4\xB9\xE8\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x14\x01\x00\x00\x24\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\xCD\xCC\xCC\x3D\x9A\x99\x99\x3E')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x80\x3F\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x6F\x53\xCC\xFA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecularMap != '' and RasterIDSpecularMap != '00_00_00_00':
			TexStateSpecularMap = StringToID(RasterDict["SpecularMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecularMap, RasterIDSpecularMap)
			IDsList[TexStateSpecularMap] = 'TextureState'
			if isSpecularMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecularMap, RasterPathSpecularMap)
				IDsList[RasterIDSpecularMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecularMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B4_A6_ED_D7(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x01\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x02\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x04\x00\x00\x00\x24\x01\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x33\x33\x33\x3F\x33\x33\x33\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\xC8\x41\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xC3\x4E\x6C\x3E\x4D\xF1\x5D\x3E\xDF\xAE\x3A\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\xB4\xA6\xED\xD7\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_AD_23_5C_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDCrumple = ''
	if "Crumple" in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict["Crumple"]
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = ''
	if "Scratch" in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict["Scratch"]
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x02\x02\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x08\x01\x00\x00\x18\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xCC\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xD6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xD8\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xE2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xEE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x02\x00\x00\x00\xFA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFC\x00\x00\x00\xE2\xC4\x97\x00\x02\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x01\x01\x00\x00\xD5\x86\xF9\x99')
		OutMaterial.write(b'\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x28\x01\x00\x00')
		OutMaterial.write(b'\x3C\x01\x00\x00\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x00\x40\x00\x00\x80\x3E\x33\x33\xB3\x3F')
		OutMaterial.write(b'\x66\x66\xE6\x3F\x00\x00\x00\x40\x00\x00\x00\x00\xCD\xCC\x4C\x3E')
		OutMaterial.write(b'\x00\x00\xF0\x42\x00\x00\x00\x40\xCD\xCC\xCC\x3E\x00\x00\x00\x40')
		OutMaterial.write(b'\x33\x33\x73\x3F\x00\x00\x20\x41\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x65\xCD\xE6\x3E\x65\xCD\xE6\x3E\x65\xCD\xE6\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xF5\x43\x09\x11')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xAD\x23\x5C\x6B\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict["Crumple"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict["Scratch"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_8A_A0_FC_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDAoMap = ''
	if "AoMap" in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict["AoMap"]
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDCrumple = ''
	if "Crumple" in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict["Crumple"]
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = ''
	if "Scratch" in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict["Scratch"]
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x04\x04\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x38\x01\x00\x00\x48\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xF4\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x08\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x18\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x04\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x24\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x29\x01\x00\x00\x32\x7E\x2A\x8F')
		OutMaterial.write(b'\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2E\x01\x00\x00')
		OutMaterial.write(b'\xE2\xC4\x97\x00\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x33\x01\x00\x00\xD5\x86\xF9\x99\x05\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x58\x01\x00\x00')
		OutMaterial.write(b'\x68\x01\x00\x00\xC0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\xB0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3F\x33\x33\x93\x3F\x0A\xD7\x23\x3E\x00\x00\x40\x3F')
		OutMaterial.write(b'\x66\x66\xA6\x3F\x66\x66\xA6\x3F\x00\x00\x00\x00\xCD\xCC\xCC\x3D')
		OutMaterial.write(b'\x00\x00\xC0\x40\x00\x00\x00\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xD7\xA3\x70\x3F\x00\x00\x80\x41\x00\x00\x40\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xF5\x43\x09\x11')
		OutMaterial.write(b'\x8A\xA0\xFC\x56\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# if game_version == "BPR":
			# 	OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			# elif game_version == "BP":
			# 	OutMaterial.write(b'\x96\xF5\xE3\x08')
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			OutMaterial.write(b'\x57\x48\x54\x45')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict["Crumple"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict["Scratch"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_E1_C4_7C_19(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDEmissive = ''
	if "Emissive" in RasterDict:
		RasterIDEmissive, RasterPathEmissive = RasterDict["Emissive"]
		RasterIDEmissive, isEmissiveGeneric = VerifyGenericIDs(game_version,RasterIDEmissive,verify_genericIDs)
	RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x03\x03\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xE8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xEC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\xF8\x00\x00\x00')
		OutMaterial.write(b'\x00\x02\x00\x00\x03\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x04\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x09\x01\x00\x00')
		OutMaterial.write(b'\xF3\x84\x27\xA7\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x02\x00\x00\x00\x30\x01\x00\x00\x38\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3E\x00\x00\x80\x3E')
		OutMaterial.write(b'\x00\x00\x00\x43\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xE1\xC4\x7C\x19\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		# if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			# TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			# CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			# IDsList[TexStateReflection] = 'TextureState'
			# if isReflectionGeneric == False or use_UniqueIDs == True:
				# CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				# IDsList[RasterIDReflection] = 'Raster'
			# OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		# else:
			# #OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			# OutMaterial.write(b'\x12\x6C\x5E\xD3')		#2F_A3_8A_82 is a grey shader texture
		# OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDEmissive != '' and RasterIDEmissive != '00_00_00_00':
			TexStateEmissive = StringToID(RasterDict["Emissive"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateEmissive, RasterIDEmissive)
			IDsList[TexStateEmissive] = 'TextureState'
			if isEmissiveGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDEmissive, RasterPathEmissive)
				IDsList[RasterIDEmissive] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateEmissive.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_8B_4D_5D_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDAoMap = ''
	if "AoMap" in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict["AoMap"]
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDCrumple = ''
	if "Crumple" in RasterDict:
		RasterIDCrumple, RasterPathCrumple = RasterDict["Crumple"]
		RasterIDCrumple, isCrumpleGeneric = VerifyGenericIDs(game_version,RasterIDCrumple,verify_genericIDs)
	RasterIDCrumple = StringToID(RasterIDCrumple, use_UniqueIDs, vehicleName)
	RasterIDScratch = ''
	if "Scratch" in RasterDict:
		RasterIDScratch, RasterPathScratch = RasterDict["Scratch"]
		RasterIDScratch, isScratchGeneric = VerifyGenericIDs(game_version,RasterIDScratch,verify_genericIDs)
	RasterIDScratch = StringToID(RasterIDScratch, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x04\x03\x03\x00\xA4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x20\x01\x00\x00\x30\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x60\xAD\xE0\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\xE8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xEC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xF8\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0B\xC7\x04\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x03\x00\x00\x00\x0C\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x0F\x01\x00\x00\x32\x7E\x2A\x8F\x03\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x14\x01\x00\x00\xE2\xC4\x97\x00')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x19\x01\x00\x00')
		OutMaterial.write(b'\xD5\x86\xF9\x99\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x04\x00\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\xA0\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00')
		OutMaterial.write(b'\xCD\xCC\xCC\x3E\xCD\xCC\xCC\x3E\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\xCC\x3E\xCD\xCC\xCC\x3E\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xCD\xCC\xCC\x3D\xCD\xCC\xCC\x3D\xCD\xCC\xCC\x3D\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\xE6\xAB\xBB\xFF\x04\x50\xED\xAA\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x8B\x4D\x5D\x01\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			OutMaterial.write(b'\x57\x48\x54\x45')
		OutMaterial.write(b'\x00\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDCrumple != '' and RasterIDCrumple != '00_00_00_00':
			TexStateCrumple = StringToID(RasterDict["Crumple"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateCrumple, RasterIDCrumple)
			IDsList[TexStateCrumple] = 'TextureState'
			if isCrumpleGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDCrumple, RasterPathCrumple)
				IDsList[RasterIDCrumple] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateCrumple.replace('_', '')))
		else:
			OutMaterial.write(b'\xF5\xA1\x4F\xDD')
		OutMaterial.write(b'\x00\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDScratch != '' and RasterIDScratch != '00_00_00_00':
			TexStateScratch = StringToID(RasterDict["Scratch"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateScratch, RasterIDScratch)
			IDsList[TexStateScratch] = 'TextureState'
			if isScratchGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDScratch, RasterPathScratch)
				IDsList[RasterIDScratch] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateScratch.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')

## OTHER MATERIALS FOR EACH SHADER

def CreateMaterial_79_7D_2F_76(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDBlurDiffuse = ''
	if "BlurDiffuse" in RasterDict:
		RasterIDBlurDiffuse, RasterPathBlurDiffuse = RasterDict["BlurDiffuse"]
		RasterIDBlurDiffuse, isBlurDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDBlurDiffuse,verify_genericIDs)
	RasterIDBlurDiffuse = StringToID(RasterIDBlurDiffuse, use_UniqueIDs, vehicleName)
	RasterIDBlurNormal = ''
	if "BlurNormal" in RasterDict:
		RasterIDBlurNormal, RasterPathBlurNormal = RasterDict["BlurNormal"]
		RasterIDBlurNormal, isBlurNormalGeneric = VerifyGenericIDs(game_version,RasterIDBlurNormal,verify_genericIDs)
	RasterIDBlurNormal = StringToID(RasterIDBlurNormal, use_UniqueIDs, vehicleName)
	RasterIDEmissive = ''
	if "Emissive" in RasterDict:
		RasterIDEmissive, RasterPathEmissive = RasterDict["Emissive"]
		RasterIDEmissive, isEmissiveGeneric = VerifyGenericIDs(game_version,RasterIDEmissive,verify_genericIDs)
	RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x06\x06\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x48\x01\x00\x00\x58\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA9\xBB\xFC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x1C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x24\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x2A\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2F\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x34\x01\x00\x00')
		OutMaterial.write(b'\xCB\x53\x4D\xA6\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x39\x01\x00\x00\xDB\x28\x38\x1B\x04\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\x3E\x01\x00\x00\xF3\x84\x27\xA7\x05\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x43\x01\x00\x00\xBD\xD7\x53\x45')
		OutMaterial.write(b'\x06\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x68\x01\x00\x00')
		OutMaterial.write(b'\x78\x01\x00\x00\xD0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x90\x01\x00\x00\xA0\x01\x00\x00')
		OutMaterial.write(b'\xB0\x01\x00\x00\xC0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x40\x3F\x00\x00\xC0\x3F\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x34\x42\x00\x00\x80\x3F\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x40\x41\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x79\x7D\x2F\x76\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurDiffuse != '' and RasterIDBlurDiffuse != '00_00_00_00':
			TexStateBlurDiffuse = StringToID(RasterDict["BlurDiffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurDiffuse, RasterIDBlurDiffuse)
			IDsList[TexStateBlurDiffuse] = 'TextureState'
			if isBlurDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurDiffuse, RasterPathBlurDiffuse)
				IDsList[RasterIDBlurDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurNormal != '' and RasterIDBlurNormal != '00_00_00_00':
			TexStateBlurNormal = StringToID(RasterDict["BlurNormal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurNormal, RasterIDBlurNormal)
			IDsList[TexStateBlurNormal] = 'TextureState'
			if isBlurNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurNormal, RasterPathBlurNormal)
				IDsList[RasterIDBlurNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDEmissive != '' and RasterIDEmissive != '00_00_00_00':
			TexStateEmissive = StringToID(RasterDict["Emissive"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateEmissive, RasterIDEmissive)
			IDsList[TexStateEmissive] = 'TextureState'
			if isEmissiveGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDEmissive, RasterPathEmissive)
				IDsList[RasterIDEmissive] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateEmissive.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_98_98_75_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDBlurDiffuse = ''
	if "BlurDiffuse" in RasterDict:
		RasterIDBlurDiffuse, RasterPathBlurDiffuse = RasterDict["BlurDiffuse"]
		RasterIDBlurDiffuse, isBlurDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDBlurDiffuse,verify_genericIDs)
	RasterIDBlurDiffuse = StringToID(RasterIDBlurDiffuse, use_UniqueIDs, vehicleName)
	RasterIDBlurNormal = ''
	if "BlurNormal" in RasterDict:
		RasterIDBlurNormal, RasterPathBlurNormal = RasterDict["BlurNormal"]
		RasterIDBlurNormal, isBlurNormalGeneric = VerifyGenericIDs(game_version,RasterIDBlurNormal,verify_genericIDs)
	RasterIDBlurNormal = StringToID(RasterIDBlurNormal, use_UniqueIDs, vehicleName)
	RasterIDEmissive = ''
	if "Emissive" in RasterDict:
		RasterIDEmissive, RasterPathEmissive = RasterDict["Emissive"]
		RasterIDEmissive, isEmissiveGeneric = VerifyGenericIDs(game_version,RasterIDEmissive,verify_genericIDs)
	RasterIDEmissive = StringToID(RasterIDEmissive, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x03\x06\x06\x00\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x48\x01\x00\x00\x58\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xA9\xBB\xFC\x00\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x0C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x14\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x1C\x01\x00\x00')
		OutMaterial.write(b'\x00\x04\x00\x00\x06\x00\x00\x00\x24\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x2A\x01\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x2F\x01\x00\x00\x6F\x74\x15\x3E')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x34\x01\x00\x00')
		OutMaterial.write(b'\xCB\x53\x4D\xA6\x03\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x39\x01\x00\x00\xDB\x28\x38\x1B\x04\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\x3E\x01\x00\x00\xF3\x84\x27\xA7\x05\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x43\x01\x00\x00\xBD\xD7\x53\x45')
		OutMaterial.write(b'\x06\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x68\x01\x00\x00')
		OutMaterial.write(b'\x78\x01\x00\x00\xD0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x90\x01\x00\x00\xA0\x01\x00\x00')
		OutMaterial.write(b'\xB0\x01\x00\x00\xC0\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x40\x3F\x00\x00\xC0\x3F\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x34\x42\x00\x00\x80\x3F\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDB\xF9\x7E\x3F\x00\x00\x40\x41\x00\x00\x00\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x0B\x10\x59\x38\x04\x50\xED\xAA\xF5\x43\x09\x11\xAA\x7C\xE2\xF6')
		OutMaterial.write(b'\x98\x98\x75\x56\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x64\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It is a generic vehicle black texture being used as normal (blue)
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xBC\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurDiffuse != '' and RasterIDBlurDiffuse != '00_00_00_00':
			TexStateBlurDiffuse = StringToID(RasterDict["BlurDiffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurDiffuse, RasterIDBlurDiffuse)
			IDsList[TexStateBlurDiffuse] = 'TextureState'
			if isBlurDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurDiffuse, RasterPathBlurDiffuse)
				IDsList[RasterIDBlurDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurDiffuse.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlurNormal != '' and RasterIDBlurNormal != '00_00_00_00':
			TexStateBlurNormal = StringToID(RasterDict["BlurNormal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlurNormal, RasterIDBlurNormal)
			IDsList[TexStateBlurNormal] = 'TextureState'
			if isBlurNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlurNormal, RasterPathBlurNormal)
				IDsList[RasterIDBlurNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlurNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDEmissive != '' and RasterIDEmissive != '00_00_00_00':
			TexStateEmissive = StringToID(RasterDict["Emissive"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateEmissive, RasterIDEmissive)
			IDsList[TexStateEmissive] = 'TextureState'
			if isEmissiveGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDEmissive, RasterPathEmissive)
				IDsList[RasterIDEmissive] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateEmissive.replace('_', '')))
		else:
			OutMaterial.write(b'\xB0\x37\xC7\x80')
		OutMaterial.write(b'\x00\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')

#TRKs

def CreateMaterial_57_0B_99_65(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xCC\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xAA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xB0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xBA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xBD\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC2\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC7\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00')
		OutMaterial.write(b'\xEC\x00\x00\x00\x00\x01\x00\x00\x70\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x8A\x64\x80\x72')
		OutMaterial.write(b'\x0A\x5F\x89\xA4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x57\x0B\x99\x65\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_3C_A3_99_3E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x3C\xA3\x99\x3E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_AD_57_BF_E3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xAD\x57\xBF\xE3\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B0_1D_35_C6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x02\x00\x00\x00\x90\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x02\x00\x00\x00\x98\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9A\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x9F\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x01\x00\x00\x00\xB4\x00\x00\x00\xB8\x00\x00\x00')
		OutMaterial.write(b'\xD0\x00\x00\x00\x01\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\xE4\x00\x00\x00\xE8\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB0\x1D\x35\xC6\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B6_7A_FA_60(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB6\x7A\xFA\x60\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_BD_2E_A8_C4(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\xF3\x11\xBA\xC6\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xBD\x2E\xA8\xC4\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_37_C2_9A_C3(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x37\xC2\x9A\xC3\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_95_66_1E_23(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x95\x66\x1E\x23\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_4B_D9_70_EA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x4B\xD9\x70\xEA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_89_41_8E_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDMaskMap = ''
	if "MaskMap" in RasterDict:
		RasterIDMaskMap, RasterPathMaskMap = RasterDict["MaskMap"]
		RasterIDMaskMap, isMaskMapGeneric = VerifyGenericIDs(game_version,RasterIDMaskMap,verify_genericIDs)
	RasterIDMaskMap = StringToID(RasterIDMaskMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x04\x04\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE8\x00\x00\x00\xF8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xB4\x00\x00\x00')
		OutMaterial.write(b'\x00\x06\x00\x00\x04\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xC4\x00\x00\x00')
		OutMaterial.write(b'\x00\x06\x00\x00\x04\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD4\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xD9\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xDE\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xE3\x00\x00\x00\xFE\x35\x0E\xC3\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x08\x01\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00\x70\x01\x00\x00')
		OutMaterial.write(b'\x80\x01\x00\x00\x90\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x80\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\xB8\x32\x5F\x68\x9F\x90\x73\x4A')
		OutMaterial.write(b'\x8A\x64\x80\x72\x0A\x5F\x89\xA4\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x89\x41\x8E\x7B\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDMaskMap != '' and RasterIDMaskMap != '00_00_00_00':
			TexStateMaskMap = StringToID(RasterDict["MaskMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateMaskMap, RasterIDMaskMap)
			IDsList[TexStateMaskMap] = 'TextureState'
			if isMaskMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDMaskMap, RasterPathMaskMap)
				IDsList[RasterIDMaskMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateMaskMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_3D_C9_A3_7B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x3D\xC9\xA3\x7B\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_7B_7B_A2_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDLineMap = ''
	if "LineMap" in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict["LineMap"]
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	RasterIDLineMap = StringToID(RasterIDLineMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDNormalDetail = ''
	if "NormalDetail" in RasterDict:
		RasterIDNormalDetail, RasterPathNormalDetail = RasterDict["NormalDetail"]
		RasterIDNormalDetail, isNormalDetailGeneric = VerifyGenericIDs(game_version,RasterIDNormalDetail,verify_genericIDs)
	RasterIDNormalDetail = StringToID(RasterIDNormalDetail, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x05\x05\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x01\x00\x00\x34\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xD8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE5\x00\x00\x00\x0C\x7B\x95\xC5\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEA\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEF\x00\x00\x00')
		OutMaterial.write(b'\xF3\x11\xBA\xC6\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xF4\x00\x00\x00\x6F\x74\x15\x3E\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xF9\x00\x00\x00\x24\x9D\x5C\xAB\x04\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x10\x01\x00\x00\x14\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40')
		OutMaterial.write(b'\x1B\x1E\x2C\x48\x03\x00\x00\x00\x44\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x90\x06\x29\x3F\x90\x06\x29\x3F\x90\x06\x29\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x7B\x7B\xA2\x8E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		#LineMapsLists = ['70_78_95_A6']
		#if RasterIDLineMap not in LineMapsLists: RasterIDLineMap = ''		#FIXAR
		if RasterIDLineMap != '' and RasterIDLineMap != '00_00_00_00':
			TexStateLineMap = StringToID(RasterDict["LineMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureStateLineMap(game_version, srcPath, TexStateLineMap, RasterIDLineMap)
			IDsList[TexStateLineMap] = 'TextureState'
			if isLineMapGeneric == False or use_UniqueIDs == True:
				CreateRasterLineMap(game_version, srcPath, RasterIDLineMap, RasterPathLineMap)
				IDsList[RasterIDLineMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLineMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x31\x92\xB1\x67')		#D1_21_05_AF is a generic trk unit line map for road
			CreateTextureStateLineMap(game_version, srcPath, "31_92_B1_67", "D1_21_05_AF")
			IDsList["31_92_B1_67"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x75\x48\x8C\xCE')		#0C_7A_20_E9 is a generic trk unit detail map for road
			CreateTextureState(game_version, srcPath, "75_48_8C_CE", "0C_7A_20_E9")
			IDsList["75_48_8C_CE"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xE8\x80\x42\x53')		#76_6F_76_3D is a generic trk unit baseMap texture for road
			CreateTextureState(game_version, srcPath, "E8_80_42_53", "76_6F_76_3D")
			IDsList["E8_80_42_53"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xED\x82\xF7\xA4')		#88_79_A2_E0 is a generic trk unit normal texture
			CreateTextureState(game_version, srcPath, "ED_82_F7_A4", "88_79_A2_E0")
			IDsList["ED_82_F7_A4"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormalDetail != '' and RasterIDNormalDetail != '00_00_00_00':
			TexStateNormalDetail = StringToID(RasterDict["NormalDetail"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormalDetail, RasterIDNormalDetail)
			IDsList[TexStateNormalDetail] = 'TextureState'
			if isNormalDetailGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormalDetail, RasterPathNormalDetail)
				IDsList[RasterIDNormalDetail] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormalDetail.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal detail (green-blue)
			OutMaterial.write(b'\xA1\x53\x76\x4C')		#AE_7E_C6_7D is a generic trk unit normal (green-blue) texture
			CreateTextureState(game_version, srcPath, "A1_53_76_4C", "AE_7E_C6_7D")
			IDsList["A1_53_76_4C"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_7C_C6_D3_1D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x07\x73\xA5\x3E\x88\xD2\xA7\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x7C\xC6\xD3\x1D\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_AE_B3_92_62(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0D\x93\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\xEA\xE9\x69\x3F\xD6\x0E\x12\x3F\x8D\x72\x0E\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xAE\xB3\x92\x62\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_71_12_EC_98(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDVerticalFace = ''
	if "VerticalFace" in RasterDict:
		RasterIDVerticalFace, RasterPathVerticalFace = RasterDict["VerticalFace"]
		RasterIDVerticalFace, isVerticalFaceGeneric = VerifyGenericIDs(game_version,RasterIDVerticalFace,verify_genericIDs)
	RasterIDVerticalFace = StringToID(RasterIDVerticalFace, use_UniqueIDs, vehicleName)
	RasterIDSlantedFace = ''
	if "SlantedFace" in RasterDict:
		RasterIDSlantedFace, RasterPathSlantedFace = RasterDict["SlantedFace"]
		RasterIDSlantedFace, isSlantedFaceGeneric = VerifyGenericIDs(game_version,RasterIDSlantedFace,verify_genericIDs)
	RasterIDSlantedFace = StringToID(RasterIDSlantedFace, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDHorizontalFace = ''
	if "HorizontalFace" in RasterDict:
		RasterIDHorizontalFace, RasterPathHorizontalFace = RasterDict["HorizontalFace"]
		RasterIDHorizontalFace, isHorizontalFaceGeneric = VerifyGenericIDs(game_version,RasterIDHorizontalFace,verify_genericIDs)
	RasterIDHorizontalFace = StringToID(RasterIDHorizontalFace, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD4\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x07\x00\x00\x03\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xB4\x00\x00\x00')
		OutMaterial.write(b'\x00\x07\x00\x00\x03\x00\x00\x00\xC2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC5\x00\x00\x00\x80\x0F\xDB\xDB\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCA\x00\x00\x00\xEF\x95\xF2\x78')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCF\x00\x00\x00')
		OutMaterial.write(b'\x65\x77\xB8\x39\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x07\x00\x00\x00\xF4\x00\x00\x00\x10\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB2\xB2\x32\x3F\xB2\xB2\x32\x3F\xB2\xB2\x32\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x66\x66\xE6\x3E\x66\x66\xE6\x3E\x66\x66\xE6\x3E\x66\x66\xE6\x3E')
		OutMaterial.write(b'\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x48\xCE\x3F\x33\xC7\xBE\xA0\x8D\xBE\x50\x04\xDA')
		OutMaterial.write(b'\x3D\x00\xE1\x19\x3B\xC3\xDA\x41\x4F\x9F\x81\x8D\x00\x00\x00\x00')
		OutMaterial.write(b'\x71\x12\xEC\x98\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDVerticalFace != '' and RasterIDVerticalFace != '00_00_00_00':
			TexStateVerticalFace = StringToID(RasterDict["VerticalFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateVerticalFace, RasterIDVerticalFace)
			IDsList[TexStateVerticalFace] = 'TextureState'
			if isVerticalFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDVerticalFace, RasterPathVerticalFace)
				IDsList[RasterIDVerticalFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateVerticalFace.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSlantedFace != '' and RasterIDSlantedFace != '00_00_00_00':
			TexStateSlantedFace = StringToID(RasterDict["SlantedFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSlantedFace, RasterIDSlantedFace)
			IDsList[TexStateSlantedFace] = 'TextureState'
			if isSlantedFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSlantedFace, RasterPathSlantedFace)
				IDsList[RasterIDSlantedFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSlantedFace.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDHorizontalFace != '' and RasterIDHorizontalFace != '00_00_00_00':
			TexStateHorizontalFace = StringToID(RasterDict["HorizontalFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateHorizontalFace, RasterIDHorizontalFace)
			IDsList[TexStateHorizontalFace] = 'TextureState'
			if isHorizontalFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDHorizontalFace, RasterPathHorizontalFace)
				IDsList[RasterIDHorizontalFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateHorizontalFace.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_AD_08_F1_AA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDBlendMap = ''
	if "BlendMap" in RasterDict:
		RasterIDBlendMap, RasterPathBlendMap = RasterDict["BlendMap"]
		RasterIDBlendMap, isBlendMapGeneric = VerifyGenericIDs(game_version,RasterIDBlendMap,verify_genericIDs)
	RasterIDBlendMap = StringToID(RasterIDBlendMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xAC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xB2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB5\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBA\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBF\x00\x00\x00')
		OutMaterial.write(b'\x71\xF7\x1E\x60\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		#OutMaterial.write(b'\x98\x98\x18\x3E\x98\x97\x17\x3F\x81\x80\x80\x3E\x00\x00\x80\x3F')	# Many parts were getting green
		OutMaterial.write(b'\x57\x65\xC6\x3E\x32\x60\xFC\x3E\x69\x90\x06\x3F\xC3\x4E\x6C\x3E')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xAD\x08\xF1\xAA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlendMap != '' and RasterIDBlendMap != '00_00_00_00':
			TexStateBlendMap = StringToID(RasterDict["BlendMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlendMap, RasterIDBlendMap)
			IDsList[TexStateBlendMap] = 'TextureState'
			if isBlendMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlendMap, RasterPathBlendMap)
				IDsList[RasterIDBlendMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlendMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_D4_90_D6_B8(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDLineMap = ''
	if "LineMap" in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict["LineMap"]
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	RasterIDLineMap = StringToID(RasterIDLineMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x04\x04\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xF8\x00\x00\x00\x5C\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xB4\x00\x00\x00')
		OutMaterial.write(b'\x03\x06\x00\x00\x04\x00\x00\x00\xC6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xCC\x00\x00\x00')
		OutMaterial.write(b'\x03\x06\x00\x00\x04\x00\x00\x00\xDE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE2\x00\x00\x00\x0C\x7B\x95\xC5\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xE7\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEC\x00\x00\x00')
		OutMaterial.write(b'\xF3\x11\xBA\xC6\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xF1\x00\x00\x00\x4D\xE3\xE5\x45\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x03\x00\x00\x00\x08\x01\x00\x00')
		OutMaterial.write(b'\x14\x01\x00\x00\x50\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x20\x01\x00\x00\x30\x01\x00\x00\x40\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x90\x40\x00\x00\x90\x40\x00\x00\x90\x40\x00\x00\x90\x40')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xDC\x21\x53\x48\x1B\x1E\x2C\x48\x1A\x78\xCE\xD1\x06\x00\x00\x00')
		OutMaterial.write(b'\x6C\x01\x00\x00\x84\x01\x00\x00\x00\x02\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xA0\x01\x00\x00\xB0\x01\x00\x00\xC0\x01\x00\x00')
		OutMaterial.write(b'\xD0\x01\x00\x00\xE0\x01\x00\x00\xF0\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E')
		OutMaterial.write(b'\x66\x66\xA6\x3F\x66\x66\xA6\x3F\x66\x66\xA6\x3F\x66\x66\xA6\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x04\x5D\xD6\x59\x7A\xA5\xB9\xF2\x73\xE7\xE0\x81')
		OutMaterial.write(b'\x9F\x90\x73\x4A\x2E\xE8\x71\xE6\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xD4\x90\xD6\xB8\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		#LineMapsLists = ['70_78_95_A6']
		#if RasterIDLineMap not in LineMapsLists: RasterIDLineMap = ''		#FIXAR
		if RasterIDLineMap != '' and RasterIDLineMap != '00_00_00_00':
			TexStateLineMap = StringToID(RasterDict["LineMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureStateLineMap(game_version, srcPath, TexStateLineMap, RasterIDLineMap)
			IDsList[TexStateLineMap] = 'TextureState'
			if isLineMapGeneric == False or use_UniqueIDs == True:
				CreateRasterLineMap(game_version, srcPath, RasterIDLineMap, RasterPathLineMap)
				IDsList[RasterIDLineMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLineMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_D0_75_4B_DF(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFB\xEC\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xD0\x75\x4B\xDF\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B8_A5_9E_01(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFB\xEC\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xB8\xA5\x9E\x01\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_49_A7_17_A0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x49\xA7\x17\xA0\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_5D_C3_BE_4F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDLineMap = ''
	if "LineMap" in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict["LineMap"]
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	RasterIDLineMap = StringToID(RasterIDLineMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDNormalDetail = ''
	if "NormalDetail" in RasterDict:
		RasterIDNormalDetail, RasterPathNormalDetail = RasterDict["NormalDetail"]
		RasterIDNormalDetail, isNormalDetailGeneric = VerifyGenericIDs(game_version,RasterIDNormalDetail,verify_genericIDs)
	RasterIDNormalDetail = StringToID(RasterIDNormalDetail, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x05\x05\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x01\x00\x00\x34\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xD8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE5\x00\x00\x00\x0C\x7B\x95\xC5\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEA\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEF\x00\x00\x00')
		OutMaterial.write(b'\xF3\x11\xBA\xC6\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xF4\x00\x00\x00\x6F\x74\x15\x3E\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xF9\x00\x00\x00\x24\x9D\x5C\xAB\x04\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x10\x01\x00\x00\x14\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x1B\x1E\x2C\x48\x03\x00\x00\x00\x44\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x5D\xC3\xBE\x4F\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		#LineMapsLists = ['70_78_95_A6']
		#if RasterIDLineMap not in LineMapsLists: RasterIDLineMap = ''		#FIXAR
		if RasterIDLineMap != '' and RasterIDLineMap != '00_00_00_00':
			TexStateLineMap = StringToID(RasterDict["LineMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureStateLineMap(game_version, srcPath, TexStateLineMap, RasterIDLineMap)
			IDsList[TexStateLineMap] = 'TextureState'
			if isLineMapGeneric == False or use_UniqueIDs == True:
				CreateRasterLineMap(game_version, srcPath, RasterIDLineMap, RasterPathLineMap)
				IDsList[RasterIDLineMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLineMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x31\x92\xB1\x67')		#D1_21_05_AF is a generic trk unit line map for road
			CreateTextureStateLineMap(game_version, srcPath, "31_92_B1_67", "D1_21_05_AF")
			IDsList["31_92_B1_67"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x75\x48\x8C\xCE')		#0C_7A_20_E9 is a generic trk unit detail map for road
			CreateTextureState(game_version, srcPath, "75_48_8C_CE", "0C_7A_20_E9")
			IDsList["75_48_8C_CE"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xE8\x80\x42\x53')		#76_6F_76_3D is a generic trk unit baseMap texture for road
			CreateTextureState(game_version, srcPath, "E8_80_42_53", "76_6F_76_3D")
			IDsList["E8_80_42_53"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xED\x82\xF7\xA4')		#88_79_A2_E0 is a generic trk unit normal texture
			CreateTextureState(game_version, srcPath, "ED_82_F7_A4", "88_79_A2_E0")
			IDsList["ED_82_F7_A4"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormalDetail != '' and RasterIDNormalDetail != '00_00_00_00':
			TexStateNormalDetail = StringToID(RasterDict["NormalDetail"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormalDetail, RasterIDNormalDetail)
			IDsList[TexStateNormalDetail] = 'TextureState'
			if isNormalDetailGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormalDetail, RasterPathNormalDetail)
				IDsList[RasterIDNormalDetail] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormalDetail.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal detail (green-blue)
			OutMaterial.write(b'\xA1\x53\x76\x4C')		#AE_7E_C6_7D is a generic trk unit normal (green-blue) texture
			CreateTextureState(game_version, srcPath, "A1_53_76_4C", "AE_7E_C6_7D")
			IDsList["A1_53_76_4C"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_BA_2E_9B_81(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\xF3\x11\xBA\xC6\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xBA\x2E\x9B\x81\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_94_B4_DB_B5(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0D\x93\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x94\xB4\xDB\xB5\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_19_6E_C7_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDOverlay = ''
	if "Overlay" in RasterDict:
		RasterIDOverlay, RasterPathOverlay = RasterDict["Overlay"]
		RasterIDOverlay, isOverlayGeneric = VerifyGenericIDs(game_version,RasterIDOverlay,verify_genericIDs)
	RasterIDOverlay = StringToID(RasterIDOverlay, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xD4\x00\x00\x00\xE4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\xD2\x64\x7B\x38')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xB0\x00\x00\x00\xB4\x00\x00\x00\xD0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xF4\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x20\x40\x00\x00\x20\x40\x00\x00\x20\x40\x00\x00\x20\x40')
		OutMaterial.write(b'\x00\x00\x70\x42\x00\x00\x70\x42\x00\x00\x70\x42\x00\x00\x70\x42')
		OutMaterial.write(b'\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40')
		OutMaterial.write(b'\x3C\x01\x00\x00\x49\x01\x00\x00\x5D\x01\x00\x00\x41\x6E\x69\x6D')
		OutMaterial.write(b'\x44\x75\x72\x61\x74\x69\x6F\x6E\x00\x41\x6E\x69\x6D\x4E\x75\x6D')
		OutMaterial.write(b'\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x55\x00\x41\x6E\x69')
		OutMaterial.write(b'\x6D\x4E\x75\x6D\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x56')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x19\x6E\xC7\x0F\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDOverlay != '' and RasterIDOverlay != '00_00_00_00':
			TexStateOverlay = StringToID(RasterDict["Overlay"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateOverlay, RasterIDOverlay)
			IDsList[TexStateOverlay] = 'TextureState'
			if isOverlayGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDOverlay, RasterPathOverlay)
				IDsList[RasterIDOverlay] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateOverlay.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_37_E7_77_6B(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\xCD\xCC\x4C\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x37\xE7\x77\x6B\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_FF_3B_D3_06(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFF\x3B\xD3\x06\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_46_FB_C2_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x02\x00\x00\x00\x90\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x02\x00\x00\x00\x98\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9A\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x9F\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x01\x00\x00\x00\xB4\x00\x00\x00\xB8\x00\x00\x00')
		OutMaterial.write(b'\xD0\x00\x00\x00\x01\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\xE4\x00\x00\x00\xE8\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x46\xFB\xC2\x67\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_D2_FB_F8_AB(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xD2\xFB\xF8\xAB\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_1F_DA_DF_6E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x34\xFD\xB8\x3E\x69\xF1\xE3\x3E\x07\x73\xA5\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x1F\xDA\xDF\x6E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_42_73_1A_D2(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x8C\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x01\x00\x00\x00\x7C\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x96\x33\x80\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x01\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x85\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x9C\x00\x00\x00\xA0\x00\x00\x00\xC0\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xB0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\xD4\x00\x00\x00\xD8\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x01\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x42\x73\x1A\xD2\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xBE\x2F\x14\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')


def CreateMaterial_9E_FB_32_8E(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDLineMap = ''
	if "LineMap" in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict["LineMap"]
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	RasterIDLineMap = StringToID(RasterIDLineMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDAoMap = ''
	if "AoMap" in RasterDict:
		RasterIDAoMap, RasterPathAoMap = RasterDict["AoMap"]
		RasterIDAoMap, isAoMapGeneric = VerifyGenericIDs(game_version,RasterIDAoMap,verify_genericIDs)
	RasterIDAoMap = StringToID(RasterIDAoMap, use_UniqueIDs, vehicleName)
	RasterIDlightMap = ''
	if "lightMap" in RasterDict:
		RasterIDlightMap, RasterPathlightMap = RasterDict["lightMap"]
		RasterIDlightMap, islightMapGeneric = VerifyGenericIDs(game_version,RasterIDlightMap,verify_genericIDs)
	elif "LightMap" in RasterDict:
		RasterIDlightMap, RasterPathlightMap = RasterDict["LightMap"]
		RasterIDlightMap, islightMapGeneric = VerifyGenericIDs(game_version,RasterIDlightMap,verify_genericIDs)
	RasterIDlightMap = StringToID(RasterIDlightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x06\x06\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x18\x01\x00\x00\x44\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xDC\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x06\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xEC\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x06\x00\x00\x00\xF4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xFA\x00\x00\x00\x0C\x7B\x95\xC5\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xFF\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x04\x01\x00\x00')
		OutMaterial.write(b'\xF3\x11\xBA\xC6\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\x09\x01\x00\x00\x6F\x74\x15\x3E\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\x0E\x01\x00\x00\x24\x9D\x5C\xAB\x04\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x13\x01\x00\x00\x83\x0F\xF3\xB2')
		OutMaterial.write(b'\x05\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F')
		OutMaterial.write(b'\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x01\x00\x00\x00\x28\x01\x00\x00')
		OutMaterial.write(b'\x2C\x01\x00\x00\x40\x01\x00\x00\x01\x00\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40\x00\x00\x80\x40')
		OutMaterial.write(b'\x1B\x1E\x2C\x48\x03\x00\x00\x00\x54\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x9E\xFB\x32\x8E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLineMap != '' and RasterIDLineMap != '00_00_00_00':
			TexStateLineMap = StringToID(RasterDict["LineMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLineMap, RasterIDLineMap)
			IDsList[TexStateLineMap] = 'TextureState'
			if isLineMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLineMap, RasterPathLineMap)
				IDsList[RasterIDLineMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLineMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAoMap != '' and RasterIDAoMap != '00_00_00_00':
			TexStateAoMap = StringToID(RasterDict["AoMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAoMap, RasterIDAoMap)
			IDsList[TexStateAoMap] = 'TextureState'
			if isAoMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAoMap, RasterPathAoMap)
				IDsList[RasterIDAoMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAoMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDlightMap != '' and RasterIDlightMap != '00_00_00_00':
			if "lightMap" in RasterDict:
				TexStatelightMap = StringToID(RasterDict["lightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			elif "LightMap" in RasterDict:
				TexStatelightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStatelightMap, RasterIDlightMap)
			IDsList[TexStatelightMap] = 'TextureState'
			if islightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDlightMap, RasterPathlightMap)
				IDsList[RasterIDlightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStatelightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\xD8\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_9F_D5_D8_48(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFB\xEC\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9F\xD5\xD8\x48\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_1B_D8_B8_27(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\xF3\x11\xBA\xC6\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x1B\xD8\xB8\x27\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_8A_88_2A_56(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\xFC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x03\x01\x00\x00\x01\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x6A\xEC\x84\x00\x00\x00')
		OutMaterial.write(b'\x03\x01\x00\x00\x01\x00\x00\x00\x8C\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x8D\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x00\x00\x03\x00\x00\x00\xA4\x00\x00\x00\xB0\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\xD0\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E\xCD\xCC\x4C\x3E')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E')
		OutMaterial.write(b'\xEE\x67\x52\x94\xCB\x58\xF6\x40\x09\x01\xD9\xF0\x01\x00\x00\x00')
		OutMaterial.write(b'\x0C\x01\x00\x00\x10\x01\x00\x00\x30\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xA4\x41\x1A\x3F\xA4\x41\x1A\x3F\xA4\x41\x1A\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x8A\x88\x2A\x56\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_EB_BF_C4_9D(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEB\xBF\xC4\x9D\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_36_9A_6B_40(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xED\x2E\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x36\x9A\x6B\x40\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_C7_1B_BF_08(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x96\x33\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xC7\x1B\xBF\x08\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xBE\x2F\x14\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B4_56_99_82(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDlightMap = ''
	if "lightMap" in RasterDict:
		RasterIDlightMap, RasterPathlightMap = RasterDict["lightMap"]
		RasterIDlightMap, islightMapGeneric = VerifyGenericIDs(game_version,RasterIDlightMap,verify_genericIDs)
	RasterIDlightMap = StringToID(RasterIDlightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xAC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xB2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB5\x00\x00\x00\xF3\x11\xBA\xC6\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBA\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBF\x00\x00\x00')
		OutMaterial.write(b'\x83\x0F\xF3\xB2\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xB4\x56\x99\x82\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDlightMap != '' and RasterIDlightMap != '00_00_00_00':
			TexStatelightMap = StringToID(RasterDict["lightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStatelightMap, RasterIDlightMap)
			IDsList[TexStatelightMap] = 'TextureState'
			if islightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDlightMap, RasterPathlightMap)
				IDsList[RasterIDlightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStatelightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_86_6F_8D_FC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	RasterIDAnimMap = ''
	if "AnimMap" in RasterDict:
		RasterIDAnimMap, RasterPathAnimMap = RasterDict["AnimMap"]
		RasterIDAnimMap, isAnimMapGeneric = VerifyGenericIDs(game_version,RasterIDAnimMap,verify_genericIDs)
	RasterIDAnimMap = StringToID(RasterIDAnimMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC0\x00\x00\x00\xF4\x00\x00\x00\x24\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x03\x00\x00\x00\xA4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\xA8\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x03\x00\x00\x00\xAC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xB4\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xB9\x00\x00\x00')
		OutMaterial.write(b'\x61\x2F\x1B\x29\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\xD4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\x04\x01\x00\x00\x08\x01\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x03\x00\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x41\x00\x00\x80\x41\x00\x00\x80\x41\x00\x00\x80\x41')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x7C\x01\x00\x00\x89\x01\x00\x00\x9D\x01\x00\x00\x41\x6E\x69\x6D')
		OutMaterial.write(b'\x44\x75\x72\x61\x74\x69\x6F\x6E\x00\x41\x6E\x69\x6D\x4E\x75\x6D')
		OutMaterial.write(b'\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x55\x00\x41\x6E\x69')
		OutMaterial.write(b'\x6D\x4E\x75\x6D\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x56')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x86\x6F\x8D\xFC\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAnimMap != '' and RasterIDAnimMap != '00_00_00_00':
			TexStateAnimMap = StringToID(RasterDict["AnimMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAnimMap, RasterIDAnimMap)
			IDsList[TexStateAnimMap] = 'TextureState'
			if isAnimMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAnimMap, RasterPathAnimMap)
				IDsList[RasterIDAnimMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAnimMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_4E_83_F2_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	RasterIDBlendMap = ''
	if "BlendMap" in RasterDict:
		RasterIDBlendMap, RasterPathBlendMap = RasterDict["BlendMap"]
		RasterIDBlendMap, isBlendMapGeneric = VerifyGenericIDs(game_version,RasterIDBlendMap,verify_genericIDs)
	RasterIDBlendMap = StringToID(RasterIDBlendMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xCC\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xAA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xB0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xBA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xBD\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC2\x00\x00\x00\x26\x50\xF6\xD0')
		OutMaterial.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC7\x00\x00\x00')
		OutMaterial.write(b'\x71\xF7\x1E\x60\x04\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00')
		OutMaterial.write(b'\xEC\x00\x00\x00\x00\x01\x00\x00\x70\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x29\x3F\x6D\x3F\x7B\x14\x6E\x3F\xD7\x69\x6C\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x40\x00\x00\x40\x40\x00\x00\x40\x40\x00\x00\x40\x40')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x8A\x64\x80\x72')
		OutMaterial.write(b'\x0A\x5F\x89\xA4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x4E\x83\xF2\xD0\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlendMap != '' and RasterIDBlendMap != '00_00_00_00':
			TexStateBlendMap = StringToID(RasterDict["BlendMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlendMap, RasterIDBlendMap)
			IDsList[TexStateBlendMap] = 'TextureState'
			if isBlendMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlendMap, RasterPathBlendMap)
				IDsList[RasterIDBlendMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlendMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_49_3C_26_F6(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDBlendMap = ''
	if "BlendMap" in RasterDict:
		RasterIDBlendMap, RasterPathBlendMap = RasterDict["BlendMap"]
		RasterIDBlendMap, isBlendMapGeneric = VerifyGenericIDs(game_version,RasterIDBlendMap,verify_genericIDs)
	RasterIDBlendMap = StringToID(RasterIDBlendMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\xAC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xB2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB5\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBA\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBF\x00\x00\x00')
		OutMaterial.write(b'\x71\xF7\x1E\x60\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x10\x58\x3F\x08\xC7\x6C\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41')
		OutMaterial.write(b'\x7A\x36\x1F\x40\x7A\x36\x1F\x40\x7A\x36\x1F\x40\x7A\x36\x1F\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x49\x3C\x26\xF6\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBlendMap != '' and RasterIDBlendMap != '00_00_00_00':
			TexStateBlendMap = StringToID(RasterDict["BlendMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBlendMap, RasterIDBlendMap)
			IDsList[TexStateBlendMap] = 'TextureState'
			if isBlendMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBlendMap, RasterPathBlendMap)
				IDsList[RasterIDBlendMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBlendMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_65_25_EA_21(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xC8\xC8\x48\x3F\xDC\xDA\x5A\x3F\xC1\xC0\x40\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x65\x25\xEA\x21\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_F7_30_97_BD(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0D\x93\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xC8\xC8\x48\x3F\xDC\xDA\x5A\x3F\xC1\xC0\x40\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF7\x30\x97\xBD\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_C5_1D_C5_57(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFB\xEC\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xC5\x1D\xC5\x57\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B1_2C_80_67(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDVerticalFace = ''
	if "VerticalFace" in RasterDict:
		RasterIDVerticalFace, RasterPathVerticalFace = RasterDict["VerticalFace"]
		RasterIDVerticalFace, isVerticalFaceGeneric = VerifyGenericIDs(game_version,RasterIDVerticalFace,verify_genericIDs)
	RasterIDVerticalFace = StringToID(RasterIDVerticalFace, use_UniqueIDs, vehicleName)
	RasterIDSlantedFace = ''
	if "SlantedFace" in RasterDict:
		RasterIDSlantedFace, RasterPathSlantedFace = RasterDict["SlantedFace"]
		RasterIDSlantedFace, isSlantedFaceGeneric = VerifyGenericIDs(game_version,RasterIDSlantedFace,verify_genericIDs)
	RasterIDSlantedFace = StringToID(RasterIDSlantedFace, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDHorizontalFace = ''
	if "HorizontalFace" in RasterDict:
		RasterIDHorizontalFace, RasterPathHorizontalFace = RasterDict["HorizontalFace"]
		RasterIDHorizontalFace, isHorizontalFaceGeneric = VerifyGenericIDs(game_version,RasterIDHorizontalFace,verify_genericIDs)
	RasterIDHorizontalFace = StringToID(RasterIDHorizontalFace, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x0A\x00\x00\x03\x00\x00\x00\xB4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xB8\x00\x00\x00')
		OutMaterial.write(b'\x00\x0A\x00\x00\x03\x00\x00\x00\xCC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xCF\x00\x00\x00\x80\x0F\xDB\xDB\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xD4\x00\x00\x00\xEF\x95\xF2\x78')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xD9\x00\x00\x00')
		OutMaterial.write(b'\x65\x77\xB8\x39\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x0A\x00\x00\x00\x00\x01\x00\x00\x28\x01\x00\x00\xF0\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00\xA0\x01\x00\x00')
		OutMaterial.write(b'\xB0\x01\x00\x00\xC0\x01\x00\x00\xD0\x01\x00\x00\xE0\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x30\x41\x00\x00\x30\x41\x00\x00\x30\x41\x00\x00\x30\x41')
		OutMaterial.write(b'\x33\x33\x33\x3F\x33\x33\x33\x3F\x33\x33\x33\x3F\x33\x33\x33\x3F')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x3F\x00\x00\x00\x3F')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F\xCD\xCC\x4C\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\xE7\x69\xF4\xFD')
		OutMaterial.write(b'\x48\xCE\x3F\x33\xC7\xBE\xA0\x8D\xBE\x50\x04\xDA\x3D\x00\xE1\x19')
		OutMaterial.write(b'\x3B\xC3\xDA\x41\x4F\x9F\x81\x8D\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB1\x2C\x80\x67\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDVerticalFace != '' and RasterIDVerticalFace != '00_00_00_00':
			TexStateVerticalFace = StringToID(RasterDict["VerticalFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateVerticalFace, RasterIDVerticalFace)
			IDsList[TexStateVerticalFace] = 'TextureState'
			if isVerticalFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDVerticalFace, RasterPathVerticalFace)
				IDsList[RasterIDVerticalFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateVerticalFace.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSlantedFace != '' and RasterIDSlantedFace != '00_00_00_00':
			TexStateSlantedFace = StringToID(RasterDict["SlantedFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSlantedFace, RasterIDSlantedFace)
			IDsList[TexStateSlantedFace] = 'TextureState'
			if isSlantedFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSlantedFace, RasterPathSlantedFace)
				IDsList[RasterIDSlantedFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSlantedFace.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDHorizontalFace != '' and RasterIDHorizontalFace != '00_00_00_00':
			TexStateHorizontalFace = StringToID(RasterDict["HorizontalFace"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateHorizontalFace, RasterIDHorizontalFace)
			IDsList[TexStateHorizontalFace] = 'TextureState'
			if isHorizontalFaceGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDHorizontalFace, RasterPathHorizontalFace)
				IDsList[RasterIDHorizontalFace] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateHorizontalFace.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_6B_A8_27_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xED\x2E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x6B\xA8\x27\xCA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x26\xA0\x72\x7E\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_35_91_5B_CA(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xD4\x00\x00\x00\xE4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x07\x00\x00\x03\x00\x00\x00\xAE\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x80\xF1\xB4\x00\x00\x00')
		OutMaterial.write(b'\x00\x07\x00\x00\x03\x00\x00\x00\xC2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC5\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCA\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCF\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x07\x00\x00\x00\xF4\x00\x00\x00\x10\x01\x00\x00')
		OutMaterial.write(b'\xA0\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x80\x01\x00\x00\x90\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44\x00\x00\xFA\x44')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\xCD\xCC\xCC\x3E\xCD\xCC\xCC\x3E\xCD\xCC\xCC\x3E\xCD\xCC\xCC\x3E')
		OutMaterial.write(b'\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x72\xFD\x88\x61')
		OutMaterial.write(b'\xA5\x47\x1F\xAD\x5C\x19\x37\xF1\x28\xB8\xF8\xFB\x00\x00\x00\x00')
		OutMaterial.write(b'\x35\x91\x5B\xCA\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xBE\x2F\x14\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xFE\x64\xA3\x0B\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_BA_1F_F8_AC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA8\x00\x00\x00\xB8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x94\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x02\x00\x00\x00\x9A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xA1\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65')
		OutMaterial.write(b'\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\xD4\x00\x00\x00\x10\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00\x00\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\xBA\x1F\xF8\xAC\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_66_63_5A_26(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x84\x00\x00\x00\x94\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\x7C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x01\x00\x00\x00\x7E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x7F\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\x00\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\xA4\x00\x00\x00\xA8\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x66\x63\x5A\x26\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B9_E2_4F_D0(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDLightMap = ''
	if "LightMap" in RasterDict:
		RasterIDLightMap, RasterPathLightMap = RasterDict["LightMap"]
		RasterIDLightMap, isLightMapGeneric = VerifyGenericIDs(game_version,RasterIDLightMap,verify_genericIDs)
	RasterIDLightMap = StringToID(RasterIDLightMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x02\x02\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xA0\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x8C\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x90\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x02\x00\x00\x00\x92\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\x99\x00\x00\x00\x4D\xE3\xE5\x45')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xC0\x00\x00\x00\xC4\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xE2\x4F\xD0\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDLightMap != '' and RasterIDLightMap != '00_00_00_00':
			TexStateLightMap = StringToID(RasterDict["LightMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateLightMap, RasterIDLightMap)
			IDsList[TexStateLightMap] = 'TextureState'
			if isLightMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDLightMap, RasterPathLightMap)
				IDsList[RasterIDLightMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLightMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_73_B0_DA_EC(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDWaveNormal = ''
	if "WaveNormal" in RasterDict:
		RasterIDWaveNormal, RasterPathWaveNormal = RasterDict["WaveNormal"]
		RasterIDWaveNormal, isWaveNormalGeneric = VerifyGenericIDs(game_version,RasterIDWaveNormal,verify_genericIDs)
	RasterIDWaveNormal = StringToID(RasterIDWaveNormal, use_UniqueIDs, vehicleName)
	RasterIDRiverFloor = ''
	if "RiverFloor" in RasterDict:
		RasterIDRiverFloor, RasterPathRiverFloor = RasterDict["RiverFloor"]
		RasterIDRiverFloor, isRiverFloorGeneric = VerifyGenericIDs(game_version,RasterIDRiverFloor,verify_genericIDs)
	RasterIDRiverFloor = StringToID(RasterIDRiverFloor, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\xAC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xB2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB5\x00\x00\x00\x2C\x5B\x17\x72\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBA\x00\x00\x00\x81\x81\x95\x63')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBF\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x0B\x46\x02\x3F\xCB\x32\x17\x3F\x8B\x39\x23\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43')
		OutMaterial.write(b'\x6E\xDE\x27\x40\x6E\xDE\x27\x40\x6E\xDE\x27\x40\x6E\xDE\x27\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x73\xB0\xDA\xEC\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDWaveNormal != '' and RasterIDWaveNormal != '00_00_00_00':
			TexStateWaveNormal = StringToID(RasterDict["WaveNormal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateWaveNormal, RasterIDWaveNormal)
			IDsList[TexStateWaveNormal] = 'TextureState'
			if isWaveNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDWaveNormal, RasterPathWaveNormal)
				IDsList[RasterIDWaveNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateWaveNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDRiverFloor != '' and RasterIDRiverFloor != '00_00_00_00':
			TexStateRiverFloor = StringToID(RasterDict["RiverFloor"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateRiverFloor, RasterIDRiverFloor)
			IDsList[TexStateRiverFloor] = 'TextureState'
			if isRiverFloorGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDRiverFloor, RasterPathRiverFloor)
				IDsList[RasterIDRiverFloor] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateRiverFloor.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_B8_A1_8A_50(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x94\x00\x00\x00\xA4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x01\x00\x00\x00\x82\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\x84\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x01\x00\x00\x00\x8E\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x8F\x00\x00\x00\x26\x50\xF6\xD0\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x05\x00\x00\x00\xB4\x00\x00\x00\xC8\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\xE0\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xDB\xDB\x5B\x3F\xE7\xE6\x66\x3F\xE6\xE4\x64\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x33\x33\x33\x3F\x33\x33\x33\x3F\x33\x33\x33\x3F\x33\x33\x33\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E\x00\x00\x80\x3E')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x20\x40\x00\x00\x20\x40\x00\x00\x20\x40\x00\x00\x20\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x5C\x19\x37\xF1\x28\xB8\xF8\xFB\x73\xE7\xE0\x81')
		OutMaterial.write(b'\x9F\x90\x73\x4A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB8\xA1\x8A\x50\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xBE\x2F\x14\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_7F_B8_3B_1A(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xCC\x00\x00\x00\xDC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xAA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xB0\x00\x00\x00')
		OutMaterial.write(b'\x00\x05\x00\x00\x03\x00\x00\x00\xBA\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xBD\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC2\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xC7\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E')
		OutMaterial.write(b'\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00')
		OutMaterial.write(b'\xEC\x00\x00\x00\x00\x01\x00\x00\x70\x01\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x30\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41\x00\x00\x40\x41')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43')
		OutMaterial.write(b'\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40\x00\x00\xA0\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x8A\x64\x80\x72')
		OutMaterial.write(b'\x0A\x5F\x89\xA4\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x7F\xB8\x3B\x1A\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

#Generics

def CreateMaterial_1A_06_FF_0F(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x01\x01\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x8C\x00\x00\x00\xC4\x00\x00\x00\xF4\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x78\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x01\x00\x00\x00\x7C\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x7A\x10\x80\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x01\x00\x00\x00\x84\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x85\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\x00\x00\x00')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x9C\x00\x00\x00\xA0\x00\x00\x00\xC0\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\xB0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\xD4\x00\x00\x00\xD8\x00\x00\x00')
		OutMaterial.write(b'\xF0\x00\x00\x00\x01\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\xE0\xDB\xC7\x3D\xD6\x83\xA8\x3D\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x03\x00\x00\x00\x04\x01\x00\x00')
		OutMaterial.write(b'\x40\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\xC3\xF5\xA8\x3E\xC3\xF5\xA8\x3E\xC3\xF5\xA8\x3E\xC3\xF5\xA8\x3E')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x10\x41\x00\x00\x10\x41\x00\x00\x10\x41\x00\x00\x10\x41')
		OutMaterial.write(b'\x4C\x01\x00\x00\x59\x01\x00\x00\x6D\x01\x00\x00\x41\x6E\x69\x6D')
		OutMaterial.write(b'\x44\x75\x72\x61\x74\x69\x6F\x6E\x00\x41\x6E\x69\x6D\x4E\x75\x6D')
		OutMaterial.write(b'\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x55\x00\x41\x6E\x69')
		OutMaterial.write(b'\x6D\x4E\x75\x6D\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x56')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x1A\x06\xFF\x0F\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xCD\xF0\x44\xF7\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x62\x15\x71\x78\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_93_5F_33_58(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x00\x00\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\xC8\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\x64\x00\x00\x00')
		OutMaterial.write(b'\x02\x01\x00\x00\x00\x00\x00\x00\x6A\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x0D\x93\x6C\x00\x00\x00')
		OutMaterial.write(b'\x02\x01\x00\x00\x00\x00\x00\x00\x72\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\x00\x00\x02\x00\x00\x00\x84\x00\x00\x00\x8C\x00\x00\x00')
		OutMaterial.write(b'\xC0\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\xA0\x00\x00\x00')
		OutMaterial.write(b'\xB0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41')
		OutMaterial.write(b'\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43\x00\x00\x48\x43')
		OutMaterial.write(b'\xC9\x8F\x7E\xB0\x2E\xD6\xA8\x83\x01\x00\x00\x00\xD8\x00\x00\x00')
		OutMaterial.write(b'\xDC\x00\x00\x00\xF0\x00\x00\x00\x01\x00\x00\x00\xE0\x00\x00\x00')
		OutMaterial.write(b'\x7E\xCB\x37\x3E\x7E\xCB\x37\x3E\x7E\xCB\x37\x3E\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x93\x5F\x33\x58\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xB9\xBE\x2F\x14\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xF0\x46\xDA\xCD\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_3F_28_A4_93(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDSpecular = ''
	if "Specular" in RasterDict:
		RasterIDSpecular, RasterPathSpecular = RasterDict["Specular"]
		RasterIDSpecular, isSpecularGeneric = VerifyGenericIDs(game_version,RasterIDSpecular,verify_genericIDs)
	RasterIDSpecular = StringToID(RasterIDSpecular, use_UniqueIDs, vehicleName)
	RasterIDReflection = ''
	if "Reflection" in RasterDict:
		RasterIDReflection, RasterPathReflection = RasterDict["Reflection"]
		RasterIDReflection, isReflectionGeneric = VerifyGenericIDs(game_version,RasterIDReflection,verify_genericIDs)
	RasterIDReflection = StringToID(RasterIDReflection, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\xD4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xA6\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xAC\x00\x00\x00')
		OutMaterial.write(b'\x00\x03\x00\x00\x03\x00\x00\x00\xB2\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xB5\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBA\x00\x00\x00\xDB\x08\x0F\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xBF\x00\x00\x00')
		OutMaterial.write(b'\x26\x50\xF6\xD0\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x03\x00\x00\x00\xE4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x30\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x00\x01\x00\x00\x10\x01\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\xF8\x5F\x05\x3F\xD0\x3C\xE5\x3D\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41\x00\x00\x20\x41')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x3F\x28\xA4\x93\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDSpecular != '' and RasterIDSpecular != '00_00_00_00':
			TexStateSpecular = StringToID(RasterDict["Specular"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateSpecular, RasterIDSpecular)
			IDsList[TexStateSpecular] = 'TextureState'
			if isSpecularGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDSpecular, RasterPathSpecular)
				IDsList[RasterIDSpecular] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateSpecular.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDReflection != '' and RasterIDReflection != '00_00_00_00':
			TexStateReflection = StringToID(RasterDict["Reflection"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateReflection, RasterIDReflection)
			IDsList[TexStateReflection] = 'TextureState'
			if isReflectionGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDReflection, RasterPathReflection)
				IDsList[RasterIDReflection] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateReflection.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_C0_04_1A_37(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	RasterIDIllumMap = ''
	if "IllumMap" in RasterDict:
		RasterIDIllumMap, RasterPathIllumMap = RasterDict["IllumMap"]
		RasterIDIllumMap, isIllumMapGeneric = VerifyGenericIDs(game_version,RasterIDIllumMap,verify_genericIDs)
	RasterIDIllumMap = StringToID(RasterIDIllumMap, use_UniqueIDs, vehicleName)
	RasterIDAnimMap = ''
	if "AnimMap" in RasterDict:
		RasterIDAnimMap, RasterPathAnimMap = RasterDict["AnimMap"]
		RasterIDAnimMap, isAnimMapGeneric = VerifyGenericIDs(game_version,RasterIDAnimMap,verify_genericIDs)
	RasterIDAnimMap = StringToID(RasterIDAnimMap, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x03\x03\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xC0\x00\x00\x00\xF4\x00\x00\x00\x24\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xA0\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x03\x00\x00\x00\xA4\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xA8\x00\x00\x00')
		OutMaterial.write(b'\x01\x01\x00\x00\x03\x00\x00\x00\xAC\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xAF\x00\x00\x00\x02\x09\x64\x6A\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xB4\x00\x00\x00\xCC\xEA\xD1\x61')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xB9\x00\x00\x00')
		OutMaterial.write(b'\x61\x2F\x1B\x29\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xD0\x00\x00\x00\xD4\x00\x00\x00\xF0\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x59\x19\x69\x77\x01\x00\x00\x00\x04\x01\x00\x00\x08\x01\x00\x00')
		OutMaterial.write(b'\x20\x01\x00\x00\x01\x00\x00\x00\x10\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x00\x00\x00\x00\x03\x00\x00\x00\x34\x01\x00\x00')
		OutMaterial.write(b'\x70\x01\x00\x00\x40\x01\x00\x00\x50\x01\x00\x00\x60\x01\x00\x00')
		OutMaterial.write(b'\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F\x00\x00\xC0\x3F')
		OutMaterial.write(b'\x00\x00\xC8\x42\x00\x00\xC8\x42\x00\x00\xC8\x42\x00\x00\xC8\x42')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x7C\x01\x00\x00\x89\x01\x00\x00\x9D\x01\x00\x00\x41\x6E\x69\x6D')
		OutMaterial.write(b'\x44\x75\x72\x61\x74\x69\x6F\x6E\x00\x41\x6E\x69\x6D\x4E\x75\x6D')
		OutMaterial.write(b'\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x55\x00\x41\x6E\x69')
		OutMaterial.write(b'\x6D\x4E\x75\x6D\x62\x65\x72\x4F\x66\x46\x72\x61\x6D\x65\x73\x56')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xC0\x04\x1A\x37\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDIllumMap != '' and RasterIDIllumMap != '00_00_00_00':
			TexStateIllumMap = StringToID(RasterDict["IllumMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateIllumMap, RasterIDIllumMap)
			IDsList[TexStateIllumMap] = 'TextureState'
			if isIllumMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDIllumMap, RasterPathIllumMap)
				IDsList[RasterIDIllumMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateIllumMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDAnimMap != '' and RasterIDAnimMap != '00_00_00_00':
			TexStateAnimMap = StringToID(RasterDict["AnimMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateAnimMap, RasterIDAnimMap)
			IDsList[TexStateAnimMap] = 'TextureState'
			if isAnimMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDAnimMap, RasterPathAnimMap)
				IDsList[RasterIDAnimMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateAnimMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was using a generic vehicle black texture
			if game_version == "BPR":
				OutMaterial.write(b'\x12\x6C\x5E\xD3')	 #2F_A3_8A_82 is a grey shader texture
			elif game_version == "BP":
				OutMaterial.write(b'\x96\xF5\xE3\x08')
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterial_7B_7B_A2_8E_beta(srcPath, MaterialName, RasterDict, IDsList, verify_genericIDs, use_UniqueIDs, vehicleName, game_version):
	RasterIDLineMap = ''
	if "LineMap" in RasterDict:
		RasterIDLineMap, RasterPathLineMap = RasterDict["LineMap"]
		RasterIDLineMap, isLineMapGeneric = VerifyGenericIDs(game_version,RasterIDLineMap,verify_genericIDs)
	RasterIDLineMap = StringToID(RasterIDLineMap, use_UniqueIDs, vehicleName)
	RasterIDDetailMap = ''
	if "DetailMap" in RasterDict:
		RasterIDDetailMap, RasterPathDetailMap = RasterDict["DetailMap"]
		RasterIDDetailMap, isDetailMapGeneric = VerifyGenericIDs(game_version,RasterIDDetailMap,verify_genericIDs)
	RasterIDDetailMap = StringToID(RasterIDDetailMap, use_UniqueIDs, vehicleName)
	RasterIDBaseMap = ''
	if "BaseMap" in RasterDict:
		RasterIDBaseMap, RasterPathBaseMap = RasterDict["BaseMap"]
		RasterIDBaseMap, isBaseMapGeneric = VerifyGenericIDs(game_version,RasterIDBaseMap,verify_genericIDs)
	RasterIDBaseMap = StringToID(RasterIDBaseMap, use_UniqueIDs, vehicleName)
	RasterIDNormal = ''
	if "Normal" in RasterDict:
		RasterIDNormal, RasterPathNormal = RasterDict["Normal"]
		RasterIDNormal, isNormalGeneric = VerifyGenericIDs(game_version,RasterIDNormal,verify_genericIDs)
	RasterIDNormal = StringToID(RasterIDNormal, use_UniqueIDs, vehicleName)
	RasterIDNormalDetail = ''
	if "NormalDetail" in RasterDict:
		RasterIDNormalDetail, RasterPathNormalDetail = RasterDict["NormalDetail"]
		RasterIDNormalDetail, isNormalDetailGeneric = VerifyGenericIDs(game_version,RasterIDNormalDetail,verify_genericIDs)
	RasterIDNormalDetail = StringToID(RasterIDNormalDetail, use_UniqueIDs, vehicleName)
	RasterIDDiffuse = ''
	if "Diffuse" in RasterDict:
		RasterIDDiffuse, RasterPathDiffuse = RasterDict["Diffuse"]
		RasterIDDiffuse, isDiffuseGeneric = VerifyGenericIDs(game_version,RasterIDDiffuse,verify_genericIDs)
	RasterIDDiffuse = StringToID(RasterIDDiffuse, use_UniqueIDs, vehicleName)
	OutBasename = StringToID(MaterialName, use_UniqueIDs, vehicleName)
	MaterialPath = srcPath + "\\" + "Material" + "\\" + OutBasename + ".dat"
	with open(MaterialPath, "wb") as OutMaterial:
		OutMaterial.write(b'\x24\x00\x00\x00')
		OutMaterial.write(bytearray.fromhex(OutBasename.replace('_', '')))
		OutMaterial.write(b'\x02\x05\x05\x00\x64\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x01\x00\x00\x34\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x50\x9A\xC8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xD0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\x76\x8E\xD8\x00\x00\x00')
		OutMaterial.write(b'\x01\x03\x00\x00\x05\x00\x00\x00\xE0\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xE5\x00\x00\x00\x0C\x7B\x95\xC5\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEA\x00\x00\x00\x28\x10\x9B\xFB')
		OutMaterial.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xEF\x00\x00\x00')
		OutMaterial.write(b'\xF3\x11\xBA\xC6\x02\x00\x00\x00\x00\x00\x00\x00\xEF\xBE\xD0\xDA')
		OutMaterial.write(b'\xF4\x00\x00\x00\x6F\x74\x15\x3E\x03\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\xEF\xBE\xD0\xDA\xF9\x00\x00\x00\x24\x9D\x5C\xAB\x04\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x00\x00\xEF\xBE\xD0\xDA\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x00\x00\x00\xCD\xCD\xCD\xCD\xCD\xCD\xCD\xCD')
		OutMaterial.write(b'\xCD\xCD\xCD\xCD\xCD\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E')
		OutMaterial.write(b'\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x6E\x6F\x6E\x65\x00\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x10\x01\x00\x00\x14\x01\x00\x00\x30\x01\x00\x00')
		OutMaterial.write(b'\x01\x00\x00\x00\x20\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x1B\x1E\x2C\x48\x03\x00\x00\x00\x44\x01\x00\x00\x50\x01\x00\x00')
		OutMaterial.write(b'\x90\x01\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		OutMaterial.write(b'\x60\x01\x00\x00\x70\x01\x00\x00\x80\x01\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x90\x06\x29\x3F\x90\x06\x29\x3F\x90\x06\x29\x3F\x00\x00\x80\x3F')
		OutMaterial.write(b'\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41\x00\x00\xA0\x41')
		OutMaterial.write(b'\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40\x00\x00\x00\x40')
		OutMaterial.write(b'\xAA\x7C\xE2\xF6\x73\xE7\xE0\x81\x9F\x90\x73\x4A\x00\x00\x00\x00')
		OutMaterial.write(b'\x7B\x7B\xA2\x8E\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00')
		OutMaterial.write(b'\x9B\x9F\x65\xD4\x00\x00\x00\x00\x44\x00\x00\x00\x00\x00\x00\x00')
		#LineMapsLists = ['70_78_95_A6']
		#if RasterIDLineMap not in LineMapsLists: RasterIDLineMap = ''		#FIXAR
		if RasterIDLineMap != '' and RasterIDLineMap != '00_00_00_00':
			TexStateLineMap = StringToID(RasterDict["LineMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureStateLineMap(game_version, srcPath, TexStateLineMap, RasterIDLineMap)
			IDsList[TexStateLineMap] = 'TextureState'
			if isLineMapGeneric == False or use_UniqueIDs == True:
				CreateRasterLineMap(game_version, srcPath, RasterIDLineMap, RasterPathLineMap)
				IDsList[RasterIDLineMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateLineMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x31\x92\xB1\x67')		#D1_21_05_AF is a generic trk unit line map for road
			CreateTextureStateLineMap(game_version, srcPath, "31_92_B1_67", "D1_21_05_AF")
			IDsList["31_92_B1_67"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x74\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDDetailMap != '' and RasterIDDetailMap != '00_00_00_00':
			TexStateDetailMap = StringToID(RasterDict["DetailMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDetailMap, RasterIDDetailMap)
			IDsList[TexStateDetailMap] = 'TextureState'
			if isDetailMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDetailMap, RasterPathDetailMap)
				IDsList[RasterIDDetailMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDetailMap.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\x75\x48\x8C\xCE')		#0C_7A_20_E9 is a generic trk unit detail map for road
			CreateTextureState(game_version, srcPath, "75_48_8C_CE", "0C_7A_20_E9")
			IDsList["75_48_8C_CE"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x88\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDBaseMap != '' and RasterIDBaseMap != '00_00_00_00':
			TexStateBaseMap = StringToID(RasterDict["BaseMap"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateBaseMap, RasterIDBaseMap)
			IDsList[TexStateBaseMap] = 'TextureState'
			if isBaseMapGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDBaseMap, RasterPathBaseMap)
				IDsList[RasterIDBaseMap] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateBaseMap.replace('_', '')))
		elif RasterIDDiffuse != '' and RasterIDDiffuse != '00_00_00_00':
			TexStateDiffuse = StringToID(RasterDict["Diffuse"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateDiffuse, RasterIDDiffuse)
			IDsList[TexStateDiffuse] = 'TextureState'
			if isDiffuseGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDDiffuse, RasterPathDiffuse)
				IDsList[RasterIDDiffuse] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateDiffuse.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xE8\x80\x42\x53')		#76_6F_76_3D is a generic trk unit baseMap texture for road
			CreateTextureState(game_version, srcPath, "E8_80_42_53", "76_6F_76_3D")
			IDsList["E8_80_42_53"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\x9C\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormal != '' and RasterIDNormal != '00_00_00_00':
			TexStateNormal = StringToID(RasterDict["Normal"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormal, RasterIDNormal)
			IDsList[TexStateNormal] = 'TextureState'
			if isNormalGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormal, RasterPathNormal)
				IDsList[RasterIDNormal] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormal.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal (blue)
			OutMaterial.write(b'\xED\x82\xF7\xA4')		#88_79_A2_E0 is a generic trk unit normal texture
			CreateTextureState(game_version, srcPath, "ED_82_F7_A4", "88_79_A2_E0")
			IDsList["ED_82_F7_A4"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xB0\x00\x00\x00\x00\x00\x00\x00')
		if RasterIDNormalDetail != '' and RasterIDNormalDetail != '00_00_00_00':
			TexStateNormalDetail = StringToID(RasterDict["NormalDetail"][0] + "_texturestate", use_UniqueIDs, vehicleName)
			CreateTextureState(game_version, srcPath, TexStateNormalDetail, RasterIDNormalDetail)
			IDsList[TexStateNormalDetail] = 'TextureState'
			if isNormalDetailGeneric == False or use_UniqueIDs == True:
				CreateRaster(game_version, srcPath, RasterIDNormalDetail, RasterPathNormalDetail)
				IDsList[RasterIDNormalDetail] = 'Raster'
			OutMaterial.write(bytearray.fromhex(TexStateNormalDetail.replace('_', '')))
		else:
			#OutMaterial.write(b'\xB0\x37\xC7\x80')		#It was a generic vehicle black texture being used as normal detail (green-blue)
			OutMaterial.write(b'\xA1\x53\x76\x4C')		#AE_7E_C6_7D is a generic trk unit normal (green-blue) texture
			CreateTextureState(game_version, srcPath, "A1_53_76_4C", "AE_7E_C6_7D")
			IDsList["A1_53_76_4C"] = 'TextureState'
		OutMaterial.write(b'\x00\x00\x00\x00\xC4\x00\x00\x00\x00\x00\x00\x00')

def CreateVertexDesc(srcPath):
	VertexDesc1Path = srcPath + "\\" + "VertexDesc" + "\\" + "B8_23_13_0F" + ".dat"
	VertexDesc2Path = srcPath + "\\" + "VertexDesc" + "\\" + "7F_44_88_2B" + ".dat"
	VertexDesc3Path = srcPath + "\\" + "VertexDesc" + "\\" + "0E_46_97_8F" + ".dat"
	VertexDesc4Path = srcPath + "\\" + "VertexDesc" + "\\" + "9F_F0_42_9F" + ".dat"
	if not os.path.exists(srcPath + "\\" + "VertexDesc"):
		os.makedirs(srcPath + "\\" + "VertexDesc")
	with open(VertexDesc1Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x6A\xE0\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x3C\x00\x00\x00\x03\x00\x00\x00\x06\x00\x00\x00\x0C\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x3C\x00\x00\x00\x0F\x00\x00\x00\x06\x00\x00\x00')
		vd.write(b'\x18\x00\x00\x00\x00\x00\x00\x00\x3C\x00\x00\x00\x05\x00\x00\x00')
		vd.write(b'\x10\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00\x3C\x00\x00\x00')
		vd.write(b'\x06\x00\x00\x00\x10\x00\x00\x00\x2C\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x3C\x00\x00\x00\x0D\x00\x00\x00\x1E\x00\x00\x00\x34\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x3C\x00\x00\x00\x0E\x00\x00\x00\x1C\x00\x00\x00')
		vd.write(b'\x38\x00\x00\x00\x00\x00\x00\x00\x3C\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc2Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x2A\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x3C\x00\x00\x00\x03\x00\x00\x00\x06\x00\x00\x00\x0C\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x3C\x00\x00\x00\x05\x00\x00\x00\x10\x00\x00\x00')
		vd.write(b'\x24\x00\x00\x00\x00\x00\x00\x00\x3C\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc3Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x3C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc4Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x02\x60\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x3C\x00\x00\x00\x0D\x00\x00\x00\x1E\x00\x00\x00\x34\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x3C\x00\x00\x00\x0E\x00\x00\x00\x1C\x00\x00\x00')
		vd.write(b'\x38\x00\x00\x00\x00\x00\x00\x00\x3C\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreateVertexDesc_BP(srcPath):
	VertexDesc1Path = srcPath + "\\" + "VertexDesc" + "\\" + "B8_23_13_0F" + ".dat"
	VertexDesc2Path = srcPath + "\\" + "VertexDesc" + "\\" + "7F_44_88_2B" + ".dat"
	VertexDesc3Path = srcPath + "\\" + "VertexDesc" + "\\" + "0E_46_97_8F" + ".dat"
	VertexDesc4Path = srcPath + "\\" + "VertexDesc" + "\\" + "9F_F0_42_9F" + ".dat"
	if not os.path.exists(srcPath + "\\" + "VertexDesc"):
		os.makedirs(srcPath + "\\" + "VertexDesc")
	with open(VertexDesc1Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xCA\xC0\x20\x00\x07\x00\x00\x00')
		vd.write(b'\x00\x3C\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x0C\x00\x02\x00\x00\x00\x00\xFF\xFF\x03\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x18\x00\x02\x00\x00\x00\x00\xFF\xFF\x15\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x24\x00\x01\x00\x00\x00\x00\xFF\xFF\x06\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x2C\x00\x01\x00\x00\x00\x00\xFF\xFF\x07\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x34\x00\x05\x00\x00\x00\x00\xFF\xFF\x0E\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x38\x00\x08\x00\x00\x00\x00\xFF\xFF\x0F\x01\x00\x00\x00')
	with open(VertexDesc2Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x4A\x00\x00\x00\x03\x00\x00\x00')
		vd.write(b'\x00\x3C\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x0C\x00\x02\x00\x00\x00\x00\xFF\xFF\x03\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x24\x00\x01\x00\x00\x00\x00\xFF\xFF\x06\x01\x00\x00\x00')
	with open(VertexDesc3Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
	with open(VertexDesc4Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\xC0\x00\x00\x03\x00\x00\x00')
		vd.write(b'\x00\x3C\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x34\x00\x05\x00\x00\x00\x00\xFF\xFF\x0E\x01\x00\x00\x00')
		vd.write(b'\x00\x3C\x38\x00\x08\x00\x00\x00\x00\xFF\xFF\x0F\x01\x00\x00\x00')

def CreateVertexDescTRK(srcPath):
	VertexDesc1Path = srcPath + "\\" + "VertexDesc" + "\\" + "4C_66_C2_A5" + ".dat"
	VertexDesc2Path = srcPath + "\\" + "VertexDesc" + "\\" + "E1_74_B4_4A" + ".dat"
	VertexDesc1Path0x28 = srcPath + "\\" + "VertexDesc" + "\\" + "5B_96_3F_E2" + ".dat"
	VertexDesc2Path0x28 = srcPath + "\\" + "VertexDesc" + "\\" + "8C_24_A1_BD" + ".dat"
	if not os.path.exists(srcPath + "\\" + "VertexDesc"):
		os.makedirs(srcPath + "\\" + "VertexDesc")
	with open(VertexDesc1Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x6A\x80\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x34\x00\x00\x00\x03\x00\x00\x00\x06\x00\x00\x00\x0C\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x34\x00\x00\x00\x0F\x00\x00\x00\x06\x00\x00\x00')
		vd.write(b'\x18\x00\x00\x00\x00\x00\x00\x00\x34\x00\x00\x00\x05\x00\x00\x00')
		vd.write(b'\x10\x00\x00\x00\x24\x00\x00\x00\x00\x00\x00\x00\x34\x00\x00\x00')
		vd.write(b'\x06\x00\x00\x00\x10\x00\x00\x00\x2C\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x34\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc2Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x34\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc1Path0x28, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x6A\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x28\x00\x00\x00\x03\x00\x00\x00\x06\x00\x00\x00\x0C\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x28\x00\x00\x00\x05\x00\x00\x00\x10\x00\x00\x00')
		vd.write(b'\x18\x00\x00\x00\x00\x00\x00\x00\x28\x00\x00\x00\x06\x00\x00\x00')
		vd.write(b'\x10\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x28\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(VertexDesc2Path0x28, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x01\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		vd.write(b'\x28\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreateVertexDescTRK_BP(srcPath):
	VertexDesc1Path = srcPath + "\\" + "VertexDesc" + "\\" + "4C_66_C2_A5" + ".dat"
	VertexDesc2Path = srcPath + "\\" + "VertexDesc" + "\\" + "E1_74_B4_4A" + ".dat"
	VertexDesc1Path0x28 = srcPath + "\\" + "VertexDesc" + "\\" + "5B_96_3F_E2" + ".dat"
	VertexDesc2Path0x28 = srcPath + "\\" + "VertexDesc" + "\\" + "8C_24_A1_BD" + ".dat"
	if not os.path.exists(srcPath + "\\" + "VertexDesc"):
		os.makedirs(srcPath + "\\" + "VertexDesc")
	with open(VertexDesc1Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xCA\x00\x20\x00\x05\x00\x00\x00')
		vd.write(b'\x00\x34\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
		vd.write(b'\x00\x34\x0C\x00\x02\x00\x00\x00\x00\xFF\xFF\x03\x01\x00\x00\x00')
		vd.write(b'\x00\x34\x18\x00\x02\x00\x00\x00\x00\xFF\xFF\x15\x01\x00\x00\x00')
		vd.write(b'\x00\x34\x24\x00\x01\x00\x00\x00\x00\xFF\xFF\x06\x01\x00\x00\x00')
		vd.write(b'\x00\x34\x2C\x00\x01\x00\x00\x00\x00\xFF\xFF\x07\x01\x00\x00\x00')
	with open(VertexDesc2Path, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x00\x34\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
	with open(VertexDesc1Path0x28, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\xCA\x00\x00\x00\x04\x00\x00\x00')
		vd.write(b'\x00\x28\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')
		vd.write(b'\x00\x28\x0C\x00\x02\x00\x00\x00\x00\xFF\xFF\x03\x01\x00\x00\x00')
		vd.write(b'\x00\x28\x18\x00\x01\x00\x00\x00\x00\xFF\xFF\x06\x01\x00\x00\x00')
		vd.write(b'\x00\x28\x20\x00\x01\x00\x00\x00\x00\xFF\xFF\x07\x01\x00\x00\x00')
	with open(VertexDesc2Path0x28, "wb") as vd:
		vd.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00')
		vd.write(b'\x00\x28\x00\x00\x02\x00\x00\x00\x00\xFF\xFF\x01\x01\x00\x00\x00')

def CreateTextureState(game_version, srcPath, TexStateID, RasterID):
	TexStatePath = srcPath + "\\" + "TextureState" + "\\" + TexStateID + ".dat"
	if not os.path.exists(srcPath + "\\" + "TextureState"):
		os.makedirs(srcPath + "\\" + "TextureState")
	TexState = open(TexStatePath, "wb")
	value1 = -0.9
	if RasterID == 'B1_6F_7B_68':
		value1 = 0
	if game_version == "BPR":
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(b'\xFF\xFF\x7F\xFF')
		TexState.write(b'\xFF\xFF\x7F\x7F')
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<f", value1))
		TexState.write(b'\xFF\xFF\xFF\xFF')
		TexState.write(struct.pack("<i", 0))			#Change sometimes
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(bytearray.fromhex(RasterID.replace('_', '')))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0x38))
		TexState.write(struct.pack("<i", 0))
	elif game_version == "BP":
		# 0x0
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 2))
		# 0x10
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		# 0x20
		TexState.write(struct.pack("<f", value1))		#Change sometimes
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		# 0x30
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 0))
		# 0x40
		TexState.write(bytearray.fromhex(RasterID.replace('_', '')))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0x3C))
		TexState.write(struct.pack("<i", 0))
	TexState.close()

def CreateTextureStateLineMap(game_version, srcPath, TexStateID, RasterID):
	TexStatePath = srcPath + "\\" + "TextureState" + "\\" + TexStateID + ".dat"
	if not os.path.exists(srcPath + "\\" + "TextureState"):
		os.makedirs(srcPath + "\\" + "TextureState")
	TexState = open(TexStatePath, "wb")
	value1 = 0.0
	if RasterID == 'B1_6F_7B_68':
		value1 = 0
	if game_version == "BPR":
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 1))
		TexState.write(b'\xFF\xFF\x7F\xFF')
		TexState.write(b'\xFF\xFF\x7F\x7F')
		TexState.write(struct.pack("<i", 8))
		TexState.write(struct.pack("<f", value1))
		TexState.write(b'\xFF\xFF\xFF\xFF')
		TexState.write(struct.pack("<i", 0))			#Change sometimes
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(bytearray.fromhex(RasterID.replace('_', '')))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0x38))
		TexState.write(struct.pack("<i", 0))
	elif game_version == "BP":
		# 0x0
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 2))
		# 0x10
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 2))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		# 0x20
		TexState.write(struct.pack("<f", value1))		#Change sometimes
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 1))
		# 0x30
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 1))
		TexState.write(struct.pack("<i", 0))
		# 0x40
		TexState.write(bytearray.fromhex(RasterID.replace('_', '')))
		TexState.write(struct.pack("<i", 0))
		TexState.write(struct.pack("<i", 0x3C))
		TexState.write(struct.pack("<i", 0))
	TexState.close()

def CreateMaterialState(srcPath):
	MatStateDir = srcPath + "\\" + "MaterialState"
	MatStatePath1 = MatStateDir + "\\" + "26_A0_72_7E" + ".dat"
	MatStatePath2 = MatStateDir + "\\" + "62_15_71_78" + ".dat"
	MatStatePath3 = MatStateDir + "\\" + "9B_9F_65_D4" + ".dat"
	MatStatePath4 = MatStateDir + "\\" + "B9_BE_2F_14" + ".dat"
	MatStatePath5 = MatStateDir + "\\" + "CD_F0_44_F7" + ".dat"
	MatStatePath6 = MatStateDir + "\\" + "EC_4F_6F_B4" + ".dat"
	MatStatePath7 = MatStateDir + "\\" + "F0_46_DA_CD" + ".dat"
	MatStatePath8 = MatStateDir + "\\" + "FE_64_A3_0B" + ".dat"
	if MatStatePath1 is None:
		return 0
	if not os.path.exists(MatStateDir):
		os.makedirs(MatStateDir)
	with open(MatStatePath1, "wb") as mts1:
		mts1.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8A\x49\x31\x01')
		mts1.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts1.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts1.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x01\x00\x8C\x03')
		mts1.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x76\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath2, "wb") as mts2:
		mts2.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8A\x49\x31\x01')
		mts2.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts2.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts2.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x02\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath3, "wb") as mts3:
		mts3.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8A\x49\x31\x79')
		mts3.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts3.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts3.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x93\x03')
		mts3.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x48\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath4, "wb") as mts4:
		mts4.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8B\x49\x31\x79')
		mts4.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts4.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts4.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x07\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath5, "wb") as mts5:
		mts5.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8B\x49\x31\x79')
		mts5.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts5.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts5.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x01\x00\x8C\x03')
		mts5.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts5.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x76\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath6, "wb") as mts6:
		mts6.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8B\x49\x31\x79')
		mts6.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts6.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts6.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x5E\x00')
		mts6.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x00\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath7, "wb") as mts7:
		mts7.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8A\x49\x31\x79')
		mts7.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts7.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts7.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x03\x01')
		mts7.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x50\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath8, "wb") as mts8:
		mts8.write(b'\x0C\x00\x00\x00\x48\x00\x00\x00\x88\x00\x00\x00\x8A\x49\x31\x79')
		mts8.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79')
		mts8.write(b'\x8A\x49\x31\x79\x8A\x49\x31\x79\x8A\x49\x31\x79\x00\x00\x80\x3F')
		mts8.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x01\x00\x86\x03')
		mts8.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01\x01\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x00\x01\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreateMaterialState_BP(srcPath):
	MatStateDir = srcPath + "\\" + "MaterialState"
	MatStatePath1 = MatStateDir + "\\" + "26_A0_72_7E" + ".dat"
	MatStatePath2 = MatStateDir + "\\" + "62_15_71_78" + ".dat"
	MatStatePath3 = MatStateDir + "\\" + "9B_9F_65_D4" + ".dat"
	MatStatePath4 = MatStateDir + "\\" + "B9_BE_2F_14" + ".dat"
	MatStatePath5 = MatStateDir + "\\" + "CD_F0_44_F7" + ".dat"
	MatStatePath6 = MatStateDir + "\\" + "EC_4F_6F_B4" + ".dat"
	MatStatePath7 = MatStateDir + "\\" + "F0_46_DA_CD" + ".dat"
	MatStatePath8 = MatStateDir + "\\" + "FE_64_A3_0B" + ".dat"
	if MatStatePath1 is None:
		return 0
	if not os.path.exists(MatStateDir):
		os.makedirs(MatStateDir)
	with open(MatStatePath1, "wb") as mts1:	# 7B_00_AB_82, but named as 26_A0_72_7E
		mts1.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x22\x01\x22\x01')
		mts1.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts1.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x05\x00\x00\x00')
		mts1.write(b'\x80\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts1.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts1.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts1.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts1.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath2, "wb") as mts2:	# DA_39_D6_F9, but named as 62_15_71_78
		mts2.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x22\x01\x22\x01')
		mts2.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts2.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts2.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts2.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts2.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts2.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath3, "wb") as mts3:	# 54 34 D7 81 and AF F8 EF 55, but named as 9B_9F_65_D4
		mts3.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x22\x01\x22\x01')
		mts3.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')	# The first byte (0x0F) is 0x0 in the materialState AF F8 EF 55
		mts3.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts3.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts3.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts3.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts3.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath4, "wb") as mts4:	# 83_F9_9E_5F, but named as B9_BE_2F_14
		mts4.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x25\x06\x25\x06')
		mts4.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts4.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts4.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x05\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts4.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts4.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts4.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath5, "wb") as mts5:	# 99 55 82 56, but named as CD_F0_44_F7
		mts5.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x25\x06\x25\x06')
		mts5.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts5.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts5.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x05\x00\x00\x00')
		mts5.write(b'\x40\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts5.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts5.write(b'\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts5.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts5.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath6, "wb") as mts6:	# F4 1E 6C 71, but named as EC_4F_6F_B4
		mts6.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x25\x06\x25\x06')
		mts6.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts6.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts6.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts6.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts6.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts6.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath7, "wb") as mts7:	# 50_BF_2E_A0 and 41_FA_B0_10, but named as F0_46_DA_CD
		mts7.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x22\x01\x22\x01')
		mts7.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')	# The first byte (0x0F) is 0x0 in the materialState 41_FA_B0_10
		mts7.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts7.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts7.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts7.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	with open(MatStatePath8, "wb") as mts8:	# C3_49_AA_A3 and 1C_2C_72_89, but named as FE_64_A3_0B
		mts8.write(b'\x0C\x00\x00\x00\x54\x00\x00\x00\x9C\x00\x00\x00\x22\x01\x22\x01')
		mts8.write(b'\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00\x0F\x00\x00\x00')
		mts8.write(b'\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F\x00\x00\x80\x3F')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x05\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x0F\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')	# The byte 0x01 is 0x0 in the materialState 1C_2C_72_89
		mts8.write(b'\x01\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts8.write(b'\xFF\xFF\xFF\xFF\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
		mts8.write(b'\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		mts8.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreateRaster(game_version, srcPath, RasterID, RasterPath):
	if RasterPath == '': return
	RasterName, extension = os.path.splitext(os.path.basename(RasterPath))
	RasterFolder = os.path.dirname(RasterPath)
	OutRasterPath = srcPath + "\\" + "Raster" + "\\" + RasterID + ".dds"
	OutRasterHeaderPath = srcPath + "\\" + "Raster" + "\\" + RasterID + ".dat"
	OutRasterBodyPath = srcPath + "\\" + "Raster" + "\\" + RasterID + "_texture.dat"
	if not os.path.exists(srcPath + "\\" + "Raster"):
		os.makedirs(srcPath + "\\" + "Raster")
	if extension != ".Editeddds":								# FIX
		ImageToDDS(srcPath, RasterID, RasterPath, OutRasterPath)
	else:
		shutil.copy2(RasterPath, OutRasterPath)
	with open(OutRasterPath, "rb") as tex:
		tex.seek(0xC, 0)
		imgHeight, imgWidth = struct.unpack("<ii", tex.read(8))
		tex.seek(0x8, 1)
		mipCount = struct.unpack("<i", tex.read(4))[0]
		tex.seek(0x54, 0)
		imgFmt2 = tex.read(4)
		imgFmt = 0
		#DXT1
		if imgFmt2 == b'\x44\x58\x54\x31':
			imgFmt = 0x47
		#DXT5
		elif imgFmt2 == b'\x44\x58\x54\x35':
			imgFmt = 0x4D
		#RGBA
		elif imgFmt2 == b'\x15\x00\x00\x00':
			imgFmt = 0x1C
		# Unknow
		else:
			print("Image format not recognize, please save the image in dxt5 or dxt1")
			print("Image", RasterPath)
		#elif imgFmt == 0x3D:
		#	imgFmt2 = b'\x15\x00\x00\x00'
		tex.seek(0x80, 0)
		texLen = os.path.getsize(OutRasterPath) - 0x80
		texData = tex.read(texLen)
		RasterHeader = open(OutRasterHeaderPath, "wb")
		if game_version == "BPR":
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 7))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			#RasterHeader.write(imgFmt)
			RasterHeader.write(struct.pack("<i", imgFmt))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<H", imgWidth))
			RasterHeader.write(struct.pack("<H", imgHeight))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", mipCount))
			RasterHeader.write(struct.pack("<H", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0x5))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(b'\x50\xEE\xAF\x07')
			RasterHeader.write(struct.pack("<i", 0))
		elif game_version == "BP":
			#0x10
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			#0x20
			RasterHeader.write(imgFmt2)
			RasterHeader.write(struct.pack("<H", imgWidth))
			RasterHeader.write(struct.pack("<H", imgHeight))
			RasterHeader.write(struct.pack("<B", 1))	# Always 0x01?
			RasterHeader.write(struct.pack("<B", mipCount))
			RasterHeader.write(struct.pack("<B", 0))	# Always 0x00?
			RasterHeader.write(struct.pack("<B", 8))	# Always 0x08?
			RasterHeader.write(struct.pack("<i", 0))	# Always 0?
		RasterHeader.close()
		RasterTex = open(OutRasterBodyPath, "wb")
		RasterTex.write(texData)
		RasterTex.close()
	os.remove(OutRasterPath)

def CreateRasterLineMap(game_version, srcPath, RasterID, RasterPath):
	if RasterPath == '': return
	RasterName, extension = os.path.splitext(os.path.basename(RasterPath))
	RasterFolder = os.path.dirname(RasterPath)
	OutRasterPath = srcPath + "\\" + "Raster" + "\\" + RasterID + ".dds"
	OutRasterHeaderPath = srcPath + "\\" + "Raster" + "\\" + RasterID + ".dat"
	OutRasterBodyPath = srcPath + "\\" + "Raster" + "\\" + RasterID + "_texture.dat"
	if not os.path.exists(srcPath + "\\" + "Raster"):
		os.makedirs(srcPath + "\\" + "Raster")
	if extension != ".Editeddds":								# FIX
		ImageToDDS(srcPath, RasterID, RasterPath, OutRasterPath)
	else:
		shutil.copy2(RasterPath, OutRasterPath)
	with open(OutRasterPath, "rb") as tex:
		tex.seek(0xC, 0)
		imgHeight, imgWidth = struct.unpack("<ii", tex.read(8))
		tex.seek(0x8, 1)
		mipCount = struct.unpack("<i", tex.read(4))[0]
		tex.seek(0x54, 0)
		imgFmt2 = tex.read(4)
		#DXT1
		if imgFmt2 == b'\x44\x58\x54\x31':
			imgFmt = 0x47
		#DXT5
		elif imgFmt2 == b'\x44\x58\x54\x35':
			imgFmt = 0x4D
		#RGBA
		elif imgFmt2 == b'\x15\x00\x00\x00':
			imgFmt = 0x1C
		else:
			print("Image format not recognize, please save the image in dxt5 or dxt1")
			print("Image", RasterPath)
		#elif imgFmt == 0x3D:
		#	imgFmt2 = b'\x15\x00\x00\x00'
		tex.seek(0x80, 0)
		texLen = os.path.getsize(OutRasterPath) - 0x80
		texData = tex.read(texLen)
		RasterHeader = open(OutRasterHeaderPath, "wb")
		if game_version == "BPR":
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 7))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			#RasterHeader.write(imgFmt)
			RasterHeader.write(struct.pack("<i", imgFmt))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<H", imgWidth))
			RasterHeader.write(struct.pack("<H", imgHeight))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", mipCount))
			RasterHeader.write(struct.pack("<H", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0x5))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(b'\xB4\xE9\xAF\x07')			#Different
			RasterHeader.write(struct.pack("<i", 0))
		elif game_version == "BP":
			#0x10
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			#0x20
			RasterHeader.write(imgFmt2)
			RasterHeader.write(struct.pack("<H", imgWidth))
			RasterHeader.write(struct.pack("<H", imgHeight))
			RasterHeader.write(struct.pack("<B", 1))	# Always 0x01?
			RasterHeader.write(struct.pack("<B", mipCount))
			RasterHeader.write(struct.pack("<B", 0))	# Always 0x00?
			RasterHeader.write(struct.pack("<B", 8))	# Always 0x08?
			RasterHeader.write(struct.pack("<i", 0))	# Always 0?
		RasterHeader.close()
		RasterTex = open(OutRasterBodyPath, "wb")
		RasterTex.write(texData)
		RasterTex.close()
	os.remove(OutRasterPath)

def CreateWhiteRaster(game_version, srcPath):
	OutPathHeader = srcPath + "\\" + "Raster" + "\\" +  "57_48_54_C9" + ".dat"
	OutPathTexture = srcPath + "\\" + "Raster" + "\\" +  "57_48_54_C9" + "_texture.dat"
	if os.path.exists(OutPathHeader):
		os.remove(OutPathHeader)
	if os.path.exists(OutPathTexture):
		os.remove(OutPathTexture)
	if not os.path.exists(srcPath + "\\" + "Raster"):
		os.makedirs(srcPath + "\\" + "Raster")
	with open(OutPathHeader, "wb") as RasterHeader:
		if game_version == "BPR":
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 7))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0x4D))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<H", 0x10))
			RasterHeader.write(struct.pack("<H", 0x10))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<H", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", 0x5))
			RasterHeader.write(struct.pack("<H", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0xC0))
			RasterHeader.write(struct.pack("<B", 0x5))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(b'\x50\xEE\xAF\x07')
			RasterHeader.write(struct.pack("<i", 0))
		elif game_version == "BP":
			#0x10
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<i", 0))
			RasterHeader.write(struct.pack("<B", 1))
			RasterHeader.write(struct.pack("<B", 0))
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			RasterHeader.write(struct.pack("<B", 0))	# Sometimes is 0x1(normal?)
			#0x20
			RasterHeader.write(b'\x44\x58\x54\x35')
			RasterHeader.write(struct.pack("<H", 0x10))
			RasterHeader.write(struct.pack("<H", 0x10))
			RasterHeader.write(struct.pack("<B", 1))	# Always 0x01?
			RasterHeader.write(struct.pack("<B", 0x5))
			RasterHeader.write(struct.pack("<B", 0))	# Always 0x00?
			RasterHeader.write(struct.pack("<B", 8))	# Always 0x08?
			RasterHeader.write(struct.pack("<i", 0))	# Always 0?
	with open(OutPathTexture, "wb") as RasterTex:
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00\x00\x00\x00\x00\x00')
		RasterTex.write(b'\x00\x05\x3F\xF0\x03\x00\x00\x00\xFF\xFF\x00\x00\xF0\xF0\xFF\xFF')
		RasterTex.write(b'\x00\x05\x07\x00\x00\x00\x00\x00\xFF\xFF\x00\x00\xFC\xFF\xFF\xFF')

def EditDeformationSpec(srcPath, vehicleName, skeletonName, EffectsDummyHelperList, BoneCoordsList, use_Damage):
	mainPath = os.path.dirname(srcPath)
	DeformationSpecID = StringToID(vehicleName + "deformationmodel")
	DeformationSpecDir = srcPath + "\\" + "StreamedDeformationSpec"
	DeformationSpecPath = DeformationSpecDir + "\\" + DeformationSpecID + ".dat"
	if DeformationSpecPath is None:
		return 0
	if not os.path.exists(DeformationSpecDir):
		os.makedirs(DeformationSpecDir)
	if skeletonName != "":
		LibraryPath = BurnoutLibraryGet()
		skeletonID = StringToID(skeletonName + "deformationmodel")
		SkeletonPathBPR = LibraryPath + "\\" + "BPR_Library_PC" + "\\" + "StreamedDeformationSpec" + "\\" + skeletonID + ".dat"
		if os.path.isfile(srcPath + "\\" + skeletonID + ".dat"):
			DeformationPath = srcPath + "\\" + skeletonID + ".dat"
		elif os.path.isfile(SkeletonPathBPR):
			DeformationPath = SkeletonPathBPR
		else:
			return 0
	else:
		if os.path.isfile(srcPath + "\\" + "Skeleton" + ".dat"):
			DeformationPath = srcPath + "\\" + "Skeleton" + ".dat"
		elif os.path.isfile(srcPath + "\\" + "Bones" + ".dat"):
			DeformationPath = srcPath + "\\" + "Bones" + ".dat"
		else:
			return 0
	shutil.copy2(DeformationPath, DeformationSpecPath)
	with open(DeformationSpecPath, "rb") as f:
		DefaultPCoords = [[0,0,0]]
		bonePCoords = [[0,0,0] for _ in range(0,20)]
		f.seek(0x4, 0)
		BonesPositions = struct.unpack("<i", f.read(4))[0]
		f.seek(0x14, 0)
		animBlockOffset, numAnims = struct.unpack("<ii", f.read(8))
		f.seek(0x8, 1)
		numBoosts, boostBlockOffset = struct.unpack("<ii", f.read(8))
		numStuffs, stuffBlockOffset = struct.unpack("<ii", f.read(8))
		numLights, lightBlockOffset = struct.unpack("<ii", f.read(8))
		f.seek(BonesPositions - 0x40, 0)
		DefaultPCoords[0][0], DefaultPCoords[0][1], DefaultPCoords[0][2] = struct.unpack("<fff", f.read(12))
		f.seek(0x110, 0)
		for i in range(0, 20):
			bonePCoords[i][0], bonePCoords[i][1], bonePCoords[i][2] = struct.unpack("<fff", f.read(12))
			bonePCoords[i][0] = bonePCoords[i][0] + DefaultPCoords[0][0]
			bonePCoords[i][1] = bonePCoords[i][1] + DefaultPCoords[0][1]
			bonePCoords[i][2] = bonePCoords[i][2] + DefaultPCoords[0][2]
			f.seek(0x34, 1)
		f.seek(0x70, 0)
		WheelFRoffset = struct.unpack("<B", f.read(1))[0]*0x50 + BonesPositions
		f.seek(0x2F, 1)
		WheelFLoffset = struct.unpack("<B", f.read(1))[0]*0x50 + BonesPositions
		f.seek(0x2F, 1)
		WheelRRoffset = struct.unpack("<B", f.read(1))[0]*0x50 + BonesPositions
		f.seek(0x2F, 1)
		WheelRLoffset = struct.unpack("<B", f.read(1))[0]*0x50 + BonesPositions
		
	OutanimBlockOffset = (numAnims-1)*0x1E0 + animBlockOffset
	OutnumAnims = 1
	with open(DeformationSpecPath, "r+b") as f:
		f.seek(0x14, 0)
		f.write(struct.pack("<ii", OutanimBlockOffset,OutnumAnims))
		f.seek(0x24, 0)
		f.write(struct.pack("<i", 0))	#Remove boost effects		# It should be 0x24 instead of 0x2C
		f.seek(0x34, 0)
		f.write(struct.pack("<i", 0))	#Remove light effects
		
		# Reading original data
		f.seek(boostBlockOffset, 0)
		boost = f.read(numBoosts*0x50)
		f.seek(stuffBlockOffset, 0)
		stuff = f.read(numStuffs*0x50)
		f.seek(lightBlockOffset, 0)
		light = f.read(numLights*0x50)
		
		# Boost effects
		f.seek(boostBlockOffset, 0)
		numBoosts = 0
		numLights = 0
		for i in range (0, len(EffectsDummyHelperList)):
			if "wheel" == EffectsDummyHelperList[i][0].lower():
				if "fr" == EffectsDummyHelperList[i][1].lower():
					WheelOffset0 = 0x50
					WheelOffset = WheelFRoffset
					#f.seek(WheelFRoffset, 0)
				elif "fl" == EffectsDummyHelperList[i][1].lower():
					WheelOffset0 = 0x80
					WheelOffset = WheelFLoffset
					#f.seek(WheelFLoffset, 0)
				elif "rr" == EffectsDummyHelperList[i][1].lower():
					WheelOffset0 = 0xB0
					WheelOffset = WheelRRoffset
					#f.seek(WheelRRoffset, 0)
				elif "rl" == EffectsDummyHelperList[i][1].lower():
					WheelOffset0 = 0xE0
					WheelOffset = WheelRLoffset
					#f.seek(WheelRLoffset, 0)
				f.seek(WheelOffset0, 0)
				x = EffectsDummyHelperList[i][2] - DefaultPCoords[0][0]
				y = EffectsDummyHelperList[i][4] - DefaultPCoords[0][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - DefaultPCoords[0][2]
				f.write(struct.pack("<fff", x,y,z))
				f.seek(WheelOffset, 0)
				f.seek(0x3C,1)
				ParentBone1, null, ParentBone2, null = struct.unpack("<BBBB", f.read(4))
				f.seek(-0x40,1)
				x = EffectsDummyHelperList[i][2] - bonePCoords[ParentBone1][0]
				y = EffectsDummyHelperList[i][4] - bonePCoords[ParentBone1][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - bonePCoords[ParentBone1][2]
				f.write(struct.pack("<fff", x,y,z))
				f.seek(0x4,1)
				x = EffectsDummyHelperList[i][2] - bonePCoords[ParentBone2][0]
				y = EffectsDummyHelperList[i][4] - bonePCoords[ParentBone2][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - bonePCoords[ParentBone2][2]
				f.write(struct.pack("<fff", x,y,z))
				f.seek(0x4,1)
				x = EffectsDummyHelperList[i][2] - DefaultPCoords[0][0]
				y = EffectsDummyHelperList[i][4] - DefaultPCoords[0][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - DefaultPCoords[0][2]
				f.write(struct.pack("<fff", x,y,z))
			elif "boost" == EffectsDummyHelperList[i][0].lower():
				f.seek(boostBlockOffset + numBoosts*0x50, 0)
				numBoosts += 1
				f.write(b'\x00\x00\x80\xBF\x00\x00\x00\x00\x00\x30\x0D\xA5\x00\x00\x00\x00')
				f.write(b'\x00\x00\x00\x00\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
				f.write(b'\x00\x30\x0D\x25\x00\x00\x00\x00\x00\x00\x80\xBF\x00\x00\x00\x00')
				x = EffectsDummyHelperList[i][2] - DefaultPCoords[0][0]
				y = EffectsDummyHelperList[i][4] - DefaultPCoords[0][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - DefaultPCoords[0][2]
				f.write(struct.pack("<ffff", x,y,z,1))
				BoneIndex1, BoneIndex2, BoneIndex3, BoneWeight1, BoneWeight2, BoneWeight3 = NearestPoints(EffectsDummyHelperList[i][2],EffectsDummyHelperList[i][4],-EffectsDummyHelperList[i][3],0,0,BoneCoordsList[:-4])
				#BoneIndex1 += 1		# Not sure why it's better with + 1, verify
				if use_Damage == False:
					BoneIndex1 = 0x0	# or 0xFF (idk)
				if "l1" == EffectsDummyHelperList[i][1].lower():	#Outside
					f.write(b'\x29\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "r1" == EffectsDummyHelperList[i][1].lower():	#Outside
					f.write(b'\x2A\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "l2" == EffectsDummyHelperList[i][1].lower():	#Inside
					f.write(b'\x2B\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "r2" == EffectsDummyHelperList[i][1].lower():	#Inside
					f.write(b'\x2C\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				else:
					f.write(b'\x29\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				stuffBlockOffset = f.tell()
				lightBlockOffset = stuffBlockOffset + numStuffs*0x50
		for i in range (0, len(EffectsDummyHelperList)):
			if "light" == EffectsDummyHelperList[i][0].lower():
				f.seek(lightBlockOffset + numLights*0x50, 0)
				numLights += 1
				f.write(b'\x00\x00\x80\xBF\x00\x00\x00\x00\x00\x4C\x23\xA6\x00\x00\x00\x00')
				f.write(b'\x00\x00\x00\x00\x00\x00\x80\x3F\x00\x00\x00\x00\x00\x00\x00\x00')
				f.write(b'\x00\x4C\x23\x26\x00\x00\x00\x00\x00\x00\x80\xBF\x00\x00\x00\x00')
				x = EffectsDummyHelperList[i][2] - DefaultPCoords[0][0]
				y = EffectsDummyHelperList[i][4] - DefaultPCoords[0][1]		#z = y
				z = -EffectsDummyHelperList[i][3] - DefaultPCoords[0][2]
				f.write(struct.pack("<ffff", x,y,z,1))
				BoneIndex1, BoneIndex2, BoneIndex3, BoneWeight1, BoneWeight2, BoneWeight3 = NearestPoints(EffectsDummyHelperList[i][2],EffectsDummyHelperList[i][4],-EffectsDummyHelperList[i][3],0,0,BoneCoordsList[:-4])
				#BoneIndex1 += 1		# Not sure why it's better with + 1, verify
				if use_Damage == False:
					BoneIndex1 = 0x0	# or 0xFF (idk)
				if "brakel" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0B\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "braker" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0C\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "brake" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0B\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "high-beaml" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x01\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "high-beamr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x02\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "high-beam" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x01\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "blinkerl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x07\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "blinkerr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x08\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "blinker" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x07\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "taill" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x03\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "tailr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x04\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "tail" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x03\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "reversingl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0E\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "reversingr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0F\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "reversing" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0E\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				# The next lights were made by Piotrek, special thanks to him
				#Front-Blinker
				elif "front-blinkerl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x07\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "front-blinkerr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x08\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "front-blinker" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x07\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Rear-Blinker
				elif "rear-blinkerl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x09\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "rear-blinkerr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0A\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "rear-blinker" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x09\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Spot
				elif "spotl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x05\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "spotr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x06\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "spot" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x05\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Spotlight
				elif "spotlightl" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x10\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "spotlightr" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x11\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "spotlight" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x10\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#BrakeCentre
				elif "brakecentre" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x0D\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Police (from citizen)
				elif "policedefaultred" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x12\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "policedefaultblue" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x13\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Police (PCPD DLC seem to be the same as citizen one)
				elif "policered" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x3A\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "policeblue" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x40\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#White flashing light (rear)
				elif "policewhite" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x45\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#Strong blue light facing rear (probably from Manhattan Spirit with no animation)
				elif "bluest1" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x41\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "bluest2" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x42\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "bluest3" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x43\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				elif "bluest4" == EffectsDummyHelperList[i][1].lower():
					f.write(b'\x44\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
				#else
				else:
					f.write(b'\x0B\x00\x00\x00\xFF\xFF')
					f.write(struct.pack("<B", BoneIndex1))
					f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.seek(stuffBlockOffset,0)
		f.write(stuff)
		if numLights == 0:
			f.seek(lightBlockOffset,0)
			f.write(light)
		f.seek(0x24, 0)
		f.write(struct.pack("<ii", numBoosts,boostBlockOffset))
		f.write(struct.pack("<ii", numStuffs,stuffBlockOffset))
		f.write(struct.pack("<ii", numLights,lightBlockOffset))

def MoveAttribsys(srcPath, vehicleName, skeletonName):
	mainPath = os.path.dirname(srcPath)
	AttribsysID = StringToID(vehicleName + "_attribsys")
	AttribsysSkeletonID = StringToID(skeletonName + "_attribsys")
	AttribsysDir = srcPath + "\\" + "AttribSysVault"
	AttribsysPath = AttribsysDir + "\\" + AttribsysID + ".dat"
	if AttribsysPath is None:
		return 0
	if not os.path.exists(AttribsysDir):
		os.makedirs(AttribsysDir)
	LibraryPath = BurnoutLibraryGet()
	AttribsysPathBPR = LibraryPath + "\\" + "BPR_Library_PC" + "\\" + "AttribSysVault" + "\\" + AttribsysID + ".dat"
	AttribsysSkeletonPathBPR = LibraryPath + "\\" + "BPR_Library_PC" + "\\" + "AttribSysVault" + "\\" + AttribsysSkeletonID + ".dat"
	if os.path.isfile(srcPath + "\\" + AttribsysID + ".dat"):	# Search in the vehicle folder
		ATPath = srcPath + "\\" + AttribsysID + ".dat"
	elif os.path.isfile(AttribsysPathBPR):						# Search in the library folder for the Vehicle attribsys
		ATPath = AttribsysPathBPR
	elif os.path.isfile(AttribsysSkeletonPathBPR):				# Search in the library folder for the Skeleton attribsys
		print("Attribsys file of the base car. Remember to edit the vehiclelist.")
		ATPath = AttribsysSkeletonPathBPR
	else:
		return 0
	shutil.copy2(ATPath, AttribsysPath)		

def MoveDeformationSpec(srcPath, vehicleName):
	mainPath = os.path.dirname(srcPath)
	DeformationSpecID = StringToID(vehicleName + "deformationmodel")
	DeformationSpecDir = srcPath + "\\" + "StreamedDeformationSpec"
	DeformationSpecPath = DeformationSpecDir + "\\" + DeformationSpecID + ".dat"
	if DeformationSpecPath is None:
		return 0
	if not os.path.exists(DeformationSpecDir):
		os.makedirs(DeformationSpecDir)
	LibraryPath = BurnoutLibraryGet()
	DeformationSpecBPR = LibraryPath + "\\" + "BPR_Library_PC" + "\\" + "StreamedDeformationSpec" + "\\" + DeformationSpecID + ".dat"
	if os.path.isfile(srcPath + "\\" + DeformationSpecID + ".dat"):
		ATPath = srcPath + "\\" + DeformationSpecID + ".dat"
	elif os.path.isfile(DeformationSpecBPR):
		ATPath = DeformationSpecBPR
	else:
		return 0
	shutil.copy2(ATPath, DeformationSpecPath)	

def CreateVanm(srcPath, vehicleName, ModelNames, DummyHelperList, Transform):
	VehicleAnimationID = StringToID(vehicleName + "_vanm")
	VanmDir = srcPath + "\\" + "VehicleAnimation"
	VanmPath = VanmDir + "\\" + VehicleAnimationID + ".dat"
	if VanmPath is None:
		return 0
	if not os.path.exists(VanmDir):
		os.makedirs(VanmDir)
	with open(VanmPath, "wb") as vanm:
		Count = 0
		vanm.write(struct.pack("<i", 0x3D0))
		vanm.write(struct.pack("<i", 1))
		vanm.write(struct.pack("<i", 7))
		vanm.write(struct.pack("<i", 0x130))
		vanm.write(struct.pack("<i", 0xA))
		vanm.write(struct.pack("<i", 0x150))
		vanm.write(struct.pack("<i", 0))
		vanm.write(struct.pack("<i", 0x3D0))
		for i in range(0, 0x44):
			vanm.write(struct.pack("<i", 0))
		vanm.write(struct.pack("<B", 0))
		vanm.write(struct.pack("<B", 1))
		for i in range(0,0x13):
			vanm.write(struct.pack("<B", 0xFF))
		vanm.flush()
		padComp = Padding(VanmPath, 0x10)
		vanm.write(bytearray([0])*padComp)
		NumParts = len(ModelNames)
		part_number = -1
		#for i in range(0, NumParts):
		for i in range(NumParts-1, -1, -1):
			#print("Model name:", ModelNames[i], "i:", i)
			part_number += 1
			ModelInfo = ModelNames[i].split("_")
			if len(ModelInfo) < 2: continue
			for j in range (0, len(DummyHelperList)):
				if ModelInfo[0] == DummyHelperList[j][0] and ModelInfo[1] == DummyHelperList[j][1]:
					x = DummyHelperList[j][2]
					y = DummyHelperList[j][4]		#z = y
					z = -DummyHelperList[j][3]
					if ModelInfo[1] == "FL" or ModelInfo[1] == "FR":
						#print(ModelNames[i], "i", i)
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 1))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 1))			#Change from 0 to 1
						vanm.write(struct.pack("<f", 0))			#Change from 1 to 0 (wrong direction of movement)
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))			#Changed from x, y, z to 0
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xF1\x66\xDF\xBE\x5E\xAD\x92\x3F\xF1\x66\xDF\xBE\xF1\x66\xDF\x3E')
					vanm.write(struct.pack("<B", part_number))
					vanm.write(struct.pack("<B", 2))
					if ModelInfo[1] == "FL":
						Count += 1
						vanm.write(struct.pack("<B", 4))
					elif ModelInfo[1] == "FR":
						Count += 1
						vanm.write(struct.pack("<B", 2))
					elif ModelInfo[1] == "RL":
						Count += 1
						vanm.write(struct.pack("<B", 5))
					elif ModelInfo[1] == "RR":
						Count += 1
						vanm.write(struct.pack("<B", 3))
					else:
						Count += 1
						vanm.write(struct.pack("<B", 4))
					vanm.flush()
					padComp = Padding(VanmPath, 0x10)
					vanm.write(bytearray([0])*padComp)
					vanm.write(struct.pack("<f", 0))
					vanm.write(struct.pack("<f", 1))
					vanm.write(struct.pack("<f", 0))
					vanm.write(struct.pack("<f", 0))
					vanm.write(struct.pack("<ffff", 0,0,0,0))
					vanm.write(struct.pack("<f", -1))
					vanm.write(struct.pack("<f", 0.5))
					vanm.write(struct.pack("<f", -1))
					vanm.write(struct.pack("<f", 1))
					if ModelInfo[1] == "FL":
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 7))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", 1*abs(Transform[0][0])))		#Changed from 0 to 1
						vanm.write(struct.pack("<f", 0))		#Changed from 1 to 0
						vanm.write(struct.pack("<f", 0))		#(b'\x00\x00\x80\x25')
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xCF\x53\xFB\xC2\x37\x61\x82\x3B\xCF\x53\xFB\xC2\xCF\x53\xFB\x42')
					elif ModelInfo[1] == "FR":
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 6))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", -1*abs(Transform[0][0])))		#Changed from 0 to -1
						vanm.write(struct.pack("<f", 0))		#Changed from -1 to 0
						vanm.write(struct.pack("<f", 0))		#(b'\x00\x00\x80\x25')
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xCF\x53\xFB\xC2\x37\x61\x82\x3B\xCF\x53\xFB\x42\xCF\x53\xFB\xC2')
					elif ModelInfo[1] == "RL":
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 9))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", 1*abs(Transform[0][0])))		#Changed from 0 to 1
						vanm.write(struct.pack("<f", 0))		#Changed from 1 to 0
						vanm.write(struct.pack("<f", 0))		#(b'\x00\x00\x80\x25')
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xCF\x53\xFB\xC2\x37\x61\x82\x3B\xCF\x53\xFB\xC2\xCF\x53\xFB\x42')
					elif ModelInfo[1] == "RR":
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 8))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", -1*abs(Transform[0][0])))		#Changed from 0 to -1
						vanm.write(struct.pack("<f", 0))		#Changed from -1 to 0
						vanm.write(struct.pack("<f", 0))		#(b'\x00\x00\x80\x25')
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xCF\x53\xFB\xC2\x37\x61\x82\x3B\xCF\x53\xFB\x42\xCF\x53\xFB\xC2')
					else:
						Count += 1
						vanm.write(struct.pack("<B", part_number))
						vanm.write(struct.pack("<B", 1))
						vanm.write(struct.pack("<B", 7))
						vanm.flush()
						padComp = Padding(VanmPath, 0x10)
						vanm.write(bytearray([0])*padComp)
						vanm.write(struct.pack("<f", 1*abs(Transform[0][0])))		#Changed from 0 to 1
						vanm.write(struct.pack("<f", 0))		#Changed from 1 to 0
						vanm.write(struct.pack("<f", 0))		#(b'\x00\x00\x80\x25')
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(struct.pack("<f", 0))
						vanm.write(b'\xCF\x53\xFB\xC2\x37\x61\x82\x3B\xCF\x53\xFB\xC2\xCF\x53\xFB\x42')
		vanm.flush()
		FileLen = os.path.getsize(VanmPath)
		vanm.seek(0, 0)
		vanm.write(struct.pack("<i", FileLen))
		vanm.seek(0xC, 1)
		vanm.write(struct.pack("<i", Count))
		vanm.seek(0x8, 1)
		vanm.write(struct.pack("<i", FileLen))

def CreateCommsToolList(srcPath,vehicleName):
	CommsToolListID = StringToID(vehicleName)
	CommsToolListPath = srcPath + "\\" + "CommsToolList" + "\\" + CommsToolListID + ".dat"
	if CommsToolListPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "CommsToolList"):
		os.makedirs(srcPath + "\\" + "CommsToolList")
	with open(CommsToolListPath, "wb") as cd:
		cd.write(b'\x23\xAD\xF7\xB4')
		cd.write(struct.pack("<i", 0x8))
		cd.write(b'\x9E\xF2\xA6\xD7')
		cd.write(struct.pack("<i", 0x28))
		cd.write(struct.pack("<i", 0x20))
		cd.flush()
		padComp = Padding(CommsToolListPath,0x10)
		cd.write(bytearray([0])*padComp)
		cd.write(struct.pack("<f", 110))
		cd.write(struct.pack("<f", 90))
		cd.flush()
		padComp = Padding(CommsToolListPath,0x10)
		cd.write(bytearray([0])*padComp)

def CreateInstanceList(srcPath,InstanceListID,ModelNames,is_backdrop,CoordinatesList,Transform, use_Rotation, vehicleName, use_UniqueIDs):
	InstanceListPath = srcPath + "\\" + "InstanceList" + "\\" + InstanceListID + ".dat"
	if InstanceListPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "InstanceList"):
		os.makedirs(srcPath + "\\" + "InstanceList")
	NumParts = len(ModelNames)
	
	backdrops = []
	for i in range(0, NumParts):
		if is_backdrop[i] == 1 or is_backdrop[i] == True or is_backdrop[i] == "True":
			backdrops.append(i)
	NumBackdrops = len(backdrops)
	NumAlwaysLoaded = NumParts - NumBackdrops
	
	with open(InstanceListPath, "wb") as f:
		f.write(struct.pack("<i", 0x10))
		f.write(struct.pack("<i", NumParts))
		f.write(struct.pack("<i", NumAlwaysLoaded))
		f.write(struct.pack("<i", 1))
		for i in range(0, NumParts):
			if i in backdrops:
				continue
			f.write(struct.pack("<i", 0x0))
			f.write(struct.pack("<i", 0xFFFF))
			f.write(struct.pack("<i", 0x0))
			f.write(struct.pack("<i", 0x0))
			# x = CoordinatesList[ModelNames[i]][0]
			# y = CoordinatesList[ModelNames[i]][2]
			# z = -CoordinatesList[ModelNames[i]][1]
			# f.write(struct.pack("<ffff", *[1, 0, 0, 0]))
			# f.write(struct.pack("<ffff", *[0, 1, 0, 0]))
			# f.write(struct.pack("<ffff", *[0, 0, 1, 0]))
			# f.write(struct.pack("<ffff", *[x, y, z, 1]))
			
			if use_Rotation:
				matrix_world = Transform[i]
				matrix_world = Matrix(matrix_world)
				matrix_world = matrix_world.transposed()
				f.write(struct.pack("<4f", *matrix_world[0]))
				f.write(struct.pack("<4f", *matrix_world[1]))
				f.write(struct.pack("<4f", *matrix_world[2]))
				f.write(struct.pack("<4f", *matrix_world[3]))
			elif not use_Rotation:
				x = CoordinatesList[ModelNames[i]][0]
				y = CoordinatesList[ModelNames[i]][2]
				z = -CoordinatesList[ModelNames[i]][1]
				f.write(struct.pack("<ffff", *[1, 0, 0, 0]))
				f.write(struct.pack("<ffff", *[0, 1, 0, 0]))
				f.write(struct.pack("<ffff", *[0, 0, 1, 0]))
				f.write(struct.pack("<ffff", *[x, y, z, 1]))
		# Backdrops
		for i in backdrops:
			f.write(struct.pack("<i", 0x0))
			f.write(struct.pack("<i", 0xFFFF))
			f.write(struct.pack("<i", 0x0))
			f.write(struct.pack("<i", 0x0))
			
			if use_Rotation:
				matrix_world = Transform[i]
				matrix_world = Matrix(matrix_world)
				matrix_world = matrix_world.transposed()
				f.write(struct.pack("<4f", *matrix_world[0]))
				f.write(struct.pack("<4f", *matrix_world[1]))
				f.write(struct.pack("<4f", *matrix_world[2]))
				f.write(struct.pack("<4f", *matrix_world[3]))
			elif not use_Rotation:
				x = CoordinatesList[ModelNames[i]][0]
				y = CoordinatesList[ModelNames[i]][2]
				z = -CoordinatesList[ModelNames[i]][1]
				f.write(struct.pack("<ffff", *[1, 0, 0, 0]))
				f.write(struct.pack("<ffff", *[0, 1, 0, 0]))
				f.write(struct.pack("<ffff", *[0, 0, 1, 0]))
				f.write(struct.pack("<ffff", *[x, y, z, 1]))
		
		j = 0
		for i in range(0, NumParts):
			if i in backdrops:
				continue
			f.write(bytearray.fromhex(StringToID(ModelNames[i], use_UniqueIDs, vehicleName).replace('_', '')))
			f.write(struct.pack("<i", 0))
			f.write(struct.pack("<i", 0x10 + 0x50*j))
			f.write(struct.pack("<i", 0))
			j += 1
		
		# Backdrops
		j = 0
		for i in backdrops:
			f.write(bytearray.fromhex(StringToID(ModelNames[i], use_UniqueIDs, vehicleName).replace('_', '')))
			f.write(struct.pack("<i", 0))
			f.write(struct.pack("<i", 0x10 + 0x50*NumAlwaysLoaded + 0x50*j))
			f.write(struct.pack("<i", 0))
			j += 1

def CreatePropInstanceData(srcPath,PropInstanceDataID,TrkNumber):
	PropInstanceDataPath = srcPath + "\\" + "PropInstanceData" + "\\" + PropInstanceDataID + ".dat"
	if PropInstanceDataPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "PropInstanceData"):
		os.makedirs(srcPath + "\\" + "PropInstanceData")
	with open(PropInstanceDataPath, "wb") as f:
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
		#f.write(b'\xD3\x00\x00\x00')
		f.write(struct.pack("<i", int(TrkNumber)))
		f.write(b'\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreatePropGraphicsList(srcPath,PropGraphicsListID,TrkNumber):
	PropGraphicsListPath = srcPath + "\\" + "PropGraphicsList" + "\\" + PropGraphicsListID + ".dat"
	if PropGraphicsListPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "PropGraphicsList"):
		os.makedirs(srcPath + "\\" + "PropGraphicsList")
	with open(PropGraphicsListPath, "wb") as f:
		f.write(b'\x20\x00\x00\x00')
		#f.write(b'\xD3\x00\x00\x00')
		f.write(struct.pack("<i", int(TrkNumber)))
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreateStaticSoundMap(srcPath,StaticSoundMapID):
	StaticSoundMapPath = srcPath + "\\" + "StaticSoundMap" + "\\" + StaticSoundMapID + ".dat"
	if StaticSoundMapPath is None:
		return 0
	if not os.path.exists(srcPath + "\\" + "StaticSoundMap"):
		os.makedirs(srcPath + "\\" + "StaticSoundMap")
	with open(StaticSoundMapPath, "wb") as f:
		f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x48\x42\x00\x00\x48\x42\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\x00\x00\x48\x42\x40\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')
		f.write(b'\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		f.write(b'\xFF\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

def CreatePolygonSoupList(srcPath, context, TRKnumber):
	indicesList = []
	pointListTransformed = []
	BoxListMin = []
	BoxListMax = []
	propertyList = []
	propertyListCount = []
	quadCount = []
	i = 0
	elementnames = []
	collision_objects = []
	
	for element in reversed(bpy.context.scene.objects):
		if element.type != "MESH": continue
		if element.hide == True: continue
		if len(element.data.vertices) == 0: continue
		indicesList.append([0,0,0,0])
		pointListTransformed.append([0.0,0.0,0.0])
		BoxListMin.append([0.0,0.0,0.0])
		BoxListMax.append([0.0,0.0,0.0])
		propertyList.append(["material_0000_0000_FF_FF_FF_FF"])
		propertyListCount.append(0)
		quadCount.append(0)
		elementnames.append(element.name)
		collision_objects.append(element)
		
		bpy.context.scene.objects.active=element
		#bpy.ops.object.mode_set(mode='EDIT')
		#bpy.ops.mesh.select_all(action='SELECT')
		#stdout = io.StringIO()
		#with redirect_stdout(stdout):
		#	bpy.ops.mesh.remove_doubles()	# TESTAR
		#	bpy.ops.mesh.dissolve_degenerate()
		#	bpy.ops.mesh.delete_loose()
		#	bpy.ops.mesh.dissolve_degenerate()
		#	bpy.ops.mesh.delete_loose()
		#	bpy.ops.mesh.remove_doubles()	# TESTAR
		#bpy.ops.mesh.select_all(action='DESELECT')
		#bpy.ops.object.mode_set(mode='OBJECT')
		
		indicesList[i],pointListTransformed[i],BoxListMin[i],BoxListMax[i],propertyList[i],propertyListCount[i],quadCount[i] = ReadObjectCollision(element)
		i += 1
	if i == 0:	#NO MESHES
		#Writing empty collision
		CollisionName = "TRK_COL_" + TRKnumber
		CollisionID = StringToID(CollisionName)
		CollisionPath = srcPath + "\\" + "PolygonSoupList" + "\\" + CollisionID + ".dat"
		if not os.path.exists(srcPath + "\\" + "PolygonSoupList"):
			os.makedirs(srcPath + "\\" + "PolygonSoupList")
		with open(CollisionPath, "wb") as f:
			f.write(struct.pack('<iiii', 0,0,0,0))
			f.write(struct.pack('<iiii', 0,0,0,0))
			f.write(struct.pack('<iiii', 0,0,0,0x30))
		return 1
	
	lenghtLists = i
	chunkCount = lenghtLists
	MinX = min([sublist[0] for sublist in BoxListMin])
	MinY = min([sublist[1] for sublist in BoxListMin])
	MinZ = min([sublist[2] for sublist in BoxListMin])
	MaxX = max([sublist[0] for sublist in BoxListMax])
	MaxY = max([sublist[1] for sublist in BoxListMax])
	MaxZ = max([sublist[2] for sublist in BoxListMax])
	BoxMin = [MinX,MinY,MinZ]
	BoxMax = [MaxX,MaxY,MaxZ]
	
	## Verifications
	mfComprGranularity = []
	maiVertexOffsets = []
	vertices = []
	for i in range(0, chunkCount):
		k = -1
		negative_value = True
		huge_value = True
		using_maiVertexOffsets = False
		
		pointCount = len(pointListTransformed[i])
		
		scale = 0.015
		scale = 0.0005
		base = [BoxListMin[i][0]/scale,BoxListMin[i][1]/scale,BoxListMin[i][2]/scale]
		baseInt = [math.floor(BoxListMin[i][0]/scale),math.floor(BoxListMin[i][1]/scale),math.floor(BoxListMin[i][2]/scale)]
		base = baseInt[:]
		
		try:
			pass
			#scale = collision_objects[i]['mfComprGranularity']
			#base = collision_objects[i]['maiVertexOffsets']
			#base = [int(l) for l in base]
			#using_maiVertexOffsets = True
		except:
			pass
		
		while negative_value == True or huge_value == True or k >= 20:
			k += 1
			negative_value = False
			huge_value = False
			
			pointListScaled = []
			for j in range(0, pointCount):
				pointX = round((pointListTransformed[i][j][0])/scale - base[0])
				pointY = round((pointListTransformed[i][j][1])/scale - base[1])
				pointZ = round((pointListTransformed[i][j][2])/scale - base[2])
				pointListScaled.append([pointX, pointY, pointZ])
			
			minPointX = min([sublist[0] for sublist in pointListScaled])
			minPointY = min([sublist[1] for sublist in pointListScaled])
			minPointZ = min([sublist[2] for sublist in pointListScaled])
			maxPointX = max([sublist[0] for sublist in pointListScaled])
			maxPointY = max([sublist[1] for sublist in pointListScaled])
			maxPointZ = max([sublist[2] for sublist in pointListScaled])
			minPoint = min(minPointX, minPointY, minPointZ)
			maxPoint = max(maxPointX, maxPointY, maxPointZ)
			
			if minPointX < 0.0 or minPointY < 0.0 or minPointZ < 0.0:
				negative_value = True
				print("Negative value")
			if maxPointX > 65535.0 or maxPointY > 65535.0 or maxPointZ > 65535.0:
				huge_value = True
				print("Huge value")
			
			if (negative_value == True or huge_value == True) and using_maiVertexOffsets == True:
				base = [BoxListMin[i][0]/scale,BoxListMin[i][1]/scale,BoxListMin[i][2]/scale]
				baseInt = [math.floor(BoxListMin[i][0]/scale),math.floor(BoxListMin[i][1]/scale),math.floor(BoxListMin[i][2]/scale)]
				base = baseInt[:]
				using_maiVertexOffsets = False
				print("First fix")
			elif negative_value == True or huge_value == True:
				newScale = 65535.0/((maxPoint-minPoint)*1.1)						# 1.1 for security
				scale = (math.ceil(scale/newScale * 10.0**4.0)/(10.0**4.0))			# More fitness scale, just use four digits
				base = [BoxListMin[i][0]/scale, BoxListMin[i][1]/scale, BoxListMin[i][2]/scale]
				baseInt = [math.floor(BoxListMin[i][0]/scale), math.floor(BoxListMin[i][1]/scale), math.floor(BoxListMin[i][2]/scale)]
				base = baseInt[:]
				print("Second fix")
			
		if negative_value == True or k >= 20:
			print("Error: not able to found adequate maiVertexOffsets and mfComprGranularity values.")
		
		mfComprGranularity.append(scale)
		maiVertexOffsets.append(base)
		vertices.append(pointListScaled)
	## End of verifications
	
	#Write
	CollisionName = "TRK_COL_" + TRKnumber
	CollisionID = StringToID(CollisionName)
	CollisionPath = srcPath + "\\" + "PolygonSoupList" + "\\" + CollisionID + ".dat"
	if not os.path.exists(srcPath + "\\" + "PolygonSoupList"):
		os.makedirs(srcPath + "\\" + "PolygonSoupList")
	with open(CollisionPath, "wb") as f:
		f.write(struct.pack('<fff', *BoxMin))
		f.write(struct.pack('<i', 0))
		f.write(struct.pack('<fff', *BoxMax))
		f.write(struct.pack('<i', 0))
		chunkPointerStart = 0x30
		boxListStart = chunkPointerStart + 0x4*lenghtLists
		boxListStart = boxListStart + PaddingLenght(boxListStart, 0x10)
		chunkCount = lenghtLists
		FileLen = 0			#Fixing later
		f.write(struct.pack('<iiii', *[chunkPointerStart,boxListStart,chunkCount,FileLen]))
		boxListEnd = math.ceil(chunkCount/4.0)*0x70 + boxListStart
		chunkStart = CalcChunkStart(chunkCount, boxListEnd)
		chunkPointers = [chunkStart]*chunkCount
		for i in range(0,chunkCount):
			f.write(struct.pack('<i', chunkPointers[i]))		#Fixing later
		f.flush()
		padComp = Padding(CollisionPath,0x10)
		f.write(bytearray([0])*padComp)
		for i in range(0,chunkCount):
			f.seek(int(boxListStart + 0x70*(i//4) + 0x4*(i%4)), 0)
			f.write(struct.pack('<f', BoxListMin[i][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', BoxListMin[i][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', BoxListMin[i][2]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', BoxListMax[i][0]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', BoxListMax[i][1]))
			f.seek(0xC, 1)
			f.write(struct.pack('<f', BoxListMax[i][2]))
			f.seek(0xC, 1)
			f.write(b'\xFF\xFF\xFF\xFF')
		f.flush()
		padComp = Padding(CollisionPath,0x10)
		f.write(bytearray([0])*padComp)
		padComp = chunkStart - boxListEnd
		f.write(bytearray([0])*padComp)
		f.flush()
		for i in range(0, chunkCount):
			chunkPointers[i] = f.tell()
			#scale = 0.015
			#base = [BoxListMin[i][0]/scale,BoxListMin[i][1]/scale,BoxListMin[i][2]/scale]
			#baseInt = [math.floor(BoxListMin[i][0]/scale),math.floor(BoxListMin[i][1]/scale),math.floor(BoxListMin[i][2]/scale)]
			
			scale = mfComprGranularity[i]
			baseInt = maiVertexOffsets[i]
			pointListScaled = vertices[i]
			
			pointCount = len(pointListTransformed[i])
			pointListStart = chunkPointers[i] + 0x20
			propertyListStart = pointListStart + pointCount*0x6
			padCompPointList = PaddingLenght(propertyListStart, 0x10)
			propertyListStart = propertyListStart + padCompPointList
			chunkLenght = propertyListStart + propertyListCount[i]*0xC - chunkPointers[i]
			unknown10 = 0
			unknown11 = 0
			f.write(struct.pack('<iii', *baseInt))
			f.write(struct.pack('<f', scale))
			f.write(struct.pack('<ii', *[propertyListStart,pointListStart]))
			f.write(struct.pack('<H', chunkLenght))
			f.write(struct.pack('<BBBB', *[propertyListCount[i],quadCount[i],pointCount,unknown10]))
			f.write(struct.pack('<H', unknown11))
			#print(elementnames[i])
			#print([propertyListCount[i],quadCount[i],pointCount,unknown10])
			
			for j in range(0, pointCount):
				f.write(struct.pack('<HHH', *vertices[i][j]))
			f.write(bytearray([0])*padCompPointList)
			
			for j in range(0, propertyListCount[i]):
				#"material_FFFF_A410_A0_28_A0_26"
				properties = propertyList[i][j].split("_")
				gameCode = properties[0]
				if "BPR" in gameCode.upper():
					property1, property2 = [int(properties[1], 16), int(properties[2], 16)]
					unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d = [int(properties[3], 16), int(properties[4], 16),int(properties[5], 16), int(properties[6], 16)]
				elif "BP" in gameCode.upper():
					property1, property2 = [int(properties[1], 16), int(properties[2], 16)]
					unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d = [int(properties[3], 16), int(properties[4], 16),int(properties[5], 16), int(properties[6], 16)]
				elif "NFSMW" in gameCode.upper():
					property1, property2 = [0,0]
					unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d = [0xFF,0xFF,0xFF,0xFF]
				elif "NFSHP" in gameCode.upper():
					property1, property2 = [0,0]
					unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d = [0xFF,0xFF,0xFF,0xFF]
				else:
					property1, property2 = [0,0]
					unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d = [0xFF,0xFF,0xFF,0xFF]
				f.write(struct.pack('<HH', *[property1,property2]))
				f.write(struct.pack('<BBBB', *indicesList[i][j]))
				f.write(struct.pack('<BBBB', *[unkProperty3a, unkProperty3b, unkProperty3c, unkProperty3d]))
			f.flush()
			padComp = Padding(CollisionPath,0x80)
			f.write(bytearray([0])*padComp)
			f.flush()
		FileLen = os.path.getsize(CollisionPath)
		f.seek(0x2C, 0)
		f.write(struct.pack('<i', FileLen))
		for i in range(0,chunkCount):
			f.write(struct.pack('<i', chunkPointers[i]))

def CalcChunkStart(chunkCount,boxListEnd):
	chunkStart = boxListEnd + PaddingLenght(boxListEnd, 0x80)
	for i in range(0,math.ceil(chunkCount/4)):
		if ((i % 8) % 3 == 0):
			chunkStart += 256
		else:
			chunkStart += 384
	return int(chunkStart)

def MergeRenderables(srcPath, step, ModelNames, RenderableNames, is_backdrop, CoordinatesList, DummyHelperList, Transform, IDsList, world, vehicleName, use_UniqueIDs):
	#step = int(math.ceil(len(RenderableNames)/100)) #The max seems to be 96 (0x60), maybe 97
	#step = int(math.ceil(len(RenderableNames)/70))
	#NewModelNames = []
	#NewTransform = []
	MergedModelNames = []
	NewModelNames = ModelNames[:]
	NewTransform = Transform[:]
	NewRenderableNames = RenderableNames[:]
	NewIs_backdrop = is_backdrop[:]
	if world.name.lower() == "trk" or world.name.lower() == "track":
		#VertexSize = 0x34
		VertexSize = 0x28
	else:
		VertexSize = 0x3C
	for i in range(0, len(ModelNames)):
		list = []
		if ModelNames[i] in MergedModelNames: continue
		#for j in range (0, len(ModelNames)):					#could be just step
		for j in range (0, len(ModelNames)-i):
			#print("step:", step)
			#print("Number of models", len(ModelNames))
			#print(ModelNames[i+j], "i:", i, "j:", j)
			if (i+j) == len(ModelNames)-1:
				#print("Here0")
				step = len(list)+1
			if len(DummyHelperList) == 0:
				list.append(ModelNames[i+j])
				MergedModelNames.append(ModelNames[i+j])
			elif len(ModelNames[i+j].split("_")) < 2:
				#print("Here1")
				list.append(ModelNames[i+j])
				MergedModelNames.append(ModelNames[i+j])
			else:
				if ModelNames[i+j].split("_")[0] not in [row[0] for row in DummyHelperList] and ModelNames[i+j].split("_")[1] not in [row[1] for row in DummyHelperList]:
					#print("Here2")
					list.append(ModelNames[i+j])
					MergedModelNames.append(ModelNames[i+j])
				else:
					#print("Here3")
					#NewModelNames.append(ModelNames[i+j])
					#NewTransform.append(Transform[i+j])
					MergedModelNames.append(ModelNames[i+j])
					if (i+j) == len(ModelNames)-1:
						#print("Here4")
						step = len(list)
				#for k in range (0, len(DummyHelperList)):
					#while len(list) < step: pass
					#if len(ModelNames[i+j].split("_")) < 2:
					#	print("Here1")
					#	list.append(ModelNames[i+j])
					#	MergedModelNames.append(ModelNames[i+j])
					#	break
					#elif ModelNames[i+j].split("_")[0] != DummyHelperList[k][0] and ModelNames[i+j].split("_")[1] != DummyHelperList[k][1]:
					#	print("Here2")
					#	list.append(ModelNames[i+j])
					#	MergedModelNames.append(ModelNames[i+j])
					#	break
					#else:
					#	print("Here3")
					#	NewModelNames.append(ModelNames[i+j])
			#ta adicionando varios item na list, e len(list) >= step
			#if len(list) >= step:
			if len(list) == step:
				#print("Here5")
				break
		if step == 0: continue
		#print("Here6")
		#NewModelNames.append(list[0])
		#NewTransform.append(Transform[i])
		RenderablePaths = []
		BodyPaths = []
		centerXList = [None]*step
		centerYList = [None]*step
		centerZList = [None]*step
		viewableDiameterList = [None]*step
		NumMeshes = []
		VertexBlockSize = []
		VBuf = []
		IndexList = [[] for _ in range(step)]
		IndexListOriginal = [[] for _ in range(step)]
		IStart = []
		PolyCount = []
		ICount = [[] for _ in range(step)]
		MaterialIDs = []
		Constants = ["BPR","PC",0x12,0x0,0xC,0xC,0x4,0x80,0x10,0x4,0x48,0x4,0x50,0x60,0x80,0x4,0x4,0x4,0x4,0x8]
		for j in range(0, step):
			#RenderablePaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i+j], use_UniqueIDs, vehicleName) + ".dat")
			#BodyPaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i+j], use_UniqueIDs, vehicleName) + "_model.dat")
			RenderablePaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(list[j][:-6], use_UniqueIDs, vehicleName) + ".dat")
			BodyPaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(list[j][:-6], use_UniqueIDs, vehicleName) + "_model.dat")
		OutRenderablePath = RenderablePaths[0]
		for j in range(0, step):
			with open(RenderablePaths[j], "rb") as f:
				datasize = os.path.getsize(RenderablePaths[j])
				centerXList[j], centerYList[j], centerZList[j], viewableDiameterList[j] = struct.unpack("<ffff", f.read(16))
				f.seek(Constants[2], 0)
				NumMeshes.append(struct.unpack("<H", f.read(2))[0])
				f.seek(Constants[3], 1)
				Position0 = struct.unpack("<i", f.read(4))[0]
				f.seek(Constants[4], 1)
				RP = struct.unpack("<i", f.read(4))[0]
				f.seek(RP+Constants[5], 0)
				VertexBlock = struct.unpack("<i", f.read(4))[0]
				nothing = struct.unpack("<i", f.read(4))[0]
				if Constants[0] == "BPR" and Constants[1] == "PC":
					f.seek(-0x4, 1)
				VertexBlockSize.append(struct.unpack("<i", f.read(4))[0])
				f.seek(Position0, 0)
				Position_1 = struct.unpack("<i", f.read(4))[0]
				f.seek(Position0 + (NumMeshes[j]-1)*Constants[6], 0)
				PositionLast = struct.unpack("<i", f.read(4))[0]
				NumIds1 = int((datasize-(PositionLast+Constants[7]))/Constants[8])
				for k in range (0, NumMeshes[j]):
					f.seek(Position0 + (k)*Constants[9], 0)
					Position1 = struct.unpack("<i", f.read(4))[0]
					f.seek(Position1, 0)
					f.seek(Constants[10], 1)
					IndexStart =  struct.unpack("<i", f.read(4))[0]
					#IStart[j].append(IndexStart)
					if Constants[0] == "BPR":
						IndexCount = struct.unpack("<i", f.read(4))[0]
						ICount[j].append(IndexCount)
					MaterialPointer = Position1 + Constants[12]
					f.seek(PositionLast+Constants[14], 0)
					for l in range(0, NumIds1):
						ID = f.read(4)
						f.seek(Constants[15], 1)
						IDPointer = struct.unpack("<i", f.read(4))[0]
						if IDPointer == MaterialPointer:
							MatBytes = ID
							MaterialID = binascii.hexlify(ID)
							MaterialID = str(MaterialID,'ascii')
							MaterialID = MaterialID.upper()
							MaterialID = '_'.join([ MaterialID[x:x+2] for x in range(0, len(MaterialID), 2) ])
							MaterialIDs.append(MaterialID)
						else:
							f.seek(Constants[18], 1)
			with open(BodyPaths[j], "rb") as body:
				FileLen1 = os.path.getsize(BodyPaths[j])
				for k in range (0, NumMeshes[j]):
					for l in range(0, int(ICount[j][k])):
						a = struct.unpack("<H", body.read(2))[0]
						IndexListOriginal[j].append(a)
						if j != 0:
							#IndexList[j].append(struct.unpack("<H", body.read(2))[0]+max(IndexList[j-1])+1)
							IndexList[j].append(a+max(IndexList[j-1])+1)
						elif j == 0:
							#IndexList[j].append(struct.unpack("<H", body.read(2))[0])
							IndexList[j].append(a)
				body.seek(VertexBlock, 0)
				#VBuf.append(body.read(VertexBlockSize[j]))
				#VBuf.append(body.read(VertexBlockSize[j]-0x3C))
				VBuf.append(body.read((max(IndexListOriginal[j])+1)*VertexSize))
		maxIndex = max([sublist[-1] for sublist in IndexList])
		if maxIndex > 0xFFFF:
			print("Too many vertices (", maxIndex,") for an unique renderable! Fixed and continuing...")
			continue
		else:
			for j in range (1, step):
				index = NewModelNames.index(list[j])
				del NewModelNames[index]
				del NewTransform[index]
		with open(BodyPaths[0], "wb") as body:
			#body.write(IBuf1)
			for j in range (0, step):
				for k in range (0, NumMeshes[j]):
					IStart.append(int(body.tell()/2))
					PolyCount.append(int(ICount[j][k]/3))
					if k == 0:
						for l in range(0, int(ICount[j][k])):
							body.write(struct.pack('<H', IndexList[j][l]))
					else:
						#for l in range(int(ICount[j][k-1]), int(ICount[j][k])):
						#	body.write(struct.pack('<H', IndexList[j][k]))
						for l in range(0, int(ICount[j][k])):
							body.write(struct.pack('<H', IndexList[j][l]))
					body.flush()
			body.flush()
			padComp1 = Padding(BodyPaths[0],0x10)
			body.write(bytearray([0])*padComp1)
			VertexBlock = body.tell()
			for j in range (0, step):
				body.write(VBuf[j])
			body.flush()
			padComp2 = Padding(BodyPaths[0],0x80)
			body.write(bytearray([0])*padComp2)
		OutNumMeshes = sum(NumMeshes)
		VertexBlockLen = sum(VertexBlockSize)
		if world.name.lower() == "trk" or world.name.lower() == "track":
			NumVertexDesc = [2]*OutNumMeshes
			#VertexDesc1IDs = ["4C_66_C2_A5"]*OutNumMeshes		#0x3C
			#VertexDesc2IDs = ["E1_74_B4_4A"]*OutNumMeshes
			VertexDesc1IDs = ["5B_96_3F_E2"]*OutNumMeshes		#0x28
			VertexDesc2IDs = ["8C_24_A1_BD"]*OutNumMeshes
			VertexDesc3IDs = ["0E_46_97_8F"]*OutNumMeshes
			VertexDesc4IDs = ["9F_F0_42_9F"]*OutNumMeshes
		else:
			NumVertexDesc = [4]*OutNumMeshes
			VertexDesc1IDs = ["B8_23_13_0F"]*OutNumMeshes
			VertexDesc2IDs = ["7F_44_88_2B"]*OutNumMeshes
			VertexDesc3IDs = ["0E_46_97_8F"]*OutNumMeshes
			VertexDesc4IDs = ["9F_F0_42_9F"]*OutNumMeshes
		viewableDiameter = viewableDiameterList[0]
		centerX, centerY, centerZ = (0,0,0)
		newLocationX, newLocationY, newLocationZ = (0,0,0)
		for j in range(0,step):
			if j > 0:
				viewableDiameter = ((centerYList[j]-centerY/j)**2+(centerZList[j]-centerZ/j)**2+(centerXList[j]-centerX/j)**2)**0.5+max([viewableDiameterList[j],viewableDiameter])
			centerX += centerXList[j]
			centerY += centerYList[j]
			centerZ += centerZList[j]
			index = ModelNames.index(list[j])
			locationX, locationY, locationZ = CoordinatesList[ModelNames[index]]
			newLocationX += locationX
			newLocationY += locationY
			newLocationZ += locationZ
		centerX = centerX/step
		centerY = centerY/step
		centerZ = centerZ/step
		newLocationX = newLocationX/step
		newLocationY = newLocationY/step
		newLocationZ = newLocationZ/step
		index = ModelNames.index(list[0])
		CoordinatesList[ModelNames[index]] = (newLocationX, newLocationY, newLocationZ)
		#centerX, centerY, centerZ = [0,0,0]
		SubPartCode = []
		CreateRenderableHeader(OutRenderablePath[:-4], centerX, centerY, centerZ, viewableDiameter, OutNumMeshes, VertexBlock, VertexBlockLen, IStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world)
	for i in range(0, len(ModelNames)):
		if ModelNames[i] not in NewModelNames:
			try:
				del IDsList[StringToID(ModelNames[i], use_UniqueIDs, vehicleName)]
			except: pass
			try:
				del IDsList[StringToID(RenderableNames[i], use_UniqueIDs, vehicleName)]
			except: pass
			#print(ModelNames[i], RenderableNames[i])
			os.remove(srcPath + "\\" + "Model" + "\\" + StringToID(ModelNames[i], use_UniqueIDs, vehicleName) + ".dat")
			os.remove(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i], use_UniqueIDs, vehicleName) + ".dat")
			os.remove(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i], use_UniqueIDs, vehicleName) + "_model.dat")
			try:
				index = NewRenderableNames.index(RenderableNames[i])
				del NewRenderableNames[index]
			except: pass
			try:
				index = NewIs_backdrop.index(is_backdrop[i])
				del NewIs_backdrop[index]
			except: pass
	return (NewModelNames, NewRenderableNames, NewIs_backdrop, CoordinatesList, NewTransform)

def MergeWheelsRenderables(srcPath, ModelNames, RenderableNames, CoordinatesList, DummyHelperList, Transform, IDsList, world, vehicleName, use_UniqueIDs):
	#NewModelNames = []
	#NewTransform = []
	NewModelNames = ModelNames[:]
	NewTransform = Transform[:]
	NewRenderableNames = RenderableNames[:]
	VertexSize = 0x3C
	for i in range(0, len(DummyHelperList)):
		list = []
		for j in range (0, len(ModelNames)):
			ModelInfo = ModelNames[j].split("_")
			if len(ModelInfo) < 2: continue
			if ModelInfo[0] == DummyHelperList[i][0] and ModelInfo[1] == DummyHelperList[i][1]:
				list.append(ModelNames[j])
		step = len(list)
		if step == 0:
			break
		RenderablePaths = []
		BodyPaths = []
		centerXList = [None]*step
		centerYList = [None]*step
		centerZList = [None]*step
		viewableDiameterList = [None]*step
		NumMeshes = []
		VertexBlockSize = []
		VBuf = []
		IndexList = [[] for _ in range(step)]
		IndexListOriginal = [[] for _ in range(step)]
		IStart = []
		PolyCount = []
		ICount = [[] for _ in range(step)]
		MaterialIDs = []
		Constants = ["BPR","PC",0x12,0x0,0xC,0xC,0x4,0x80,0x10,0x4,0x48,0x4,0x50,0x60,0x80,0x4,0x4,0x4,0x4,0x8]
		for j in range(0, step):
			RenderablePaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(list[j][:-6], use_UniqueIDs, vehicleName) + ".dat")
			BodyPaths.append(srcPath + "\\" + "Renderable" + "\\" + StringToID(list[j][:-6], use_UniqueIDs, vehicleName) + "_model.dat")
		OutRenderablePath = RenderablePaths[0]
		for j in range(0, step):
			with open(RenderablePaths[j], "rb") as f:
				datasize = os.path.getsize(RenderablePaths[j])
				centerXList[j], centerYList[j], centerZList[j], viewableDiameterList[j] = struct.unpack("<ffff", f.read(16))
				f.seek(Constants[2], 0)
				NumMeshes.append(struct.unpack("<H", f.read(2))[0])
				f.seek(Constants[3], 1)
				Position0 = struct.unpack("<i", f.read(4))[0]
				f.seek(Constants[4], 1)
				RP = struct.unpack("<i", f.read(4))[0]
				f.seek(RP+Constants[5], 0)
				VertexBlock = struct.unpack("<i", f.read(4))[0]
				nothing = struct.unpack("<i", f.read(4))[0]
				if Constants[0] == "BPR" and Constants[1] == "PC":
					f.seek(-0x4, 1)
				VertexBlockSize.append(struct.unpack("<i", f.read(4))[0])
				f.seek(Position0, 0)
				Position_1 = struct.unpack("<i", f.read(4))[0]
				f.seek(Position0 + (NumMeshes[j]-1)*Constants[6], 0)
				PositionLast = struct.unpack("<i", f.read(4))[0]
				NumIds1 = int((datasize-(PositionLast+Constants[7]))/Constants[8])
				for k in range (0, NumMeshes[j]):
					f.seek(Position0 + (k)*Constants[9], 0)
					Position1 = struct.unpack("<i", f.read(4))[0]
					f.seek(Position1, 0)
					f.seek(Constants[10], 1)
					IndexStart =  struct.unpack("<i", f.read(4))[0]
					if Constants[0] == "BPR":
						IndexCount = struct.unpack("<i", f.read(4))[0]
						ICount[j].append(IndexCount)
					MaterialPointer = Position1 + Constants[12]
					f.seek(PositionLast+Constants[14], 0)
					for l in range(0, NumIds1):
						ID = f.read(4)
						f.seek(Constants[15], 1)
						IDPointer = struct.unpack("<i", f.read(4))[0]
						if IDPointer == MaterialPointer:
							MatBytes = ID
							MaterialID = binascii.hexlify(ID)
							MaterialID = str(MaterialID,'ascii')
							MaterialID = MaterialID.upper()
							MaterialID = '_'.join([ MaterialID[x:x+2] for x in range(0, len(MaterialID), 2) ])
							MaterialIDs.append(MaterialID)
						else:
							f.seek(Constants[18], 1)
			with open(BodyPaths[j], "rb") as body:
				FileLen1 = os.path.getsize(BodyPaths[j])
				for k in range (0, NumMeshes[j]):
					for l in range(0, int(ICount[j][k])):
						a = struct.unpack("<H", body.read(2))[0]
						IndexListOriginal[j].append(a)
						if j != 0:
							IndexList[j].append(a+max(IndexList[j-1])+1)
						elif j == 0:
							IndexList[j].append(a)
				body.seek(VertexBlock, 0)
				VBuf.append(body.read((max(IndexListOriginal[j])+1)*VertexSize))
		maxIndex = max([sublist[-1] for sublist in IndexList])
		if maxIndex > 0xFFFF:
			print("Too many vertices (", maxIndex,") for an unique renderable! Fixed and continuing...")
			continue
		else:
			for j in range (1, step):
				index = NewModelNames.index(list[j])
				del NewModelNames[index]
				del NewTransform[index]
				#NewModelNames.pop(index)
				#NewTransform.pop(index)
		with open(BodyPaths[0], "wb") as body:
			for j in range (0, step):
				for k in range (0, NumMeshes[j]):
					IStart.append(int(body.tell()/2))
					PolyCount.append(int(ICount[j][k]/3))
					if k == 0:
						for l in range(0, int(ICount[j][k])):
							body.write(struct.pack('<H', IndexList[j][l]))
					else:
						for l in range(0, int(ICount[j][k])):
							body.write(struct.pack('<H', IndexList[j][l]))
					body.flush()
			body.flush()
			padComp1 = Padding(BodyPaths[0],0x10)
			body.write(bytearray([0])*padComp1)
			VertexBlock = body.tell()
			for j in range (0, step):
				body.write(VBuf[j])
			body.flush()
			padComp2 = Padding(BodyPaths[0],0x80)
			body.write(bytearray([0])*padComp2)
		OutNumMeshes = sum(NumMeshes)
		VertexBlockLen = sum(VertexBlockSize)
		NumVertexDesc = [4]*OutNumMeshes
		VertexDesc1IDs = ["B8_23_13_0F"]*OutNumMeshes
		VertexDesc2IDs = ["7F_44_88_2B"]*OutNumMeshes
		VertexDesc3IDs = ["0E_46_97_8F"]*OutNumMeshes
		VertexDesc4IDs = ["9F_F0_42_9F"]*OutNumMeshes
		viewableDiameter = viewableDiameterList[0]
		centerX, centerY, centerZ = (0,0,0)
		newLocationX, newLocationY, newLocationZ = (0,0,0)
		for j in range(0,step):
			if j > 0:
				viewableDiameter = ((centerYList[j]-centerY/j)**2+(centerZList[j]-centerZ/j)**2+(centerXList[j]-centerX/j)**2)**0.5+max([viewableDiameterList[j],viewableDiameter])
			centerX += centerXList[j]
			centerY += centerYList[j]
			centerZ += centerZList[j]
			index = ModelNames.index(list[j])
			locationX, locationY, locationZ = CoordinatesList[ModelNames[index]]
			newLocationX += locationX
			newLocationY += locationY
			newLocationZ += locationZ
		centerX = centerX/step
		centerY = centerY/step
		centerZ = centerZ/step
		newLocationX = newLocationX/step
		newLocationY = newLocationY/step
		newLocationZ = newLocationZ/step
		index = ModelNames.index(list[0])
		CoordinatesList[ModelNames[index]] = (newLocationX, newLocationY, newLocationZ)
		#centerX, centerY, centerZ = [0,0,0]
		SubPartCode = []
		CreateRenderableHeader(OutRenderablePath[:-4], centerX, centerY, centerZ, viewableDiameter, OutNumMeshes, VertexBlock, VertexBlockLen, IStart, PolyCount, NumVertexDesc, MaterialIDs, VertexDesc1IDs, VertexDesc2IDs, VertexDesc3IDs, VertexDesc4IDs, SubPartCode, world)
	for i in range(0, len(ModelNames)):
		if ModelNames[i] not in NewModelNames:
			try:
				del IDsList[StringToID(ModelNames[i], use_UniqueIDs, vehicleName)]
			except: pass
			try:
				del IDsList[StringToID(RenderableNames[i], use_UniqueIDs, vehicleName)]
			except: pass
			#print(ModelNames[i], RenderableNames[i])
			os.remove(srcPath + "\\" + "Model" + "\\" + StringToID(ModelNames[i], use_UniqueIDs, vehicleName) + ".dat")
			os.remove(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i], use_UniqueIDs, vehicleName) + ".dat")
			os.remove(srcPath + "\\" + "Renderable" + "\\" + StringToID(RenderableNames[i], use_UniqueIDs, vehicleName) + "_model.dat")
			try:
				index = NewRenderableNames.index(RenderableNames[i])
				del NewRenderableNames[index]
			except: pass
	return (NewModelNames, NewRenderableNames, CoordinatesList, NewTransform)

def ReadObject(obj, use_Rotation, use_Accurate_split, recalculate_bones):
	mesh = obj.data
	mesh_vertices = len(mesh.vertices)
	face_index_pairs = [(face, index) for index, face in enumerate(mesh.polygons)]
	faceuv = len(mesh.uv_textures) > 0
	
	# Verifications
	if not (len(face_index_pairs) + mesh_vertices):  # Make sure there is something to write
		# clean up
		bpy.data.meshes.remove(mesh)
		emptyList = []
		return (emptyList,emptyList,emptyList,emptyList,emptyList,emptyList) # dont bother with this mesh.
	
	if len(obj.material_slots) == 0:
		mat = bpy.data.materials.new("Mat_%s" % obj.name)
		mesh.materials.append(mat)
	
	# Inits
	mesh.calc_normals_split()
	loops = mesh.loops
	bm = bmesh.new()
	bm.from_mesh(mesh)
	if faceuv:
		uv_layer = mesh.uv_layers.active.data[:]
	uv_layers = bm.loops.layers.uv
	
	# Definitions
	len_uv_layers = len(uv_layers)
	IndexList = [None] * len(face_index_pairs)
	TriangleList = []
	VerticesList = [None] * mesh_vertices
	NormalList = [None] * mesh_vertices
	TangentList = [None] * mesh_vertices
	UV1List = [None] * mesh_vertices
	UV2List = [None] * mesh_vertices
	BoneIndicesList = [None] * mesh_vertices
	BoneWeightsList = [None] * mesh_vertices
	#UV1sList = [[] for _ in range(mesh_vertices)]
	#UV2sList = [[] for _ in range(mesh_vertices)]
	#UVLayersList = [ [[] for _ in range(mesh_vertices)] for __ in range(0, len_uv_layers)]
	#UVallList = [None] * mesh_vertices
	
	# Check if boneIndices and boneWeights exist
	has_bones = False
	try:
		boneIndex1 = bm.verts.layers.int.get("boneIndex1")
		boneIndex2 = bm.verts.layers.int.get("boneIndex2")
		boneIndex3 = bm.verts.layers.int.get("boneIndex3")
		boneIndex4 = bm.verts.layers.int.get("boneIndex4")
		boneWeight1 = bm.verts.layers.int.get("boneWeight1")
		boneWeight2 = bm.verts.layers.int.get("boneWeight2")
		boneWeight3 = bm.verts.layers.int.get("boneWeight3")
		boneWeight4 = bm.verts.layers.int.get("boneWeight4")
		if None in [boneIndex1, boneIndex2, boneIndex3, boneIndex4, boneWeight1, boneWeight2, boneWeight3, boneWeight4]:
			has_bones = False
		else:
			has_bones = True
	except:
		has_bones = False
		BoneIndicesList = []
		BoneWeightsList = []
	
	# Triangles
	FaceIndex_Material = {}
	cte_index = 0
	for index, slot in enumerate(obj.material_slots):
		Triangles = []
		#select the verts from faces with material index
		if not slot.material:
			# empty slot
			#FIX
			cte_index -= 1
			continue
		mat = slot.material
		position = 0
		for face in mesh.polygons:
			if face.hide == False and face.material_index == index:
				Triangles.append([face.vertices[0],face.vertices[1],face.vertices[2]])
				FaceIndex_Material[face.index] = [index + cte_index, position]
				position += 1
		if Triangles != []:
			TriangleList.append(Triangles)
		else:
			cte_index -= 1
	
	# Coordinates and normals
	vertex_map = defaultdict(list)
	for face in mesh.polygons:
		for v_ix, l_ix in zip(face.vertices, face.loop_indices):
			vertex_map[v_ix].append(l_ix)
	for face in mesh.polygons:
		# gather the face vertices
		v_idxs = []
		for v in face.vertices:
			vert = mesh.vertices[v]
			if use_Rotation:
				VerticesList[vert.index] = [vert.co.x, vert.co.y, vert.co.z]
			else:
				VerticesList[vert.index] = [vert.co.x, vert.co.z, -vert.co.y]
			v_idxs.append(vert.index)
		
		for l_idx in face.loop_indices:
			for v_ix in v_idxs:
				for l_ix in vertex_map[v_ix]:
					if l_ix == l_idx:
						# This is where you extract the split normals from the mesh
						vert_normal = loops[l_idx].normal
						if use_Rotation:
							NormalList[v_ix] = [vert_normal.x, vert_normal.y, vert_normal.z]
						else:
							NormalList[v_ix] = [vert_normal.x, vert_normal.z, -vert_normal.y]
						break
	
	# Tangents
	#mesh.calc_tangents(mesh.uv_layers[mesh.uv_layers.active.name].name)
	#for loop in mesh.loops:
	#	TangentList[loop.vertex_index] = loop.tangent
	#mesh.free_tangents()
	
	#len_mesh_loops = len(mesh.loops)
	#t_ln = [np.zeros(len_mesh_loops * 3)]*len_uv_layers
	#for idx, uvlayer in enumerate(mesh.uv_layers):
	#	mesh.calc_tangents(uvmap=uvlayer.name)
	#	mesh.loops.foreach_get("tangent", t_ln[idx])
	#	#mesh.loops.foreach_get("bitangent", t_ln)
	#TangentList = np.reshape(t_ln[0],(len_mesh_loops,3))
	
	if len_uv_layers > 0:
		len_mesh_loops = len(mesh.loops)
		t_ln = np.zeros(len_mesh_loops * 3)
		mesh.calc_tangents(uvmap=mesh.uv_layers[0].name)
		mesh.loops.foreach_get("tangent", t_ln)
		#mesh.loops.foreach_get("bitangent", b_ln)
		TangentList = np.reshape(t_ln,(len_mesh_loops,3))
		mesh.free_tangents()
		TangentList = TangentList.tolist()
	else:
		TangentList = [[0.0,0.0,0.0]]*mesh_vertices
	
	# Bones
	if has_bones and recalculate_bones == False:
		for vert in bm.verts:
			BoneIndicesList[vert.index] = [vert[boneIndex1], vert[boneIndex2], vert[boneIndex3], vert[boneIndex4]]
			BoneWeightsList[vert.index] = [vert[boneWeight1], vert[boneWeight2], vert[boneWeight3], vert[boneWeight4]]
	else:
		BoneIndicesList = []
		BoneWeightsList = []
	
	# UV
	if faceuv:
		if use_Accurate_split == True:
			UVLayersList = [ [[] for _ in range(mesh_vertices)] for __ in range(0, len_uv_layers)]
			UVallList = [None] * mesh_vertices
			#splitted_vertices_indices = []
			#splitted_vertices = []
			splitted_vertices2 = {}
			for face in bm.faces:
				if face.hide == True: continue
				vertices_index = []
				add_new_face = False
				for loop in face.loops:
					uv = []
					for layer in range(0, len_uv_layers):
						uv_layer = bm.loops.layers.uv[layer]
						#uv.append(loop[uv_layer].uv)		# uv = [[u1,v1], [u2,v2], [u3,v3]]
						uv.append(tuple(loop[uv_layer].uv))
					uv = tuple(uv)
					if UVallList[loop.vert.index] == None:
						#print("No need to split")
						UVallList[loop.vert.index] = uv[:]	# UVallList = [uv_vert0, uv_vert1, uv_vert2, uv_vert3, ...]
						for layer in range(0, len_uv_layers):
							# UVLayersList = [[uv1_vert0, uv1_vert1, [uv[0].x,1.0-uv[0].y] , ...   ], [uv2_vert0, uv2_vert1, ...],[]]
							#UVLayersList[layer][loop.vert.index] = [uv[layer].x,1.0-uv[layer].y]
							UVLayersList[layer][loop.vert.index] = [uv[layer][0],1.0-uv[layer][1]]
						vertices_index.append(loop.vert.index)
					elif UVallList[loop.vert.index] == uv:
						vertices_index.append(loop.vert.index)
					#elif [loop.vert.index, uv] in splitted_vertices:
					#	#print("Vertex already splitted")
					#	lists = [loop.vert.index, uv]
					#	for i in range(len(splitted_vertices_indices)-1, -1, -1):
					#		if lists == splitted_vertices[i]:
					#			vertices_index.append(splitted_vertices_indices[i])
					#			break
					#	add_new_face = True
					elif (loop.vert.index, uv) in splitted_vertices2:
						#print("Vertex already splitted")
						vertice_index = splitted_vertices2[(loop.vert.index, uv)]
						vertices_index.append(vertice_index)
						add_new_face = True
					elif UVallList[loop.vert.index] != uv:
						#print("Need to split this vertex")
						VerticesList.append(VerticesList[loop.vert.index])
						NormalList.append(NormalList[loop.vert.index])
						TangentList.append(TangentList[loop.vert.index])
						if has_bones and recalculate_bones == False:
							BoneIndicesList.append(BoneIndicesList[loop.vert.index])
							BoneWeightsList.append(BoneWeightsList[loop.vert.index])
						UVallList.append(uv)
						for layer in range(0, len_uv_layers):
							#UVLayersList[layer].append([uv[layer].x,1.0-uv[layer].y])
							UVLayersList[layer].append([uv[layer][0],1.0-uv[layer][1]])
						
						len_VerticesList_1 = len(VerticesList)-1
						vertices_index.append(len_VerticesList_1)
						#splitted_vertices_indices.append(len_VerticesList_1)
						#splitted_vertices.append([loop.vert.index, uv])
						
						splitted_vertices2[(loop.vert.index, uv)] = len_VerticesList_1
						
						add_new_face = True
				if add_new_face == True:
					list_index, position = FaceIndex_Material[face.index]
					TriangleList[list_index][position] = vertices_index[:]
				
				for layer in range(0, len_uv_layers):
					for index, UVs in enumerate(UVLayersList[layer]):
						if len(UVs) == 0:
							UVLayersList[layer][index] = [0.0, 0.0]
					if layer == 0:
						UV1List = UVLayersList[layer][:]
						UV2List = UVLayersList[layer][:]
					elif layer == 1:
						UV2List = UVLayersList[layer][:]
					elif layer == 2:
						UV2List = UVLayersList[layer][:]
		elif use_Accurate_split == False:
			uv_layer = bm.loops.layers.uv.active
			uv_layer2 = bm.loops.layers.uv.active
			if len_uv_layers > 1:
				uv_layer2 = bm.loops.layers.uv[1]
				if len_uv_layers > 2:									# Need for Speed Most Wanted scratch uv layer
					uv_layer2 = bm.loops.layers.uv[2]
			splitted_vertices_indices = []
			splitted_vertices = []
			for face in bm.faces:
				if face.hide == True: continue
				vertices_index = []
				add_new_face = False
				for loop in face.loops:
					uv = loop[uv_layer].uv
					uv2 = loop[uv_layer2].uv
					if UV1List[loop.vert.index] == None:
						#print("No need to split")
						UV1List[loop.vert.index] = [uv.x,1.0-uv.y]
						UV2List[loop.vert.index] = [uv2.x,1.0-uv2.y]
						vertices_index.append(loop.vert.index)
					elif UV1List[loop.vert.index] == [uv.x,1.0-uv.y]:
						vertices_index.append(loop.vert.index)
					elif [loop.vert.index, uv.x, 1.0-uv.y] in splitted_vertices:
						#print("Vertex already splitted")
						lists = [loop.vert.index, uv.x, 1.0-uv.y]
						for i in range(len(splitted_vertices_indices)-1, -1, -1):
							if lists == splitted_vertices[i]:
								vertices_index.append(splitted_vertices_indices[i])
								break
						add_new_face = True
					elif UV1List[loop.vert.index] != [uv.x,1.0-uv.y]:
						#print("Need to split this vertex")
						VerticesList.append(VerticesList[loop.vert.index])
						NormalList.append(NormalList[loop.vert.index])
						TangentList.append(TangentList[loop.vert.index])
						if has_bones and recalculate_bones == False:
							BoneIndicesList.append(BoneIndicesList[loop.vert.index])
							BoneWeightsList.append(BoneWeightsList[loop.vert.index])
						UV1List.append([uv.x,1.0-uv.y])
						UV2List.append([uv2.x,1.0-uv2.y])
						
						len_VerticesList_1 = len(VerticesList)-1
						vertices_index.append(len_VerticesList_1)
						splitted_vertices_indices.append(len_VerticesList_1)
						splitted_vertices.append([loop.vert.index, uv.x,1.0-uv.y])
						add_new_face = True
				if add_new_face == True:
					list_index, position = FaceIndex_Material[face.index]
					TriangleList[list_index][position] = vertices_index[:]
	else:
		UV1List = [[0.0,0.0]]*mesh_vertices
		UV2List = [[0.0,0.0]]*mesh_vertices
	
	bm.clear()
	bm.free()
	
	return (TriangleList,VerticesList,NormalList,TangentList,UV1List,UV2List,BoneIndicesList,BoneWeightsList)

def ReadObjectCollision(obj):
	mesh = obj.data
	# Definitions
	face_index_pairs = [(face, index) for index, face in enumerate(mesh.polygons)]
	indicesList = [None] * len(face_index_pairs)
	pointListTransformed = [None] * len(mesh.vertices)
	propertyList = [None] * len(face_index_pairs)
	propertyList2 = []
	BoxListMin = [None]
	BoxListMax = [None]
	quadCount = 0
	triangleCount = 0
	GlobalCoordinates = (obj.location.x,obj.location.y,obj.location.z)
	#cte = [GlobalCoordinates[0],GlobalCoordinates[2],-GlobalCoordinates[1]]
	cte = [GlobalCoordinates[0],-GlobalCoordinates[1],GlobalCoordinates[2]]
	
	if not (len(face_index_pairs) + len(mesh.vertices)):  # Make sure there is something to write
		# clean up
		bpy.data.meshes.remove(mesh)
		return (indicesList,pointListTransformed,BoxListMin,BoxListMax,propertyList,propertyListCount,quadCount) # dont bother with this mesh.
	loops = mesh.loops
	
	if len(obj.material_slots) == 0:
		mat = bpy.data.materials.new("Mat_%s" % obj.name)
		mesh.materials.append(mat)
	
	# Triangles
	for index, face in enumerate(mesh.polygons):
		if len(face.vertices) == 4:
			#indicesList[index] = [face.vertices[0],face.vertices[1],face.vertices[2],face.vertices[3]]
			indicesList[index] = [face.vertices[0],face.vertices[1],face.vertices[3],face.vertices[2]]	#Maybe it is in this order
			quadCount += 1
		elif len(face.vertices) == 3:
			indicesList[index] = [face.vertices[0],face.vertices[1],face.vertices[2],0xFF]			#Add verification for triangle or quad
			triangleCount += 1
		else:
			print("Ngon", len(face.vertices))
		slot = obj.material_slots[face.material_index]
		mat = slot.material
		if mat is not None:
			propertyList[index] = mat.name
			if "." in mat.name:
				propertyList[index] = mat.name.split(".")[0]
		else:
			propertyList[index] = "material_0000_0000_FF_FF_FF_FF"
			#print("No mat in slot", face.material_index)
		
		# Verifying if the face has more materials
		try:
			if obj.name == "Mesh_128":
				print(index)
				print("\tMaterial_" + obj.name + "_index" + "_" + str(index))
				print("\t" + mat["Material_" + obj.name + "_index" + "_" + str(index)])
				print("\tMaterial_" + obj.name + "_" + str(index))
				print("\t" + mat["Material_" + obj.name + "_" + str(index)])
				print("\tMaterial_" + obj.name + "_vertices_winding" + "_" + str(index))
				print("\t" + mat["Material_" + obj.name + "_vertices_winding" + "_" + str(index)])
			propertyList2.append([mat["Material_" + obj.name + "_index" + "_" + str(index)], index, mat["Material_" + obj.name + "_" + str(index)], mat["Material_" + obj.name + "_vertices_winding" + "_" + str(index)]])
			if obj.name == "Mesh_128":
				print("after ", len(face.vertices))
		except:
			pass
	
	# Adding duplicated faces when a face has more materials
	propertyList_temp = propertyList[:]
	indicesList_temp = indicesList[:]
	for item in propertyList2:
		face_index       = item[0]
		base_face_index  = item[1]
		property         = item[2]
		vertices_winding = [int(i) for i in item[3].split(" ")]
		
		indices_base = indicesList[base_face_index][:]
		
		if len(vertices_winding) == 4:
			indices_ = [indices_base[vertices_winding[0]], indices_base[vertices_winding[1]], indices_base[vertices_winding[2]], indices_base[vertices_winding[3]]]
		else:
			print("---------------triangle----------------")
			indices_ = [indices_base[vertices_winding[0]], indices_base[vertices_winding[1]], indices_base[vertices_winding[2]], 0xFF]
		
		print(hex(indices_base[0]), hex(indices_base[1]), hex(indices_base[2]), hex(indices_base[3]))
		print(hex(indices_[0]), hex(indices_[1]), hex(indices_[2]), hex(indices_[3]))
		print(vertices_winding)
		print()
		
		indicesList_temp.insert(face_index, indices_)
		propertyList_temp.insert(face_index, property)
		
		if indicesList[base_face_index][3] != 0xFF:
			quadCount += 1
	
	#indicesList = indicesList_temp[:]
	#propertyList = propertyList_temp[:]
	
	# Sorting the indices list, because every quad must came before the triangles
	indicesList.clear()
	propertyList.clear()
	for i in range(0, len(indicesList_temp)):
		indices = indicesList_temp[i]
		if indices[3] != 0xFF:	# The face is a quad
			indicesList.append(indices)
			propertyList.append(propertyList_temp[i])
	for i in range(0, len(indicesList_temp)):
		indices = indicesList_temp[i]
		if indices[3] == 0xFF:	# The face is a triangle
			indicesList.append(indices)
			propertyList.append(propertyList_temp[i])
	
	# Vertices
	for v_index, v in enumerate(mesh.vertices[:]):
		#pointListTransformed[v_index] = [v.co.x*obj.matrix_world[0][0], v.co.y, v.co.z*(-obj.matrix_world[1][2])]		#BOM
		#pointListTransformed[v_index] = [v.co.x*obj.matrix_world[0][0] + cte[0], v.co.y + cte[1], v.co.z*(-obj.matrix_world[1][2])+cte[2]]	#BOM
		#pointListTransformed[v_index] = [v.co.x + cte[0], v.co.z + cte[2], -v.co.y + cte[1]]
		pointListTransformed[v_index] = [v.co.x, v.co.z, -v.co.y]
		#pointListTransformed[v_index] = [v.co.x, v.co.y, v.co.z]	#Certo
		#pointListTransformed[v_index] = [v.co.x, v.co.y, -v.co.z]	#Meio bom
		#pointListTransformed[v_index] = [-v.co.x, v.co.y, -v.co.z]
	minX = min([sublist[0] for sublist in pointListTransformed])
	minY = min([sublist[1] for sublist in pointListTransformed])
	minZ = min([sublist[2] for sublist in pointListTransformed])
	maxX = max([sublist[0] for sublist in pointListTransformed])
	maxY = max([sublist[1] for sublist in pointListTransformed])
	maxZ = max([sublist[2] for sublist in pointListTransformed])
	BoxListMin = [minX,minY,minZ]
	BoxListMax = [maxX,maxY,maxZ]
	propertyListCount = len(propertyList)
	
	return (indicesList,pointListTransformed,BoxListMin,BoxListMax,propertyList,propertyListCount,quadCount)

def CalculateVertexNormals(Triangles, Positions):
	NormalList = []
	Nx = 0.0
	Ny = 0.0
	Nz = 0.0
	SharedNormalsList = [[] for _ in range(len(Positions))]
	for triangle in Triangles:
		v1 = [Positions[triangle[1]][0] - Positions[triangle[0]][0], Positions[triangle[1]][1] - Positions[triangle[0]][1], Positions[triangle[1]][2] - Positions[triangle[0]][2]]
		v2 = [Positions[triangle[2]][0] - Positions[triangle[0]][0], Positions[triangle[2]][1] - Positions[triangle[0]][1], Positions[triangle[2]][2] - Positions[triangle[0]][2]]
		N = CrossProduct(v1,v2)
		for index in triangle:
			SharedNormalsList[index].append(N)
	for SharedNormals in SharedNormalsList:
		Nx = 0.0
		Ny = 0.0
		Nz = 0.0
		for Normal in SharedNormals:
			Nx += Normal[0]
			Ny += Normal[1]
			Nz += Normal[2]
		N = [Nx, Ny, Nz]
		N = Normalize(N)
		NormalList.append(N)
	return NormalList

def CalculateVertexTangents(Triangles, Positions, UV):
	TangentList = []
	BiTangentList = []
	Tx = 0.0
	Ty = 0.0
	Tz = 0.0
	BiTangentsx = 0.0
	BiTangentsy = 0.0
	BiTangentsz = 0.0
	SharedTangentsList = [[] for _ in range(len(Positions))]
	SharedBiTangentsList = [[] for _ in range(len(Positions))]
	for triangle in Triangles:
		#v1 = (x1-x0, y1-y0, z1-z0)
		#v2 = (x2-x0, y2-y0, z2-z0)
		v1 = [Positions[triangle[1]][0] - Positions[triangle[0]][0], Positions[triangle[1]][1] - Positions[triangle[0]][1], Positions[triangle[1]][2] - Positions[triangle[0]][2]]
		v2 = [Positions[triangle[2]][0] - Positions[triangle[0]][0], Positions[triangle[2]][1] - Positions[triangle[0]][1], Positions[triangle[2]][2] - Positions[triangle[0]][2]]
		s1 = UV[triangle[1]][0] - UV[triangle[0]][0]
		t1 = UV[triangle[1]][1] - UV[triangle[0]][1]
		s2 = UV[triangle[2]][0] - UV[triangle[0]][0]
		t2 = UV[triangle[2]][1] - UV[triangle[0]][1]
		check = s1*t2-s2*t1
		if check != 0:
			a = 1.0/(s1*t2-s2*t1)
			#T = 1.0/(s1*t2-s2*t1)*[t2*v1[0]-t1*v2[0], t2*v1[1]-t1*v2[1], t2*v1[2]-t1*v2[2]]
			#BiTangent = 1.0/(s1*t2-s2*t1)*[-s2*v1[0]+s1*v2[0], -s2*v1[1]+s1*v2[1], -s2*v1[2]+s1*v2[2]]
			T = [a*(t2*v1[0]-t1*v2[0]), a*(t2*v1[1]-t1*v2[1]), a*(t2*v1[2]-t1*v2[2])]
			BiTangent = [a*(-s2*v1[0]+s1*v2[0]), a*(-s2*v1[1]+s1*v2[1]), a*(-s2*v1[2]+s1*v2[2])]
		elif check == 0:
			T = [1.0,1.0,1.0]
			BiTangent = [0.0,0.0,0.0]
		for index in triangle:
			SharedTangentsList[index].append(T)
			SharedBiTangentsList[index].append(BiTangent)
	for SharedTangents in SharedTangentsList:
		Tx = 0.0
		Ty = 0.0
		Tz = 0.0
		for Tangents in SharedTangents:
			Tx += Tangents[0]
			Ty += Tangents[1]
			Tz += Tangents[2]
		T = [Tx, Ty, Tz]
		T = Normalize(T)
		TangentList.append(T)
	for SharedBiTangents in SharedBiTangentsList:
		BiTangentsx = 0.0
		BiTangentsy = 0.0
		BiTangentsz = 0.0
		for BiTangents in SharedBiTangents:
			BiTangentsx += BiTangents[0]
			BiTangentsy += BiTangents[1]
			BiTangentsz += BiTangents[2]
		BiTangent = [BiTangentsx, BiTangentsy, BiTangentsz]
		BiTangent = Normalize(BiTangent)
		BiTangentList.append(BiTangent)
	return TangentList

def Padding(FilePath, alignment):
	division1 = (os.path.getsize(FilePath)/alignment)
	division2 = math.ceil(os.path.getsize(FilePath)/alignment)
	padComp = int((division2 - division1)*alignment)
	return padComp

def PaddingLenght(lenght, alignment):
	division1 = (lenght/alignment)
	division2 = math.ceil(lenght/alignment)
	padComp = int((division2 - division1)*alignment)
	return padComp

def StringToID(String, use_UniqueIDs=False, vehicleName=''):
	if String == '':
		return String
	if use_UniqueIDs == True and vehicleName != '':
		String = String + "_" + vehicleName
	ID = hex(zlib.crc32(String.lower().encode()) & 0xffffffff)
	ID = ID[2:].upper().zfill(8)
	ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0,len(ID),2)])
	return ID

def VerifyGenericIDs(game_version, Name, verify_genericIDs):
	if verify_genericIDs == False:
		Name = Name + "_raster"
		return (Name, False)
	if Name == '':
		return (Name, False)
	resourcePath = GenericResourceStringTableGet(game_version)
	if not resourcePath:
		#print("ResourceStringTable not found")
		Name = Name + "_Raster"
		return (Name, False)
	tree = et.parse(resourcePath)
	ResourceStringTable = tree.getroot()
	Resource = []
	try:
		#Resource = tree.find('.//Resource[contains(@name,"%s")]' % Name)
		Resource = tree.xpath('.//Resource[contains(@name,"%s")]' % Name)
	except:
		try:
			for n in ResourceStringTable:
				if Name in n.get('name') and (n.get('type') == "Texture" or n.get('type') == "PlaneTexture"):
					Resource.append(n)
					break
		except:
			Name = Name + "_raster"
			return (Name, False)
	if Resource == None:
		Name = Name + "_raster"
		return (Name, False)
	if len(Resource) == 0:
		Name = Name + "_raster"
		return (Name, False)
	
	try:
		Name = Resource[0].get('name')				#MAY SOMETIMES IT HAVE MORE ELEMENTS IN LIST
		for data in Resource:
			if data.get('type') == "Texture" or data.get('type') == "PlaneTexture":		# At least get one name of a file with the same format with high possibility of being the right one
				Name = data.get('name')
				break
		return (Name, True)
	except:
		Name = Name + "_raster"
		return (Name, False)

def BurnoutLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\BurnoutParadise'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None

def GenericResourceStringTableGet(game_version):
	if game_version == "BPR":
		path1 = '\\addons\\BurnoutParadise\\GenericResourceStringTables.xml'
		path2 = '\\addons\\BurnoutParadise\\GenericResourceStringTables_BP.xml'
	elif game_version == "BP":
		path1 = '\\addons\\BurnoutParadise\\GenericResourceStringTables_BP.xml'
		path2 = '\\addons\\BurnoutParadise\\GenericResourceStringTables.xml'
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + path1
		tpath2 = rpath + path2
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
		elif os.path.exists(tpath2):
			npath = '"' + tpath2 + '"'
			return tpath2
	return None

def CreateImage(srcPath, MaterialName, color):
	size = 32, 32
	if not os.path.exists(srcPath + "\\" + "CreatedTexture"):
		os.makedirs(srcPath + "\\" + "CreatedTexture")
	#ImageName = MaterialName[:-9] + "_DiffuseColor"
	ImageName = MaterialName[:-9].replace(chr(92),"").replace(chr(47),"").replace(chr(58),"").replace(chr(63),"").replace(chr(42),"").replace(chr(34),"").replace(chr(60),"").replace(chr(62),"").replace(chr(124),"")
	ImageName = ImageName + "_DiffuseColor"
	ImagePath = srcPath + "\\" + "CreatedTexture" + "\\" + ImageName + ".png"
	image = bpy.data.images.new(MaterialName[:-9], alpha=True, width=size[0], height=size[1])
	image.use_alpha = True
	image.alpha_mode = 'STRAIGHT'
	image.pixels = [color[0],color[1],color[2],color[3]] * size[0] * size[1]
	image.filepath_raw = ImagePath
	image.file_format = 'PNG'
	image.save()
	return (ImageName, ImagePath)

def nvidiaGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		#tpath = rpath + '\\addons\\nvidia\\nvidia_dds.exe'
		tpath = rpath + '\\addons\\nvidia-texture-tools-2.1.1-win64\\bin64\\nvcompress.exe'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return npath
	return None

def ImageToDDS(srcPath, RasterID, RasterPath, OutRasterPath):
	RasterName, extension = os.path.splitext(os.path.basename(RasterPath))
	RasterFolder = os.path.dirname(RasterPath)
	bpy.types.Scene.cuda = 0
	#dxtType = "DXT1(no alpha)"
	dxtType = "DXT5(with alpha)"
	NvidiaTool = nvidiaGet()
	if bpy.context.scene.cuda == 0:
		dxt5 = "-fast -alpha -nocuda -bc3 -silent"
		dxt1 = "-fast -nocuda -bc1 -silent"
	else:
		dxt5 = "-alpha -bc3 -silent"
		dxt1 = "-bc1 -silent"
	if extension == '.dds' or extension == '.DDS':
		with open(RasterPath, "rb") as tex:
			tex.seek(0x1C, 0)
			mipCount = struct.unpack("<i", tex.read(4))[0]
			if mipCount != 0: 
				shutil.copy2(RasterPath, OutRasterPath)
				return 1
			tex.seek(0x54, 0)
			imgFmt2 = tex.read(4)
			#DXT1
			if imgFmt2 == b'\x44\x58\x54\x31':
				dxtType = 'DXT1(no alpha)'
			#DXT5
			elif imgFmt2 == b'\x44\x58\x54\x35':
				dxtType = 'DXT5(with alpha)'
	if not NvidiaTool:
		print("Nvidia tools not found")
		return 0
	if extension in ['.png','.PNG','.tga','.TGA','.dds','.DDS']:
		if dxtType == 'DXT1(no alpha)':
			os.system('"' + NvidiaTool + ' ' + dxt1 + ' ' + '"' + RasterPath + '"' + ' ' + '"' + OutRasterPath + '"' + '"')
		elif dxtType == 'DXT5(with alpha)':
			os.system('"' + NvidiaTool + ' ' + dxt5 + ' ' + '"' + RasterPath + '"' + ' ' + '"' + OutRasterPath + '"' + '"')

def ReadBPBones(srcPath, skeletonName):
	BoneCoordsList = []
	if skeletonName != "":
		LibraryPath = BurnoutLibraryGet()
		skeletonID = StringToID(skeletonName + "deformationmodel")
		SkeletonPathBPR = LibraryPath + "\\" + "BPR_Library_PC" + "\\" + "StreamedDeformationSpec" + "\\" + skeletonID + ".dat"
		if os.path.isfile(srcPath + "\\" + skeletonID + ".dat"):
			DeformationPath = srcPath + "\\" + skeletonID + ".dat"
		elif os.path.isfile(SkeletonPathBPR):
			DeformationPath = SkeletonPathBPR
		elif os.path.isfile(srcPath + "\\" + "Skeleton" + ".dat"):
			DeformationPath = srcPath + "\\" + "Skeleton" + ".dat"
		elif os.path.isfile(srcPath + "\\" + "Bones" + ".dat"):
			DeformationPath = srcPath + "\\" + "Bones" + ".dat"
		else:
			return (BoneCoordsList)
	else:
		if os.path.isfile(srcPath + "\\" + "Skeleton" + ".dat"):
			DeformationPath = srcPath + "\\" + "Skeleton" + ".dat"
		elif os.path.isfile(srcPath + "\\" + "Bones" + ".dat"):
			DeformationPath = srcPath + "\\" + "Bones" + ".dat"
		else:
			return (BoneCoordsList)
	with open(DeformationPath, "rb") as f:
		bonePCoords = [[0,0,0] for _ in range(0,20)]
		DefaultPCoords = [[0,0,0]]
		f.seek(0x4, 0)
		BonesPositions, NumBones = struct.unpack("<ii", f.read(8))
		f.seek(BonesPositions - 0x40, 0)
		DefaultPCoords[0][0], DefaultPCoords[0][1], DefaultPCoords[0][2] = struct.unpack("<fff", f.read(12))
		f.seek(0x110, 0)
		for i in range(0, 20):
			bonePCoords[i][0], bonePCoords[i][1], bonePCoords[i][2] = struct.unpack("<fff", f.read(12))
			bonePCoords[i][0] = bonePCoords[i][0] + DefaultPCoords[0][0]
			bonePCoords[i][1] = bonePCoords[i][1] + DefaultPCoords[0][1]
			bonePCoords[i][2] = bonePCoords[i][2] + DefaultPCoords[0][2]
			f.seek(0x34, 1)
		f.seek(BonesPositions, 0)
		for i in range(0, NumBones):
			boneCoords = [[0,0,0]]
			boneCoords[0][0], boneCoords[0][1], boneCoords[0][2] = struct.unpack("<fff", f.read(12))
			f.seek(0x30, 1)
			boneParentIndex = struct.unpack("<B", f.read(1))[0]
			boneCoords[0][0] = bonePCoords[boneParentIndex][0] + boneCoords[0][0]
			boneCoords[0][1] = bonePCoords[boneParentIndex][1] + boneCoords[0][1]
			boneCoords[0][2] = bonePCoords[boneParentIndex][2] + boneCoords[0][2]
			f.seek(0x13, 1)
			#BoneCoordsList.append(boneCoords)
			BoneCoordsList.append([boneCoords[0][0],boneCoords[0][1],boneCoords[0][2]])
	return (BoneCoordsList)

def BonePositions(srcPath):
	BoneCoords = []
	BoneCoord = [0]*3
	BonesFilePath = srcPath + "\\" + "Bones" + ".txt"
	if not os.path.isfile(BonesFilePath):
		return (BoneCoords)
	with open(BonesFilePath, "r") as BonesFile:
		line0 = BonesFile.readline()
		a = line0.rstrip()
		a = a.split(" ")
		NumBones = int(a[3])
		BCoord = [0,0,0]*NumBones
		line00 = BonesFile.readline()
		for i in range(0, NumBones):
			line1 = BonesFile.readline()
			a = line1.rstrip()
			a = a.split(" ")
			BoneIndex = a[2]
			line2 = BonesFile.readline()
			a = line2.rstrip()
			a = a.split(" ")
			PBoneIndex = a[3]
			line3 = BonesFile.readline()
			a = line3.rstrip()
			a = a.replace(',', '')
			a = a.split(" ")
			BoneCoord[0] = float(a[0])
			BoneCoord[1] = float(a[1])
			BoneCoord[2] = float(a[2])
			BCoord[i] = [BoneCoord[0], BoneCoord[1], BoneCoord[2]]
			BoneCoords.append(BCoord[i])
			line4 = BonesFile.readline()
	return (BoneCoords)

def NearestPoints(x,y,z,CoordinatesList,TransformMat,BoneCoords):
	BoneIndex1 = None
	BoneIndex2 = None
	BoneIndex3 = None
	#x,y,z = Transform(x,y,z,CoordinatesList,TransformMat)
	D = [0.0]*(len(BoneCoords))
	for i in range(0,len(BoneCoords)):
		D[i] = ((x-BoneCoords[i][0])**2 + (y-BoneCoords[i][1])**2 + (z-BoneCoords[i][2])**2)**0.5
	min1,min2,min3 = sorted(D)[:3]
	for i in range(0,len(BoneCoords)):
		if D[i] == min1 and BoneIndex1 == None:
			BoneIndex1 = i
		elif D[i] == min2 and BoneIndex2 == None:
			BoneIndex2 = i
		elif D[i] == min3:
			BoneIndex3 = i
	if min2 == min1:
		BoneIndex2 = BoneIndex1
	if min3 == min2:
		BoneIndex3 = BoneIndex2
	dt = min1 + min2
	BoneWeight1 = min2/dt*255.0
	BoneWeight2 = min1/dt*255.0
	BoneWeight3 = 255.0 - BoneWeight1 - BoneWeight2
	return (BoneIndex1,BoneIndex2,BoneIndex3,BoneWeight1,BoneWeight2,BoneWeight3)

def Transform(x,y,z,CoordinatesList,TransformMat):
	x = abs(TransformMat[0][0])*(x+CoordinatesList[0])
	y = abs(TransformMat[2][1])*(y+CoordinatesList[2])
	z = abs(-TransformMat[1][2])*(z-CoordinatesList[1])
	#[x,y,z,1] = TransformMat*[(x+CoordinatesList[0]),y+CoordinatesList[2],CoordinatesList[1],1]
	return (x,y,z)

def CrossProduct(v1, v2):
	return [v1[1]*v2[2]-v1[2]*v2[1], v1[2]*v2[0]-v1[0]*v2[2], v1[0]*v2[1]-v1[1]*v2[0]]

def Normalize(N):
	if N[0] != 0 or N[1] != 0 or N[2] != 0:
		M = (N[0]**2+N[1]**2+N[2]**2)**0.5
		N[0] = N[0]/M
		N[1] = N[1]/M
		N[2] = N[2]/M
		N = [N[0],N[1],N[2]]
	return N

def veckey3d(v):
	return round(v.x, 4), round(v.y, 4), round(v.z, 4)

def veckey2d(v):
	return round(v[0], 4), round(v[1], 4)

def RemoveDuplicatedIDs(IDsList):
	TempDict = {}
	for key,value in IDsList.items():
		if key not in TempDict.keys():
			TempDict[(key)] = value
	IDsList = TempDict
	return IDsList

def RemoveUnderscoresIDs(IDsList):		#NOT WORKING WELL
	TempDict = {}
	for key,value in IDsList.items():
		key.replace('_', '')
		TempDict[key] = value
	IDsList = TempDict
	return IDsList

def type2id(type):
	list = {'00000000':'Raster',
		'00000001':'Material',
		'00000003':'TextFile',
		'0000000A':'VertexDesc',
		'0000000B':'0B (console only)',
		'0000000C':'Renderable',
		'0000000D':'0D (console only)',
		'0000000E':'TextureState',
		'0000000F':'MaterialState',
		'00000012':'ShaderProgramBuffer',
		'00000014':'ShaderParameter',
		'00000016':'Debug',
		'00000017':'KdTree',
		'00000019':'Snr',
		'0000001B':'AttribSysSchema',
		'0000001C':'AttribSysVault',
		'0000001E':'AptDataHeaderType',
		'0000001F':'GuiPopup',
		'00000021':'Font',
		'00000022':'LuaCode',
		'00000023':'InstanceList',
		'00000024':'CollisionMeshData (2006 build)',
		'00000025':'IdList',
		'00000027':'Language',
		'00000028':'SatNavTile',
		'00000029':'SatNavTileDirectory',
		'0000002A':'Model',
		'0000002B':'ColourCube',
		'0000002C':'HudMessage',
		'0000002D':'HudMessageList',
		'0000002E':'HudMessageSequence',
		'0000002F':'HudMessageSequenceDictionary',
		'00000030':'WorldPainter2D',
		'00000031':'PFXHookBundle',
		'00000032':'Shader',
		'00000041':'ICETakeDictionary',
		'00000042':'VideoData',
		'00000043':'PolygonSoupList',
		'00000045':'CommsToolListDefinition',
		'00000046':'CommsToolList',
		'00000051':'AnimationCollection',
		'0000A000':'Registry',
		'0000A020':'GenericRwacWaveContent',
		'0000A021':'GinsuWaveContent',
		'0000A022':'AemsBank',
		'0000A023':'Csis',
		'0000A024':'Nicotine',
		'0000A025':'Splicer',
		'0000A028':'GenericRwacReverbIRContent',
		'0000A029':'SnapshotData',
		'0000B000':'ZoneList',
		'00010000':'LoopModel',
		'00010001':'AISections',
		'00010002':'TrafficData',
		'00010003':'Trigger',
		'00010004':'DeformationModel (2006 build)',
		'00010005':'VehicleList',
		'00010006':'GraphicsSpec',
		'00010008':'ParticleDescriptionCollection',
		'00010009':'WheelList',
		'0001000A':'WheelGraphicsSpec',
		'0001000B':'TextureNameMap',
		'0001000C':'ICEList (2006 build)',
		'0001000D':'ICEData (2006 build)',
		'0001000E':'Progression',
		'0001000F':'PropPhysics',
		'00010010':'PropGraphicsList',
		'00010011':'PropInstanceData',
		'00010012':'EnvironmentKeyframe',
		'00010013':'EnvironmentTimeLine',
		'00010014':'EnvironmentDictionary',
		'00010015':'GraphicsStub',
		'00010016':'StaticSoundMap',
		'00010018':'StreetData',
		'00010019':'VFXMeshCollection',
		'0001001A':'MassiveLookupTable',
		'0001001B':'VFXPropCollection',
		'0001001C':'StreamedDeformationSpec',
		'0001001D':'ParticleDescription',
		'0001001E':'PlayerCarColours',
		'0001001F':'ChallengeList',
		'00010020':'FlaptFile',
		'00010021':'ProfileUpgrade',
		'00010023':'VehicleAnimation',
		'00010024':'BodypartRemapping',
		'00010025':'LUAList',
		'00010026':'LUAScript'}
	#Thanks to burninrubber0 for this list
	for ResourceID, ResourceType in list.items():
		if ResourceType == type:
			type = ResourceID
	return (type)

def SplitMeshVertices(max, modeltype):
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		bpy.context.scene.objects.active=element
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		stdout = io.StringIO()
		with redirect_stdout(stdout):
			if modeltype == "col": bpy.ops.mesh.remove_doubles()	# It brokes the uvs
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			if modeltype == "col": bpy.ops.mesh.remove_doubles()	# It brokes the uvs
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		
		if len(element.data.vertices) > (max+1):
			#print("High number of vertices detected, splitting them")
			element.select = True
			bpy.context.scene.objects.active=element
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')
			mesh = element.data
			VerticesList = []
			bpy.ops.object.mode_set(mode='OBJECT')
			i = 0
			while i < len(mesh.polygons):
				face = mesh.polygons[i]
				newVertices = []
				verts = face.vertices[:]
				for vertice in face.vertices:
					if vertice in VerticesList: continue
					newVertices.append(vertice)
				if newVertices == []:
					i += 1
					continue
				if (len(VerticesList) + len(newVertices)) > (max+1):
					bpy.ops.object.mode_set(mode='EDIT')
					bpy.ops.mesh.separate(type='SELECTED')
					bpy.ops.mesh.select_all(action='DESELECT')
					bpy.ops.object.mode_set(mode='OBJECT')
					VerticesList = []
					VerticesList.extend([*verts])
					i = 0
					continue
				VerticesList.extend([*newVertices])
				face.select = True
				i += 1
			bpy.ops.object.select_all(action='DESELECT')
			bpy.context.scene.objects.active = None

def SplitEdges():
	bm = bmesh.new()
	meshes = set(object.data for object in bpy.context.scene.objects if object.type == 'MESH' and object.hide == False)
	for mesh in meshes:
		bm.from_mesh(mesh)
		bmesh.ops.split_edges(bm, edges=bm.edges)
		#bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # worst, lot of holes
		bm.to_mesh(mesh)
		bm.clear() 
		mesh.update()
	bm.free()

def Resize_small_images(x=16,y=16):
	ImageName = ''
	images = bpy.data.images
	for image in images:
		filepath = bpy.path.abspath(image.filepath)
		if not os.path.isfile(filepath):
			try:
				image.unpack(method='USE_LOCAL')	# Default method, it unpacks to the current .blend directory
			except:
				continue
		width = image.size[0]
		height = image.size[1]
		if width <= 4 or height <= 4:
			if width == 0 or height == 0:
				continue
			ratio = (width*1.0)/(height*1.0)	# x/y
			if ratio != 1.0:
				if width < height:
					y = x/ratio
				elif height < width:
					x = ratio*y
			ImageName = image.name
			bpy.data.images[ImageName].scale(x, y)
			
			# Saving
			image.filepath_raw = image.filepath.replace(".dds",".png")
			image.file_format = 'PNG'
			image.save()
			image.filepath = image.filepath.replace(".dds",".png")
			image.name = image.name.replace(".dds",".png")
			image.reload()

def Split_UVs():
	bm = bmesh.new()
	meshes = set(object.data for object in bpy.context.scene.objects if object.type == 'MESH' and object.hide == False)
	for mesh in meshes:
		UVsList = [[] for _ in range(len(mesh.vertices))]
		faceuv = len(mesh.uv_textures) > 0
		
		mesh.calc_normals_split()
		bm.from_mesh(mesh)
		bm.normal_update()
		bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
		bm.faces.ensure_lookup_table()
		#bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-06)
		#bm.to_mesh(mesh)
		
		if faceuv:
			uv_layer = bm.loops.layers.uv.active
			
			NewFaces = []
			faces_to_delete = []
			verticesUV_splitted = []
			new_vertices = []
			vert_normals_list = []
			BMFaces_new_indices = []
			create_face = False
			for face in bm.faces:
				newVerts = []
				for vert in face.verts:
					newVerts.append(vert)
				for loop in face.loops:
					uvs = [[loop[bm.loops.layers.uv[i]].uv.x,loop[bm.loops.layers.uv[i]].uv.y] for i in range(0,len(bm.loops.layers.uv))]
					
					if UVsList[loop.vert.index] == []:
						UVsList[loop.vert.index] = uvs
					elif UVsList[loop.vert.index] != uvs:
						#print("Not equal but with the same xy coordinates, should be different vertices")
						if [loop.vert.index,uvs] not in verticesUV_splitted:
							# Adding to a list of splitted vertex
							verticesUV_splitted.append([loop.vert.index,uvs])
							# Splitting the vertex
							BMVert = bm.verts.new(loop.vert.co, loop.vert)
							BMVert.normal = loop.vert.normal
							BMVert.index = len(bm.verts)
							#bm.verts.index_update()
							# Adding the new created vertex to a list
							new_vertices.append(BMVert)
						else:
							BMVert = new_vertices[verticesUV_splitted.index([loop.vert.index,uvs])]
						# Replacing the loop/face vertex
						for i, vert in enumerate(newVerts):
							if vert.index == loop.vert.index:
								newVerts[i] = BMVert
						create_face = True
				if create_face:
					NewFaces.append([newVerts,face])
					create_face = False
			for face in NewFaces:
				BMFace = bm.faces.new(face[0], face[1])
				BMFace.index = len(bm.faces)-1
				bm.faces.ensure_lookup_table()
				
				for loop, loop_original in zip(BMFace.loops, face[1].loops):
					uv_layers = bm.loops.layers.uv
					uv = loop_original[uv_layer].uv
					loop[uv_layer].uv = [uv[0], uv[1]]
					if len(uv_layers) > 1:
						uv2_layer = bm.loops.layers.uv[1]
						if len(uv_layers) > 2:									# Need for Speed Most Wanted scratch uv layer
							uv2_layer = bm.loops.layers.uv[2]
						uv2 = loop_original[uv2_layer].uv
						loop[uv2_layer].uv = [uv2[0], uv2[1]]
					
					# The code below should be working too
					#for i in range(0,len(bm.loops.layers.uv)):
					#	loop[bm.loops.layers.uv[i]].uv = [loop_original[bm.loops.layers.uv[i]].uv.x,loop_original[bm.loops.layers.uv[i]].uv.y]
				BMFace.smooth = True
				BMFace.material_index = face[1].material_index
				
				#bm.faces.ensure_lookup_table()
				vert_normals = []
				face_ = mesh.polygons[face[1].index]
				for l_idx in face_.loop_indices:
					vert_normals.append(mesh.loops[l_idx].normal)
				vert_normals_list.append(vert_normals)
				BMFaces_new_indices.append(BMFace.index)
				
				if face[1] not in faces_to_delete:
					faces_to_delete.append(face[1])
			#bmesh.ops.delete(bm, geom=faces_to_delete, context=5)
			bm.to_mesh(mesh)
			
			for i, index in enumerate(BMFaces_new_indices):
				print(index, len(mesh.polygons), len(bm.faces))
				face_ = mesh.polygons[index]
				for j, l_idx in enumerate(face_.loop_indices):
					vert_normals.append(mesh.loops[l_idx].normal)
					mesh.loops[l_idx].normal = vert_normals_list[i][j]
			bmesh.ops.delete(bm, geom=faces_to_delete, context=5)
			bm.to_mesh(mesh)
		bm.clear()
		
		mesh.validate(clean_customdata=False)
		mesh.update()
	
	bm.free()

def SplitMeshTriangles(max):
	modeltype = "veh"	# TESTAR FIX
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		bpy.context.scene.objects.active=element
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_mode(type='FACE')
		bpy.ops.mesh.select_all(action='SELECT')
		stdout = io.StringIO()
		with redirect_stdout(stdout):
			if modeltype == "col": bpy.ops.mesh.remove_doubles()	# TESTAR
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			if modeltype == "col": bpy.ops.mesh.remove_doubles()	# TESTAR
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		
		if len(element.data.polygons) > (max):
			#print("High number of faces detected, splitting them")
			element.select = True
			bpy.context.scene.objects.active=element
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')
			mesh = element.data
			bpy.ops.object.mode_set(mode='OBJECT')
			i = 1
			while i <= len(mesh.polygons):
				face = mesh.polygons[i-1]
				if i > max:
					bpy.ops.object.mode_set(mode='EDIT')
					bpy.ops.mesh.separate(type='SELECTED')
					bpy.ops.mesh.select_all(action='DESELECT')
					bpy.ops.object.mode_set(mode='OBJECT')
					i = 1
					continue
				face.select = True
				i += 1
			bpy.ops.object.select_all(action='DESELECT')
			bpy.context.scene.objects.active = None

def ConvertNgons():
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		bpy.context.scene.objects.active=element
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER', extend=True)
		bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.context.scene.objects.active = None

def SplitByMaterial():
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		bpy.context.scene.objects.active = element	#make it the active element
		if bpy.context.mode != 'EDIT':				#if not in edit mode
			bpy.ops.object.editmode_toggle()		#enters in edit mode
			bpy.ops.mesh.separate(type='MATERIAL')	#separate it by material parts
			bpy.ops.object.editmode_toggle()		#exit edit mode
		else :										#else
			bpy.ops.mesh.separate(type='MATERIAL')	#separate it by material parts

def check_centering(DummyHelperList):
	if len(DummyHelperList) > 0:
		wheel_0 = DummyHelperList[0][1]
		wheel_0_x = DummyHelperList[0][2]
		wheel_0_y = DummyHelperList[0][3]
		wheel_1 = ""
		wheel_2 = ""
		centered_x = 0.0
		centered_y = 0.0
		break_1 = False
		break_2 = False
		if wheel_0 == "fr":
			wheel_1 = "rl"			# For checking y centering
			wheel_2 == "fl"			# For checking x centering
		elif wheel_0 == "fl":
			wheel_1 = "rr"
			wheel_2 == "fr"
		elif wheel_0 == "rr":
			wheel_1 = "fl"
			wheel_0 == "rl"
		elif wheel_2 == "rl":
			wheel_1 = "fr"
			wheel_2 == "rr"
		for i in range(1, len(DummyHelperList)):
			if wheel_1 == DummyHelperList[i][1]:
				if wheel_0[0] == "f":
					centered_y = DummyHelperList[i][3] + wheel_0_y
				elif wheel_0[0] == "r":
					centered_y = wheel_0_y - DummyHelperList[i][3]
				centered_y = wheel_0_y + DummyHelperList[i][3]
				break_1 = True
			elif wheel_2 == DummyHelperList[i][1]:
				if wheel_0[0] == "f":
					centered_x = DummyHelperList[i][2] + wheel_0_x
				elif wheel_0[0] == "r":
					centered_x = wheel_0_x - DummyHelperList[i][2]
				centered_x = wheel_0_x + DummyHelperList[i][2]
				break_2 = True
			if break_1 == True and break_2 == True:
				break
		if centered_y != 0.0 and centered_x != 0.0:
			print("Wheels distances from origin should be almost equal.")
			print("Consider moving your model", -0.5*centered_y, "in the y axis and", -0.5*centered_x, "in the x axis.")
		elif centered_y != 0.0:
			print("Wheels distances from origin should be almost equal.")
			print("Consider moving your model", -0.5*centered_y,"in the y axis.")
		elif centered_x != 0.0:
			print("Wheels distances from origin should be almost equal.")
			print("Consider moving your model", -0.5*centered_x,"in the x axis.")

def ApplyScale():
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
	bpy.ops.object.select_all(action='TOGGLE')

def ApplyRotation():
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
	bpy.ops.object.select_all(action='TOGGLE')

def ApplyTransform(location=False, rotation=False, scale=False):
	#bpy.ops.object.select_all(action='SELECT')
	#bpy.ops.object.select_by_type(type='MESH')
	#bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
	#if location == True:
	#	bpy.ops.object.transforms_to_deltas(mode='LOC')
	#bpy.ops.object.select_all(action='TOGGLE')
	for element in bpy.context.scene.objects:
		if element.type == "EMPTY":
			#if "body" in element.name.lower():
			if len(element.children) > 0:				# If there is an Empty inside an Empty it enters in the if
				element.select = True
				bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)		# Maybe just scale in wheels
				bpy.ops.object.visual_transform_apply()
				element.select = False
		if element.type != "MESH": continue
		if element.hide == True: continue
		Info = element.name.split("_")
		element.select = True
		if element.name.split("_")[0].lower() == "wheel":
			if location == True:
				bpy.ops.object.transforms_to_deltas(mode='LOC')
				bpy.ops.object.transform_apply(location=False, rotation=rotation, scale=scale)
		else:
			bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
			bpy.ops.object.visual_transform_apply()
		element.select = False
	bpy.ops.object.select_all(action='DESELECT')

def RotateAllObjects(angle=0.0):
	Transform = []
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
	bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0.0, 0.0, 0.0))
	empty = bpy.context.active_object

	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		element.select = True

	bpy.ops.object.parent_set()
	#empty.rotation_euler.x = math.pi*3.0/2.0			# Working too
	empty.rotation_euler.x = radians(angle)
	empty.rotation_euler.y = 0.0
	empty.rotation_euler.z = 0.0
	bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
	bpy.ops.object.select_all(action='DESELECT')
	empty.select = True
	bpy.ops.object.delete()
	bpy.context.scene.objects.active = None
	bpy.ops.object.select_all(action='DESELECT')
	
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		if len(element.data.vertices) == 0: continue
		Transform.append(element.matrix_world)
	return Transform

def RotateSingleObject(element, angle=0.0):
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
	bpy.ops.object.empty_add(type='PLAIN_AXES',location=(0.0, 0.0, 0.0))
	empty = bpy.context.active_object
	
	element.select = True

	bpy.ops.object.parent_set()
	empty.rotation_euler.x = radians(angle)
	empty.rotation_euler.y = 0.0
	empty.rotation_euler.z = 0.0
	bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
	bpy.ops.object.select_all(action='DESELECT')
	empty.select = True
	bpy.ops.object.delete()
	bpy.context.scene.objects.active = None
	bpy.ops.object.select_all(action='DESELECT')

	return element.matrix_world 

def main(context, srcPath, vehicleName, skeletonName, verify_genericIDs, use_Rotation, use_Accurate_split, use_Damage, use_UniqueIDs, recalculate_bones, game_version):
	os.system('cls')
	start_time = time.time()
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	Resize_small_images(x=16,y=16)
	#SplitEdges()			# Fix the UVs, remove doubles fix normals but mess with the UVs
	# world = bpy.context.scene.world
	# if world.name.lower() == "trk" or world.name.lower() == "track":
		# for element in bpy.context.scene.objects:
			# if element.type != "MESH": continue
			# if len(element.data.vertices) == 0: continue
			# bpy.context.scene.cursor_location = (0.0, 0.0, 0.0)
			# element.select = True
			# bpy.context.scene.objects.active=element
			# for i in range(0, 10):
				# #bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
				# bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			# bpy.ops.object.select_all(action='DESELECT')
			# bpy.context.scene.objects.active = None
	#ApplyTransform(location=True, rotation=True, scale=True)				# CHANGED
	if bpy.context.scene.world is None:
		newworld = bpy.data.worlds.new("World")
		bpy.context.scene.world = newworld
	world = bpy.context.scene.world
	if world.name.lower() == "collision" or world.name.lower() == "colision" or world.name.lower() == "col":
		Nobjects = sum(1 for object in bpy.context.scene.objects if object.type == 'MESH' and object.hide == False)
		if Nobjects == 0:
			print("No meshes in the scene of ", vehicleName)
			CreatePolygonSoupList(srcPath, context, vehicleName)
			elapsed_time = time.time() - start_time
			print("Elapsed time:",elapsed_time)
			return {'FINISHED'}
		#original_area = bpy.context.area.type
		#bpy.context.area.type = 'VIEW_3D'
		#bpy.ops.object.mode_set(mode='EDIT')
		#bpy.ops.mesh.select_mode(type='FACE')
		#bpy.ops.object.mode_set(mode='OBJECT')
		#bpy.context.area.type = original_area
		#ApplyTransform(location=True, rotation=True, scale=True)
		#SplitMeshVertices(0xFF)
		
		SplitMeshTriangles(0xFE)	# Fixed
		SplitMeshVertices(0xFE, "col") # The maximum lenght is 255 (counts)
		ConvertNgons()
		ApplyTransform(location=True, rotation=True, scale=True)				## WARNING: SOMETIMES CAUSE AN ISSUE IF REMOVE DOUBLES
		CreatePolygonSoupList(srcPath, context, vehicleName)
		elapsed_time = time.time() - start_time
		print("Elapsed time:",elapsed_time)
		return {'FINISHED'}
	#SplitMeshVertices(0xFFFF, "")
	SplitMeshVertices(0xCFFF, "")
	ModelNames = []
	ModelNumbers = []
	RenderableNames = []
	is_backdrop = []
	#CoordinatesList = []
	CoordinatesList = {}
	DummyHelperList = []
	EffectsDummyHelperList = []
	Transform = []
	TransformBP = []
	IDsList = {}
	IDsListAT = {}
	IDsListCD = {}
	ModelDict = {}
	MaterialDict = {}
	SubPart_ModelNames = []
	SubPart_ModelNumbers = []
	SubPart_Info = []
	wheels = False
	reuse_Object = False
	cte_transform = 0
	#SplitByMaterial()
	#ApplyScale()
	BoneCoordsList = ReadBPBones(os.path.dirname(srcPath), skeletonName)
	#bpy.ops.object.select_all(action = 'SELECT')
	#bpy.ops.object.origin_set(type = 'ORIGIN_GEOMETRY')
	if use_Rotation and (world.name.lower() == "trk" or world.name.lower() == "track"):
		reuse_Object = True
		TransformBP = RotateAllObjects(angle=270.0)
		#ApplyTransform(location=True, rotation=True, scale=True)
	elif use_Rotation:
		TransformBP = RotateAllObjects(angle=270.0)
		#ApplyTransform(location=True, rotation=True, scale=True)
	else:
		ApplyTransform(location=True, rotation=True, scale=True)
	for element in bpy.context.scene.objects:
		if element.type != "EMPTY": continue
		if element.hide == True: continue
		obj = element
		print("%s" % obj.name)
		Info = obj.name.split("_")
		if Info[0].lower() == "wheel":
			DummyHelperList.append([Info[0],Info[1],obj.location.x,obj.location.y,obj.location.z])
			EffectsDummyHelperList.append([Info[0],Info[1],obj.location.x,obj.location.y,obj.location.z])
		elif Info[0].lower() == "boost":
			EffectsDummyHelperList.append([Info[0],Info[1],obj.location.x,obj.location.y,obj.location.z])
		elif Info[0].lower() == "light":
			EffectsDummyHelperList.append([Info[0],Info[1],obj.location.x,obj.location.y,obj.location.z])
	
	# Just checking if the model is centered (wheels distances from origin should be almost equal)
	check_centering(DummyHelperList)
	
	#+ grab the current area
	#original_area = bpy.context.area.type
	
	#scene = bpy.context.scene
	#for count, obj in enumerate(bpy.context.selected_objects):
	# for count, obj in enumerate(bpy.context.scene.objects):
		# if obj.type == 'MESH':
			# faceuv = len(obj.data.uv_textures) > 0
			# if faceuv:
				# #scene.objects.active = obj
				# bpy.context.scene.objects.active=obj
				# #+ switch to the image editor to perform transforms etc
				# bpy.context.area.type = 'IMAGE_EDITOR'
				# #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
				# bpy.ops.object.mode_set(mode='EDIT')
				
				# #bpy.ops.mesh.reveal()
				# bpy.ops.mesh.select_all(action='SELECT')
				# #+ select the uvs
				# bpy.ops.uv.select_all(action='SELECT')
				
				# bpy.ops.transform.translate(value=(0, 1, 0), constraint_axis=(True, True, True))
				
				# obj.data.update()
				
				# #+ return to the original mode where the script was run
				# #bpy.context.area.type = original_area
				# #bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
				# bpy.ops.object.mode_set(mode='OBJECT')
				# bpy.context.area.type = original_area
			
	#+ grab the current area
	#original_area = bpy.context.area.type
	index = -1		# visible meshes index (used for deleting entries on TransformBP list)
	for element in bpy.context.scene.objects:
		if element.type != "MESH": continue
		if element.hide == True: continue
		if len(element.data.vertices) == 0: continue
		index += 1
		#element.rotation_euler = (0,0,radians(90))
		obj = element
		mesh = element.data
		#ModelNames.append(obj.name + "_model")
		#RenderableNames.append(obj.name)
		print("%s" % obj.name)
		#CoordinatesList.append([obj.location.x,obj.location.y,obj.location.z])
		bpy.context.scene.objects.active=obj
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		stdout = io.StringIO()
		with redirect_stdout(stdout):
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			bpy.ops.mesh.dissolve_degenerate()
			bpy.ops.mesh.delete_loose()
			#bpy.ops.mesh.remove_doubles()	# TESTAR
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
		bpy.ops.mesh.select_all(action='DESELECT')
		
		#bpy.context.area.type = 'IMAGE_EDITOR'
		#bpy.ops.object.mode_set(mode='EDIT', toggle=False)
		#bpy.ops.mesh.reveal()
		#bpy.ops.mesh.select_all(action='SELECT')
		#+ select the uvs
		#bpy.ops.uv.select_all(action='SELECT')
		#bpy.ops.transform.translate(value=(0, 0.0039, 0), constraint_axis=(False, True, False))
		#+ return to the original mode where the script was run
		#bpy.context.area.type = original_area
		#bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
		bpy.ops.object.mode_set(mode='OBJECT')
		
		if not use_Rotation:
			if world.name.lower() == "trk" or world.name.lower() == "track":
				element.select = True
				bpy.context.scene.objects.active=element
				for i in range(0, 10):
					#bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
					bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
				bpy.ops.object.select_all(action='DESELECT')
				bpy.context.scene.objects.active = None
		#CoordinatesList[obj.name + "_model"] = (obj.location.x,obj.location.y,obj.location.z)
		#Transform.append(element.matrix_world)
		#matrix_world = element.matrix_world
		LOD, ModelID = CreateRenderableBody(srcPath, obj, [obj.location.x,obj.location.y,obj.location.z], element.matrix_world, DummyHelperList, BoneCoordsList, ModelDict, MaterialDict, IDsList, world, vehicleName, verify_genericIDs, reuse_Object, use_Rotation, use_Accurate_split, use_Damage, use_UniqueIDs, recalculate_bones, game_version)
		if LOD == 0:
			CoordinatesList[obj.name + "_model"] = (obj.location.x,obj.location.y,obj.location.z)
			#ModelNames.append(ModelID)
			RenderableName = obj.name
			if reuse_Object:
				RenderableName = RenderableName.split(".")[0]
				#ModelNames.append(obj.name.split(".")[0] + "_model")
				#ModelNames.append(obj.name + "_model")
			try:
				if obj['ModelID'] == RenderableName:
					ModelNames.append(obj['ModelID'] + "_model")
				else:
					ModelNames.append(obj['ModelID'])
			except: ModelNames.append(RenderableName + "_model")
			RenderableNames.append(RenderableName)
			try: is_backdrop.append(obj['Backdrop'])
			except: is_backdrop.append(0)
			
			try:
				ModelNumbers.append(obj['ObjectNumber'])	# Maybe use later to sort the modelnames and write them in the original ordering in the GraphicsSpec
			except:
				#ModelNumbers.append(len(ModelNumbers))
				ModelNumbers.append(-1)
			Transform.append(element.matrix_world)
			ModelInfo = obj.name.split("_")
			if len(ModelInfo) >= 2:
				if ModelInfo[0].lower() == "wheel": wheels = True
		elif LOD >= 1:
			if use_Rotation:
				# removing in order to not add them on GraphicsSpec (just LOD0)
				del TransformBP[index - cte_transform]
				cte_transform += 1 
		
		# Checking if it is a glass subpart
		SubPart = False
		try:
			SubPart = obj['SubPartParentNumber']
			SubPart = obj['SubPartParentNumber2']
			SubPart = True
		except: SubPart = False
		if SubPart == True and LOD == 0:
			SubPart_ModelNames.append(ModelNames[-1])
			SubPart_ModelNumbers.append(ModelNumbers[-1])
			SubPart_Info.append([obj['SubPartParentNumber'], obj['SubPartParentNumber2']])
			del ModelNames[-1]
			del ModelNumbers[-1]
			del RenderableNames[-1]
			del is_backdrop[-1]
			del CoordinatesList[obj.name + "_model"]
			del Transform[-1]
			if use_Rotation:
				# removing in order to not add them on GraphicsSpec (just LOD0)
				del TransformBP[index - cte_transform]
				cte_transform += 1
	
	for ModelID, RenderableList in ModelDict.items():
		RenderableList = [ID for ID in RenderableList if ID is not None]
		if len(RenderableList) == 1:
			RenderableID = RenderableList[0]
			CreateModel(srcPath, ModelID, RenderableID, world.name.lower())
		elif len(RenderableList) > 1:
			CreateModel_withlods(srcPath, ModelID, RenderableList, world.name.lower())
			
	
	if use_Rotation and (world.name.lower() == "trk" or world.name.lower() == "track"):
		Transform = copy.deepcopy(TransformBP)
	elif use_Rotation:
		Transform = copy.deepcopy(TransformBP)
	#if len(RenderableNames) >= 100:
	if len(RenderableNames) >= 96:
		if (world.name.lower() == "trk" or world.name.lower() == "track") and len(RenderableNames) >= 1000:		#maybe 793 or 608 (always loaded)
			step = int(math.ceil(len(RenderableNames)/1000))
			ModelNames, RenderableNames, is_backdrop, CoordinatesList, Transform = MergeRenderables(srcPath, step, ModelNames, RenderableNames, is_backdrop, CoordinatesList, DummyHelperList, Transform, IDsList, world, vehicleName, use_UniqueIDs)
		elif world.name.lower() != "trk" and world.name.lower() != "track":
			step = int(math.ceil(len(RenderableNames)/70))
			ModelNames, RenderableNames, is_backdrop, CoordinatesList, Transform = MergeRenderables(srcPath, step, ModelNames, RenderableNames, is_backdrop, CoordinatesList, DummyHelperList, Transform, IDsList, world, vehicleName, use_UniqueIDs)
			if len(DummyHelperList) != 0:
				ModelNames, RenderableNames, CoordinatesList, Transform = MergeWheelsRenderables(srcPath, ModelNames, RenderableNames, CoordinatesList, DummyHelperList, Transform, IDsList, world, vehicleName, use_UniqueIDs)
	IDsList['26_A0_72_7E'] = 'MaterialState'
	IDsList['62_15_71_78'] = 'MaterialState'
	IDsList['9B_9F_65_D4'] = 'MaterialState'
	IDsList['B9_BE_2F_14'] = 'MaterialState'
	IDsList['CD_F0_44_F7'] = 'MaterialState'
	IDsList['EC_4F_6F_B4'] = 'MaterialState'
	IDsList['F0_46_DA_CD'] = 'MaterialState'
	IDsList['FE_64_A3_0B'] = 'MaterialState'
	IDsList['57_48_54_45'] = 'TextureState'
	IDsList['B0_37_C7_80'] = 'TextureState'
	IDsList['F5_A1_4F_DD'] = 'TextureState'
	IDsList['52_76_AE_90'] = 'TextureState'
	IDsList['57_48_54_C9'] = 'Raster'
	CreateTextureState(game_version, srcPath, 'B0_37_C7_80', 'B3_37_C7_80')	#Black
	CreateTextureState(game_version, srcPath, 'F5_A1_4F_DD', 'B1_6F_7B_68')	#Crumple
	CreateTextureState(game_version, srcPath, '57_48_54_45', '57_48_54_C9')	#White
	CreateTextureState(game_version, srcPath, '52_76_AE_90', 'ED_69_B6_11')	#Mirror
	CreateWhiteRaster(game_version, srcPath)
	if len(ModelNames) > 0:
		if world.name.lower() == "trk" or world.name.lower() == "track":
			TrkNumber = vehicleName
			InstanceListID = StringToID("TRK_UNIT" + TrkNumber + "_list")
			PropInstanceDataID = StringToID("PRP_INST_" + TrkNumber)
			PropGraphicsListID = StringToID("PRP_GL__" + TrkNumber)
			StaticSoundMapID1 = StringToID("TRK_UNIT" + TrkNumber + "_Emitter")
			StaticSoundMapID2 = StringToID("TRK_UNIT" + TrkNumber + "_Passby")
			IDsList[InstanceListID] = 'InstanceList'
			IDsList[PropInstanceDataID] = 'PropInstanceData'
			IDsList[PropGraphicsListID] = 'PropGraphicsList'
			IDsList[StaticSoundMapID1] = 'StaticSoundMap'
			IDsList[StaticSoundMapID2] = 'StaticSoundMap'
			CreateInstanceList(srcPath,InstanceListID,ModelNames,is_backdrop,CoordinatesList,Transform,use_Rotation,TrkNumber,use_UniqueIDs)
			CreatePropInstanceData(srcPath,PropInstanceDataID,TrkNumber)
			CreatePropGraphicsList(srcPath,PropGraphicsListID,TrkNumber)
			CreateStaticSoundMap(srcPath,StaticSoundMapID1)
			CreateStaticSoundMap(srcPath,StaticSoundMapID2)
			IDsList = RemoveDuplicatedIDs(IDsList)
			IDsList = RemoveUnderscoresIDs(IDsList)
			CreateIDsTable(srcPath, IDsList, "IDs_GR")
			
			# Return objects to its original rotation
			if use_Rotation:
				_ = RotateAllObjects(angle=-270.0)
			
			elapsed_time = time.time() - start_time
			print("Elapsed time:",elapsed_time)
			return {'FINISHED'}
		else:
			IDsList[StringToID(vehicleName + "_graphics")] = 'GraphicsSpec'
			CreateGraphicsSpec(srcPath, vehicleName, ModelNames, CoordinatesList, DummyHelperList, Transform, SubPart_ModelNames, SubPart_Info, use_Rotation, use_UniqueIDs)
	IDsList = RemoveDuplicatedIDs(IDsList)
	IDsList = RemoveUnderscoresIDs(IDsList)
	CreateIDsTable(srcPath, IDsList, "IDs_GR")
	#AT
	if BoneCoordsList != []:
		EditDeformationSpec(srcPath,vehicleName,skeletonName,EffectsDummyHelperList,BoneCoordsList,use_Damage)
		IDsListAT[StringToID(vehicleName + "deformationmodel")] = 'StreamedDeformationSpec'
	if len(DummyHelperList) != 0 and wheels == True:
		CreateVanm(srcPath, vehicleName, ModelNames, DummyHelperList, Transform[0])
		IDsListAT[StringToID(vehicleName + "_vanm")] = 'VehicleAnimation'
	if len(IDsListAT) != 0:
		MoveAttribsys(srcPath, vehicleName, skeletonName)
		IDsListAT[StringToID(vehicleName + "_attribsys")] = 'AttribSysVault'
		if BoneCoordsList == []:
			MoveDeformationSpec(srcPath, vehicleName)
			IDsListAT[StringToID(vehicleName + "deformationmodel")] = 'StreamedDeformationSpec'
		CreateIDsTable(srcPath, IDsListAT, "IDs_AT")
	CreateCommsToolList(srcPath,vehicleName)
	IDsListCD[StringToID(vehicleName)] = 'CommsToolList'
	if len(IDsListCD) != 0:
		CreateIDsTable(srcPath, IDsListCD, "IDs_CD")
	
	# Return objects to its original rotation
	if use_Rotation:
		_ = RotateAllObjects(angle=-270.0)
	
	elapsed_time = time.time() - start_time
	print("Elapsed time:",elapsed_time)
	return {'FINISHED'}
#1KaL2FbD3acn4
class ExportBurnoutParadise(Operator, ExportHelper):
	"""Export to Burnout Paradise Remastered (PC) or Burnout Paradise The Ultimate Box (PC) file format"""
	bl_idname = "export_bpr.dat"  # important since its how bpy.ops.import_test.some_data is constructed
	bl_label = "Export to folder"

	# ExportHelper mixin class uses this
	filename_ext = ""
	use_filter_folder = True
	
	vehicleName = StringProperty(name="Replaced vehicle name", description="Write the replaced vehicle abbreviated name", default="PUSMC01")
	#AT_path = StringProperty(name="Custom DeformationSpec path", description="Write the complete DeformationSpec path", default="", subtype="FILE_PATH")
	
	skeletonName = StringProperty(name="Base skeleton vehicle name", description="Write the skeleton name to use", default="")
	
	game_version = EnumProperty(
			name="Export to",
			description="Choose which format do you want to export to",
			items=(('BPR', "Burnout Paradise Remastered", "Export to Burnout Paradise Remastered format"),
					('BP', "Burnout Paradise TUB", "Export to Burnout Paradise The Ultimate Box format")),
			default='BPR',
			)
	
	if decodedIDsOption:
		verify_genericIDs = BoolProperty(
				name="Verify generic IDs",
				description="Check in order to verify if the meshes and textures are generics using the ResourceStringTable",
				default=False,
				)
	elif not decodedIDsOption:
		verify_genericIDs = False
	
	use_Rotation = BoolProperty(
            name="Use object rotation",
            description="Check in order to use the object rotations instead of applying it in the model. It is recommended just for BP models",
            default=False,
            )
	
	use_Accurate_split = BoolProperty(
            name="Use accurate UV split",
            description="Check in order to use a more accurate UV spliting for vertices with different UVs per loop. It is recommended just in case of issue on second UV layers or release mod version",
            default=False,
            )
	
	use_Damage = BoolProperty(
            name="Use damage",
            description="Check in order to use damage (experimental). If checked make sure to write on the Skeleton text box a name of a BP vehicle similar to the one being exported",
            default=True,
            )
	
	recalculate_bones = BoolProperty(
            name="Recalculate bones",
            description="Check in order to recalculate bones indices and weights. If checked it replaces any preexisting damage info of the model being exported. It is recommended if you are exporting a game vehicle to a vehicle that uses a totally different bones positions",
            default=False,
            )
	
	use_UniqueIDs = BoolProperty(
            name="Use unique IDs",
            description="Check in order to use unique IDs, avoing IDs conflict. Useful when doing finishes",
            default=False,
            )
	
	def execute(self, context):
		userpath = self.properties.filepath
		if(os.path.isdir(userpath)):
			msg = "Please select a directory not a file\n" + userpath
			self.report({'WARNING'}, msg)
		return main(context, self.filepath, self.vehicleName, self.skeletonName, self.verify_genericIDs, self.use_Rotation, self.use_Accurate_split, self.use_Damage, self.use_UniqueIDs, self.recalculate_bones, self.game_version)

# Only needed if you want to add into a dynamic menu (export menu)
def menu_func_export(self, context):
	self.layout.operator(ExportBurnoutParadise.bl_idname, text="Burnout Paradise (.dat)")

def register():
	bpy.utils.register_class(ExportBurnoutParadise)
	bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
	bpy.utils.unregister_class(ExportBurnoutParadise)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
	register()

    # test call
	bpy.ops.export_bpr.dat('INVOKE_DEFAULT')