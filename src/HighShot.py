# --------------------------------- #
# --- github.com/Vauth/highshot --- #
# --------------------------------- #

import os
import sys
import uuid
import ctypes
from pathlib import Path
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath, QIcon, QGuiApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QSlider, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox

class Config(object):
    VERSION_NUMBER = 'v1.0'
    DRAFT = 'false'
    PRE_RELEASE = 'false'
    OS = 'Windows-x64'
    COPYRIGHT = 2025
    CREDIT = 'github.com/vauth'


class HighShot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.darkener(self.winId().__int__())
        self.initUI()
        self.selection_start = QPoint()
        self.selection_end = QPoint()
        self.screenshot = None

    def initUI(self):
        self.setWindowTitle("HighShot")
        self.setFixedSize(480, 600)

        icon = QIcon(self.get_path('media/icon.png'))
        self.setWindowIcon(icon)

        font = QFont()
        font.setFamily("Segoe UI")
        self.setFont(font)

        self.preview_label = QLabel("Capture Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background: #1E1E1E;border: 2px dashed #404040;border-radius: 12px;padding: 8px;")
        self.preview_label.setMinimumHeight(280)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(100)

        self.border_radius_slider = QSlider(Qt.Horizontal)
        self.border_radius_slider.setRange(0, 100)
        self.border_radius_slider.setValue(0)

        self.btn_full = QPushButton("Full Screen")
        self.btn_area = QPushButton("Area Select")
        self.btn_save = QPushButton("Save Now")
        self.btn_copy = QPushButton("Copy to Clipboard")

        self.setStyleSheet((open(self.get_path("asset/style.css"), "r")).read())

        controls = QHBoxLayout()
        controls.addWidget(self.btn_full)
        controls.addWidget(self.btn_area)

        save_controls = QHBoxLayout()
        save_controls.addWidget(self.btn_save)
        save_controls.addWidget(self.btn_copy)

        main_layout = QVBoxLayout()
        main_layout.addLayout(controls)
        main_layout.addSpacing(15)
        main_layout.addWidget(QLabel("Image Quality:"))
        main_layout.addWidget(self.quality_slider)
        main_layout.addSpacing(15)
        main_layout.addWidget(QLabel("Corner Radius:"))
        main_layout.addWidget(self.border_radius_slider)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.preview_label)
        main_layout.addSpacing(15)
        main_layout.addLayout(save_controls)
        main_layout.setContentsMargins(24, 24, 24, 24)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.btn_full.clicked.connect(self.capture_full)
        self.btn_area.clicked.connect(self.start_area_selection)
        self.btn_save.clicked.connect(self.save_screenshot)
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.border_radius_slider.valueChanged.connect(self.update_preview)

    def darkener(self, hwnd):
        if sys.platform != 'win32': return

        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_CAPTION_COLOR = 35
            if hasattr(ctypes, 'windll'):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int(1)))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(0x000000)), ctypes.sizeof(ctypes.c_int(1)))
        except Exception as e:
            print(f"Dark title bar not supported: {e}")

    def dark_message(self, title, text, icon=QMessageBox.Information):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        self.darkener(msg.winId().__int__())
        return msg.exec_()

    def get_path(self, paths):
        if hasattr(sys, '_MEIPASS'):
            return str(os.path.join(sys._MEIPASS, paths)).replace('\\', '/')
        return str(os.path.join(os.path.abspath("."), paths)).replace('\\', '/')

    def capture_full(self):
        self.hide()
        QApplication.processEvents()
        self.screenshot = QTimer.singleShot(200, self.complete_full_capture)

    def complete_full_capture(self):
        try: self.screenshot = QApplication.primaryScreen().grabWindow(0)
        finally: self.show(); self.update_preview()

    def start_area_selection(self):
        self.hide()
        self.overlay = QWidget()
        self.overlay.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setGeometry(QApplication.primaryScreen().geometry())
        self.overlay.show()
        self.overlay.setCursor(Qt.CrossCursor)
        self.overlay.mousePressEvent = self.area_mouse_press
        self.overlay.mouseMoveEvent = self.area_mouse_move
        self.overlay.mouseReleaseEvent = self.area_mouse_release
        self.overlay.paintEvent = self.area_paint_event

    def area_mouse_press(self, event):
        if event.button() == Qt.RightButton: self.cancel_selection(); return
        self.selection_start = event.pos()
        self.selection_end = event.pos()
        self.overlay.update()

    def cancel_selection(self):
        self.overlay.hide()
        self.overlay.close()
        self.show()

    def area_mouse_move(self, event):
        self.selection_end = event.pos()
        self.overlay.update()

    def area_mouse_release(self, event):
        self.overlay.hide()
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        rect = QRect(self.selection_start, self.selection_end).normalized()
        self.screenshot = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        self.overlay.close()
        self.show()
        self.update_preview()

    def area_paint_event(self, event):
        painter = QPainter(self.overlay)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(QRect(self.selection_start, self.selection_end), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawRect(QRect(self.selection_start, self.selection_end))
        painter.fillRect(self.overlay.rect(), QColor(0, 0, 0, 120))

    def apply_rounded_corners(self, pixmap):
        radius_percent = self.border_radius_slider.value()
        if radius_percent == 0 or pixmap.isNull(): return pixmap
        img_size = pixmap.size()
        min_side = min(img_size.width(), img_size.height())
        radius = int(min_side * (radius_percent / 100) * 0.5)
        rounded = QPixmap(img_size)
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(0, 0, img_size.width(), img_size.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return rounded

    def update_preview(self):
        if self.screenshot:
            processed = self.apply_rounded_corners(self.screenshot)
            preview = processed.scaled(self.preview_label.width() - 20, self.preview_label.height() - 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(preview)

    def save_screenshot(self):
        if not self.screenshot: return self.dark_message("Error", "No screenshot captured!", QMessageBox.Critical)
        filename = f"{uuid.uuid4()}.png"
        filepath = Path.cwd() / filename

        try:
            processed = self.apply_rounded_corners(self.screenshot)
            quality = self.quality_slider.value()
            processed.save(str(filepath), "PNG", quality)
            self.dark_message("Information", f"Saved as: {filename}", QMessageBox.Information)
        except Exception as e:
            self.dark_message("Error", f"Failed to save screenshot:\n{str(e)}", QMessageBox.Critical)

    def copy_to_clipboard(self):
        if not self.screenshot: return self.dark_message("Error", "No screenshot captured!", QMessageBox.Critical)

        try:
            processed = self.apply_rounded_corners(self.screenshot)
            clipboard = QGuiApplication.clipboard()
            clipboard.setPixmap(processed)
            self.dark_message("Information", "Screenshot copied to clipboard!", QMessageBox.Information)
        except Exception as e:
            self.dark_message("Error", f"Failed to copy to clipboard:\n{str(e)}", QMessageBox.Critical)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HighShot()
    window.show()
    sys.exit(app.exec_())
