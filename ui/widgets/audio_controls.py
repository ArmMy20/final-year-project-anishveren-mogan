from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDoubleSpinBox, QSlider
)

class AudioControlsWidget(QWidget):
    play_pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    trim_changed = pyqtSignal(float, float)
    volume_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.duration = 0
        self.is_playing = False

        self.setup_ui()
        self.set_enabled(False)

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        playback_layout = QHBoxLayout()

        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.clicked.connect(self.on_play_pause)
        self.play_pause_btn.setStyleSheet("padding: 10px; font-size: 14px;")

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setStyleSheet("padding: 10px; font-size: 14px;")

        self.position_label = QLabel("00:00 / 00:00")
        self.position_label.setStyleSheet("font-family: monospace; font-size: 14px;")

        playback_layout.addWidget(self.play_pause_btn)
        playback_layout.addWidget(self.stop_btn)
        playback_layout.addWidget(self.position_label)
        playback_layout.addStretch()

        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("font-size: 16px;")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(120)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        self.volume_label = QLabel("70%")
        self.volume_label.setMinimumWidth(40)
        self.volume_label.setStyleSheet("color: #666;")

        playback_layout.addWidget(volume_label)
        playback_layout.addWidget(self.volume_slider)
        playback_layout.addWidget(self.volume_label)

        layout.addLayout(playback_layout)

        trim_label = QLabel("Trim Region (seconds):")
        trim_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(trim_label)

        trim_layout = QHBoxLayout()

        start_label = QLabel("Start:")
        self.start_spinbox = QDoubleSpinBox()
        self.start_spinbox.setDecimals(2)
        self.start_spinbox.setSingleStep(0.1)
        self.start_spinbox.setMinimum(0.0)
        self.start_spinbox.setMaximum(999.99)
        self.start_spinbox.setValue(0.0)
        self.start_spinbox.setSuffix(" s")
        self.start_spinbox.valueChanged.connect(self.on_trim_changed)
        self.start_spinbox.setStyleSheet("padding: 5px;")

        end_label = QLabel("End:")
        self.end_spinbox = QDoubleSpinBox()
        self.end_spinbox.setDecimals(2)
        self.end_spinbox.setSingleStep(0.1)
        self.end_spinbox.setMinimum(0.0)
        self.end_spinbox.setMaximum(999.99)
        self.end_spinbox.setValue(10.0)
        self.end_spinbox.setSuffix(" s")
        self.end_spinbox.valueChanged.connect(self.on_trim_changed)
        self.end_spinbox.setStyleSheet("padding: 5px;")

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_trim)
        reset_btn.setStyleSheet("padding: 5px;")

        trim_layout.addWidget(start_label)
        trim_layout.addWidget(self.start_spinbox)
        trim_layout.addWidget(end_label)
        trim_layout.addWidget(self.end_spinbox)
        trim_layout.addWidget(reset_btn)
        trim_layout.addStretch()

        layout.addLayout(trim_layout)

        self.trim_info_label = QLabel("Trim duration: 0.00s")
        self.trim_info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.trim_info_label)

    def on_play_pause(self):
        """Handle play/pause button click"""
        self.play_pause_clicked.emit()

    def on_stop(self):
        """Handle stop button click"""
        self.stop_clicked.emit()
        self.set_playing(False)

    def on_volume_changed(self, value):
        """Handle volume slider changes"""
        self.volume_label.setText(f"{value}%")
        volume = value / 100.0
        self.volume_changed.emit(volume)

    def on_trim_changed(self):
        """Handle trim value changes"""
        start = self.start_spinbox.value()
        end = self.end_spinbox.value()

        if start >= end:
            if self.sender() == self.start_spinbox:
                self.start_spinbox.setValue(max(0, end - 0.1))
            else:
                self.end_spinbox.setValue(min(self.duration, start + 0.1))
            return

        duration = end - start
        self.trim_info_label.setText(f"Trim duration: {duration:.2f}s")
        self.trim_changed.emit(start, end)

    def reset_trim(self):
        """Reset trim to full duration"""
        self.start_spinbox.setValue(0.0)
        self.end_spinbox.setValue(self.duration)

    def set_duration(self, duration):
        """Set the audio duration"""
        self.duration = duration
        self.end_spinbox.setMaximum(duration)
        self.end_spinbox.setValue(duration)
        self.start_spinbox.setMaximum(duration)
        self.on_trim_changed()

    def set_playing(self, playing):
        """Update UI based on playing state"""
        self.is_playing = playing
        if playing:
            self.play_pause_btn.setText("⏸ Pause")
        else:
            self.play_pause_btn.setText("▶ Play")

    def set_enabled(self, enabled):
        """Enable/disable controls"""
        self.play_pause_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.start_spinbox.setEnabled(enabled)
        self.end_spinbox.setEnabled(enabled)

    def update_position(self, position):
        """Update position display"""
        pos_min = int(position // 60)
        pos_sec = int(position % 60)
        dur_min = int(self.duration // 60)
        dur_sec = int(self.duration % 60)

        self.position_label.setText(
            f"{pos_min:02d}:{pos_sec:02d} / {dur_min:02d}:{dur_sec:02d}"
        )

    def get_trim_start(self):
        """Get trim start time"""
        return self.start_spinbox.value()

    def get_trim_end(self):
        """Get trim end time"""
        return self.end_spinbox.value()
