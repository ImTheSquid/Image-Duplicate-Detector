import os
import appdirs
import pickle

from PyQt5.QtWidgets import QWidget

from os import listdir
from os.path import join, isfile


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
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
