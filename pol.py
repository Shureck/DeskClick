import json
import evdev
from shapely.geometry import Point, Polygon
import pygame
import os.path as path
import os
import secrets
import requests
import subprocess
import time
class MouseTracker:

    def synthesize(self, folder_id, iam_token, text):
        url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        headers = {
            'Authorization': 'Bearer ' + iam_token,
        }

        data = {
            'text': text,
            'lang': 'ru-RU',
            'voice': 'filipp',
            'folderId': folder_id,
            'format': 'mp3',
            'sampleRateHertz': 48000,
        }

        with requests.post(url, headers=headers, data=data, stream=True) as resp:
            if resp.status_code != 200:
                raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

            for chunk in resp.iter_content(chunk_size=None):
                yield chunk

    def __init__(self, polygons_file):
        # Read polygons from JSON file
        subprocess.run(['pulseaudio', '--start'])

        time.sleep(2)

        pygame.mixer.init(devicename='UACDemoV1.0 Аналоговый стерео')
        self.polygons_file = polygons_file
        with open(self.polygons_file, 'r') as f:
            self.polygons = json.load(f)
        
        self.back_path = path.abspath(path.join(__file__, "../")
                         ).replace("\\", "/") + '/dir'

        for polygon in self.polygons['paths']:
            if polygon['text'] != "" and polygon['filename'] == "":
                    hash_hex = secrets.token_hex(nbytes=10)
                    polygon['filename'] = hash_hex+"."+"mp3"
                    with open(self.back_path+"/files/"+hash_hex+"."+"mp3", "wb") as f:
                        for audio_content in self.synthesize("b1gnbu1bvm56hin6jfbd", "t1.9euelZrHkMyVz5XInpKRzozPxs-WzO3rnpWayMjMk52eysiWyZrJzpSKjZvl8_dMHHpe-e9KGRx9_d3z9wxLd17570oZHH39.SPdJPScETa6S8W7jAEsSQGE-fcStTyjlvK_AfddjTWMAhJS77foxoW5zZYkM_nmlwlen-nCO77sCD2guo_J2Ag", polygon['text']):
                            f.write(audio_content)
        
        with open("polygons.json", "w") as f:
            json.dump(self.polygons, f, ensure_ascii=False)

        # Convert dots to tuple of float values and adjust coordinates to (0, 32768)
        for polygon in self.polygons['paths']:
            polygon['dots'] = [(int(dot[0]/self.polygons['size']['width']*32768), int(dot[1]/self.polygons['size']['height']*32768)) for dot in polygon['dots']]
 
        # Initialize last_polygon
        self.last_polygon = -1

    def play(self, file_path, device):
        if device is None:
            devices = get_devices()
            if not devices:
                raise RuntimeError("No device!")
            device = devices[0]
        print("Play: {}\r\nDevice: {}".format(file_path, device))
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(1)
        pygame.mixer.music.play()

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

            print("play "+polygon['filename'])
            self.play(self.back_path+"/files/"+polygon['filename'], 'UACDemoV1.0 Аналоговый стерео')

    def update_polygon(self):
        with open(self.polygons_file, 'r') as f:
            self.polygons = json.load(f)

        for polygon in self.polygons['paths']:
            if polygon['text'] != "" and polygon['filename'] == "":
                    hash_hex = secrets.token_hex(nbytes=10)
                    polygon['filename'] = hash_hex+"."+"mp3"
                    with open(self.back_path+"/files/"+hash_hex+"."+"mp3", "wb") as f:
                        for audio_content in self.synthesize("b1gnbu1bvm56hin6jfbd", "t1.9euelZrHkMyVz5XInpKRzozPxs-WzO3rnpWayMjMk52eysiWyZrJzpSKjZvl8_dMHHpe-e9KGRx9_d3z9wxLd17570oZHH39.SPdJPScETa6S8W7jAEsSQGE-fcStTyjlvK_AfddjTWMAhJS77foxoW5zZYkM_nmlwlen-nCO77sCD2guo_J2Ag", polygon['text']):
                            f.write(audio_content)

        with open("polygons.json", "w") as f:
            json.dump(self.polygons, f, ensure_ascii=False)

        for polygon in self.polygons['paths']:
            polygon['dots'] = [(int(dot[0]/self.polygons['size']['width']*32768), int(dot[1]/self.polygons['size']['height']*32768)) for dot in polygon['dots']]
        self.last_polygon = -1

    def get_mouse(self):
        global x
        global y
        x_ = 0
        y_ = 0
        device_name = "Multi touch   Multi touch overlay device"
        for filename in os.listdir('/dev/input/'):
            if filename.startswith('event'):
                device_path = os.path.join('/dev/input/', filename)
                dev = evdev.InputDevice(device_path)
                if dev.name == device_name:
                    print(f"Device {device_name} found at path {device_path}")
                    # Далее можно использовать найденное устройство `device`
                    break
        else:
            print(f"No device with name {device_name} found")
        for event in dev.read_loop():
            if event.code == 0: #evdev.ecodes.ABS_X:
                x_ = event.value
            if event.code == 1: #evdev.ecodes.ABS_Y:
                y_ = event.value
            if x_ != 0 and y_ != 0:
                x = x_
                y = y_
                self.check_coordinates(x, y)
