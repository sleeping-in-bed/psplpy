import datetime
import os
import random
import re
import sys
import time
from typing import Tuple

import pyperclip
import uiautomation as auto
import file_util
import other_util

auto.uiautomation.DEBUG_SEARCH_TIME = False


def run_automation(write_path: str = None) -> str:
    log_file = '@AutomationLog.txt'
    if os.path.exists(log_file):
        os.remove(log_file)
    python_path = sys.executable
    result = other_util.run_command(
        f'{python_path} {os.path.join(os.path.join(os.path.dirname(python_path), "Scripts"), "automation.py")}')
    if write_path:
        with open(write_path, 'w', encoding='utf-8') as f:
            f.write(result)
    return result


def get_components_image(top_window, save_dir: str, control_type: str = None, start_interval: float = 5) -> None:
    def get_image(control_type: str) -> None:
        count = 1
        while True:
            command = f'top.{control_type}(foundIndex={count})'
            c = eval(command)
            if c.Exists(0.1):
                print(c)
                path = os.path.join(save_dir, control_type + str(count) + '.png')
                print(path)
                c.CaptureToImage(path)
            else:
                break
            count += 1

    print(f'{start_interval}s后开始，请切换到目标窗口')
    time.sleep(start_interval)
    file_util.create_dir(save_dir)
    top = top_window
    if not control_type:
        for control_type in auto.ControlTypeNames:
            get_image(control_type)
    else:
        get_image(control_type)


def find_longest_common_interval(list1: list, list2: list) -> Tuple[Tuple, Tuple] | Tuple[None, None]:
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
    system_mes = ['Below are new messages']
    Sticker_mes = '[Sticker]'
    Custom_Stickers = 'Custom Stickers'
    All_Stickers = 'All Stickers'

    def __init__(self, set_top_most: bool = False):
        self.win = auto.WindowControl(Depth=1, ClassName='WeChatMainWndForPC')
        if set_top_most:
            self.win.SetTopmost(True)

    @staticmethod
    def _match_time_message(message: str) -> bool:
        match = re.match(AutoWechat.message_time_pattern, message)
        if match:
            return True

    @staticmethod
    def get_new_chat_message(new_message_list, old_message_list) -> list:
        new_interval, old_interval = find_longest_common_interval(new_message_list, old_message_list)
        return new_message_list[new_interval[1]: len(new_message_list)]

    def _send_sticker(self, sticker_class: str = All_Stickers, sticker_id: int = 1,
                      sticker_name: str = 'Laugh') -> None:
        sticker = self.win.ToolBarControl(Depth=12).ButtonControl(searchDepth=1, Name='Sticker')
        sticker.Click()
        stickerClass = self.win.CheckBoxControl(Depth=5, Name=sticker_class)
        stickerClass.Click()
        if sticker_class == AutoWechat.All_Stickers:
            certain_sticker = self.win.ListItemControl(Depth=5, Name=sticker_name)
        elif sticker_class == AutoWechat.Custom_Stickers:
            certain_sticker = self.win.ListItemControl(Depth=6, foundIndex=sticker_id)
        else:
            raise ValueError
        certain_sticker.Click()

    def select_all_sticker(self, sticker_name: str = 'Laugh') -> None:
        self._send_sticker(AutoWechat.All_Stickers, sticker_name=sticker_name)

    def send_custom_sticker(self, sticker_id: int = 1) -> None:
        self._send_sticker(AutoWechat.Custom_Stickers, sticker_id)

    def send_message(self, message: str) -> None:
        entry = self.win.EditControl()
        entry.SendKeys(message)
        auto.SendKeys('{Enter}')

    def get_chat_sticker(self, sticker_name: str = Sticker_mes) -> auto.PaneControl:
        chat_sticker = self.win.ListItemControl(Depth=12, Name=sticker_name).PaneControl().PaneControl(
            foundIndex=2).PaneControl().PaneControl().PaneControl().PaneControl(foundIndex=2).PaneControl()
        return chat_sticker

    def get_chat_history(self) -> list:
        def ret_true(*args):
            return True

        chat_history_list = []
        count = 1
        sub = self.win.PaneControl(Depth=3, foundIndex=2).PaneControl().PaneControl().PaneControl().PaneControl(). \
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
        chat_history_list = [message for message in chat_history_list if message not in AutoWechat.system_mes]
        return chat_history_list


class AutoChrome:
    def __init__(self, set_top_most: bool = False):
        self.win = auto.PaneControl(Depth=1, ClassName='Chrome_WidgetWin_1')
        if set_top_most:
            self.win.SetTopmost(True)

    def get_tab(self, SubName: str):
        tab = self.win.TabItemControl(Depth=8, SubName=SubName)
        return tab


class AutoChatGPT(AutoChrome):
    def __init__(self, set_top_most: bool = False, premise_list: list = None):
        super().__init__(set_top_most=set_top_most)
        if not premise_list:
            self.premise_list = []
        else:
            self.premise_list = premise_list
        self.premise_str = self.get_premise_str()

    def get_premise_str(self):
        premise_str = '前提：'
        for index, premise in enumerate(self.premise_list):
            premise_str += f'{index + 1}.{premise}；'
        return premise_str

    def send_question(self, question: str):
        self.question = question
        question_entry = self.win.EditControl(Depth=11, Name='Send a message')
        pyperclip.copy(f'{self.premise_str}问题：{self.question}')
        question_entry.Click()
        question_entry.SendKeys('{Ctrl}v')
        question_entry.SendKeys('{Enter}')

    def get_chat_history(self) -> list:
        count = 1
        answer_win = self.win.DocumentControl().GroupControl().GroupControl().GroupControl().GroupControl(searchDepth=1, foundIndex=2)
        answer_win_sub = answer_win.GroupControl().GroupControl().GroupControl().GroupControl()
        chat_info = answer_win_sub.TextControl(searchDepth=5, foundIndex=count)
        chat_history_list = [chat_info.Name]
        count += 1
        while True:
            chat_info = answer_win_sub.TextControl(searchDepth=5, foundIndex=count)
            if chat_info:
                print(chat_info.Name)
                chat_history_list.append(chat_info.Name)
                count += 1
            else:
                break
        return chat_history_list

    def wait_generate_finish(self):
        regenerate_button = self.win.ButtonControl(Depth=11, Name='Regenerate')
        while True:
            if regenerate_button.Exists(1):
                break

    def get_answer(self) -> str:
        # sub = self.win.DocumentControl().GroupControl().GroupControl().GroupControl().GroupControl().GroupControl(foundIndex=2)
        # sub2 = sub.GroupControl().GroupControl().GroupControl().GroupControl()
        if not self.question:
            return ''
        else:
            self.wait_generate_finish()
            chat_history = self.get_chat_history()
            index = chat_history.index(f'{self.premise_str}问题：{self.question}')
            return '\n'.join(chat_history[index + 1:])



if __name__ == '__main__':
    # def test():
    #     set_time = '2023-08-08_05:55:10'
    #     format_str = '%Y-%m-%d_%H:%M:%S'
    #     datetime_obj = datetime.datetime.strptime(set_time, format_str)
    #     delta = datetime.timedelta(hours=1, minutes=45, seconds=59)
    #     has_send_first_message = False
    #
    #     send_count = 0
    #     wechat = AutoWechat()
    #     chat_history = wechat.get_chat_history()
    #     print(chat_history)
    #     while True:
    #         chat_history2 = wechat.get_chat_history()
    #         new_message_list = wechat.get_new_chat_message(chat_history2, chat_history)
    #         if datetime.datetime.now() >= datetime_obj:
    #             if new_message_list or not has_send_first_message:
    #                 print(new_message_list)
    #                 if send_count != 5:
    #                     wechat.send_custom_sticker(random.randint(1, 12))
    #                     send_count += 1
    #                     has_send_first_message = True
    #                     chat_history2.append(AutoWechat.Sticker_mes)
    #                 else:
    #                     message = 'hi'
    #                     wechat.send_message(message)
    #                     send_count = 0
    #                     has_send_first_message = False
    #                     datetime_obj = datetime_obj + delta
    #                     print(datetime_obj.strftime(format_str))
    #                     chat_history2.append(message)
    #                 chat_history = chat_history2
    #         time.sleep(0.2)
    #
    #
    # test()
    premise_list = ['你回答的所有文字均必须使用无格式的纯文本包括代码等文本，不允许任何的markdown语法被使用']
    gpt = AutoChatGPT(premise_list=premise_list)
    # l = gpt.send_question('使用python编写一段生成java代码的代码')
    # print(f'答案：{gpt.get_answer()}')
    print(gpt.get_chat_history())