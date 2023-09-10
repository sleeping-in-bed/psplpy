import json
import lzma
import multiprocessing
import os
import pickle
import re
import time
import zlib
from typing import Any

from file_util import create_file
from interact_util import progress_bar


def check_int_or_float(input_str: str) -> type:
    int_pattern = r'^[-+]?\d+$'
    float_pattern = r'^[-+]?\d+(\.\d+)?$'

    if re.match(int_pattern, input_str):
        return int
    elif re.match(float_pattern, input_str):
        return float
    else:
        return str


def convert_json_dict_key_to_number(data: object) -> object:
    if isinstance(data, dict):
        # if data type is dict, convert it
        converted_dict = {}
        for key, value in data.items():
            if type(key) == str:
                trans_type = check_int_or_float(key)
                key = trans_type(key)
            # process the values in dict, using recursion
            value = convert_json_dict_key_to_number(value)
            converted_dict[key] = value
        return converted_dict
    elif isinstance(data, (list, tuple, set)):
        # if date type is list, tuple or set, process it recursively
        converted_list = []
        for item in data:
            converted_item = convert_json_dict_key_to_number(item)
            converted_list.append(converted_item)
        return type(data)(converted_list)
    else:
        # if it's other type, don't process
        return data


def load_json(file_path: str, encoding: str = 'utf-8', trans_key_to_num: bool = False) -> Any:
    with open(file_path, encoding=encoding) as file_path:
        pyjson = json.load(file_path)
    if trans_key_to_num:
        return convert_json_dict_key_to_number(pyjson)
    else:
        return pyjson


def _get_empty_data_structure(data_type: type):
    t = (dict, list, tuple, set)
    if data_type in t:
        return data_type()
    else:
        raise ValueError(f"Just support {t}.")


def load_json_maybe_null(file_path: str, data_type, allow_null: bool = False, encoding: str = 'utf-8',
                         trans_key_to_num: bool = False) -> Any:
    create_file(file_path)
    try:
        pyjson = load_json(file_path, encoding, trans_key_to_num)
        if pyjson is None and not allow_null:
            return _get_empty_data_structure(data_type)
        else:
            return pyjson
    except json.decoder.JSONDecodeError:
        return _get_empty_data_structure(data_type)


def dump_json(pyjson: object, file_path: str, encoding: str = 'utf-8') -> None:
    with open(file_path, 'w', encoding=encoding) as file_path:
        json.dump(pyjson, file_path)


def dump_json_human_friendly(pyjson: object, file_path, encoding='utf-8', indent: int = 4,
                             ensure_ascii: bool = False) -> None:
    with open(file_path, 'w', encoding=encoding) as file_path:
        json.dump(pyjson, file_path, indent=indent, ensure_ascii=ensure_ascii)


def save_obj_with_pickle(obj: object, file_path: str) -> None:
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def load_obj_with_pickle(file_path: str) -> object:
    with open(file_path, 'rb') as f:
        obj = pickle.load(f)
    return obj


compress_error_info = 'Used_lib just can be choose in "lzma" and "zlib"'


def compress_obj(obj: object, used_lib: str = 'lzma') -> bytes:
    # serializing python obj into byte stream using pickle
    serialized_obj = pickle.dumps(obj)
    if used_lib == 'lzma':
        # compress the byte stream using lzma
        compressed_data = lzma.compress(serialized_obj)
    elif used_lib == 'zlib':
        compressed_data = zlib.compress(serialized_obj)
    else:
        raise ValueError(compress_error_info)
    return compressed_data


def decompress_obj(compressed_data, used_lib='lzma') -> object:
    if used_lib == 'lzma':
        serialized_obj = lzma.decompress(compressed_data)
    elif used_lib == 'zlib':
        serialized_obj = zlib.decompress(compressed_data)
    else:
        raise ValueError(compress_error_info)
    # deserialize
    obj = pickle.loads(serialized_obj)
    return obj


def compress_and_store_obj(obj: object, file_path: str, used_lib: str = 'lzma') -> None:
    with open(file_path, "wb") as f:
        compressed_data = compress_obj(obj, used_lib)
        f.write(compressed_data)


def load_and_decompress_obj(file_path: str, used_lib: str = 'lzma') -> object:
    with open(file_path, "rb") as f:
        compressed_data = f.read()
    return decompress_obj(compressed_data, used_lib)


def compress_file_lzma(input_file: str, output_file: str, chunk_size: int = 1024 * 1024 * 10):
    with open(input_file, 'rb') as f_in:
        with lzma.open(output_file, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)


def decompress_file_lzma(input_file: str, output_file: str, chunk_size: int = 1024 * 1024 * 10):
    with lzma.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)


def _compress_chunk(input_path: str, chunk_size: int, shared_offsets: list, shared_data: dict,
                    max_queue_length: int = 100, sleep_time: float = 0.1) -> None:
    while True:
        try:
            offset = shared_offsets.pop(0)
        except IndexError:
            break
        with open(input_path, 'rb') as file:
            file.seek(offset)
            data = file.read(chunk_size)
        compressed_data = lzma.compress(data)
        shared_data[offset] = compressed_data
        while True:
            if len(shared_data) < max_queue_length:
                break
            else:
                time.sleep(sleep_time)


def _write_compressed_data(output_path: str, file_size: int, chunk_size: int, shared_data: dict,
                           sleep_time: float = 0.1, show_progress_bar: bool = False) -> None:
    if show_progress_bar:
        progress_bar(0)
    with open(output_path, 'wb') as compressed_file:
        offset = 0
        while offset < file_size:
            if offset in shared_data:
                compressed_file.write(shared_data[offset])
                del shared_data[offset]
                offset += chunk_size
                if show_progress_bar:
                    progress_bar(offset / file_size)
            else:
                time.sleep(sleep_time)
        if show_progress_bar:
            progress_bar(1)
            print()


def compress_file_multiprocessing_lzma(input_path: str, output_path: str,
                                       num_processes: int = multiprocessing.cpu_count(),
                                       chunk_size: int = 1024 * 1024 * 10, max_queue_length: int = 100,
                                       sleep_time: float = 0.1, show_progress_bar: bool = False) -> dict:
    """
    basic idea:
        1.block the file in advance, and save the offset to a list shared by multiple processes
        2.create a multi-process compressing function, and each function read the first value in the shared list,
            then delete it, and reads data from the offset value from the file.In total, read a block size of data.
            Then compress it and put it in a shared dict
        3.create a write process, and read the compressed data from the shared dict by offset order,
            and write it to file, until the offset value is greater than or equal to the file size.
    """

    t_start = time.time()
    file_size = os.path.getsize(input_path)
    shared_offsets = multiprocessing.Manager().list(range(0, file_size, chunk_size))
    if len(shared_offsets) < num_processes:
        num_processes = len(shared_offsets)
    shared_data = multiprocessing.Manager().dict()

    write_process = multiprocessing.Process(target=_write_compressed_data, args=(
        output_path, file_size, chunk_size, shared_data, sleep_time, show_progress_bar))

    compress_processes = [
        multiprocessing.Process(target=_compress_chunk, args=(input_path, chunk_size, shared_offsets, shared_data,
                                                              max_queue_length, sleep_time)) for _ in
        range(num_processes)]
    processes = [write_process, *compress_processes]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    return {'output_path': os.path.abspath(output_path), 'used_time': time.time() - t_start,
            'compress_ratio': os.path.getsize(output_path) / file_size}
