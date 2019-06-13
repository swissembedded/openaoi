import math

def rotate_point(x, y, center_x, center_y, alpa):
    alpa_radian = math.pi * alpa / 180
    rot_x = (x - center_x) * math.cos(alpa_radian) + (y-center_y) * math.sin(alpa_radian) + center_x
    rot_y = (y-center_y) * math.cos(alpa_radian) - (x-center_x) * math.sin(alpa_radian) + center_y

    return rot_x, rot_y

def rotate_rectangle(x, y, cx, cy, alpa):
    center_x = x + cx * 0.5
    center_y = y + cy * 0.5

    x1,y1 = rotate_point(x, y, center_x, center_y, alpa)
    x2,y2 = rotate_point(x+cx, y, center_x, center_y, alpa)
    x3,y3 = rotate_point(x+cx, y+cy, center_x, center_y, alpa)
    x4,y4 = rotate_point(x, y+cy, center_x, center_y, alpa)

    return x1,y1,x2,y2,x3,y3,x4,y4




