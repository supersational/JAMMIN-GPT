import json
import os
import pickle
import re
import threading
import time
import traceback
import itertools
from collections import defaultdict

from mido import MidiFile

# Local application/library specific imports
import fluidsynth_lib
from client import AbletonOSCClient
from generate_midi import make_midi, modify_midi, midifile_to_notes


# Constants
IP = "127.0.0.1"
PORT = 11000
OPERATOR_MAP_PATH = "./params/OperatorMap.json"
MIDI_MAP_PATH = "./params/MidiMap.json"

# Load operator params (mapping generated by chatgpt)
with open(OPERATOR_MAP_PATH, "r") as f:
    operator_map = {int(k): v for k, v in json.load(f).items()}

# Load general midi map
with open(MIDI_MAP_PATH, "r") as f:
    midi_map = {int(k): v for k, v in json.load(f).items()}

# Initialize Ableton OSC client
client = AbletonOSCClient(IP, PORT)


try:
    assert client.query("/live/test")[0] == "ok"
except:
    print(
        """no response from Ableton.
you need to copy client.py into Remote Scripts,
and enable it as a control surface in preferences"""
    )


class Clip:
    def get_name(x, y):
        x, y, name = client.query("/live/clip/get/name", (x, y))
        return name

    def get_curr_name():
        try:
            x, y = client.query("/live/view/get/selected_clip")
        except RuntimeError:
            # print('get_curr_name: no selected clip')
            return None, None, None

        try:
            name = Clip.get_name(x, y)
            return x, y, name
        except RuntimeError:
            # print('get_curr_name: no name for selected clip')
            return None, None, None

    def set_name(x, y, name):
        client.send_message("/live/clip/set/name", (x, y, name))

    def create(x, y, length):
        client.send_message("/live/clip_slot/create_clip", (x, y, length))

    def remove_notes(x, y):
        client.send_message("/live/clip/remove/notes", (x, y, 0, 127, 0, 100000))

    def get_notes(x, y):
        try:
            notes = client.query("/live/clip/get/notes", (x, y, 0, 127, 0, 100000))[2:]
            print("notes:", notes)
            return notes
        except Exception as e:
            print("failed to get notes", e)
            return None

    def set_loop_points(x, y, start, end):
        client.send_message("/live/clip/set/loop_start", (x, y, start))
        client.send_message("/live/clip/set/loop_end", (x, y, end))

    def insert_clip(x, y, midifilename, prompt):
        try:
            class_name = client.query("/live/device/get/class_name", (x, 0))[2]
        except Exception:
            class_name = None

        Clip.remove_notes(x, y)
        midifile = MidiFile(midifilename)

        full_notes, length, instrument = midifile_to_notes(midifile)
        Clip.create(x, y, length)
        Clip.set_name(x, y, "AI:" + prompt + ("empty" if len(full_notes) == 0 else ""))
        for note, velocity, start, duration in full_notes:
            client.send_message(
                "/live/clip/add/notes",
                (x, y, note, start, duration, velocity, 0)
                # last param is 'mute'
            )
        Clip.set_loop_points(x, y, 0, length)
        if instrument is None:
            print("no instrument found")
            return
        if class_name == "Operator":
            print("Setting Operator instrument to", instrument)
            Clip.set_instrument(x, y, instrument)
        else:
            channel = Clip.get_output_channel(x)
            if channel is not None:
                fluidsynth_lib.set_instrument(channel, instrument)
                try:
                    name = midi_map[instrument]
                    client.send_message("/live/track/set/name", (x, name))
                except Exception as e:
                    print("failed to set instrument name", e)
                    traceback.print_exc()

    def get_output_channel(x):
        try:
            chan = client.query("/live/track/get/output_routing_channel", (x,))[1]
            print(chan)
            chan = chan.rsplit(" ", 1)[-1]
            return int(chan) - 1
        except Exception as e:
            print("Failed to set GM-MIDI instrument. Couldn't get output channel:", e)
            return None

    def set_instrument(x, y, instrument):
        try:
            print("setting instrument to", instrument)
            filename = operator_map[instrument]
            print("OP Patch:", filename)
            names, values = pickle.load(open(f"./params/Operator/{filename}.pkl", "rb"))
            client.send_message("/live/device/set/parameters/value", (x, 0, *values))
            client.send_message("/live/track/set/name", (x, filename))
        except Exception as e:
            print()
            print("failed to set instrument", e)
            # print traceback

            traceback.print_exc()

    def is_midi_track(x):
        try:
            return client.query("/live/track/get/has_midi_input", (x,))[1]
        except:
            return None


# x,y -> prompt
WAIT_LIST = {}
SPINNER_GRID = defaultdict(lambda: itertools.cycle(["-", "/", "|", "\\"]))


class Gen:
    def add_prompt(x, y, prompt):
        filename = Gen.get_filename(x, y)
        if os.path.exists(filename + ".midi"):
            os.remove(filename + ".midi")

        WAIT_LIST[(x, y)] = prompt

    def wait_list():
        files = []
        for (x, y), prompt in WAIT_LIST.items():
            files.append((x, y, Gen.get_filename(x, y)))
        return files

    def finished(x, y):
        prompt = WAIT_LIST[(x, y)]
        del WAIT_LIST[(x, y)]
        return prompt

    def get_filename(x, y):
        gen_dir = os.path.join(os.path.dirname(__file__), "gens")
        return os.path.join(gen_dir, f"{x}-{y}")


# async generate MIDI using GPT
def start_thread_prompt(x, y, prompt):
    the_thread = threading.Thread(
        target=make_midi, args=(prompt, Gen.get_filename(x, y))
    )
    the_thread.start()


def start_thread_modify(x, y, prompt, existing_abc):
    the_thread = threading.Thread(
        target=modify_midi, args=(prompt, existing_abc, Gen.get_filename(x, y))
    )
    the_thread.start()


def extract_abc_title(abc):
    title = re.search(r"^T:(.*)$", abc, re.MULTILINE).group(1)
    return title


def event_loop():
    files = Gen.wait_list()
    for x, y, filename in files:
        if os.path.exists(filename + ".midi"):
            prompt = Gen.finished(x, y)
            print("finished generating", filename)
            print("inserting clip name =", prompt)
            with open(filename + ".abc", "r") as f:
                f.read()

            Clip.insert_clip(x, y, filename + ".midi", prompt)
        else:
            Clip.set_name(x, y, SPINNER_GRID[(x, y)].__next__())

    x, y, name = Clip.get_curr_name()
    if Clip.is_midi_track(x) is False:
        print("not a midi track")
        return
    if name is None:
        return
    if name.startswith("AI"):
        # print(f'clip name: "{name}"     (already starts with "AI:")')
        pass
    elif len(name) <= 1:
        # print('spinner or empty clip name')
        pass
    else:
        print(f'AI needed clip found: "{name}"')
        prompt = name
        if os.path.exists(Gen.get_filename(x, y) + ".abc"):
            # ADD CHECK FOR THERE's MIDI NOTES IN CURR CLIP
            try:
                notes = len(Clip.get_notes(x, y)) > 0
            except Exception as e:
                print("error getting notes:", e)
                notes = False
            if notes:
                print("already generated", Gen.get_filename(x, y))
                Gen.add_prompt(x, y, prompt)
                with open(Gen.get_filename(x, y) + ".abc", "r") as f:
                    existing_abc = f.read()
                start_thread_modify(x, y, prompt, existing_abc)
            else:
                Gen.add_prompt(x, y, prompt)
                start_thread_prompt(x, y, prompt)
        else:
            Gen.add_prompt(x, y, prompt)
            start_thread_prompt(x, y, prompt)


print("waiting for named MIDI clip to appear..")
while True:
    event_loop()
    time.sleep(0.1)
