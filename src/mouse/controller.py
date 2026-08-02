import ctypes

# Windows User32 API Mouse Event Flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

class NativeMouseController:
    """
    Zero-dependency, sub-millisecond Windows OS Native Mouse Controller.
    Interacts directly with the OS Windowing system via ctypes.windll.user32.
    """
    def __init__(self):
        try:
            self.user32 = ctypes.windll.user32
            self.is_windows = True
        except Exception:
            self.user32 = None
            self.is_windows = False

    def move_to(self, screen_x: int, screen_y: int) -> None:
        """
        Moves system desktop cursor to exact screen coordinates (X, Y).
        """
        if self.is_windows and self.user32:
            self.user32.SetCursorPos(screen_x, screen_y)

    def left_press(self) -> None:
        """
        Triggers Left Mouse Button Down event (starts click or drag operation).
        """
        if self.is_windows and self.user32:
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def left_release(self) -> None:
        """
        Triggers Left Mouse Button Up event (ends click or drag operation).
        """
        if self.is_windows and self.user32:
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def left_click(self) -> None:
        """
        Triggers full Left Click (Press + Release).
        """
        self.left_press()
        self.left_release()
