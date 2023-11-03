import multiprocessing
import os
import shutil
import time
import fitz
import psutil
from PIL import Image, ImageEnhance

import data_process
import file_util
import image_util
import interact_util
import ocr_util


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
                 temp_dir: str = file_util.base_dir(__file__, 'temp'), show_process: bool = True, debug: bool = False):
        self.pdf_path = pdf_path
        self.ocr = ocr
        self.number_of_processing = number_of_processing
        self.save_path = save_path or file_util.rename_duplicate_file(self.pdf_path)
        self.skip_page_set = skip_page_set or set()
        self.auto_skip = auto_skip
        self.render_page_to_image = render_page_to_image
        self.temp_dir = file_util.create_dir(temp_dir)
        self.show_process = show_process
        self.debug = debug

        self._check_system_state()

        self.pdf = fitz.open(self.pdf_path, filetype='pdf')
        self.pages_image = self._extract_images()
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

    def _get_pix(self, image):
        xref = image[0]  # get the XREF of the image
        pix = fitz.Pixmap(self.pdf, xref)  # create a Pixmap
        if pix.n - pix.alpha > 3:  # CMYK: convert to RGB first
            pix = fitz.Pixmap(fitz.csRGB, pix)
        return pix

    def _get_image_path(self, image, page_index, suffix='') -> str:
        pix = self._get_pix(image)
        image_name = f'{os.path.splitext(os.path.basename(self.pdf_path))[0]}{page_index}{suffix}.png'
        image_path = os.path.join(self.temp_dir, image_name)
        pix.save(image_path)
        return image_path

    def _extract_images(self) -> dict:
        if self.show_process: print('正在获取每页图片')
        pages_image = {}
        for page_index in range(len(self.pdf)):  # iterate over pdf pages
            if self.show_process: interact_util.overlay_print(f'进度: {page_index}/{len(self.pdf)}')
            if page_index in self.skip_page_set:
                print(f'\nSkip: {page_index}')
            else:
                page = self.pdf[page_index]  # get the page
                if not self.render_page_to_image:
                    image_list = page.get_images()
                    if len(image_list) > 1:  # 每页图片不止一个，说明不是纯扫描图pdf
                        for index, image in enumerate(image_list):
                            image_path = self._get_image_path(image, page_index, suffix=f'_{index}')
                        info = f'Page {page_index} has {len(image_list)} images, not equals one.' + \
                               f'Please check this directory: {os.path.dirname(image_path)}'
                        if self.auto_skip:
                            self.skip_page_set.add(page_index)
                            print('\n' + info)
                        else:
                            raise ValueError(info)
                    elif len(image_list) < 1:
                        raise ValueError(f'No image in page {page_index}.')
                    else:
                        image_path = self._get_image_path(image_list[0], page_index)
                        pages_image[page_index] = image_path
                else:
                    pix = page.get_pixmap(dpi=self.dpi)  # render page to an image
                    image_name = f'{os.path.splitext(os.path.basename(self.pdf_path))[0]}{page_index}.png'
                    image_path = os.path.join(self.temp_dir, image_name)
                    pix.save(image_path)  # store image as a PNG
                    pages_image[page_index] = image_path

        if self.show_process: print()
        return pages_image

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
    def image_process(image_list: list, count, resize_ratio: float = 2, save_resize_ratio: float = 0.25,
                      contrast: float = 1.5,
                      brightness: float = 1.75, sharpness: float = 0.5, pure_black: bool = True, color_diff: int = 10):
        for image_path in image_list:
            image = Image.open(image_path)
            image = image.resize((int(image.width * resize_ratio), int(image.height * resize_ratio)))
            # 提高图像对比度
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)
            # 提高图像亮度
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)
            # 提高图像锐度
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(sharpness)

            if pure_black:
                # 将图片转换为灰度图
                image = image.convert('L')
                # 获得像素点的颜色数据
                pixels = image.load()

                differ = 255 - color_diff
                for i in range(image.width):
                    for j in range(image.height):
                        if differ <= pixels[i, j] <= 255:
                            pixels[i, j] = 255
                        else:
                            pixels[i, j] = 0
            image = image.resize((int(image.width * save_resize_ratio), int(image.height * save_resize_ratio)))
            image.save(image_path)
            print(f'{count.value}')
            count.value += 1

    def ocr_pdf(self):
        p_list = []
        image_lists = data_process.split_list(list(self.pages_image.values()), self.number_of_processing)
        count = multiprocessing.Value("i", 0)
        for i in range(self.number_of_processing):
            p = multiprocessing.Process(target=self.image_process, args=(image_lists[i], count))
            p_list.append(p)
            p.start()
        for p in p_list:
            p.join()

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
            shutil.rmtree(self.temp_dir)    # 移除临时目录
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
                                             align=fitz.TEXT_ALIGN_JUSTIFY)
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
    path = r'D:\WorkSpaceW\电子书架\EbooksLib\JavaScript权威指南（原书第7版）_ [美] David Flanagan  李松峰_19244750_zhelper-search.pdf'
    # pdf_processor = PDFProcessor(path)
    # pdf_processor.select([i for i in range(10)])
    # path = pdf_processor.save()

    a = PDFOCR(path, ocr_util.PyOcr(), number_of_processing=6, render_page_to_image=True)
    print(a.ocr_pdf())
