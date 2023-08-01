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


if __name__ == '__main__':
    pass
