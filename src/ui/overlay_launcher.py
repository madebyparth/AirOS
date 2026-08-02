import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple
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
from PySide6.QtGui import QColor, QFont, QCursor, QGuiApplication, QPainter, QPen
from src.core.actions import ActionDispatcher

@dataclass
class LauncherItemData:
    id: str
    label: str
    action_name: str
    subtitle: str
    category: str
    color_hex: str

class ItemCardWidget(QPushButton):
    """
    Raycast / Windows 11 Fluent styled item card widget.
    Features smooth hover state transitions, category pills, and vibrant accent borders.
    """
    def __init__(self, data: LauncherItemData, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(62)
        self.setCursor(Qt.PointingHandCursor)

        self.normal_qss = f"""
            QPushButton {{
                background-color: rgba(30, 30, 40, 200);
                color: #E0E0E0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
                text-align: left;
                padding-left: 18px;
                padding-right: 18px;
            }}
        """
        self.hover_qss = f"""
            QPushButton {{
                background-color: rgba(45, 48, 65, 245);
                color: #FFFFFF;
                border: 2px solid {self.data.color_hex};
                border-radius: 14px;
                text-align: left;
                padding-left: 18px;
                padding-right: 18px;
            }}
        """
        self.setStyleSheet(self.normal_qss)
        self.is_hovered = False

        self._init_content()

    def _init_content(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Category Badge Dot
        dot = QLabel(self)
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {self.data.color_hex}; border-radius: 5px; border: none;")
        layout.addWidget(dot)

        # Label & Subtitle Box
        text_box = QVBoxLayout()
        text_box.setSpacing(2)

        self.label_lbl = QLabel(self.data.label, self)
        self.label_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.label_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        text_box.addWidget(self.label_lbl)

        sub_lbl = QLabel(self.data.subtitle, self)
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setStyleSheet("color: #9090A5; border: none; background: transparent;")
        text_box.addWidget(sub_lbl)

        layout.addLayout(text_box)
        layout.addStretch()

        # Category Pill
        cat_lbl = QLabel(f" [{self.data.category}] ", self)
        cat_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        cat_lbl.setStyleSheet(f"""
            color: {self.data.color_hex};
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 3px 8px;
        """)
        layout.addWidget(cat_lbl)

    def set_hover_state(self, hovered: bool):
        if self.is_hovered != hovered:
            self.is_hovered = hovered
            self.setStyleSheet(self.hover_qss if hovered else self.normal_qss)

class AirOSOverlayWindow(QWidget):
    """
    AirOS Native Raycast/Spotlight Styled Overlay.
    - Hides Windows OS cursor completely while active.
    - Raycast glassmorphism acrylic aesthetics.
    - Gesture target indicator driven by index finger position.
    """
    action_triggered = Signal(str)

    def __init__(self, action_dispatcher: ActionDispatcher):
        super().__init__()
        self.dispatcher = action_dispatcher
        self.items_data: List[LauncherItemData] = [
            LauncherItemData("spotify", "Spotify", "open_spotify", "Play music & podcasts", "APP", "#00E676"),
            LauncherItemData("chrome", "Chrome", "open_chrome", "Browse the web", "APP", "#00B0FF"),
            LauncherItemData("vscode", "VS Code", "open_vscode", "Edit code workspace", "TOOL", "#FF9100"),
            LauncherItemData("screenshot", "Screenshot", "take_screenshot", "Capture desktop screen", "TOOL", "#AA00FF"),
            LauncherItemData("settings", "Settings", "open_settings", "AirOS preferences", "SYSTEM", "#B0BEC5"),
        ]

        self.item_widgets: List[ItemCardWidget] = []
        self.is_visible_target = False
        self.finger_screen_pos: Optional[Tuple[int, int]] = None
        self.override_cursor_set = False

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
        self.setFixedSize(540, 460)

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    def _init_ui(self):
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 540, 460)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(18, 18, 24, 230);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
            }
        """)

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(10)

        # Header Search-Bar Pill Style
        header_box = QHBoxLayout()
        header_box.setSpacing(10)

        search_pill = QWidget(self.container)
        search_pill.setFixedHeight(44)
        search_pill.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
            }
        """)
        sp_layout = QHBoxLayout(search_pill)
        sp_layout.setContentsMargins(14, 0, 14, 0)

        search_lbl = QLabel(" AirOS Launcher", search_pill)
        search_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        search_lbl.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        sp_layout.addWidget(search_lbl)
        sp_layout.addStretch()

        hint_lbl = QLabel("Pinch to Select", search_pill)
        hint_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        hint_lbl.setStyleSheet("color: #00D7FF; border: none; background: transparent;")
        sp_layout.addWidget(hint_lbl)

        header_box.addWidget(search_pill)
        layout.addLayout(header_box)
        layout.addSpacing(4)

        for item_data in self.items_data:
            card = ItemCardWidget(item_data, self.container)
            card.clicked.connect(lambda _, name=item_data.action_name: self.on_item_clicked(name))
            layout.addWidget(card)
            self.item_widgets.append(card)

        layout.addStretch()

    def _init_animations(self):
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_launcher(self):
        if not self.is_visible_target:
            self.is_visible_target = True

            # Hide OS mouse cursor while launcher is active
            if not self.override_cursor_set:
                QGuiApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
                self.override_cursor_set = True

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

            # Restore OS mouse cursor on overlay close
            if self.override_cursor_set:
                QGuiApplication.restoreOverrideCursor()
                self.override_cursor_set = False

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

    def update_finger_hover(self, screen_pos: Optional[Tuple[int, int]]):
        """
        Updates gesture target pointer location and highlights the single card under finger.
        """
        self.finger_screen_pos = screen_pos
        self.update()  # Repaint gesture target pointer indicator

        if not self.is_visible_target or screen_pos is None:
            for card in self.item_widgets:
                card.set_hover_state(False)
            return

        sx, sy = screen_pos
        local_pos = self.mapFromGlobal(QPoint(sx, sy))

        # Exclusive hit-testing: highlight only one hovered card at a time
        hovered_card: Optional[ItemCardWidget] = None
        for card in self.item_widgets:
            if card.geometry().contains(local_pos):
                hovered_card = card
                break

        for card in self.item_widgets:
            card.set_hover_state(card is hovered_card)

    def trigger_selection_at_finger(self, screen_pos: Optional[Tuple[int, int]]) -> bool:
        if not self.is_visible_target:
            return False

        if screen_pos is not None:
            sx, sy = screen_pos
            local_pos = self.mapFromGlobal(QPoint(sx, sy))

            for card in self.item_widgets:
                if card.geometry().contains(local_pos):
                    self.on_item_clicked(card.data.action_name)
                    return True

        self.hide_launcher()
        return False

    def on_item_clicked(self, action_name: str):
        self.dispatcher.execute_action(action_name)
        self.action_triggered.emit(action_name)
        self.hide_launcher()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Render custom glowing gesture pointer target dot over Qt overlay
        if self.is_visible_target and self.finger_screen_pos is not None:
            sx, sy = self.finger_screen_pos
            local_pos = self.mapFromGlobal(QPoint(sx, sy))

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Glowing Cyan Ring
            pen = QPen(QColor(0, 215, 255, 220), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(local_pos, 10, 10)

            # Core White Pointer Dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 240))
            painter.drawEllipse(local_pos, 4, 4)
            painter.end()
