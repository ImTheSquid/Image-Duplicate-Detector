import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QHBoxLayout

from date_sorter.main import DateSorter
from duplicate_finder.main import DuplicateFinder


class Runner(QWidget):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        # Init the basic window frame
        self.setWindowTitle('Jack\'s Photo Utilities v.1.7')
        self.setWindowIcon(QIcon('icon.png'))
        layout = QHBoxLayout()
        tabs = QTabWidget()
        duplicate_detector = DuplicateFinder()
        tabs.addTab(duplicate_detector, 'Duplicate Finder')
        date_sorter = DateSorter()
        tabs.addTab(date_sorter, 'Date Sorter')
        layout.addWidget(tabs)
        self.setLayout(layout)
        self.show()


if __name__ == '__main__':
    app = QApplication([])
    win = Runner()
    sys.exit(app.exec_())
