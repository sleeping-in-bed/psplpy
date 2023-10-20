import unicodedata


def get_all_utf8_chrs(show_info: bool = True, write_to_file: str = None) -> None | dict:
    # 定义UTF-8字符范围（从U+0000到U+10FFFF）
    start = 0x0000
    end = 0x10FFFF

    chr_dict = {}
    surrogate_list = []
    # 使用循环遍历
    for code_point in range(start, end + 1):
        character = chr(code_point)  # 尝试将代码点转换为字符
        # 检验字符是否可以编码
        try:
            character.encode('utf-8')
            chr_dict[code_point] = character
        except UnicodeEncodeError:
            # surrogates pairs 代理对字符
            surrogate_list.append(code_point)
    if show_info:
        print(f'number of surrogates: {len(surrogate_list)}')
        print(f'number of being able to encode: {len(chr_dict)}')
    if write_to_file:
        with open(write_to_file, 'w', encoding='utf-8') as f:
            f.write(''.join(chr_dict.values()))
    else:
        return chr_dict


def get_unicode_name(character: str) -> str:
    # 使用unicodedata查找字符的Unicode名称
    unicode_name = unicodedata.name(character)
    return unicode_name


def find_list_duplicates(lst: list) -> dict:
    '''
    find out all duplicate items in list, return the item: [offset] dict
    :return: {item1: [offset1, offset2, ...], item2: ..., ...}
    '''
    duplicates = {}
    for i, item in enumerate(lst):
        if item in duplicates:
            duplicates[item].append(i)
        else:
            duplicates[item] = [i]

    result = {}
    for item, indices in duplicates.items():
        if len(indices) > 1:
            result[item] = indices

    return result


def sorted_dict_according_to_value(dic: dict, reversed: bool = False) -> dict:
    return dict(sorted(dic.items(), key=lambda item: item[1]), reversed=reversed)
