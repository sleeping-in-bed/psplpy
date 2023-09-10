import os
import shutil
import sys


def build(python_path: str):
    os.system(f'{python_path} -m build')


def upload(python_path: str, username: str, passwd: str, passwd_test: str, upload_to_pypi_test: bool):
    if upload_to_pypi_test:
        command = f'{python_path} -m twine upload dist/* -u {username} -p {passwd_test} --repository testpypi'
    else:
        command = f'{python_path} -m twine upload dist/* -u {username} -p {passwd}'
    os.system(command)


def upload_pypi_project(project_dir: str, username: str = '__token__', passwd: str = None,
                        passwd_test: str = None, python_path: str = None,
                        upload_to_pypi_test: bool = False, just_build: bool = False):
    if not python_path:
        python_path = sys.executable
    os.chdir(project_dir)
    try:
        shutil.rmtree('dist')
    except FileNotFoundError:
        print(f"dist doesn't exist or fail to delete.")
    if just_build:
        build(python_path)
    else:
        build(python_path)
        upload(python_path, username, passwd, passwd_test, upload_to_pypi_test)


if __name__ == '__main__':
    project_dir = r''
    username = '__token__'
    passwd = ''
    passwd_test = ''

    upload_pypi_project(project_dir, username, passwd, passwd_test,
                        python_path=None, upload_to_pypi_test=False, just_build=False)