import os
import appdirs
import pickle

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QListWidget, QVBoxLayout, QLabel, QPushButton

from os import listdir
from os.path import join, isfile

from albums.album_data import AlbumCreator, AlbumData
from albums.layouts import FlowLayout, CaptionedImage


def check_save_data():
    main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
    album_dir = join(main_data, 'albums')
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)
    # Searches for pickled album data files
    album_files = [f for f in listdir(album_dir) if isfile(join(album_dir, f))
                   and join(album_dir, f).lower().endswith('.jalbum')]
    if len(album_files) == 0:
        return None
    else:
        loaded_albums = []
        for album in album_files:
            with open(album, 'r') as f:
                loaded_albums.append(pickle.load(f))
        return loaded_albums


class Albums(QWidget):

    def __init__(self):
        super().__init__()

        self.loaded_albums = []
        self.selected_album = None

        # GUI
        self.album_list = QListWidget()
        self.remove_album = QPushButton('Remove Album')
        self.setLayout(self.init_gui())
        # Check data
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.update_list()

        self.show()

    def init_gui(self):
        main_layout = QHBoxLayout()
        album_group = QGroupBox('Albums')
        album_group.setMaximumWidth(250)
        self.album_list.setMaximumWidth(250)
        main_layout.addWidget(album_group)
        sort_group = QGroupBox('Album Contents')
        self.sort_container = QVBoxLayout()
        sort_group.setLayout(self.sort_container)
        main_layout.addWidget(sort_group)
        import_group = QGroupBox('Other Photos')
        main_layout.addWidget(import_group)

        list_layout = QVBoxLayout()
        list_layout.addWidget(self.album_list)
        self.album_list.clicked.connect(self.get_selected_item)
        add_album = QPushButton('Add Album')
        add_album.clicked.connect(self.add_new_album)
        list_layout.addWidget(add_album)
        list_layout.addWidget(self.remove_album)
        self.remove_album.setEnabled(False)
        album_group.setLayout(list_layout)

        self.sort_container.addLayout(self.update_album_layout())

        import_layout = FlowLayout(5, 5, 5)
        import_group.setLayout(import_layout)

        return main_layout

    def update_album_layout(self):
        layout = QHBoxLayout()
        layout.addStretch()
        if self.selected_album is None:
            label1 = QLabel('No Album Selected')
            label1.setAlignment(Qt.AlignCenter)
            layout.addWidget(label1)
            layout.addStretch()
            return layout
        if len(self.selected_album.get_paths()) == 0:
            label = QLabel('No Photos in Album')
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            layout.addStretch()
            return layout
        else:
            flow = FlowLayout(5, 5, 5)
            for entry in self.selected_album.get_paths():
                img = CaptionedImage(entry, entry.split('/')[-1], 100, 100, True)
                flow.addWidget(img)
            return flow

    def update_list(self):
        self.album_list.clear()
        self.remove_album.setEnabled(False)
        for album in self.loaded_albums:
            self.album_list.addItem(album.get_title())
        if self.selected_album is None and len(self.loaded_albums) > 0:
            self.selected_album = self.loaded_albums[0]

    def add_new_album(self):
        dialog = AlbumCreator()
        if len(dialog.get_title().text()) == 0:
            return
        self.loaded_albums.append(AlbumData(dialog.get_title().text(), dialog.get_description().text()))
        self.update_list()

    def get_selected_item(self):
        list_sel = self.album_list.currentItem().text()
        for album in self.loaded_albums:
            if album.get_title() == list_sel:
                self.selected_album = album
                break
        self.remove_album.setEnabled(True)
        self.sort_container.takeAt(0)
        self.sort_container.addLayout(self.update_album_layout())
