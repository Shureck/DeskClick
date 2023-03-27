from fastapi import FastAPI, status, Request, Body, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Set, Union, Optional
from shapely.geometry import Point, Polygon
import os.path as path
import os
import requests
import json
import secrets
import evdev
from pydantic import BaseModel
import threading
import uvicorn
from pol import MouseTracker
import wave
from speechkit import Session, SpeechSynthesis

app = FastAPI()

back_path = path.abspath(path.join(__file__, "../")
                         ).replace("\\", "/") + '/dir'
path = path.abspath(path.join(__file__, "../")
                         ).replace("\\", "/") + '/build'

pwd = back_path+"/"
app.mount("/dir", StaticFiles(directory=back_path), name="dir")

app.mount("/static", StaticFiles(directory=path+"/static"), name="static")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


polygons_file = 'polygons.json'
mt = MouseTracker(polygons_file)

oauth_token = "y0_AgAAAAAhwzfrAATuwQAAAADcbw9GsZVig0DqTnObK5XXzXI4UVoZie8"
catalog_id = "b1gnbu1bvm56hin6jfbd"

# Экземпляр класса `Session` можно получать из разных данных 
session = Session.from_yandex_passport_oauth_token(oauth_token, catalog_id)

@app.on_event("startup")
async def startup_event():
    global mt

    synthesizeAudio = SpeechSynthesis(session)
    synthesizeAudio.synthesize(
        'out.wav', text='Привет мир!',
        voice='oksana', format='lpcm', sampleRateHertz='16000'
    )

    thread = threading.Thread(target = mt.get_mouse)
    thread.start()

# async def check_point_in_polygon(point: PointModel, polygons: List[PolygonModel]):
#     for polygon in polygons:
#         poly = Polygon(polygon.dots)
#         if poly.contains(Point(point.x, point.y)):
#             return {"text": polygon.text}
#     return {"text": None}
class Size(BaseModel):
    height: int = None
    width: int = None

class PolygonModel(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None
    level: int
    dots: List[List[str]]   

class PointModel(BaseModel):
    x: float
    y: float


class Poly(BaseModel):
    paths: List[PolygonModel]
    size: Size

@app.post("/file")
async def create_file(file: UploadFile):
    hash_hex = secrets.token_hex(nbytes=10)
    with open(back_path+"/files/"+hash_hex+"."+file.filename.split('.')[-1], "wb") as f:
        f.write(await file.read())
    return {"filename":hash_hex+"."+file.filename.split('.')[-1]}

@app.post("/polygons")
async def check_point_in_polygon(request: Request):
    global mt
    print(await request.json())
    polygons = await request.json()
    for polygon in polygons['paths']:
        for dot in polygon['dots']:
            dot[0] = int(dot[0])
            dot[1] = int(dot[1])
    with open("polygons.json", "w") as f:
        json.dump(polygons, f, ensure_ascii=False)

    mt.update_polygon()
    return polygons

app.mount("/", StaticFiles(directory=path), name="build")

# def run_mouse():
#     # Read polygons from JSON file
#     with open('polygons.json', 'r') as f:
#         polygons = json.load(f)

#     last_polygon = -1

#     for polygon in polygons:
#         polygon['dots'] = [(int(dot[0]/1920*32768), int(dot[1]/1080*32768)) for dot in polygon['dots']]

#     # Function to check which polygon the coordinates fall into and play the audio file if it exists
#     def check_coordinates(x_, y_):
#         global last_polygon
#         for polygon in polygons:
#             poly = Polygon(polygon['dots'])
#             if poly.contains(Point(x_, y_)):
#                 if polygon['level'] != last_polygon:
#                     last_polygon = polygon['level']
#                     if polygon['text'] != "":
#                         print(polygon['text'])

#     x = 0
#     y = 0

#     # Function to get mouse coordinates and trigger check_coordinates function
#     def get_mouse(device_id):
#         global x
#         global y
#         x_ = 0
#         y_ = 0
#         dev = evdev.InputDevice("/dev/input/event3")
#         for event in dev.read_loop():
#             if event.code == 0: #evdev.ecodes.ABS_X:
#                 x_ = event.value
#             if event.code == 1: #evdev.ecodes.ABS_Y:
#                 y_ = event.value
#             if x_ != 0 and y_ != 0:
#                 x = x_
#                 y = y_
#                 check_coordinates(x, y)

#     print("TTTT")
#     get_mouse(4)

# if __name__ == '__main__':
#     uvicorn.run(app, host="0.0.0.0", port=8000)