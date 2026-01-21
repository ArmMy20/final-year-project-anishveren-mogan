from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import soundfile as sf


class WaveformWidget(QWidget):
    """Widget to display audio waveform"""

    # Signals for interactive controls
    seek_requested = pyqtSignal(float)  # Emit when user clicks to seek
    trim_start_changed = pyqtSignal(float)  # Emit when trim start is dragged
    trim_end_changed = pyqtSignal(float)  # Emit when trim end is dragged

    def __init__(self, parent=None):
        super().__init__(parent)

        self.audio_data = None
        self.sample_rate = None
        self.duration = 0
        self.trim_start = 0
        self.trim_end = 0
        self.playback_position = 0

        # Interaction state
        self.dragging_element = None  # Can be 'trim_start', 'trim_end', 'playback', or None
        self.drag_threshold = 0.5  # seconds - how close click needs to be to grab a line

        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Status label
        self.status_label = QLabel("No audio loaded")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-style: italic; padding: 10px;")
        layout.addWidget(self.status_label)

        # Matplotlib figure with transparent background
        self.figure = Figure(figsize=(12, 4))  # Larger default size
        self.figure.patch.set_facecolor('none')  # Transparent figure background
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setMinimumHeight(200)  # Set minimum height
        layout.addWidget(self.canvas, stretch=1)  # Allow it to expand

        # Initial empty plot with styled appearance
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

        # Tight layout to minimize whitespace
        self.figure.tight_layout(pad=1.5)
        self.canvas.draw()

        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def load_audio(self, file_path):
        """Load and display audio waveform"""
        try:
            # Load audio file
            self.audio_data, self.sample_rate = sf.read(file_path)

            # Convert stereo to mono if needed
            if len(self.audio_data.shape) > 1:
                self.audio_data = np.mean(self.audio_data, axis=1)

            self.duration = len(self.audio_data) / self.sample_rate
            self.trim_start = 0
            self.trim_end = self.duration

            # Update status
            self.status_label.setText(
                f"Loaded: {self.duration:.2f}s, {self.sample_rate}Hz, "
                f"{len(self.audio_data)} samples"
            )

            # Plot waveform
            self.plot_waveform()

        except Exception as e:
            self.status_label.setText(f"Error loading audio: {str(e)}")
            raise

    def plot_waveform(self):
        if self.audio_data is None:
            return

        # Clear previous plot
        self.ax.clear()

        # Reapply styling after clear
        self.ax.set_facecolor('#f5f5f5')
        self.ax.spines['top'].set_color('#ccc')
        self.ax.spines['right'].set_color('#ccc')
        self.ax.spines['bottom'].set_color('#999')
        self.ax.spines['left'].set_color('#999')

        # Downsample for display (plot every Nth sample for performance)
        downsample_factor = max(1, len(self.audio_data) // 10000)
        display_data = self.audio_data[::downsample_factor]
        time_axis = np.linspace(0, self.duration, len(display_data))

        # Grey out areas outside trim region (plot these first, so they're in the background)
        if self.trim_start > 0 or self.trim_end < self.duration:
            # Grey out left side (before trim start)
            if self.trim_start > 0:
                self.ax.axvspan(0, self.trim_start, alpha=0.4, color='#999999', zorder=1)

            # Grey out right side (after trim end)
            if self.trim_end < self.duration:
                self.ax.axvspan(self.trim_end, self.duration, alpha=0.4, color='#999999', zorder=1)

            # Highlight trim region with white background
            self.ax.axvspan(
                self.trim_start, self.trim_end,
                alpha=0.8, color='white', zorder=2
            )

            # Add green boundary lines for trim region
            self.ax.axvline(self.trim_start, color='#4CAF50', linestyle='--', linewidth=2, alpha=0.9, zorder=4)
            self.ax.axvline(self.trim_end, color='#4CAF50', linestyle='--', linewidth=2, alpha=0.9, zorder=4)

        # Plot waveform with nice blue color (on top of regions)
        self.ax.plot(time_axis, display_data, color='#2196F3', linewidth=0.5, alpha=0.8, zorder=3)

        # Show playback position
        self.playback_line = self.ax.axvline(
            self.playback_position, color='#f44336', linestyle='-', linewidth=2, alpha=0.8, zorder=5
        )

        # Labels and formatting
        self.ax.set_xlabel('Time (seconds)', fontsize=10, color='#333')
        self.ax.set_ylabel('Amplitude', fontsize=10, color='#333')
        self.ax.tick_params(colors='#666', labelsize=9)
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color='#999', zorder=0)

        # Add some padding to x-axis limits so the waveform doesn't touch the edges
        padding = self.duration * 0.02  # 2% padding on each side
        self.ax.set_xlim(-padding, self.duration + padding)

        # Tight layout to minimize whitespace
        self.figure.tight_layout(pad=1.5)

        # Redraw
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

        # Clamp to valid range
        click_time = max(0, min(self.duration, click_time))

        # Check if clicking near trim start
        if abs(click_time - self.trim_start) < self.drag_threshold:
            self.dragging_element = 'trim_start'
            self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
        # Check if clicking near trim end
        elif abs(click_time - self.trim_end) < self.drag_threshold:
            self.dragging_element = 'trim_end'
            self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
        # Otherwise, seek to clicked position
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
            # Reset cursor when leaving the plot
            if self.dragging_element is None:
                self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
            return

        move_time = event.xdata
        if move_time is None:
            return

        # Clamp to valid range
        move_time = max(0, min(self.duration, move_time))

        # If dragging, update the appropriate element
        if self.dragging_element == 'trim_start':
            # Don't allow trim start to go past trim end
            new_start = min(move_time, self.trim_end - 0.1)
            self.trim_start = max(0, new_start)
            self.trim_start_changed.emit(self.trim_start)
            self.plot_waveform()

        elif self.dragging_element == 'trim_end':
            # Don't allow trim end to go before trim start
            new_end = max(move_time, self.trim_start + 0.1)
            self.trim_end = min(self.duration, new_end)
            self.trim_end_changed.emit(self.trim_end)
            self.plot_waveform()

        elif self.dragging_element == 'playback':
            # Scrubbing through audio
            self.seek_requested.emit(move_time)

        else:
            # Not dragging - show appropriate cursor when hovering
            if abs(move_time - self.trim_start) < self.drag_threshold or \
               abs(move_time - self.trim_end) < self.drag_threshold:
                self.canvas.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
