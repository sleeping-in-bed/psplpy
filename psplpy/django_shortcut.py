import os
import shutil
import sys

from psplpy import file_util, package_dir


class DjangoShortcut:
    def __init__(self, project_name: str, project_dir: str, python_path: str = None):
        self.python = (lambda python_path: python_path if python_path else sys.executable)(python_path)
        self.project_name = project_name
        self.project_dir = os.path.join(project_dir, self.project_name)

        self.scripts = os.path.join(os.path.dirname(self.python), 'Scripts')
        self.base_dir = self._get_base_dir()
        self.project_app_dir = os.path.join(self.project_dir, self.project_name)
        self.setting_path = os.path.join(self.project_app_dir, 'settings.py')

    def prompt_loop(self):
        while True:
            command = input('请输入命令(1: startproject, 2: one_run_migration, 3: start_baseapp)：\n')
            if command == '1':
                self.startproject()
                break
            elif command == '2':
                self.one_run_migration()
            elif command == '3':
                self.start_baseapp()
            else:
                eval(f'self.{command}')

    def _run(self, func, suffix: str = ''):
        return os.system(f'{self.python} {self.get_manage_dir()} {func.__name__} {suffix}')

    @staticmethod
    def _get_base_dir():
        return os.path.dirname(os.path.abspath(__file__))

    def get_manage_dir(self):
        return os.path.join(self.base_dir, 'manage.py')

    def startproject(self):
        file_util.create_dir(self.project_dir)
        os.system(f'{os.path.join(self.scripts, "django-admin.exe")} {self.startproject.__name__}'
                  f' {self.project_name} {self.project_dir}')
        shutil.copy2(__file__, os.path.join(self.project_dir, os.path.basename(__file__)))
        self.auto_setting()

    def auto_setting(self):
        shutil.copytree(os.path.join(package_dir, r'data/django/templates'),
                        os.path.join(self.project_dir, r'templates'))
        dir_dict = dict((name, os.path.join(self.project_dir, name)) for name in ['media', 'static'])
        for key in dir_dict:
            file_util.create_dir(dir_dict[key])

        with open(self.setting_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            content += "\nSTATICFILES_DIRS = [BASE_DIR / 'static']\n"
            content += "MEDIA_ROOT = BASE_DIR / 'media'\n"
            content += "MEDIA_URL = '/media/'\n"
            content = content.replace("'DIRS': [],", "'DIRS': [BASE_DIR / 'templates'],")
            # moving the pointer to the beginning, otherwise it's appending mode
            f.seek(0)
            f.write(content)

        urls_path = os.path.join(self.project_app_dir, 'urls.py')
        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write(open(os.path.join(package_dir, r'data/django/urls.py'), encoding='utf-8').read())

    def startapp(self, name: str):
        self._run(self.startapp, name)
        self.startapp_extra(name)

    def startapp_extra(self, name):
        app_dir = os.path.join(self.base_dir, name)
        file_util.create_dir(os.path.join(app_dir, rf'static\{name}'))
        file_util.create_dir(os.path.join(app_dir, rf'templates\{name}'))

        urls_path = file_util.create_file(os.path.join(app_dir, 'urls.py'))
        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write('from django.urls import path\n\nurlpatterns = [\n\n]')

        with open(self.setting_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            content = content.replace("INSTALLED_APPS = [", f"INSTALLED_APPS = [\n    '{name}',")
            f.seek(0)
            f.write(content)

    def start_baseapp(self):
        app_name = 'baseapp'
        self.startapp(app_name)
        app_dir = os.path.join(self.base_dir, app_name)
        commands_dir = os.path.join(app_dir, r'management/commands')
        shutil.copytree(os.path.join(package_dir, r'data/django/management/commands'), commands_dir)

        app_views = os.path.join(app_dir, 'views.py')
        views_content = open(os.path.join(package_dir, r'data/django/views.py'), encoding='utf-8').read()
        open(app_views, 'w', encoding='utf-8').write(views_content)

        self.migrate()

    def makemigrations(self):
        return self._run(self.makemigrations)

    def migrate(self):
        return self._run(self.migrate)

    def showmigrations(self):
        return self._run(self.showmigrations)

    def one_run_migration(self):
        self.makemigrations()
        self.migrate()
        self.showmigrations()

    def collectstatic(self):
        return self._run(self.collectstatic)

    def createsuperuser(self):
        return self._run(self.createsuperuser)


if __name__ == '__main__':
    django_shortcut = DjangoShortcut(project_name='my_bookr7',
                                     project_dir=rf'D:\WorkSpace\PycharmProjects\MyApplications\bookrs',
                                     python_path=r'D:\WorkSpaceW\Environment\Anaconda3\py310_2310\python.exe')
    django_shortcut.prompt_loop()
