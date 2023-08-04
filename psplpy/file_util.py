import datetime
import os
import re
import shutil


def get_this_dir_abspath(__file__) -> str:
    """return the directory name where this function be used"""
    return os.path.dirname(os.path.abspath(__file__))


def create_file(file_path: str) -> None:
    """if file path doesn't exist, then create all directories on the path and the file"""
    if not os.path.exists(file_path):
        dir_name = os.path.dirname(file_path)
        if dir_name:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        open(file_path, 'w').close()


def create_dir(dir: str) -> None:
    """if directory doesn't exist, then create it"""
    if not os.path.isdir(dir):
        dir = os.path.dirname(dir)
    if not os.path.exists(dir):
        os.makedirs(dir)


def rename_duplicate_file(file_path: str) -> str:
    """if file name has existed, add (n) after the file name and return, or return the origin name"""
    count = 1
    while True:
        if os.path.exists(file_path):
            basename, ext = os.path.splitext(file_path)
            basename = re.sub(r"\(\d+\)$", "", basename)
            file_path = f'{basename}({count}){ext}'
        else:
            return file_path
        count = count + 1


def copy_file(src_path: str, dst_path: str) -> str:
    """copy file, if dst dir doesn't exist, create it, if dst file has existed, rename it"""
    create_dir(dst_path)
    # if dst file has existed, rename it
    dst_path = rename_duplicate_file(dst_path)
    # copy
    shutil.copy2(src_path, dst_path)
    return dst_path


def get_current_time_as_file_name(ext: str, format_str: str = None) -> str:
    """generate file name according to the current time"""
    if not format_str:
        format_str = "%Y%m%d_%H%M%S%f"
    file_name = datetime.datetime.now().strftime(format_str)
    if ext:
        if ext.startswith("."):
            file_name = f'{file_name}{ext}'
        else:
            file_name = f'{file_name}.{ext}'
    return rename_duplicate_file(file_name)


def get_file_size(file_path, ignore_not_exist: bool = False):
    """get file size by bytes"""
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        size_in_bytes = file_info.st_size
        return size_in_bytes
    else:
        if ignore_not_exist:
            return 0
        else:
            raise FileNotFoundError


if __name__ == '__main__':
    pass
