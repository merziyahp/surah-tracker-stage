# Recitation POC

Tests whether AI models can assess a child's Quran recitation against expected text.

## What this includes

| File | What it is |
|------|-----------|
| `test_recitation.py` | Python test script — runs recordings through ASR and Gemini |
| `recitation-prototype.html` | Phone-friendly web prototype — record and assess in browser |
| `PRD.md` | Decision log and product requirements |

---

## Python test script

### Passes

| Pass | Model | Key needed | Notes |
|------|-------|------------|-------|
| A | OpenAI Whisper, no prompt | Yes — OpenAI | Baseline |
| B | OpenAI Whisper, prompted | Yes — OpenAI | Constrained transcription |
| C | tarteel-ai/whisper-base-ar-quran | No — local | Quran-tuned, fails on child speech |
| D | Gemini 2.5 Flash | Yes — Gemini | **Recommended — most reliable** |

Pass C downloads ~290MB on first run and caches it.
Passes A & B are currently blocked by OpenAI project permissions.
Pass D is the one that works.

### Setup

**Install dependencies:**
```bash
pip3 install -r requirements.txt
```

**Set your Gemini API key** (get one free at aistudio.google.com/apikey):
```bash
export GEMINI_API_KEY=your_key_here      # Mac/Linux
set GEMINI_API_KEY=your_key_here         # Windows
```

To make it permanent across terminal sessions, add it to your shell profile:
```bash
echo 'export GEMINI_API_KEY=your_key_here' >> ~/.zshrc
source ~/.zshrc
```

**Set your OpenAI key** (for Passes A & B, optional):
```bash
export OPENAI_API_KEY=your_key_here      # Mac/Linux
set OPENAI_API_KEY=your_key_here         # Windows
```

Note: `export` only lasts for the current terminal session unless added to `~/.zshrc`.

### Run the script

```bash
# Gemini only (recommended)
python3 test_recitation.py --audio sample_recordings/ikhlas.mp3 --surah ikhlas --skip-openai --skip-tarteel

# Gemini + Tarteel comparison
python3 test_recitation.py --audio sample_recordings/ikhlas.mp3 --surah ikhlas --skip-openai

# All passes
python3 test_recitation.py --audio sample_recordings/ikhlas.mp3 --surah ikhlas
```

### Available surahs

| Key | Surah |
|-----|-------|
| `fatiha` | Al-Fatiha (1) |
| `asr` | Al-Asr (103) |
| `humaza` | Al-Humaza (104) |
| `fil` | Al-Fil (105) |
| `quraysh` | Quraysh (106) |
| `maun` | Al-Maun (107) |
| `kawthar` | Al-Kawthar (108) |
| `kafirun` | Al-Kafirun (109) |
| `nasr` | Al-Nasr (110) |
| `masad` | Al-Masad (111) |
| `ikhlas` | Al-Ikhlas (112) |
| `falaq` | Al-Falaq (113) |
| `nas` | Al-Nas (114) |

---

## Web prototype

A single HTML file that records audio in the browser and sends it to Gemini.
Designed to run on iPhone Safari for demos and live testing.

### Setup

**1. Add your Gemini API key**

Open `recitation-prototype.html` in any text editor, find this line near the top:
```
const GEMINI_API_KEY = 'PASTE_YOUR_GEMINI_API_KEY_HERE';
```
Replace with your actual key and save.

**2. Host it — option A: local server on Mac (quick test)**

```bash
cd /path/to/recitation-poc
python3 -m http.server 8080
```

Then open in your browser:
```
http://localhost:8080/recitation-prototype.html
```

To open on your iPhone over the same WiFi — find your Mac's local IP address first:
- System Settings → Wi-Fi → click your network name → IP address (e.g. 192.168.1.42)

Then on your iPhone open Safari and go to:
```
http://192.168.1.42:8080/recitation-prototype.html
```

**3. Host it — option B: GitHub Pages (shareable URL for demos)**

1. Create a new GitHub repo (e.g. `recitation-prototype`)
2. Upload `recitation-prototype.html` renamed to `index.html`
3. Go to Settings → Pages → set source to main branch
4. Open the generated URL in Safari on your iPhone
5. Tap Share → Add to Home Screen for the full app feel

Note: the prototype will **not** work when opened directly as a file or inside Claude —
it must be hosted (local server or GitHub Pages) to access the microphone.

---

## Findings summary

See `PRD.md` for the full decision log. Short version:

- **Pass C (local Quran model)** failed on child speech across all surahs — hallucinates
- **Pass D (Gemini)** correctly assessed all recordings tested including fast recitation, missing Bismillah, dropped words mid-ayah, skipped full ayahs, and word substitutions
- Audio compression matters — AirDrop directly rather than uploading via Google Drive
- Gemini flags long pauses, out-of-order recitation, and Tajweed errors spontaneously
- Some non-determinism observed on subtle errors — same recording can give slightly different results across runs
