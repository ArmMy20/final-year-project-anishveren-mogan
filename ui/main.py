from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import sys
from main_window import DrumTranscriptionUI

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName('Drum Transcription System')
    app.setStyle('Fusion')

    window = DrumTranscriptionUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()