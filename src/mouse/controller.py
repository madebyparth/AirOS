import ctypes

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class NativeMouseController:
    def __init__(self):
        try:
            self.user32 = ctypes.windll.user32
            self.is_windows = True
        except Exception:
            self.user32 = None
            self.is_windows = False

    def move_to(self, screen_x: int, screen_y: int) -> None:
        if self.is_windows and self.user32:
            self.user32.SetCursorPos(screen_x, screen_y)

    def left_press(self) -> None:
        if self.is_windows and self.user32:
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def left_release(self) -> None:
        if self.is_windows and self.user32:
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def left_click(self) -> None:
        self.left_press()
        self.left_release()
