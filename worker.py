import cv2
import numpy as np
from PyQt5.QtCore import QRunnable, pyqtSlot

from signals import WorkerSignals


class Worker(QRunnable):
    def __init__(self, function, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = function
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        self.function(self.signals.progress)
        self.signals.finished.emit()
