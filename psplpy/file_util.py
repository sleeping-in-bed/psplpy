import datetime
import hashlib
import os
import re
import shutil

import interact_util
import other_util


def read_text_in_file(file_path: str, encoding: str = 'utf-8'):
    with open(file_path, encoding=encoding) as file:
        content = file.read()
    return content


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
    create_dir(os.path.dirname(dst_path))
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


def get_file_size(file_path: str, ignore_not_exist: bool = False) -> int:
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


class PyHash:
    md5 = 'md5'
    sha1 = 'sha1'
    sha256 = 'sha256'
    sha512 = 'sha512'
    blake2b = 'blake2b'
    blake2s = 'blake2s'
    hash_algorithms_list = [md5, sha1, sha256, sha512, blake2b, blake2s]

    def __init__(self, hash_algorithm: str, show_rate_of_progress: bool = False):
        if type(hash_algorithm) == str and hash_algorithm in self.hash_algorithms_list:
            self.hash_algorithm = eval(f'hashlib.{hash_algorithm}()')
        else:
            raise ValueError(f'{hash_algorithm} no support')
        self.show_rate_of_progress = show_rate_of_progress

    def cal_data_hash(self, data: object, encoding: str = 'utf-8') -> str:
        data = str(data).encode(encoding=encoding)
        self.hash_algorithm.update(data)
        return self.hash_algorithm.hexdigest()

    def cal_file_hash(self, file_path: str, block_size: int = 1024 * 1024 * 10) -> str:
        if self.show_rate_of_progress:
            file_size = get_file_size(file_path)
        with open(file_path, "rb") as f:
            if block_size:
                if self.show_rate_of_progress:
                    count = 0
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    self.hash_algorithm.update(data)
                    if self.show_rate_of_progress:
                        count += block_size
                        interact_util.progress_bar(progress=count / file_size)
                if self.show_rate_of_progress:
                    print()
            else:
                data = f.read()
                self.hash_algorithm.update(data)
        return self.hash_algorithm.hexdigest()


def get_current_user_dir() -> str:
    user_folder = os.path.expanduser('~')
    return user_folder


def create_hard_link(new_file: str, original_file: str) -> str:
    return other_util.run_command(f'mklink /h {new_file} {original_file}')


if __name__ == '__main__':
    pass
