import os, sys, tempfile, subprocess
from pathlib import Path
from urllib.parse import quote
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QAction, QKeySequence, QFont, QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
     QStackedWidget, QPushButton, QLabel, QLineEdit, QPlainTextEdit, QFileDialog,
    QMessageBox, QSplitter, QToolButton, QFrame)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
class WallpaperDesktop(QWidget):
    def __init__(self, wallpaper_path):
        super().__init__()
        self.wallpaper = QPixmap(str(wallpaper_path))
    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.wallpaper.isNull():
            painter.drawPixmap(self.rect(), self.wallpaper)
        else:
            painter.fillRect(self.rect(), QColor("#0a1a27"))
class BrowserPage(QWebEnginePage):
    def createWindow(self, window_type):
        return self
class DumpsterFireOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dumpster fire OS")
        self.resize(1000, 650)
        self.folder, self.code_file = Path.home(), None
        shell, shell_layout = QWidget(), QVBoxLayout()
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell.setLayout(shell_layout)
        self.pages = QStackedWidget()
        shell_layout.addWidget(self.pages, 1)
        self.build_taskbar(shell_layout)
        self.setCentralWidget(shell)
        wallpaper_path = Path(__file__).resolve().parent / "Assets" / "DesktopWallpaper.png"
        self.desktop, self.browser, self.studio = WallpaperDesktop(wallpaper_path), QWidget(), QWidget()
        for page in (self.desktop, self.browser, self.studio):
            self.pages.addWidget(page)
        self.build_desktop()
        self.build_browser()
        self.build_studio()
        self.show_page(self.desktop)
    def build_topbar(self, layout):
        bar = QFrame(objectName="topbar")
        bar.setFixedHeight(38)
        row = QHBoxLayout(bar)
        row.setContentsMargins(10, 3, 10, 3)
        row.setSpacing(6)
        row.addStretch()
        for name, action in (("Desktop", lambda: self.show_page(self.desktop) if hasattr(self, "desktop") else None),
                             ("Duck Duck Go", lambda: self.show_page(self.browser) if hasattr(self, "browser") else None),
                             ("Python Studio", lambda: self.show_page(self.studio) if hasattr(self, "studio") else None)):
            b = QPushButton(name, objectName="topButton")
            b.clicked.connect(action)
            row.addWidget(b)
        layout.addWidget(bar)
    def button(self, layout, text, action):
        b = QPushButton(text)
        b.clicked.connect(action)
        layout.addWidget(b)
        return b
    def topbar(self, layout, title):
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        row.addStretch()
        self.button(row, "Desktop", lambda: self.show_page(self.desktop))
        layout.addLayout(row)
    def show_page(self, page):
        self.pages.setCurrentWidget(page)
    def load_app_icon(self, asset_name, size=28):
        assets_dir = Path(__file__).resolve().parent / "Assets"
        candidates = [assets_dir / asset_name]
        for extension in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".ico"):
            candidates.append(assets_dir / f"{asset_name}{extension}")
        for image_path in candidates:
            if not image_path.is_file():
                continue
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                continue
            pixmap = pixmap.scaled(
                QSize(size, size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            return QIcon(pixmap)
        fallback = QPixmap(size, size)
        fallback.fill(QColor("#242424"))
        painter = QPainter(fallback)
        painter.setPen(QPen(QColor("#3a3a3a"), 2))
        painter.drawRect(1, 1, size - 2, size - 2)
        painter.end()
        return QIcon(fallback)
    def build_taskbar(self, layout):
        bar = QFrame(objectName="taskbar")
        bar.setFixedHeight(48)
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)
        for name, asset_name, action in (
                ("Duck Duck Go", "DuckDuckGo", lambda: self.show_page(self.browser)),
                ("Python Studio", "Python_Studio", lambda: self.show_page(self.studio))):
            button = QToolButton()
            button.setObjectName("taskAppButton")
            button.setIcon(self.load_app_icon(asset_name, 28))
            button.setIconSize(QSize(28, 28))
            button.setFixedSize(38, 38)
            button.setToolTip(name)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(action)
            row.addWidget(button)
        row.addStretch()
        layout.addWidget(bar)
    def build_desktop(self):
        self.desktop.setObjectName("desktop")
        layout = QVBoxLayout(self.desktop)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        shortcuts = QHBoxLayout()
        shortcuts.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        shortcuts.setSpacing(10)
        fallback_icon = QPixmap(36, 36)
        fallback_icon.fill(QColor("#242424"))
        painter = QPainter(fallback_icon)
        painter.setPen(QPen(QColor("#3a3a3a"), 2))
        painter.drawRect(1, 1, 33, 33)
        painter.end()
        assets_dir = Path(__file__).resolve().parent / "Assets"
        def shortcut_icon(asset_name):
            candidates = [assets_dir / asset_name]
            for extension in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".ico"):
                candidates.append(assets_dir / f"{asset_name}{extension}")
            for image_path in candidates:
                if not image_path.is_file():
                    continue
                pixmap = QPixmap(str(image_path))
                if pixmap.isNull():
                    continue
                pixmap = pixmap.scaled(
                    QSize(36, 36),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = max(0, (pixmap.width() - 36) // 2)
                y = max(0, (pixmap.height() - 36) // 2)
                return QIcon(pixmap.copy(x, y, 36, 36))
            return QIcon(fallback_icon)
        for name, asset_name, action in (
                ("Duck Duck Go", "DuckDuckGo", lambda: self.show_page(self.browser)),
                ("Python Studio", "Python_Studio", lambda: self.show_page(self.studio))):
            b = QToolButton()
            b.setText(name)
            b.setIcon(shortcut_icon(asset_name))
            b.setIconSize(QSize(36, 36))
            b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            b.setFixedSize(100, 92)
            b.setObjectName("desktopShortcut")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(action)
            shortcuts.addWidget(b)
        layout.addLayout(shortcuts)
        layout.addStretch()
    def build_browser(self):
        layout = QVBoxLayout(self.browser)
        self.topbar(layout, "Duck Duck Go")
        row = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("Website or search...")
        self.url.returnPressed.connect(self.navigate)
        self.button(row, "Back", lambda: self.view.back())
        self.button(row, "Forward", lambda: self.view.forward())
        self.button(row, "Go", self.navigate)
        row.addWidget(self.url, 1)
        layout.addLayout(row)
        self.view = QWebEngineView()
        self.view.setPage(BrowserPage(self.view))
        self.view.urlChanged.connect(lambda u: self.url.setText(u.toString()))
        layout.addWidget(self.view)
        self.view.setUrl(QUrl("https://lite.duckduckgo.com/lite/"))
    def navigate(self):
        text = self.url.text().strip()
        if not text:
            return
        first = text.split("/")[0]
        if " " in text or ("." not in first and "://" not in text):
            address = "https://lite.duckduckgo.com/lite/?q=" + quote(text)
        else:
            address = text if "://" in text else "https://" + text
        self.show_page(self.browser)
        self.view.setUrl(QUrl(address))
    def build_studio(self):
        layout = QVBoxLayout(self.studio)
        self.topbar(layout, "Python Studio")
        row = QHBoxLayout()
        self.filename = QLabel("Untitled.py")
        row.addWidget(self.filename)
        row.addStretch()
        for label, action in (("New", self.new_code), ("Open", self.choose_code),
                              ("Save", self.save_code), ("Save As", self.save_as),
                              ("Run", self.run_code)):
            self.button(row, label, action)
        layout.addLayout(row)
        split = QSplitter(Qt.Orientation.Vertical)
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlainText('print("Welcome to Dumpster fire OS!")')
        split.addWidget(self.editor)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        split.addWidget(self.output)
        split.setSizes([400, 180])
        layout.addWidget(split)
        self.status = QLabel("Ready")
        layout.addWidget(self.status)
        for key, action in (("F5", self.run_code), ("Ctrl+S", self.save_code)):
            shortcut = QAction(self)
            shortcut.setShortcut(QKeySequence(key))
            shortcut.triggered.connect(action)
            self.addAction(shortcut)
    def new_code(self):
        if self.editor.toPlainText().strip() and QMessageBox.question(
                self, "New File", "Discard current code?") != QMessageBox.StandardButton.Yes:
            return
        self.code_file = None
        self.filename.setText("Untitled.py")
        self.editor.clear()
        self.output.clear()
    def choose_code(self):
        name, _ = QFileDialog.getOpenFileName(self, "Open Python", str(self.folder),
                                               "Python files (*.py);;All files (*)")
        if name:
            self.load_code(Path(name))
    def load_code(self, path):
        try:
            self.editor.setPlainText(path.read_text(encoding="utf-8", errors="replace"))
            self.code_file, self.folder = path, path.parent
            self.filename.setText(path.name)
            self.status.setText(f"Opened {path}")
            self.show_page(self.studio)
        except OSError as e:
            QMessageBox.warning(self, "Python Studio", str(e))
    def save_code(self):
        self.write_code(self.code_file) if self.code_file else self.save_as()
    def save_as(self):
        name, _ = QFileDialog.getSaveFileName(self, "Save Python", str(self.folder / "untitled.py"),
                                               "Python files (*.py);;All files (*)")
        if name:
            path = Path(name)
            self.write_code(path if path.suffix else path.with_suffix(".py"))
    def write_code(self, path):
        try:
            path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.code_file, self.folder = path, path.parent
            self.filename.setText(path.name)
            self.status.setText("Saved")
        except OSError as e:
            QMessageBox.warning(self, "Python Studio", str(e))
    def run_code(self):
        code = self.editor.toPlainText()
        if not code.strip():
            self.output.setPlainText("Nothing to run.")
            return
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as f:
                f.write(code)
                temp = f.name
            result = subprocess.run([sys.executable, temp],
                cwd=str(self.code_file.parent if self.code_file else self.folder),
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            self.output.setPlainText(result.stdout + result.stderr or "Program finished with no output.")
            self.status.setText("Finished" if result.returncode == 0 else f"Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            self.output.setPlainText("Stopped: execution exceeded 15 seconds.")
            self.status.setText("Timed out")
        except Exception as e:
            self.output.setPlainText(str(e))
            self.status.setText("Error")
        finally:
            if temp:
                try:
                    os.remove(temp)
                except OSError:
                    pass
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow, QWidget { background: #242424; color: #eeeeee; }
        QWidget#desktop { background: transparent; color: #f2f2f2; }
        QLabel { color: #eeeeee; }
        QLabel#desktopTitle { color: #ffffff; font-size: 24px; font-weight: 600; }
        QToolButton#desktopShortcut { color: white; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 6px; font-size: 13px; }
        QToolButton#desktopShortcut:hover { background: rgba(36,36,36,190); border: 1px solid #555555; }
        QFrame#topbar { background: #202020; border-bottom: 1px solid #3b3b3b; }
        QPushButton#topButton { background: #292929; color: #eeeeee; border: 1px solid #414141; padding: 4px 9px; border-radius: 3px; }
        QPushButton#topButton:hover { background: #3b3b3b; }
        QFrame#taskbar { background: #1b1b1b; border-top: 1px solid #3b3b3b; }
        QPushButton { background: #303030; color: #f0f0f0; border: 1px solid #484848; padding: 5px 9px; border-radius: 3px; }
        QPushButton:hover { background: #3a3a3a; border-color: #606060; }
        QPushButton:pressed { background: #1d1d1d; }
        QToolButton#taskAppButton { background: #262626; border: 1px solid #414141; border-radius: 4px; padding: 3px; }
        QToolButton#taskAppButton:hover { background: #3b3b3b; border-color: #606060; }
        QToolButton#taskAppButton:pressed { background: #1d1d1d; }
        QLineEdit, QPlainTextEdit { background: #181818; color: #eeeeee; border: 1px solid #484848; selection-background-color: #555555; }
        QSplitter::handle { background: #353535; }
        QScrollBar:vertical, QScrollBar:horizontal { background: #202020; }
        QMenu { background: #292929; color: #eeeeee; border: 1px solid #484848; }
        QMenu::item:selected { background: #414141; }
        QToolTip { background: #303030; color: #ffffff; border: 1px solid #555555; }
    """)
    window = DumpsterFireOS()
    window.show()
    sys.exit(app.exec())
