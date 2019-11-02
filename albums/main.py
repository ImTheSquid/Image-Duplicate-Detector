import os
import appdirs
import pickle

from PyQt5.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QListWidget, QVBoxLayout

from os import listdir
from os.path import join, isfile

from albums.layouts import FlowLayout


def check_save_data():
    main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
    album_dir = join(main_data, 'albums')
    if not os.path.exists(album_dir):
        os.makedirs(album_dir)
    # Searches for pickled album data files
    album_files = [f for f in listdir(album_dir) if isfile(join(album_dir, f))
                   and join(album_dir, f).lower().endswith('.pickle')]
    if len(album_files) == 0:
        return None
    else:
        loaded_albums = []
        for album in album_files:
            with open(album, 'r') as f:
                loaded_albums.append(pickle.load(f))
        return loaded_albums


class Albums(QWidget):

    loaded_albums = []
    selected_album = None

    def __init__(self):
        super().__init__()

        # GUI
        self.album_list = QListWidget()
        self.setLayout(self.init_gui())
        # Check data
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data

        self.show()

    def init_gui(self):
        main_layout = QHBoxLayout()
        album_group = QGroupBox('Albums')
        album_group.setMaximumWidth(250)
        main_layout.addWidget(album_group)
        sort_group = QGroupBox('Album Contents')
        main_layout.addWidget(sort_group)
        import_group = QGroupBox('Other Photos')
        main_layout.addWidget(import_group)

        list_layout = QVBoxLayout()
        list_layout.addWidget(self.album_list)
        album_group.setLayout(list_layout)

        content_layout = FlowLayout(5, 5, 5, self)

        return main_layout
