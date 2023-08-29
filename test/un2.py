import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSlider
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import Qt

class ImageOpacityApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image Opacity")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal, self)
        layout.addWidget(self.opacity_slider)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(255)
        self.opacity_slider.valueChanged.connect(self.updateImageOpacity)

        self.image = QPixmap("/Users/angzeng/Pictures/星空.jpeg")  # Replace with your image path
        self.updateImageOpacity()

    def updateImageOpacity(self):
        opacity = self.opacity_slider.value()
        modified_image = self.applyOpacity(self.image, opacity)
        self.image_label.setPixmap(modified_image)

    def applyOpacity(self, pixmap, opacity):
        image = pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                color.setAlpha(opacity)
                image.setPixelColor(x, y, color)
        modified_pixmap = QPixmap.fromImage(image)
        return modified_pixmap

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageOpacityApp()
    window.show()
    sys.exit(app.exec())