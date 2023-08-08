import datetime
import random
import re
import time

import uiautomation as auto
# auto.uiautomation.DEBUG_SEARCH_TIME = True


def find_longest_common_interval(list1, list2):
    """return start and end indexes tuple with half-open interval"""
    max_length = 0
    max_interval1 = None
    max_interval2 = None

    for i in range(len(list1)):
        for j in range(len(list2)):
            if list1[i] == list2[j]:
                length = 1
                while i + length < len(list1) and j + length < len(list2) and list1[i + length] == list2[j + length]:
                    length += 1

                if length > max_length:
                    max_length = length
                    max_interval1 = (i, i + length)
                    max_interval2 = (j, j + length)

    if max_length == 0:
        return None, None
    else:
        return max_interval1, max_interval2


class AutoWechat:
    message_time_pattern = r'((?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday) \d{1,2}:\d{2} (?:AM|PM))|' \
              r'(?:\d{1,2}:\d{2} (?:AM|PM))|' \
              r'(?:Yesterday \d{1,2}:\d{2} (?:AM|PM))|' \
              r'(?:\d{1,2}-\d{1,2}-\d{2} \d{1,2}:\d{2} (?:AM|PM))'
    Sticker_mes = '[Sticker]'
    Custom_Stickers = 'Custom Stickers'
    All_Stickers = 'All Stickers'

    def __init__(self, set_top_most: bool = True):
        self.wcWin = auto.WindowControl(searchDepth=1, ClassName='WeChatMainWndForPC')
        if set_top_most:
            self.wcWin.SetTopmost(True)

    @staticmethod
    def _match_time_message(message: str) -> bool:
        match = re.match(AutoWechat.message_time_pattern, message)
        if match:
            return True

    @staticmethod
    def get_new_chat_message(new_message_list, old_message_list) -> list:
        new_interval, old_interval = find_longest_common_interval(new_message_list, old_message_list)
        return new_message_list[new_interval[1]: len(new_message_list)]

    def send_sticker(self, sticker_class: str = 'All Stickers', sticker_id: int = 1) -> None:
        sticker = self.wcWin.ToolBarControl(Depth=12).ButtonControl(searchDepth=1, Name='Sticker')
        sticker.Click()
        stickerClass = self.wcWin.CheckBoxControl(Depth=5, Name=sticker_class)
        stickerClass.Click()
        certain_sticker = self.wcWin.ListItemControl(Depth=6, foundIndex=sticker_id)
        certain_sticker.Click()

    def send_message(self, message: str) -> None:
        entry = self.wcWin.EditControl()
        entry.SendKeys(message)
        auto.SendKeys('{Enter}')

    def get_chat_sticker(self, sticker_name: str = '[Sticker]') -> auto.PaneControl:
        chat_sticker = self.wcWin.ListItemControl(Depth=12, Name=sticker_name).PaneControl().PaneControl(
            foundIndex=2).PaneControl().PaneControl().PaneControl().PaneControl(foundIndex=2).PaneControl()
        return chat_sticker

    def get_chat_history(self) -> list:
        def ret_true(*args):
            return True

        chat_history_list = []
        count = 1
        sub = self.wcWin.PaneControl(Depth=3, foundIndex=2).PaneControl().PaneControl().PaneControl().PaneControl(). \
            PaneControl(searchDepth=1, foundIndex=2)
        chat_info = sub.PaneControl().PaneControl().ListControl(searchDepth=1).ListItemControl(searchDepth=1,
                                                                                               foundIndex=count)
        while True:
            chat_info = chat_info.GetSiblingControl(ret_true)
            if chat_info:
                # print(chat_info.Name)
                chat_history_list.append(chat_info.Name)
                count += 1
            else:
                break
        # 获取的消息中会包含发送的时间信息，去掉这些时间信息，防止对是否有新消息发生误判
        chat_history_list = [message for message in chat_history_list if not AutoWechat._match_time_message(message)]
        return chat_history_list


if __name__ == '__main__':
    def test():
        set_time = '2023-08-08_05:55:10'
        format_str = '%Y-%m-%d_%H:%M:%S'
        datetime_obj = datetime.datetime.strptime(set_time, format_str)
        delta = datetime.timedelta(hours=1, minutes=45, seconds=59)
        has_send_first_message = False

        send_count = 0
        wechat = AutoWechat()
        chat_history = wechat.get_chat_history()
        print(chat_history)
        while True:
            chat_history2 = wechat.get_chat_history()
            new_message_list = wechat.get_new_chat_message(chat_history2, chat_history)
            if datetime.datetime.now() >= datetime_obj:
                if new_message_list or not has_send_first_message:
                    print(new_message_list)
                    if send_count != 5:
                        wechat.send_sticker(AutoWechat.Custom_Stickers, random.randint(1, 12))
                        send_count += 1
                        has_send_first_message = True
                        chat_history2.append(AutoWechat.Sticker_mes)
                    else:
                        message = 'hi'
                        wechat.send_message(message)
                        send_count = 0
                        has_send_first_message = False
                        datetime_obj = datetime_obj + delta
                        print(datetime_obj.strftime(format_str))
                        chat_history2.append(message)
                    chat_history = chat_history2
            time.sleep(0.2)


    test()
