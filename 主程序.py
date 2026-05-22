from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QSpinBox, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QMenu, QFileDialog, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QImage
import sys
from qframelesswindow import AcrylicWindow
from qfluentwidgets import FlowLayout, SwitchButton, PrimaryToolButton, SpinBox
from qframelesswindow.titlebar import StandardTitleBar
from qfluentwidgets import FluentIcon as FIF

import requests
import time
from PIL import Image, ImageQt
import math
import io
import numpy as np

class normalinferthread(QThread):
    infer_image = Signal(str, list)

    def __init__(self, images_path):
        super().__init__()
        self.images_path = images_path

    def run(self):
        total_time, results = self.infer()
        if total_time is not None:
            self.infer_image.emit(total_time, results)

    def infer(self):

        results = []

        # 1. 计时器开始
        start_time = time.time()

        # 依次处理每张图片
        for image_file in self.images_path:
            results.append(self.process_image(image_file))

        # 1. 计时器结束
        end_time = time.time()

        # 计算总耗时
        total_time = end_time - start_time
        return str(total_time), results

    def process_image(self, image_file):
        url = "http://127.0.0.1:8010/detect/"
        with Image.open(image_file) as img:
            # 将图像转换为字节流
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format=img.format)
            img_byte_array.seek(0)

            # 发送POST请求
            files = {"image_file": img_byte_array}
            response = requests.post(url, files=files)
            pil_image = Image.open(io.BytesIO(response.content))

            return pil_image


class splicinginferthread(QThread):
    infer_image = Signal(str, list)

    def __init__(self, images_path):
        super().__init__()
        self.images_path = images_path

    def run(self):
        total_time, results = self.infer()
        if total_time is not None:
            self.infer_image.emit(total_time, results)

    def infer(self):
        # 1. 计时器开始
        start_time = time.time()

        # 从列表中加载图像
        images, filenames = self.load_images_from_list(self.images_path)
        results = self.process_images(images, filenames)

        # 计时器结束
        end_time = time.time()

        # 计算总耗时
        total_time = end_time - start_time
        return total_time, results

    # 定义一个函数，用于计算排列后的行数和列数
    def calculate_grid_size(self, num_images):
        size = int(math.sqrt(num_images))
        if size * size < num_images:
            size += 1
        return size

    # 加载图像文件
    def load_images_from_list(self, filenames):
        images = []
        for filename in filenames:
            try:
                image = Image.open(filename)
                images.append(image)
            except IOError:
                print("加载图片出错：", filename)
        return images

    # 处理图像函数
    def process_images(self, images):
        results = []
        num_images_loaded = len(images)
        grid_size = self.calculate_grid_size(num_images_loaded)
        image_sizes = [image.size for image in images]
        max_width = max(size[0] for size in image_sizes)
        max_height = max(size[1] for size in image_sizes)
        new_size = (max_width * grid_size, max_height * grid_size)
        new_image = Image.new("RGB", new_size)
        image_positions = []
        bbox_info = []  # 新增用于记录bbox信息的列表
        for index, image in enumerate(images):
            row = index // grid_size
            col = index % grid_size
            x_offset = col * max_width
            y_offset = row * max_height
            new_image.paste(image, (x_offset, y_offset))
            image_positions.append((x_offset, y_offset))

            # 记录bbox信息
            bbox_info.append((x_offset, y_offset, x_offset + max_width, y_offset + max_height))

        img_byte_array = io.BytesIO()
        new_image.save(img_byte_array, format="JPEG")
        img_byte_array.seek(0)

        url = "http://127.0.0.1:8010/detect/"
        files = {"image_file": img_byte_array}
        response = requests.post(url, files=files)
        pil_image = Image.open(io.BytesIO(response.content))

        for bbox in enumerate(bbox_info):
            x1, y1, x2, y2 = bbox
            cropped_image = pil_image.crop((x1, y1, x2, y2))
            results.append(cropped_image)

        return results
            

class CustomWidget(QWidget):
    file_path = Signal(str)

    def __init__(self):
        super().__init__()

        self.current_image_path = None

        self.initUI()

    def initUI(self):
        # 设置小部件大小
        self.setGeometry(300, 300, 250, 150)

    def contextMenuEvent(self, event):
        # 创建菜单
        menu = QMenu(self)

        # 添加菜单项
        action1 = menu.addAction("选择图像")

        # 显示菜单
        action = menu.exec_(self.mapToGlobal(event.pos()))

        # 处理菜单项点击事件
        if action == action1:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog  # 这行是可选的，它禁用了一些平台上的原生对话框
            fileName, _ = QFileDialog.getOpenFileName(self, "打开图像", "", "图像文件 (*.png *.jpg)", options=options)
            if fileName:  # 如果有选择文件
                self.current_image_path = fileName  # 更新当前图像路径
                self.file_path.emit(fileName)  # 发射信号通知文件路径已更新

class CustomTitleBar(StandardTitleBar):
    """ Custom title bar """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setTitle("基于拼接式的缺陷检测方法 开发者: 吴鸿杰")
        self.setIcon("Logo.jpg")

class MainWindow(AcrylicWindow):
    def __init__(self):
        super().__init__()
        self.text = "经典模式"
        self.setTitleBar(CustomTitleBar(self))
        self.mainlayout = QHBoxLayout()
        self.mainlayout.setContentsMargins(0, 32, 0, 0)
        self.setLayout(self.mainlayout)

        self.workwidget = QWidget()
        self.worklayout = QVBoxLayout()
        self.workwidget.setLayout(self.worklayout)

        self.barwidget = QWidget()
        self.barlayout = QVBoxLayout()
        self.barwidget.setLayout(self.barlayout)
        self.mainlayout.addWidget(self.workwidget, 8)
        self.mainlayout.addWidget(self.barwidget, 2)

        self.dockswidget = QWidget()
        self.dockslayout = FlowLayout()
        self.dockswidget.setLayout(self.dockslayout)
        self.timinglayout = QHBoxLayout()

        self.worklayout.addWidget(self.dockswidget, 9)
        self.worklayout.addLayout(self.timinglayout, 1)


        self.timinglabel = QLabel("处理时延：")
        self.timinglayout.addWidget(self.timinglabel)

        self.barspace = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.barlayout.addSpacerItem(self.barspace)

        self.switchButton = SwitchButton(parent=self)
        self.switchButton.setText("经典模式")
        self.switchButton.checkedChanged.connect(self.onswitchCheckedChanged)
        self.barlayout.addWidget(self.switchButton)

        self.spin_box = SpinBox()
        self.spin_box.setMinimum(0)
        self.spin_box.setMaximum(9)
        self.spin_box.valueChanged.connect(self.create_dock_widgets)
        self.barlayout.addWidget(self.spin_box)

        self.inferbutton = PrimaryToolButton(FIF.PLAY, self)
        self.inferbutton.clicked.connect(self.requestapi)
        self.inferbutton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.barlayout.addWidget(self.inferbutton)

        self.dock_widgets = []  # 用于跟踪停靠窗口的列表

        self.create_dock_widgets()

    def create_dock_widgets(self):
        num_docks = self.spin_box.value()
        num_docks = min(num_docks, 9)

        while len(self.dock_widgets) > num_docks:
            dock_widget = self.dock_widgets.pop()
            dock_widget.close()

        for i in range(num_docks - len(self.dock_widgets)):
            dock_widget = QDockWidget(f"通道窗口 {len(self.dock_widgets) + 1}")
            dock_widget.setFixedSize(200, 200)

            # 将dock_widget添加到布局中
            self.dockslayout.addWidget(dock_widget)

            # 为停靠窗口创建带有标签的小部件
            dock_content_widget = CustomWidget()
            dock_content_widget.file_path.connect(self.handle_file_dropped)
            label = QLabel(f"通道 {len(self.dock_widgets) + 1}")
            layout = QVBoxLayout()
            layout.addWidget(label)
            dock_content_widget.setLayout(layout)

            dock_widget.setWidget(dock_content_widget)
            self.dock_widgets.append(dock_widget)

    def handle_file_dropped(self, file_path):
        # 假设 file_path 是图像文件的路径
        pixmap = QPixmap(file_path)  # 从 file_path 加载图像
        if not pixmap.isNull():  # 检查 pixmap 是否有效
            # 找到相应的 QLabel
            sender_widget = self.sender()
            if sender_widget:
                layout = sender_widget.layout()
                if layout:
                    label = layout.itemAt(0).widget()  # 假设 QLabel 是布局中的第一个项目
                    if label:
                        # 将 pixmap 设置为标签的 pixmap
                        label.setPixmap(pixmap)

    def onswitchCheckedChanged(self, isChecked: bool):
        self.text = '拼接模式' if isChecked else '经典模式'
        self.switchButton.setText(self.text)
    
    def get_all_image_paths(self):
        image_paths = []
        for dock_widget in self.dock_widgets:
            dock_content_widget = dock_widget.widget()
            if isinstance(dock_content_widget, CustomWidget):
                image_paths.append(dock_content_widget.current_image_path)
        return image_paths

    def requestapi(self):
        image_paths = self.get_all_image_paths()
        if self.text == "经典模式":
            self.infer_thread = normalinferthread(image_paths)
            self.infer_thread.infer_image.connect(self.update_info)
            self.infer_thread.start()
        else:
            self.infer_thread = splicinginferthread(image_paths)
            self.infer_thread.infer_image.connect(self.update_info)
            self.infer_thread.start()

    def update_info(self, timing, images):

        self.timinglabel.setText("处理时延：" + timing)
        for dock_widget in self.dock_widgets:
            # 获取当前停靠窗口中的 CustomWidget
            dock_content_widget = dock_widget.widget()
            if isinstance(dock_content_widget, CustomWidget):
                # 获取当前 CustomWidget 中的 QLabel
                layout = dock_content_widget.layout()
                if layout:
                    label = layout.itemAt(0).widget()  # 假设 QLabel 是布局中的第一个项目
                    if label and images:
                        # 获取处理好的图像
                        pil_image = images.pop(0)
                        # 将 PIL 图像转换为 QImage 对象
                        qpixmap = ImageQt.toqpixmap(pil_image)
                        # 将 pixmap 设置为标签的 pixmap
                        label.setPixmap(qpixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
