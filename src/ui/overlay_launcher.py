import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide6.QtGui import QColor, QFont, QCursor
from src.core.actions import ActionDispatcher

@dataclass
class LauncherItemData:
    id: str
    label: str
    action_name: str
    subtitle: str
    color_hex: str

class ItemWidget(QPushButton):
    """
    Custom PySide6 widget representing a launcher item card.
    Supports dynamic hover highlighting driven by index finger position or desktop mouse.
    """
    def __init__(self, data: LauncherItemData, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(56)

        self.setText(f"  ●  {self.data.label}   —   {self.data.subtitle}")
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self.setCursor(Qt.PointingHandCursor)

        self.normal_qss = f"""
            QPushButton {{
                background-color: rgba(35, 35, 45, 220);
                color: #DCDCDC;
                border: 1px solid rgba(60, 60, 75, 180);
                border-radius: 12px;
                text-align: left;
                padding-left: 16px;
            }}
        """
        self.hover_qss = f"""
            QPushButton {{
                background-color: rgba(55, 55, 75, 255);
                color: #FFFFFF;
                border: 2px solid {self.data.color_hex};
                border-radius: 12px;
                text-align: left;
                padding-left: 16px;
            }}
        """
        self.setStyleSheet(self.normal_qss)
        self.is_hovered = False

    def set_hover_state(self, hovered: bool):
        if self.is_hovered != hovered:
            self.is_hovered = hovered
            self.setStyleSheet(self.hover_qss if hovered else self.normal_qss)

class AirOSOverlayWindow(QWidget):
    """
    AirOS Native Desktop Overlay Window.
    - Frameless, translucent, always-on-top floating window.
    - Smooth 60 FPS opacity & geometry scale animation.
    - Data-driven action buttons.
    """
    action_triggered = Signal(str)

    def __init__(self, action_dispatcher: ActionDispatcher):
        super().__init__()
        self.dispatcher = action_dispatcher
        self.items_data: List[LauncherItemData] = [
            LauncherItemData("spotify", "Spotify", "open_spotify", "Music & Podcasts", "#FFD700"),
            LauncherItemData("chrome", "Chrome", "open_chrome", "Web Browser", "#00D7FF"),
            LauncherItemData("vscode", "VS Code", "open_vscode", "Code Editor", "#FF7800"),
            LauncherItemData("screenshot", "Screenshot", "take_screenshot", "Capture Desktop Screen", "#32CD32"),
            LauncherItemData("settings", "Settings", "open_settings", "AirOS Preferences", "#C0C0C0"),
        ]

        self.item_widgets: List[ItemWidget] = []
        self.is_visible_target = False

        self._init_window()
        self._init_ui()
        self._init_animations()

    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(500, 420)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.target_center = QPoint(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        self.move(self.target_center)

    def _init_ui(self):
        container = QWidget(self)
        container.setGeometry(0, 0, 500, 420)
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 26, 240);
                border: 2px solid rgba(0, 215, 255, 180);
                border-radius: 20px;
            }
        """)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        header = QLabel("AirOS Central Launcher", container)
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        layout.addWidget(header)

        sub_header = QLabel("Pinch Thumb+Middle to Select | Hold Victory 1s to Close", container)
        sub_header.setFont(QFont("Segoe UI", 9))
        sub_header.setStyleSheet("color: #A0A0B0; border: none; background: transparent;")
        layout.addWidget(sub_header)

        layout.addSpacing(6)

        for item_data in self.items_data:
            btn = ItemWidget(item_data, container)
            btn.clicked.connect(lambda _, name=item_data.action_name: self.on_item_clicked(name))
            layout.addWidget(btn)
            self.item_widgets.append(btn)

        layout.addStretch()

    def _init_animations(self):
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_launcher(self):
        if not self.is_visible_target:
            self.is_visible_target = True
            self.setWindowOpacity(0.0)
            self.show()
            self.raise_()
            self.activateWindow()

            self.opacity_anim.stop()
            self.opacity_anim.setStartValue(0.0)
            self.opacity_anim.setEndValue(1.0)
            self.opacity_anim.start()

    def hide_launcher(self):
        if self.is_visible_target:
            self.is_visible_target = False
            self.opacity_anim.stop()
            self.opacity_anim.setStartValue(self.windowOpacity())
            self.opacity_anim.setEndValue(0.0)
            self.opacity_anim.finished.connect(self._on_hide_finished)
            self.opacity_anim.start()

    def _on_hide_finished(self):
        try:
            self.opacity_anim.finished.disconnect(self._on_hide_finished)
        except Exception:
            pass
        if not self.is_visible_target:
            self.hide()

    def toggle_launcher(self):
        if self.is_visible_target:
            self.hide_launcher()
        else:
            self.show_launcher()

    def update_finger_hover(self, screen_pos: Optional[tuple[int, int]]):
        """
        Highlights launcher item card under the given screen position (X, Y).
        """
        if not self.is_visible_target or screen_pos is None:
            for btn in self.item_widgets:
                btn.set_hover_state(False)
            return

        sx, sy = screen_pos
        local_pos = self.mapFromGlobal(QPoint(sx, sy))

        for btn in self.item_widgets:
            rect = btn.geometry()
            is_inside = rect.contains(local_pos)
            btn.set_hover_state(is_inside)

    def trigger_selection_at_finger(self, screen_pos: Optional[tuple[int, int]]) -> bool:
        """
        Triggers action of launcher item under finger position if valid,
        and closes the launcher overlay. Returns True if an item was executed.
        """
        if not self.is_visible_target:
            return False

        if screen_pos is not None:
            sx, sy = screen_pos
            local_pos = self.mapFromGlobal(QPoint(sx, sy))

            for btn in self.item_widgets:
                if btn.geometry().contains(local_pos):
                    self.on_item_clicked(btn.data.action_name)
                    return True

        # Dismiss launcher if clicked outside
        self.hide_launcher()
        return False

    def on_item_clicked(self, action_name: str):
        self.dispatcher.execute_action(action_name)
        self.action_triggered.emit(action_name)
        self.hide_launcher()
