import sys
sys.path.append("../")

import os
import queue
import time
import signal
from pyaudio import PyAudio, paContinue, paFloat32

from cochl_sense.stream import StreamBuilder

import json
import pprint
from phue import Bridge
import numpy as np


def switch_color(color):
    # Color change rules
    if color == [1,0]:  # Red
        color_new = [0,1]
    elif color == [0,1]:  # Green
        color_new = [0,0]
    elif color == [0,0]:  # Blue
        color_new = [0.3,0.3]
    elif color == [0.3,0.3]:  # White
        color_new = [1,0]
    return color_new


def tag2idx(tag):
    tag_list = ['Clap', 'Finger_snap', 'Knock', 'Whisper', 'Whistling', 'Others']
    return tag_list.index(tag)


# # Step 1: Phue settings
# If the app is not registered and the button is not pressed, 
# press the button and call connect() (this only needs to be run a single time)
b = Bridge('<YOUR_BRIDGE_IP_ADDRESS>')
b.connect()
b.get_api()
lights = b.get_light_objects()
# The light index you want to control (0 ~ number_of_Phue - 1)
idx = 0


# # Step 2: Sense API-related parameters
# You can get API key in https://dashboard.cochl.ai/projects/api
# If your API key is not for human-interaction, 
# fix tag2idx() and on_detected_events() functions.
api_key = '<COCHL.SENSE_API_KEY>'
prev_tag = ''
current_color = [0.3,0.3]  # Initial color is white

SECOND_TO_INFERENCE=1200000


class PyAudioSense:
    def __init__(self):
        self.rate = 22050
        chunk = int(self.rate / 2)
        self.buff = queue.Queue()
        self.audio_interface = PyAudio()
        self.audio_stream = self.audio_interface.open(
             format=paFloat32,
             channels=1, rate=self.rate,
             input=True, frames_per_buffer=chunk,
             stream_callback=self._fill_buffer
        )

    def stop(self):
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.buff.put(None)
        self.audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self.buff.put(in_data)
        return None, paContinue

    def generator(self):
        while True:
            chunk = self.buff.get()
            if chunk is None:
                return
            yield chunk

stream = PyAudioSense()

sense = StreamBuilder() \
    .with_api_key(api_key) \
    .with_streamer(stream.generator) \
    .with_data_type("float32") \
    .with_sampling_rate(22050) \
    .with_smart_filtering(True) \
    .build() \

def on_detected_events(result):
    try:
        prev_tag = np.load('prev_tag.npy')
    except:
        prev_tag = 5

    mytag = result.detected_tags()[0]
    if mytag != 'Others':
        print('Detected event: {}'.format(mytag))

    # Action definition
    if prev_tag != tag2idx(mytag):
        # Whistle + already on : Reset the brightness to max
        # Whistle + currently off : Turn on and set the brightness to max
        if mytag == 'Clap':
            if lights[idx].on == False:
                lights[idx].on = True
            lights[idx].brightness = 255

        # Knock : turn off the light
        elif mytag == 'Knock' and lights[idx].on:
            lights[idx].on = False
        
        # Finger snap : change the color
        # (white -> r -> g -> b -> white ...)
        elif mytag == 'Finger_snap' and lights[idx].on:
            # Change the color
            current_color = switch_color(current_color)
            lights[idx].xy = current_color

        # Whisper: dim the light (or turn it off if it's too dark)
        elif mytag == 'Whisper':
            if lights[idx].brightness >= 100:
                lights[idx].brightness -= 100
            else:
                lights[idx].on = False

        elif mytag == 'Whistling':
            for n in range(3):
                lights[idx].on = not lights[idx].on
                time.sleep(0.5)
            lights[idx].on = not lights[idx].on

    np.save('prev_tag.npy', tag2idx(mytag))




sense.inference(on_detected_events)

def handle_exit(sig, frame):
    stream.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)

print("inferencing")
time.sleep(SECOND_TO_INFERENCE)
stream.stop()
