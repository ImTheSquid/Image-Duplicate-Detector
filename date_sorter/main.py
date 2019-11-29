import os
import shutil
from datetime import datetime
from os.path import basename, join
from pathlib import Path

from PIL import Image, ExifTags
from PyQt5.QtCore import pyqtSignal, QThreadPool, Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QLineEdit, \
    QFileDialog, QRadioButton, QPushButton, QMessageBox

from worker import Worker


# Checks if a directory exists, then moves the specified file to that directory
def check_exists(new_dir, file):
    # Makes directories and moves files
    os.makedirs(new_dir, exist_ok=True)
    shutil.move(file, join(new_dir, basename(file)))


def convert_to_month(mon):
    return {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'}[mon]


class DateSorter(QWidget):
    progress_signal = pyqtSignal(tuple)
    files = []

    def __init__(self):
        super().__init__()

        self.choose_dest_dir = QPushButton('Choose...')
        self.start = QPushButton('Start')
        self.days = QRadioButton('Years, Months, and Days')
        self.months = QRadioButton('Years and Months')
        self.years = QRadioButton('Years')
        self.sorted_text = QLineEdit()
        self.choose_dir = QPushButton('Choose...')
        self.read_text = QLineEdit()

        # Thread stuff
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.sort_photos)
        self.thread_worker.setAutoDelete(False)
        self.thread_worker.signals.progress.connect(self.progress_signal)
        self.thread_worker.signals.finished.connect(self.update_after_completion)

        layout = QVBoxLayout()
        options = QGroupBox('Options')
        options.setLayout(self.setup_options())
        progress = QGroupBox('Progress')
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('Waiting (%p%)')
        progress_layout.addWidget(self.progress_bar)
        progress.setLayout(progress_layout)
        layout.addWidget(options)
        layout.addWidget(progress)
        self.setLayout(layout)

    def setup_options(self):
        options = QVBoxLayout()
        read_dir_label = QLabel('Read Directory')
        options.addWidget(read_dir_label)

        read_box = QHBoxLayout()
        self.read_text.textEdited.connect(self.can_start_sort)
        read_box.addWidget(self.read_text)
        self.choose_dir.clicked.connect(self.open_chooser)
        read_box.addWidget(self.choose_dir)
        options.addLayout(read_box)

        dest_dir_label = QLabel('Destination Directory')
        options.addWidget(dest_dir_label)

        dest_box = QHBoxLayout()
        self.sorted_text.textEdited.connect(self.can_start_sort)
        dest_box.addWidget(self.sorted_text)
        self.choose_dest_dir.clicked.connect(self.open_dest_chooser)
        dest_box.addWidget(self.choose_dest_dir)

        options.addLayout(dest_box)

        radios = QVBoxLayout()
        sort_type_label = QLabel('Sort Type')
        radios.addWidget(sort_type_label)
        self.years.setChecked(True)
        radios.addWidget(self.years)
        radios.addWidget(self.months)
        radios.addWidget(self.days)
        options.addLayout(radios)

        options.addStretch()

        warning = QLabel('WARNING: There is no check for file permissions.\n'
                         'If you do not have permissions to access the selected directories the program will crash.')
        warning.setStyleSheet('color:#FF0000')
        warning.setAlignment(Qt.AlignCenter)

        self.start.setEnabled(False)
        self.start.clicked.connect(self.start_sorter)
        options.addWidget(warning)
        options.addWidget(self.start)

        return options

    def can_start_sort(self):
        if os.path.isdir(self.read_text.text()) and os.path.isdir(self.sorted_text.text()):
            self.start.setEnabled(True)
            self.progress_bar.setFormat('Ready (%p%)')
        else:
            self.start.setEnabled(False)
            self.progress_bar.setFormat('Waiting (%p%)')

    def open_chooser(self):
        dialog = QFileDialog.getExistingDirectory(self, 'Open Directory', '/home')
        if dialog:
            self.read_text.setText(dialog)
            self.can_start_sort()

    def open_dest_chooser(self):
        dialog = QFileDialog.getExistingDirectory(self, 'Open Directory', '/home')
        if dialog:
            self.sorted_text.setText(dialog)
            self.can_start_sort()

    def update_progress(self, val):
        self.progress_bar.setValue(val[0])

    def start_sorter(self):
        self.read_text.setEnabled(False)
        self.sorted_text.setEnabled(False)
        self.start.setEnabled(False)
        self.choose_dir.setEnabled(False)
        self.choose_dest_dir.setEnabled(False)
        self.years.setEnabled(False)
        self.months.setEnabled(False)
        self.files.clear()
        self.find_photos()
        self.thread_pool.start(self.thread_worker)
        QMessageBox.information(self, 'Date Sorter', 'Sort completed successfully.')

    def sort_photos(self, update):
        for f in range(0, len(self.files)):
            file = self.files[f]
            with Image.open(file) as img:
                if file.lower().endswith('.jpeg'):
                    exif = {ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS}
                elif file.lower().endswith('.png'):
                    exif = img.text
                else:
                    exif = img._getexif()
            if exif is not None and 36867 in exif and not exif[36867][0] == '{':
                date = datetime.strptime(exif[36867], '%Y:%m:%d %H:%M:%S')
                self.find_dir(file, date)
            else:
                self.find_dir(file, None)
            update.emit((f,))

    def find_dir(self, file, date):
        if date is None:
            check_exists(self.read_text.text() + '/Not_Sortable/', file)
        else:
            check_exists(os.path.join(self.read_text.text(), str(date.year),
                                      (convert_to_month(date.month)
                                       if self.months.isChecked() or self.days.isChecked() else ''),
                                      (str(date.day) if self.days.isChecked() else '')), file)

    def update_after_completion(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('Waiting (%p%)')
        self.read_text.setEnabled(True)
        self.sorted_text.setEnabled(True)
        self.start.setEnabled(True)
        self.choose_dir.setEnabled(True)
        self.choose_dest_dir.setEnabled(True)
        self.years.setEnabled(True)
        self.months.setEnabled(True)
        self.files.clear()

    def find_photos(self):
        self.progress_bar.setFormat('Sorting (%p%)')
        for filename in Path(self.read_text.text()).rglob('**/*.*'):
            if filename.as_posix().lower().endswith(('.png', '.jpg', '.jpeg')):
                self.files.append(filename.as_posix())
        self.progress_bar.setMaximum(len(self.files))
