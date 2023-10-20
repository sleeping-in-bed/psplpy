import datetime
import hashlib
import os
import re
import shutil

import interact_util
import other_util

win_reserved_names_list = [
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    'CONIN$', 'CONOUT$', 'NUL', 'PRN',
]
added_reserved_suffix = '_win'


def recursive_splitext(name_with_ext: str) -> str:
    name = os.path.splitext(name_with_ext)
    if not name[1]:
        return name[0]
    else:
        return recursive_splitext(name[0])


def process_win_reserved_name(path: str, restore: bool) -> (bool, str):
    # 使用os.path.normpath()规范化路径
    normalized_path = os.path.normpath(path)
    # 拆分路径成各级文件夹
    folders = normalized_path.split(os.sep)

    flag = False
    # 检查每个文件夹名称是否是保留名称
    for i in range(len(folders)):
        # 所有名称只保留第一个"."前的名字
        name = recursive_splitext(folders[i])
        # 使用 find() 方法查找第一个点号的位置
        dot_index = folders[i].find('.')
        if dot_index == -1:
            dot_index = len(folders[i])
        if not restore:
            if name.upper() in win_reserved_names_list:
                flag = True
                # 在点号之前插入文本
                folders[i] = folders[i][:dot_index] + added_reserved_suffix + folders[i][dot_index:]
        else:
            if name.endswith(added_reserved_suffix):
                original_name = name[:-len(added_reserved_suffix)]
                if original_name.upper() in win_reserved_names_list:
                    flag = True
                    # 原名接上点号后的文本
                    folders[i] = original_name + folders[i][dot_index:]

    return flag, os.sep.join(folders)


def read_text_in_file(file_path: str, encoding: str = 'utf-8'):
    with open(file_path, encoding=encoding) as file:
        content = file.read()
    return content


def base_dir(__file__, relpath: str = '') -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    return (lambda relpath: os.path.join(base, relpath) if relpath else base)(relpath)


def create_dir(dir_path: str) -> str:
    """if directory doesn't exist, then create it"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def create_file(file_path: str) -> str:
    """if file path doesn't exist, then create all directories on the path and the file"""
    if not os.path.exists(file_path):
        dir_name = os.path.dirname(file_path)
        if dir_name:
            create_dir(dir_name)
        open(file_path, 'w').close()
    return file_path


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
        format_str = "%Y%m%d_%H%M%S_%f"
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


def get_files_in_dir(directory: str, exclude_relpath: list = None, exclude_abspath: list = None,
                     exclude_abspath_match_compiled_regex: list = None, return_rel_path: bool = False) -> list:
    def _check(path: str) -> bool:
        has_rel = exclude_relpath and any(os.path.join(directory, p) in path for p in exclude_relpath)
        has_abs = exclude_abspath and any(p in path for p in exclude_abspath)
        has_match = exclude_abspath_match_compiled_regex and any(
            compiled_regex.match(path) for compiled_regex in exclude_abspath_match_compiled_regex)
        if not has_rel and not has_abs and not has_match:
            return True

    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_abspath = os.path.join(root, file)
            if _check(file_abspath):
                file_list.append(file_abspath)
    if return_rel_path:
        for i in range(len(file_list)):
            file_list[i] = file_list[i].replace(directory + '\\', '')
    return file_list


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