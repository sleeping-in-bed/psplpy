import os
import shutil
import time

import fitz

import file_util
import interact_util
import ocr_util


class PDFProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = fitz.open(self.pdf_path, filetype='pdf')

    def delete(self, page_list: list) -> list:
        for page in page_list:
            self.pdf.delete_page(page - 1)
        return page_list

    def save(self, save_path: str = None) -> str:
        if not save_path:
            save_path = file_util.rename_duplicate_file(self.pdf_path)
        self.pdf.save(save_path)
        return save_path


class PDFOCR:
    def __init__(self, pdf_path: str, ocr: ocr_util.PyOcr, temp_dir: str = file_util.base_dir(__file__, 'temp'),
                 show_process: bool = True, debug: bool = False):
        self.pdf_path = pdf_path
        self.ocr = ocr
        self.temp_dir = file_util.create_dir(temp_dir)
        self.show_process = show_process
        self.debug = debug

        self.pdf = fitz.open(self.pdf_path, filetype='pdf')
        self.pages_image = self._extract_images()
        self.new_pdf = fitz.open()

    def _get_pix(self, image):
        xref = image[0]  # get the XREF of the image
        pix = fitz.Pixmap(self.pdf, xref)  # create a Pixmap
        if pix.n - pix.alpha > 3:  # CMYK: convert to RGB first
            pix = fitz.Pixmap(fitz.csRGB, pix)
        return pix

    def _extract_images(self) -> list:
        if self.show_process:
            print('正在获取每页图片')
        pages_image = []
        for page_index in range(0, len(self.pdf)):  # iterate over pdf pages
            if self.show_process:
                interact_util.overlay_print(f'进度: {page_index + 1}/{len(self.pdf)}')
            page = self.pdf[page_index]  # get the page
            image_list = page.get_images()
            if len(image_list) != 1:    # 每页图片不止一个，说明不是纯扫描图pdf
                raise ValueError(f'Page {page_index + 1} has {len(image_list)} images, not equals one.')
            else:
                pix = self._get_pix(image_list[0])
                image_name = f'{os.path.splitext(os.path.basename(self.pdf_path))[0]}{page_index}.png'
                image_path = os.path.join(self.temp_dir, image_name)
                pix.save(image_path)
                pages_image.append(image_path)
        if self.show_process:
            print()
        return pages_image

    def _create_new_page(self, file):
        image = fitz.open(file)  # open pic as document
        rect = image[0].rect  # pic dimension
        pdfbytes = image.convert_to_pdf()  # make a PDF stream
        image.close()  # no longer needed, close
        imgPDF = fitz.open("pdf", pdfbytes)  # open stream as PDF
        page = self.new_pdf.new_page(width=rect.width, height=rect.height)  # new page with pic dimension
        page.show_pdf_page(rect, imgPDF, 0)  # image fills the page
        return file, page

    def _ocr_and_write_text(self, file, page) -> list:
        text_info_list = self.ocr.get_text_info_list(file, rect_mode=ocr_util.PyOcr.ltrb)
        wrote_text_list = []  # 记录已写入pdf的文字的信息
        for text_info in text_info_list:
            shape = page.new_shape()  # create Shape
            shape_test = page.new_shape()  # 测试字体大小用的shape

            coordinate = [*text_info[0][0], *text_info[0][1]]  # 文字写入的坐标
            # 使用fitz转换png为pdf时，写入文字坐标会对不上，这是文字坐标的缩小比例
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

    def ocr_pdf(self, save_path: str = None):
        # iterate the scanned images
        very_start = time.perf_counter()
        for index, file in enumerate(self.pages_image, start=1):
            time_start = time.perf_counter()
            file, page = self._create_new_page(file)
            wrote_text_list = self._ocr_and_write_text(file, page)
            if self.show_process:
                time_end = time.perf_counter()
                print(f'进度(页): {index}/{len(self.pages_image)}, 用时: {time_end - time_start:.1f}s'
                      f', 预计剩余时间: {(time_end - very_start) / index * (len(self.pages_image) - index):.0f}s')
            if self.debug:
                print(wrote_text_list)

        if not save_path:
            save_path = file_util.rename_duplicate_file(self.pdf_path)
        self.new_pdf.save(save_path)
        if not self.debug:
            shutil.rmtree(self.temp_dir)    # 移除临时目录
        return save_path


if __name__ == '__main__':
    path = r'D:\WorkSpace\PycharmProjects\pythonProject\PDF_OCR\all-my-pics1.pdf'
    # a(path)
    a = PDFOCR(path, ocr_util.PyOcr())
    print(a.ocr_pdf())
