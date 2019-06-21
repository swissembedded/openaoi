# G-Code template handling
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

# some usefull info can be found here
# https://reprap.org/wiki/G-code

# Fill in parameters into template g-code
import string
import math
import numpy
from numpy import array, dot, clip, subtract, arcsin, arccos
from numpy.linalg import norm
import inspection


def complete_template(template, parameters):
    gcode = template
    for key, value in parameters.items():
        token = "%" + key
        gcode = gcode.replace(token, str(value))
    return gcode


# coordinate transformation
def get_printer_point(point, radians, scale, origin=(0, 0), translation=(0, 0)):
    ### get printer point from nc drill coordinates
    x, y = point
    ox, oy = origin
    tx, ty = translation
    qx = tx + (math.cos(radians) * (x - ox) + math.sin(radians) * (y - oy)) * scale
    qy = ty + (-math.sin(radians) * (x - ox) + math.cos(radians) * (y - oy)) * scale
    return qx, qy


def panel_inspection(data, panelSelection):
    capture = []
    # header
    zp = data["Setup"]["CameraParameters"]["FocusZ"]
    br = data["Setup"]["CameraParameters"]["IlluminationPWM"]
    parameters = {"FocusZ": round(data["Setup"]["CameraParameters"]["FocusZ"], 2)}
    gcode = complete_template(data["GHeader"], parameters)
    # soldering backside?
    if data["InspectionSide"] == "Top":
        flip = 1
    else:
        flip = -1

    inspectionpath = data["InspectionPath"]
    inspection.get_sorted_inspectionpath(inspectionpath)

    # for each selected panel soldering
    for p, elem in enumerate(panelSelection):
        panel = data["Panel"][panelSelection[p]]
        # get panel data
        # teached panel coordinates
        # TODO add correction based on marker here
        xp1 = panel["RefX1"]
        yp1 = panel["RefY1"]
        xp2 = panel["RefX2"]
        yp2 = panel["RefY2"]
        if xp1 == -1 or xp2 == -1 or yp1 == -1 or yp2 == -1:
            print("error missing reference, skipping panel", p)
            continue
        # solder toolpath
        refNum1 = inspection.get_reference_1(inspectionpath)
        ref1 = inspectionpath[refNum1]
        xi1 = ref1["RefX"]
        yi1 = ref1["RefY"]
        refNum2 = inspection.get_reference_2(inspectionpath)
        ref2 = inspectionpath[refNum2]
        xi2 = ref2["RefX"]
        yi2 = ref2["RefY"]
        # print(xi1,yi1,xi2,yi2)
        # calculate transformation
        vp1 = array([xp1, yp1])
        vi1 = array([xi1, yi1])
        vp2 = array([xp2, yp2])
        vi2 = array([xi2, yi2])
        dvp = subtract(vp2, vp1)
        dvi = subtract(vi2, vi1)
        vplen = norm(dvp)
        vilen = norm(dvi)
        c = numpy.dot(dvp, dvi) / (vplen * vilen)
        # some numerical issues
        if c > 1.0:
            c = 1.0
        elif c < -1.0:
            c = -1.0
        radians = numpy.arccos(c)
        scale = vplen / vilen
        # print(vp1, vi1, vp2, vi2, dvp, dvi, vplen, vilen, c, scale, radians)
        # iterate over each capturing position
        for e in range(0, inspection.get_number_inspectionpoints(inspectionpath)):
            ip = inspection.get_inspectionpoint(inspectionpath, e)
            ipindex = data["InspectionPath"][ip]["Partsdefinition"]
            if ipindex == -1:
                continue
            pd = data["PartsDefinition"]["PartsDefinition"][ipindex]
            xi = data["InspectionPath"][ip]["RefX"] * flip
            yi = data["InspectionPath"][ip]["RefY"]
            vi = array([xi, yi])
            xp, yp = get_printer_point(vi, -radians, scale, vi1, vp1)
            # create parameterlist
            gpos = inspect_xyz(data, xp, yp, zp, br, xp, yp, panelSelection[p], ip)
            gcode += gpos
        gcode += complete_template(data["GFooter"], {})
        return gcode


def inspect_xyz(data, x, y, z, brigthness, centerx, centery, panel, partref):
    parameters = {
        "Brightness": round(brigthness, 2),
        "PosX": round(x, 2),
        "PosY": round(y, 2),
        "PosZ": round(z, 2),
        "CenterX": round(centerx, 2),
        "CenterY": round(centery, 2),
        "Panel": panel,
        "PartRef": partref,
    }
    gcode = complete_template(data["GInspect"], parameters)
    return gcode


# parse g-code capture command
def parse_capture_command(command):
    # CAPTURE %Panel %PartRef %CenterX %CenterY %PosX %PosY %PosZ %Brightness
    commandlist = command.split(" ")
    panel = int(commandlist[1])
    partref = commandlist[2]
    centerX = float(commandlist[3])
    centerY = float(commandlist[4])
    posX = float(commandlist[5])
    posY = float(commandlist[6])
    posZ = float(commandlist[7])
    brightness = float(commandlist[8])
    return panel, partref, centerX, centerY, posX, posY, posZ, brigthness


def go_xyz(data, x, y, z):
    parameters = {"CoordX": round(x, 2), "CoordY": round(y, 2), "CoordZ": round(z, 2)}
    gcode = complete_template(data["GGo"], parameters)
    return gcode


def go_home(data):
    gcode = complete_template(data["GHome"], {})
    return gcode


# strip off the command before sending to printer
def strip_comment(gcode):
    line = gcode.split(";")[0]
    return line.strip()


# convert gcode into an array of single commands
def make_array(gcode):
    splitted = gcode.splitlines()
    stripped = []
    for line, elem in enumerate(splitted):
        stripped.append(strip_comment(splitted[line]))
    return stripped
