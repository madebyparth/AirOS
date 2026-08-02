import sys
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

def create_default_tray_icon() -> QIcon:
    """Generates a sleek procedural AirOS cyan tray icon pixel map."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(20, 20, 28))
    painter.setPen(QColor(0, 215, 255))
    painter.drawRoundedRect(2, 2, 28, 28, 8, 8)

    painter.setPen(QColor(255, 255, 255))
    painter.setBrush(QColor(0, 215, 255))
    painter.drawEllipse(12, 12, 8, 8)
    painter.end()

    return QIcon(pixmap)

class AirOSTrayIcon(QSystemTrayIcon):
    """
    AirOS Windows System Tray Manager.
    Runs silently in notification area with right-click control menu.
    """
    toggle_launcher_requested = Signal()
    toggle_debug_camera_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(create_default_tray_icon(), parent)
        self.setToolTip("AirOS - AI Interaction Layer")
        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1A1A22;
                color: #E0E0E0;
                border: 1px solid #00D7FF;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #00D7FF;
                color: #000000;
            }
        """)

        title_action = menu.addAction("AirOS Background Layer v1.0")
        title_action.setEnabled(False)
        menu.addSeparator()

        launcher_action = menu.addAction("Open AirOS Launcher (Victory 1s)")
        launcher_action.triggered.connect(self.toggle_launcher_requested.emit)

        self.debug_action = menu.addAction("Toggle OpenCV Debug Window")
        self.debug_action.triggered.connect(self.toggle_debug_camera_requested.emit)

        menu.addSeparator()
        quit_action = menu.addAction("Exit AirOS")
        quit_action.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_launcher_requested.emit()
