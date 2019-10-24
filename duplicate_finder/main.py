import cv2
import os
import numpy as np
import shutil

from datetime import datetime

from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGroupBox, QFileDialog, QVBoxLayout, QProgressBar, \
    QLabel, QLineEdit, QPushButton, QListWidget, QCheckBox
from PyQt5.QtCore import pyqtSlot, QThreadPool, pyqtSignal

from duplicate_finder.image_compare import ImageCompare
from worker import Worker


# Compares two images, one of which is already in an image format to save memory
def compare_files(image1, file2):
    height1, width1, channel1 = image1.shape
    image2 = cv2.imread(file2)
    height2, width2, channel2 = image2.shape

    if (not height1 == height2) or (not width1 == width2):
        return False

    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    err = np.sum((gray1.astype("float") - gray2.astype("float")) ** 2)
    err /= float(gray1.shape[0] * gray2.shape[1])

    return err == 0


class DuplicateFinder(QWidget):
    progress_signal = pyqtSignal(tuple)

    # File storage
    files = []
    duplicates = {}
    # Files that couldn't be moved
    file_move_error = []

    # Currently selected list item
    current_selection = None

    def __init__(self):
        super().__init__()

        self.show_all = QCheckBox('Show All Files')
        self.file_list = QListWidget()
        self.list_label = QLabel()
        self.find_button = QPushButton('Find All Duplicates')
        self.open_dup_dialog = QPushButton('Choose...')
        self.duplicate_box = QLineEdit()
        self.open_dialog = QPushButton('Choose...')
        self.text_box = QLineEdit()

        # Init layouts and progress bar
        self.move_button = QPushButton('Reset')
        self.remove_dupe = QPushButton('Mark as Original')
        self.show_preview = QPushButton('Show Preview')
        main_with_progress = QVBoxLayout()
        progress_bar_container = QGroupBox('Progress')
        prog_bar_box = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('Waiting (%p%)')
        prog_bar_box.addWidget(self.progress_bar)

        self.compare_prog = QProgressBar()
        self.compare_prog.setValue(0)
        self.compare_prog.setFormat('Waiting (%p%)')
        prog_bar_box.addWidget(self.compare_prog)

        progress_bar_container.setLayout(prog_bar_box)
        main_layout = QHBoxLayout()

        left_half = QGroupBox('Options')
        left_half.setLayout(self.init_left_half())
        main_layout.addWidget(left_half)

        right_half = QGroupBox('Files')
        right_half.setLayout(self.init_right_half())
        main_layout.addWidget(right_half)

        # Init thread
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.iterate_files)
        self.thread_worker.setAutoDelete(False)
        self.thread_worker.signals.progress.connect(self.progress_signal)
        self.thread_worker.signals.finished.connect(self.update_after_completion)

        # Finish up
        main_with_progress.addLayout(main_layout)
        main_with_progress.addWidget(progress_bar_container)
        self.setLayout(main_with_progress)

    def init_left_half(self):
        vert_left = QVBoxLayout()

        # File selection
        sel_label = QLabel('Read Directory')
        vert_left.addWidget(sel_label)
        folder_select_box = QHBoxLayout()
        self.text_box.textEdited.connect(self.can_find_files)
        folder_select_box.addWidget(self.text_box)
        self.open_dialog.clicked.connect(self.open_folder)
        folder_select_box.addWidget(self.open_dialog)
        vert_left.addLayout(folder_select_box)

        # Where to put duplicates
        dup_label = QLabel('Duplicate Directory')
        vert_left.addWidget(dup_label)
        duplicate_folder_sel = QHBoxLayout()
        self.duplicate_box.textEdited.connect(self.can_find_files)
        duplicate_folder_sel.addWidget(self.duplicate_box)
        self.open_dup_dialog.clicked.connect(self.open_duplicate_folder)
        duplicate_folder_sel.addWidget(self.open_dup_dialog)
        vert_left.addLayout(duplicate_folder_sel)
        vert_left.addStretch()

        self.find_button.clicked.connect(self.find_files)
        self.find_button.setEnabled(False)
        vert_left.addWidget(self.find_button)
        return vert_left

    def init_right_half(self):
        vert_right = QVBoxLayout()
        vert_right.addWidget(self.list_label)
        self.file_list.clicked.connect(self.list_clicked)
        vert_right.addWidget(self.file_list)

        # List selection tools
        list_tools = QHBoxLayout()
        self.show_preview.setEnabled(False)
        self.show_preview.clicked.connect(self.preview)
        list_tools.addWidget(self.show_preview)
        self.remove_dupe.setEnabled(False)
        self.remove_dupe.clicked.connect(self.remove_duplicate)
        list_tools.addWidget(self.remove_dupe)
        vert_right.addLayout(list_tools)

        self.show_all.setEnabled(False)
        vert_right.addWidget(self.show_all)
        self.show_all.clicked.connect(self.update_list)
        self.update_list()

        vert_right.addStretch()

        self.move_button.setEnabled(False)
        self.move_button.clicked.connect(self.move_files)
        vert_right.addWidget(self.move_button)
        return vert_right

    def init_gui(self, layout):
        # Init the basic window frame
        self.setWindowTitle('Duplicate Photo Detector v.1.5')
        self.setWindowIcon(QIcon('../icon.png'))
        self.setLayout(layout)
        self.show()

    def update_progress(self, status):
        self.compare_prog.setMinimum(status[0] + 1)
        self.compare_prog.setMaximum(len(self.files))
        self.progress_bar.setValue(status[0])
        self.compare_prog.setValue(status[1])

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
        self.open_dup_dialog.setEnabled(False)
        self.find_button.setEnabled(False)
        self.progress_bar.setFormat('Scanning (%p%)')
        for filename in Path(self.text_box.text()).glob('**/*.*'):
            if filename.as_uri().endswith(('.png', '.jpg', '.jpeg')):
                self.files.append(filename.as_posix())
        self.compare_prog.setFormat('Comparing (%p%)')
        self.progress_bar.setMaximum(len(self.files))
        self.thread_pool.start(self.thread_worker)

    def iterate_files(self, prog_sig):
        for first_img in range(len(self.files)):
            image1 = cv2.imread(self.files[first_img])
            for second_img in range(first_img + 1, len(self.files)):
                if compare_files(image1, self.files[second_img]):
                    self.duplicates[self.files[second_img]] = self.files[first_img]
                prog_sig.emit((first_img, second_img))

    @pyqtSlot()
    def update_after_completion(self):
        self.progress_bar.setFormat('Done (%p%)')
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.compare_prog.setMinimum(0)
        self.compare_prog.setValue(0)
        self.compare_prog.setFormat('Waiting (%p%)')
        self.show_all.setEnabled(True)
        self.move_button.setEnabled(True)
        self.update_list()

    @pyqtSlot()
    def list_clicked(self):
        if self.show_all.isChecked():
            return
        path = self.file_list.currentItem().text().replace('.', self.text_box.text(), 1)
        self.current_selection = path
        self.remove_dupe.setEnabled(True)
        self.show_preview.setEnabled(True)

    @pyqtSlot()
    def preview(self):
        ImageCompare(self.duplicates[self.current_selection], self.current_selection, self)

    @pyqtSlot()
    def remove_duplicate(self):
        self.duplicates.pop(self.current_selection)
        self.update_list()

    @pyqtSlot()
    def can_find_files(self):
        if os.path.isdir(self.text_box.text()) and os.path.isdir(self.duplicate_box.text()):
            self.find_button.setEnabled(True)
            self.progress_bar.setFormat('Ready (%p%)')
        else:
            self.find_button.setEnabled(False)
            self.progress_bar.setFormat('Waiting (%p%)')

    @pyqtSlot()
    def move_files(self):
        dup_loc = self.duplicate_box.text()
        if not dup_loc[-1] == '/':
            dup_loc += '/'
        for file in self.duplicates:
            try:
                shutil.move(file, dup_loc + file.split('/')[-1])
            except FileNotFoundError or PermissionError:
                self.file_move_error.append(file)
        self.write_log()
        self.reset()

    def reset(self):
        self.compare_prog.setFormat('Waiting (%p%)')
        self.progress_bar.setFormat('Waiting (%p%)')
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
        self.open_dup_dialog.setEnabled(True)
        self.show_all.setEnabled(False)
        self.update_list()
        self.show_all.setChecked(False)

    @pyqtSlot()
    def update_list(self):
        self.show_preview.setEnabled(False)
        self.remove_dupe.setEnabled(False)
        self.current_selection = None
        self.move_button.setText('Move Duplicates and Reset' if len(self.duplicates) > 0 else 'Reset')
        if self.show_all.isChecked():
            self.list_label.setText('Showing ' + str(len(self.files)) + ' file' +
                                    ('s' if not len(self.files) == 1 else '')
                                    + ' including ' + str(len(self.duplicates)) +
                                    ' duplicate' + ('s' if not len(self.duplicates) == 1 else ''))
            display = self.files
        else:
            self.list_label.setText('Showing ' + str(len(self.duplicates)) +
                                    ' duplicate' + ('s' if not len(self.duplicates) == 1 else ''))
            display = self.duplicates
        self.file_list.clear()
        for file in display:
            self.file_list.addItem(file.replace(self.text_box.text(), '.'))

    def write_log(self):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        file = open(self.duplicate_box.text() + '/log-' + dt_string.replace('/', '-').replace(':', '-') + '.txt', 'w')
        file.write('LOG FILE FOR JACK\'S DUPLICATE FINDER ON ' + dt_string + '\n')
        file.write('If two sections are touching, there are no items in the former section.\n')
        file.write('==========DIRECTORY SCANNED==========\n')
        file.write(self.text_box.text() + '\n')
        file.write('==========DUPLICATES FOUND==========\n')
        for dupe in self.duplicates:
            file.write('"' + dupe.replace(self.text_box.text(), '.') +
                       '" dupe of "' + self.duplicates[dupe].replace(self.text_box.text(), '.') + '"\n')
        file.write('==========ERROR MOVING FILES==========\n')
        for err in self.file_move_error:
            file.write(err.replace(self.text_box.text(), '.') + '\n')
        file.write('==========FILES SCANNED==========\n')
        for f in self.files:
            file.write(f.replace(self.text_box.text(), '.') + '\n')
