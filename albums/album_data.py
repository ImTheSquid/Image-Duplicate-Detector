

# Stores paths to album's image files, for use on one system only
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox

from albums.layouts import CaptionedImage


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
    def __init__(self, title: str, description: str = '', images=None):
        if images is None:
            images = []
        self.title = title
        self.images = images
        self.desc = description

    def add_image(self, image):
        self.images.append(image)

    def get_images(self):
        return self.images

    def get_title(self):
        return self.title

    def get_description(self):
        return self.desc


class AlbumCreator(QDialog):
    def __init__(self, album_list, edit: bool = False, current_album: AlbumData = None):
        super().__init__()
        self.setMinimumWidth(300)
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
        self.title.textChanged.connect(self.check_text)
        d_label = QLabel('Description')
        self.description = QLineEdit()

        layout.addWidget(t_label)
        layout.addWidget(self.title)
        layout.addWidget(d_label)
        layout.addWidget(self.description)
        layout.addStretch()
        layout.addWidget(self.button_box)

        if edit:
            self.setWindowTitle('Album Edit Tool')
            self.setWindowIcon(QIcon('albums/assets/editAlbum.png'))
            self.setWhatsThis('This is how you edit a current album.')
            self.title.setText(current_album.get_title())
            self.description.setText(current_album.get_description())
        else:
            self.setWhatsThis('This is how you create a new album.')
            self.setWindowIcon(QIcon('albums/assets/newAlbum.png'))
            self.setWindowTitle('Album Creation Tool')

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
        print('ACTIVE')
        print(titles)
        if self.edit:
            count = 0
            for title in titles:
                if title == self.title.text():
                    count += 1
            return count <= 1
        return not self.title.text() in titles
