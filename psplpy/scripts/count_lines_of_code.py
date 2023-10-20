import re

from psplpy import file_util


def count_non_empty_lines(file_path: str, encoding='utf-8') -> int:
    with open(file_path, 'r', encoding=encoding) as file:
        lines = file.readlines()
        non_empty_lines = [line for line in lines if line.strip()]
        return len(non_empty_lines)


def count(project_dir: str, encoding='utf-8') -> int:
    regex_list = [re.compile(r'^(?:(?!\.py$).)*$'), re.compile(r'(?:.)*resource_rc[.]py')]
    file_path_list = file_util.get_files_in_dir(project_dir, exclude_abspath_match_compiled_regex=regex_list)
    print(f'文件总数：{len(file_path_list)}')
    print(file_path_list)
    sum_count = 0
    for file_path in file_path_list:
        sum_count += count_non_empty_lines(file_path, encoding=encoding)
    return sum_count


if __name__ == '__main__':
    print(count(r'D:\WorkSpace\PycharmProjects\mylib\my_app\StudyEnglish'))
