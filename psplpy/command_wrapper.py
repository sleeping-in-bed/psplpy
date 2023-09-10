import os

from __init__ import package_dir
import other_util
import file_util

builtin_webp_path = os.path.join(package_dir, r'tools\libwebp-1.3.1-windows-x64\bin')


class Webp:
    def __init__(self, show_command: bool = True, opt_str: str = None, **kwargs):

        if os.path.exists(builtin_webp_path):
            self.webp_path = builtin_webp_path
        else:
            self.webp_path = ''
        self.show_command = show_command
        self.opt_str = opt_str
        self.opt = kwargs

    def set_webp_path(self, webp_path: str = None) -> None:
        self.webp_path = webp_path

    def set_resize(self, width: int = 0, height: int = 0):
        self.opt['resize'] = f'{width} {height}'

    def set_crop(self, left: int, top: int, width: int, height: int):
        self.opt['crop'] = f'{left} {top} {width} {height}'

    def get_option_str(self):
        if self.opt_str:
            return self.opt_str
        else:
            opt_str = ''
            for o in self.opt:
                if self.opt[o] is not False:
                    opt_str += f'-{o} '
                    if (value := self.opt[o]) is not True:
                        opt_str += f'{value} '
            return opt_str

    @staticmethod
    def _check_file_name(input_file: str, output_file: str) -> str:
        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f'{base_name}.webp'
            return file_util.rename_duplicate_file(output_file)
        else:
            return output_file


class CWebp(Webp):
    def cwebp(self, input_file: str, output_file: str = None) -> str:
        output_file = Webp._check_file_name(input_file, output_file)
        opt_str = self.get_option_str()
        command = f'{os.path.join(self.webp_path, "cwebp")} {opt_str} {input_file} -o {output_file}'
        if self.show_command:
            print(command)
        return other_util.run_command(command, self.show_command)

    def set_lossless_preset(self):
        setting = {
            'lossless': True,
            'z': 9,
            'mt': True,
            'metadata': 'all',
        }
        self.opt.update(setting)

    def set_lossy_preset(self, q: int = 75):
        setting = {
            'q': q,
            'm': 6,
            'mt': True,
            'af': True,
            'sharp_yuv': True,
            'alpha_filter': 'best',
            'metadata': 'all',
        }
        self.opt.update(setting)

    def set_info_preset(self):
        setting = {
            'v': True,
            'print_ssim': True,
            'progress': True,
        }
        self.opt.update(setting)


class DWebp(Webp):
    def dwebp(self, input_file: str, output_file: str = None, output_to_stdout: bool = False) -> str:
        output_file = Webp._check_file_name(input_file, output_file)
        opt_str = self.get_option_str()
        if not output_to_stdout:
            command = f'{os.path.join(self.webp_path, "dwebp")} {opt_str} {input_file} -o {output_file}'
        else:
            command = f'{os.path.join(self.webp_path, "dwebp")} {opt_str} {input_file} -o -'
        if self.show_command:
            print(command)
        return other_util.run_command(command, self.show_command)

    def set_output_bmp(self):
        self.opt['bmp'] = True

    def set_output_tiff(self):
        self.opt['tiff'] = True

    def set_output_png(self):
        if self.opt.get('bmp'):
            self.opt.pop('bmp')
        if self.opt.get('tiff'):
            self.opt.pop('tiff')


class Anaconda:
    win_default_path = r'C:\ProgramData\anaconda3\Scripts\conda'

    def __init__(self, conda_path: str = 'conda'):
        self.conda_path = conda_path

    # def activate(self, env_name: str):
    #     command = f'{self.conda_path} activate {env_name}'
    #     other_util.run_command(command)

    def create(self, name: str, version: str = None):
        command = f'{self.conda_path} creat -n {name}'
        if version:
            command += f' python=={version}'
        other_util.run_command(command, show_output=True)

    def env_dirs(self, option: str, env_dir: str = ''):
        command = f'{self.conda_path} config --{option} envs_dirs'
        if option == 'show':
            other_util.run_command(command)
        elif option in ['append', 'prepend', 'remove']:
            other_util.run_command(command + f' {env_dir}')
        else:
            raise ValueError

    # def env_export(self, ):
    #     pass


class WinRAR:
    max_passwd_length_in_bytes = 127

    def __init__(self, path_or_dir: str = None, compress_file_path: str = None, rar_path: str = None,
                 passwd: str = None):
        self.path_or_dir = path_or_dir
        self.compress_file_path = compress_file_path
        self.rar_path = rar_path
        self.passwd = passwd

        self.dir_path = os.path.dirname(self.path_or_dir)
        self.file_or_dir_name = os.path.basename(self.path_or_dir)

    def set_preset(self):
        pass


if __name__ == '__main__':
    pass