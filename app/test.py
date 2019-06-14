# Test libraries
# This file is part of the opensoldering project distribution (https://github.com/swissembedded/opensolderingrobot.git).
# Copyright (c) 2019 by Daniel Haensse
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import data
import inspection
import robotcontrol
import mathfunc

# test mathfunction
x1,y1,x2,y2,x3,y3,x4,y4=mathfunc.rotate_rectangle(0, 0, 1, 2, 0.0)
if round(x1,1)==-0.5 and round(y1,1)==-1.0 and round(x2,1)==0.5 and round(y2,1)==-1.0 and round(x3,1)==0.5 and round(y3,1)==1.0 and round(x4,1)==-0.5 and round(y4,1)==1.0:
	print("ok rotate_rectangle")
else:
	print("nok rotate_rectangle", x1,y1,x2,y2,x3,y3,x4,y4)
x1,y1,x2,y2,x3,y3,x4,y4=mathfunc.rotate_rectangle(0, 0, 1, 2, 90.0)
if round(y1,1)==0.5 and round(x1,1)==-1.0 and round(y2,1)==-0.5 and round(x2,1)==-1.0 and round(y3,1)==-0.5 and round(x3,1)==1.0 and round(y4,1)==0.5 and round(x4,1)==1.0:
	print("ok rotate_rectangle 90")
else:
	print("nok rotate_rectangle 90", x1,y1,x2,y2,x3,y3,x4,y4)

# using folder tmp

# MENU PROJECT
# create a new project
prjdata=data.init_project_data()
# save it
data.write_project_data("temp/test", prjdata)
# load it again
prjdataload=data.read_project_data("temp/test")
if prjdata!=prjdataload:
	print("nok created and loaded data are different!")
	print("created data", prjdata)
	print("loaded data",prjdataload)
else:
	print("ok created and loaded data are identical!")

# MENU PROGRAM
# import pick and place file
inspection.load_pick_place(prjdata, "../testdata/Project Outputs for PCB_Project/Pick Place for testprint.txt")

# search for part by name
partsdefinition=prjdata['PartsDefinition']['PartsDefinition']
index=inspection.find_part_in_definition(partsdefinition, "PASSER-KREIS")
if index==0:
	print("ok search part")
else:
	print("nok search part")
# automatically assign the pick and place parts to partsdefinition entries.
inspection.assign_partsdefinition(prjdata)
unassiged=inspection.get_list_unassigned_parts(prjdata)
test=set({'61301421121', 'SOT23_L', '1870380000'})
if unassiged == test:
 	print("ok unassigned")
else:
	print("nok unassigned")

# get index of a part by designator
inspectionpath=prjdata['InspectionPath']
index=inspection.helper_get_index_by_designator(inspectionpath,"M1")
if index==6:
	print("ok get index by designator")
else:
	print("nok get index by designator")

# select reference points
inspection.set_reference_1(inspectionpath, 51.8160, 51.8160)
ref1index=inspection.get_reference_1(inspectionpath)

inspection.set_reference_2(inspectionpath, 98.2980, 68.1990 )
ref2index=inspection.get_reference_2(inspectionpath)
if ref1index==6 and ref2index==2:
	print("ok ref")
else:
	print("nok ref", refindex1,refindex2)

# marker bounding box
xb,yb,rotb,shapeb=inspection.get_bounding_box(partsdefinition, 0, "Body", 0, 0, 0, 0)
xm,ym,rotm, shapem=inspection.get_bounding_box(partsdefinition, 0, "Mask", 0, 0, 0, 0)

if [ xb, yb, rotb ] == [ 0.0, 1.1, 0.0] and [ xm, ym, rotm ]==[1.5, 0.0, 0.0]:
	print("ok body and mask")
else:
	print("not body and mask", xb, yb, rotb, xm, ym, rotm)

# panel
panel=[]
inspection.set_num_panel(panel, 5)
num=inspection.get_num_panel(panel)
if num==5:
	print("ok num panel")
else:
	print("nok num panel",num)

# teachin coordinates
ref1x=51.8160
ref1y=51.8160
inspection.set_panel_reference_1(panel,0,ref1x+10,ref1y+10)
x1,y1 = inspection.get_panel_reference_1(panel,0)
if x1 == ref1x+10 and y1 == ref1y+10:
	print("ok panel ref 1")
else:
	print("nok panel ref 1", x1, y1, z1)

ref2x=98.2980
ref2y=68.1990
inspection.set_panel_reference_2(panel,0,ref2x+10,ref2y+10)
x2,y2 = inspection.get_panel_reference_2(panel,0)
if x2 == 10+ref2x and y2 == 10+ref2y:
	print("ok panel ref 2")
else:
	print("nok panel ref 2", x2, y2)

# partsdefinition list for gui selection
list=inspection.get_list_part_definition(partsdefinition)
if len(list)==len(partsdefinition):
	print("ok parts definition list")
else:
	print("nok parts definition list", len(list), len(partsdefinition), partsdefinition)
# soldering profile first entry
firstdefinition=inspection.get_part_definition(partsdefinition,0)
if firstdefinition==partsdefinition[0]:
	print("ok parts definition")
else:
	print("nok parts definition")

# make array out of gcode
garray=robotcontrol.make_array("1\n2\n3\n")
if len(garray) == 3:
	print("ok gcode array")
else:
	print("nok gcode array")

# create g-code for home
#go_xyz(prjdata, x,y,z)
gcode=robotcontrol.go_xyz(prjdata, 1,2,3)
if "G1 X1 Y2 Z3" in gcode:
	print("ok go xyz")
else:
	print("nok goxyz", gcode)

#go_home(prjdata)
gcode=robotcontrol.go_home(prjdata)
if "G28" in gcode and "G90" in gcode:
	print("ok home")
else:
	print("nok home", gcode)

gcode=robotcontrol.strip_comment("G28; this is a comment")
if gcode=="G28":
	print("ok strip")
else:
	print("nok strip",gcode)

# create g-code for inspection
prjdata['Panel']=panel
gcode=robotcontrol.panel_inspection(prjdata, [0])
print("inspection", gcode)
