import time
import functools
import data_access

"""
timing_dict = {func_name->str: [{'elapsed_time': float, 'start_time': float}, ...], ...}
"""
timing_dict = {}
timing_dict_save_path = ['']


def timing_decorator(enable: bool = True, show_time: bool = False, set_path_and_real_time_write: str = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not enable:
                return func(*args, **kwargs)
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            global timing_dict
            if show_time:
                print(f'{func.__name__}: {elapsed_time}s')
            if set_path_and_real_time_write:
                timing_dict = data_access.load_json_maybe_null(set_path_and_real_time_write, dict)
            if not timing_dict.get(func.__name__):
                timing_dict[func.__name__] = []
            info_dict = {'elapsed_time': elapsed_time, 'start_time': start_time}
            timing_dict[func.__name__].append(info_dict)
            if set_path_and_real_time_write:
                data_access.dump_json_human_friendly(timing_dict, set_path_and_real_time_write)
            return result
        return wrapper
    return decorator


def set_path_and_save_timing_dict(path: str = 'timing.json', is_add: bool = True):
    global timing_dict_save_path
    timing_dict_save_path[0] = path
    if is_add:
        old_timing_dict = data_access.load_json_maybe_null(path, dict)
        for key in timing_dict:
            if old_timing_dict.get(key):
                old_timing_dict[key].extend(timing_dict[key])
            else:
                old_timing_dict[key] = timing_dict[key]
        data_access.dump_json_human_friendly(old_timing_dict, path)
    else:
        data_access.dump_json_human_friendly(timing_dict, path)

