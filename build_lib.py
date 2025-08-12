#!/usr/bin/env python3
"""
Cross-platform build script for libebur128 dynamic library.
Works on macOS, Linux, and Windows.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_library_extension():
    """Get the appropriate library extension for the current platform."""
    system = platform.system()
    if system == 'Darwin':
        return '.dylib'
    elif system == 'Linux':
        return '.so'
    elif system == 'Windows':
        return '.dll'
    else:
        raise RuntimeError(f'Unsupported platform: {system}')


def get_cmake_generator():
    """Get the appropriate CMake generator for the current platform."""
    system = platform.system()
    if system == 'Windows':
        # Check if Visual Studio is available
        try:
            subprocess.run(['cl'], capture_output=True, check=False)
            return 'Visual Studio 17 2022'  # You can adjust the version
        except FileNotFoundError:
            # Fall back to MinGW if available
            try:
                subprocess.run(['gcc', '--version'], capture_output=True, check=True)
                return 'MinGW Makefiles'
            except (FileNotFoundError, subprocess.CalledProcessError):
                return 'NMake Makefiles'
    else:
        # Unix-like systems use Makefiles by default
        return 'Unix Makefiles'


def get_cpu_count():
    """Get the number of CPU cores for parallel compilation."""
    try:
        return os.cpu_count() or 1
    except:
        return 1


def build_library():
    """Build the libebur128 library."""
    # Get project root
    project_root = Path(__file__).parent.absolute()
    libebur128_dir = project_root / 'thirdparty' / 'libebur128'
    build_dir = libebur128_dir / 'cmake-build-release'
    
    print(f"Building libebur128 in {build_dir}...")
    
    # Create build directory
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to build directory
    original_dir = os.getcwd()
    os.chdir(build_dir)
    
    try:
        # Configure with CMake
        cmake_args = [
            'cmake',
            '..',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DBUILD_SHARED_LIBS=ON'
        ]
        
        # Add generator for Windows
        if platform.system() == 'Windows':
            generator = get_cmake_generator()
            cmake_args.extend(['-G', generator])
            # For 64-bit builds on Windows
            if 'Visual Studio' in generator:
                cmake_args.extend(['-A', 'x64'])
        
        print(f"Running CMake: {' '.join(cmake_args)}")
        result = subprocess.run(cmake_args, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"CMake configuration failed:\n{result.stderr}")
            return False
        
        # Build the library
        build_args = ['cmake', '--build', '.', '--config', 'Release']
        
        # Add parallel build option
        cpu_count = get_cpu_count()
        if platform.system() != 'Windows' or 'Visual Studio' not in get_cmake_generator():
            build_args.extend(['--', f'-j{cpu_count}'])
        else:
            build_args.extend(['--', f'/maxcpucount:{cpu_count}'])
        
        print(f"Building with: {' '.join(build_args)}")
        result = subprocess.run(build_args, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Build failed:\n{result.stderr}")
            return False
        
        print("Build successful!")
        return True
        
    finally:
        os.chdir(original_dir)


def copy_library():
    """Copy the built library to the Python package."""
    project_root = Path(__file__).parent.absolute()
    build_dir = project_root / 'thirdparty' / 'libebur128' / 'cmake-build-release'
    target_dir = project_root / 'src' / 'stream_loudness_meter' / 'libs'
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Find and copy the library
    lib_ext = get_library_extension()
    lib_name = f'libebur128{lib_ext}'
    
    # On Windows, the library might be in a Release subdirectory
    if platform.system() == 'Windows':
        possible_paths = [
            build_dir / 'Release' / lib_name,
            build_dir / 'Release' / 'ebur128.dll',  # Sometimes it's named without 'lib' prefix
            build_dir / lib_name,
            build_dir / 'ebur128.dll',
            build_dir / 'ebur128' / 'Release' / 'ebur128.dll',
            build_dir / 'ebur128' / 'ebur128.dll',
        ]
    else:
        possible_paths = [
            build_dir / lib_name,
            build_dir / 'ebur128' / lib_name,  # Sometimes in subdirectory
        ]
    
    source_path = None
    for path in possible_paths:
        if path.exists():
            source_path = path
            break
    
    if source_path is None:
        print(f"Error: Could not find the built library!")
        print(f"Searched in: {[str(p) for p in possible_paths]}")
        return False
    
    # Copy the library
    target_path = target_dir / lib_name
    print(f"Copying {source_path} to {target_path}...")
    shutil.copy2(source_path, target_path)
    
    # On Windows, also copy any required DLLs (if they exist)
    if platform.system() == 'Windows':
        # Copy MSVC runtime libraries if they exist in the build directory
        for dll in build_dir.glob('*.dll'):
            if dll.name != lib_name and 'msvc' in dll.name.lower():
                print(f"Also copying {dll.name}...")
                shutil.copy2(dll, target_dir)
    
    print(f"Library copied to {target_dir}/")
    return True


def main():
    """Main build process."""
    print(f"Building libebur128 for {platform.system()}...")
    print("=" * 50)
    
    # Check if CMake is available
    try:
        result = subprocess.run(['cmake', '--version'], capture_output=True, text=True)
        print(f"Found CMake: {result.stdout.split()[2] if result.returncode == 0 else 'Unknown version'}")
    except FileNotFoundError:
        print("Error: CMake is not installed or not in PATH!")
        print("Please install CMake from https://cmake.org/download/")
        sys.exit(1)
    
    # Build the library
    if not build_library():
        print("Build failed!")
        sys.exit(1)
    
    # Copy to Python package
    if not copy_library():
        print("Failed to copy library!")
        sys.exit(1)
    
    print("=" * 50)
    print("Build complete! Library copied to src/stream_loudness_meter/libs/")
    print("")
    print("You can now install the Python package with:")
    print("  pip install -e .")
    print("Or build a wheel with:")
    print("  pip install build")
    print("  python -m build")


if __name__ == '__main__':
    main()
