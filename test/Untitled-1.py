import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor
from PyQt6.QtCore import Qt

class ImageDragApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Image Dragger")
        self.setGeometry(100, 100, 1400, 800)

        self.left_layout = QVBoxLayout()
        self.image_label1 = QLabel(self)
        self.image_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label1.setMinimumSize(300, 200)
        self.image_label1.setMouseTracking(True)
        # self.image_label1.setStyleSheet("background-color: red;") #设置背景颜色
        self.left_layout.addWidget(self.image_label1)

        self.image_label2 = QLabel(self)
        self.image_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label2.setMinimumSize(300, 200)
        self.image_label2.setMouseTracking(True)
        # self.image_label2.setStyleSheet("background-color: yellow;") #设置背景颜色
        self.left_layout.addWidget(self.image_label2)

        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)

        self.right_layout = QVBoxLayout()

        self.right_groupbox1 = QGroupBox("Controls for Image 1")
        self.controls1_layout = QVBoxLayout()

        self.load_button1 = QPushButton("Load Image 1", self)
        self.controls1_layout.addWidget(self.load_button1)
        self.load_button1.clicked.connect(self.loadImage1)

        self.zoom_layout1 = QHBoxLayout()
        self.zoom_in_button1 = QPushButton("Zoom In", self)
        self.zoom_layout1.addWidget(self.zoom_in_button1)
        self.zoom_in_button1.clicked.connect(lambda: self.zoomImage(self.image_label1, 0.1))

        self.zoom_out_button1 = QPushButton("Zoom Out", self)
        self.zoom_layout1.addWidget(self.zoom_out_button1)
        self.zoom_out_button1.clicked.connect(lambda: self.zoomImage(self.image_label1, -0.1))

        self.controls1_layout.addLayout(self.zoom_layout1)

        self.opacity_slider1 = QSlider(Qt.Orientation.Horizontal, self)
        self.controls1_layout.addWidget(self.opacity_slider1)
        self.opacity_slider1.setRange(0, 100)
        self.opacity_slider1.setValue(100)
        self.opacity_slider1.valueChanged.connect(self.updateImages)

        self.right_groupbox1.setLayout(self.controls1_layout)
        self.right_layout.addWidget(self.right_groupbox1)

        self.right_groupbox2 = QGroupBox("Controls for Image 2")
        self.controls2_layout = QVBoxLayout()

        self.load_button2 = QPushButton("Load Image 2", self)
        self.controls2_layout.addWidget(self.load_button2)
        self.load_button2.clicked.connect(self.loadImage2)

        self.zoom_layout2 = QHBoxLayout()
        self.zoom_in_button2 = QPushButton("放大", self)
        self.zoom_layout2.addWidget(self.zoom_in_button2)
        self.zoom_in_button2.clicked.connect(lambda: self.zoomImage(self.image_label2, 0.1))

        self.zoom_out_button2 = QPushButton("缩小", self)
        self.zoom_layout2.addWidget(self.zoom_out_button2)
        self.zoom_out_button2.clicked.connect(lambda: self.zoomImage(self.image_label2, -0.1))

        self.controls2_layout.addLayout(self.zoom_layout2)

        self.opacity_slider2 = QSlider(Qt.Orientation.Horizontal, self)
        self.controls2_layout.addWidget(self.opacity_slider2)
        self.opacity_slider2.setRange(0, 100)
        self.opacity_slider2.setValue(100)
        self.opacity_slider2.valueChanged.connect(self.updateImages)

        self.right_groupbox2.setLayout(self.controls2_layout)
        self.right_layout.addWidget(self.right_groupbox2)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)

        self.setCentralWidget(self.splitter)

        self.original_pixmap1 = None
        self.original_pixmap2 = None
        self.drag_start_position1 = None
        self.drag_start_position2 = None
        self.image_scale1 = 1.0
        self.image_scale2 = 1.0

    def loadImage1(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image 1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")

        if file_name:
            pixmap = QPixmap(file_name)
            self.original_pixmap1 = pixmap
            self.image_scale1 = 1.0
            self.displayImage(pixmap, self.image_label1)

    def loadImage2(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image 2", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")

        if file_name:
            pixmap = QPixmap(file_name)
            self.original_pixmap2 = pixmap
            self.image_scale2 = 1.0
            self.displayImage(pixmap, self.image_label2)

    def displayImage(self, pixmap, label):
        opacity = self.opacity_slider1.value() if label == self.image_label1 else self.opacity_slider2.value()
        pixmap = pixmap.scaled(label.size() * (self.image_scale1 if label == self.image_label1 else self.image_scale2), Qt.AspectRatioMode.KeepAspectRatio)
        pixmap = self.applyOpacity(pixmap, opacity)
        label.setPixmap(pixmap)

    def applyOpacity(self, pixmap, opacity):
        image = pixmap.toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                color.setAlpha(opacity * color.alpha() // 100)
                image.setPixelColor(x, y, color)
        pixmap = QPixmap.fromImage(image)
        return pixmap

    def updateImages(self):
        if self.original_pixmap1:
            self.displayImage(self.original_pixmap1, self.image_label1)
        if self.original_pixmap2:
            self.displayImage(self.original_pixmap2, self.image_label2)

    def zoomImage(self, label, increment):
        if label == self.image_label1:
            self.image_scale1 += increment
            if self.original_pixmap1:
                self.displayImage(self.original_pixmap1, self.image_label1)
        elif label == self.image_label2:
            self.image_scale2 += increment
            if self.original_pixmap2:
                self.displayImage(self.original_pixmap2, self.image_label2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos() in self.image_label1.geometry():
                self.drag_start_position1 = event.pos()
            elif event.pos() in self.image_label2.geometry():
                self.drag_start_position2 = event.pos()

    def	mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton):
            if self.drag_start_position1:
                delta = event.pos() - self.drag_start_position1
                self.image_label1.move(self.image_label1.pos() + delta)
                self.drag_start_position1 = event.pos()

            if self.drag_start_position2:
                delta = event.pos() - self.drag_start_position2
                self.image_label2.move(self.image_label2.pos() + delta)
                self.drag_start_position2 = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position1 = None
            self.drag_start_position2 = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageDragApp()
    window.show()
    sys.exit(app.exec())
