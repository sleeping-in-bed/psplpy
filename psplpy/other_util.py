import logging
import os
import sys


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


if __name__ == '__main__':
    pass
