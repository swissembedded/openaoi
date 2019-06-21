# Math
# This file is part of the opensoldering project distribution (https://github.com/swissembedded/opensolderingrobot.git).
# Copyright (c) 2019 by Ming
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

import math

#   rotation transformation matrix
#
#   | rot_x |   |  cos(alpa),  sin(alpa) |   | x |   | center_x |
#   |       | = |                        | x |   | + |          |
#   | rot_y |   | -sin(alpa),  cos(alpa) |   | y |   | center_y |
#

def rotate_point(x, y, center_x, center_y, alpha):
    alpha_radian = math.pi * alpha / 180.0
    rot_x = (x - center_x) * math.cos(alpha_radian) + (y - center_y) * math.sin(alpha_radian) + center_x
    rot_y = -(x - center_x) * math.sin(alpha_radian) + (y - center_y) * math.cos(alpha_radian) + center_y

    return rot_x, rot_y

def rotate_rectangle(x, y, cx, cy, alpha):
    cxhalf = cx * 0.5
    cyhalf = cy * 0.5

    # 1: bottom left, 2: bottom right, 3: top right, 4: top left
    x1,y1 = rotate_point(x-cxhalf, y-cyhalf, x, y, alpha)
    x2,y2 = rotate_point(x+cxhalf, y-cyhalf, x, y, alpha)
    x3,y3 = rotate_point(x+cxhalf, y+cyhalf, x, y, alpha)
    x4,y4 = rotate_point(x-cxhalf, y+cyhalf, x, y, alpha)

    return x1,y1,x2,y2,x3,y3,x4,y4

def rotate_polarity(x,y,cx,cy, alpha):
    cxhalf = cx * 0.5
    cyhalf = cy * 0.5

    xr,yr = rotate_point(x-cxhalf, y+cyhalf, x, y, alpha)
    return xr, yr
