import multiprocessing
import os
import subprocess
import time
from typing import Any
import pyautogui
from pynput.keyboard import Controller

import file_util


def click_key(key: str) -> None:
    """click one key"""
    Controller().press(key)
    Controller().release(key)


def type_string(string: str, interval: float = 0) -> None:
    """click keys by string's order"""
    for c in string:
        click_key(c)
        time.sleep(interval)


def _multiple_clicks(num: int, point: tuple = None) -> None:
    for _ in range(num):
        pyautogui.click(point)


def quick_click(num: int, thread: int = 10, point: tuple = None, start_interval: float = 0) -> None:
    """click quickly with multiprocess, but once 'thread' more than one, the number of clicks won't enough"""
    time.sleep(start_interval)
    process_list = []
    for _ in range(thread):
        process_list.append(multiprocessing.Process(target=_multiple_clicks, args=(int(num / thread), point)))
    for p in process_list:
        p.start()
    for p in process_list:
        p.join()


adb_path = os.path.join(file_util.get_this_dir_abspath(__file__), r'tools\platform-tools\adb.exe')
if not os.path.exists(adb_path):
    adb_path = 'adb'


def _execute_adb_command(command) -> Any:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stderr:
        raise RuntimeError(result.stderr)
    return result


def get_devices_with_adb() -> dict:
    """using adb gets device names and states"""
    command = rf'{adb_path} devices'
    result = _execute_adb_command(command)
    devices_list = result.stdout.split('\n')
    devices_list = [devices_list[i] for i in range(0, len(devices_list)) if devices_list[i] and i != 0]
    devices_dict = dict(tuple(item.split('\t')) for item in devices_list)
    return devices_dict


def auto_get_device_name() -> str:
    devices = get_devices_with_adb()
    if list(devices.values()).count('device') == 1:
        device = [key for key in devices if devices[key] == 'device'][0]
        return device
    else:
        raise RuntimeError(f'More than one online device: {devices}')


def click_with_adb(x: int, y: int, device: str = None, show_time: bool = False) -> float:
    """using adb clicks the phone screen"""
    if not device:
        device = auto_get_device_name()
    t_start = time.time()
    command = rf'{adb_path} -s {device} shell input tap {x} {y}'
    result = _execute_adb_command(command)
    duration = time.time() - t_start
    if show_time:
        print(f'click time: {duration}')
    return duration


def get_screen_size_with_adb(device: str = None, show_time: bool = False) -> tuple[int, int]:
    """using adb get phone screen's pixel width and height"""
    t_start = time.time()
    if not device:
        device = auto_get_device_name()
    command = rf'{adb_path} -s {device} shell wm size'
    result = _execute_adb_command(command)
    size_str = result.stdout.split(': ')[1]
    width, height = map(int, size_str.split('x'))
    if show_time:
        print(f'get size time: {time.time() - t_start}')
    return width, height


def capture_screen_with_adb(device: str = None, output_path: str = file_util.rename_duplicate_file('screenshot.png'),
                            show_time: bool = False):
    """using adb screenshot"""
    t_start = time.time()
    if not device:
        device = auto_get_device_name()
    command = rf"{adb_path} -s {device} shell screencap -p /sdcard/screenshot.png"
    result = _execute_adb_command(command)
    if show_time:
        print(f'screenshot time: {time.time() - t_start}')
    t_start = time.time()
    command = rf"{adb_path} -s {device} pull /sdcard/screenshot.png {output_path}"
    result = _execute_adb_command(command)
    if show_time:
        print(f'transmit time: {time.time() - t_start}')
    return output_path


if __name__ == '__main__':
    pass