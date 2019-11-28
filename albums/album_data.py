import pickle
from os import makedirs, listdir
from os.path import join, isdir, basename, isfile
from pathlib import Path

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QThreadPool, pyqtSignal
from PyQt5.QtGui import QIcon, QImageReader, QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox, QProgressBar, QMessageBox

from worker import Worker


class AlbumData:
    def __init__(self, title: str, description: str = '', paths: str = None):
        if paths is None:
            paths = []
        self.title = title
        self.paths = paths
        self.desc = description

        self.hashes = {}

    def add_path(self, path: str):
        self.paths.append(path)
        self.hashes[path] = cv2.cvtColor(cv2.imread(path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2GRAY)

    def get_gray_from_path(self, path: str):
        if path not in self.hashes:
            return None
        return self.hashes[path]

    def remove_path(self, path: str):
        self.paths.pop(self.paths.index(path))
        self.hashes.pop(path)

    def replace_path(self, old_path: str, new_path: str):
        self.paths[self.paths.index(old_path)] = new_path
        self.hashes[new_path] = cv2.cvtColor(cv2.imread(new_path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2GRAY)
        self.hashes.pop(old_path)

    def get_paths(self) -> [str]:
        return self.paths

    def get_title(self):
        return self.title

    def set_title(self, title: str):
        self.title = title

    def get_description(self):
        return self.desc

    def set_description(self, desc: str):
        self.desc = desc


# Stores raw image data to be used for transferring between systems
class FatAlbumData:
    def __init__(self, title: str, description: str = '', images: [] = None):
        if images is None:
            images = []
        self.title = title
        self.images = images
        self.desc = description

    def add_image(self, image):
        self.images.append(image)

    def get_images(self):
        return self.images

    def set_title(self, title: str):
        self.title = title

    def get_title(self):
        return self.title

    def set_description(self, desc: str):
        self.desc = desc

    def get_description(self):
        return self.desc


class FatPhoto:
    def __init__(self, image, name: str):
        self. image = image
        self.name = name

    def get_image(self):
        return self.image

    def get_name(self):
        return self.name


class AlbumCreator(QDialog):
    def __init__(self, parent, album_list, edit: bool = False, current_album: AlbumData = None,
                 prefill_title: str = '', prefill_desc: str = ''):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.album_list = album_list
        self.edit = edit

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.rejected.connect(self.my_reject)
        self.button_box.accepted.connect(self.accept)

        layout = QVBoxLayout()
        self.setLayout(layout)
        t_label = QLabel('Title (Required)')
        self.title = QLineEdit()
        self.title.setText(prefill_title)
        self.title.textChanged.connect(self.check_text)
        d_label = QLabel('Description')
        self.description = QLineEdit()
        self.description.setText(prefill_desc)

        layout.addWidget(t_label)
        layout.addWidget(self.title)
        layout.addWidget(d_label)
        layout.addWidget(self.description)
        layout.addStretch()
        layout.addWidget(self.button_box)

        if edit:
            self.setWindowTitle('Album Edit Tool')
            self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/editAlbum.png').read())))
            self.title.setText(current_album.get_title())
            self.description.setText(current_album.get_description())
        else:
            self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/newAlbum.png').read())))
            self.setWindowTitle('Album Creation Tool')

        if len(prefill_title) > 0:
            self.check_text()

        self.exec()

    def check_text(self):
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(
            len(self.title.text()) > 0 and len(self.description.text()) <= 300 and self.check_originality())

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def my_reject(self):
        self.reject()
        if not self.edit:
            self.title.setText('')

    # Returns true if name is original, false otherwise
    def check_originality(self) -> bool:
        titles = [f.get_title() for f in self.album_list]
        if self.edit:
            count = 0
            for title in titles:
                if title == self.title.text():
                    count += 1
            return count <= 1
        return not self.title.text() in titles


class FatContentImporter(QDialog):
    progress_signal = pyqtSignal(tuple)

    def __init__(self, parent, album: FatAlbumData, photo_destination: str, dest_album: AlbumData):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle('Album Content Importer')
        self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/importAlbumContent.png').read())))

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Importing album files...'))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat('Waiting (%p%)')
        layout.addWidget(self.progress)
        self.current_file = QLabel('Waiting...')
        layout.addWidget(self.current_file)
        layout.addStretch()

        # Init thread
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.run)
        self.thread_worker.signals.progress.connect(self.progress_signal)
        self.thread_worker.signals.finished.connect(self.update_after_completion)

        # Make dirs for album content
        if not isdir(join(photo_destination, album.get_title())):
            makedirs(join(photo_destination, album.get_title()))

        self.album_photos = album.get_images()
        self.progress.setMaximum(len(self.album_photos) - 1)
        self.album = album
        self.photo_loc = photo_destination
        self.dest_album = dest_album

        self.setLayout(layout)
        self.setFixedSize(300, 80)
        self.thread_pool.start(self.thread_worker)
        self.exec()

    def update_progress(self, status: tuple):
        if status[0] is 'SAVING':
            self.progress.setFormat('Extracting (%p%)')
        else:
            self.progress.setFormat('Importing (%p%)')
        self.progress.setValue(status[1] + 1)
        self.current_file.setText(status[2])

    def update_after_completion(self):
        self.hide()

    def run(self, signal):
        for album_photo in self.album_photos:
            cv2.imwrite(join(self.photo_loc, self.album.get_title(), album_photo.get_name()), album_photo.get_image())
            signal.emit(('SAVING', self.album_photos.index(album_photo), album_photo.get_name()))

        files = [f for f in Path(join(self.photo_loc, self.album.get_title())).rglob('**/*.*')
                 if basename(f.as_posix()) in listdir(join(self.photo_loc, self.album.get_title()))]

        for photo in files:
            signal.emit(('IMPORTING', files.index(photo), basename(photo.as_posix())))
            self.dest_album.add_path(str(photo))


class FatContentExporter(QDialog):
    progress_signal = pyqtSignal(tuple)

    def __init__(self, parent, dest_dir: str, selected_album: AlbumData, images: []):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle('Album Content Exporter')
        self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/exportAlbumContent.png').read())))

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Exporting album files...'))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat('Waiting (%p%)')
        layout.addWidget(self.progress)
        self.current_file = QLabel('Waiting...')
        layout.addWidget(self.current_file)
        layout.addStretch()

        # Init thread
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.run)
        self.thread_worker.signals.progress.connect(self.progress_signal)
        self.thread_worker.signals.finished.connect(self.update_after_completion)

        self.images = images
        self.selected_album = selected_album
        self.dest_dir = dest_dir

        self.setLayout(layout)
        self.setFixedSize(300, 80)
        self.thread_pool.start(self.thread_worker)
        self.exec()

    def update_after_completion(self):
        self.hide()

    def update_progress(self, status: tuple):
        if status[0] is 'COLLECTING':
            self.progress.setFormat('Collecting (%p%)')
        else:
            self.progress.setFormat('Saving (%p%)')
        self.progress.setValue(status[1] + 1)
        self.current_file.setText(status[2])

    def run(self, signal):
        self.progress.setMaximum(len(self.images) - 1)
        images = []
        for cap_img in self.images:
            images.append(FatPhoto(cv2.imread(cap_img.get_image(), cv2.IMREAD_UNCHANGED),
                                   basename(cap_img.get_image())))
            signal.emit(('COLLECTING', self.images.index(cap_img), cap_img.get_name()))
        fat_data = FatAlbumData(self.selected_album.get_title(), self.selected_album.get_description(), images)

        signal.emit(('SAVING', -1, fat_data.get_title() + '.jfatalbum'))
        self.progress.setMaximum(0)
        pickle.dump(fat_data, open(join(self.dest_dir, fat_data.get_title() + '.jfatalbum'), 'wb'), 4)


class AlbumRecovery(QDialog):
    progress_signal = pyqtSignal(tuple)

    def __init__(self, parent, album: AlbumData, recovery_dir: str):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle('Album Content Recovery')
        self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/recoverAlbumContent.png').read())))

        self.album = album
        self.recovery_dir = recovery_dir

        # Init thread
        self.progress_signal.connect(self.update_progress)
        self.thread_pool = QThreadPool()
        self.thread_worker = Worker(self.run)
        self.thread_worker.signals.progress.connect(self.progress_signal)
        self.thread_worker.signals.finished.connect(self.update_after_completion)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Recovering album files...'))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat('Waiting (%p%)')
        layout.addWidget(self.progress)
        self.current_file = QLabel('Waiting...')
        layout.addWidget(self.current_file)
        layout.addStretch()

        self.setLayout(layout)
        self.setFixedSize(300, 80)
        self.thread_pool.start(self.thread_worker)
        self.exec()

    def update_after_completion(self):
        self.hide()

    def update_progress(self, status: tuple):
        # Indexing missing files or finding them
        if status[0] is 'INDEX':
            self.progress.setFormat('Indexing (%p%)')
        else:
            self.progress.setFormat('Locating (%p%)')
        self.progress.setValue(status[1] + 1)
        self.current_file.setText(status[2])

    def run(self, signal):
        # Find which photos are missing
        self.progress.setMaximum(0)
        signal.emit(('INDEX', -1, 'Indexing lost photos...'))
        lost_photos = []
        for path in self.album.get_paths():
            signal.emit(('INDEX', self.album.get_paths().index(path), basename(path)))
            if not isfile(path):
                lost_photos.append(path)

        # Recurse through dirs to find possible matches
        files = [f for f in Path(self.recovery_dir).rglob("**/*.*") if f.as_uri().endswith(('.png', '.jpg', '.jpeg'))]
        self.progress.setMaximum(len(files) * len(lost_photos))
        for lost in lost_photos:
            gray = self.album.get_gray_from_path(lost)
            if gray is None:
                QMessageBox.critical(self, 'Error Recovering Photos', 'Incompatible album data.')
                return
            for file in files:
                signal.emit(('LOCATE', lost_photos.index(lost) * len(files) + files.index(file),
                             basename(file.as_posix())))
                gray2 = cv2.cvtColor(cv2.imread(file.as_posix(), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2GRAY)
                if not (gray.shape[0] == gray2.shape[0] and gray.shape[1] == gray2.shape[1]):
                    continue
                err = np.sum((gray.astype("float") - gray2.astype("float")) ** 2)
                err /= float(gray.shape[0] * gray2.shape[1])
                if err == 0:
                    self.album.replace_path(lost, file.as_posix())
                    break
