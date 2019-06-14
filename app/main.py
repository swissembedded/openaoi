# Main routine
# This file is part of the opensoldering project distribution (https://github.com/swissembedded/opensolderingrobot.git).
# Copyright (c) 2019 by Susanna
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

import time
import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.popup import Popup
# list view for soldering profile
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton, ListView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from kivy.graphics import Color, Rectangle, Line, Triangle, Ellipse, Rotate
from kivy.graphics.texture import Texture
# set the initial size
from kivy.config import Config

import os
import requests
import math
import io

# for camera view
import cv2
import imutils
from videocaptureasync import VideoCaptureAsync

import json
from PIL import Image as pil_image
try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO
#to send a file of gcode to the printer
from printrun.printcore import printcore
from printrun import gcoder

import data
import inspection
import robotcontrol

import numpy as np
import touchimage



MAX_SIZE = (1280, 768)
Config.set('graphics', 'width', MAX_SIZE[0])
Config.set('graphics', 'height', MAX_SIZE[1])
Config.set('graphics', 'resizable', False)

#############################
screen = {"screen":"main"}
real_img_size = {}
bound_box = {}
hit_info = []
sel_hit_info = []
sel_draw_hit_info = []
sel_last_hit_info = {"last":"","first":"","second":""}

def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)
assure_path_exists("temp/")

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
class ImportDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
class ListPopup(BoxLayout):
    pass
class EditPopup(BoxLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
class ControlPopup(BoxLayout):
    controlXYZ = ObjectProperty(None)
    get_panel_ref1 = ObjectProperty(None)
    set_panel_ref1 = ObjectProperty(None)
    get_panel_ref2 = ObjectProperty(None)
    set_panel_ref2 = ObjectProperty(None)
    teachin_reference  = ObjectProperty(None)
    cancel = ObjectProperty(None)
class TeachinPopup(BoxLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
class ErrorDialog(Popup):
    def __init__(self, obj, **kwargs):
        super(ErrorDialog, self).__init__(**kwargs)
        self.obj = obj
class ScreenManagement(ScreenManager):
    pass

### this is the main screen
class ListScreen(Screen):
    def __init__(self, **kwargs):
        super(ListScreen, self).__init__(**kwargs)
        # run clock
        Clock.schedule_interval(self.init_gui, 0.2)
        Clock.schedule_interval(self.show_status, 0.03)

    def init_gui(self, dt):
        self.new_file()
        Clock.unschedule(self.init_gui)
        Clock.schedule_interval(self.cam_update, 0.03)

    def cam_capture_video(self, frame, path, scalex, scaley, footprint, designator, angle, polarity, bodyShape, bodySize, maskShape, maskSize):
        frame2=frame.copy()
        rotated=imutils.rotate(frame, int(angle))
        # create a mask image of the same shape as input image, filled with 0s (black color)
        mask = np.zeros_like(rotated)
        if maskShape == "Rectangular":
            # create a white filled ellipse
            center = (rotated.shape[1]*0.5, rotated.shape[0]*0.5)
            bottomleft = (int(center[0]-maskSize[0]*scalex*0.5), int(center[1]-maskSize[1]*scaley*0.5))
            topright = (int(center[0]+maskSize[0]*scalex*0.5), int(center[1]+maskSize[1]*scaley*0.5))
            maskMask=cv2.rectangle(mask, bottomleft, topright, (255,255,255), -1)
        elif maskShape == "Circular":
            # create a white filled ellipse
            center = (int(rotated.shape[1]*0.5), int(rotated.shape[0]*0.5))
            axis = (int(maskSize[0]*scalex*0.5), int(maskSize[1]*scaley*0.5))
            maskMask=cv2.ellipse(mask, center, axis, 0, 0, 360, (255,255,255), -1)
        # Bitwise AND operation to black out regions outside the mask
        resultMask = np.bitwise_and(rotated, maskMask)

        # create a mask image of the same shape as input image, filled with 0s (black color)
        mask = np.zeros_like(rotated)
        if bodyShape == "Rectangular":
            # create a white filled ellipse
            center = (rotated.shape[1]*0.5, rotated.shape[0]*0.5)
            bottomleft = (int(center[0]-bodySize[0]*scalex*0.5), int(center[1]-bodySize[1]*scaley*0.5))
            topright = (int(center[0]+bodySize[0]*scalex*0.5), int(center[1]+bodySize[1]*scaley*0.5))
            maskBody=cv2.rectangle(mask, bottomleft, topright, (255,255,255), -1)
        elif bodyShape == "Circular":
            # create a white filled ellipse
            center = (int(rotated.shape[1]*0.5), int(rotated.shape[0]*0.5))
            axis = (int(bodySize[0]*scalex*0.5), int(bodySize[1]*scaley*0.5))
            maskBody=cv2.ellipse(mask, center, axis, 0, 0, 360, (255,255,255), -1)
        # Bitwise AND operation to black out regions outside the mask
        maskSolder = np.bitwise_and(maskMask, np.invert(maskBody))
        resultBody = np.bitwise_and(rotated, maskBody)
        resultSolder = np.bitwise_and(rotated, maskSolder)
        station = self.project_data['Setup']['Station']
        filename=station+"_"+str(int(round(time.time()*1000)))
        filename+="_["+designator+"]_["+footprint+"]_["+str(angle)
        filename+="]_["+str(polarity)+"]_"+bodyShape+"["+str(bodySize[0])+"_"+str(bodySize[1])+"]_"+maskShape+"["+str(maskSize[0])+"_"+str(maskSize[1])+"]"
        filename+="_"
        joined=os.path.join(path, filename)
        print("Capturing", joined+"*.png")
        cv2.imwrite(joined+"RotatedMask.jpg",resultMask, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(joined+"RotatedBody.jpg",resultBody, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(joined+"RotatedSolder.jpg",resultSolder, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(joined+"MaskMask.png",maskMask, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        cv2.imwrite(joined+"MaskBody.png",maskBody, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        cv2.imwrite(joined+"MaskSolder.png",maskSolder, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        cv2.imwrite(joined+"Raw.jpg",frame2, [cv2.IMWRITE_JPEG_QUALITY, 90])


    def cam_draw_crosshair(self, frame):
        center = (int(frame.shape[1]*0.5), int(frame.shape[0]*0.5))
        left = (center[0]-100, center[1])
        right = (center[0]+100, center[1])
        top = (center[0], center[1]-100)
        bottom = (center[0], center[1]+100)

        cv2.line(frame, left, right, (255,0,0), 2)
        cv2.line(frame, top, bottom, (255,0,0), 2)

        for i in range(-5,6):
            # horizontal dashes
            start = (center[0]+i*20,center[1]+5)
            end = (center[0]+i*20,center[1]-5)
            cv2.line(frame, start, end, (255,0,0), 2)
            # vertical dashes
            start = (center[0]+5,center[1]+i*20)
            end = (center[0]-5,center[1]+i*20)
            cv2.line(frame, start, end, (255,0,0), 2)

    def cam_teachin_part(self, frame, scalex, scaley, angle, bodyShape, bodySize, maskShape, maskSize):
            rotated=imutils.rotate(frame, int(angle))
            # draw body
            if bodyShape == "Rectangular":
                center = (rotated.shape[1]*0.5, rotated.shape[0]*0.5)
                bottomleft = (int(center[0]-bodySize[0]*scalex*0.5), int(center[1]-bodySize[1]*scaley*0.5))
                topright = (int(center[0]+bodySize[0]*scalex*0.5), int(center[1]+bodySize[1]*scaley*0.5))
                cv2.rectangle(rotated, bottomleft, topright, (64,64,64), 2)
            elif bodyShape == "Circular":
                center = (int(rotated.shape[1]*0.5), int(rotated.shape[0]*0.5))
                axis = (int(bodySize[0]*scalex*0.5), int(bodySize[1]*scaley*0.5))
                cv2.ellipse(rotated, center, axis, 0,0,360, (64,64,64), 2)
            # draw mask
            if maskShape == "Rectangular":
                center = (rotated.shape[1]*0.5, rotated.shape[0]*0.5)
                bottomleft = (int(center[0]-maskSize[0]*scalex*0.5), int(center[1]-maskSize[1]*scaley*0.5))
                topright = (int(center[0]+maskSize[0]*scalex*0.5), int(center[1]+maskSize[1]*scaley*0.5))
                cv2.rectangle(rotated, bottomleft, topright, (0,0,0), 2)
            elif maskShape == "Circular":
                center = (int(rotated.shape[1]*0.5), int(rotated.shape[0]*0.5))
                axis = (int(maskSize[0]*scalex*0.5), int(maskSize[1]*scaley*0.5))
                cv2.ellipse(rotated, center, axis, 0,0,360, (0,0,0), 2)
            return rotated

    def cam_update(self, dt):
        try:
            _, frame = self.capture.read()
            # capture
            if self.capture_video:
                path=os.path.expanduser(self.project_data['Setup']['ReportingPath'])
                inspectpart=self.project_data['InspectionPath'][self.capture_video_inspectionpart]
                partref=inspectpart['Partsdefinition']
                if partref != -1:
                    part=inspection.get_part_definition(self.project_data['PartsDefinition']['PartsDefinition'], partref)
                    body_shape=part['BodyShape']
                    body_size=part['BodySize']
                    mask_shape=part['MaskShape']
                    mask_size=part['MaskSize']
                    rotation=inspectpart['Rotation']-part['Rotation']
                    polarity=part['Polarity']
                    designator=inspectpart['Designator']
                    footprint=inspectpart['Footprint']
                    self.cam_capture_video(frame, path, self.project_data['Setup']['CalibrationScaleX'], self.project_data['Setup']['CalibrationScaleY'], footprint, designator, rotation, polarity, body_shape, body_size, mask_shape, mask_size)
                self.capture_video=0
            # overlay cross
            if self.overlay_crosshair:
                self.cam_draw_crosshair(frame)
            if self.overlay_teachin:
                #print("overlay", self.overlay_teachin_body_shape, self.overlay_teachin_body_size, self.overlay_teachin_mask_shape, self.overlay_teachin_mask_size, self.overlay_teachin_rotation)
                frame=self.cam_teachin_part(frame, self.project_data['Setup']['CalibrationScaleX'], self.project_data['Setup']['CalibrationScaleY'], self.overlay_teachin_rotation,self.overlay_teachin_body_shape, self.overlay_teachin_body_size, self.overlay_teachin_mask_shape, self.overlay_teachin_mask_size)
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tostring()
            texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.ids['img_cam'].texture = texture1

        except Exception as e:
            print("cam exception", e)
            pass

    #### File menu
    def exit_app(self):
        self.camera_disconnect()
        self.printer_disconnect()
        App.get_running_app().stop()
    def new_file(self):
        ## File menu / New Project
        self.init_project()

    def init_project(self):
        # init data
        self.project_file_path = ""
        self.project_data=data.init_project_data()
        self.project_data['CADMode']="None"
        self.ids["img_cad_origin"].set_cad_view(self.project_data)
        self.ids["img_cad_origin"].redraw_cad_view()
        self.capture = None
        self.print = None
        self.paneldisselection=[]
        self.overlay_crosshair=0
        self.overlay_teachin=0
        self.capture_video=0

        try:
            self.camera_disconnect()
            self.camera_connect()
            self.printer_disconnect()
            self.printer_connect()
        except Exception as e:
            print(e, "cam or printer start problem")
            pass

    def load_file(self):
        ### File Menu / Load project
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
        self.project_data['CADMode']="None"

    def load(self, path, filename):
        ### click load button of Loading Dialog
        ### load all info from pre saved project file
        try:
            ### if proper project file
            self.project_file_path =  os.path.expanduser(filename[0])
            self.project_data=data.read_project_data(self.project_file_path)
            self.paneldisselection=[]
            try:
                self.camera_disconnect()
                self.camera_connect()
                self.printer_disconnect()
                self.printer_connect()
            except Exception as e:
                print(e, "cam or printer start problem")
                pass

            self.ids["img_cad_origin"].set_cad_view(self.project_data)
            self.ids["img_cad_origin"].redraw_cad_view()
        except:
            ### if not proper project file
            print("Problem loading file")
            self.dismiss_popup()
            return
        self.dismiss_popup()

    def save_file(self):
        ### File Menu / Save Project
        if self.project_file_path == "":
            self.save_as_file()
        else:
            data.write_project_data(self.project_file_path, self.project_data)

    def save_as_file(self):
        ### File Menu / Save as Project
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save(self, path, filename):
        ### after click Save button of Save Dialog
        self.project_file_path = os.path.expanduser(os.path.join(path, filename))
        print(path, filename, self.project_file_path)
        data.write_project_data(self.project_file_path, self.project_data)
        self.dismiss_popup()


    #### program menu ####
    def import_file(self):
        ### Program menu / import pick and place
        content = ImportDialog(load=self.import_pp, cancel=self.dismiss_popup)
        self._popup = Popup(title="Import file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()
        self.project_data['CADMode']="None"

    def import_pp(self, path, filename):

        ### after click load button of Loading button
        try:
            ### if proper project file
            pp_file_path  = os.path.expanduser(filename[0])
            inspection.load_pick_place(self.project_data, pp_file_path)
            inspection.assign_partsdefinition(self.project_data)
            #print("data", self.project_data)
            # redraw
            self.ids["img_cad_origin"].redraw_cad_view()

        except:
            ### if not proper project file
            self.dismiss_popup()
            return

        self.dismiss_popup()


    def select_side(self):
        ### Program menu / Select Soldering Side
        side = [  { "text" : "Top", "is_selected" : self.project_data['InspectionSide']=="Top" },
                { "text" : "Bottom", "is_selected" : self.project_data['InspectionSide']=="Bottom" }  ]
        self.ignore_first=not side[0]['is_selected']

        content = ListPopup()
        args_converter = lambda row_index, rec: {'text': rec['text'], 'is_selected': rec['is_selected'], 'size_hint_y': None, 'height': 50}
        list_adapter = ListAdapter(data=side, args_converter=args_converter, propagate_selection_to_data=True, cls=ListItemButton, selection_mode='single', allow_empty_selection=False)
        list_view = ListView(adapter=list_adapter)

        content.ids.profile_list.add_widget(list_view)

        list_view.adapter.bind(on_selection_change=self.selected_side)

        self._popup = Popup(title="Select Soldering Side", content=content, size_hint=(0.5, 0.6))
        self._popup.open()
        self.project_data['CADMode']="None"

    def selected_side(self, adapter):
        if self.ignore_first:
            self.ignore_first=False
            return
        self.project_data['InspectionSide']=adapter.selection[0].text
        self.dismiss_popup()
        self.ids["img_cad_origin"].redraw_cad_view()

    def set_reference1(self):
        ### Program Menu / Set Reference point 1
        self.project_data['CADMode']="Ref1"

    def set_reference2(self):
        ### Program Menu /  Set Reference Point 2
        self.project_data['CADMode']="Ref2"

    def calibrate(self):
        ### Program Menu /  Calibrate
        #Move Camera to Panel Reference 1 and take picture
        #Move Camera to Panel Reference 1 + x=10mm and take picture
        #Move Camera to Panel Reference 1 + x=-10mm and take picture
        #Move Camera to Panel Reference 1 + y=10mm and take picture
        #Move Camera to Panel Reference 1 + y=-10mm and take picture
        #Calculate center position of the marker on each picture
        # on x Number of Pixels  scalex = offset x / 20mm
        # on y Number of Pixels  scaley = offset y / 20mm
        return

    def teachin(self):
        ### Program Menu /  Teachin
        # Dialog let user choose unassign part from list
        # Show Dialog for Teachin "TeachinPopup"
        # MaskShape possible choice Rectangular / Circular
        # MaskSize [ x, y] convert pixel to mm of box size, also possible to input size in textfield for x and y
        # BodyShape possible choice Rectangular / Circular
        # BodySize [ x, y ] convert pixel to mm of box size, also possible to input size in textfield for x and y
        # Save, Cancel Button
        # On Save store in partsdefinition.json and update data_project['PartsDefinition']['PartsDefinition'] with the file, see data.py for details
        self.ids["tab_panel"].switch_to(self.ids["tab_panel"].tab_list[0])
        self.content = TeachinPopup(save=self.select_teachin_save, cancel=self.dismiss_popup)

        #initialize control
        self.content.ids["body_input_x"].text = format(self.project_data['Setup']['BodySize'][0],".1f")
        self.content.ids["body_input_y"].text = format(self.project_data['Setup']['BodySize'][1],".1f")
        self.content.ids["mask_input_x"].text = format(self.project_data['Setup']['MaskSize'][0],".1f")
        self.content.ids["mask_input_y"].text = format(self.project_data['Setup']['MaskSize'][1],".1f")

        if self.project_data['Setup']['BodyShape'] == "Rectangular" :
            self.content.ids["body_switch"].active =  True
        else:
            self.content.ids["body_switch"].active =  False

        if self.project_data['Setup']['MaskShape'] == "Rectangular" :
            self.content.ids["mask_switch"].active =  True
        else:
            self.content.ids["mask_switch"].active =  False

        self._popup = Popup(title="Teachin Part", content=self.content,
                            size_hint=(0.2, 0.5), background_color=[0, 0, 0, 0.0])
        self._popup.pos_hint={"center_x": .9, "center_y": .75}
        self._popup.open()

        # set body and mask
        #ref=inspection.get_reference_1(self.project_data['InspectionPath'])
        #self.capture_video_inspectionpart=ref
        #self.set_part_overlay(ref)

        self.project_data['CADMode']="None"

    def select_teachin_save(self):
        #frame=self.cam_teachin_part(frame, self.project_data['Setup']['CalibrationScaleX'], self.project_data['Setup']['CalibrationScaleY'], self.overlay_teachin_rotation,self.overlay_teachin_body_shape, self.overlay_teachin_body_size, self.overlay_teachin_mask_shape, self.overlay_teachin_mask_size)
        
        #self.overlay_teachin_body_size = 
        body_cx = float(self.content.ids["body_input_x"].text)
        body_cy = float(self.content.ids["body_input_y"].text)
        mask_cx = float(self.content.ids["mask_input_x"].text)
        mask_cy = float(self.content.ids["mask_input_y"].text)
        self.overlay_teachin_body_size = (body_cx, body_cy)
        self.overlay_teachin_mask_size = (mask_cx, mask_cy)

        if self.content.ids["body_switch"].active :
            self.overlay_teachin_body_shape = "Rectangular"
        else:
            self.overlay_teachin_body_shape = "Circular"

        if self.content.ids["mask_switch"].active :
            self.overlay_teachin_mask_shape = "Rectangular"
        else:
            self.overlay_teachin_mask_shape = "Circular"

        return

    ##### panel menu
    def set_num_panel(self):
        num=inspection.get_num_panel(self.project_data['Panel'])
        content = EditPopup(save=self.save_panel_num, cancel=self.dismiss_popup)
        content.ids["btn_connect"].text = "Save"
        content.ids["text_port"].text = str(num)
        self._popup = Popup(title="Select panel num", content=content,
                            size_hint=(0.5, 0.4))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save_panel_num(self, txt_port):
        # set num of panels
        num  = int(txt_port)
        num = max(1, num)
        num = min(self.project_data['Setup']['MaxPanel'], num)
        inspection.set_num_panel(self.project_data['Panel'], num)
        self.dismiss_popup()

    def set_part_overlay(self, partindex):
        partref=-1
        if partindex!=-1:
            inspectpart=self.project_data['InspectionPath'][partindex]
            partref=inspectpart['Partsdefinition']
        if partref != -1:
            part=inspection.get_part_definition(self.project_data['PartsDefinition']['PartsDefinition'], partref)
            self.overlay_teachin_body_shape=part['BodyShape']
            self.overlay_teachin_body_size=part['BodySize']
            self.overlay_teachin_mask_shape=part['MaskShape']
            self.overlay_teachin_mask_size=part['MaskSize']
            self.overlay_teachin_rotation=inspectpart['Rotation']-part['Rotation']
        else:
            setup=self.project_data['Setup']
            self.overlay_teachin_body_shape=setup['BodyShape']
            self.overlay_teachin_body_size=setup['BodySize']
            self.overlay_teachin_mask_shape=setup['MaskShape']
            self.overlay_teachin_mask_size=setup['MaskSize']
            self.overlay_teachin_rotation=0
        #print("overlay", self.overlay_teachin_body_shape, self.overlay_teachin_body_size, self.overlay_teachin_mask_shape, self.overlay_teachin_mask_size, self.overlay_teachin_rotation)
        self.overlay_teachin=1
        self.overlay_crosshair=1

    def set_reference_panel(self):
        #  show dialpad
        #print("ref")
        self.ids["tab_panel"].switch_to(self.ids["tab_panel"].tab_list[0])
        self.content = ControlPopup(controlXYZ=self.control_XYZ, set_panel_ref1=self.set_panel_ref1, set_panel_ref2=self.set_panel_ref2, get_panel_ref1=self.get_panel_ref1, get_panel_ref2=self.get_panel_ref2, teachin_reference=self.teachin_reference, cancel=self.dismiss_popup)
        self.content.ids["cur_X"].text = format(self.project_data['Setup']['TravelX'],".2f")
        self.content.ids["cur_Y"].text = format(self.project_data['Setup']['TravelY'],".2f")
        self.content.ids["cur_Z"].text = format(self.project_data['Setup']['TravelZ'],".2f")
        self.content.ids["cur_panel"].text = "1"
        self._popup = Popup(title="Set reference point", content=self.content,
                            size_hint=(0.4, 0.4), background_color=[0, 0, 0, 0.0])
        self._popup.pos_hint={"center_x": .8, "center_y": .8}
        self._popup.open()
        self.project_data['CADMode']="None"
        
        # set body and mask
        ref=inspection.get_reference_1(self.project_data['InspectionPath'])
        self.capture_video_inspectionpart=ref
        self.set_part_overlay(ref)

        # home printer
        gcode=robotcontrol.go_home(self.project_data)
        self.queue_printer_command(gcode)

    def teachin_reference(self):
        self.capture_video=1
        return

    def control_XYZ(self, axis, value):
        ### click any button on dialpad, calculate new position
        index=int(self.content.ids["cur_panel"].text)
        x=float(self.content.ids["cur_X"].text)
        y=float(self.content.ids["cur_Y"].text)
        z=float(self.content.ids["cur_Z"].text)

        if axis == "X":
            x += float(value)
        elif axis == "Y":
            y += float(value)
        # TODO cleanup dialpad
        #elif axis == "Z":
        #    z += float(value)
        elif axis == "HomeXY":
            x=self.project_data['Setup']['TravelX']
            y=self.project_data['Setup']['TravelY']
        elif axis == "HomeZ":
            z=self.project_data['Setup']['TravelZ']

        index = max(1, index)
        index = min(self.project_data['Setup']['MaxPanel'], index)
        x=max(self.project_data['Setup']['MinX'],x)
        x=min(self.project_data['Setup']['MaxX'],x)
        y=max(self.project_data['Setup']['MinY'],y)
        y=min(self.project_data['Setup']['MaxY'],y)
        z=max(self.project_data['Setup']['MinZ'],z)
        z=min(self.project_data['Setup']['MaxZ'],z)

        self.content.ids["cur_panel"].text = str(index)
        self.content.ids["cur_X"].text = format(x,".2f")
        self.content.ids["cur_Y"].text = format(y,".2f")
        self.content.ids["cur_Z"].text = format(z,".2f")

        # go xyz printer
        gcode=robotcontrol.go_xyz(self.project_data,x,y,z)
        self.queue_printer_command(gcode)

    def set_panel_ref1(self):
        ### click set1 button on dialpad
        index=int(self.content.ids["cur_panel"].text)
        index=min(index,inspection.get_num_panel(self.project_data['Panel']))
        index=max(index,1)

        x=float(self.content.ids["cur_X"].text)
        y=float(self.content.ids["cur_Y"].text)
        z=float(self.content.ids["cur_Z"].text)
        inspection.set_panel_reference_1(self.project_data['Panel'], index-1, x, y)

    def set_panel_ref2(self):
        ### click set2 button on dialpad
        index=int(self.content.ids["cur_panel"].text)
        x=float(self.content.ids["cur_X"].text)
        y=float(self.content.ids["cur_Y"].text)
        z=float(self.content.ids["cur_Z"].text)
        inspection.set_panel_reference_2(self.project_data['Panel'], index-1, x, y)

    def get_panel_ref1(self):
        ### click on get1 button on dialpad
        index=int(self.content.ids["cur_panel"].text)
        x,y = inspection.get_panel_reference_1(self.project_data['Panel'], index-1)
        if x==-1 and y==-1 and z==-1:
            x=self.project_data['Setup']['TravelX']
            y=self.project_data['Setup']['TravelY']
        z=self.project_data['Setup']['TravelZ']
        self.content.ids["cur_X"].text = format(x,".2f")
        self.content.ids["cur_Y"].text = format(y,".2f")
        self.content.ids["cur_Z"].text = format(z,".2f")
        # set body and mask
        ref=inspection.get_reference_1(self.project_data['InspectionPath'])
        self.set_part_overlay(ref)
        self.capture_video_inspectionpart=ref

        # go xyz printer
        gcode=robotcontrol.go_xyz(self.project_data,x,y,z)
        self.queue_printer_command(gcode)

    def get_panel_ref2(self):
        ### click on get2 button on dialpad
        index=int(self.content.ids["cur_panel"].text)
        x,y = inspection.get_panel_reference_2(self.project_data['Panel'], index-1)
        if x==-1 and y==-1:
            x=self.project_data['Setup']['TravelX']
            y=self.project_data['Setup']['TravelY']
        z=self.project_data['Setup']['TravelZ']
        self.content.ids["cur_X"].text = format(x,".2f")
        self.content.ids["cur_Y"].text = format(y,".2f")
        self.content.ids["cur_Z"].text = format(z,".2f")
        # set body and mask
        ref=inspection.get_reference_2(self.project_data['InspectionPath'])
        self.set_part_overlay(ref)
        self.capture_video_inspectionpart=ref

        # go xyz printer
        gcode=robotcontrol.go_xyz(self.project_data,x,y,z)
        self.queue_printer_command(gcode)

    def select_pcb_in_panel(self):
        num=inspection.get_num_panel(self.project_data['Panel'])
        content = EditPopup(save=self.save_pcb_in_panel, cancel=self.dismiss_popup)
        content.ids["btn_connect"].text = "Save"
        content.ids["text_port"].text = ""
        self._popup = Popup(title="Select Panels to exclude from Soldering example \"1,2\"", content=content,
                            size_hint=(0.5, 0.4))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save_pcb_in_panel(self, txt_port):
        # set array of panels
        excludepanels=txt_port.split(",")
        panel=[]
        for p in range(inspection.get_num_panel(self.project_data['Panel'])):
            if str(p+1) in excludepanels:
                panel.append(p)
        self.paneldisselection=panel
        self.dismiss_popup()

    def start_inspection(self):
        ### toolbar start soldering button
        # prepare panel
        panel=[]
        for p in range(inspection.get_num_panel(self.project_data['Panel'])):
            if p not in self.paneldisselection:
                panel.append(p)
        # print
        #print("panel", panel)
        gcode=robotcontrol.panel_inspection(self.project_data, panel)
        self.queue_printer_command(gcode)

    def pause_inspection(self):
        ### toolbar pause inspection button
        if self.print.printing:
            self.print.pause()

    def resume_inspection(self):
        ### toolbar resume inspection button
        if self.print.printing:
            self.print.resume()

    def stop_inspection(self):
        ### toolbar stop inspection button
        if self.print.printing:
            self.print.cancelprint()

    def queue_printer_command(self, gcode):
        garray=robotcontrol.make_array(gcode)
        #print("gcode raw", gcode, garray)

        gcoded = gcoder.LightGCode(garray)
        #print("gcoded", gcoded)
        if hasattr(self,'print') and self.print is not None:
            if not self.print.online or not self.print.printer:
                print("Problem with printer", self.print.online, self.print.printer)
            if self.print.printing:
                self.print.send(gcoded)
            else:
                self.print.startprint(gcoded)
        else:
            print("Problem with printer interface")
    #### Connect menu
    def set_printer(self):
        ### Connect Menu /  Connect Printer
        content = EditPopup(save=self.save_printer_port, cancel=self.dismiss_popup)
        content.ids["text_port"].text = self.project_data['Setup']['RobotPort']
        self._popup = Popup(title="Select Printer port", content=content,
                            size_hint=(0.5, 0.4))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save_printer_port(self, txt_port):
        self.project_data['Setup']['RobotPort'] = txt_port
        try:
            self.printer_disconnect()
            self.printer_connect()
        except  Exception as e:
            print(e,"exception save robot port")
            pass
        self.dismiss_popup()

    def set_camera(self):
        # set camera device
        content = EditPopup(save=self.save_camera_port, cancel=self.dismiss_popup)
        content.ids["text_port"].text = self.project_data['Setup']['CameraPort']
        self._popup = Popup(title="Select Camera port", content=content,
                            size_hint=(0.5, 0.4))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save_camera_port(self, txt_port):
        self.project_data['Setup']['CameraPort'] = txt_port
        try:
            self.camera_disconnect()
            self.camera_connect()
        except  Exception as e:
            print(e,"exception save cam port")
            pass
        self.dismiss_popup()

    def set_reporting(self):
        # set camera device
        content = EditPopup(save=self.save_camera_port, cancel=self.dismiss_popup)
        content.ids["text_port"].text = self.project_data['Setup']['ReportingPath']
        self._popup = Popup(title="Select Camera port", content=content,
                            size_hint=(0.5, 0.4))
        self._popup.open()
        self.project_data['CADMode']="None"

    def save_reporting_port(self, txt_port):
        self.project_data['Setup']['ReportingPath'] = txt_port
        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()
        self.overlay_crosshair=0
        self.overlay_teachin=0

    def camera_connect(self):
        ### connect camera
        self.capture = VideoCaptureAsync(self.project_data['Setup']['CameraPort'], self.project_data['Setup']['CameraResX'],self.project_data['Setup']['CameraResY'])
        self.capture.start()

    def camera_disconnect(self):
        if self.capture is not None:
            self.capture.stop()
            self.capture = None

    def printer_connect(self):
        if self.print is None:
            self.print = printcore(self.project_data['Setup']['RobotPort'], 115200)
            self.print.addEventHandler(self)

    def printer_disconnect(self):
        if self.print is not None:
            self.print.disconnect()
            self.print = None

    # printrun events:
    def on_init(self):
        return #self.__write("on_init")

    def on_send(self, command, gline):
        return #self.__write("on_send", command)

    def on_recv(self, line):
        return #self.__write("on_recv", line.strip())

    def on_connect(self):
        return #self.__write("on_connect")

    def on_disconnect(self):
        return #self.__write("on_disconnect")

    def on_error(self, error):
        return #self.__write("on_error", error)

    def on_online(self):
        return #self.__write("on_online")

    def on_temp(self, line):
        return #self.__write("on_temp", line)

    def on_start(self, resume):
        return #self.__write("on_start", "true" if resume else "false")

    def on_end(self):
        return #self.__write("on_end")

    def on_layerchange(self, layer):
        return #self.__write("on_layerchange", "%f" % (layer))

    def on_preprintsend(self, gline, index, mainqueue):
        return #self.__write("on_preprintsend", gline)

    def on_printsend(self, gline):
        return #self.__write("on_printsend", gline)

    def show_status(self, dt):
        self.ids["lbl_layer_status"].text="Layer: "+self.project_data['InspectionSide']
        self.ids["lbl_cad_status"].text="CADMode: "+self.project_data['CADMode']
        unassigned=inspection.get_list_unassigned_parts(self.project_data)
        self.ids["lbl_profile_status"].text="# unassigned parts: "+str(len(unassigned))
        if hasattr(self,'capture') and self.capture is not None:
            self.ids["lbl_cam_status"].text="Camera: Connected"
        else:
            self.ids["lbl_cam_status"].text="Camera: Not Found"
        #printer
        if hasattr(self,'print') and self.print is not None:
            if self.print.printer is None:
                self.ids["lbl_printer_status"].text="Robot: No 3d printer found"
            elif self.print.printing:
                if len(self.print.mainqueue)>0:
                    self.ids["lbl_printer_status"].text="Robot: Inspecting "+ str(round(float(self.print.queueindex) / len(self.print.mainqueue)*100,2))+"%"
                else:
                    self.ids["lbl_printer_status"].text="Robot: Inspecting"
            elif self.print.online:
                self.ids["lbl_printer_status"].text="Robot: Idle"
            else:
                self.ids["lbl_printer_status"].text="Robot: Connected"
        else:
            self.ids["lbl_printer_status"].text="Robot: Not Found"


### Application
class MyApp(App):

    def check_resize(self, instance, x, y):
        # resize X
        if x > MAX_SIZE[0]:
            Window.size = (MAX_SIZE[0], Window.size[1])
        # resize Y
        if y > MAX_SIZE[1]:
            Window.size = (Window.size[0], MAX_SIZE[1])
    def mainscreen(self):
        screen["screen"] = "main"

    def build(self):
        self.title = 'SMD Optical Inspection'
        Window.size = MAX_SIZE
        Window.bind(on_resize=self.check_resize)
        self.screen_manage = ScreenManagement()
        return self.screen_manage
    def on_stop(self):
        self.screen_manage.current_screen.camera_disconnect()
        self.screen_manage.current_screen.printer_disconnect()


if __name__ == '__main__':
    Builder.load_file("main.kv")
    MyApp().run()
    cv2.destroyAllWindows()
