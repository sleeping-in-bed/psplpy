import multiprocessing
import os
import subprocess
import tempfile
import time
from typing import Any, Tuple
import pyautogui
from pynput.keyboard import Controller

import file_util
import ocr_util


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


class Adb:
    def __init__(self, device: str = None, adb_path: str = None, show_time: bool = False):
        if not adb_path:
            adb_path = file_util.get_abspath_from_relpath(__file__, r'tools\platform-tools\adb.exe')
            if not os.path.exists(adb_path):
                adb_path = 'adb'
            self.adb_path = adb_path
        if not device:
            self.device = self.auto_get_device_name()
        self.show_time = show_time

    @staticmethod
    def _execute_adb_command(command) -> Any:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.stderr:
            raise RuntimeError(result.stderr)
        return result

    def get_devices(self) -> dict:
        """using adb gets device names and states"""
        command = rf'{self.adb_path} devices'
        result = Adb._execute_adb_command(command)
        devices_list = result.stdout.split('\n')
        devices_list = [devices_list[i] for i in range(0, len(devices_list)) if devices_list[i] and i != 0]
        devices_dict = dict(tuple(item.split('\t')) for item in devices_list)
        return devices_dict

    def auto_get_device_name(self) -> str:
        devices = self.get_devices()
        number_of_devices = list(devices.values()).count('device')
        if number_of_devices == 1:
            device = [key for key in devices if devices[key] == 'device'][0]
            return device
        elif number_of_devices > 1:
            raise RuntimeError(f'More than one online device: {devices}')
        else:
            raise RuntimeError(f'No online device')

    def _common_operation(self, command, tip):
        t_start = time.time()
        result = Adb._execute_adb_command(command)
        duration = time.time() - t_start
        if self.show_time:
            print(f'{tip}: {duration}')
        return duration

    def tap(self, point: Tuple[int, int]) -> float:
        """using adb taps the phone screen"""
        command = rf'{self.adb_path} -s {self.device} shell input tap {point[0]} {point[1]}'
        return self._common_operation(command, 'click time')

    def swipe(self, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """using adb swipes the phone screen"""
        command = rf'{self.adb_path} -s {self.device} shell input swipe {start[0]} {start[1]} {end[0]} {end[1]}'
        return self._common_operation(command, 'swipe time')

    def get_screen_size(self) -> tuple[int, int]:
        """using adb get phone screen's pixel width and height"""
        t_start = time.time()
        command = rf'{self.adb_path} -s {self.device} shell wm size'
        result = Adb._execute_adb_command(command)
        size_str = result.stdout.split(': ')[1]
        width, height = map(int, size_str.split('x'))
        if self.show_time:
            print(f'get size time: {time.time() - t_start}')
        return width, height

    def capture_screen(self, output_path: str = file_util.rename_duplicate_file('screenshot.png')):
        """using adb screenshot"""
        t_start = time.time()
        command = rf"{self.adb_path} -s {self.device} shell screencap -p /sdcard/screenshot.png"
        result = Adb._execute_adb_command(command)
        if self.show_time:
            print(f'screenshot time: {time.time() - t_start}')
        t_start = time.time()
        command = rf"{self.adb_path} -s {self.device} pull /sdcard/screenshot.png {output_path}"
        result = Adb._execute_adb_command(command)
        if self.show_time:
            print(f'transmit time: {time.time() - t_start}')
        return output_path

    def _multiple_clicks(self, num: int, point: tuple, i) -> None:
        for _ in range(num):
            self.tap(*point)
            if self.show_time:
                print(f'{i}_{_}: {time.time()}')

    def quick_click(self, num: int, point: tuple, thread: int = 50,
                    start_interval: float = 0, thread_start_interval: float = 0.01) -> None:
        p_list = []
        for i in range(thread):
            p_list.append(multiprocessing.Process(target=self._multiple_clicks,
                                                  args=(int(num / thread), point, i)))
        time.sleep(start_interval)
        for p in p_list:
            p.start()
            time.sleep(thread_start_interval)
        for p in p_list:
            p.join()

    def get_text_info_list(self, ocr: ocr_util.PyOcr, ignore_case: bool = False,
                           keep_only_en_and_num: bool = False, image_enlarge: float = 1) -> Tuple[
        Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]], str, float]:
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_file:
            self.capture_screen(temp_file.name)
            return ocr.get_text_info_list(temp_file.name, ignore_case, keep_only_en_and_num, image_enlarge)


if __name__ == '__main__':
    pass