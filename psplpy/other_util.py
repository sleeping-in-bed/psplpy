import functools
import json
import logging
import os
import subprocess
import sys
import threading
import time
import traceback


def function_multiprocess(func, lock, args: tuple = None, kwargs: dict = None) -> object:
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    lock.acquire()
    try:
        result = func(*args, **kwargs)
    finally:
        lock.release()
    return result


def write_to_pth(path: str, pth_file_name: str = 'my_pth.pth', show_info: bool = True,
                 designate_python_dir: str = None) -> str:
    """writes the specified path to the pth file, so that python adds it to the search path"""
    if designate_python_dir:
        current_python_dir = designate_python_dir
    else:
        current_python_dir = sys.prefix
    site_packages_dir = os.path.join(current_python_dir, r'Lib\site-packages')
    pth_path = os.path.join(site_packages_dir, pth_file_name)
    with open(pth_path, 'a+') as f:
        f.write(path + '\n')
    if show_info:
        print(f'add "{path}" to "{pth_path}" successfully.')
    return pth_path


def default_logger(level=logging.DEBUG):
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # create formatter
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d - %(message)s')
    console_handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(console_handler)
    return logger

'''
Known error: 
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x89 in position 0: invalid start byte,
in "output_line = process.stdout.readline()"
'''
def run_command(command: str, show_output: bool = True, print_interval: float = 0.01) -> str:
    # 运行命令，并将标准输出捕获
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                               bufsize=1, encoding='utf-8')
    output_list = []
    # 实时输出命令的输出
    if show_output:
        while True:
            output_line = process.stdout.readline()
            if output_line == '' and process.poll() is not None:
                break
            elif output_line:
                output_list.append(output_line)
                print(output_line.rstrip('\n'))
            else:
                time.sleep(print_interval)

    # 等待命令运行完毕
    process.wait()
    # 获取完整的命令输出
    if show_output:
        command_output = ''.join(output_list)
    else:
        command_output = ''.join(process.stdout.readlines())
    if process.returncode == 0:
        # 返回命令输出
        return command_output
    else:
        raise ChildProcessError(command_output)


def run_py(script_path: str, python_path: str = 'python'):
    try:
        os.system(f'{python_path} {script_path}')
    except:
        traceback.print_exc()
        input()


def run_py_advanced(script_path: str, python_path: str = 'python'):
    def read_last_line_as_json(file_path, data_type):
        with open(file_path, 'rb') as file:
            file.seek(-2, 2)  # 移动到文件末尾的倒数第二个字节
            while file.read(1) != b'\n':
                file.seek(-2, 1)  # 继续向前移动，直到找到换行符为止
            try:
                last_line = file.readline().decode().strip()  # 读取最后一行并解码为字符串
                json_data = json.loads(last_line)
                return json_data
            except Exception:
                return data_type()

    def modify_last_line(input_file_path, output_file_path, json_data, replace_last_line=True):
        with open(input_file_path, 'rb') as input_file:
            lines = input_file.readlines()

        if replace_last_line:
            lines[-1] = json.dumps(json_data).encode()  # 替换最后一行为新的JSON数据
        else:
            lines.append(b'\n' + json.dumps(json_data).encode())  # 添加新的JSON数据为新的一行

        with open(output_file_path, 'wb') as output_file:
            output_file.writelines(lines)

    try:
        file_path = os.path.abspath(__file__)
        exe_path = sys.executable
        failure_count = 0
        data = read_last_line_as_json(exe_path, dict)
        has_data = False
        py_path = python_path
        if data:
            has_data = True
            py_path = data['python_path']
        while True:
            result_code = os.system(f'{py_path} {script_path}')
            if result_code:
                if failure_count == 0:
                    py_path = 'python'
                elif failure_count == 1 and has_data:
                    py_path = python_path
                else:
                    while True:
                        choose = input('python解释器路径不存在，请输入"1"修改解释器路径，或将解释器路径添加到环境变量后重新运行\n')
                        if choose == '1':
                            break
                        else:
                            print('输入错误，请重新输入')
                    print(f'当前解释器路径：{python_path}')
                    python_path = input('请输入新的解释器路径\n')
                    data['python_path'] = python_path
                    new_exe_path = exe_path + '.new'
                    # 将python路径写入exe文件的末尾
                    modify_last_line(exe_path, new_exe_path, data, has_data)
                    print(f'已将新文件保存在当前目录，文件路径为：{new_exe_path}')
                    print(f'下次运行请删除旧文件，然后在修改新文件名后，运行新文件')
                failure_count += 1
            else:
                break
    except:
        traceback.print_exc()
        input()


def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                try:
                    thread._stop()  # force termination of process
                except AssertionError:
                    pass
                raise TimeoutError(f"Function '{func.__name__}' exceeded the timeout of {seconds} seconds")

            if exception[0] is not None:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator


if __name__ == '__main__':
    pass