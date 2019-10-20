import cv2
import sys
import os
import numpy as np
import gc
import shutil

from pathlib import Path
from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QGroupBox, QFileDialog, QVBoxLayout, QProgressBar, \
    QLabel, QLineEdit, QPushButton, QListWidget, QCheckBox
from PyQt5.QtCore import pyqtSlot


# Compares two images, one of which is already in an image format to save memory
def compare_files(image1, file2):
    height1, width1, channel1 = image1.shape
    image2 = cv2.imread(file2)
    height2, width2, channel2 = image2.shape

    # Does something that keeps my program responsive, but I don't know what it is
    cv2.waitKey(0)

    if (not height1 == height2) or (not width1 == width2):
        gc.collect()
        return False

    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    err = np.sum((gray1.astype("float") - gray2.astype("float")) ** 2)
    err /= float(gray1.shape[0] * gray2.shape[1])

    return err == 0


class MainWin(QWidget):

    def __init__(self):
        super().__init__()

        # File storage
        self.files = []
        self.duplicates = []

        # Init layouts and progress bar
        main_with_progress = QVBoxLayout()
        progress_bar_container = QGroupBox('Progress')
        prog_bar_box = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(' Waiting (%p%)')
        prog_bar_box.addWidget(self.progress_bar)

        self.compare_prog = QProgressBar()
        self.compare_prog.setValue(0)
        self.compare_prog.setFormat(' Waiting (%p%)')
        prog_bar_box.addWidget(self.compare_prog)

        progress_bar_container.setLayout(prog_bar_box)
        main_layout = QHBoxLayout()

        left_half = QGroupBox('Options')
        left_half.setLayout(self.init_left_half())
        main_layout.addWidget(left_half)

        right_half = QGroupBox('Files')
        right_half.setLayout(self.init_right_half())
        main_layout.addWidget(right_half)

        # Finish up
        main_with_progress.addLayout(main_layout)
        main_with_progress.addWidget(progress_bar_container)
        self.init_gui(main_with_progress)

    def init_left_half(self):
        vert_left = QVBoxLayout()

        # File selection
        sel_label = QLabel('Read Directory')
        vert_left.addWidget(sel_label)
        folder_select_box = QHBoxLayout()
        self.text_box = QLineEdit()
        self.text_box.textEdited.connect(self.can_find_files)
        folder_select_box.addWidget(self.text_box)
        self.open_dialog = QPushButton('Choose...')
        self.open_dialog.clicked.connect(self.open_folder)
        folder_select_box.addWidget(self.open_dialog)
        vert_left.addLayout(folder_select_box)

        # Where to put duplicates
        dup_label = QLabel('Duplicate Directory')
        vert_left.addWidget(dup_label)
        duplicate_folder_sel = QHBoxLayout()
        self.duplicate_box = QLineEdit()
        self.duplicate_box.textEdited.connect(self.can_find_files)
        duplicate_folder_sel.addWidget(self.duplicate_box)
        self.open_dup_diag = QPushButton('Choose...')
        self.open_dup_diag.clicked.connect(self.open_duplicate_folder)
        duplicate_folder_sel.addWidget(self.open_dup_diag)
        vert_left.addLayout(duplicate_folder_sel)
        vert_left.addStretch()

        self.find_button = QPushButton('Find All Duplicates')
        self.find_button.clicked.connect(self.find_files)
        self.find_button.setEnabled(False)
        vert_left.addWidget(self.find_button)
        return vert_left

    def init_right_half(self):
        vert_right = QVBoxLayout()
        self.list_label = QLabel()
        vert_right.addWidget(self.list_label)
        self.file_list = QListWidget()
        vert_right.addWidget(self.file_list)
        self.show_all = QCheckBox('Show All Files')
        vert_right.addWidget(self.show_all)
        self.show_all.clicked.connect(self.update_list)
        self.update_list()

        vert_right.addStretch()

        self.move_button = QPushButton('Move Duplicates and Reset')
        self.move_button.setEnabled(False)
        self.move_button.clicked.connect(self.move_files)
        vert_right.addWidget(self.move_button)
        return vert_right

    def init_gui(self, layout):
        # Init the basic window frame
        self.setWindowTitle('Duplicate Photo Detector v.1.0')
        self.setLayout(layout)
        self.show()

    @pyqtSlot()
    def open_folder(self):
        dialog = QFileDialog.getExistingDirectory(self, 'Open Directory', '/home')
        if dialog:
            self.text_box.setText(dialog)
            self.can_find_files()

    @pyqtSlot()
    def open_duplicate_folder(self):
        dialog = QFileDialog.getExistingDirectory(self, 'Open Directory', '/home')
        if dialog:
            self.duplicate_box.setText(dialog)
            self.can_find_files()

    @pyqtSlot()
    def find_files(self):
        self.text_box.setEnabled(False)
        self.duplicate_box.setEnabled(False)
        self.open_dialog.setEnabled(False)
        self.open_dup_diag.setEnabled(False)
        self.find_button.setEnabled(False)
        self.progress_bar.setFormat(' Scanning (%p%)')
        for filename in Path(self.text_box.text()).glob('**/*.*'):
            if filename.as_uri().endswith(('.png', '.jpg')):
                self.files.append(filename.as_posix())
        self.progress_bar.setFormat(' Scanning (%p%)')
        self.compare_prog.setFormat(' Comparing (%p%)')
        self.progress_bar.setMaximum(len(self.files))
        self.iterate_files()
        self.update_list()

    def iterate_files(self):
        for firstImg in range(len(self.files)):
            self.progress_bar.setValue(firstImg+1)
            self.compare_prog.setMinimum(firstImg+1)
            self.compare_prog.setMaximum(len(self.files))
            image1 = cv2.imread(self.files[firstImg])
            for secondImg in range(firstImg + 1, len(self.files)):
                self.compare_prog.setValue(secondImg)
                print('Comparing image ' + str(firstImg) + ' with image ' + str(secondImg))
                if compare_files(image1, self.files[secondImg]):
                    self.duplicates.append(self.files[secondImg])
        self.progress_bar.setFormat(' Done (%p%)')
        self.compare_prog.setMinimum(0)
        self.compare_prog.setValue(0)
        self.compare_prog.setFormat(' Waiting (%p%)')
        self.move_button.setEnabled(len(self.duplicates) > 0)

    @pyqtSlot()
    def can_find_files(self):
        if os.path.isdir(self.text_box.text()) and os.path.isdir(self.duplicate_box.text()):
            self.find_button.setEnabled(True)
            self.progress_bar.setFormat(' Ready (%p%)')
        else:
            self.find_button.setEnabled(False)
            self.progress_bar.setFormat(' Waiting (%p%)')

    @pyqtSlot()
    def move_files(self):
        dup_loc = self.duplicate_box.text()
        if not dup_loc[-1] == '/':
            dup_loc += '/'
        for file in self.duplicates:
            shutil.move(file, dup_loc+file.split('/')[-1])
        self.reset()

    def reset(self):
        self.compare_prog.setFormat(' Waiting (%p%)')
        self.progress_bar.setFormat(' Waiting (%p%)')
        self.progress_bar.setValue(0)
        self.move_button.setEnabled(False)
        self.list_label.setText('No files')
        self.files = []
        self.duplicates = []
        self.text_box.setText('')
        self.duplicate_box.setText('')
        self.text_box.setEnabled(True)
        self.duplicate_box.setEnabled(True)
        self.open_dialog.setEnabled(True)
        self.open_dup_diag.setEnabled(True)
        self.update_list()
        self.show_all.setChecked(False)

    @pyqtSlot()
    def update_list(self):
        if self.show_all.isChecked():
            self.list_label.setText('Showing ' + str(len(self.files)) + ' file' +
                                    ('s' if not len(self.files) == 1 else '')
                                    + ' including ' + str(len(self.duplicates)) +
                                    ' duplicate'+('s' if not len(self.duplicates) == 1 else ''))
            display = self.files
        else:
            self.list_label.setText('Showing ' + str(len(self.duplicates)) +
                                    ' duplicate'+('s' if not len(self.duplicates) == 1 else ''))
            display = self.duplicates
        self.file_list.clear()
        for file in display:
            self.file_list.addItem(file.replace(self.text_box.text(), '.'))


if __name__ == '__main__':
    app = QApplication([])
    win = MainWin()
    sys.exit(app.exec_())
