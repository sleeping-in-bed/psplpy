import os
import shutil
import sys


def startproject(name: str, project_dir: str):
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    os.system(f'{os.path.join(scripts, "django-admin.exe")} {startproject.__name__} {name} {project_dir}')
    shutil.copy2(__file__, os.path.join(project_dir, os.path.basename(__file__)))


def _run(func, suffix: str = ''):
    return os.system(f'{python} {manage_py} {func.__name__} {suffix}')


def startapp(name: str):
    return _run(startapp, name)


def makemigrations():
    return _run(makemigrations)


def migrate():
    return _run(migrate)


def showmigrations():
    return _run(showmigrations)


def collectstatic():
    return _run(collectstatic)


if __name__ == '__main__':
    python = r'D:\WorkSpaceW\Environment\Anaconda3\py310_2310\python.exe'
    if not python:
        python = sys.executable
    scripts = os.path.join(os.path.dirname(python), 'Scripts')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    manage_py = os.path.join(base_dir, 'manage.py')

    startproject('my_bookr', r'D:\WorkSpace\PycharmProjects\MyApplications\bookrs\my_bookr')
    # startapp('reviews')
