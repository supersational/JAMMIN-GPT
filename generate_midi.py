import os
import re
from copy import deepcopy

from chatlib import get_completion
from mido import MidiFile

MODEL_NUM = 4
SYSTEM = """You generate music in ABC notation, respond with notation between ```abc blocks and no other text.
Set MIDI-instrument using: %%MIDI program {GM number} (after the V: block) for drums set %%MIDI channel 10"""


def parse_file(filename):
    # /opt/homebrew/bin/abc2midi
    os.system(f"/opt/homebrew/bin/abc2midi {filename}.abc -o {filename}.midi")


def extract_message(message):
    match = re.search(r"```abc(.*?)```", message, flags=re.DOTALL | re.M)
    print(match)
    if match:
        message = match.group(1)
    else:
        print("no match so using whole string")
    message = "\n".join([x for x in message.split("\n") if x.strip() != ""])

    pattern = r'"([^"]*)"'  # Match anything inside double quotes
    message = re.sub(
        pattern, lambda x: '"' + re.sub(r",+", "", x.group(1)) + '"', message
    )

    return message


def make_midi(prompt, filename, DEBUG=False):
    """Generate a MIDI file from a given prompt.

    Args:
        prompt (str): The musical prompt to generate MIDI for.
        filename (str): The filename to save the MIDI file as.
        DEBUG (bool): Flag to enable debugging output.

    Returns:
        None
    """
    print("START MAKE MIDI", prompt, filename)
    if not DEBUG:
        print(">>>>> getting response")
        prompt = f"""Write ABC notation for "{prompt}"""
        response = get_completion(
            prompt, system=SYSTEM, model_num=MODEL_NUM, frequency_penalty=0.3
        )
        print(">>>>> raw response")
        print(response)

        message = response.choices[0].message.content

    message = extract_message(message)
    print(message)
    with open(f"{filename}.abc", "w") as f:
        f.write(message)
    parse_file(filename)


def modify_midi(prompt, existing_abc, filename, DEBUG=False):
    print("START modify MIDI", prompt, filename)
    if not DEBUG:
        print(">>>>> getting response")
        message = f"""```Modify the title AND CHANGE THE NOTES to make a new abc with this instruction: "{prompt}"
Here is the previous ABC notation:
```abc\n{existing_abc}\n```\n"""
        response = get_completion(
            message, system=SYSTEM, frequency_penalty=0.6, model_num=MODEL_NUM
        )
        print(">>>>> raw response")
        print(response)
        message = response.choices[0].message.content
    #     with open(f"{filename}.abc", "w") as f:
    #         f.write(message)
    # with open(f"{filename}.abc", "r") as f:
    #     message = f.read()
    message = extract_message(message)
    print(message)
    with open(f"{filename}.abc", "w") as f:
        f.write(message)
    parse_file(filename)


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