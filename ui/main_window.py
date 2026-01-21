"""
Main window for the Drum Transcription application
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
import os

from ui.widgets.waveform_widget import WaveformWidget
from ui.widgets.audio_controls import AudioControlsWidget
from ui.workers.transcription_worker import TranscriptionWorker


class DrumTranscriptionUI(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.audio_file = None
        self.worker = None
        self.current_result = None

        # Audio player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)  # Set initial volume to 70%
        self.media_player.setAudioOutput(self.audio_output)

        # Window setup
        self.setWindowTitle("Drum Transcription System")
        self.setGeometry(100, 100, 1200, 800)

        # Setup UI
        self.setup_ui()

        # Connect signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)

    def setup_ui(self):
        """Initialize the user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # === Title ===
        title = QLabel("🥁 Drum Transcription System")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # === File Selection Section ===
        file_group = QGroupBox("Audio File")
        file_layout = QVBoxLayout()

        file_select_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 5px;")
        upload_btn = QPushButton("📁 Upload Audio File")
        upload_btn.clicked.connect(self.upload_file)
        upload_btn.setStyleSheet("padding: 10px;")

        file_select_layout.addWidget(self.file_label, stretch=1)
        file_select_layout.addWidget(upload_btn)
        file_layout.addLayout(file_select_layout)

        # Duration label
        self.duration_label = QLabel("Duration: --:--")
        self.duration_label.setStyleSheet("color: #666; padding: 5px;")
        file_layout.addWidget(self.duration_label)

        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # === Splitter for waveform and controls ===
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === Waveform Display ===
        waveform_group = QGroupBox("Waveform")
        waveform_layout = QVBoxLayout()
        self.waveform_widget = WaveformWidget()
        # Connect interactive signals
        self.waveform_widget.seek_requested.connect(self.on_seek_requested)
        self.waveform_widget.trim_start_changed.connect(self.on_waveform_trim_start_changed)
        self.waveform_widget.trim_end_changed.connect(self.on_waveform_trim_end_changed)
        waveform_layout.addWidget(self.waveform_widget)
        waveform_group.setLayout(waveform_layout)
        splitter.addWidget(waveform_group)

        # === Audio Controls ===
        controls_group = QGroupBox("Audio Controls & Trimming")
        controls_layout = QVBoxLayout()
        self.audio_controls = AudioControlsWidget()
        self.audio_controls.play_pause_clicked.connect(self.toggle_playback)
        self.audio_controls.stop_clicked.connect(self.stop_playback)
        self.audio_controls.trim_changed.connect(self.on_trim_changed)
        self.audio_controls.volume_changed.connect(self.on_volume_changed)
        controls_layout.addWidget(self.audio_controls)
        controls_group.setLayout(controls_layout)
        splitter.addWidget(controls_group)

        splitter.setStretchFactor(0, 2)  # Waveform gets more space
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # === Transcribe Button ===
        self.transcribe_btn = QPushButton("🎵 Transcribe")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setStyleSheet(
            "padding: 15px; font-size: 16px; font-weight: bold; "
            "background-color: #4CAF50; color: white;"
        )
        main_layout.addWidget(self.transcribe_btn)

        # === Progress Bar ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("padding: 5px;")
        main_layout.addWidget(self.progress_bar)

        # === Results Section ===
        results_group = QGroupBox("Transcription Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText(
            "Results will appear here after transcription...\n\n"
            "Upload an isolated drum track and click 'Transcribe' to begin."
        )
        self.results_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

        # === Export Buttons ===
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout()

        self.export_xml_btn = QPushButton("📄 MusicXML")
        self.export_xml_btn.clicked.connect(self.export_musicxml)
        self.export_xml_btn.setEnabled(False)
        self.export_xml_btn.setStyleSheet("padding: 10px;")

        self.export_midi_btn = QPushButton("🎹 MIDI")
        self.export_midi_btn.clicked.connect(self.export_midi)
        self.export_midi_btn.setEnabled(False)
        self.export_midi_btn.setStyleSheet("padding: 10px;")

        self.export_text_btn = QPushButton("📝 Text")
        self.export_text_btn.clicked.connect(self.export_text)
        self.export_text_btn.setEnabled(False)
        self.export_text_btn.setStyleSheet("padding: 10px;")

        export_layout.addWidget(self.export_xml_btn)
        export_layout.addWidget(self.export_midi_btn)
        export_layout.addWidget(self.export_text_btn)

        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)

        # === Status Bar ===
        self.statusBar().showMessage("Ready - Upload an isolated drum track to begin")

    def upload_file(self):
        """Handle file upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.m4a *.ogg);;All Files (*)"
        )

        if file_path:
            self.load_audio_file(file_path)

    def load_audio_file(self, file_path):
        """Load an audio file"""
        try:
            self.audio_file = file_path
            filename = os.path.basename(file_path)

            # Update UI
            self.file_label.setText(f"📁 {filename}")
            self.transcribe_btn.setEnabled(True)
            self.statusBar().showMessage(f"Loading: {filename}...")

            # Load into waveform widget
            self.waveform_widget.load_audio(file_path)

            # Load into media player
            self.media_player.setSource(QUrl.fromLocalFile(file_path))

            # Enable audio controls
            self.audio_controls.set_enabled(True)

            # Clear previous results
            self.results_text.clear()
            self.current_result = None
            self.export_xml_btn.setEnabled(False)
            self.export_midi_btn.setEnabled(False)
            self.export_text_btn.setEnabled(False)

            self.statusBar().showMessage(f"✓ Loaded: {filename}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Could not load audio file:\n{str(e)}"
            )
            self.statusBar().showMessage("✗ Error loading file")

    def on_duration_changed(self, duration):
        """Update duration label when audio duration is known"""
        if duration > 0:
            seconds = duration / 1000
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            self.duration_label.setText(f"Duration: {minutes:02d}:{secs:02d}")

            # Update audio controls max duration
            self.audio_controls.set_duration(seconds)

    def on_position_changed(self, position):
        """Update playback position"""
        seconds = position / 1000
        self.audio_controls.update_position(seconds)
        self.waveform_widget.update_playback_position(seconds)

        # Stop playback if we've reached the trim end
        trim_end = self.audio_controls.get_trim_end()
        if seconds >= trim_end and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_playback()

    def toggle_playback(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.audio_controls.set_playing(False)
        else:
            # Get trim times
            start_time = self.audio_controls.get_trim_start()

            # Seek to start position if at beginning
            if self.media_player.position() == 0:
                self.media_player.setPosition(int(start_time * 1000))

            self.media_player.play()
            self.audio_controls.set_playing(True)

    def stop_playback(self):
        """Stop playback"""
        self.media_player.stop()
        self.audio_controls.set_playing(False)

    def on_volume_changed(self, volume):
        """Handle volume changes (volume is 0.0 to 1.0)"""
        self.audio_output.setVolume(volume)

    def on_trim_changed(self, start_time, end_time):
        """Handle trim time changes from spin boxes"""
        self.waveform_widget.update_trim_region(start_time, end_time)
        self.statusBar().showMessage(
            f"Trim region: {start_time:.2f}s - {end_time:.2f}s"
        )

    def on_seek_requested(self, time):
        """Handle seek request from waveform (click/drag on playback line)"""
        self.media_player.setPosition(int(time * 1000))

    def on_waveform_trim_start_changed(self, start_time):
        """Handle trim start change from waveform drag"""
        # Update the spin box (which will trigger on_trim_changed and update waveform)
        self.audio_controls.start_spinbox.blockSignals(True)
        self.audio_controls.start_spinbox.setValue(start_time)
        self.audio_controls.start_spinbox.blockSignals(False)
        # Update info label manually since we blocked signals
        self.audio_controls.on_trim_changed()

    def on_waveform_trim_end_changed(self, end_time):
        """Handle trim end change from waveform drag"""
        # Update the spin box (which will trigger on_trim_changed and update waveform)
        self.audio_controls.end_spinbox.blockSignals(True)
        self.audio_controls.end_spinbox.setValue(end_time)
        self.audio_controls.end_spinbox.blockSignals(False)
        # Update info label manually since we blocked signals
        self.audio_controls.on_trim_changed()

    def start_transcription(self):
        """Start transcription in background thread"""
        if not self.audio_file:
            QMessageBox.warning(self, "No File", "Please upload an audio file first!")
            return

        # Get trim times
        start_time = self.audio_controls.get_trim_start()
        end_time = self.audio_controls.get_trim_end()

        # Stop playback if playing
        self.stop_playback()

        # Disable controls during processing
        self.transcribe_btn.setEnabled(False)
        self.audio_controls.set_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage(
            f"Transcribing {start_time:.2f}s - {end_time:.2f}s..."
        )

        # Create and start worker thread
        self.worker = TranscriptionWorker(self.audio_file, start_time, end_time)
        self.worker.progress.connect(self.update_progress)
        self.worker.status_message.connect(self.update_status)
        self.worker.finished.connect(self.display_results)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """Update status bar with worker messages"""
        self.statusBar().showMessage(message)

    def display_results(self, result):
        """Display transcription results"""
        self.current_result = result

        # Format results nicely
        text = "═" * 60 + "\n"
        text += "PRIMARY STICKING\n"
        text += "═" * 60 + "\n"
        text += f"{result['primary_sticking']}\n"
        text += f"Confidence: {result['confidence']:.1%}\n\n"

        if result.get('drum_assignments'):
            text += f"Drum Assignments:\n{result['drum_assignments']}\n\n"

        text += "─" * 60 + "\n"
        text += "ALTERNATIVE STICKINGS\n"
        text += "─" * 60 + "\n"
        for i, alt in enumerate(result['alternatives'], 1):
            text += f"{i}. {alt['sticking']:<25} "
            text += f"({alt['confidence']:.1%}) - {alt.get('pattern', 'N/A')}\n"

        text += "═" * 60 + "\n"

        self.results_text.setText(text)

        # Re-enable controls
        self.transcribe_btn.setEnabled(True)
        self.audio_controls.set_enabled(True)
        self.export_xml_btn.setEnabled(True)
        self.export_midi_btn.setEnabled(True)
        self.export_text_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("✓ Transcription complete!")

    def show_error(self, error_msg):
        """Show error message"""
        QMessageBox.critical(
            self,
            "Transcription Error",
            f"Transcription failed:\n{error_msg}"
        )
        self.transcribe_btn.setEnabled(True)
        self.audio_controls.set_enabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("✗ Error occurred")

    def export_musicxml(self):
        """Export to MusicXML"""
        if not self.current_result:
            QMessageBox.warning(self, "No Results", "Please transcribe audio first!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save MusicXML",
            "transcription.musicxml",
            "MusicXML Files (*.musicxml *.xml)"
        )

        if file_path:
            # TODO: Implement actual export when transcription code is ready
            # from src.export.musicxml_export import export_to_musicxml
            # export_to_musicxml(self.current_result, file_path)

            QMessageBox.information(
                self,
                "Export",
                f"MusicXML export will be saved to:\n{file_path}\n\n"
                "(Export functionality will be implemented when transcription code is ready)"
            )
            self.statusBar().showMessage(f"✓ MusicXML: {os.path.basename(file_path)}")

    def export_midi(self):
        """Export to MIDI"""
        if not self.current_result:
            QMessageBox.warning(self, "No Results", "Please transcribe audio first!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save MIDI",
            "transcription.mid",
            "MIDI Files (*.mid *.midi)"
        )

        if file_path:
            # TODO: Implement actual export when transcription code is ready
            QMessageBox.information(
                self,
                "Export",
                f"MIDI export will be saved to:\n{file_path}\n\n"
                "(Export functionality will be implemented when transcription code is ready)"
            )
            self.statusBar().showMessage(f"✓ MIDI: {os.path.basename(file_path)}")

    def export_text(self):
        """Export to text file"""
        if not self.current_result:
            QMessageBox.warning(self, "No Results", "Please transcribe audio first!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text",
            "transcription.txt",
            "Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("DRUM TRANSCRIPTION RESULTS\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Primary Sticking: {self.current_result['primary_sticking']}\n")
                    f.write(f"Confidence: {self.current_result['confidence']:.1%}\n\n")

                    if self.current_result.get('drum_assignments'):
                        f.write(f"Drum Assignments:\n{self.current_result['drum_assignments']}\n\n")

                    f.write("Alternative Stickings:\n")
                    f.write("-" * 60 + "\n")
                    for i, alt in enumerate(self.current_result['alternatives'], 1):
                        f.write(f"{i}. {alt['sticking']} ")
                        f.write(f"({alt['confidence']:.1%})")
                        if 'pattern' in alt:
                            f.write(f" - {alt['pattern']}")
                        f.write("\n")

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Text file saved to:\n{file_path}"
                )
                self.statusBar().showMessage(f"✓ Exported: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Could not save file:\n{str(e)}"
                )

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        # Stop media player
        self.media_player.stop()

        event.accept()
