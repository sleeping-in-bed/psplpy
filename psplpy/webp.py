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

    def set_resize(self, width: int = 0, height: int = 0):
        self.opt['resize'] = f'{width} {height}'

    def set_crop(self, left: int, top: int, width: int, height: int):
        self.opt['crop'] = f'{left} {top} {width} {height}'

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


if __name__ == '__main__':
    pass