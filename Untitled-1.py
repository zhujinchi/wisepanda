class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        # 上半区 列表区
        self.upper_widget = QWidget(self)
        self.upper_layout = QVBoxLayout(self.upper_widget)
        self.upper_widget.setStyleSheet("background-color: red;")
        self.image_label = QLabel(self.upper_widget)
        self.upper_layout.addWidget(self.image_label)
        self.layout.addWidget(self.upper_widget)

        # 下半区
        self.lower_widget = QWidget(self)
        self.lower_layout = QHBoxLayout(self.lower_widget)
        self.lower_left_widget = QWidget(self.lower_widget)
        self.lower_right_widget = QWidget(self.lower_widget)

        self.lower_left_widget.setStyleSheet("background-color: green;")
        self.lower_right_widget.setStyleSheet("background-color: blue;")
        
        self.lower_layout.addWidget(self.lower_left_widget)
        self.lower_layout.addWidget(self.lower_right_widget)
        self.layout.addWidget(self.lower_widget)

        # 下半区 控制区
        self.button_layout = QVBoxLayout(self.lower_right_widget)

        self.load_button = QPushButton('Load Image', self.lower_right_widget)
        self.load_button.clicked.connect(self.loadImage)
        self.button_layout.addWidget(self.load_button)

        self.lower_left_layout = QVBoxLayout(self.lower_left_widget)
        
        self.lower_left_layout.addStretch()
        
        self.lower_widget.setLayout(self.lower_layout)
        self.lower_left_widget.setLayout(self.lower_left_layout)
        self.lower_right_widget.setLayout(self.button_layout)

        self.setLayout(self.layout)

    def loadImage(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.bmp *.jpeg);;All Files (*)", QFileDialog.FileMode.ExistingFile)
        
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), aspectRatioMode=True))
class ImageMatchWidget(QWidget):
    """ Image match view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 800, 600)
       
        self.left_layout = QVBoxLayout()
        self.image_label1 = QLabel(self)
        self.image_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label1.setMinimumSize(300, 200)
        self.image_label1.setMouseTracking(True)
        self.left_layout.addWidget(self.image_label1)

        self.image_label2 = QLabel(self)
        self.image_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label2.setMinimumSize(300, 200)
        self.image_label2.setMouseTracking(True)
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
        self.zoom_in_button1.clicked.connect(self.zoomInImage1)

        self.zoom_out_button1 = QPushButton("Zoom Out", self)
        self.zoom_layout1.addWidget(self.zoom_out_button1)
        self.zoom_out_button1.clicked.connect(self.zoomOutImage1)

        self.controls1_layout.addLayout(self.zoom_layout1)

        self.opacity_slider1 = QSlider(Qt.Orientation.Horizontal, self)
        self.controls1_layout.addWidget(self.opacity_slider1)
        self.opacity_slider1.setRange(0, 100)
        self.opacity_slider1.setValue(100)
        self.opacity_slider1.valueChanged.connect(self.updateImage1)

        self.right_groupbox1.setLayout(self.controls1_layout)
        self.right_layout.addWidget(self.right_groupbox1)

        self.right_groupbox2 = QGroupBox("Controls for Image 2")
        self.controls2_layout = QVBoxLayout()

        self.load_button2 = QPushButton("Load Image 2", self)
        self.controls2_layout.addWidget(self.load_button2)
        self.load_button2.clicked.connect(self.loadImage2)

        self.zoom_layout2 = QHBoxLayout()
        self.zoom_in_button2 = QPushButton("Zoom In", self)
        self.zoom_layout2.addWidget(self.zoom_in_button2)
        self.zoom_in_button2.clicked.connect(self.zoomInImage2)

        self.zoom_out_button2 = QPushButton("Zoom Out", self)
        self.zoom_layout2.addWidget(self.zoom_out_button2)
        self.zoom_out_button2.clicked.connect(self.zoomOutImage2)

        self.controls2_layout.addLayout(self.zoom_layout2)

        self.opacity_slider2 = QSlider(Qt.Orientation.Horizontal, self)
        self.controls2_layout.addWidget(self.opacity_slider2)
        self.opacity_slider2.setRange(0, 100)
        self.opacity_slider2.setValue(100)
        self.opacity_slider2.valueChanged.connect(self.updateImage2)

        self.right_groupbox2.setLayout(self.controls2_layout)
        self.right_layout.addWidget(self.right_groupbox2)

        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)

    

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
        print(file_name)

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

    def updateImage1(self):
        if self.original_pixmap1:
            self.displayImage(self.original_pixmap1, self.image_label1)

    def updateImage2(self):
        if self.original_pixmap2:
            self.displayImage(self.original_pixmap2, self.image_label2)

    def zoomInImage1(self):
        self.image_scale1 += 0.1
        if self.original_pixmap1:
            self.displayImage(self.original_pixmap1, self.image_label1)

    def zoomOutImage1(self):
        self.image_scale1 -= 0.1
        if self.original_pixmap1:
            self.displayImage(self.original_pixmap1, self.image_label1)

    def zoomInImage2(self):
        self.image_scale2 += 0.1
        if self.original_pixmap2:
            self.displayImage(self.original_pixmap2, self.image_label2)

    def zoomOutImage2(self):
        self.image_scale2 -= 0.1
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