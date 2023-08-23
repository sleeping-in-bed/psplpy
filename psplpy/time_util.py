import datetime
import re
import time

t_fmt = {
    'day': '%Y-%m-%d',
    'sec': '%Y-%m-%d_%H:%M:%S',
    'milli': '%Y-%m-%d_%H:%M:%S.%f',
    'compact_milli': '%Y%m%d %H%M%S.%f'
}


def parse_datetime_str(datetime_str: str) -> datetime:
    """Match time format strings, allow any non-numeric char between them"""
    patterns = [
        r'^(\d{4})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{1,6})$',
        r'^(\d{4})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})\D?(\d{2})$',
        r'^(\d{4})\D?(\d{2})\D?(\d{2})$',
    ]
    matched_time_format = [
        '%Y%m%d%H%M%S%f',
        '%Y%m%d%H%M%S',
        '%Y%m%d',
    ]

    for index, pattern in enumerate(patterns):
        match = re.match(pattern, datetime_str)
        if match:
            groups = match.groups()
            formatted_datetime = ''.join(groups)
            dt = datetime.datetime.strptime(formatted_datetime, matched_time_format[index])
            return dt

    raise ValueError("Unrecognized datetime format")


def wait_certain_time(set_time: str, format_str: str = None, interval: float = 0) -> None:
    if not format_str:
        dt = parse_datetime_str(set_time)
    else:
        dt = datetime.datetime.strptime(set_time, format_str)
    while True:
        if datetime.datetime.now() >= dt:
            break
        else:
            time.sleep(interval)


if __name__ == '__main__':
    wait_certain_time('2023-08-25-22-21.50')
