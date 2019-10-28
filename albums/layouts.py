from PyQt5.QtWidgets import QLayout, QLayoutItem


class FlowLayout(QLayout):

    item_list = []

    def __init__(self, margin, v_spacing, h_spacing, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.v_space = v_spacing
        self.h_space = h_spacing

    def addItem(self, a0: QLayoutItem):
        self.item_list.append(a0)
