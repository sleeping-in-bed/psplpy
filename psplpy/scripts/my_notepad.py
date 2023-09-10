import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFontDatabase, QTextOption
from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMessageBox, QApplication, QPlainTextEdit

from psplpy import gui_util


'''
know_error:
    1.Though it doesn't edit a binary file, it's still seen as edited file.
'''
class MenuBar(QMenuBar):
    def __init__(self, parent=None, filters: str = "All files (*.*);;Text documents (*.txt)",
                 edit=None, debug: bool = False):
        super().__init__(parent)

        self.parent = parent
        self.filters = filters
        self.edit = edit
        self.debug = debug

        self.path = None
        self.text = ''
        self.data = None
        self.set_data = None

        self.initUI()

    def initUI(self):
        file_menu = self.addMenu("&File")

        new_action = QAction('&New', self)
        new_action.triggered.connect(self.file_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.triggered.connect(self.file_open)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.triggered.connect(self.file_save)
        file_menu.addAction(save_action)

        save_as_file_action = QAction("Save &As...", self)
        save_as_file_action.triggered.connect(self.file_save_as)
        file_menu.addAction(save_as_file_action)

        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.file_exit)
        file_menu.addAction(exit_action)

        self.update_title()

    def _empty(self):
        self.path = None
        self.text = ''
        self.data = None
        if self.edit:
            self.edit.setPlainText(self.text)
        self.update_title()

    def _is_consistency(self) -> bool:
        text = self.edit.toPlainText()
        if text == self.text:
            return True

    def _save_check(self) -> QMessageBox.StandardButton | None:
        if self.edit:
            if not self._is_consistency():
                is_save = self._whether_save()
                if is_save == QMessageBox.StandardButton.Yes:
                    self.file_save()
                return is_save

    def _update_data(self, path, text, data):
        self.path = path
        self.text = text
        self.data = data

    def file_new(self):
        if self.edit:
            is_save = self._save_check()
            if is_save != QMessageBox.StandardButton.Cancel:
                self._empty()
        else:
            self._empty()

    def file_open(self):
        is_save = self._save_check()
        if is_save != QMessageBox.StandardButton.Cancel:
            path, _ = QFileDialog.getOpenFileName(self, "Open...", "", self.filters)
            success_flag = False

            if path:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = text = f.read()
                    success_flag = True
                except UnicodeDecodeError:
                    try:
                        with open(path, 'rb') as file:
                            data = file.read()
                            text = data.decode('utf-8', errors='replace')
                        success_flag = True
                    except Exception as e:
                        self.dialog_critical(str(e))
                except Exception as e:
                    self.dialog_critical(str(e))
                if success_flag:
                    self._update_data(path, text, data)
                    if self.debug:
                        print(data)
                    if self.edit:
                        self.edit.setPlainText(text)
                self.update_title()

    def file_save(self) -> bool:
        if not self.path:
            # If we do not have a path, we need to use Save As.
            return self.file_save_as()
        return self._save_to_path(self.path)

    def file_save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Save As...", "", self.filters)

        if not path:
            # If dialog is cancelled, will return ''
            return False

        return self._save_to_path(path)

    def _save_to_path(self, path: str) -> bool:
        if self.set_data:
            data = self.set_data
            self.set_data = None
        else:
            data = self.edit.toPlainText()
        try:
            if isinstance(data, str):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(data)
            else:
                with open(path, 'wb') as f:
                    f.write(data)
        except Exception as e:
            self.dialog_critical(str(e))
            return False
        else:
            self._update_data(path, data, data)
        self.update_title()
        if self.debug:
            print(f'Save to {path} successful!')
        return True

    def _whether_save(self) -> QMessageBox.StandardButton:
        dlg = QMessageBox(self)
        dlg.setWindowTitle(self.get_title())
        dlg.setText(f'Do you want to save changes to {self.get_title()}')
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        button = dlg.exec()
        button = QMessageBox.StandardButton(button)
        if self.debug:
            print(button)
        return button

    def _close_window(self):
        self.parent.close()
        self.parent = None

    def file_exit(self):
        if not self._is_consistency():
            is_save = self._whether_save()
            if is_save == QMessageBox.StandardButton.Yes:
                self.file_save()
            elif is_save != QMessageBox.StandardButton.Cancel:
                self._close_window()
        else:
            self._close_window()

    def get_text(self) -> str:
        return self.text

    def get_data(self) -> str | bytes:
        return self.data

    def set_data(self, s: str | bytes):
        self.set_data = s

    def dialog_critical(self, s: str):
        dlg = QMessageBox(self.parent)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.show()

    def get_title(self):
        return os.path.basename(self.path) if self.path else "Untitled"

    def update_title(self):
        self.parent.setWindowTitle(self.get_title())


class Notepad(gui_util.PyMainWindow):
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug

        self.editor = QPlainTextEdit()  # Could also use a QTextEdit and set self.editor.setAcceptRichText(False)
        self.editor.setWordWrapMode(QTextOption.WrapMode.NoWrap)  # 取消自动换行
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # 横向滚动条始终显示

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(12)
        self.editor.setFont(fixed_font)

        menubar = MenuBar(self, edit=self.editor, debug=debug)
        self.setMenuBar(menubar)

        self.setCentralWidget(self.editor)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    notepad = Notepad()
    notepad.show()

    app.exec()
