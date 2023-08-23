import ctypes
import os
import sys
import glob

package_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(package_dir)

pydll = ctypes.CDLL(os.path.join(package_dir, r'lib\PyDll.dll'))

py_files = glob.glob(os.path.join(package_dir, "*.py"))
__all__ = [*py_files, pydll]