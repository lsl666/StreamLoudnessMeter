#!/usr/bin/env python
"""Test script to verify the wheel installation and library loading."""

import os
import sys

def test_wheel_installation():
    print("=" * 60)
    print("Testing wheel installation of stream-loudness-meter")
    print("=" * 60)
    
    # Test 1: Import the package
    try:
        import stream_loudness_meter
        print("✓ Package imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import package: {e}")
        return False
    
    # Test 2: Check package location
    package_dir = os.path.dirname(stream_loudness_meter.__file__)
    print(f"✓ Package location: {package_dir}")
    
    # Test 3: Check libs directory exists
    libs_dir = os.path.join(package_dir, 'libs')
    if os.path.exists(libs_dir):
        print(f"✓ libs directory exists: {libs_dir}")
    else:
        print(f"✗ libs directory not found: {libs_dir}")
        return False
    
    # Test 4: Check for library files
    lib_files = os.listdir(libs_dir)
    dylib_files = [f for f in lib_files if f.endswith('.dylib')]
    if dylib_files:
        print(f"✓ Found library files: {dylib_files}")
    else:
        print(f"✗ No .dylib files found in libs directory")
        return False
    
    # Test 5: Import the ebur128 module
    try:
        from stream_loudness_meter import ebur128
        print("✓ ebur128 module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ebur128 module: {e}")
        return False
    
    # Test 6: Check library path function
    try:
        lib_path = ebur128.get_lib_path()
        print(f"✓ Library path from get_lib_path(): {lib_path}")
        if os.path.exists(lib_path):
            print(f"✓ Library file exists at: {lib_path}")
        else:
            print(f"✗ Library file not found at: {lib_path}")
            return False
    except Exception as e:
        print(f"✗ Failed to get library path: {e}")
        return False
    
    # Test 7: Try to load the library via ctypes
    try:
        import ctypes
        lib = ctypes.CDLL(lib_path)
        print(f"✓ Library loaded successfully via ctypes")
    except Exception as e:
        print(f"✗ Failed to load library: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! The library is properly shipped in the wheel.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_wheel_installation()
    sys.exit(0 if success else 1)
