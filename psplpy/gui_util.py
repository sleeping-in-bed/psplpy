import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication

import file_util


class PyMainWindow(QMainWindow):
    def __init__(self, title: str = 'python',
                 icon_path: str = file_util.get_abspath_from_relpath(__file__, r'data/icon.png'),
                 length_ratio: float = 3 / 5):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon_path))
        self.length_ratio = length_ratio

        self.initUI()

    def initUI(self):
        size = self.screen().availableSize()

        margin = (1 - self.length_ratio) / 2
        x = int(size.width() * margin)
        y = int(size.height() * margin)
        w = int(size.width() * self.length_ratio)
        h = int(size.height() * self.length_ratio)
        self.setGeometry(x, y, w, h)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PyMainWindow('simple app')
    window.show()
    app.exec()
