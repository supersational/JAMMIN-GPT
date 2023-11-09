import rtmidi


def set_instrument(channel, program_number):
    print("setting instrument", channel, program_number)
    # Define the program change message
    # channel = 0  # MIDI channel (0-15)
    # program_number = 4  # Program number (0-127)

    # Create an rtmidi output object
    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    # print(available_ports)
    # virtual_port_name = "FluidSynth virtual port"
    virtual_port_name = "FluidSynth"

    # Find the virtual MIDI port in the list of available ports
    virtual_port = None
    for port in available_ports:
        if virtual_port_name in port:
            virtual_port = midiout.open_port(available_ports.index(port))
            break

    if virtual_port:
        # Send the program change message to the virtual MIDI port
        message = [0xC0 | channel, program_number]
        virtual_port.send_message(message)
        print(
            f"Sent program change to channel {channel}, program number {program_number} on port {virtual_port_name}"
        )
    else:
        print(f"Virtual MIDI port {virtual_port_name} not found in available ports.")

    # Close the virtual MIDI port
    virtual_port.close_port()
