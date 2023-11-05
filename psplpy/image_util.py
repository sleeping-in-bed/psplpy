from io import BytesIO
from typing import Tuple, Any, List
import numpy as np
import pyautogui
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

"""
rect_format:
    ltwh: (left, top, width, height)
    ltrb: ((left, top), (right, bottom))
    four_vertexes: ((left, top), (right, top), (right, bottom), (left, bottom))
    
"""


def get_screen_box() -> tuple[int, int, int, int]:
    return 0, 0, *pyautogui.size()


def get_box_center(region: Tuple) -> Tuple[int, int]:
    region = trans_to_ltwh(region)
    return int(region[0] + region[2] * 0.5), int(region[1] + region[3] * 0.5)


def trans_to_ltwh(region: Tuple) -> Tuple:
    if len(region) == 4:
        if isinstance(region[0], int):  # ltwh
            return region
        elif len(region[0]) == 2:   # four vertexes
            return *region[0], region[2][0] - region[0][0], region[2][1] - region[0][1]
    elif len(region) == 2:
        if len(region[0]) == 2:     # ltrb
            return *region[0], region[1][0] - region[0][0], region[1][1] - region[0][1]
    raise ValueError(f'No match region type: {region}')


def trans_to_ltrb(region: Tuple) -> Tuple:
    if len(region) == 4:
        if isinstance(region[0], int):  # ltwh
            return (region[0], region[1]), (region[0] + region[2], region[1] + region[3])
        elif len(region[0]) == 2:   # four vertexes
            return region[0], region[2]
    elif len(region) == 2:  # ltrb
        if len(region[0]) == 2:
            return region
    raise ValueError(f'No match region type: {region}')


def draw_figures_on_pic(image: Any, figure_list: list, figure_type: str, save_path: str = '',
                        outline: str | Tuple[int, int, int] | Tuple[int, int, int, int] = 'red',
                        width: int = 1) -> [np.ndarray, str]:
    img = convert_image_to_ndarray(image)
    img = Image.fromarray(img)
    # create ImageDraw obj
    draw = ImageDraw.Draw(img)

    # draw polygons
    if figure_type == 'polygon':
        for figure in figure_list:
            draw.polygon(figure, outline=outline)
    # draw rectangles
    elif figure_type == 'rectangle':
        for figure in figure_list:
            draw.rectangle(figure, outline=outline, width=width)
    else:
        raise ValueError
    if save_path:
        img.save(save_path)
        return save_path
    else:
        return np.array(img)


def draw_polygons_on_pic(image: Any, polygon_list: list, save_path: str = '',
                         outline: str | Tuple[int, int, int] | Tuple[int, int, int, int] = 'red') -> [np.ndarray, str]:
    draw_figures_on_pic(image, polygon_list, 'polygon', save_path, outline)


def draw_rects_on_img(image: Any, rect_list: list, save_path: str = '',
                      outline: str | Tuple[int, int, int] | Tuple[int, int, int, int] = 'red',
                      width: int = 1) -> [np.ndarray, str]:
    rect_list = [trans_to_ltrb(region) for region in rect_list]
    draw_figures_on_pic(image, rect_list, 'rectangle', save_path, outline, width)


def convert_image_to_ndarray(image: Any) -> np.ndarray:
    if type(image) == str:
        img = Image.open(image)
        image_array = np.array(img)
    elif type(image) == np.ndarray:
        image_array = image
    elif isinstance(image, (list, tuple)):
        image_array = np.array(pyautogui.screenshot(region=trans_to_ltwh(image)))
    else:
        raise TypeError
    return image_array


def save_ndarray_image(image_array: np.ndarray, file_path: str) -> str:
    Image.fromarray(image_array).save(file_path)
    return file_path


def point_rotate_180(point: Tuple[int, int], size: Tuple[int, int]):
    return size[0] - point[0], size[1] - point[1]


def overlap_percentage(rect1: Tuple, rect2: Tuple) -> Tuple[float, float]:
    """calculate the ratio of the overlap of two rectangles to the area of each rectangle"""
    rect1 = trans_to_ltrb(rect1)
    rect2 = trans_to_ltrb(rect2)

    (x1, y1), (r1, b1) = rect1
    (x2, y2), (r2, b2) = rect2
    x_overlap = max(0, min(r1, r2) - max(x1, x2))
    y_overlap = max(0, min(b1, b2) - max(y1, y2))
    area1 = (r1 - x1) * (b1 - y1)
    area2 = (r2 - x2) * (b2 - y2)

    area_overlap = x_overlap * y_overlap
    percent1 = area_overlap / area1
    percent2 = area_overlap / area2

    return percent1, percent2


def point_in_polygon(point: [List, Tuple], polygon: [List, Tuple]) -> bool:
    """determine if the point in is inside the polygon
       polygon: [(x1, y1), (x2, y2), ..., (xn, yn)]"""

    # determine if the point on the edge
    if point in polygon:
        return True

    # calculate the number of points where the boundary of the polygon intersects with the ray
    count = 0
    for i in range(len(polygon)):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % len(polygon)]
        if ((p1[1] > point[1]) != (p2[1] > point[1])) and (point[0] < (p2[0] - p1[0]) *
                                                           (point[1] - p1[1]) / (p2[1] - p1[1]) + p1[0]):
            count += 1

    return count % 2 == 1


def polygon_bounding_rect(polygon: [List, Tuple]) -> Tuple:
    """find the smallest rectangle that can cover a polygon"""
    x_min = min(x for x, y in polygon)
    y_min = min(y for x, y in polygon)
    x_max = max(x for x, y in polygon)
    y_max = max(y for x, y in polygon)

    return (x_min, y_min), (x_max, y_max)


class ImageProcess:
    def __init__(self, image_path: str, save_path: str = None):
        self.image_path = image_path
        self.save_path = save_path or self.image_path
        self.image = Image.open(self.image_path)

    def resize(self, ratio: float):
        self.image = self.image.resize((int(self.image.width * ratio), int(self.image.height * ratio)))
        return self

    def contrast(self, contrast: float):
        enhancer = ImageEnhance.Contrast(self.image)
        self.image = enhancer.enhance(contrast)
        return self

    def brightness(self, brightness: float):
        enhancer = ImageEnhance.Brightness(self.image)
        self.image = enhancer.enhance(brightness)
        return self

    def sharpness(self, sharpness: float):
        enhancer = ImageEnhance.Sharpness(self.image)
        self.image = enhancer.enhance(sharpness)
        return self

    def grayscale(self):
        self.image = self.image.convert('L')
        # self.image = ImageOps.grayscale(self.image)   # backup
        return self

    def _is_grayscale(self):
        if len(self.image.getbands()) == 1:
            return True

    def binaryzation(self, threshold: int = 255 - 20):
        if not self._is_grayscale():
            self.grayscale()
        self.image = self.image.point(lambda p: p > threshold and 255)
        return self

    def invert(self):
        self.image = ImageOps.invert(self.image)
        return self

    def rotate(self, angle: float, expand: bool = True):
        self.image = self.image.rotate(angle, expand=expand)
        return self

    def save(self):
        self.image.save(self.save_path)
        return self.save_path

    def get_image(self):
        return self.image

    def get_ndarray(self):
        return np.array(self.image)

    def get_bytesio(self, format: str = 'PNG'):
        bytesio = BytesIO()
        self.image.save(bytesio, format=format)
        return bytesio


if __name__ == '__main__':
    path = r'C:\Users\ocg20\Desktop\IMG_20220724_162804.jpg'
    imgp = ImageProcess(path)
    bio = imgp.get_bytesio()
    image = Image.open(bio)
    image.show()
