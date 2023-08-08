import ast
import inspect
import os
import re
import timeit
from typing import Tuple, Dict, List

import file_util

setup_func_prefix = 'setup'
main_func_prefix = 'main_statement'


def get_path_directly_call() -> str:
    """get the file path to call a function that uses this function directly"""
    # get call stack infomation
    stack = inspect.stack()
    # the first element is stack() function, the second element is this function,
    # and the third element is a function that calls this function
    caller_filename = stack[2].filename
    return caller_filename


def get_defs_definition(text: str, not_in_class: bool = False) -> List:
    """
    Traverse the abstract syntax tree to find functions definition.
    :return: [{name: str, args_list: list, body: str}, ...]
    """
    def _determine(node) -> bool:
        if isinstance(node, ast.FunctionDef):
            if not_in_class:
                if not hasattr(node, 'parent') or not isinstance(node.parent, ast.ClassDef):
                    return True
            else:
                return True

    function_list = []
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if _determine(node):
            # Extract function name, parameters list and function body code
            function_name = node.name
            args = [arg.arg for arg in node.args.args]
            function_body = ast.unparse(node.body)
            function_list.append({'name': function_name, 'args_list': args, 'body': function_body})
    return function_list


def generate_time_it_template(file_dir: str = '', file_name: str = '') -> str:
    if not file_dir:
        file_dir = os.path.dirname(get_path_directly_call())
    if not file_name:
        file_name = 'time_test.py'
    file_path = file_util.rename_duplicate_file(os.path.join(file_dir, file_name))
    with open(r'data/time_it_template.txt', encoding='utf-8') as f:
        template = f.read()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    print(f'Template file has been saved in: {file_path}')
    return file_path


def _get_test_functions(function_list: list) -> Tuple[Dict, Dict]:
    setup_pattern = rf"{setup_func_prefix}(\d+)"
    main_pattern = rf'{main_func_prefix}(\d+)'
    setup_dict = {}
    main_dict = {}
    for func in function_list:
        setup_match = re.match(setup_pattern, func['name'])
        main_match = re.match(main_pattern, func['name'])
        if setup_match:
            setup_dict[int(setup_match.group(1))] = func['body']
        if main_match:
            main_dict[int(main_match.group(1))] = func['body']
    return setup_dict, main_dict


def _test(setup_dict, main_dict, test_num) -> Dict:
    test_time_dic = {}
    if setup_dict:
        for i in setup_dict:
            for j in main_dict:
                t = timeit.Timer(main_dict[j], setup_dict[i])
                test_time_dic[(i, j)] = t.timeit(test_num)
    else:
        for j in main_dict:
            t = timeit.Timer(main_dict[j])
            test_time_dic[j] = t.timeit(test_num)
    return test_time_dic


def _start_test(setup_dict, main_dict, test_num, time_significant_digits) -> Tuple[Dict, Dict, Dict]:
    print('# Start test')
    if test_num <= 0:
        test_num = 1
        while True:
            longest_time = sorted(_test(setup_dict, main_dict, test_num).values())[-1]
            if longest_time < 0.001:
                test_num *= 10
            else:
                break
        test_num = int(1 / longest_time) * test_num
    else:
        test_num = int(test_num)

    print(f'# Number of tests: {test_num}')
    test_time_dic = _test(setup_dict, main_dict, test_num)
    test_time_dic_value_sorted = sorted(test_time_dic.values())
    keys_lst = []
    for test_time_dic_value in test_time_dic_value_sorted:
        keys_lst.extend(key for key in test_time_dic.keys() if test_time_dic[key] == test_time_dic_value)

    test_time_dic = dict((key, test_time_dic[key]) for key in keys_lst)
    test_time_dic_ratio = dict(
        (key, f'{test_time_dic[key] / test_time_dic[keys_lst[0]]:.{time_significant_digits}g}') for key in keys_lst)
    test_time_dic_str = dict((key, f'{test_time_dic[key]:.{time_significant_digits}g}') for key in keys_lst)
    return test_time_dic, test_time_dic_str, test_time_dic_ratio


def time_it(__file__, test_num: int = 0, time_significant_digits: int = 5) -> Tuple[Dict, Dict, Dict]:
    file_path = os.path.abspath(__file__)
    with open(file_path, encoding='utf-8') as f:
        content = f.read()
    function_list = get_defs_definition(content, not_in_class=True)
    setup_dict, main_dict = _get_test_functions(function_list)
    if not main_dict:
        raise ValueError(f"Please use {__name__}.{generate_time_it_template.__name__}() to generate a test template "
                         f"file first, or add some {main_func_prefix} test examples.")
    return _start_test(setup_dict, main_dict, test_num, time_significant_digits)
