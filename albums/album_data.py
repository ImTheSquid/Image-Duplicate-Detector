import cv2

from os import makedirs, listdir
from os.path import join, isdir, basename
from pathlib import Path

from PyQt5.QtCore import Qt, QThreadPool, pyqtSignal
from PyQt5.QtGui import QIcon, QImageReader, QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox, QProgressBar

from worker import Worker


class AlbumData:
    def __init__(self, title: str, description: str = '', paths: str = None):
        if paths is None:
            paths = []
        self.title = title
        self.paths = paths
        self.desc = description

    def add_path(self, path: str):
        self.paths.append(path)

    def remove_path(self, path: str):
        self.paths.pop(self.paths.index(path))

    def get_paths(self):
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
    def __init__(self, album_list, edit: bool = False, current_album: AlbumData = None,
                 prefill_title: str = '', prefill_desc: str = ''):
        super().__init__()
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
            self.setWindowIcon(QIcon(QPixmap(QImageReader('assets/editAlbum.png')).read()))
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

    def __init__(self, album: FatAlbumData, photo_destination: str, dest_album: AlbumData):
        super().__init__()
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
        self.thread_worker.setAutoDelete(False)
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

        files = [f for f in Path(join(self.photo_loc, self.album.get_title())).glob('**/*.*')
                 if basename(f.as_posix()) in listdir(join(self.photo_loc, self.album.get_title()))]

        for photo in files:
            signal.emit(('IMPORTING', files.index(photo), basename(photo.as_posix())))
            self.dest_album.add_path(str(photo))
