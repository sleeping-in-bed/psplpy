import os
import re
import time
from typing import Tuple, List, Any
import pyautogui
from PIL import Image

import file_util
import image_util
import other_util


def keep_only_english_and_num(text: str) -> str:
    """using regular expression to match characters that are not english alphabet"""
    return re.sub(r'[^a-zA-Z0-9]', '', text)


class PyOcr:
    paddle_ocr = 'PaddleOCR'
    easy_ocr = 'easyocr'
    dddd_ocr = 'ddddocr'

    def __init__(self, detect_module: str = 'PaddleOCR', lang: str = 'chs', debug: bool = False,
                 debug_dir: str = os.path.join(file_util.get_this_dir_abspath(__file__), r'debug\ocr_pic'),
                 logger=other_util.default_logger(), log_path: str = None, use_gpu: bool = False):
        self.detect_module = detect_module.casefold()
        self.debug = debug
        self.debug_dir = debug_dir
        file_util.create_dir(self.debug_dir)
        self.logger = logger
        if not log_path:
            self.log_path = os.path.join(self.debug_dir, 'pyocr.log')
        else:
            self.log_path = log_path
        if self.debug:
            t1 = time.monotonic()
        if self.detect_module == 'paddleocr':
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, use_gpu=use_gpu, show_log=False)
        elif self.detect_module == 'easyocr':
            import easyocr
            if lang.casefold() in ['chs', 'ch_sim']:
                self.ocr = easyocr.Reader(['ch_sim', 'en'])  # need to run only once to load model into memory
            elif lang.casefold() == 'en':
                self.ocr = easyocr.Reader(['en'])
            else:
                self.ocr = easyocr.Reader([lang])
        elif self.detect_module == 'ddddocr':
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
        else:
            raise ValueError(f'Module {self.detect_module} not exist')
        if self.debug:
            self.logger.debug('Model loading time：' + str(time.monotonic() - t1))

    def get_text_info_list(self, image: Any = None, ignore_case: bool = False,
                           keep_only_en_and_num: bool = False, image_enlarge: float = 1) -> Tuple[
        Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]], str, float]:
        if self.debug:
            t1 = time.monotonic()
        if not image:
            image = 0, 0, *pyautogui.size()
        image_array = image_util.convert_image_to_ndarray(image)
        if image_enlarge != 1:
            image_array = image_util.enlarge_img(image_array, image_enlarge)

        str_info_list = []
        if self.detect_module == 'paddleocr':
            # all text info
            text = self.ocr.ocr(image_array, cls=True)
            # format text info list
            for i in range(0, len(text[0])):
                temp_list = [[tuple(x) for x in text[0][i][0]], text[0][i][1][0], text[0][i][1][1]]
                str_info_list.append(temp_list)
        # similar with PaddleOCR
        elif self.detect_module == 'easyocr':
            str_info_list = self.ocr.readtext(image_array, detail=1)
            # format text info list
            for i in range(0, len(str_info_list)):
                str_info_list[i] = [[tuple(x) for x in str_info_list[i][0]], str_info_list[i][1], str_info_list[i][2]]
        elif self.detect_module in ['ddddocr']:
            raise ValueError(f'{self.detect_module} not support this function')
        else:
            raise ValueError(f'Module {self.detect_module} not exist')

        if ignore_case:
            str_info_list = [[str_info[0], str_info[1].casefold(), str_info[2]] for str_info in str_info_list]
        if keep_only_en_and_num:
            str_info_list = [[str_info[0], keep_only_english_and_num(str_info[1]), str_info[2]] for str_info in
                             str_info_list]
        if self.debug:
            dst_path = os.path.join(self.debug_dir, os.path.basename(file_util.get_current_time_as_file_name('.png')))
            try:
                image_util.draw_polygons_on_pic(image_array, [[tuple(x[0][0]), tuple(x[0][1]), tuple(x[0][2]),
                                                   tuple(x[0][3])] for x in str_info_list], dst_path)
                self.logger.debug('pic_path：' + str(dst_path))
            except Exception as e:
                self.logger.critical(str(e))
            self.logger.debug('detect_time：' + str(time.monotonic() - t1))
            self.logger.debug('detected_info：' + str(str_info_list))

        return str_info_list

    @staticmethod
    def get_text_list_from_text_info_list(text_info_list: List) -> List:
        return [info[1] for info in text_info_list]

    @staticmethod
    def get_merged_text_from_text_info_list(text_info_list: List) -> str:
        return ''.join(PyOcr.get_text_list_from_text_info_list(text_info_list))

    @staticmethod
    def transform_text_info_list_to_ltrb(text_info_list: List) -> List:
        """convert the four vertexes to ((left, top), (right, bottom))"""
        return [[image_util.four_vertexes_transform_to_ltrb(text_info[0]),
                 text_info[1], text_info[2]] for text_info in text_info_list]

    @staticmethod
    def transform_text_info_list_to_ltwh(text_info_list: List) -> List:
        """convert the four vertexes to (left, top, width, height)"""
        return [[image_util.ltrb_transform_to_ltwh(image_util.four_vertexes_transform_to_ltrb(text_info[0])),
                 text_info[1], text_info[2]] for text_info in text_info_list]

    def get_text_list(self, image: Any = None, ignore_case: bool = False, keep_only_en_and_num: bool = False,
                      image_enlarge: float = 1) -> List:
        return [info[1] for info in self.get_text_info_list(image, ignore_case, keep_only_en_and_num, image_enlarge)]

    def get_merged_text(self, image: Any = None, ignore_case: bool = False, keep_only_en_and_num: bool = False,
                        image_enlarge: float = 1) -> str:
        return ''.join(self.get_text_list(image, ignore_case, keep_only_en_and_num, image_enlarge))

    def get_captcha(self, image: Any):
        if self.detect_module == 'ddddocr':
            img = Image.fromarray(image_util.convert_image_to_ndarray(image))
            result = self.ocr.classification(img)
        elif self.detect_module in ['paddleocr', 'easyocr']:
            raise ValueError(f'{self.detect_module} not support this function')
        else:
            raise ValueError(f'Module {self.detect_module} not exist')
        return result


if __name__ == '__main__':
    ocr = PyOcr(debug=True, use_gpu=True)
    l = ocr.get_text_info_list()
    print(l)