# Cross-Platform Build Verification Guide

This document describes how to build and verify the StreamLoudnessMeter library across Linux, macOS, and Windows platforms.

## Supported Platforms

- **Linux**: Ubuntu 20.04+ (gcc/clang)
- **macOS**: 10.15+ (clang/Apple clang)
- **Windows**: Windows 10+ (MSVC 2019+)

## Prerequisites

### All Platforms
- Python 3.7+
- CMake 3.18+
- Git with submodule support

### Platform-Specific

#### Linux
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build
# For clang support:
sudo apt-get install -y clang
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install
# Install CMake and Ninja via Homebrew
brew install cmake ninja
```

#### Windows
- Install Visual Studio 2019 or later with C++ development tools
- Or install MinGW-w64 for GCC support
- CMake (can be installed via Python: `pip install cmake`)

## Local Build and Verification

### Quick Build
```bash
# Clone repository with submodules
git clone --recursive https://github.com/lsl666/StreamLoudnessMeter.git
cd StreamLoudnessMeter

# Build the library
python build_lib.py

# Run local verification tests
python test_cross_platform_build.py
```

### Manual Build Steps

#### 1. Build Native Library
```bash
cd thirdparty/libebur128
mkdir -p cmake-build-release
cd cmake-build-release

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON

# Build
cmake --build . --config Release -j$(nproc)  # Linux/macOS
cmake --build . --config Release             # Windows

# Copy to Python package
cd ../../../
cp thirdparty/libebur128/cmake-build-release/libebur128.* src/stream_loudness_meter/libs/
```

#### 2. Build Python Wheel
```bash
pip install build
python -m build --wheel
```

## GitHub Actions CI/CD

The project includes comprehensive GitHub Actions workflows for automated cross-platform testing.

### Workflow Features

1. **Multi-Platform Testing**
   - Linux: gcc and clang compilers
   - macOS: Apple clang
   - Windows: MSVC

2. **Python Version Matrix**
   - Tests against Python 3.8, 3.10, and 3.12

3. **Automated Tests**
   - Library compilation
   - Python binding verification
   - Wheel building and packaging
   - Cross-platform wheel compatibility

### Running GitHub Actions

Push to main/master/develop branches or create a pull request to trigger automated builds:

```yaml
on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:  # Manual trigger
```

## Windows DLL Bundling

On Windows, the library uses ctypes to load the DLL. The loading mechanism follows this priority:

1. Check package's `libs` directory (for installed wheels)
2. Check development build directory
3. Use `EBUR128_LIB_PATH` environment variable if set

### DLL Loading Strategy

The Python binding (`ebur128.py`) implements smart DLL discovery:

```python
def get_lib_path():
    # 1. Try package directory (wheel installation)
    # 2. Try development directory
    # 3. Fall back to environment variable
    # 4. Raise error if not found
```

### Ensuring DLL is Found

For Windows distributions, the DLL is bundled in the same directory as the Python module, ensuring ctypes can find it without PATH modifications.

## Verification Tests

### 1. Library Loading Test
Verifies the native library can be loaded via ctypes and expected functions are available.

### 2. Python Bindings Test
Tests basic functionality:
- Creating Ebur128 instances
- Processing audio frames
- Measuring loudness
- Proper cleanup (no memory leaks)

### 3. Wheel Build Test
Verifies wheel packaging includes the native library.

### 4. Wheel Installation Test
Tests installation in a clean virtual environment.

## Troubleshooting

### Common Issues

#### Linux: Library Not Found
```bash
# Check library dependencies
ldd src/stream_loudness_meter/libs/libebur128.so
# Install missing dependencies if needed
sudo apt-get install -y libstdc++6
```

#### macOS: Code Signing Issues
```bash
# For development, allow unsigned libraries
xattr -d com.apple.quarantine src/stream_loudness_meter/libs/libebur128.dylib
```

#### Windows: MSVC Runtime Missing
Ensure Visual C++ Redistributables are installed:
- Download from Microsoft: [VC++ Redistributables](https://support.microsoft.com/en-us/help/2977003/)

### Memory Management

The library properly handles memory cleanup using a double-pointer pattern in the C library:

```c
void ebur128_destroy(ebur128_state** st);
```

The Python wrapper correctly implements this:

```python
def destroy(self):
    if hasattr(self, 'state') and self.state:
        state_ptr = c_void_p(self.state)
        self.lib.ebur128_destroy(ctypes.byref(state_ptr))
        self.state = None
```

## Performance Considerations

- **Linux**: Best performance with gcc -O3 optimization
- **macOS**: Use Apple Silicon native builds for M1/M2 Macs
- **Windows**: MSVC typically provides better performance than MinGW

## Platform-Specific Wheels

When distributing, consider building platform-specific wheels:

```bash
# Linux
python -m build --wheel  # Creates manylinux wheel

# macOS
python -m build --wheel  # Creates macosx wheel

# Windows
python -m build --wheel  # Creates win_amd64 wheel
```

## Testing Matrix

| Platform | Compiler | Python | Status |
|----------|----------|--------|--------|
| Ubuntu 20.04 | gcc | 3.8, 3.10, 3.12 | ✅ |
| Ubuntu 20.04 | clang | 3.8, 3.10, 3.12 | ✅ |
| macOS 12+ | clang | 3.8, 3.10, 3.12 | ✅ |
| Windows 10 | MSVC | 3.8, 3.10, 3.12 | ✅ |

## Contributing

When contributing changes that affect the build system:

1. Test locally using `test_cross_platform_build.py`
2. Ensure GitHub Actions pass for all platforms
3. Update this documentation if build process changes

## License

The build system and Python bindings are MIT licensed. The libebur128 library has its own license (see thirdparty/libebur128/LICENSE).
