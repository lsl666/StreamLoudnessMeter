import os
import ctypes
import platform
import importlib.resources as resources
from ctypes import c_int, c_uint, c_ulong, c_double, c_void_p, POINTER, c_float, c_size_t
import numpy as np
from enum import IntFlag

def get_lib_path():
    """Return the path to the ebur128 library."""
    system = platform.system()
    if system == 'Darwin':
        lib_ext = '.dylib'
    elif system == 'Linux':
        lib_ext = '.so'
    elif system == 'Windows':
        lib_ext = '.dll'
    else:
        raise RuntimeError(f'Unsupported platform: {system}')

    lib_name = f'libebur128{lib_ext}'
    lib_path = None

    # First, try to find the library in the package's libs directory
    try:
        with resources.files(__package__).joinpath('libs') as lib_dir:
            candidate = lib_dir / lib_name
            if candidate.exists():
                lib_path = str(candidate)
    except (ImportError, FileNotFoundError, ModuleNotFoundError):
        # Fallback for development/editable installs
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        package_lib_path = os.path.join(current_file_dir, 'libs', lib_name)
        if os.path.exists(package_lib_path):
            lib_path = package_lib_path
        else:
            # Try to find it in the thirdparty build directory (for development)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir)))
            build_lib_path = os.path.join(project_root, 'thirdparty', 'libebur128', 
                                         'cmake-build-release', lib_name)
            if os.path.exists(build_lib_path):
                lib_path = build_lib_path

    # Fall back to environment variable if provided
    if lib_path is None:
        lib_path = os.environ.get('EBUR128_LIB_PATH')

    if lib_path is None:
        raise FileNotFoundError(
            f'Could not find {lib_name} library. '
            'Please build it in thirdparty/libebur128/cmake-build-release/ '
            'or copy it to src/stream_loudness_meter/libs/'
        )
    return lib_path

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
            lib_path = get_lib_path()
        self.lib = ctypes.CDLL(lib_path)
        self._setup_functions()
        self.state = self.lib.ebur128_init(c_uint(channels), c_ulong(samplerate), c_int(mode))
        if not self.state:
            raise Ebur128Error('Failed to initialize ebur128_state')

    def _setup_functions(self):
        self.lib.ebur128_init.restype = c_void_p
        self.lib.ebur128_init.argtypes = [c_uint, c_ulong, c_int]

        self.lib.ebur128_destroy.restype = None
        self.lib.ebur128_destroy.argtypes = [POINTER(c_void_p)]

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

    def destroy(self):
        """Explicitly destroy the ebur128 state."""
        if hasattr(self, 'state') and self.state:
            # ebur128_destroy expects a double pointer (ebur128_state**)
            state_ptr = c_void_p(self.state)
            self.lib.ebur128_destroy(ctypes.byref(state_ptr))
            self.state = None
    
    def __del__(self):
        """Clean up resources when object is garbage collected."""
        try:
            self.destroy()
        except Exception as e:
            # Log the error but don't raise - destructors should not raise
            import sys
            if hasattr(sys, 'stderr'):
                sys.stderr.write(f"Warning: Failed to destroy ebur128_state: {e}\n")
