import sys
import numpy as np
import soundfile as sf
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from stream_loudness_meter import Ebur128, Ebur128Mode

# 配置参数
AUDIO_PATH = os.path.expanduser('~/Downloads/testwav/Hotel California-Eagles.wav')  # 修改为你自己的音频路径
MODE = Ebur128Mode.EBUR128_MODE_I | Ebur128Mode.EBUR128_MODE_HISTOGRAM | Ebur128Mode.EBUR128_MODE_S  # 通常1=EBUR128_MODE_I, 可根据需要调整
FRAME_SIZE = 1024


def main():
    data, samplerate = sf.read(AUDIO_PATH, always_2d=True, dtype='float32')
    channels = data.shape[1]
    ebur = Ebur128(channels, samplerate, MODE)
    num_frames = data.shape[0]
    for i in range(0, num_frames, FRAME_SIZE):
        frames = data[i:i + FRAME_SIZE]
        # 展平成一维交错数组
        frames_interleaved = frames.flatten()
        ebur.add_frames_float(frames_interleaved)
    print('Global loudness (LUFS):', ebur.loudness_global())
    print('Momentary loudness (LUFS):', ebur.loudness_momentary())
    print('Short-term loudness (LUFS):', ebur.loudness_shortterm())


if __name__ == '__main__':
    main()
