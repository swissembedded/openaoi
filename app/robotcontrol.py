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
from numpy import (array, dot, clip, subtract, arcsin, arccos)
from numpy.linalg import norm
import inspection



def complete_template(template, parameters):
    gcode=template
    for key,value in parameters.items():
        token="%"+key
        gcode=gcode.replace(token,str(value))
    return gcode

# coordinate transformation
def get_printer_point(point, radians, scale, origin=(0, 0), translation=(0,0)):
    ### get printer point from nc drill coordinates
    x, y = point
    ox, oy = origin
    tx, ty = translation
    qx = tx + (math.cos(radians) * (x - ox) + math.sin(radians) * (y - oy))*scale
    qy = ty + (-math.sin(radians) * (x - ox) + math.cos(radians) * (y - oy))*scale
    return qx, qy

def panel_inspection(data, panelSelection):
    # header
    zp=data['Setup']['CameraParameters']['FocusZ']
    br=data['Setup']['CameraParameters']['IlluminationPWM']
    parameters={ "FocusZ" : round(data['Setup']['CameraParameters']['FocusZ'],2) }
    gcode = complete_template(data['GHeader'],parameters)
    # soldering backside?
    if data['InspectionSide']=="Top":
        flip=1
    else:
        flip=-1
    # for each selected panel soldering
    for p, elem in enumerate(panelSelection):
        panel=data['Panel'][panelSelection[p]]
        # get panel data
        # teached panel coordinates
        # TODO add correction based on marker here
        xp1=panel['RefX1']
        yp1=panel['RefY1']
        xp2=panel['RefX2']
        yp2=panel['RefY2']
        if xp1==-1 or xp2==-1 or yp1==-1 or yp2==-1:
            print("error missing reference, skipping panel",p)
            continue
        # solder toolpath
        inspectionpath=data['InspectionPath']
        refNum1=inspection.get_reference_1(inspectionpath)
        ref1=inspectionpath[refNum1]
        xi1=ref1['RefX']
        yi1=ref1['RefY']
        refNum2=inspection.get_reference_2(inspectionpath)
        ref2=inspectionpath[refNum2]
        xi2=ref2['RefX']
        yi2=ref2['RefY']
        #print(xi1,yi1,xi2,yi2)
        # calculate transformation
        vp1=array([xp1,yp1])
        vi1=array([xi1,yi1])
        vp2=array([xp2,yp2])
        vi2=array([xi2,yi2])
        dvp=subtract(vp2,vp1)
        dvi=subtract(vi2,vi1)
        vplen=norm(dvp)
        vilen=norm(dvi)
        c = numpy.dot(dvp,dvi)/(vplen*vilen)
        # some numerical issues
        if c > 1.0:
            c=1.0
        elif c<-1.0:
            c=-1.0
        radians = numpy.arccos(c)
        scale = vplen / vilen
        #print(vp1, vi1, vp2, vi2, dvp, dvi, vplen, vilen, c, scale, radians)
        # iterate over each capturing position
        for e, elem in enumerate(inspectionpath):
            ip=inspectionpath[e]
            ipindex=ip['Partsdefinition']
            if ipindex==-1:
                continue
            pd=data['PartsDefinition']['PartsDefinition'][ipindex]
            xi=ip['RefX']*flip
            yi=ip['RefY']
            vi=array([xi, yi])
            xp, yp = get_printer_point(vi, -radians, scale, vi1, vp1)
            # create parameterlist
            parameters={
                    "Brightness" : round(br,2),
                    "PosX" : round(xp,2),
                    "PosY" : round(yp,2),
                    "PosZ" : round(zp,2)}
            gpos = complete_template(data['GInspect'], parameters)
            gcode+=gpos
            gcode+=";CAPTURE_Footprint-"+ip['Footprint']+"_Rotation-"+str(ip['Rotation'])+"_Designator-"+ip['Designator']+"\n"
        gcode += complete_template(data['GFooter'], {})
        return gcode

def go_xyz(data, x,y,z):
    parameters = {
        "CoordX": round(x,2),
        "CoordY" : round(y,2),
        "CoordZ" : round(z,2) }
    gcode = complete_template(data['GGo'], parameters)
    return gcode

def go_home(data):
    gcode = complete_template(data['GHome'], {})
    return gcode

# convert gcode into an array of single commands
def make_array(gcode):
    return gcode.splitlines()

# strip off the command before sending to printer
def strip_comment(gcode):
    return gcode.split(';')[0]
