from PyQt5.QtCore import QSize, QRect, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QMouseEvent, QResizeEvent, QImageReader
from PyQt5.QtWidgets import QLayout, QSizePolicy, QWidget, QVBoxLayout, QLabel, QSpacerItem


class FlowLayout(QLayout):
    """A QLayout that arranges its child widgets horizontally and
    vertically.

    If enough horizontal space is available, it looks like an HBoxLayout,
    but if enough space is lacking, it automatically wraps its children into
    multiple rows.
    """
    heightChanged = pyqtSignal(int)

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

        self._item_list = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def addSpacing(self, size):
        self.addItem(QSpacerItem(size, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._item_list:
            minsize = item.minimumSize()
            extent = item.geometry().bottomRight()
            size = size.expandedTo(QSize(minsize.width(), extent.y()))

        margin = self.contentsMargins().left()
        size += QSize(2 * margin, 2 * margin)
        return size

    def _do_layout(self, rect, test_only=False):
        m = self.contentsMargins()
        effective_rect = rect.adjusted(+m.left(), +m.top(), -m.right(), -m.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            wid = item.widget()

            space_x = self.spacing()
            space_y = self.spacing()
            if wid is not None:
                space_x += wid.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
                space_y += wid.style().layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        new_height = y + line_height - rect.y()
        self.heightChanged.emit(new_height)
        return new_height

    def get_widget_pos(self, index):
        return self._item_list[index].geometry()

    def get_widgets(self):
        return self._item_list


# This class tracks where the mouse clicks inside a FlowLayout
class MouseFlowWidget(QWidget):

    mouse_down = pyqtSignal(tuple)
    double_click = pyqtSignal(tuple)
    resize = pyqtSignal(QSize)

    def __init__(self, flow: FlowLayout):
        super().__init__()
        self.setMouseTracking(True)
        self.flow = flow
        self.setLayout(flow)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.mouse_down.emit((a0, self.calc_location(a0)))

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        self.double_click.emit((a0, self.calc_location(a0)))

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.resize.emit(a0.size())

    def calc_location(self, mouse: QMouseEvent):
        item_list = self.flow.get_widgets()
        for item in item_list:
            if item.geometry().contains(mouse.pos()):
                return self.flow.get_widgets().index(item)
        return None


class CaptionedImage(QWidget):
    def __init__(self, file_type: str, image, path: str, text='', width=None, height=None, scaled=True, error=False):
        super().__init__()

        self.file_type = file_type
        self.image = image
        self.path = path
        self.text = text

        # Image
        self.holder = QLabel('hold')
        self.pixmap = QPixmap(QImageReader(image).read())
        self.holder.setAlignment(Qt.AlignCenter)

        # Init sizes
        if width is not None:
            self.holder.setFixedWidth(width)
        if height is not None:
            self.holder.setFixedHeight(height)
        if scaled:
            self.holder.setPixmap(self.pixmap.scaled(self.holder.width(), self.holder.height(), Qt.KeepAspectRatio))
        else:
            self.holder.setPixmap(self.pixmap)

        # Image caption
        caption = QLabel(text)
        if error:
            caption.setStyleSheet('color: #FF0000')
        caption.setFixedWidth(self.holder.width())
        caption.setWordWrap(True)
        caption.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.holder)
        layout.addWidget(caption)
        self.setToolTip(text)

    def get_image(self):
        return self.image

    def get_file_path(self):
        return self.path

    def get_name(self):
        return self.text

    def get_file_type(self):
        return self.file_type

    def setFixedWidth(self, w: int) -> None:
        self.holder.setPixmap(self.pixmap.scaledToWidth(w))
