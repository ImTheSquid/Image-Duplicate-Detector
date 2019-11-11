import os

import appdirs
import pickle

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QListWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, \
    QFileDialog, QScrollArea, QFrame

from os import listdir
from os.path import join, isfile, isdir

from albums.album_data import AlbumCreator, AlbumData
from albums.layouts import FlowLayout, CaptionedImage, MouseFlowWidget


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
            with open(join(album_dir, album), 'rb') as f:
                loaded_albums.append(pickle.load(f))
        return loaded_albums


class Albums(QWidget):

    def __init__(self):
        super().__init__()

        self.import_flow = FlowLayout(self, 5, 5)
        self.sort_container = QVBoxLayout()
        # Albums
        self.loaded_albums = []
        self.selected_album = None
        # Mirror array for indexing files/folders selected using import_flow without casting issues
        self.loaded_images = []

        # GUI
        self.album_list = QListWidget()
        self.remove_album_button = QPushButton('Remove Album')
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.init_gui())

        file = QGroupBox('File')
        file_controls = QHBoxLayout()
        file.setLayout(file_controls)
        save = QPushButton('Save')
        save.clicked.connect(self.save_albums)
        file_controls.addWidget(save)
        rescan = QPushButton('Rescan for Albums')
        rescan.clicked.connect(self.rescan_albums)
        file_controls.addWidget(rescan)
        import_album = QPushButton('Import')
        import_album.clicked.connect(self.import_fat)
        file_controls.addWidget(import_album)
        export_album = QPushButton('Export')
        export_album.clicked.connect(self.export_fat)
        file_controls.addWidget(export_album)
        main_layout.addWidget(file)

        self.setLayout(main_layout)
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
        list_layout.addWidget(self.remove_album_button)
        self.remove_album_button.setEnabled(False)
        album_group.setLayout(list_layout)

        self.sort_container.addLayout(self.update_album_layout())

        import_layout = QVBoxLayout()
        path_finder = QHBoxLayout()
        self.go_up = QPushButton('↑')
        self.go_up.clicked.connect(self.go_up_dir)
        self.go_up.setMaximumWidth(25)
        path_finder.addWidget(self.go_up)
        self.path = QLineEdit()
        self.path.setText(str(Path.home()))
        self.update_path()
        self.path.textChanged.connect(self.update_path)
        path_finder.addWidget(self.path)
        dialog = QPushButton('Choose...')
        dialog.clicked.connect(self.choose_path)
        path_finder.addWidget(dialog)
        import_layout.addLayout(path_finder)

        # Contains the whole thing
        scroll_container = QVBoxLayout()
        # Contains FlowLayout
        scroll_widget = MouseFlowWidget(self.import_flow)
        scroll_widget.mouse_down.connect(self.import_flow_mouse_down)
        # Actual scroll area and configuration
        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        # Add scroll widget to parent container
        scroll_container.addWidget(scroll_area)

        import_layout.addLayout(scroll_container)
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
            flow = FlowLayout(self, 5, 5)
            for entry in self.selected_album.get_paths():
                img = CaptionedImage(entry, entry.split('/')[-1], 100, 100, True)
                flow.addWidget(img)
            return flow

    def update_list(self):
        self.album_list.clear()
        self.remove_album_button.setEnabled(False)
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
        self.remove_album_button.setEnabled(True)
        self.clear_layout(self.sort_container)
        self.sort_container.addLayout(self.update_album_layout())

    def save_albums(self):
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')
        for album in self.loaded_albums:
            pickle.dump(album, open(join(album_dir, album.get_title()+'.jalbum'), 'wb'), 4)

    def rescan_albums(self):
        self.save_albums()
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.update_list()

    def import_fat(self):
        pass

    def export_fat(self):
        pass

    def remove_album(self):
        self.loaded_albums.remove(self.selected_album)
        self.remove_album_button.setEnabled(False)
        self.update_list()
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')
        # Searches for pickled album data files
        album_files = [f for f in listdir(album_dir) if isfile(join(album_dir, f))
                       and join(album_dir, f).lower().endswith('.jalbum')]
        if self.selected_album.get_title() + '.jalbum' in album_files:
            os.remove(join(album_dir, self.selected_album.get_title() + '.jalbum'))

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def fill_import(self, directory: str, layout: FlowLayout):
        self.clear_layout(layout)
        files = listdir(directory)
        dirs = []
        photos = []
        other_files = []
        for file in files:
            f = join(directory, file)
            if isdir(f):
                caption = CaptionedImage('albums/assets/folder.png', str(file), 150, 150)
                dirs.append(caption)
            elif isfile(f) and f.lower().endswith(('.png', '.jpg', '.jpeg')):
                caption = CaptionedImage(str(f), str(file), 150, 150)
                photos.append(caption)
            else:
                caption = CaptionedImage('albums/assets/unknownFile.png', str(file), 150, 150)
                other_files.append(caption)
        for direct in dirs:
            layout.addWidget(direct)
            self.loaded_images.append(direct)
        for photo in photos:
            layout.addWidget(photo)
            self.loaded_images.append(photo)
        for other in other_files:
            layout.addWidget(other)
            self.loaded_images.append(other)

    def update_path(self):
        # Turns text red if path is invalid
        if isdir(self.path.text()):
            self.path.setStyleSheet("color: #000000;")
            self.fill_import(self.path.text(), self.import_flow)
        else:
            self.path.setStyleSheet("color: #FF0000")

    # Open file dialog for choosing import path
    def choose_path(self):
        dialog = QFileDialog.getExistingDirectory(self, 'Open Directory', '/home')
        if dialog:
            self.path.setText(dialog)

    def go_up_dir(self):
        self.path.setText(str(Path(self.path.text()).parent))

    # param: e[0]: QMouseEvent, e[1]: index of clicked widget
    def import_flow_mouse_down(self, e: tuple):
        index = e[1]
        widget = self.import_flow.get_widgets()[index].widget()
        print(self.loaded_images[index].get_label_name())
        if widget.styleSheet() is '':
            widget.setStyleSheet('background-color: #93b6ed')
        else:
            widget.setStyleSheet('')
