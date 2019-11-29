import sys

from PyQt5.QtGui import QIcon, QPixmap, QImageReader
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QHBoxLayout

from albums.main import Albums
from date_sorter.main import DateSorter
from duplicate_finder.main import DuplicateFinder


class Runner(QWidget):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        # Init the basic window frame
        self.setWindowTitle('Jack\'s Photo Utilities v.2.2')
        pix = QPixmap(QImageReader('assets/icon.png').read())
        self.setWindowIcon(QIcon(pix))
        layout = QHBoxLayout()
        tabs = QTabWidget()
        duplicate_detector = DuplicateFinder()
        tabs.addTab(duplicate_detector, 'Duplicate Finder')
        date_sorter = DateSorter()
        tabs.addTab(date_sorter, 'Date Sorter')
        albums = Albums()
        tabs.addTab(albums, 'Albums')
        layout.addWidget(tabs)
        self.setLayout(layout)
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    win = Runner()
    sys.exit(app.exec_())
