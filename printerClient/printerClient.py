#!/usr/bin/env python3
import click
import requests
import threading
import struct
import serial
import time
import io
from PIL import Image

from queue import Queue, Empty
from flask import Flask, request, abort

app = Flask(__name__)
app.use_reloader=False
app.host = "0.0.0.0"

printQueue = Queue()

@app.route("/print", methods=["POST"])
def printRoute():
    if "image" not in request.files:
        abort(400)
    # We have to use BytesIO as PIL accesses file after the request ends
    img = Image.open(io.BytesIO(request.files["image"].read()))
    printQueue.put(img)
    return {"status": "OK"}

def resizeToFit(image):
    w, h = image.size
    ratio = 384 / w
    return image.resize((384, int(h * ratio)))

def setSpeed(port, speed):
    port.write(struct.pack("BBB", 0x1D, 0x2F, speed))

def setIntensity(port, intensity):
    port.write(struct.pack("BBB", 0x1D, 0x44, intensity))

def sendImage(port, image):
    bytesize = image.size[0] * image.size[1] // 8
    port.write(struct.pack("BBBBBBBB", 0x1B, 0x2A,
        bytesize % 256, (bytesize // 256) % 256, (bytesize // 65536) % 256,
        0, 0, image.size[0] // 8))
    for y in range(image.size[1]):
        b = 0
        for x in range(image.size[0]):
            v = 0 if image.getpixel((x, y)) > 0 else 1
            b = b | v
            if x % 8 == 7:
                port.write(struct.pack("B", b))
                b = 0
            else:
                b *= 2

def readLevel(port):
    port.write(struct.pack("BB", 0x1D, 0x6F))
    response = port.read()
    return int(response[0])

def feedForward(port, mm):
    dots = int(mm / 0.125)
    port.write(struct.pack("BBB", 0x1B, 0x4A, dots))

def feedBackward(port, mm):
    dots = int(mm / 0.125)
    port.write(struct.pack("BBB", 0x1B, 0x6A, dots))

def findEdge(port):
    GAP = 2
    PAPER_THRESHOLD = 230
    while readLevel(port) < PAPER_THRESHOLD:
        print(readLevel(port))
        feedForward(port, 1)
        time.sleep(0.2)
    feedForward(port, GAP + 9)

def printImage(image, port, speed, intensity):
    image = resizeToFit(image)
    image = image.convert('1') # convert image to black and white
    setIntensity(port, 100)
    setSpeed(port, 15)
    sendImage(port, image)
    feedForward(port, 10)


@click.command()
@click.option("--device", type=str, required=True,
    help="Name or a path of printer COM port")
@click.option("--name", type=str, required=True,
    help="Name of the printer in the system")
@click.option("--speed", type=int, default=15)
@click.option("--intensity", type=int, default=200)
@click.option("--server", type=str, required=True,
    help="Server IP address")
@click.option("--port", type=int, default=5000)
def run(device, name, speed, intensity, server, port):
    with serial.Serial(port=device, baudrate=57600, rtscts=True) as serialPort:
        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
        while True:
            try:
                requests.post(f"{server}/printers", data={
                    "name": name,
                    "port": port
                })
            except Exception as e:
                print(f"WARNING: Cannot connect to server: {e}")
            try:
                img = printQueue.get(timeout=30)
                printImage(img, serialPort, speed, intensity)
            except Empty:
                pass

if __name__ == "__main__":
    run()

