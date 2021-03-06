#!/usr/bin/env python

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import print_function

import argparse
import os.path
import json
import time
import threading
import RPi.GPIO as GPIO

import google.oauth2.credentials

from subprocess import call

from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file

PINS = [17,18,27]

class Lights(object):
    """Thread that controlls the lights
    """
    def __init__(self):
        """Constructor"""
        self.led = 0
        self.mode = 0
        self.lastmode = 0
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
    def run(self):
        while True:
            if self.mode == 1: #running lights
                for led in PINS:
                    on = GPIO.LOW
                    if led == PINS[self.led]:
                        on = GPIO.HIGH
                    GPIO.output(led,on)
                self.led += 1
                if self.led > 2:
                    self.led = 0
            elif self.mode == 2: #blink 3 times
                if self.led % 2 == 0:
                    GPIO.output(PINS[0],GPIO.LOW)
                elif self.led % 2 == 1:
                    GPIO.output(PINS[0],GPIO.HIGH)
                self.led += 1
                if self.led == 9:
                    self.mode = 0
            if self.mode == 0 and self.lastmode != 0:
                for led in PINS:
                    GPIO.output(led,GPIO.LOW)
                self.led = 0
            self.lastmode = self.mode
            time.sleep(0.2)

lights = Lights()

def reboot():
    call(["/usr/bin/sudo","reboot"])

def shutdown():
    call(["/usr/bin/sudo","shutdown"])
    
            
def process_event(event,assistant):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_START_FINISHED:
        lights.mode = 2;
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        print()
        lights.mode = 1;
    if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args['text'] == 'reboot':
        lights.mode = 3;
        reboot();
        assistant.stop_conversation();	
    if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and (event.args['text'] == 'shutdown' or event.args['text'] == 'shut down'):
        lights.mode = 3;
        shutdown();
        assistant.stop_conversation();

    print(event)

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        print()
        lights.mode = 0;



def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in PINS: 
        GPIO.setup(pin,GPIO.OUT)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='Path to store and read OAuth2 credentials')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))

    with Assistant(credentials) as assistant:
        for event in assistant.start():
            process_event(event,assistant)


if __name__ == '__main__':
    main()
