import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QListWidget,
    QListWidgetItem, QLabel, QProgressBar, QFrame, QSizePolicy,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon, QCursor
import requests
from io import BytesIO
from searcher import SearchWorker
from downloader import DownloadManager

DARK_BG = "#0F0F0F"
CARD_BG = "#1A1A1A"
ACCENT = "#FF0000"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#AAAAAA"
BORDER = "#2A2A2A"
HOVER = "#252525"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', 'Tajawal', Arial;
}}
QLineEdit {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT};
}}
QPushButton {{
    background-color: {ACCENT};
    color: {TEXT_PRIMARY};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
}}
QPushButton:hover {{
    background-color: #CC0000;
}}
QPushButton:pressed {{
    background-color: #990000;
}}
QPushButton#btn_folder {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    font-size: 18px;
    padding: 8px 14px;
    border-radius: 8px;
}}
QPushButton#btn_folder:hover {{
    background-color: {HOVER};
    border-color: {ACCENT};
}}
QPushButton#btn_download_item {{
    background-color: #1A1A2E;
    border: 1px solid #FF0000;
    color: {ACCENT};
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton#btn_download_item:hover {{
    background-color: {ACCENT};
    color: white;
}}
QPushButton#btn_download_item:disabled {{
    background-color: #1A1A1A;
    border-color: #444;
    color: #666;
}}
QComboBox {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 160px;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT_SECONDARY};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {DARK_BG};
    border: none;
}}
QScrollBar:vertical {{
    background: {CARD_BG};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #555;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QProgressBar {{
    background-color: {CARD_BG};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}
QLabel {{
    color: {TEXT_PRIMARY};
}}
QLabel#lbl_secondary {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}
QFrame#card {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame#card:hover {{
    border-color: #444;
}}
QFrame#separator {{
    background-color: {BORDER};
    max-height: 1px;
}}
"""


class ResultCard(QFrame):
    download_clicked = pyqtSignal(dict)

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.info = info
        self.setObjectName("card")
        self.setFixedHeight(90)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        self.btn_dl = QPushButton("↓ تنزيل")
        self.btn_dl.setObjectName("btn_download_item")
        self.btn_dl.setFixedSize(90, 36)
        self.btn_dl.clicked.connect(lambda: self.download_clicked.emit(self.info))
        layout.addWidget(self.btn_dl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        title = info.get("title", "بدون عنوان")
        if len(title) > 65:
            title = title[:65] + "..."
        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_title.setWordWrap(False)
        info_layout.addWidget(lbl_title)

        duration_str = self._format_duration(info.get("duration", 0))
        uploader = info.get("uploader", "")
        meta = f"⏱ {duration_str}  •  {uploader}" if uploader else f"⏱ {duration_str}"
        lbl_meta = QLabel(meta)
        lbl_meta.setObjectName("lbl_secondary")
        lbl_meta.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(lbl_meta)

        layout.addLayout(info_layout)
        layout.addStretch()

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 70)
        self.thumbnail_label.setStyleSheet(
            f"background-color: #111; border-radius: 6px;"
        )
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setText("🎬")
        layout.addWidget(self.thumbnail_label)

        self._load_thumbnail(info.get("thumbnail", ""))

    def _format_duration(self, seconds):
        if not seconds:
            return "--:--"
        h = int(seconds) // 3600
        m = (int(seconds) % 3600) // 60
        s = int(seconds) % 60
        if h:
            return f"{h}:{m:02}:{s:02}"
        return f"{m}:{s:02}"

    def _load_thumbnail(self, url):
        if not url:
            return
        self._thumb_thread = ThumbnailLoader(url)
        self._thumb_thread.loaded.connect(self._set_thumbnail)
        self._thumb_thread.start()

    def _set_thumbnail(self, pixmap):
        self.thumbnail_label.setText("")
        self.thumbnail_label.setPixmap(
            pixmap.scaled(120, 70, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                          Qt.TransformationMode.SmoothTransformation)
        )

    def mark_downloaded(self):
        self.btn_dl.setText("✓ تم")
        self.btn_dl.setEnabled(False)
        self.btn_dl.setStyleSheet("background-color: #1a3a1a; color: #4CAF50; border: 1px solid #4CAF50;")

    def mark_downloading(self):
        self.btn_dl.setText("⏳ ...")
        self.btn_dl.setEnabled(False)


class ThumbnailLoader(QThread):
    loaded = pyqtSignal(QPixmap)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            pixmap = QPixmap()
            pixmap.loadFromData(BytesIO(response.content).read())
            self.loaded.emit(pixmap)
        except Exception:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KSO SnapTube Turbo V2")
        self.setMinimumSize(820, 680)
        self.resize(900, 740)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads", "KSO_SnapTube")
        os.makedirs(self.download_path, exist_ok=True)

        self.result_cards = []
        self.total_dl = 0
        self.done_dl = 0

        self.download_manager = DownloadManager()
        self.download_manager.progress_signal.connect(self._on_progress)
        self.download_manager.done_signal.connect(self._on_done)
        self.download_manager.speed_signal.connect(self._on_speed)
        self.download_manager.error_signal.connect(self._on_error)
        self.download_manager.start()

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)

        header = QLabel("KSO SnapTube Turbo V2 🚀")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(f"color: {ACCENT}; margin-bottom: 4px;")
        root.addWidget(header)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_row.setDirection(QHBoxLayout.Direction.RightToLeft)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث أو الصق رابط YouTube / SoundCloud / Playlist...")
        self.search_input.setMinimumHeight(44)
        self.search_input.returnPressed.connect(self._do_search)

        self.btn_search = QPushButton("بحث 🔍")
        self.btn_search.setFixedHeight(44)
        self.btn_search.setMinimumWidth(110)
        self.btn_search.clicked.connect(self._do_search)

        search_row.addWidget(self.btn_search)
        search_row.addWidget(self.search_input)
        root.addLayout(search_row)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(8)
        opts_row.setDirection(QHBoxLayout.Direction.RightToLeft)
        opts_row.setAlignment(Qt.AlignmentFlag.AlignRight)

        lbl_dl = QLabel("عدد التنزيلات:")
        lbl_dl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        opts_row.addWidget(lbl_dl)

        self.combo_workers = QComboBox()
        for i in range(1, 9):
            self.combo_workers.addItem(str(i), i)
        self.combo_workers.setCurrentIndex(2)
        opts_row.addWidget(self.combo_workers)

        self.btn_folder = QPushButton("📂")
        self.btn_folder.setObjectName("btn_folder")
        self.btn_folder.setFixedSize(44, 44)
        self.btn_folder.setToolTip("اختر مجلد التحميل")
        self.btn_folder.clicked.connect(self._pick_folder)
        opts_row.addWidget(self.btn_folder)

        self.lbl_folder = QLabel(self._short_path(self.download_path))
        self.lbl_folder.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        opts_row.addWidget(self.lbl_folder)

        opts_row.addStretch()
        root.addLayout(opts_row)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        self.lbl_results_title = QLabel("النتائج")
        self.lbl_results_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.lbl_results_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        root.addWidget(self.lbl_results_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(6)
        self.results_layout.setContentsMargins(0, 0, 6, 0)
        scroll.setWidget(self.results_container)
        root.addWidget(scroll, 1)

        self.lbl_empty = QLabel("ابحث عن فيديو أو الصق رابط للبدء")
        self.lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empty.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; margin: 40px;")
        self.results_layout.addWidget(self.lbl_empty)

        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_frame.setFixedHeight(64)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 6, 12, 6)
        status_layout.setSpacing(4)

        self.lbl_status = QLabel("جاهز")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        status_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        status_layout.addWidget(self.progress_bar)

        root.addWidget(status_frame)

        self.search_worker = None

    def _short_path(self, path):
        if len(path) > 40:
            return "..." + path[-37:]
        return path

    def _pick_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "اختر مجلد التحميل", self.download_path)
        if folder:
            self.download_path = folder
            self.lbl_folder.setText(self._short_path(folder))

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self._clear_results()
        self.lbl_status.setText("🔍 جاري البحث...")
        self.btn_search.setEnabled(False)

        self.search_worker = SearchWorker(query)
        self.search_worker.result_ready.connect(self._on_search_result)
        self.search_worker.error.connect(self._on_search_error)
        self.search_worker.finished.connect(lambda: self.btn_search.setEnabled(True))
        self.search_worker.start()

    def _clear_results(self):
        self.result_cards.clear()
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_search_result(self, results: list):
        if not results:
            self.lbl_results_title.setText("لا توجد نتائج")
            self.lbl_status.setText("لم يتم العثور على نتائج")
            return

        self.lbl_results_title.setText(f"النتائج ({len(results)})")
        self.lbl_status.setText(f"تم العثور على {len(results)} نتيجة")

        for info in results:
            card = ResultCard(info)
            card.download_clicked.connect(self._queue_download)
            self.results_layout.addWidget(card)
            self.result_cards.append(card)

    def _on_search_error(self, msg: str):
        self.lbl_status.setText(f"خطأ: {msg}")
        err = QLabel(f"⚠️ {msg}")
        err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        err.setStyleSheet(f"color: #FF6B6B; font-size: 14px; margin: 30px;")
        self.results_layout.addWidget(err)

    def _queue_download(self, info: dict):
        card = self._find_card(info.get("id", ""))
        if card:
            card.mark_downloading()

        max_workers = self.combo_workers.currentData()
        self.download_manager.set_max_workers(max_workers)
        self.download_manager.add_download(info, self.download_path)

        self.total_dl += 1
        self._update_status_label()

    def _find_card(self, video_id: str):
        for card in self.result_cards:
            if card.info.get("id") == video_id:
                return card
        return None

    def _on_progress(self, video_id: str, percent: float):
        self.progress_bar.setValue(int(percent))

    def _on_done(self, video_id: str):
        self.done_dl += 1
        card = self._find_card(video_id)
        if card:
            card.mark_downloaded()
        self._update_status_label()
        if self.done_dl >= self.total_dl and self.total_dl > 0:
            self.progress_bar.setValue(100)

    def _on_speed(self, speed_str: str):
        self._update_status_label(speed_str)

    def _on_error(self, video_id: str, msg: str):
        card = self._find_card(video_id)
        if card:
            card.btn_dl.setText("✗ فشل")
            card.btn_dl.setStyleSheet("background-color: #3a1a1a; color: #FF6B6B; border: 1px solid #FF6B6B;")
            card.btn_dl.setEnabled(True)
        self.lbl_status.setText(f"⚠️ فشل: {msg[:60]}")

    def _update_status_label(self, speed: str = ""):
        workers = self.combo_workers.currentData()
        if self.total_dl == 0:
            self.lbl_status.setText("جاهز")
            return
        text = f"تحميل {self.done_dl}/{self.total_dl}"
        if speed:
            text += f"  •  سرعة {speed}"
        text += f"  •  متزامن: {workers}"
        self.lbl_status.setText(text)

    def closeEvent(self, event):
        self.download_manager.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT_PRIMARY))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
