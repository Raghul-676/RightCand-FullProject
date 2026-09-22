import sounddevice as sd
import numpy as np

def callback(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata) * 10
    print("|" * int(volume_norm))

print("Speak into your microphone! Press Ctrl+C to stop.")
with sd.InputStream(callback=callback):
    sd.sleep(10000)
