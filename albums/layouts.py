from PyQt5.QtCore import QSize, QRect, Qt, QPoint
from PyQt5.QtWidgets import QLayout, QLayoutItem, QStyle, QSizePolicy


class FlowLayout(QLayout):

    item_list = []

    def __init__(self, margin=0, v_spacing=0, h_spacing=0, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.v_space = v_spacing
        self.h_space = h_spacing

    def __del__(self):
        self.item_list.clear()

    def addItem(self, a0: QLayoutItem):
        self.item_list.append(a0)

    def smart_spacing(self, pixel_metric):
        if not self.parent():
            return -1
        elif self.parent().isWidgetType():
            return self.parentWidget().style().pixelMetric(pixel_metric, None, self.parentWidget())
        else:
            return self.parent().spacing()
        pass

    def horizontal_spacing(self):
        if self.h_space >= 0:
            return self.h_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutHorizontalSpacing)

    def vertical_spacing(self):
        if self.v_space >= 0:
            return self.v_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutVerticalSpacing)

    def minimum_size(self) -> QSize:
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right() + margins.top() + margins.bottom())
        return size

    def sizeHint(self) -> QSize:
        return self.minimum_size()

    def setGeometry(self, a0: QRect):
        self.setGeometry(a0)
        # self.doLayout(a0, false)

    def doLayout(self, rect, test_only):
        left, right, top, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(+left, +top, -right, - bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        for item in self.item_list:
            wid = item.widget()
            space_X = self.horizontal_spacing()
            if space_X == -1:
                space_X = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            space_Y = self.vertical_spacing()
            if space_Y == -1:
                space_Y = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            next_X = x + item.sizeHint().width() + space_X
            if next_X - space_X > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y += line_height + space_Y
                next_X = x + item.sizeHint().width() + space_X
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_X
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom
