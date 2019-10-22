import cv2
import numpy as np
from PyQt5.QtCore import QRunnable, pyqtSlot

from signals import WorkerSignals


def compare_files(image1, file2):
    height1, width1, channel1 = image1.shape
    image2 = cv2.imread(file2)
    height2, width2, channel2 = image2.shape

    # Does something that keeps my program responsive, but I don't know what it is
    cv2.waitKey(0)

    if (not height1 == height2) or (not width1 == width2):
        return False

    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    err = np.sum((gray1.astype("float") - gray2.astype("float")) ** 2)
    err /= float(gray1.shape[0] * gray2.shape[1])

    return err == 0


class Worker(QRunnable):
    def __init__(self, files, duplicates, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = files
        self.duplicates = duplicates
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        for firstImg in range(len(self.files)):
            image1 = cv2.imread(self.files[firstImg])
            for secondImg in range(firstImg + 1, len(self.files)):
                print('Comparing image ' + str(firstImg) + ' with image ' + str(secondImg))
                if compare_files(image1, self.files[secondImg]):
                    self.duplicates.append(self.files[secondImg])
                self.signals.progress.emit((firstImg, secondImg))
        self.signals.finished.emit()
