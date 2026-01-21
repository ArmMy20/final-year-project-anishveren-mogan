import numpy as np
import soundfile as sf

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class WaveformWidget(QWidget):
    """Widget to display audio waveform"""

    seek_requested = pyqtSignal(float)
    trim_start_changed = pyqtSignal(float)
    trim_end_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_data = None
        self.sample_rate = None
        self.duration = 0
        self.trim_start = 0
        self.trim_end = 0
        self.playback_position = 0

        self.dragging_element = None
        self.drag_threshold = 0.5

        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.status_label = QLabel("No audio loaded")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-style: italic; padding: 10px;")
        layout.addWidget(self.status_label)

        self.figure = Figure(figsize=(12, 4))
        self.figure.patch.set_facecolor('none')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setMinimumHeight(200)
        layout.addWidget(self.canvas, stretch=1)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#f5f5f5')  # Light gray background
        self.ax.set_xlabel('Time (seconds)', fontsize=10, color='#333')
        self.ax.set_ylabel('Amplitude', fontsize=10, color='#333')
        self.ax.tick_params(colors='#666', labelsize=9)
        self.ax.spines['top'].set_color('#ccc')
        self.ax.spines['right'].set_color('#ccc')
        self.ax.spines['bottom'].set_color('#999')
        self.ax.spines['left'].set_color('#999')
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        self.figure.tight_layout(pad=1.5)
        self.canvas.draw()
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def load_audio(self, file_path):
        """Load and display audio waveform"""
        try:
            self.audio_data, self.sample_rate = sf.read(file_path)

            if len(self.audio_data.shape) > 1:
                self.audio_data = np.mean(self.audio_data, axis=1)

            self.duration = len(self.audio_data) / self.sample_rate
            self.trim_start = 0
            self.trim_end = self.duration

            self.status_label.setText(
                f"Loaded: {self.duration:.2f}s, {self.sample_rate}Hz, "
                f"{len(self.audio_data)} samples"
            )

            self.plot_waveform()

        except Exception as e:
            self.status_label.setText(f"Error loading audio: {str(e)}")
            raise

    def plot_waveform(self):
        if self.audio_data is None:
            return

        self.ax.clear()
        self.ax.set_facecolor('#f5f5f5')
        self.ax.spines['top'].set_color('#ccc')
        self.ax.spines['right'].set_color('#ccc')
        self.ax.spines['bottom'].set_color('#999')
        self.ax.spines['left'].set_color('#999')

        downsample_factor = max(1, len(self.audio_data) // 10000)
        display_data = self.audio_data[::downsample_factor]
        time_axis = np.linspace(0, self.duration, len(display_data))

        if self.trim_start > 0 or self.trim_end < self.duration:
            if self.trim_start > 0:
                self.ax.axvspan(0, self.trim_start, alpha=0.4, color='#999999', zorder=1)

            if self.trim_end < self.duration:
                self.ax.axvspan(self.trim_end, self.duration, alpha=0.4, color='#999999', zorder=1)

            self.ax.axvspan(
                self.trim_start, self.trim_end,
                alpha=0.8, color='white', zorder=2
            )

            self.ax.axvline(self.trim_start, color='#4CAF50', linestyle='--', linewidth=2, alpha=0.9, zorder=4)
            self.ax.axvline(self.trim_end, color='#4CAF50', linestyle='--', linewidth=2, alpha=0.9, zorder=4)

        self.ax.plot(time_axis, display_data, color='#2196F3', linewidth=0.5, alpha=0.8, zorder=3)
        self.playback_line = self.ax.axvline(
            self.playback_position, color='#f44336', linestyle='-', linewidth=2, alpha=0.8, zorder=5
        )

        self.ax.set_xlabel('Time (seconds)', fontsize=10, color='#333')
        self.ax.set_ylabel('Amplitude', fontsize=10, color='#333')
        self.ax.tick_params(colors='#666', labelsize=9)
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color='#999', zorder=0)

        padding = self.duration * 0.02
        self.ax.set_xlim(-padding, self.duration + padding)

        self.figure.tight_layout(pad=1.5)
        self.canvas.draw()

    def update_trim_region(self, start_time, end_time):
        self.trim_start = start_time
        self.trim_end = end_time
        self.plot_waveform()

    def update_playback_position(self, position):
        self.playback_position = position

        if self.audio_data is not None and hasattr(self, 'playback_line'):
            self.playback_line.set_xdata([position, position])
            self.canvas.draw_idle()

    def on_mouse_press(self, event):
        """Handle mouse press events for dragging"""
        if event.inaxes != self.ax or self.audio_data is None:
            return

        click_time = event.xdata
        if click_time is None:
            return

        click_time = max(0, min(self.duration, click_time))

        if abs(click_time - self.trim_start) < self.drag_threshold:
            self.dragging_element = 'trim_start'
            self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
        elif abs(click_time - self.trim_end) < self.drag_threshold:
            self.dragging_element = 'trim_end'
            self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.dragging_element = 'playback'
            self.seek_requested.emit(click_time)

    def on_mouse_release(self, event):
        """Handle mouse release events"""
        self.dragging_element = None
        self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

    def on_mouse_move(self, event):
        """Handle mouse move events for dragging"""
        if event.inaxes != self.ax or self.audio_data is None:
            if self.dragging_element is None:
                self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
            return

        move_time = event.xdata
        if move_time is None:
            return

        move_time = max(0, min(self.duration, move_time))

        if self.dragging_element == 'trim_start':
            new_start = min(move_time, self.trim_end - 0.1)
            self.trim_start = max(0, new_start)
            self.trim_start_changed.emit(self.trim_start)
            self.plot_waveform()

        elif self.dragging_element == 'trim_end':
            new_end = max(move_time, self.trim_start + 0.1)
            self.trim_end = min(self.duration, new_end)
            self.trim_end_changed.emit(self.trim_end)
            self.plot_waveform()

        elif self.dragging_element == 'playback':
            self.seek_requested.emit(move_time)

        else:
            if abs(move_time - self.trim_start) < self.drag_threshold or \
               abs(move_time - self.trim_end) < self.drag_threshold:
                self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
