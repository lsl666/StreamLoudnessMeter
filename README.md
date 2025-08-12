# StreamLoudnessMeter

## Installation

You can install StreamLoudnessMeter using pip:

```bash
pip install stream-loudness-meter
```

## Usage

After installation, you can import and use the library:

```python
from stream_loudness_meter import Ebur128, Ebur128Mode

# Create an instance with your audio parameters
ebur = Ebur128(channels, samplerate, mode)

# Process audio frames
ebur.add_frames_float(audio_data)

# Get loudness measurements
global_loudness = ebur.loudness_global()
```

For a complete example, see the `example/wav_loudness_example.py` file.
