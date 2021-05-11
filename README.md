# sense-phue

Cochl.sense python client code fixed to control phillips hue smart lightbulb

This repository is split in two folders : 
- `cochl_sense` contains the source code of the cochlear.ai sense python client
- `examples` contains an example code

## Quick start

Go in `examples` folder

### Installation

If you want to inference **a stream**, you will need to install `portaudio` on your system.

To install pyaudio, you can follow the pyaudio documentation here  https://people.csail.mit.edu/hubert/pyaudio/


Make sure that dependencies are installed by running 
```
pip install -r requirements.txt
```

### Run code

Open sense-phue.py and put your `api_key` and your bridge's IP address.
Then run
```
python sense-phue.py
```
Make sure that your bridge is properly connected to this code.

Note that this code can be run on Linux or macOS. We currently don't support Windows OS.


## How it works

- Clap: The light is turned on.
- Finger_snap: Light color changes. (Red -> Green -> Blue -> White)
- Whistling: The light dims twice. 
- Whisper: Gradually go dark and eventually be turned off.
- Knock: The light is turned off.


