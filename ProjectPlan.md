# Drum Transcription System - Project Plan

## Project Overview

A PyTorch-based system to transcribe drum performances from audio clips, identifying:
- Drum onsets (when hits occur)
- Drum types (kick, snare, hi-hat, toms, cymbals)
- Sticking patterns (R/L/K notation)
- Export to MusicXML for notation software (Sibelius, MuseScore)

**Example Use Case:**
User provides an audio clip with a drum fill → System analyzes audio → Outputs: "RlKKRllrrL" with drum assignments (R=snare, K=kick, etc.) → Exports to MusicXML

---

## Table of Contents

1. [Project Scope](#project-scope)
2. [Processing Flow](#processing-flow)
2. [Technical Architecture](#technical-architecture)
3. [Project Structure](#project-structure)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Key Technologies](#key-technologies)
6. [Datasets & Training](#datasets--training)
7. [Evaluation Strategy](#evaluation-strategy)
8. [Challenges & Solutions](#challenges--solutions)

---

## Project Scope

### Core Features (Essential)
- Transcribe isolated drum tracks
- Detect kick, snare, hi-hat, toms, cymbals
- Basic sticking prediction (rule-based + ML model)
- Audio trimming functionality
- Single best-guess transcription output

### Important Extensions (Recommended)
- **Multiple sticking hypotheses** with confidence scores
- **MusicXML export** for notation software
- **Source separation preprocessing** for full music mixes (using Demucs/Spleeter)

### Advanced Features (If Time Permits)
- Train on hand-labeled sticking dataset
- Velocity/dynamics detection (changing notation based on ghost notes, for instance)
- Web UI for interactive transcription
- Real-time transcription

### Out of Scope
- Video analysis
- 3D motion capture
- Real-time performance feedback
- Mobile app

---

## Processing Flow
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Audio File (.wav, .mp3) │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ OPTIONAL: Source Separation (for full mixes) │ │ (Demucs/Spleeter model) │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ Preprocessing & Trimming │ │ - Resampling to 44.1kHz │ │ - User-defined trim points │ │ - Normalization │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ Feature Extraction │ │ - Mel Spectrograms │ │ - MFCCs (optional) │ │ - Onset Strength Envelope │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ STAGE 1: Onset Detection │ │ - Detect timestamps of drum hits │ │ - Baseline: librosa/madmom │ │ - ML: CNN-based onset detector │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ STAGE 2: Drum Classification │ │ - Classify each onset as kick/snare/hat/tom/cymbal │ │ - Model: CNN or CRNN │ │ - Input: Audio frames around onset (±50ms window) │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ STAGE 3: Sticking Prediction │ │ - Assign L/R/K to each hit │ │ - Kick detection (always K) │ │ - Rule-based: Alternating pattern, rudiments │ │ - ML-based: LSTM/Transformer with context │ │ - Generate multiple hypotheses with confidence │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ Post-Processing │ │ - Quantization to musical grid (optional) │ │ - Duration estimation │ │ - Dynamics/velocity mapping │ 
└─────────────────────────────────────────────────────────────────┘ 
↓ 
┌─────────────────────────────────────────────────────────────────┐ 
│ OUTPUT GENERATION │ │ - Primary sticking + alternatives │ │ - Text notation (RlKKRllrrL) │ │ - MusicXML export │ │ - MIDI export │ │ - Visualization │ 
└─────────────────────────────────────────────────────────────────┘

### Component Details

#### 1. Preprocessing Pipeline
**Purpose**: Prepare audio for analysis

**Inputs**: Raw audio file
**Outputs**: Normalized, trimmed, resampled audio

**Key Operations**:
- Load audio with torchaudio
- Optional source separation for full mixes
- User-defined trimming (start/end times)
- Resample to consistent sample rate (44.1kHz)
- Normalize audio levels

**Libraries**: torchaudio, demucs/spleeter

---

#### 2. Feature Extraction
**Purpose**: Convert audio to ML-friendly representations

**Features to Extract**:
- **Mel Spectrogram**: Time-frequency representation
  - Window size: 2048 samples (~46ms at 44.1kHz)
  - Hop length: 512 samples (~11ms)
  - Mel bins: 128
- **MFCC**: Compact spectral representation (optional)
- **Onset Strength**: Spectral flux for onset detection

**Libraries**: torchaudio.transforms, librosa

---

#### 3. Onset Detection
**Purpose**: Identify timestamps when drum hits occur

**Approach Options**:
- **Baseline**: Use librosa.onset.onset_detect() or madmom
  - Fast, no training needed
  - Good starting point
- **ML-based**: CNN trained on onset/non-onset frames
  - Input: Mel spectrogram frames
  - Output: Binary classification (onset vs. no onset)
  - Can be more accurate with training

**Evaluation**: Precision, Recall, F1 (with tolerance window ±50ms)

---

#### 4. Drum Classification
**Purpose**: Classify each onset as specific drum type

**Classes**:
- Kick drum (bass drum)
- Snare drum
- Hi-hat (closed)
- Hi-hat (open) - optional
- Tom (high/mid/low) - can merge or separate
- Crash cymbal
- Ride cymbal

**Model Architecture** (suggested):
Input: Mel spectrogram window (±50ms around onset) Shape: [1, 128, ~10 frames]

CNN Feature Extractor:

    Conv2D(1, 32, kernel=3x3) + ReLU + MaxPool
    Conv2D(32, 64, kernel=3x3) + ReLU + MaxPool
    Conv2D(64, 128, kernel=3x3) + ReLU + MaxPool
    Flatten

Classifier Head:

    Linear(128 * features, 256) + ReLU + Dropout(0.5)
    Linear(256, num_classes)
    Softmax

Output: Probability distribution over drum classes

**Alternative**: Use pretrained audio models (PANNs, YAMNet) and fine-tune

**Loss**: Cross-entropy
**Evaluation**: Accuracy, Per-class F1, Confusion matrix

---

#### 5. Sticking Prediction
**Purpose**: Assign L (left), R (right), or K (kick) to each hit

**Challenge**: Audio alone doesn't uniquely determine sticking!

**Approach - Hybrid System**:

**Part A - Rule-Based (Baseline)**:

Below is a mock function demonstrating how the system could predict the sticking:  
```python
def predict_sticking_rules(onsets, drum_types):
    sticking = []
    current_hand = 'R'  # Start with right (configurable)
    
    for drum in drum_types:
        if drum == 'kick':
            sticking.append('K')
        elif drum in ['hi-hat-closed', 'ride']:
            # Cymbals often alternate
            sticking.append(current_hand)
            current_hand = 'L' if current_hand == 'R' else 'R'
        elif drum == 'snare':
            # Default alternating, but check for doubles
            sticking.append(current_hand)
            # Could detect doubles based on timing
        else:
            sticking.append(current_hand)
            current_hand = 'L' if current_hand == 'R' else 'R'
    
    return sticking
```

**Part B - ML-Based (If ground truth available\*):**
###### \*ground truth = definitive sticking pattern of a drum pattern in an audio clip verified by a human

Input: Sequence of (drum_type, velocity, time_since_last, position_in_bar)
Model: LSTM or Transformer
Output: Sequence of L/R/K predictions

Architecture:
  - Embedding layer for drum types
  - Concatenate with numerical features (velocity, timing)
  - Bidirectional LSTM (hidden_size=128)
  - Linear classifier → L/R/K

**Part C - Multiple Hypotheses: Use beam search to maintain top-k sticking sequences:**

````json
{
    "primary": {
        "sticking": "RlKRLKrlRL",
        "confidence": 0.85,
        "pattern": "Standard alternating"
    },
    "alternatives": [
        {
            "sticking": "RrKRLKrlRL",
            "confidence": 0.72,
            "pattern": "Double stroke on beat 2"
        },
        {
            "sticking": "RlKRRKllRL",
            "confidence": 0.65,
            "pattern": "Inverted diddle pattern"
        }
    ]
}
````

## Technical Architecture

### Overall Pipeline

#### 9. Desktop User Interface
**Purpose**: Provide user-friendly desktop application for transcription workflow

**Features**:
- Audio file upload and playback
- Audio trimming controls (visual waveform editor)
- Processing settings (source separation toggle, model selection)
- Real-time progress indication
- Results display (primary + alternative stickings)
- Interactive sticking selection
- Export options (MusicXML, MIDI, text)
- Visualization of results (spectrogram + notation overlay)

**Technology**: PyQt6 (or PySide6 for LGPL licensing)

**Architecture**:

┌─────────────────────────────────────────────────────────────────┐ 
│ Main Application Window │ 
├─────────────────────────────────────────────────────────────────┤ 
│ Menu Bar: File | Edit | View | Help │ 
├──────────────────┬──────────────────────────────────────────────┤ 
│ │ │ │ Control Panel │ Main Display Area │ │ │ │ │ [Upload Audio] │ 
┌────────────────────────────────────────┐ 
│ │ [Play/Pause] │ │ Waveform Visualization │ │ │ │ │ (with trim markers) │ │ │ Trim Controls: │ 
└────────────────────────────────────────┘ 
│ │ Start: [00:00] │ │ │ End: [00:10] │ 
┌────────────────────────────────────────┐ 
│ │ │ │ Spectrogram (optional) │ │ │ [✓] Full Mix │ 
└────────────────────────────────────────┘ 
│ │ (Source Sep.) │ │ │ │ Results: │ │ [Transcribe] │ Primary: R l K R L K r l R L (85%) │ │ │ │ │ │ Alternatives: │ │ │ • R r K R L K r l R L (72%) [Select] │ │ │ • R l K R R K l l R L (65%) [Select] │ │ │ │ │ Export: │ 
┌────────────────────────────────────────┐ 
│ │ [MusicXML] │ │ Drum Notation Preview │ │ │ [MIDI] │ │ (rendered score) │ │ │ [Text] │ 
└────────────────────────────────────────┘ 
│ │ │ │ 
└──────────────────┴──────────────────────────────────────────────┘ 
│ Status Bar: Ready | Processing: 45% | Last export: 2 min ago │ 
└─────────────────────────────────────────────────────────────────┘