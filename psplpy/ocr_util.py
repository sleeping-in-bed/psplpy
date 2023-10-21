import multiprocessing
import os
import re
import threading
import time
from typing import List, Any

import numpy as np
import pyautogui
from PIL import Image
import pickle

import file_util
import image_util
import network_util
import other_util


def keep_only_english_and_num(text: str) -> str:
    """using regular expression to match characters that are not english alphabet"""
    return re.sub(r'[^a-zA-Z0-9]', '', text)


class PyOcr:
    paddle_ocr = 'PaddleOCR'
    easy_ocr = 'easyocr'
    dddd_ocr = 'ddddocr'

    ltwh = 'ltwh'
    ltrb = 'ltrb'
    ltrtrblt = 'ltrtrblt'

    def __init__(self, detect_module: str = paddle_ocr, lang: str = 'chs', debug: bool = False,
                 debug_dir: str = file_util.base_dir(__file__, r'debug\pyocr'),
                 logger=other_util.default_logger(), log_path: str = None, use_gpu: bool = False):
        self.detect_module = detect_module.casefold()
        self.debug = debug
        self.debug_dir = debug_dir
        if self.debug:
            file_util.create_dir(self.debug_dir)
        self.logger = logger
        if not log_path:
            self.log_path = os.path.join(self.debug_dir, 'pyocr.log')
        else:
            self.log_path = log_path
        time_start = time.perf_counter()
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
            self.logger.debug('Model loading time：' + str(time.perf_counter() - time_start))

    @staticmethod
    def _transform_image(image: Any):
        if isinstance(image, (str, np.ndarray, bytes)):
            return image
        elif isinstance(image, (list, tuple)):
            return np.array(pyautogui.screenshot(region=image_util.trans_to_ltwh(image)))
        else:
            raise TypeError

    def _transform_rect(self, text_info_list: list, rect_mode: str) -> list:
        if rect_mode == self.ltrtrblt:
            return text_info_list
        elif rect_mode == self.ltrb:
            """convert the four vertexes to ((left, top), (right, bottom))"""
            return [[image_util.four_vertexes_transform_to_ltrb(info[0]), info[1], info[2]] for info in text_info_list]
        elif rect_mode == self.ltwh:
            """convert the four vertexes to (left, top, width, height)"""
            return [[image_util.trans_to_ltwh(info[0]), info[1], info[2]] for info in text_info_list]
        else:
            raise ValueError

    def get_text_info_list(self, image: Any = None, ignore_case: bool = False,
                           keep_only_en_and_num: bool = False, image_enlarge: float = 1,
                           rect_mode: str = ltrtrblt) -> list[list[str | Any]] | list[list[Any]] | list:
        time_start = time.perf_counter()
        if not image:
            image = 0, 0, *pyautogui.size()
        image_array = PyOcr._transform_image(image)
        if image_enlarge != 1:
            image_array = image_util.enlarge_img(image_array, image_enlarge)

        text_info_list = []
        if self.detect_module == 'paddleocr':
            text = self.ocr.ocr(image_array, cls=True)
            # format text info list to: ([left top][right top][right bottom][left bottom]], text, confidence)
            # for instance:             ([[459, 5], [869, 5], [869, 19], [459, 19]], '1', 0.0004511636577615576)
            for i in range(0, len(text[0])):
                temp_list = [text[0][i][0], text[0][i][1][0], text[0][i][1][1]]
                text_info_list.append(temp_list)
        elif self.detect_module == 'easyocr':  # similar with PaddleOCR
            text_info_list = self.ocr.readtext(image_array, detail=1)
        elif self.detect_module in ['ddddocr']:
            raise ValueError(f'{self.detect_module} not support this function')
        else:
            raise ValueError(f'Module {self.detect_module} not exist')

        text_info_list = self._transform_rect(text_info_list, rect_mode)
        if ignore_case:
            text_info_list = [[str_info[0], str_info[1].casefold(), str_info[2]] for str_info in text_info_list]
        if keep_only_en_and_num:
            text_info_list = [[str_info[0], keep_only_english_and_num(str_info[1]), str_info[2]] for str_info in
                              text_info_list]
        if self.debug:
            dst_path = os.path.join(self.debug_dir, os.path.basename(file_util.get_current_time_as_file_name('.png')))
            try:
                image_util.draw_polygons_on_pic(image_array, [[tuple(x[0][0]), tuple(x[0][1]), tuple(x[0][2]),
                                                               tuple(x[0][3])] for x in text_info_list], dst_path)
                self.logger.debug('pic_path：' + str(dst_path))
            except Exception as e:
                self.logger.critical(str(e))
            self.logger.debug('detect_time：' + str(time.perf_counter() - time_start))
            self.logger.debug('detected_info：' + str(text_info_list))

        return text_info_list

    @staticmethod
    def get_text_list_from_text_info_list(text_info_list: List) -> List:
        return [info[1] for info in text_info_list]

    @staticmethod
    def get_merged_text_from_text_info_list(text_info_list: List) -> str:
        return ''.join(PyOcr.get_text_list_from_text_info_list(text_info_list))

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


class PyOcrClient:
    def __init__(self, server_address: tuple[str, int], self_address: tuple[str, int], debug: bool = False):
        self.server_address = server_address
        self.self_address = self_address
        self.debug = debug
        self.client_socket = network_util.ClientSocket(*self.server_address)
        self.server_socket = network_util.ServerSocket(*self.self_address)
        self.result_dict = {}
        self.id = 0
        threading.Thread(target=self._receive_text_info).start()

    def request_text_info_list(self, image: Any = None, ignore_case: bool = False, keep_only_en_and_num: bool = False,
                               image_enlarge: float = 1, rect_mode: str = PyOcr.ltrtrblt) -> int:
        if self.debug: print(f'开始发送图像 {self.id}')
        self.client_socket.connect()
        with open(image, 'rb') as image_file:
            id = self.id
            kwargs = {'ignore_case': ignore_case, 'keep_only_en_and_num': keep_only_en_and_num,
                      'image_enlarge': image_enlarge, 'rect_mode': rect_mode}
            self.client_socket.send_obj({'id': id, 'value': image_file.read(), 'address': self.self_address,
                                         'kwargs': kwargs})
            self.id += 1
        if self.debug: print('图像发送完成')
        self.client_socket.close()
        return id

    def _receive_text_info(self) -> None:
        while True:
            if self.debug: print('等待连接')
            client_socket, client_address = self.server_socket.accept()
            if self.debug: print(f"来自 {client_address} 的连接")
            data = pickle.loads(client_socket.recv_all())
            if self.debug: print("接收信息：", data)
            self.result_dict[data['id']] = data['value']
            client_socket.close()

    def fetch_text_info_list(self, id: int) -> list:
        while True:
            if self.result_dict.get(id) is not None:  # 要使用None，防止get返回空列表被判假
                return self.result_dict.pop(id)
            time.sleep(0.01)


class PyOcrServer:
    def __init__(self, self_address: tuple[str, int], number_of_processing: int = 1, server_debug: bool = False,
                 detect_module: str = 'paddleocr', lang: str = 'chs', debug: bool = False,
                 debug_dir: str = file_util.base_dir(__file__, r'debug\pyocr'),
                 logger=other_util.default_logger(), log_path: str = None, use_gpu: bool = False):
        self.self_address = self_address
        self.number_of_processing = number_of_processing
        self.server_debug = server_debug
        self.kwargs = locals()
        for key in ['self', 'self_address', 'number_of_processing', 'server_debug']:
            self.kwargs.pop(key)
        if self.server_debug: print(self.kwargs)

        self.lock = multiprocessing.Lock()
        manager = multiprocessing.Manager()
        self.share_image_list = manager.list()
        self.server_socket = network_util.ServerSocket(*self.self_address)
        threading.Thread(target=self._receive_image).start()

        for i in range(self.number_of_processing):
            multiprocessing.Process(target=self._ocr_server, args=(self.kwargs, self.lock)).start()

    def _ocr_server(self, kwargs, lock):
        ocr = PyOcr(**kwargs)
        if self.server_debug: print(ocr)
        while True:
            # if self.server_debug: print(len(self.share_image_list))
            data = None
            with lock:
                if self.share_image_list:
                    data = self.share_image_list.pop(0)
            if data:
                text_info_list = ocr.get_text_info_list(data['value'], **data['kwargs'])
                self._send_data({'id': data['id'], 'value': text_info_list}, data['address'])
            time.sleep(0.01)

    def _receive_image(self):
        while True:
            if self.server_debug: print('等待连接')
            client_socket, client_address = self.server_socket.accept()
            if self.server_debug: print(f"来自 {client_address} 的连接")
            data = pickle.loads(client_socket.recv_all())
            if self.server_debug: print(f'图像 {data["id"]} 接收完成')
            client_socket.close()
            self.share_image_list.append(data)

    def _send_data(self, data, address):
        if self.server_debug: print(f'发送 {data["id"]} 数据')
        client_socket = network_util.ClientSocket(*address)
        client_socket.connect()
        client_socket.send_obj(data)
        client_socket.close()


if __name__ == '__main__':
    choose = input('input\n')
    if choose == '1':
        ocr = PyOcr(debug=True, use_gpu=False, detect_module=PyOcr.easy_ocr)
        l = ocr.get_text_info_list()
        print(l)
    elif choose == '2':
        server_address = ('127.0.0.1', 12345)
        client_address = ('127.0.0.1', 12346)
        PyOcrServer(server_address)
        client = PyOcrClient(server_address, client_address)
        id = client.request_text_info_list(r'C:\Users\ocg20\Pictures\2023-08-25\New folder\016_1_1550_775.png',
                                           rect_mode=PyOcr.ltwh)
        print(client.fetch_text_info_list(id))
