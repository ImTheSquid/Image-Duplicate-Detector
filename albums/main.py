import math
import os

import appdirs
import pickle

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QListWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, \
    QFileDialog, QScrollArea

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


# Tests to see if a certain key is in an array of CaptionedImages
def test_names(arr, key: CaptionedImage):
    label = key.get_name()
    for cap in arr:
        if label == cap.get_name():
            return True
    return False


def get_index_from_name(target_arr, key: CaptionedImage):
    for cap in range(len(target_arr)):
        if target_arr[cap].get_name() == key.get_name():
            return cap


class Albums(QWidget):

    def __init__(self):
        super().__init__()

        self.clear_selected = QPushButton('Clear Selected Items')
        self.import_files = QPushButton('Import 0 Selected Items')
        self.edit_album_button = QPushButton('Edit Album')
        self.path = QLineEdit()
        self.go_up = QPushButton('↑')
        self.import_flow = FlowLayout(self, 5, 5)
        self.scroll_widget = MouseFlowWidget(self.import_flow)
        self.sort_container = QVBoxLayout()
        # Albums
        self.loaded_albums = []
        self.selected_album = None
        # Mirror array for indexing files/folders selected using import_flow without casting issues
        self.loaded_images = []
        # Stores selected files and directories
        self.selected_files = []

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
        rescan.setToolTip('Scans for albums in the data directory ('
                          + appdirs.user_data_dir('PhotoUtilities', 'JackHogan') + ')')
        rescan.clicked.connect(self.rescan_albums)
        file_controls.addWidget(rescan)
        import_album = QPushButton('Import')
        import_album.clicked.connect(self.import_fat)
        file_controls.addWidget(import_album)
        export_album = QPushButton('Export')
        export_album.clicked.connect(self.export_fat)
        file_controls.addWidget(export_album)
        recover_albums = QPushButton('Recover Albums')
        recover_albums.setToolTip('Attempts rebuild of selected album using photos in the import directory')
        file_controls.addWidget(recover_albums)
        main_layout.addWidget(file)

        self.setLayout(main_layout)
        # Check data
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.update_list()

        self.sort_container.addLayout(self.update_album_layout())

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

        self.edit_album_button.setEnabled(False)
        self.edit_album_button.clicked.connect(self.edit_selected_album)
        list_layout.addWidget(self.edit_album_button)

        list_layout.addWidget(self.remove_album_button)
        self.remove_album_button.setEnabled(False)
        album_group.setLayout(list_layout)

        self.sort_container.addLayout(self.update_album_layout())

        import_layout = QVBoxLayout()
        path_finder = QHBoxLayout()
        self.go_up.clicked.connect(self.go_up_dir)
        self.go_up.setMaximumWidth(25)
        path_finder.addWidget(self.go_up)
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
        self.scroll_widget.mouse_down.connect(self.import_flow_mouse_down)
        self.scroll_widget.double_click.connect(self.import_flow_double_click)
        self.scroll_widget.resize.connect(self.import_resize)
        # Actual scroll area and configuration
        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.scroll_widget)
        # Add scroll widget to parent container
        scroll_container.addWidget(scroll_area)

        import_layout.addLayout(scroll_container)

        self.import_files.setEnabled(False)
        self.import_files.clicked.connect(self.import_selected_items)
        import_layout.addWidget(self.import_files)

        self.clear_selected.setEnabled(False)
        self.clear_selected.clicked.connect(self.clear_selected_items)
        import_layout.addWidget(self.clear_selected)

        import_group.setLayout(import_layout)

        return main_layout

    def update_album_layout(self):
        self.clear_layout(self.sort_container)
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
                img = CaptionedImage(entry, entry.split('/')[-1], 100)
                flow.addWidget(img)
            return flow

    def update_list(self):
        self.album_list.clear()
        self.remove_album_button.setEnabled(False)
        self.edit_album_button.setEnabled(False)
        for album in self.loaded_albums:
            self.album_list.addItem(album.get_title())
        self.selected_album = None
        self.update_album_layout()

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
        self.edit_album_button.setEnabled(True)
        self.sort_container.addLayout(self.update_album_layout())
        self.update_import_button()

    def save_albums(self):
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')
        for album in self.loaded_albums:
            pickle.dump(album, open(join(album_dir, album.get_title() + '.jalbum'), 'wb'), 4)

    def rescan_albums(self):
        self.save_albums()
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.update_list()
        self.sort_container.addLayout(self.update_album_layout())

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

    def import_resize(self, new_size):
        size = int(math.ceil(new_size.width() / 100.0)) * 100
        widgets = []
        for wid_item in self.import_flow.get_widgets():
            widgets.append(wid_item.widget())
        for w in widgets:
            w.setFixedWidth(size / 6)

    # Fills the import_flow FlowLayout with the current directory
    def fill_import(self, directory: str, layout: FlowLayout):
        self.clear_layout(layout)
        self.loaded_images.clear()
        files = listdir(directory)
        dirs = []
        photos = []
        other_files = []
        width = self.scroll_widget.width() / 5
        for file in files:
            f = join(directory, file)
            if isdir(f):
                caption = CaptionedImage('FOLDER', 'albums/assets/folder.png', str(file), width)
                dirs.append(caption)
            elif isfile(f) and f.lower().endswith(('.png', '.jpg', '.jpeg')):
                caption = CaptionedImage('PHOTO', str(f), str(file), width)
                photos.append(caption)
            else:
                caption = CaptionedImage('UNKNOWN', 'albums/assets/unknownFile.png', str(file), width)
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

        # Highlight selected items
        for index in range(len(self.loaded_images)):
            widget = layout.get_widgets()[index].widget()
            if test_names(self.selected_files, widget):
                widget.setStyleSheet('background-color: #93b6ed')
            else:
                widget.setStyleSheet('')

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
        try:
            widget = self.import_flow.get_widgets()[index].widget()
        except TypeError:
            return
        if widget.styleSheet() is '':
            if self.loaded_images[index] not in self.selected_files:
                self.selected_files.append(self.loaded_images[index])
            widget.setStyleSheet('background-color: #93b6ed')
        else:
            if get_index_from_name(self.selected_files, self.loaded_images[index]) is not None:
                self.selected_files.pop(get_index_from_name(self.selected_files, self.loaded_images[index]))
            widget.setStyleSheet('')
        self.update_import_button()

    def import_flow_double_click(self, e: tuple):
        index = e[1]
        try:
            widget = self.loaded_images[index]
        except TypeError:
            return
        if widget.get_file_type() is 'FOLDER':
            self.path.setText(join(self.path.text(), widget.get_name()))
            self.update_path()
        if widget in self.selected_files:
            self.selected_files.pop(self.selected_files.index(widget))
        self.update_import_button()

    def update_import_button(self):
        self.import_files.setText('Import ' + str(len(self.selected_files)) + ' Selected '
                                  + ('Item' if len(self.selected_files) == 1 else 'Items'))
        self.clear_selected.setEnabled(len(self.selected_files) > 0)
        self.import_files.setEnabled(len(self.selected_files) > 0 and self.selected_album is not None)

    def clear_selected_items(self):
        self.selected_files.clear()
        self.update_import_button()
        for wid in self.import_flow.get_widgets():
            wid.widget().setStyleSheet('')

    def edit_selected_album(self):
        pass

    def import_selected_items(self):
        for file in self.selected_files:
            if isdir(file.get_path()):
                for filename in Path(file.get_path()).glob('**/*.*'):
                    if filename.as_uri().lower().endswith(('.png', '.jpg', '.jpeg')):
                        width = self.scroll_widget.width() / 5
                        caption = CaptionedImage('PHOTO', str(filename), str(file.get_name()), width)
                        self.selected_album.add_path(caption)
            else:
                if file.get_name().endswith(('.png', '.jpg', '.jpeg')):
                    self.selected_album.add_path(file)
        self.clear_selected_items()
        self.sort_container.addLayout(self.update_album_layout())
