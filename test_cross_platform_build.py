#!/usr/bin/env python3
"""
Local cross-platform build verification script.
Tests building and loading the library on Linux, macOS, and Windows.
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
from pathlib import Path
import ctypes


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def get_compiler_info():
    """Get information about available compilers."""
    system = platform.system()
    compilers = []
    
    if system in ['Linux', 'Darwin']:
        # Check for GCC
        try:
            result = subprocess.run(['gcc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                compilers.append(('gcc', version))
        except FileNotFoundError:
            pass
        
        # Check for Clang
        try:
            result = subprocess.run(['clang', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                compilers.append(('clang', version))
        except FileNotFoundError:
            pass
    
    elif system == 'Windows':
        # Check for MSVC
        try:
            result = subprocess.run(['cl'], capture_output=True, text=True)
            if 'Microsoft' in result.stderr:
                version = result.stderr.split('\n')[0]
                compilers.append(('msvc', version))
        except FileNotFoundError:
            pass
        
        # Check for MinGW GCC
        try:
            result = subprocess.run(['gcc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                compilers.append(('gcc (MinGW)', version))
        except FileNotFoundError:
            pass
    
    return compilers


def test_library_loading():
    """Test that the library can be loaded with ctypes."""
    print_section("Testing Library Loading")
    
    # Import the module to get the library path
    sys.path.insert(0, 'src')
    from stream_loudness_meter.ebur128 import get_lib_path
    
    try:
        lib_path = get_lib_path()
        print(f"Library path: {lib_path}")
        print(f"Library exists: {os.path.exists(lib_path)}")
        
        if not os.path.exists(lib_path):
            print("ERROR: Library file does not exist!")
            return False
        
        # Get file size
        file_size = os.path.getsize(lib_path)
        print(f"Library size: {file_size:,} bytes")
        
        # Try to load with ctypes
        print("\nAttempting to load library with ctypes...")
        lib = ctypes.CDLL(lib_path)
        print("✓ Successfully loaded library with ctypes")
        
        # Check for some expected symbols
        expected_functions = [
            'ebur128_init',
            'ebur128_destroy',
            'ebur128_add_frames_float',
            'ebur128_loudness_global'
        ]
        
        print("\nChecking for expected functions:")
        for func_name in expected_functions:
            try:
                func = getattr(lib, func_name)
                print(f"  ✓ {func_name} found")
            except AttributeError:
                print(f"  ✗ {func_name} NOT found")
                return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to load library: {e}")
        return False


def test_python_bindings():
    """Test the Python bindings."""
    print_section("Testing Python Bindings")
    
    try:
        # Make sure src is in path
        if 'src' not in sys.path:
            sys.path.insert(0, 'src')
        
        print("Importing stream_loudness_meter...")
        from stream_loudness_meter import Ebur128, Ebur128Mode, Ebur128Error
        print("✓ Successfully imported module")
        
        print("\nTesting basic functionality...")
        import numpy as np
        
        # Create a test signal
        sample_rate = 48000
        duration = 0.5
        channels = 2
        samples = int(sample_rate * duration)
        
        # Generate a simple sine wave
        t = np.linspace(0, duration, samples)
        frequency = 440.0  # A4 note
        signal = np.sin(2 * np.pi * frequency * t) * 0.5
        
        # Create stereo signal
        stereo_signal = np.column_stack([signal, signal]).flatten()
        
        print(f"Created test signal: {channels} channels, {sample_rate} Hz, {duration} seconds")
        
        # Initialize meter
        meter = Ebur128(channels, sample_rate, Ebur128Mode.EBUR128_MODE_I)
        print("✓ Successfully created Ebur128 instance")
        
        # Process frames
        meter.add_frames_float(stereo_signal)
        print("✓ Successfully processed audio frames")
        
        # Get loudness
        loudness = meter.loudness_global()
        print(f"✓ Measured loudness: {loudness:.2f} LUFS")
        
        # Cleanup
        del meter
        print("✓ Successfully cleaned up")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wheel_build():
    """Test building a wheel package."""
    print_section("Testing Wheel Build")
    
    try:
        # Check if build module is available
        try:
            import build as build_module
        except ImportError:
            print("Installing 'build' package...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'build'], check=True)
        
        # Clean previous builds
        dist_dir = Path('dist')
        if dist_dir.exists():
            print(f"Cleaning previous builds in {dist_dir}...")
            shutil.rmtree(dist_dir)
        
        print("Building wheel...")
        result = subprocess.run(
            [sys.executable, '-m', 'build', '--wheel'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"ERROR: Wheel build failed:\n{result.stderr}")
            return False
        
        # Check if wheel was created
        wheels = list(dist_dir.glob('*.whl'))
        if not wheels:
            print("ERROR: No wheel file was created")
            return False
        
        wheel_path = wheels[0]
        wheel_size = wheel_path.stat().st_size
        print(f"✓ Successfully built wheel: {wheel_path.name}")
        print(f"  Size: {wheel_size:,} bytes")
        
        # Check wheel contents
        print("\nChecking wheel contents...")
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract wheel (it's a zip file)
            import zipfile
            with zipfile.ZipFile(wheel_path, 'r') as zf:
                zf.extractall(tmpdir)
            
            # Look for the library file
            tmp_path = Path(tmpdir)
            system = platform.system()
            if system == 'Darwin':
                lib_pattern = '**/*.dylib'
            elif system == 'Linux':
                lib_pattern = '**/*.so'
            elif system == 'Windows':
                lib_pattern = '**/*.dll'
            else:
                lib_pattern = '**/*'
            
            libs = list(tmp_path.glob(lib_pattern))
            if libs:
                print(f"✓ Found {len(libs)} library file(s) in wheel:")
                for lib in libs:
                    rel_path = lib.relative_to(tmp_path)
                    print(f"    - {rel_path}")
            else:
                print(f"WARNING: No library files matching '{lib_pattern}' found in wheel")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wheel_installation():
    """Test installing and using the wheel in a clean environment."""
    print_section("Testing Wheel Installation")
    
    try:
        # Find the wheel
        dist_dir = Path('dist')
        wheels = list(dist_dir.glob('*.whl'))
        if not wheels:
            print("ERROR: No wheel file found. Run wheel build test first.")
            return False
        
        wheel_path = wheels[0].absolute()
        print(f"Testing wheel: {wheel_path.name}")
        
        # Create a temporary virtual environment
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_dir = Path(tmpdir) / 'test_venv'
            print(f"\nCreating virtual environment in {venv_dir}...")
            
            # Create venv
            subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
            
            # Get python executable in venv
            if platform.system() == 'Windows':
                venv_python = venv_dir / 'Scripts' / 'python.exe'
            else:
                venv_python = venv_dir / 'bin' / 'python'
            
            # Install wheel
            print(f"Installing wheel in virtual environment...")
            result = subprocess.run(
                [str(venv_python), '-m', 'pip', 'install', str(wheel_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"ERROR: Failed to install wheel:\n{result.stderr}")
                return False
            
            print("✓ Successfully installed wheel")
            
            # Test import in clean environment
            print("\nTesting import in clean environment...")
            test_script = '''
import sys
from stream_loudness_meter import Ebur128, Ebur128Mode
print("Import successful!")

# Test basic functionality
import numpy as np

sample_rate = 48000
duration = 0.5
channels = 2
samples = int(sample_rate * duration)

t = np.linspace(0, duration, samples)
frequency = 440.0
signal = np.sin(2 * np.pi * frequency * t) * 0.5
stereo_signal = np.column_stack([signal, signal]).flatten()

meter = Ebur128(channels, sample_rate, Ebur128Mode.EBUR128_MODE_I)
meter.add_frames_float(stereo_signal)
loudness = meter.loudness_global()
print(f"Loudness: {loudness:.2f} LUFS")
print("Functional test passed!")
'''
            
            result = subprocess.run(
                [str(venv_python), '-c', test_script],
                capture_output=True,
                text=True,
                cwd='/'  # Run from root to ensure no local imports
            )
            
            if result.returncode != 0:
                print(f"ERROR: Test failed:\n{result.stderr}")
                return False
            
            print(result.stdout)
            print("✓ All tests passed in clean environment")
            
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    print("\n" + "#" * 60)
    print("#  Cross-Platform Build Verification")
    print("#" * 60)
    
    # System information
    print_section("System Information")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Compiler information
    print("\nAvailable Compilers:")
    compilers = get_compiler_info()
    if compilers:
        for name, version in compilers:
            print(f"  - {name}: {version}")
    else:
        print("  No compilers found!")
    
    # Check if library is built
    print_section("Checking Library Build")
    lib_dir = Path('src/stream_loudness_meter/libs')
    if not lib_dir.exists():
        print(f"Library directory does not exist: {lib_dir}")
        print("Running build_lib.py...")
        result = subprocess.run([sys.executable, 'build_lib.py'])
        if result.returncode != 0:
            print("ERROR: Build failed!")
            sys.exit(1)
    else:
        libs = list(lib_dir.glob('*'))
        if libs:
            print(f"Found libraries in {lib_dir}:")
            for lib in libs:
                print(f"  - {lib.name} ({lib.stat().st_size:,} bytes)")
        else:
            print(f"No libraries found in {lib_dir}")
            print("Running build_lib.py...")
            result = subprocess.run([sys.executable, 'build_lib.py'])
            if result.returncode != 0:
                print("ERROR: Build failed!")
                sys.exit(1)
    
    # Run tests
    tests = [
        ("Library Loading", test_library_loading),
        ("Python Bindings", test_python_bindings),
        ("Wheel Build", test_wheel_build),
        ("Wheel Installation", test_wheel_installation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("Test Summary")
    all_passed = True
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name:.<30} {status}")
        if not success:
            all_passed = False
    
    print("\n" + "#" * 60)
    if all_passed:
        print("#  All tests PASSED! 🎉")
    else:
        print("#  Some tests FAILED ⚠️")
    print("#" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
