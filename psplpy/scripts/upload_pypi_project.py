import os
import shutil
import sys

# option vars
directly_upload_to_pypi = True
##

python_path = sys.executable
python_dir = os.path.dirname(python_path)

username = '__token__'
passwd_test = input()

passwd = input()

project_folder = input()

upload_to_pypi_test = False


def build():
    os.system(f'{python_path} -m build')


def upload():
    if upload_to_pypi_test:
        command = f'{python_path} -m twine upload dist/* -u {username} -p {passwd_test}'
        os.system(f'{command} --repository testpypi')
    else:
        if not directly_upload_to_pypi:
            choose = input('currently in formal upload mode, to confirm input "1", or input "2" to exit\n')
            if choose == '1':
                command = f'{python_path} -m twine upload dist/* -u {username} -p {passwd}'
                os.system(command)
            elif choose == '2':
                pass
            else:
                raise ValueError
        else:
            command = f'{python_path} -m twine upload dist/* -u {username} -p {passwd}'
            os.system(command)


def analyse_options(option):
    if '-f' in option:
        global directly_upload_to_pypi
        directly_upload_to_pypi = False



if __name__ == '__main__':
    os.chdir(project_folder)
    option = input('please input options\n')
    analyse_options(option)

    if os.path.exists(r'dist'):
        choose = input('dist has existed, whether to repack? Input "1" repack and upload, '
                       'input "2" skip pack and upload, input "3" end program, input "4" just build.\n')
        if choose == '1':
            shutil.rmtree('dist')
            build()
            upload()
        elif choose == '2':
            upload()
        elif choose == '3':
            pass
        elif choose == '4':
            shutil.rmtree('dist')
            build()
        else:
            raise ValueError
    else:
        choose = input('Input "1" pack and upload, input "2" just build, input "3" end program.\n')
        if choose == '1':
            build()
            upload()
        elif choose == '2':
            build()
        elif choose == '3':
            pass
        else:
            raise ValueError
