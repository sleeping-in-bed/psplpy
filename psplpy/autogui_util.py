import multiprocessing
import time

import pyautogui


def _multiple_clicks(num: int, point: tuple = None) -> None:
    if point:
        for _ in range(num):
            pyautogui.click(point)
    else:
        for _ in range(num):
            pyautogui.click()


def quick_click(num: int, thread: int = 10, point: tuple = None, start_interval: float = 1) -> None:
    time.sleep(start_interval)
    process_list = []
    for _ in range(thread):
        process_list.append(multiprocessing.Process(target=_multiple_clicks, args=(int(num / thread), point)))
    for p in process_list:
        p.start()
    for p in process_list:
        p.join()