from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox
)
from workers.transcription_worker import TranscriptionWorker
import os


class DrumTranscriptionUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_file = None
        self.worker = None
        self.current_result = None

        self.setWindowTitle("Drum Transcription System")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # === Title ===
        title = QLabel("Drum Transcription System")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        # === File Selection Section ===
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 5px;")
        upload_btn = QPushButton("Upload Audio File")
        upload_btn.clicked.connect(self.upload_file)
        upload_btn.setStyleSheet("padding: 10px;")

        file_layout.addWidget(self.file_label, stretch=1)
        file_layout.addWidget(upload_btn)
        main_layout.addLayout(file_layout)

        # === Info Label ===
        info_label = QLabel("Upload isolated drum tracks only (WAV, MP3, FLAC)")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        main_layout.addWidget(info_label)

        # === Transcribe Button ===
        self.transcribe_btn = QPushButton("🎵 Transcribe")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setStyleSheet("padding: 15px; font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.transcribe_btn)

        # === Progress Bar ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("padding: 5px;")
        main_layout.addWidget(self.progress_bar)

        # === Results Section ===
        results_label = QLabel("Results:")
        results_label.setStyleSheet("font-weight: bold; padding-top: 10px;")
        main_layout.addWidget(results_label)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Results will appear here after transcription...")
        self.results_text.setStyleSheet("font-family: monospace; font-size: 12px;")
        main_layout.addWidget(self.results_text)

        # === Export Buttons ===
        export_label = QLabel("Export:")
        export_label.setStyleSheet("font-weight: bold; padding-top: 10px;")
        main_layout.addWidget(export_label)

        export_layout = QHBoxLayout()

        self.export_xml_btn = QPushButton("📄 Export MusicXML")
        self.export_xml_btn.clicked.connect(self.export_musicxml)
        self.export_xml_btn.setEnabled(False)
        self.export_xml_btn.setStyleSheet("padding: 10px;")

        self.export_midi_btn = QPushButton("🎹 Export MIDI")
        self.export_midi_btn.clicked.connect(self.export_midi)
        self.export_midi_btn.setEnabled(False)
        self.export_midi_btn.setStyleSheet("padding: 10px;")

        self.export_text_btn = QPushButton("📝 Export Text")
        self.export_text_btn.clicked.connect(self.export_text)
        self.export_text_btn.setEnabled(False)
        self.export_text_btn.setStyleSheet("padding: 10px;")

        export_layout.addWidget(self.export_xml_btn)
        export_layout.addWidget(self.export_midi_btn)
        export_layout.addWidget(self.export_text_btn)
        main_layout.addLayout(export_layout)

        # === Status Bar ===
        self.statusBar().showMessage("Ready - Upload an isolated drum track to begin")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        )

        if file_path:
            self.audio_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(f"📁 {filename}")
            self.transcribe_btn.setEnabled(True)
            self.statusBar().showMessage(f"Loaded: {filename}")

            self.results_text.clear()
            self.current_result = None
            self.export_xml_btn.setEnabled(False)
            self.export_midi_btn.setEnabled(False)
            self.export_text_btn.setEnabled(False)

    def start_transcription(self):
        if not self.audio_file:
            QMessageBox.warning(self, "No File", "Please upload an audio file first!")
            return

        self.transcribe_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Transcribing...")

        self.worker = TranscriptionWorker(self.audio_file)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.display_results)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_results(self, result):
        self.current_result = result

        # Format results
        text = "═" * 50 + "\n"
        text += "PRIMARY STICKING\n"
        text += "═" * 50 + "\n"
        text += f"{result['primary_sticking']}\n"
        text += f"Confidence: {result['confidence']:.1%}\n\n"

        text += "─" * 50 + "\n"
        text += "ALTERNATIVE STICKINGS\n"
        text += "─" * 50 + "\n"
        for i, alt in enumerate(result['alternatives'], 1):
            text += f"{i}. {alt['sticking']:<20} ({alt['confidence']:.1%})\n"

        text += "═" * 50 + "\n"

        self.results_text.setText(text)

        self.transcribe_btn.setEnabled(True)
        self.export_xml_btn.setEnabled(True)
        self.export_midi_btn.setEnabled(True)
        self.export_text_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("✓ Transcription complete!")

    def show_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Transcription failed:\n{error_msg}")
        self.transcribe_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("✗ Error occurred")

    def export_musicxml(self):
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
            # TODO: Implement actual export
            # from src.export.musicxml_export import export_to_musicxml
            # export_to_musicxml(self.current_result, file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"MusicXML will be exported to:\n{file_path}\n\n(Export functionality to be implemented)"
            )
            self.statusBar().showMessage(f"✓ Exported to {os.path.basename(file_path)}")

    def export_midi(self):
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
            # TODO: Implement actual export
            # from src.export.midi_export import export_to_midi
            # export_to_midi(self.current_result, file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"MIDI will be exported to:\n{file_path}\n\n(Export functionality to be implemented)"
            )
            self.statusBar().showMessage(f"✓ Exported to {os.path.basename(file_path)}")

    def export_text(self):
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
                    f.write(f"Primary Sticking: {self.current_result['primary_sticking']}\n")
                    f.write(f"Confidence: {self.current_result['confidence']:.1%}\n\n")
                    f.write("Alternative Stickings:\n")
                    for i, alt in enumerate(self.current_result['alternatives'], 1):
                        f.write(f"{i}. {alt['sticking']} ({alt['confidence']:.1%})\n")

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Text exported to:\n{file_path}"
                )
                self.statusBar().showMessage(f"✓ Exported to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not save file:\n{str(e)}")
