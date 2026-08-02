import sys
import argparse
import cv2
import numpy as np
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QApplication

from src.core.actions import ActionDispatcher
from src.system_actions import (
    OpenSpotifyAction,
    OpenChromeAction,
    OpenVSCodeAction,
    TakeScreenshotAction,
    OpenSettingsAction,
    ConsoleLogAction,
)
from src.ui.overlay_launcher import AirOSOverlayWindow
from src.ui.tray_icon import AirOSTrayIcon
from src.core.worker import TrackingWorker

def parse_args():
    parser = argparse.ArgumentParser(description="AirOS Background Layer & Desktop Launcher")
    parser.add_argument("--debug", action="store_true", help="Open OpenCV camera preview debug window on startup")
    return parser.parse_args()

def main():
    args = parse_args()

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    print("==================================================")
    print("             AirOS Desktop Runtime v1.0           ")
    print("   Running silently in the Windows System Tray.   ")
    print("   Hold Victory (PEACE) 1.0s to toggle Launcher.  ")
    print("==================================================")

    dispatcher = ActionDispatcher()
    dispatcher.register_action(OpenSpotifyAction())
    dispatcher.register_action(OpenChromeAction())
    dispatcher.register_action(OpenVSCodeAction())
    dispatcher.register_action(TakeScreenshotAction())
    dispatcher.register_action(OpenSettingsAction())
    dispatcher.register_action(ConsoleLogAction())

    overlay_window = AirOSOverlayWindow(dispatcher)
    tray_icon = AirOSTrayIcon()

    worker = TrackingWorker(dispatcher, hold_threshold_sec=1.0)
    worker.show_debug_window = args.debug

    # Wire Qt Signals and Slots
    worker.victory_toggle_triggered.connect(overlay_window.toggle_launcher)
    worker.cursor_position_updated.connect(overlay_window.update_finger_hover)

    @Slot(object)
    def on_pinch_click(screen_pos):
        if overlay_window.is_visible_target:
            overlay_window.trigger_selection_at_finger(screen_pos)

    worker.pinch_click_triggered.connect(on_pinch_click)

    debug_window_visible = [args.debug]

    @Slot(object)
    def on_debug_frame(frame: np.ndarray):
        if debug_window_visible[0]:
            cv2.imshow("AirOS Debug Camera View", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                cv2.destroyWindow("AirOS Debug Camera View")
                debug_window_visible[0] = False
                worker.show_debug_window = False

    worker.frame_processed.connect(on_debug_frame)

    @Slot()
    def toggle_debug_window():
        debug_window_visible[0] = not debug_window_visible[0]
        worker.show_debug_window = debug_window_visible[0]
        if not debug_window_visible[0]:
            cv2.destroyAllWindows()
        else:
            print("[AirOS System Tray] Debug Camera View Enabled.")

    tray_icon.toggle_launcher_requested.connect(overlay_window.toggle_launcher)
    tray_icon.toggle_debug_camera_requested.connect(toggle_debug_window)

    @Slot()
    def on_quit():
        print("Shutting down AirOS Runtime...")
        worker.stop()
        cv2.destroyAllWindows()
        app.quit()

    tray_icon.quit_requested.connect(on_quit)

    tray_icon.show()
    worker.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
