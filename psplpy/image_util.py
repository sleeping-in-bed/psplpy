from typing import Tuple, Any, List
import numpy as np
import pyautogui
from PIL import Image, ImageDraw

import file_util


def four_vertexes_transform_to_ltrb(four_vertexes: [List, Tuple]) -> Tuple:
    return four_vertexes[0], four_vertexes[2]


def ltrb_transform_to_ltwh(region: [List, Tuple]) -> Tuple:
    """convert ((left, top), (right, bottom)) to (left, top, width, height)"""
    if len(region) == 4:
        return region
    elif len(region) == 2:
        if len(region[0]) == 2 and len(region[1]) == 2:
            return *region[0], region[1][0] - region[0][0], region[1][1] - region[0][1]
        else:
            raise ValueError('Wrong length of region')
    raise ValueError('Wrong length of region')


def ltwh_transform_to_ltrb(region: [List, Tuple]) -> Tuple:
    """convert (left, top, width, height) to ((left, top), (right, bottom))"""
    if len(region) == 4:
        return (region[0], region), (region[0] + region[2], region[1] + region[3])
    elif len(region) == 2:
        if len(region[0]) == 2 and len(region[1]) == 2:
            return region
        else:
            raise ValueError('Wrong length of region')
    raise ValueError('Wrong length of region')


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
        dst_path = file_util.rename_duplicate_file(save_path)
        img.save(dst_path)
        return dst_path
    else:
        return np.array(img)


def draw_polygons_on_pic(image: Any, polygon_list: list, save_path: str = '',
                         outline: str | Tuple[int, int, int] | Tuple[int, int, int, int] = 'red') -> [np.ndarray, str]:
    draw_figures_on_pic(image, polygon_list, 'polygon', save_path, outline)


def draw_rects_on_img(image: Any, rect_list: list, save_path: str = '',
                      outline: str | Tuple[int, int, int] | Tuple[int, int, int, int] = 'red',
                      width: int = 1) -> [np.ndarray, str]:
    rect_list = [ltwh_transform_to_ltrb(region) for region in rect_list]
    draw_figures_on_pic(image, rect_list, 'rectangle', save_path, outline, width)


def convert_image_to_ndarray(image: Any) -> np.ndarray:
    if type(image) == str:
        img = Image.open(image)
        image_array = np.array(img)
    elif type(image) == np.ndarray:
        image_array = image
    elif isinstance(image, (list, tuple)):
        image_array = np.array(pyautogui.screenshot(region=ltrb_transform_to_ltwh(image)))
    else:
        raise TypeError
    return image_array


def save_ndarray_image(image_array: np.ndarray, file_path: str) -> str:
    Image.fromarray(image_array).save(file_path)
    return file_path


def enlarge_img(image: Any, rate: float = 2, save_path: str = None, x_rate: float = None,
                y_rate: float = None) -> [np.ndarray, str]:
    img = convert_image_to_ndarray(image)
    img = Image.fromarray(img)
    if (not x_rate and y_rate) or (x_rate and not y_rate):
        raise ValueError('x_rate and y_rate must be given at the same time')
    else:
        if x_rate and y_rate:
            enlarged_image = img.resize((int(img.width * x_rate), int(img.height * y_rate)))
        else:
            enlarged_image = img.resize((int(img.width * rate), int(img.height * rate)))
    if save_path:
        dst_path = file_util.rename_duplicate_file(save_path)
        enlarged_image.save(dst_path)
        return dst_path
    else:
        return np.array(enlarged_image)


def overlap_percentage(rect1: Tuple[float, float, float, float], rect2: Tuple[float, float, float, float]
                       ) -> Tuple[float, float]:
    """calculate the ratio of the overlap of two rectangles to the area of each rectangle"""
    rect1 = ltwh_transform_to_ltrb(rect1)
    rect2 = ltwh_transform_to_ltrb(rect2)

    x1, y1, r1, b1 = rect1
    x2, y2, r2, b2 = rect2
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


def find_minimum_bounding_rect(polygon: [List, Tuple]) -> Tuple:
    """find the smallest rectangle that can cover a polygon"""
    x_min = min(x for x, y in polygon)
    y_min = min(y for x, y in polygon)
    x_max = max(x for x, y in polygon)
    y_max = max(y for x, y in polygon)

    return (x_min, y_min), (x_max, y_max)
