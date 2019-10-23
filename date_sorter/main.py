import os

from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QThreadPool
from PyQt5.QtWidgets import QWidget, QGroupBox, QVBoxLayout, QProgressBar, QLabel, QHBoxLayout, QLineEdit, QPushButton, \
    QFileDialog, QRadioButton

from worker import Worker


class DateSorter(QWidget):

    progress_signal = pyqtSignal(tuple)

    files = []

    def __init__(self):
        super().__init__()

        # Thread stuff
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.sort_photos)
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
        self.read_text = QLineEdit()
        self.read_text.textEdited.connect(self.can_start_sort)
        read_box.addWidget(self.read_text)
        self.choose_dir = QPushButton('Choose...')
        self.choose_dir.clicked.connect(self.open_chooser)
        read_box.addWidget(self.choose_dir)
        options.addLayout(read_box)

        dest_dir_label = QLabel('Destination Directory')
        options.addWidget(dest_dir_label)

        dest_box = QHBoxLayout()
        self.sorted_text = QLineEdit()
        self.sorted_text.textEdited.connect(self.can_start_sort)
        dest_box.addWidget(self.sorted_text)
        self.choose_dest_dir = QPushButton('Choose...')
        self.choose_dest_dir.clicked.connect(self.open_dest_chooser)
        dest_box.addWidget(self.choose_dest_dir)

        options.addLayout(dest_box)

        radios = QVBoxLayout()
        sort_type_label = QLabel('Sort Type')
        radios.addWidget(sort_type_label)
        self.years = QRadioButton('Years')
        self.years.setChecked(True)
        self.months = QRadioButton('Years and Months')
        radios.addWidget(self.years)
        radios.addWidget(self.months)
        options.addLayout(radios)

        options.addStretch()

        self.start = QPushButton('Start')
        self.start.setEnabled(False)
        self.start.clicked.connect(self.start_sorter)
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
        self.find_photos()
        self.thread_pool.start(self.thread_worker)

    def sort_photos(self, update):
        pass

    def update_after_completion(self):
        pass

    def find_photos(self):
        self.progress_bar.setFormat('Scanning (%p%)')
        for filename in Path(self.read_text.text()).glob('**/*.*'):
            if filename.as_uri().endswith(('.png', '.jpg', '.jpeg')):
                self.files.append(filename.as_posix())

        self.progress_bar.setMaximum(len(self.files))
        self.thread_pool.start(self.thread_worker)
