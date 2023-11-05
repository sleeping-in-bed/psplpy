import inspect
import multiprocessing
import os
import shutil
import time
import fitz
import psutil

import data_process, file_util, image_util, interact_util, ocr_util


class PDFProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = fitz.open(self.pdf_path, filetype='pdf')

    def select(self, page_list: list) -> list:
        self.pdf.select(page_list)  # select the pages by the order of the list
        return page_list

    def delete(self, page_list: list) -> list:
        for page in page_list:
            self.pdf.delete_page(page)
        return page_list

    def save(self, save_path: str = None) -> str:
        if not save_path:
            save_path = file_util.rename_duplicate_file(self.pdf_path)
        self.pdf.save(save_path)
        return save_path


class PDFOCR:
    dpi = 600

    def __init__(self, pdf_path: str, ocr: ocr_util.PyOcr, number_of_processing: int = 1, save_path: str = None,
                 skip_page_set: set = None, auto_skip: bool = False, render_page_to_image: bool = False,
                 image_processor: str = None,
                 temp_dir: str = file_util.base_dir(__file__, 'temp'), show_process: bool = True, debug: bool = False):
        self.pdf_path = pdf_path
        self.ocr = ocr
        self.number_of_processing = number_of_processing
        self.save_path = save_path or file_util.rename_duplicate_file(self.pdf_path)
        self.skip_page_set = skip_page_set or set()
        self.auto_skip = auto_skip
        self.render_page_to_image = render_page_to_image
        self.image_processor = image_processor
        self.temp_dir = file_util.create_dir(temp_dir)
        self.show_process = show_process
        self.debug = debug

        self.kwargs = {'pdf_path': self.pdf_path, 'number_of_processing': self.number_of_processing,
                       'auto_skip': auto_skip, 'render_page_to_image': self.render_page_to_image,
                       'image_processor': image_processor, 'temp_dir': self.temp_dir, 'show_process': self.show_process,
                       'debug': self.debug, 'dpi': self.dpi}

        self._check_system_state()

        self.pdf = fitz.open(self.pdf_path, filetype='pdf')
        self.pages_image = self.get_page_image()
        self.new_pdf_list = []
        self.all_text_info_dict = {}

    def _check_system_state(self):
        memory = psutil.virtual_memory()
        predictive_memory_usage = (1024 * 1024) * (self.number_of_processing + 1)
        cpu_count = os.cpu_count()
        if memory.available < predictive_memory_usage or cpu_count < self.number_of_processing:
            print(f'当前剩余内存: {psutil._common.bytes2human(memory.available)}，cpu核心数: {cpu_count}')
            print(f'当前设置进程数: {self.number_of_processing}')
            # 最小进程数为1，其次是剩余内存GB数-1 和 cpu核心数中的最小值
            recommend_number_of_process = min(max(1, memory.available // (1024 * 1024 * 1024)), cpu_count)
            print(f'推荐设置进程数不大于: {recommend_number_of_process}')
            print_str = '输入1继续运行，输入2更改进程数，输入3设置进程数为推荐最大进程数并继续运行'
            error_tip = '输入错误，请重新输入'
            choose = interact_util.limited_input(['1', '2', '3'], print_str=print_str, error_tip=error_tip)
            if choose == '2':
                self.number_of_processing = int(interact_util.limited_input(
                    regex_list=[r'^\d+$'], print_str='请输入新的进程数', error_tip=error_tip))  # 判断是否是整数
            elif choose == '3':
                self.number_of_processing = recommend_number_of_process

    @staticmethod
    def _multiprocess(p_num, target, args_list=None, kwargs_list=None):
        p_list = []
        args_list = args_list or [() for _ in range(p_num)]
        kwargs_list = kwargs_list or [{} for _ in range(p_num)]
        for i in range(p_num):
            p = multiprocessing.Process(target=target, args=args_list[i], kwargs=kwargs_list[i])
            p_list.append(p)
        for p in p_list:
            p.start()
        for p in p_list:
            p.join()

    @staticmethod
    def _get_page_image(page_list, image_dict, **kwargs):
        def _get_pix(image):
            xref = image[0]  # get the XREF of the image
            pix = fitz.Pixmap(pdf, xref)  # create a Pixmap
            if pix.n - pix.alpha > 3:  # CMYK: convert to RGB first
                pix = fitz.Pixmap(fitz.csRGB, pix)
            return pix

        def _get_image_path(image, page_index, suffix='') -> str:
            pix = _get_pix(image)
            image_name = f'{os.path.splitext(os.path.basename(kwargs["pdf_path"]))[0]}{page_index}{suffix}.png'
            image_path = os.path.join(kwargs['temp_dir'], image_name)
            pix.save(image_path)
            return image_path

        pdf = fitz.open(kwargs['pdf_path'], filetype='pdf')
        for page_index in page_list:
            page = pdf[page_index]  # get the page
            if not kwargs['render_page_to_image']:
                image_list = page.get_images()
                if len(image_list) > 1:  # 每页图片不止一个，说明不是纯扫描图pdf
                    for index, image in enumerate(image_list):
                        image_path = _get_image_path(image, page_index, suffix=f'_{index}')
                    info = f'Page {page_index} has {len(image_list)} images, not equals one.' + \
                           f'Please check this directory: {os.path.dirname(image_path)}'
                    if kwargs['auto_skip']:
                        print('\n' + info)
                    else:
                        raise ValueError(info)
                elif len(image_list) < 1:
                    raise ValueError(f'No image in page {page_index}.')
                else:
                    image_path = _get_image_path(image_list[0], page_index)
                    image_dict[page_index] = image_path
            else:
                pix = page.get_pixmap(dpi=kwargs['dpi'])  # render page to an image
                image_name = f'{os.path.splitext(os.path.basename(kwargs["pdf_path"]))[0]}{page_index}.png'
                image_path = os.path.join(kwargs['temp_dir'], image_name)
                pix.save(image_path)  # store image as a PNG
                image_dict[page_index] = image_path
            if kwargs['show_process']:
                print(f'图像获取进度：{kwargs["count"].value}/{kwargs["sum"]}，'
                      f'已用时间：{time.perf_counter() - kwargs["very_start"]:.1f}s')
                kwargs["count"].value += 1

    def get_page_image(self):
        if self.show_process: print('正在获取每页图片')
        very_start = time.perf_counter()
        p_num = self.number_of_processing
        page_list = [index for index in range(len(self.pdf)) if index not in self.skip_page_set]
        page_lists = data_process.split_list(page_list, p_num)
        image_dict = multiprocessing.Manager().dict()
        count = multiprocessing.Value("i", 0)

        self._multiprocess(p_num, self._get_page_image, args_list=[(page_lists[i], image_dict) for i in range(p_num)],
                           kwargs_list=[{'count': count, 'sum': len(page_list), 'very_start': very_start,
                                         **self.kwargs} for _ in range(p_num)])

        return dict(sorted(image_dict.items()))   # 多进程的字典键序是乱的，排一下序

    def _get_all_text_info(self) -> None:
        server_address = ('127.0.0.1', 12345)
        client_address = ('127.0.0.1', 12346)
        ocr_util.PyOcrServer(server_address, number_of_processing=self.number_of_processing)
        ocr_client = ocr_util.PyOcrClient(server_address, client_address)
        id_dict = {}
        if self.show_process: print('正在读取图片到OCR')
        for key in self.pages_image:
            id_dict[key] = ocr_client.request_text_info_list(self.pages_image[key])
            if self.show_process: interact_util.overlay_print(f'进度: {key}/{len(self.pages_image)}')
        if self.show_process: print('\n正在进行OCR')
        very_start = time.perf_counter()
        for key in id_dict:
            time_start = time.perf_counter()
            self.all_text_info_dict[key] = ocr_client.fetch_text_info_list(id_dict[key])
            if self.show_process:
                time_end = time.perf_counter()
                print(f'进度: {key}/{len(id_dict)}, 用时: {time_end - time_start:.1f}s'
                      f', 已用时间: {time_end - very_start:.0f}s'
                      f', 预计剩余时间: {(time_end - very_start) / (key + 1) * (len(id_dict) - key):.0f}s')
        if self.show_process: print(f'OCR完成，总计用时: {time.perf_counter() - very_start:.1f}s')

    @staticmethod
    def _image_process(image_list, **kwargs):
        for image_path in image_list:
            eval(f'{kwargs["image_processor"]}(r"{image_path}")')
        if kwargs['show_process']:
            print(f'图像处理进度：{kwargs["count"].value}/{kwargs["sum"]}，'
                  f'已用时间：{time.perf_counter() - kwargs["very_start"]:.1f}s')
            kwargs["count"].value += 1

    def image_process(self):
        very_start = time.perf_counter()
        p_num = self.number_of_processing
        image_lists = data_process.split_list(list(self.pages_image.values()), p_num)
        count = multiprocessing.Value("i", 0)
        self._multiprocess(p_num, self._image_process, [(image_lists[i],) for i in range(p_num)],
                           [{'count': count, 'sum': len(self.pages_image), 'very_start': very_start,
                             **self.kwargs} for _ in range(p_num)])

    def ocr_pdf(self):
        if self.image_processor:
            self.image_process()
        self._get_all_text_info()
        if self.show_process: print('正在将OCR结果写入pdf')
        for index in range(len(self.pdf)):
            time_start = time.perf_counter()
            doc_path = os.path.join(self.temp_dir, f'{index}.pdf')
            print(doc_path)
            if self.all_text_info_dict.get(index):
                image_doc = fitz.open(self.pages_image[index])
                b = image_doc.convert_to_pdf()  # convert to pdf
                doc = fitz.open("pdf", b)  # open as pdf
                page = doc[0]
                wrote_text_list = self._write_text(self.all_text_info_dict[index], page)
                doc.save(doc_path)
                if self.show_process:
                    print(f'进度(页): {index}/{len(self.pages_image)}, 用时: {time.perf_counter() - time_start:.1f}s')
                if self.debug: print(wrote_text_list)
            else:
                skipped_pdf = fitz.open(self.pdf_path, filetype='pdf')
                skipped_pdf.select([index])
                skipped_pdf.save(doc_path)
            self.new_pdf_list.append(doc_path)
        self.merge_pdfs()
        if not self.debug:
            shutil.rmtree(self.temp_dir)  # 移除临时目录
        return self.save_path

    def merge_pdfs(self):
        doc = fitz.open(self.new_pdf_list[0])
        for i in range(1, len(self.new_pdf_list)):
            doc.insert_pdf(fitz.open(self.new_pdf_list[i]))
        doc.save(self.save_path, garbage=4)
        return self.save_path

    def _write_text(self, text_info_list, page) -> list:
        wrote_text_list = []  # 记录已写入pdf的文字的信息
        for text_info in text_info_list:
            shape = page.new_shape()  # create Shape
            shape_test = page.new_shape()  # 测试字体大小用的shape

            min_rect = image_util.polygon_bounding_rect(text_info[0])  # 找出文字多边形框的外接矩形
            coordinate = [*min_rect[0], *min_rect[1]]  # 文字写入的矩形坐标
            # 使用fitz转换png为pdf时，写入文字坐标会对不上，这是文字坐标的缩小比例
            if not self.render_page_to_image:
                ratio = 0.75
            else:
                # dpi 300: 0.24,
                # ratio = (300 / self.dpi) * 0.24
                ratio = 0.75
            for i in range(0, len(coordinate)):  # 缩小坐标
                coordinate[i] = ratio * coordinate[i]
            rect = fitz.Rect(*coordinate)  # 创建矩形

            font_size = 100  # 初始字体大小
            oversize = False  # 字体过大标识
            while True:
                # 在pdf中插入方框，在方框中插入文字                      颜色设置为黑色
                rc = shape_test.insert_textbox(rect, text_info[1], color=(0, 0, 0), fontsize=font_size,
                                               fontname='none',  # 内置字体: 需要设置为不存在的内置字体，之后设置的字体文件才会生效
                                               fontfile='C:\\Windows\\Fonts\\simsun.ttc', align=fitz.TEXT_ALIGN_JUSTIFY)
                if rc >= 0:  # 如果字体合适会返回大于0的数
                    if not oversize:  # 如果从来没有过大，就说明字体不够大，增大字体
                        font_size = int(font_size * 1.5)
                    else:
                        # 实际在pdf中写入文本
                        shape.insert_textbox(rect, text_info[1], color=(0, 0, 0), fontsize=font_size,
                                             fontname='none', fontfile='C:\\Windows\\Fonts\\simsun.ttc',
                                             align=fitz.TEXT_ALIGN_RIGHT)
                        wrote_text_list.append([text_info, font_size])
                        break
                else:  # 如果字体过大，会返回不大于0的数，需要调小字体
                    oversize = True
                    font_size -= 1

            # 提交更改，overlay为False，说明文字为透明
            if self.debug:
                shape.commit(overlay=True)
            else:
                shape.commit(overlay=False)
        return wrote_text_list


if __name__ == '__main__':
    path = r'D:\WorkSpaceW\电子书架\EbooksLib\HTML5权威指南 (Adam Freeman) _扫描版.pdf'
    # pdf_processor = PDFProcessor(path)
    # pdf_processor.select([i for i in range(119, 120)])
    # path = pdf_processor.save()

    image_processor = (lambda image_path: (image_util.ImageProcess(image_path).resize(2).contrast(1.5).
        brightness(1.5).sharpness(0.5).binaryzation(255 - 20).resize(0.25).save()))
    image_processor = inspect.getsource(image_processor).split('=')[1][:-1]
    a = PDFOCR(path, ocr_util.PyOcr(), number_of_processing=8, render_page_to_image=True,
)
    print(a.ocr_pdf())
