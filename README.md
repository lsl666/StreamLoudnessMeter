# StreamLoudnessMeter

A Python library for measuring audio loudness using the EBU R128 standard.

## Installation

### From Source (GitHub)

Since this package is not yet published to PyPI, you need to install it from source:

1. **Clone the repository with submodules:**
```bash
git clone --recursive https://github.com/lsl666/StreamLoudnessMeter.git
cd StreamLoudnessMeter
```

2. **Install the package:**
```bash
pip install .
```

Or for development (editable installation):
```bash
pip install -e .
```

### Building from Source

If you want to build the wheel yourself:
```bash
python -m build
pip install dist/*.whl
```

### Requirements

- Python 3.7+
- CMake 3.18+
- C compiler (gcc/clang on Linux/macOS, MSVC on Windows)
- NumPy

## Usage

After installation, you can import and use the library:

```python
import numpy as np
from stream_loudness_meter import Ebur128, Ebur128Mode

# Configuration
channels = 2  # stereo
samplerate = 48000  # 48 kHz
mode = Ebur128Mode.EBUR128_MODE_I | Ebur128Mode.EBUR128_MODE_S  # Integrated + Short-term

# Create an instance
ebur = Ebur128(channels, samplerate, mode)

# Generate or load your audio (example with sine wave)
duration = 3.0  # seconds
t = np.linspace(0, duration, int(samplerate * duration))
audio_left = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz
audio_right = 0.5 * np.sin(2 * np.pi * 554.37 * t)  # 554.37 Hz

# Interleave channels for processing
audio_data = np.column_stack([audio_left, audio_right]).flatten().astype(np.float32)

# Process audio frames
ebur.add_frames_float(audio_data)

# Get loudness measurements
global_loudness = ebur.loudness_global()
shortterm_loudness = ebur.loudness_shortterm()

print(f"Integrated Loudness: {global_loudness:.2f} LUFS")
print(f"Short-term Loudness: {shortterm_loudness:.2f} LUFS")
```

### Available Modes

- `EBUR128_MODE_M` - Momentary loudness (400ms window)
- `EBUR128_MODE_S` - Short-term loudness (3s window) 
- `EBUR128_MODE_I` - Integrated/Global loudness
- `EBUR128_MODE_LRA` - Loudness range
- `EBUR128_MODE_SAMPLE_PEAK` - Sample peak
- `EBUR128_MODE_TRUE_PEAK` - True peak
- `EBUR128_MODE_HISTOGRAM` - Histogram mode

Modes can be combined using the bitwise OR operator (`|`).

### Processing Audio Files

For a complete example of processing WAV files, see the `example/wav_loudness_example.py` file.
