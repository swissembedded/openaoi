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
import math


# import pick and place file
def load_pick_place(data, file):
    # use the following columns Designator, Comment, Layer, Footprint, Center-X(mm), Center-Y(mm), Rotation, Description
    pp = pd.read_csv(
        file,
        skiprows=11,
        skip_blank_lines=True,
        skipinitialspace=True,
        delimiter=" ",
        quotechar='"',
        usecols=[
            "Designator",
            "Comment",
            "Layer",
            "Footprint",
            "Center-X(mm)",
            "Center-Y(mm)",
            "Rotation",
            "Description",
        ],
        dtype={
            "Designator": str,
            "Comment": str,
            "Layer": str,
            "Footprint": str,
            "Center-X(mm)": float,
            "Center-Y(mm)": float,
            "Rotation": float,
            "Description": str,
        },
    )

    if data["InspectionSide"] == "Top":
        token = "TopLayer"
    else:
        token = "BottomLayer"

    data["InspectionPath"] = []
    for index, row in pp.iterrows():
        if token == pp["Layer"][index]:
            data["InspectionPath"].append(
                {
                    "Designator": str(pp["Designator"][index]),
                    "Footprint": str(pp["Footprint"][index]),
                    "RefX": pp["Center-X(mm)"][index],
                    "RefY": pp["Center-Y(mm)"][index],
                    "Rotation": pp["Rotation"][index],
                    "Comment": str(pp["Comment"][index]),
                    "PanelRef1": False,
                    "PanelRef2": False,
                    "Partsdefinition": -1,
                    "InspectionPathSorting": -1,
                }
            )
    # print(data['InspectionPath'])


# return the index in partsdefinition for matching id
def find_part_in_definition(partsdefinition, name):
    for e, elem in enumerate(partsdefinition):
        if partsdefinition[e]["Id"] == name:
            return e
    return -1


def find_first_unassigned_part(inspectionpath):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]["Partsdefinition"] == -1:
            return e
    return -1


# assign a partsdefinition to all the known parts
def assign_partsdefinition(data):
    di = data["InspectionPath"]
    dd = data["PartsDefinition"]["PartsDefinition"]
    for e, elem in enumerate(di):
        if di[e]["Partsdefinition"] == -1:
            di[e]["Partsdefinition"] = find_part_in_definition(dd, di[e]["Footprint"])


# merge new and old partsdefinition
def merge_partsdefinition(newpd, oldpd):
    do = oldpd["PartsDefinition"]
    dn = newpd["PartsDefinition"]
    for e, elem in enumerate(do):
        if find_part_in_definition(dn, do[e]["Id"]) == -1:
            dn.append(do[e])


# get a list of unassigned parts
def get_list_unassigned_parts(data):
    unassigned = set()
    di = data["InspectionPath"]
    for e, elem in enumerate(di):
        if di[e]["Partsdefinition"] == -1:
            unassigned.add(di[e]["Footprint"])
    return unassigned


# helper get index by Designator
def helper_get_index_by_designator(inspectionpath, designator):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]["Designator"] == designator:
            return e
    return -1


# get the inspectionpath index by position
def helper_get_index_by_position(inspectionpath, x, y):
    nearestIndex = -1
    nearestDistance = -1
    for e, elem in enumerate(inspectionpath):
        tp = inspectionpath[e]
        posX = tp["RefX"]
        posY = tp["RefY"]
        distance = math.sqrt(math.pow(x - posX, 2.0) + math.pow(y - posY, 2.0))
        if nearestDistance == -1 or distance < nearestDistance:
            nearestIndex = e
            nearestDistance = distance
    return nearestIndex


# get reference point 1 index
def get_reference_1(inspectionpath):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]["PanelRef1"] == True:
            return e
    return -1


# set reference point 1 index
def set_reference_1(inspectionpath, x, y):
    oldref = get_reference_1(inspectionpath)
    if oldref != -1:
        inspectionpath[oldref]["PanelRef1"] = False
    index = helper_get_index_by_position(inspectionpath, x, y)
    print("index1", index)
    if index != -1:
        inspectionpath[index]["PanelRef1"] = True
        inspectionpath[index]["PanelRef2"] = False


# get reference point 2 index
def get_reference_2(inspectionpath):
    for e, elem in enumerate(inspectionpath):
        if inspectionpath[e]["PanelRef2"] == True:
            return e
    return -1


# set reference point 2 index
def set_reference_2(inspectionpath, x, y):
    oldref = get_reference_2(inspectionpath)
    if oldref != -1:
        inspectionpath[oldref]["PanelRef2"] = False
    index = helper_get_index_by_position(inspectionpath, x, y)
    print("index2", index)
    if index != -1:
        inspectionpath[index]["PanelRef1"] = False
        inspectionpath[index]["PanelRef2"] = True


# set the number of panel
def set_num_panel(panel, num):
    while len(panel) < num:
        panel.append(
            {
                "RefX1": -1,
                "RefY1": -1,
                "RefZ1": -1,
                "RefX2": -1,
                "RefY2": -1,
                "RefZ2": -1,
            }
        )


# get the number of panel
def get_num_panel(panel):
    return len(panel)


# get panel reference point 1
def get_panel_reference_1(panel, index):
    return panel[index]["RefX1"], panel[index]["RefY1"]


# set reference point 1
def set_panel_reference_1(panel, index, x, y):
    panel[index]["RefX1"] = x
    panel[index]["RefY1"] = y


# get panel reference point 2
def get_panel_reference_2(panel, index):
    return panel[index]["RefX2"], panel[index]["RefY2"]


# set reference point 2
def set_panel_reference_2(panel, index, x, y):
    panel[index]["RefX2"] = x
    panel[index]["RefY2"] = y


# get list of part definitions
def get_list_part_definition(partsdefinition):
    parts = []
    for p, elem in enumerate(partsdefinition):
        parts.append(partsdefinition[p]["Id"])
    return parts


# get item of part definition
def get_part_definition(partsdefinition, index):
    return partsdefinition[index]


# calculate the bounding rectangle/round in pick & place coordinates
def get_bounding_box(partsdefinition, index, tp, x, y, rotation, orientation):
    if tp == "Body":
        dim = partsdefinition[index]["BodySize"]
        shape = partsdefinition[index]["BodyShape"]
    elif tp == "Mask":
        dim = partsdefinition[index]["MaskSize"]
        shape = partsdefinition[index]["MaskShape"]
    rotation -= partsdefinition[index]["Rotation"]
    if shape == "Rectangular":
        if orientation == 0:
            # top left
            cx = dim[0] / 2.0
            cy = dim[1] / 2.0
        elif orientation == 1:
            # top right
            cx = -dim[0] / 2.0
            cy = dim[1] / 2.0
        elif orientation == 2:
            # bottom right
            cx = dim[0] / 2.0
            cy = -dim[1] / 2.0
        elif orientation == 3:
            # bottom left
            cx = -dim[0] / 2.0
            cy = -dim[1] / 2.0
        px = x + math.cos(rotation / 360.0 * 2.0 * math.pi) * cx
        py = y + math.sin(rotation / 360.0 * 2.0 * math.pi) * cy
        return px, py, rotation, shape
    elif shape == "Circular":
        if orientation == 0:
            # top
            cx = 0
            cy = dim[1] / 2.0
        elif orientation == 1:
            # right
            cx = dim[0] / 2.0
            cy = 0
        elif orientation == 2:
            # bottom
            cx = 0
            cy = -dim[1] / 2.0
        elif orientation == 3:
            # left
            cx = -dim[0] / 2.0
            cy = 0
        px = x + cx
        py = y + cy
        return px, py, rotation, shape
    return 0.0, 0.0, 0.0, "Invalid"


# Get pp tool area
def get_pp_tool_area(data):
    xmin = 0
    xmax = 0
    ymin = 0
    ymax = 0
    inspectionpath = data["InspectionPath"]
    partsdefinition = data["PartsDefinition"]["PartsDefinition"]
    for e, elem in enumerate(inspectionpath):
        tp = inspectionpath[e]
        refx = tp["RefX"]
        refy = tp["RefY"]
        xemin = refx
        xemax = refx
        yemin = refy
        yemax = refy
        rotation = tp["Rotation"]
        footprint = tp["Footprint"]
        index = find_part_in_definition(partsdefinition, footprint)
        if index != -1:
            for orientation in range(0, 4):
                xp, yp, rot, shape = get_bounding_box(
                    partsdefinition, index, "Body", refx, refy, rotation, orientation
                )
                xemin = min(xemin, xp)
                xemax = max(xemax, xp)
                yemin = min(yemin, yp)
                yemax = max(yemax, yp)
                xp, yp, rot, shape = get_bounding_box(
                    partsdefinition, index, "Mask", refx, refy, rotation, orientation
                )
                xemin = min(xemin, xp)
                xemax = max(xemax, xp)
                yemin = min(yemin, yp)
                yemax = max(yemax, yp)
        if e == 0 or xemin < xmin:
            xmin = xemin
        if e == 0 or xemax > xmax:
            xmax = xemax
        if e == 0 or yemin < ymin:
            ymin = yemin
        if e == 0 or yemax > ymax:
            ymax = yemax
    return xmin, xmax, ymin, ymax


# Get pp position from click
def get_pixel_position(data, x, y, w, h):
    xmin, xmax, ymin, ymax = get_pp_tool_area(data)
    xt = (x - xmin) / (xmax - xmin) * w
    yt = (y - ymin) / (ymax - ymin) * h
    return xt, yt


# Get soldering position from click
def get_pp_position(data, x, y, w, h):
    xmin, xmax, ymin, ymax = get_pp_tool_area(data)
    xt = (x / w * (xmax - xmin)) + xmin
    yt = (y / h * (ymax - ymin)) + ymin
    return xt, yt


# create identifier for captures
def create_part_identifier(
    station,
    timestamp,
    panel,
    designator,
    footprint,
    angle,
    polarity,
    bodyShape,
    bodySize,
    maskShape,
    maskSize,
):
    identifier = "[" + station + "]_[" + str(int(round(timestamp * 1000)))
    identifier += "]_[" + designator + "]_[" + footprint + "]_[" + str(angle)
    identifier += (
        "]_["
        + str(polarity)
        + "]_"
        + bodyShape
        + "["
        + str(bodySize[0])
        + "_"
        + str(bodySize[1])
        + "]_"
        + maskShape
        + "["
        + str(maskSize[0])
        + "_"
        + str(maskSize[1])
        + "]"
    )
    return identifier


# return the number of soldering points that are not optimized yet
def helper_get_number_of_unsorted(inspectionpath):
    num = 0
    for e, elem in enumerate(inspectionpath):
        tp = soldertoolpath[e]
        if tp["InspectionPathSorting"] == -1 and tp["Partsdefinition"] != -1:
            num += 1
    return num


# sort the inspectionpath
def get_sorted_inspectionpath(inspectionpath):
    neighbourX = 0
    neighbourY = 0
    hasFirst = False
    hasSecond = False
    for e, elem in enumerate(inspectionpath):
        tp = soldertoolpath[e]
        if tp["PanelRef1"] == True:
            tp["InspectionPathSorting"] = 0
            hasFirst = True
        elif tp["PanelRef2"] == True:
            tp["InspectionPathSorting"] = 1
            neighbourX = tp["RefX"]
            neighbourY = tp["RefY"]
            hasSecond = True
        else:
            tp["InspectionPathSorting"] = -1
    if hasFirst == False:
        print("warning no first reference point available")
        return 0
    if hasSecond == False:
        print("warning no second reference point available")
        return 0

    # sorting against neighbour
    sortingIndex = 2
    while helper_get_number_of_unsorted() > 0:
        nearestIndex = -1
        nearestDistance = -1.0
        for e, elem in enumerate(inspectionpath):
            tp = soldertoolpath[e]
            if tp["InspectionPathSorting"] == -1 and tp["Partsdefinition"] != -1:
                posX = tp["RefX"]
                posY = tp["RefY"]
                distance = abs(neighbourX - posX) + abs(neighbourY - posY)
                if nearestDistance == -1 or nearestDistance > distance:
                    nearestIndex = e
                    nearestDistance = distance
        # choose the best
        if nearestDistance != -1.0:
            soldertoolpath[nearestIndex]["InspectionPathSorting"] = sortingIndex
            neighbourX = inspectionpath[nearestIndex]["RefX"]
            neighbourY = inspectionpath[nearestIndex]["RefY"]
            # print(sortingIndex,soldertoolpath[nearestIndex])
            sortingIndex += 1


# get inspection point by index
def get_inspectionpoint(inspectionpath, index):
    for e, elem in enumerate(inspectionpath):
        if soldertoolpath[e]["InspectionPathSorting"] == index:
            return e
    return -1


# get number of inspectionpoints
def get_number_inspectionpoints(inspectionpath):
    num = -1
    for e, elem in enumerate(inspectionpath):
        sort = inspectionpath[e]["InspectionPathSorting"]
        if sort > num:
            num = sort
    return num + 1
