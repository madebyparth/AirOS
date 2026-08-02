from dataclasses import dataclass
from typing import List, Optional, Tuple
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
    QFrame,
)
from PySide6.QtGui import QColor, QFont, QGuiApplication
from src.core.actions import ActionDispatcher

@dataclass
class LauncherItemData:
    id: str
    label: str
    action_name: str
    subtitle: str
    category: str
    color_hex: str

class ItemCardWidget(QFrame):
    """
    Windows 11 / macOS inspired action card.
    The card itself is the selector — no cursor required.
    Hover state is driven externally by finger position.
    """
    def __init__(self, data: LauncherItemData, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedHeight(68)
        self.is_hovered = False

        self._normal_style = f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 16px;
            }}
        """
        self._hover_style = f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.12);
                border: 1.5px solid {data.color_hex};
                border-radius: 16px;
            }}
        """
        self.setStyleSheet(self._normal_style)
        self._build_layout()

    def _build_layout(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 0, 18, 0)
        row.setSpacing(14)

        # Accent dot
        dot = QLabel(self)
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {self.data.color_hex}; border-radius: 4px; border: none;")
        row.addWidget(dot)

        # Text column
        col = QVBoxLayout()
        col.setSpacing(3)

        self._name_lbl = QLabel(self.data.label, self)
        self._name_lbl.setFont(QFont("Segoe UI Variable", 11, QFont.Weight.Medium))
        self._name_lbl.setStyleSheet("color: rgba(255,255,255,0.90); background: transparent; border: none;")
        col.addWidget(self._name_lbl)

        sub = QLabel(self.data.subtitle, self)
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: rgba(255,255,255,0.40); background: transparent; border: none;")
        col.addWidget(sub)

        row.addLayout(col)
        row.addStretch()

        # Category badge
        badge = QLabel(self.data.category, self)
        badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        badge.setStyleSheet(f"""
            color: {self.data.color_hex};
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 6px;
            padding: 2px 8px;
        """)
        row.addWidget(badge)

    def set_hover_state(self, hovered: bool):
        if self.is_hovered == hovered:
            return
        self.is_hovered = hovered
        self.setStyleSheet(self._hover_style if hovered else self._normal_style)
        # Brighten name label when hovered
        self._name_lbl.setStyleSheet(
            "color: rgba(255,255,255,1.0); background: transparent; border: none;"
            if hovered else
            "color: rgba(255,255,255,0.90); background: transparent; border: none;"
        )


class AirOSOverlayWindow(QWidget):
    """
    AirOS floating launcher overlay.
    - Frameless, always-on-top, translucent — pure Qt, no OpenCV dependency.
    - OS cursor hidden while active. No pointer rendered; the highlighted card IS the selector.
    - Opened/closed by gesture signal; item selection by PINCH_MIDDLE signal.
    """
    action_triggered = Signal(str)

    ITEMS: List[LauncherItemData] = [
        LauncherItemData("spotify",     "Spotify",     "open_spotify",    "Music & Podcasts",     "APP",    "#1DB954"),
        LauncherItemData("chrome",      "Chrome",      "open_chrome",     "Browse the web",       "APP",    "#4CAFF0"),
        LauncherItemData("vscode",      "VS Code",     "open_vscode",     "Code editor",          "TOOL",   "#FF9A3C"),
        LauncherItemData("screenshot",  "Screenshot",  "take_screenshot", "Capture desktop",      "TOOL",   "#B06EFF"),
        LauncherItemData("settings",    "Settings",    "open_settings",   "AirOS preferences",    "SYSTEM", "#8E9AAA"),
    ]

    def __init__(self, action_dispatcher: ActionDispatcher):
        super().__init__()
        self.dispatcher = action_dispatcher
        self.item_widgets: List[ItemCardWidget] = []
        self.is_visible_target = False
        self._cursor_override_active = False

        self._setup_window()
        self._build_ui()
        self._setup_animation()

    # ── Window setup ────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(520, 500)
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

    def _build_ui(self):
        # Outer widget carries the glass card styling + drop shadow
        card = QWidget(self)
        card.setGeometry(0, 0, 520, 500)
        card.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 20, 215);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 22px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 12)
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(card)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(8)

        # Header row
        header = QHBoxLayout()

        title = QLabel("AirOS", card)
        title.setFont(QFont("Segoe UI Variable", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: rgba(255,255,255,0.95); background: transparent; border: none;")
        header.addWidget(title)

        header.addStretch()

        hint = QLabel("Pinch thumb+middle to launch", card)
        hint.setFont(QFont("Segoe UI", 9))
        hint.setStyleSheet("color: rgba(255,255,255,0.30); background: transparent; border: none;")
        header.addWidget(hint)

        root.addLayout(header)

        # Divider
        divider = QFrame(card)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background: rgba(255,255,255,0.08); border: none; max-height: 1px;")
        root.addWidget(divider)
        root.addSpacing(4)

        # Item cards
        for item in self.ITEMS:
            w = ItemCardWidget(item, card)
            root.addWidget(w)
            self.item_widgets.append(w)

        root.addStretch()

        # Footer hint
        footer = QLabel("Hold ✌ 1s to close", card)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 8))
        footer.setStyleSheet("color: rgba(255,255,255,0.18); background: transparent; border: none;")
        root.addWidget(footer)

    def _setup_animation(self):
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(180)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Public API ──────────────────────────────────────────────────────────

    def show_launcher(self):
        if self.is_visible_target:
            return
        self.is_visible_target = True

        if not self._cursor_override_active:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.BlankCursor)
            self._cursor_override_active = True

        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()

        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.start()

    def hide_launcher(self):
        if not self.is_visible_target:
            return
        self.is_visible_target = False

        if self._cursor_override_active:
            QGuiApplication.restoreOverrideCursor()
            self._cursor_override_active = False

        for w in self.item_widgets:
            w.set_hover_state(False)

        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(self.windowOpacity())
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.finished.connect(self._on_hide_done)
        self._opacity_anim.start()

    def toggle_launcher(self):
        if self.is_visible_target:
            self.hide_launcher()
        else:
            self.show_launcher()

    def update_finger_hover(self, screen_pos: Optional[Tuple[int, int]]):
        """Drive card highlight from index finger screen coordinates."""
        if not self.is_visible_target or screen_pos is None:
            for w in self.item_widgets:
                w.set_hover_state(False)
            return

        local = self.mapFromGlobal(QPoint(*screen_pos))
        hit: Optional[ItemCardWidget] = None
        for w in self.item_widgets:
            if w.geometry().contains(local):
                hit = w
                break

        for w in self.item_widgets:
            w.set_hover_state(w is hit)

    def trigger_selection_at_finger(self, screen_pos: Optional[Tuple[int, int]]) -> bool:
        """Execute the action for the currently hovered card on PINCH_MIDDLE."""
        if not self.is_visible_target:
            return False

        if screen_pos is not None:
            local = self.mapFromGlobal(QPoint(*screen_pos))
            for w in self.item_widgets:
                if w.geometry().contains(local):
                    self.on_item_clicked(w.data.action_name)
                    return True

        self.hide_launcher()
        return False

    def on_item_clicked(self, action_name: str):
        self.dispatcher.execute_action(action_name)
        self.action_triggered.emit(action_name)
        self.hide_launcher()

    # ── Private ─────────────────────────────────────────────────────────────

    def _on_hide_done(self):
        try:
            self._opacity_anim.finished.disconnect(self._on_hide_done)
        except Exception:
            pass
        if not self.is_visible_target:
            self.hide()
