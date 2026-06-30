"""Notch overlay UI (Option B).

A frameless window that lives in the MacBook notch: a small black sliver that
merges with the physical notch when idle, and drops downward to stream the
generated response when triggered.

To sit *above* the menu bar and flush against the notch we reach through to the
underlying AppKit ``NSWindow`` (via pyobjc) and raise its window level. If that
fails for any reason (no pyobjc, OS quirk), we fall back to Option A: a normal
always-on-top pill positioned just *below* the notch.

All public mutations are exposed as Qt signals so background threads (audio /
hotkeys) can drive the UI safely by emitting, never touching widgets directly.
"""

from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

import pyperclip

# --- Geometry ---------------------------------------------------------------
COLLAPSED_W = 220     # ~ notch width
COLLAPSED_H = 34      # ~ menu-bar / notch height
EXPANDED_W = 520
EXPANDED_H = 190
AUTO_COLLAPSE_MS = 7000   # collapse this long after a response finishes

# AppKit window levels (from NSWindow.h). Menu bar is 24; status is 25.
_NS_STATUS_WINDOW_LEVEL = 25


class OverlayWindow(QWidget):
    # Signals — emit these from any thread to drive the UI safely.
    sig_start = pyqtSignal()        # begin a new response (expand + clear)
    token_received = pyqtSignal(str)  # append a streamed token
    sig_finish = pyqtSignal()       # response complete (arm auto-collapse)
    sig_copy = pyqtSignal()         # copy current response to clipboard

    def __init__(self):
        super().__init__()
        self._current_response = ""
        self._expanded = False
        self._fallback_mode = False  # True => Option A (below the notch)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Don't steal focus from the meeting app when shown/updated.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, COLLAPSED_H, 16, 16)
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: #f2f2f2; font-size: 14px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #8a8a8a; font-size: 11px;")

        layout.addWidget(self.status)
        layout.addWidget(self.label, stretch=1)
        self.setLayout(layout)

        # Wire signals -> slots (all run on the GUI thread).
        self.sig_start.connect(self.start_new_response)
        self.token_received.connect(self.append_token)
        self.sig_finish.connect(self._on_finish)
        self.sig_copy.connect(self.copy_text)

        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.timeout.connect(self.collapse)

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status.setText(""))

        self.collapse()  # start idle, merged into the notch

    # --- AppKit integration -------------------------------------------------
    def _raise_to_notch_level(self) -> None:
        """Lift the native window above the menu bar so it overlaps the notch.

        Falls back to Option A (pill below the notch) if AppKit isn't reachable.
        """
        try:
            import objc

            view = objc.objc_object(c_void_p=int(self.winId()))
            ns_window = view.window()
            ns_window.setLevel_(_NS_STATUS_WINDOW_LEVEL)
            # Show across all Spaces and over fullscreen apps.
            can_join_all_spaces = 1 << 0
            fullscreen_auxiliary = 1 << 8
            ns_window.setCollectionBehavior_(
                can_join_all_spaces | fullscreen_auxiliary
            )
            self._fallback_mode = False
        except Exception as exc:  # noqa: BLE001 - any failure => fall back
            print(f"[overlay] notch positioning unavailable, using fallback: {exc}")
            self._fallback_mode = True

    # --- Geometry helpers ---------------------------------------------------
    def _top_y(self) -> int:
        """Y of the screen top (0) for notch mode, or below the notch for fallback."""
        return COLLAPSED_H if self._fallback_mode else 0

    def _reposition(self, w: int, h: int) -> None:
        screen = self.screen() or self.window().screen()
        geo = screen.geometry()  # full frame, includes the menu-bar/notch strip
        x = geo.x() + (geo.width() - w) // 2
        y = geo.y() + self._top_y()
        self.setFixedSize(w, h)
        self.move(x, y)

    # --- State transitions --------------------------------------------------
    def expand(self) -> None:
        self._expanded = True
        self._reposition(EXPANDED_W, EXPANDED_H)
        self.update()

    def collapse(self) -> None:
        self._expanded = False
        self._current_response = ""
        self.label.setText("")
        self.status.setText("")
        self._reposition(COLLAPSED_W, COLLAPSED_H)
        self.update()

    def start_new_response(self) -> None:
        self._collapse_timer.stop()
        self._current_response = ""
        self.label.setText("")
        self.status.setText("Generating…")
        self.expand()

    def append_token(self, token: str) -> None:
        if not self._expanded:
            self.expand()
        self._current_response += token
        self.label.setText(self._current_response)

    def _on_finish(self) -> None:
        self.status.setText("Ctrl+Shift+C to copy")
        self._collapse_timer.start(AUTO_COLLAPSE_MS)

    def copy_text(self) -> None:
        if self._current_response.strip():
            pyperclip.copy(self._current_response)
            self.status.setText("Copied!")
            self._status_timer.start(1500)

    # --- Painting -----------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802 - Qt override
        """Draw a black panel: flush (square) at the top, rounded at the bottom."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        radius = 16.0
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right(), rect.top())
        path.lineTo(rect.right(), rect.bottom() - radius)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - radius, rect.bottom())
        path.lineTo(rect.left() + radius, rect.bottom())
        path.quadTo(rect.left(), rect.bottom(), rect.left(), rect.bottom() - radius)
        path.closeSubpath()

        painter.fillPath(path, QColor(0, 0, 0, 235))

    def showEvent(self, event):  # noqa: N802 - Qt override
        super().showEvent(event)
        # winId() is only valid once the native window exists.
        self._raise_to_notch_level()
        self._reposition(*( (EXPANDED_W, EXPANDED_H) if self._expanded
                            else (COLLAPSED_W, COLLAPSED_H) ))


if __name__ == "__main__":
    # Isolation test: stream dummy text into the notch, then auto-collapse.
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    overlay = OverlayWindow()
    overlay.show()

    demo = ("Absolutely, that's a really important point to surface. While there "
            "are certainly multiple perspectives to consider here, at the end of "
            "the day it really comes down to how we leverage our bandwidth going "
            "forward. Happy to dive deeper on any of these threads!")
    overlay.sig_start.emit()
    it = iter(demo.split(" "))

    def feed():
        try:
            overlay.token_received.emit(next(it) + " ")
            QTimer.singleShot(40, feed)
        except StopIteration:
            overlay.sig_finish.emit()

    QTimer.singleShot(500, feed)
    sys.exit(app.exec())
