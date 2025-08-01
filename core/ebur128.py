import os
import ctypes
from ctypes import c_int, c_uint, c_ulong, c_double, c_void_p, POINTER, c_float, c_size_t
import numpy as np
from enum import IntFlag

# Default dynamic library path
DEFAULT_LIB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'thirdparty', 'libebur128', 'cmake-build-release', 'libebur128.1.2.6.dylib')

class Ebur128Mode(IntFlag):
    """EBU R128 processing modes, matching the C enum."""
    EBUR128_MODE_M = (1 << 0)
    EBUR128_MODE_S = (1 << 1) | EBUR128_MODE_M
    EBUR128_MODE_I = (1 << 2) | EBUR128_MODE_M
    EBUR128_MODE_LRA = (1 << 3) | EBUR128_MODE_S
    EBUR128_MODE_SAMPLE_PEAK = (1 << 4) | EBUR128_MODE_M
    EBUR128_MODE_TRUE_PEAK = (1 << 5) | EBUR128_MODE_M | EBUR128_MODE_SAMPLE_PEAK
    EBUR128_MODE_HISTOGRAM = (1 << 6)

class Ebur128Error(Exception):
    """Custom exception for EBU R128 errors."""
    EBUR128_SUCCESS = 0
    EBUR128_ERROR_NOMEM = 1
    EBUR128_ERROR_INVALID_MODE = 2
    EBUR128_ERROR_INVALID_CHANNEL_INDEX = 3
    EBUR128_ERROR_NO_CHANGE = 4

class Ebur128:
    def __init__(self, channels, samplerate, mode, lib_path=None):
        self.channels = channels
        if lib_path is None:
            lib_path = os.environ.get('EBUR128_LIB_PATH', DEFAULT_LIB_PATH)
        self.lib = ctypes.CDLL(lib_path)
        self._setup_functions()
        self.state = self.lib.ebur128_init(c_uint(channels), c_ulong(samplerate), c_int(mode))
        if not self.state:
            raise Ebur128Error('Failed to initialize ebur128_state')

    def _setup_functions(self):
        self.lib.ebur128_init.restype = c_void_p
        self.lib.ebur128_init.argtypes = [c_uint, c_ulong, c_int]

        self.lib.ebur128_destroy.restype = None
        self.lib.ebur128_destroy.argtypes = [c_void_p]

        self.lib.ebur128_add_frames_float.restype = c_int
        self.lib.ebur128_add_frames_float.argtypes = [c_void_p, POINTER(c_float), c_size_t]

        self.lib.ebur128_loudness_global.restype = c_int
        self.lib.ebur128_loudness_global.argtypes = [c_void_p, POINTER(c_double)]

        self.lib.ebur128_loudness_momentary.restype = c_int
        self.lib.ebur128_loudness_momentary.argtypes = [c_void_p, POINTER(c_double)]

        self.lib.ebur128_loudness_shortterm.restype = c_int
        self.lib.ebur128_loudness_shortterm.argtypes = [c_void_p, POINTER(c_double)]

    def add_frames_float(self, frames):
        arr = np.ascontiguousarray(frames, dtype=np.float32)
        frame_count = arr.size // self.channels
        c_arr = arr.ctypes.data_as(POINTER(c_float))
        res = self.lib.ebur128_add_frames_float(self.state, c_arr, frame_count)
        if res != 0:
            raise Ebur128Error('ebur128_add_frames_float failed')

    def loudness_global(self):
        out = c_double()
        res = self.lib.ebur128_loudness_global(self.state, ctypes.byref(out))
        if res != 0:
            raise Ebur128Error('ebur128_loudness_global failed')
        return out.value

    def loudness_momentary(self):
        out = c_double()
        res = self.lib.ebur128_loudness_momentary(self.state, ctypes.byref(out))
        if res != 0:
            raise Ebur128Error('ebur128_loudness_momentary failed')
        return out.value

    def loudness_shortterm(self):
        out = c_double()
        res = self.lib.ebur128_loudness_shortterm(self.state, ctypes.byref(out))
        if res != 0:
            raise Ebur128Error('ebur128_loudness_shortterm failed')
        return out.value

    def __del__(self):
        try:
            if hasattr(self, 'state') and self.state:
                self.lib.ebur128_destroy(self.state)
        except Exception as e:
            print("Failed to destroy ebur128_state: %s" % e)
