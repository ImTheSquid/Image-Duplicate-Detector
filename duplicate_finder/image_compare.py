from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImageReader
from PyQt5.QtWidgets import QLabel, QDialog, QHBoxLayout, QVBoxLayout


class ImageCompare(QDialog):

    def __init__(self, original_path, duplicate_path, parent):
        super(ImageCompare, self).__init__(parent)
        layout = QHBoxLayout()
        img1 = QVBoxLayout()
        img2 = QVBoxLayout()
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setWindowTitle('Image Compare')

        original_label = QLabel('Original Image')
        original_label.setAlignment(Qt.AlignCenter)
        original = QLabel('Original Image')
        original.setAlignment(Qt.AlignCenter)
        pixel1 = QPixmap(QImageReader(original_path).read())
        original.setPixmap(pixel1.scaled(500, 1000, Qt.KeepAspectRatio))
        img1.addWidget(original_label)
        img1.addWidget(original)

        duplicate_label = QLabel('Duplicate Image')
        duplicate_label.setAlignment(Qt.AlignCenter)
        duplicate = QLabel('Duplicate Image')
        duplicate.setAlignment(Qt.AlignCenter)
        pixel2 = QPixmap(QImageReader(duplicate_path).read())
        duplicate.setPixmap(pixel2.scaled(500, 1000, Qt.KeepAspectRatio))
        img2.addWidget(duplicate_label)
        img2.addWidget(duplicate)

        layout.addLayout(img1)
        layout.addLayout(img2)

        self.setLayout(layout)
        self.show()


