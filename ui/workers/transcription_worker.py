from PyQt6.QtCore import QThread, pyqtSignal

class TranscriptionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file

    def run(self):
        try:
            import time

            self.progress.emit(20)
            time.sleep(1)  # Simulate preprocessing

            self.progress.emit(50)
            time.sleep(1)  # Simulate onset detection

            self.progress.emit(80)
            time.sleep(1)  # Simulate classification

            self.progress.emit(100)

            # Mock result replace with actual transcription code later
            result = {
                'primary_sticking': 'RlKRLKrlRL',
                'confidence': 0.85,
                'alternatives': [
                    {'sticking': 'RrKRLKrlRL', 'confidence': 0.72},
                    {'sticking': 'RlKRRKllRL', 'confidence': 0.65}
                ]
            }

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))