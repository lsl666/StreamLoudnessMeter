"""
Stream Loudness Meter - Python bindings for libebur128.

This package provides Python bindings for the libebur128 library,
which implements the EBU R128 standard for loudness normalisation.
"""

from .ebur128 import Ebur128, Ebur128Mode, Ebur128Error

__all__ = ['Ebur128', 'Ebur128Mode', 'Ebur128Error']
__version__ = '0.1.0'
