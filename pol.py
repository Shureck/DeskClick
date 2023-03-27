import json
import evdev
from shapely.geometry import Point, Polygon
import pygame
import os.path as path
import os

class MouseTracker:
    def __init__(self, polygons_file):
        # Read polygons from JSON file
        pygame.mixer.init()
        self.polygons_file = polygons_file
        with open(self.polygons_file, 'r') as f:
            self.polygons = json.load(f)

        # Convert dots to tuple of float values and adjust coordinates to (0, 32768)
        for polygon in self.polygons['paths']:
            polygon['dots'] = [(int(dot[0]/self.polygons['size']['width']*32768), int(dot[1]/self.polygons['size']['height']*32768)) for dot in polygon['dots']]

        # Initialize last_polygon
        self.last_polygon = -1

        self.back_path = path.abspath(path.join(__file__, "../")
                         ).replace("\\", "/") + '/dir'

    # Function to check which polygon the coordinates fall into and play the audio file if it exists
    def check_coordinates(self, x_, y_):
        polygon = None
        max = -1
        for polyg in self.polygons['paths']:
            poly = Polygon(polyg['dots'])
            if poly.contains(Point(x_, y_)):
                if polyg['level'] > max:
                    max = polyg['level']
                    polygon = polyg
        if polygon != None and polygon['level'] != self.last_polygon:
            self.last_polygon = polygon['level']
            if polygon['text'] != "":
                print(polygon['text'])
            else:
                print("play "+polygon['filename'])
                pygame.mixer.music.load(self.back_path+"/files/"+polygon['filename'])
                pygame.mixer.music.play()

    def update_polygon(self):
        with open(self.polygons_file, 'r') as f:
            self.polygons = json.load(f)

        for polygon in self.polygons['paths']:
            polygon['dots'] = [(int(dot[0]/self.polygons['size']['width']*32768), int(dot[1]/self.polygons['size']['height']*32768)) for dot in polygon['dots']]
        self.last_polygon = -1

    def get_mouse(self):
        global x
        global y
        x_ = 0
        y_ = 0
        dev = evdev.InputDevice("/dev/input/event2")
        print(dev)
        for event in dev.read_loop():
            if event.code == 0: #evdev.ecodes.ABS_X:
                x_ = event.value
            if event.code == 1: #evdev.ecodes.ABS_Y:
                y_ = event.value
            if x_ != 0 and y_ != 0:
                x = x_
                y = y_
                self.check_coordinates(x, y)
