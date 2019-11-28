import math
import os
import pickle
import webbrowser
from os import listdir
from os.path import join, isfile, isdir, basename
from pathlib import Path

import appdirs
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QListWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, \
    QFileDialog, QScrollArea, QMessageBox

from albums.album_data import AlbumCreator, AlbumData, FatContentImporter, FatContentExporter, AlbumRecovery, \
    NewContentImporter
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


def calculate_flow_size(size):
    return int(math.ceil(size.width() / 100.0)) * 100 if size.width() < 1000 else int(math.ceil(1000 / 100.0)) * 100


class Albums(QWidget):

    def __init__(self):
        super().__init__()

        self.clear_selected = QPushButton('Clear Selected Items')
        self.import_files = QPushButton('Import 0 Selected Items')
        self.edit_album_button = QPushButton('Edit Album')
        self.path = QLineEdit()
        self.go_up = QPushButton('↑')
        self.import_flow = FlowLayout(self, 1, 1)
        self.scroll_widget = MouseFlowWidget(self.import_flow)
        self.sort_container = QVBoxLayout()
        self.album_desc = QLabel('No Album Selected')
        self.sort_container.addWidget(self.album_desc)
        # Albums
        self.loaded_albums = []
        self.selected_album = None
        # Mirror array for indexing files/folders selected using import_flow/flow without casting issues
        self.loaded_images = []
        self.selected_album_mirror = []
        # Stores selected files and directories
        self.selected_files = []
        self.selected_album_files = []

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
        self.export_album = QPushButton('Export')
        self.export_album.setEnabled(False)
        self.export_album.clicked.connect(self.export_fat)
        file_controls.addWidget(self.export_album)
        self.recover_album = QPushButton('Recover Album')
        self.recover_album.setToolTip('Attempts rebuild of selected album using a selected album')
        self.recover_album.clicked.connect(self.recover_current_album)
        self.recover_album.setEnabled(False)
        file_controls.addWidget(self.recover_album)
        main_layout.addWidget(file)

        # Album management layout
        self.container = QVBoxLayout()
        self.flow = FlowLayout(self.container.parent(), 1, 1)

        # Remove all selected items from album
        self.remove_from_album = QPushButton('Remove Selected From Album')
        self.remove_from_album.setEnabled(False)
        self.remove_from_album.clicked.connect(self.remove_selected_album_items)

        # Only can be used when 1 item is selected
        self.open_path = QPushButton('Open Path')
        self.open_path.clicked.connect(self.open_selected_path)
        self.open_path.setEnabled(False)

        # Photo viewer
        album_widget = MouseFlowWidget(self.flow)
        album_widget.mouse_down.connect(self.album_flow_mouse_down)
        album_widget.setLayout(self.flow)
        album_scroll = QScrollArea()
        album_scroll.setWidget(album_widget)
        album_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        album_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        album_scroll.setWidgetResizable(True)
        self.container.addWidget(album_scroll)
        self.container.addWidget(self.open_path)
        self.container.addWidget(self.remove_from_album)

        self.setLayout(main_layout)
        # Check data
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.refresh_list()

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
        self.remove_album_button.clicked.connect(self.remove_album)
        album_group.setLayout(list_layout)

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

    # Sets album viewing area to correct layout and text
    def update_album_layout(self):
        self.clear_layout(self.flow)
        self.selected_album_mirror.clear()
        self.selected_album_files.clear()
        if self.selected_album is not None:
            self.album_desc.setText('Description: ' + self.selected_album.get_description())
            for entry in self.selected_album.get_paths():
                if isfile(entry):
                    img = CaptionedImage('PHOTO', entry, entry, basename(entry), 100)
                else:
                    img = CaptionedImage('PHOTO', 'assets/errorFindingFile.png', 'NULL', basename(entry), 100, None,
                                         True, True)
                self.flow.addWidget(img)
                self.selected_album_mirror.append(img)

        return self.container

    # Updates the list with new albums and makes sure buttons are set correctly
    def refresh_list(self):
        self.album_desc.setText('No Album Selected')
        self.album_list.clear()
        self.remove_album_button.setEnabled(False)
        self.edit_album_button.setEnabled(False)
        for album in self.loaded_albums:
            self.album_list.addItem(album.get_title())
        self.selected_album = None
        self.export_album.setEnabled(False)
        self.recover_album.setEnabled(False)
        self.update_album_layout()

    # Creates a new album, can be configured with a prefilled title and description
    def add_new_album(self, title='', description='', override_dialog=False):
        if not title or title == '' or override_dialog:
            dialog = AlbumCreator(self, self.loaded_albums, False, None, title if title else '', description)
            title = dialog.get_title().text()
            description = dialog.get_description().text()
        if not title or len(title) == 0:
            return
        self.loaded_albums.append(AlbumData(title, description))
        self.refresh_list()
        return title, description

    # Gets the currently selected album from the list of albums
    def get_selected_item(self):
        list_sel = self.album_list.currentItem().text()
        for album in self.loaded_albums:
            if album.get_title() == list_sel:
                self.selected_album = album
                self.export_album.setEnabled(True)
                self.recover_album.setEnabled(True)
                break
        self.remove_album_button.setEnabled(True)
        self.edit_album_button.setEnabled(True)
        self.update_album_layout()
        self.update_import_button()

    # Saves all albums
    def save_albums(self, rescan=False):
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')

        for file_path in listdir(album_dir):
            os.remove(join(album_dir, file_path))

        for album in self.loaded_albums:
            pickle.dump(album, open(join(album_dir, album.get_title() + '.jalbum'), 'wb'), 4)

        if not rescan:
            QMessageBox.information(self, 'Albums', 'All albums saved successfully.')

    # Scans for more albums
    def rescan_albums(self):
        self.save_albums(True)
        save_data = check_save_data()
        if save_data:
            self.loaded_albums = save_data
        self.refresh_list()
        self.update_album_layout()

    def import_fat(self):
        album_loc = QFileDialog.getOpenFileName(self, 'Open Fat Album File', '/home', 'Fat Album Files (*.jfatalbum)',
                                                'Fat Album Files (*.jfatalbum)')
        if not album_loc:
            return

        # Specifies where new photos will be located
        photo_loc = QFileDialog.getExistingDirectory(self, 'Select Extracted Photo Location (will be placed '
                                                           'under file with album name)', '/home')
        if not photo_loc:
            return

        # Load album into memory
        album = pickle.load(open(album_loc[0], 'rb'))

        # Add album to list
        results = self.add_new_album(album.get_title(), album.get_description(), True)
        album.set_title(results[0])
        album.set_description(results[1])
        self.selected_album = [f for f in self.loaded_albums if f.get_title() == album.get_title()][0]
        FatContentImporter(self, album, photo_loc, self.selected_album)

        QMessageBox.information(self, 'Import', 'Import completed successfully.')

    def export_fat(self):
        save_location = QFileDialog.getExistingDirectory(self, 'Choose an Export Directory', '/home')
        if not save_location:
            return

        FatContentExporter(self, save_location, self.selected_album, self.selected_album_mirror)

        QMessageBox.information(self, 'Export', 'Export completed successfully.')

    # Removes an album from the list and its file
    def remove_album(self):
        # Remove file
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')
        # Searches for pickled album data files
        album_files = [f for f in listdir(album_dir) if isfile(join(album_dir, f))
                       and join(album_dir, f).lower().endswith('.jalbum')]
        if self.selected_album.get_title() + '.jalbum' in album_files:
            os.remove(join(album_dir, self.selected_album.get_title() + '.jalbum'))

        # Remove from list
        self.loaded_albums.remove(self.selected_album)
        self.remove_album_button.setEnabled(False)
        self.refresh_list()

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
        size = calculate_flow_size(new_size)
        widgets = []
        for wid_item in self.import_flow.get_widgets():
            widgets.append(wid_item.widget())
        for w in widgets:
            w.setFixedWidth(size / 6)
        widgets.clear()
        for wid_item in self.flow.get_widgets():
            widgets.append(wid_item.widget())
        for w in widgets:
            w.setFixedWidth(size / 6)

    # Fills the import_flow FlowLayout with the current directory
    def fill_import(self, directory: str, layout: FlowLayout):
        self.clear_layout(layout)
        self.loaded_images.clear()
        try:
            files = listdir(directory)
        except PermissionError:
            QMessageBox.critical(self, 'File Error', 'Couldn\'t access directory: Permission Denied')
            return
        dirs = []
        photos = []
        other_files = []
        width = self.scroll_widget.width() / 5
        for file in files:
            f = join(directory, file)
            if isdir(f):
                caption = CaptionedImage('FOLDER', 'assets/folder.png', str(f), str(file), width)
                dirs.append(caption)
            elif isfile(f) and f.lower().endswith(('.png', '.jpg', '.jpeg')):
                caption = CaptionedImage('PHOTO', str(f), str(f), str(file), width)
                photos.append(caption)
            else:
                caption = CaptionedImage('UNKNOWN', 'assets/unknownFile.png', str(f), str(file), width)
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
            self.path.setStyleSheet("color: #000000")
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

    # Tracks clicks for album layout
    def album_flow_mouse_down(self, e: tuple):
        index = e[1]
        try:
            widget = self.flow.get_widgets()[index].widget()
        except TypeError:
            return
        if widget.styleSheet() is '':
            if self.selected_album_mirror[index] not in self.selected_album_files:
                self.selected_album_files.append(self.selected_album_mirror[index])
            widget.setStyleSheet('background-color: #93b6ed')
        else:
            index_name = get_index_from_name(self.selected_album_files, self.selected_album_mirror[index])
            if index_name is not None:
                self.selected_album_files.pop(index_name)
            widget.setStyleSheet('')
        self.update_album_view_buttons()

    def import_flow_double_click(self, e: tuple):
        index = e[1]
        try:
            widget = self.loaded_images[index]
        except TypeError:
            return
        try:
            listdir(join(self.path.text(), widget.get_name()))
        except PermissionError:
            QMessageBox.critical(self, 'File Error', 'Couldn\'t access directory: Permission Denied')
            return
        except NotADirectoryError:
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

    def update_album_view_buttons(self):
        self.remove_from_album.setEnabled(
            len([f for f in self.flow.get_widgets() if not f.widget().styleSheet() is '']) > 0)

        # Only enable when 1 item is selected
        self.open_path.setEnabled(len([f for f in self.flow.get_widgets() if not f.widget().styleSheet() is '']) == 1)

    def clear_selected_items(self):
        self.selected_files.clear()
        self.update_import_button()
        for wid in self.import_flow.get_widgets():
            wid.widget().setStyleSheet('')

    def edit_selected_album(self):
        original_file_name = self.selected_album.get_title()

        # Remove file
        main_data = appdirs.user_data_dir('PhotoUtilities', 'JackHogan')
        album_dir = join(main_data, 'albums')
        # Searches for pickled album data files
        album_files = [f for f in listdir(album_dir) if isfile(join(album_dir, f))
                       and join(album_dir, f).lower().endswith('.jalbum')]
        if self.selected_album.get_title() + '.jalbum' in album_files:
            os.remove(join(album_dir, original_file_name + '.jalbum'))

        edited = AlbumCreator(self, self.loaded_albums, True, self.selected_album)
        self.selected_album.set_title(edited.get_title().text())
        self.selected_album.set_description(edited.get_description().text())
        self.refresh_list()
        self.save_albums(True)

    def import_selected_items(self):
        NewContentImporter(self, self.selected_files, self.selected_album)
        self.clear_selected_items()
        self.update_album_layout()

    def remove_selected_album_items(self):
        for image in self.selected_album_files:
            self.selected_album.remove_path(image.get_image())

        self.selected_album_files.clear()
        self.update_album_view_buttons()
        self.update_album_layout()
        for wid in self.flow.get_widgets():
            wid.widget().setStyleSheet('')
        self.remove_from_album.setEnabled(False)

    def open_selected_path(self):
        if len(self.selected_album_files) > 1:
            return
        # Opens parent directory in system's file explorer
        webbrowser.open('file://' + str(Path(self.selected_album_files[0].get_file_path()).parent))

    def recover_current_album(self):
        search_dir = QFileDialog.getExistingDirectory(self, 'Select Directory to Search', '/home')
        if not search_dir:
            return

        AlbumRecovery(self, self.selected_album, search_dir)
        self.rescan_albums()

        QMessageBox.information(self, 'Album Recovery', 'Recovery completed successfully. '
                                                        'However, not all files may have been found.')
