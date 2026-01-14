import os
import re
from copy import deepcopy

from chatlib import get_completion
from mido import MidiFile

MODEL_NAME = "gpt-5-mini"
from prompt import SYSTEM_PROMPT


import mtxt
from correct_mtxt import correct_mtxt

def extract_message(message):
    match = re.search(r"```mtxt(.*?)```", message, flags=re.DOTALL | re.M)
    print(match)
    if match:
        message = match.group(1)
    else:
        print("no match so using whole string")
    message = "\n".join([x for x in message.split("\n") if x.strip() != ""])
    
    # Apply auto-corrections to fix common LLM mistakes
    message = correct_mtxt(message)
    
    return message



def make_midi(prompt, filename, DEBUG=False):
    print("START MAKE MIDI", prompt, filename)
    if not DEBUG:
        print(">>>>> getting response")
        prompt = f"""Write mtxt notation for "{prompt}"""
        response = get_completion(
            prompt, system=SYSTEM_PROMPT, model_name=MODEL_NAME, frequency_penalty=0.3
        )
        print(">>>>> raw response")
        print(response)

        message = response.choices[0].message.content

    message = extract_message(message)
    print(message)
    try:
        mtxt.parse(message).to_midi(f"{filename}.midi")
    except Exception as e:
        print(f"Failed to parse MTXT: {e}")


def modify_midi(prompt, existing_mtxt, filename, DEBUG=False):
    print("START modify MIDI", prompt, filename)
    if not DEBUG:
        print(">>>>> getting response")
        message = f"""```Modify the title AND CHANGE THE NOTES to make a new mtxt with this instruction: "{prompt}"
Here is the previous mtxt notation:
```mtxt\n{existing_mtxt}\n```\n"""
        response = get_completion(
            message, system=SYSTEM_PROMPT, frequency_penalty=0.6, model_name=MODEL_NAME
        )
        print(">>>>> raw response")
        print(response)
        message = response.choices[0].message.content
    message = extract_message(message)
    print(message)
    try:
        mtxt.parse(message).to_midi(f"{filename}.midi")
    except Exception as e:
        print(f"Failed to parse MTXT: {e}")


def midifile_to_notes(midifile):
    note_ons = {}
    full_notes = []
    t = 0.0
    instrument = None
    for msg in midifile:
        if msg.type == "note_on":
            note_ons[msg.note] = deepcopy(msg)
            note_ons[msg.note].time = t
        if msg.type == "note_off":
            assert msg.note in note_ons
            prev_msg = note_ons[msg.note]
            full_notes.append(
                (
                    msg.note,
                    prev_msg.velocity,
                    prev_msg.time,
                    t - prev_msg.time + msg.time,
                )
            )
        if msg.type == "program_change":
            if instrument is None:
                print("setting instrument", msg.program)
                instrument = msg.program
            else:
                print("already set instrument", msg.program)
        t += msg.time
    t -= msg.time
    return full_notes, round(t), instrument


if __name__ == "__main__":
    make_midi("Rock riff", "./gens/test")

    with open("./gens/test.abc") as f:
        abc = f.read()
        print(abc)
    import pyperclip

    pyperclip.copy(abc)

    midifile = MidiFile('./gens/test.midi')

    full_notes, length, instrument = midifile_to_notes(midifile)