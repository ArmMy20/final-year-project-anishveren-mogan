import os
import pytest
from pathlib import Path

pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skip frontend GUI imports on CI (headless environment)",
)

class TestFrontendImports:
    def test_import_main_window(self):
        """Verify main_window module can be imported."""
        from ui.main_window import DrumTranscriptionUI
        assert DrumTranscriptionUI is not None

    def test_import_waveform_widget(self):
        """Verify waveform_widget module can be imported."""
        from ui.widgets.waveform_widget import WaveformWidget
        assert WaveformWidget is not None

    def test_import_audio_controls(self):
        """Verify audio_controls module can be imported."""
        from ui.widgets.audio_controls import AudioControlsWidget
        assert AudioControlsWidget is not None

    def test_import_transcription_worker(self):
        """Verify transcription_worker module can be imported."""
        from ui.workers.transcription_worker import TranscriptionWorker
        assert TranscriptionWorker is not None


class TestProjectStructure:
    def test_samples_directory_exists(self):
        """Verify samples directory exists."""
        samples_dir = Path(__file__).parent.parent / "samples"
        assert samples_dir.exists(), "samples/ directory not found"

    def test_sample_audio_exists(self):
        """Verify at least one sample audio file exists."""
        samples_dir = Path(__file__).parent.parent / "samples"
        audio_files = list(samples_dir.glob("*.wav"))
        assert len(audio_files) > 0, "No .wav files found in samples/"

    def test_ui_directory_exists(self):
        """Verify ui directory structure exists."""
        ui_dir = Path(__file__).parent.parent / "ui"
        assert ui_dir.exists(), "ui/ directory not found"
        assert (ui_dir / "main_window.py").exists(), "main_window.py not found"
        assert (ui_dir / "widgets").exists(), "ui/widgets/ not found"
        assert (ui_dir / "workers").exists(), "ui/workers/ not found"


class TestDependencies:
    def test_import_pyqt6(self):
        """Verify PyQt6 is installed."""
        import PyQt6
        assert PyQt6 is not None

    def test_import_librosa(self):
        """Verify librosa is installed."""
        import librosa
        assert librosa is not None

    def test_import_numpy(self):
        """Verify numpy is installed."""
        import numpy as np
        assert np is not None

    def test_import_soundfile(self):
        """Verify soundfile is installed."""
        import soundfile as sf
        assert sf is not None

    def test_import_torch(self):
        """Verify torch is installed."""
        import torch
        assert torch is not None
