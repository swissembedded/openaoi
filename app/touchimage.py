from kivy.graphics import Color, Rectangle, Line, Triangle, Ellipse, Rotate
from kivy.uix.image import Image

import inspection
import mathfunc

class TouchImage(Image):
    def set_cad_view(self, prjdata):
        ### make project data available in class
        self.project_data=prjdata

    def redraw_cad_view(self):
        partsdefinition=self.project_data['PartsDefinition']['PartsDefinition']
        inspectionside=self.project_data['InspectionSide']
        inspectionpath=self.project_data['InspectionPath']
        xmin, xmax, ymin, ymax=inspection.get_pp_tool_area(self.project_data)
        #print("draw", xmin, xmax, ymin, ymax)
        posxp, posyp=self.pos
        widthp, heightp = self.size
        width=xmax-xmin
        height=ymax-ymin
        if width==0 or height==0:
            return

        self.canvas.after.clear()
        with self.canvas.after:
                Color(0/255,0/255,0/255)
                Rectangle(pos=(posxp, posyp), size=(widthp, heightp))
                posxp=posxp+widthp*0.01
                posyp=posyp+heightp*0.01
                widthp*=0.98
                heightp*=0.98
                scale=min(widthp / width, heightp / height)
                for e, elem in enumerate(inspectionpath):
                    tp=inspectionpath[e]
                    refx=tp['RefX']
                    refy=tp['RefY']
                    ref1=tp['PanelRef1']
                    ref2=tp['PanelRef2']
                    footprint=tp['Footprint']
                    rotationp=tp['Rotation']
                    xp, yp=inspection.get_pixel_position(self.project_data,refx,refy,width*scale,height*scale)
                    index=inspection.find_part_in_definition(partsdefinition, footprint)
                    print("ip",refx,refy,ref1,ref2,footprint, rotationp, index)
                    if ref1:
                        Color(255/255, 0/255, 0/255)
                    elif ref2:
                        Color(0/255, 0/255, 255/255)
                    elif index!=-1:
                        Color(128/255, 255/255, 128/255)
                    else:
                        Color(255/255, 165/255, 0/255)
                    if index != -1:
                        part=inspection.get_part_definition(partsdefinition, index)
                        print("part",part)
                        if part['BodyShape']=="Circular":
                            if inspectionside=="Top":
                                Ellipse(pos=(xp+posxp, yp+posyp), size=(part['BodySize'][0]*scale, part['BodySize'][1]*scale))
                            else:
                                Ellipse(pos=(widthp-xp+posxp, yp+posyp), size=(part['BodySize'][0]*scale, part['BodySize'][1]*scale))
                        elif part['BodyShape']=="Rectangular":
                            if inspectionside=="Top":
                                x = xp + posxp
                                y = yp + posyp
                                cx = part['BodySize'][0] * scale
                                cy = part['BodySize'][1] * scale
                                alpa = part['Rotation'] - rotationp
                            else:
                                x = widthp-xp+posxp
                                y = yp + posyp
                                cx = part['BodySize'][0] * scale
                                cy = part['BodySize'][1] * scale
                                alpa = rotationp - part['Rotation']

                            x1,y1,x2,y2,x3,y3,x4,y4 = mathfunc.rotate_rectangle(x,y,cx,cy,alpa)
                            Triangle(points=[x1,y1,x2,y2,x3,y3])
                            Triangle(points=[x1,y1,x3,y3,x4,y4])

                    else:
                            if inspectionside=="Top":
                                Ellipse(pos=(xp+posxp, yp+posyp), size=(5,5))
                            else:
                                Ellipse(pos=(widthp-xp+posxp, yp+posyp), size=(5,5))


    def on_touch_down(self, touch):
        ### mouse down event
        return

        inspectionpath=self.project_data['InspectionPath']
        inspectionside=self.project_data['InspectionSide']
        mode=self.project_data['CADMode']
        posxp, posyp=self.pos
        widthp, heightp = self.size
        xmin, xmax, ymin, ymax=inspection.get_pp_tool_area(self.project_data)
        width=xmax-xmin
        height=ymax-ymin

        if width==0 or height==0:
            return

        # calculate click position
        posxp=posxp+widthp*0.01
        posyp=posyp+heightp*0.01

        # scaling
        widthp*=0.98
        heightp*=0.98
        scale=min(widthp / width, heightp / height)

        touchxp, touchyp=touch.pos

        if inspectionside=="Top":
            touchxp=touchxp-posxp
            touchyp=touchyp-posyp
        else:
            touchxp=widthp-(touchxp-posxp)
            touchyp=touchyp-posyp

        xs, ys = inspection.get_pp_position(self.project_data, touchxp,touchyp,width*scale,height*scale)
        # out of image
        #print("pos:", touch.pos, self.pos, self.size, posxp, posyp, "xs ", xs, "ys ", ys, xmin, xmax, ymin, ymax)

        if xs < xmin or xs > xmax or ys < ymin or ys > ymax:
            return
        # perform action on mode
        if mode=="Select":
            #excellon.select_by_position(soldertoolpath, xnc, ync, selectedsolderingprofile)
            return
        elif mode=="Deselect":
            #excellon.deselect_by_position(soldertoolpath, xnc, ync)
            return
        elif mode=="Ref1":
            inspection.set_reference_1(inspectionpath, xs, ys)
        elif mode=="Ref2":
            inspection.set_reference_2(inspectionpath, xs, ys)
        self.redraw_cad_view()
        return
