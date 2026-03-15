# Recitation POC

Tests whether ASR models can detect word coverage when a child recites a surah.

## What this tests

| Pass | Model | API key? | What it tells you |
|------|-------|----------|-------------------|
| A | OpenAI Whisper, no prompt | Yes — OpenAI | Baseline: generic Arabic ASR cold |
| B | OpenAI Whisper, prompted | Yes — OpenAI | Whether constraining to known text helps |
| C | tarteel-ai/whisper-base-ar-quran | No — runs locally | Quran-tuned model on the child's voice |

Pass C downloads ~290MB on first run and caches it. No ongoing cost.

Note: all models were trained primarily on adult reciters. Whether they handle
child speech well enough is exactly what this POC is testing.

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

Note: torch can be large (~2GB). If you only want Pass C, this is all you need.

### 2. OpenAI API key (for Passes A & B only)

Sign up at https://platform.openai.com and create a key.
Cost: ~$0.006/min of audio. A full run costs under $0.01.

```bash
export OPENAI_API_KEY=your_key_here   # Mac/Linux
set OPENAI_API_KEY=your_key_here      # Windows
```

Skip Passes A & B entirely with --skip-openai if you have no key yet.

### 3. Get a recording

Record the child reciting Al-Ikhlas on the iPad (Voice Memos app).
AirDrop to your computer. Supported: m4a, mp3, wav, webm.

## Run the test

```bash
# All three passes
python test_recitation.py --audio recording.m4a --surah ikhlas

# Pass C only — no API key needed
python test_recitation.py --audio recording.m4a --surah ikhlas --skip-openai
```

Available surahs: ikhlas, kawthar, asr

## Interpreting results

| Coverage | Meaning |
|----------|---------|
| 80%+     | Strong signal — model is usable as the detection layer |
| 50-80%   | Partial — try a cleaner recording, compare passes |
| Under 50% | Struggling — check audio quality first |

## The most important follow-up test

Once you have a baseline, record a version where the child deliberately skips
one ayah. Run the script again. If that ayah appears in "Missing words",
the core detection mechanic works.

## Adding more surahs

Edit the SURAHS dict at the top of test_recitation.py.
Each entry needs a name and a list of ayahs as Arabic strings.
