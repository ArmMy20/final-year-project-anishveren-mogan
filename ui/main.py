from PyQt6.QtWidgets import QApplication
import sys
from main_window import DrumTranscriptionUI

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = DrumTranscriptionUI()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()