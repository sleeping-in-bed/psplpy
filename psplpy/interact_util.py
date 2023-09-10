import ctypes
import re
import sys
from unittest.mock import patch


def progress_bar(progress: float, bar_length: int = 40, finished_chr: str = '=', unfinished_chr: str = '-',
                 both_sides_border_chr_tuple: tuple = ('[', ']'), progress_precision: int = 2) -> None:
    if progress > 1:
        progress = 1
    filled_length = int(progress * bar_length)
    bar = finished_chr * filled_length + unfinished_chr * (bar_length - filled_length)
    # \r means go back to the beginning of the line
    sys.stdout.write(
        f'\r{both_sides_border_chr_tuple[0]}{bar}{both_sides_border_chr_tuple[1]} {progress * 100:.{progress_precision}f}%')
    sys.stdout.flush()


def limited_input(str_list: [list | tuple | set] = None, regex_list: [list | tuple | set] = None, print_str: str = '',
                  error_tip: str = 'Input error, please re-enter.') -> str:
    while True:
        input_str = input(print_str)
        if str_list:
            if input_str in str_list:
                return input_str
        elif regex_list:
            for regex in regex_list:
                match = re.match(regex, input_str)
                if match:
                    return input_str
        else:
            print(error_tip)

# define color constants
foreground_color_dict = {
    'black': 0x00,
    'blue': 0x01,
    'green': 0x02,
    'cyan': 0x03,
    'red': 0x04,
    'magenta': 0x05,
    'yellow': 0x06,
    'gray': 0x07,
    'intensity': 0x08
}
background_color_dict = {
    'black': 0x00,
    'blue': 0x10,
    'green': 0x20,
    'cyan': 0x30,
    'red': 0x40,
    'magenta': 0x50,
    'yellow': 0x60,
    'gray': 0x70,
    'intensity': 0x80
}


def color_print(*args, color: str = 'gray', background: str = 'black', intensity: bool = False, **kwargs) -> None:
    if not sys.platform.startswith('win'):
        print(f'Warning: {color_print.__name__} only work on windows')
    # get cmd handle
    handle = ctypes.windll.kernel32.GetStdHandle(-11)

    def set_color(color):
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)

    if color not in foreground_color_dict:
        raise ValueError(f'{color} not be support as text color')
    elif background not in background_color_dict:
        raise ValueError(f'{background} not be support as background color')
    else:
        if intensity:
            set_color(
                foreground_color_dict[color] | background_color_dict[background] | background_color_dict['intensity'])
        else:
            set_color(foreground_color_dict[color] | background_color_dict[background])
        print(*args, **kwargs)
        set_color(foreground_color_dict['gray'] | background_color_dict['black'])


def mock_input(input_list: [list | tuple], func, *args, **kwargs) -> object:
    with patch('builtins.input', side_effect=input_list):
        result = func(*args, **kwargs)
    return result