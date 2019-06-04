# Gerber / Excellon handling
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

import pandas as pd
import numpy

# import pick and place file
def load_pick_place(data, file):
    # use the following columns Designator, Comment, Layer, Footprint, Center-X(mm), Center-Y(mm), Rotation, Description
    pp=pd.read_csv(file, skiprows=11, skip_blank_lines=True, skipinitialspace=True, delimiter=' ', quotechar='\"', usecols=['Designator', 'Comment', 'Layer','Footprint','Center-X(mm)','Center-Y(mm)', 'Rotation', 'Description'], dtype={'Designator':str, 'Comment':str, 'Layer':str,'Footprint':str,'Center-X(mm)':float,'Center-Y(mm)':float, 'Rotation':float, 'Description':str})

    if data['InspectionSide']=="Top":
        token="TopLayer"
    else:
        token="BottomLayer"

    data['InspectionPath']=[]
    for index,row in pp.iterrows():
        if token==pp['Layer'][index]:
            data['InspectionPath'].append({
                "Designator" : str(pp['Designator'][index]),
                "Footprint": str(pp['Footprint'][index]),
                "RefX": pp['Center-X(mm)'][index],
                "RefY": pp['Center-Y(mm)'][index],
                "Rotation":pp['Rotation'][index],
                "Comment":str(pp['Comment'][index]),
                "PanelRef1":False,
                "PanelRef2": False,
                "Partsdefinition": -1 })
    #print(data['InspectionPath'])

# return the index in partsdefinition for matching id
def find_part_in_definition(partsdefinition, name):
    for e, elem in enumerate(partsdefinition):
        if partsdefinition[e]['Id']==name:
            return e
    return -1

# assign a partsdefinition to all the known parts
def assign_partsdefinition(data):
    di=data['InspectionPath']
    dd=data['PartsDefinition']['PartsDefinition']
    for e, elem in enumerate(di):
        if di[e]['Partsdefinition']==-1:
            di[e]['Partsdefinition']=find_part_in_definition(dd,di[e]['Footprint'])

# get a list of unassigned parts
def get_list_unassigned_parts(data):
    unassigned=set()
    di=data['InspectionPath']
    for e, elem in enumerate(di):
        if di[e]['Partsdefinition']==-1:
            unassigned.add(di[e]['Footprint'])
    return unassigned

# helper get index by Designator
def helper_get_index_by_designator(inspectionpath,designator):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]['Designator'] == designator:
            return e
    return -1


# get reference point 1 index
def get_reference_1(inspectionpath):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]['PanelRef1'] == True:
            return e
    return -1

# set reference point 1 index
def set_reference_1(inspectionpath,designator):
    oldref=get_reference_1(inspectionpath)
    if oldref !=-1:
        inspectionpath[e]['PanelRef1']=False
    index=helper_get_index_by_designator(inspectionpath, designator)
    if index!=-1:
        inspectionpath[index]['PanelRef1']=True
        inspectionpath[index]['PanelRef2']=False

# get reference point 2 index
def get_reference_2(inspectionpath):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]['PanelRef2'] == True:
            return e
    return -1

# set reference point 2 index
def set_reference_2(inspectionpath,designator):
    oldref=get_reference_2(inspectionpath)
    if oldref !=-1:
        inspectionpath[e]['PanelRef2']=False
    index=helper_get_index_by_designator(inspectionpath,designator)
    if index!=-1:
        inspectionpath[index]['PanelRef1']=False
        inspectionpath[index]['PanelRef2']=True

# set the number of panel
def set_num_panel(panel, num):
    while len(panel)<num:
        panel.append({"RefX1" : -1, "RefY1":-1, "RefZ1":-1, "RefX2":-1, "RefY2":-1, "RefZ2":-1})

# get the number of panel
def get_num_panel(panel):
    return len(panel)

# get panel reference point 1
def get_panel_reference_1(panel,index):
    return panel[index]['RefX1'], panel[index]['RefY1']

# set reference point 1
def set_panel_reference_1(panel,index,x,y):
    panel[index]['RefX1']=x
    panel[index]['RefY1']=y

# get panel reference point 2
def get_panel_reference_2(panel,index):
    return panel[index]['RefX2'], panel[index]['RefY2']

# set reference point 2
def set_panel_reference_2(panel,index,x,y):
    panel[index]['RefX2']=x
    panel[index]['RefY2']=y

# get list of part definitions
def get_list_part_definition(partsdefinition):
    parts=[]
    for p, elem in enumerate(partsdefinition):
        parts.append(partsdefinition[p]['Id'])
    return parts

# get item of part definition
def get_part_definition(partsdefinition, index):
    return partsdefinition[index]

# calculate the bounding rectangle in pick & place coordinates
def get_bounding_rectangle(partsdefinition, index, tp, x, y, rotation, orientation):
    if tp=='Body':
        dim=partsdefinition[index]['BodySize']
        shape=partsdefinition[index]['BodyShape']
    elif tp=='Mask':
        dim=partsdefinition[index]['MaskSize']
        shape=partsdefinition[index]['MaskShape']
    rotation -= partsdefinition[index]['Rotation']
    if shape=="Rectangular":
        if orientation==0:
            # top left
            cx=dim[0]/2.0
            cy=dim[1]/2.0
        elif orientation==1:
            # top right
            cx=-dim[0]/2.0
            cy=dim[1]/2.0
        elif orientation==2:
            # bottom right
            cx=dim[0]/2.0
            cy=-dim[1]/2.0
        elif orientation==3:
            # bottom left
            cx=-dim[0]/2.0
            cy=-dim[1]/2.0
        px=x+numpy.cos(rotation/360.0*2.0*numpy.pi)*cx
        py=y+numpy.sin(rotation/360.0*2.0*numpy.pi)*cy
        return px, py, rotation
    elif shape=="Circular":
        if orientation==0:
            # top
            cx=0
            cy=dim[1]/2.0
        elif orientation==1:
            # right
            cx=dim[0]/2.0
            cy=0
        elif orientation==2:
            # bottom
            cx=0
            cy=-dim[1]/2.0
        elif orientation==3:
            # left
            cx=-dim[0]/2.0
            cy=0
        px=x+cx
        py=y+cy
        return px, py, rotation
