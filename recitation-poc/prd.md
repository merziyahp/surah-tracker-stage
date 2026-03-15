# Quran Recitation Practice Aid
## Product Requirements & Decision Log
**Version 2.0 — March 2026**

| Field | Value |
|-------|-------|
| Product | Quran Recitation Practice Aid |
| Version | 2.0 (POC phase — pre-build) |
| Parent project | Surah Mission Control |
| Status | Research / POC in progress |
| Author | Private |
| Last updated | March 2026 |

---

## 1. What this document is

This document replaces the original Recitation Practice Aid PRD (v1.0). It incorporates all decisions and framing shifts made during the design session in March 2026. Anyone picking this project up — including a future LLM coding session — should read this document first. The original PRD is preserved for reference but this version is authoritative.

This is not just a product spec. It is also a decision log. Every section that reflects a deliberate choice explains the reasoning and what was ruled out.

---

## 2. Product goal

Help children practice Quran memorization between teacher sessions. For a selected surah, the system should tell a child and parent whether the child recited all the words, and flag anything that was dropped, skipped, or unclear — in a way that is encouraging, not discouraging.

This is not a replacement for a teacher. It is a practice aid.

### 2.1 What success looks like in V1

- Child records a recitation of a short surah
- System reliably detects whether all ayahs were covered
- System flags specific words or segments that appear missing or unclear
- Feedback is child-friendly and encourages another attempt
- Parent sees enough detail to know where to focus the next practice session

### 2.2 Scope — last 36 surahs only

V1 covers surahs 79–114 only. These are the surahs most commonly memorized first in traditional hifz programs. The POC focuses on the three shortest: Al-Ikhlas (112), Al-Kawthar (108), and Al-Asr (103).

---

## 3. Core architecture decision

This is the most important section. The original PRD described an open transcription pipeline — record audio, send to ASR, get a transcript, compare to expected text. This framing was revised during the design session.

### 3.1 What was ruled out: open transcription

Open transcription asks the model: "what did this person say?" For general speech this works well. For Quranic Arabic recited by a child, it fails for two compounding reasons:

- Arabic ASR models are trained predominantly on adult, Modern Standard Arabic speech. Quranic Arabic has distinct phonology. Child speech has different acoustic properties. The intersection — child + Quranic — has essentially no dedicated training data.
- Even if transcription were accurate, comparing free-form transcript output to expected text is fragile. Small transcription errors cascade into false "skipped word" signals that erode parent trust.

### 3.2 What was also ruled out: direct acoustic comparison

A second approach considered was comparing the child's audio directly against a reference recording of an adult reciting the same surah. This was ruled out because:

- Child voice and adult voice differ fundamentally in pitch, tempo, and articulation. Direct acoustic matching across that gap is not reliable.
- The reference recording cannot tell you if the child skipped an ayah. Only the text layer can do that — because the text is the only thing that knows what should have been said.

> **Decision:** reference audio is retained as a UX element (parents and children can listen to the correct recitation for comparison) but it is not a detection mechanism.

### 3.3 What was decided: constrained matching

The correct framing is a constrained matching problem, not a transcription problem. The pipeline is:

- The child selects a known surah before recording
- The system already has the exact expected Arabic text for that surah
- ASR runs on the child's audio, constrained to that specific text — not open transcription
- The system checks which words from the expected text were accounted for
- Gaps and low-confidence segments are flagged for parent review

The constraint is the most important lever for reliability. The model is not asked "what did you hear?" — it is asked "given that the child was supposed to say these specific words, which ones can you detect?" This is a much narrower and more reliable task.

### 3.4 What the text layer is responsible for

The known Arabic text of each surah is the ground truth and does the primary work:

- Defines what words should have been said
- Provides the constraint for ASR matching
- Determines what counts as missing, skipped, or substituted
- Later: provides word-level targets for Tajweed gap detection

The reference audio is not load-bearing for detection. The text is.

---

## 4. Pipeline

The V1 pipeline has five stages. Stages 1–3 are mechanical. Stage 4 is where the core technical risk lives. Stage 5 is where product quality is determined.

| Stage | What it does | Risk |
|-------|-------------|------|
| 1. Audio capture | Child records on iPad via browser mic or uploaded file | Low |
| 2. Preprocessing | Normalize volume, trim silence, check minimum quality threshold | Low |
| 3. Quality gate | If audio is too short, too faint, or too noisy — prompt re-record before processing | Low |
| 4. Constrained ASR | Run speech recognition against the known surah text | **High** |
| 5. Feedback generation | Convert detection results into child-friendly output and parent detail | Medium |

> **Note:** Stage 4 is the only stage that cannot be designed around. Everything else is engineering. Stage 4 depends on how well available models handle child Quranic speech — which is what the POC is testing.

---

## 5. POC status and test plan

Before any product is built, a proof-of-concept must answer one question:

> *Can any available model reliably detect whether a child said all the words in Al-Ikhlas?*

If yes with reasonable reliability — proceed. If no — the pipeline needs a different approach before building anything.

### 5.1 POC test script

Script: `test_recitation.py` in this folder. Runs three passes on the same recording.

| Pass | Model | API key needed? | What it tests |
|------|-------|-----------------|---------------|
| A | OpenAI Whisper (no prompt) | Yes — OpenAI | Baseline: generic Arabic ASR cold |
| B | OpenAI Whisper (prompted with surah text) | Yes — OpenAI | Effect of text constraint on accuracy |
| C | tarteel-ai/whisper-base-ar-quran | No — runs locally | Quran-tuned model on child voice |

Pass C downloads ~290MB on first run, cached after that. All three passes output a word coverage percentage and list any missing words.

### 5.2 How to interpret POC results

| Coverage | Interpretation | Next step |
|----------|---------------|-----------|
| 80%+ | Strong signal. Constrained matching is viable. | Test deliberately skipped ayah. If it shows as missing — the detection mechanic works. |
| 50–80% | Partial signal. Some reliability but not enough to build on. | Try a cleaner recording. Compare which pass scored higher. |
| Under 50% | Model is struggling with this child's voice. | Check audio quality first. If fine, the child-speech gap is a real blocker. |

### 5.3 The most important follow-up test

Record a version where the child deliberately skips one ayah. Run the script again. If that ayah's words appear in the "missing" list — the core detection mechanic works and the project can move to building a UI.

---

## 6. Model landscape

All available Quran ASR models were trained primarily on adult male reciters. This is a known gap in the field. The POC is the only way to determine if any of these models degrade gracefully on child speech or fail entirely.

| Model | Type | Notes |
|-------|------|-------|
| openai/whisper-1 | API (paid) | General Arabic. Broad training data may help with child speech. |
| tarteel-ai/whisper-base-ar-quran | Local (free) | Quran-tuned. 5.75% WER on adult test set. Child speech performance unknown. |
| tarteel-ai/whisper-tiny-ar-quran | Local (free) | Smaller/faster. Worth comparing if base model is too slow. |
| openai/whisper-large-v3 | API (paid) | Largest general Whisper. ~$0.03/min. May handle edge cases better. |

> **Note:** Tarteel AI does not offer a public API. Their technology is proprietary. The HuggingFace models above are open-source models trained on Tarteel's published dataset, not Tarteel's production system.

---

## 7. What reference audio is and is not for

The original PRD gave reference audio a detection role. This was revised.

**Reference audio has two legitimate uses in V1:**

- **Playback UX** — the child and parent can listen to a correct recitation to compare. This is valuable and should be included.
- **Duration sanity check (weak signal only)** — if a surah typically takes 25 seconds and the recording is 8 seconds, something was clearly skipped. This is a blunt heuristic, not reliable detection.

**Reference audio does not** reliably detect dropped ayahs or skipped words. That responsibility belongs entirely to the text layer combined with constrained ASR. Do not build detection logic that depends on acoustic comparison between child and adult audio.

---

## 8. Scoring and feedback philosophy

The system may calculate detailed internal scores, but user-facing output must stay human and supportive. Do not show percentages, grades, or pass/fail labels to the child.

### 8.1 Hard issues (affect main result)

- Missing ayah
- Missing word
- Added word not in the surah
- Substituted word
- Stopping before the surah is complete

### 8.2 Soft issues (flag for review, do not penalize heavily)

- Unclear pronunciation
- Possible articulation issue
- Long pause or hesitation
- Low audio quality
- Segment too noisy to assess confidently

### 8.3 Output language

| Instead of this | Use this |
|-----------------|----------|
| 82% | "You remembered the whole surah." |
| 3.5 / 5 | "Great effort. Let's practice these small parts." |
| Failed | "Nice try. Let's listen and try again." |
| Word error rate: 3 | "A few words to check — listen here." |

---

## 9. Open questions

Unresolved as of March 2026. Should be answered before V1 is built, not during.

| Question | Why it matters |
|----------|---------------|
| Does constrained Whisper reliably detect dropped ayahs on this child's voice? | The entire pipeline depends on this. Only the POC can answer it. |
| Full-surah recording only, or ayah-by-ayah mode? | Ayah-by-ayah is more forgiving of segmentation issues but changes the UX significantly. |
| What minimum audio quality should trigger a re-record prompt? | Too sensitive = frustrating. Too lenient = garbage in, garbage out. |
| How should parent prompting in the background be handled? | A parent whispering the next word will confuse the model. Needs a mitigation. |
| Browser recording, file upload, or both? | Browser recording is simpler UX but has quality/permission issues on some devices. |

---

## 10. Out of scope for V1

- Full Tajweed grading
- Phoneme-level pronunciation diagnosis
- Open-ended Arabic speech understanding
- More than 36 surahs
- Multi-child support
- Cloud storage of recordings
- Integration with Surah Mission Control data (separate product, may connect later)

---

## 11. Relationship to Surah Mission Control

Surah Mission Control is a memorization tracker. This product is a recitation practice aid. They are related but separate.

| | Surah Mission Control | Recitation Practice Aid |
|--|----------------------|------------------------|
| Purpose | Track memorization progress | Practice recitation between sessions |
| Primary user | Child + parent | Child (parent reviews results) |
| Tech stack | Single HTML file, localStorage | Python pipeline, ASR APIs |
| Data | Device-local only | Audio files, transcripts (TBD) |
| Status | Live, has users | POC phase |
| Repo | surah-tracker / surah-tracker-staging | recitation-poc/ in staging |

These may eventually connect — for example, a recitation result could update the Re-test dots on a Mission Control card. That integration is not in scope for V1 of either product.

---

## 12. Immediate next steps

1. Record the child reciting Al-Ikhlas on the iPad (Voice Memos, quiet room)
2. AirDrop to computer, run `test_recitation.py` with the recording
3. Read the coverage output for all three passes
4. Record a second version where the child deliberately skips ayah 3
5. Run the same script — confirm whether the missing ayah is detected
6. If detection works: begin designing the child-facing recording UI
7. If detection fails: evaluate whisper-large-v3 and assess whether the child-speech gap is a blocker

---

*Quran Recitation Practice Aid — PRD v2.0 — March 2026*
