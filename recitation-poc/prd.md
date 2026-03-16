# Quran Recitation Practice Aid
## Product Requirements & Decision Log
**Version 3.1 — March 2026**

| Field | Value |
|-------|-------|
| Product | Quran Recitation Practice Aid |
| Version | 3.1 (POC complete — ready to build) |
| Parent project | Surah Mission Control |
| Status | POC complete. Architecture decided. Ready to build V1. |
| Author | Private |
| Last updated | March 2026 |

---

## 1. What this document is

This is the third iteration of the Recitation Practice Aid PRD. Version 2.0 captured the architectural framing decisions made in the first design session. This version (3.0) updates the document with findings from the POC session conducted in March 2026, where the system was tested against real child recordings for the first time.

Sections 3, 4, 5, 6, 9, and 12 have changed significantly. Everything else carries forward from v2.0.

This is not just a product spec. It is a decision log. Every section that reflects a deliberate choice explains the reasoning and what was ruled out.

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

V1 covers surahs 79–114 only. These are the surahs most commonly memorized first in traditional hifz programs. The POC tested three: Al-Ikhlas (112), Al-Kawthar (108), and Al-Asr (103).

---

## 3. Core architecture decision

> **Updated in v3.0 based on POC results.**

### 3.1 What was ruled out: dedicated Quran ASR models

The POC tested `tarteel-ai/whisper-base-ar-quran`, a Whisper model fine-tuned specifically on Quranic recitation data. Despite being purpose-built for this task, it failed on child speech across all three surahs:

- Al-Ikhlas: gibberish for ayahs 1–2, 31.6% word coverage
- Al-Kawthar: garbled nearly every word, 42.9% coverage
- Al-Asr: hallucinated the first two ayahs, 55.6% coverage

The root cause: all available Quran ASR models were trained on adult male reciters. Child speech has fundamentally different acoustic properties. The model fails silently — producing plausible-sounding Arabic that bears no relation to what the child said. Silent failure is the worst possible outcome for this product because it generates false feedback that misleads parents.

### 3.2 What was ruled out: raw transcription + text matching

Even with accurate transcription, comparing free-form output to expected text word-by-word is fragile. Small transcription errors cascade into false "missing word" signals. The matching layer has no intelligence to recognise that `وَانْهَهُ` and `وَانْحَرْ` are the same word with a garbled consonant.

### 3.3 What was ruled out: forced alignment

Timing-based alignment against a reference recording was considered and ruled out. Children pause unpredictably, stretch words for emphasis, hesitate before difficult ayahs, and sometimes restart. Any timing-based approach breaks on real child recitations.

### 3.4 What was decided: Gemini as a reasoning layer

The correct architecture is to send both the audio and the expected Arabic text to Gemini together and ask it to assess whether the child covered the expected content.

This is not transcription followed by matching. It is a single comprehension task: "here is what the child should have said, here is what you heard — assess coverage."

Gemini handles this reliably because:

- It was trained on vastly more diverse audio than any Quran-specific model, including children's voices across many languages
- It uses the expected text as a reasoning constraint, not a post-processing comparison — even if it mishears a word, it can reason "this sounds like what should be here"
- It produces structured qualitative output (Complete / Partial / Missing per ayah) directly usable for feedback generation

### 3.5 Why Gemini outperformed a Quran-trained model

A model trained specifically on Quranic recitation performed worse than a general-purpose LLM on child Quranic speech. Specialisation on a narrow distribution (adult male reciters) creates brittleness outside that distribution. Gemini's breadth of training means it degrades gracefully on unusual inputs rather than hallucinating.

The lesson: do not assume domain-specific models are better for this use case. Test on actual child recordings before committing to any model.

---

## 4. Pipeline

> **Updated in v3.0. Stage 4 has changed.**

| Stage | What it does | Risk |
|-------|-------------|------|
| 1. Audio capture | Child records on iPad via browser mic | Low |
| 2. Preprocessing | Normalize volume, trim silence, check quality threshold | Low |
| 3. Quality gate | If audio is too short, faint, or noisy — prompt re-record | Low |
| 4. Gemini assessment | Send audio + expected surah text to Gemini. Assess ayah coverage and flag missing or partial words. | **Medium** (was High) |
| 5. Feedback generation | Convert Gemini's structured output into child-friendly feedback and parent detail | Medium |

Stage 4 risk is now Medium rather than High. The POC demonstrated Gemini handles child Quranic speech reliably across multiple surahs and recording conditions. Remaining risks are API cost, latency, and untested edge cases.

---

## 5. POC results

> **New section in v3.0.**

The POC ran four passes on real child recordings of Al-Ikhlas, Al-Kawthar, and Al-Asr.

| Pass | Model | Outcome |
|------|-------|---------|
| A | OpenAI Whisper (no prompt) | Not tested — OpenAI project permissions blocked access |
| B | OpenAI Whisper (prompted) | Not tested — same blocker |
| C | tarteel-ai/whisper-base-ar-quran | Tested. Failed on all three surahs. |
| D | Gemini 2.5 Flash | Tested. Passed on all recordings tested. |

### 5.1 Pass C results (Quran-tuned model — failed)

| Surah | Coverage | Notes |
|-------|----------|-------|
| Al-Ikhlas | 31.6% | Complete gibberish for ayahs 1–2. Ayahs 3–4 partially detected. |
| Al-Kawthar | 42.9% uncompressed | Heard something but garbled nearly every word. |
| Al-Asr | 55.6% | Best result but hallucinated first two ayahs. |

**Conclusion:** Pass C is not viable. Dropped from the product architecture.

### 5.2 Pass D results (Gemini — passed)

| Recording | Gemini verdict | Correct? |
|-----------|---------------|----------|
| Al-Kawthar, uncompressed | All 4 ayahs Complete, no missing words | ✓ |
| Al-Ikhlas, no Bismillah | Bismillah Missing, ayahs 1–4 Complete | ✓ |
| Al-Asr, clean | All 4 ayahs Complete, no missing words | ✓ |
| Al-Ikhlas, fast recitation | Ayahs 1–4 Complete, ayah 5 Partial — 3 specific missing words flagged | ✓ |
| Al-Asr, prompted mid-recitation | All 4 ayahs Complete — Gemini noted long pause mid-ayah 4 | ✓ |
| Al-Kawthar, fast + out-of-order Bismillah | Ayahs 2–4 Complete, Bismillah Partial — flagged out of sequence | ✓ |
| Al-Kafirun, skipped ayah 6 | Ayah 6 Missing, all others Complete — exact skipped text quoted | ✓ |
| Al-Maun, multiple issues | Bismillah Missing, ayah 2 substitution caught, ayahs 6–7 Partial with specific missing words | ✓ |
| Al-Humaza, run 1 | 8 Complete, 2 Partial — caught `مُوقَدَةُ`→`مُوَصَدَةُ` substitution missed | △ partial |
| Al-Humaza, run 2 (same audio) | 6 Complete, 3 Partial — caught substitution + missing shadda + missing suffix | ✓ better |

Gemini correctly handled: complete recitation, missing Bismillah, fast recitation with dropped words, long pauses, out-of-order recitation, deliberately skipped ayahs, word substitutions, and partial word omissions. On longer surahs with subtle errors, results showed some non-determinism between runs.

### 5.3 Emerging result taxonomy

The POC revealed that Gemini naturally distinguishes between more recitation states than the original design anticipated. These should be reflected in the product's feedback model:

| State | Example | Severity |
|-------|---------|----------|
| Complete, in order | Normal correct recitation | None — praise |
| Complete, with pause | Child hesitated mid-ayah, needed prompting | Soft — flag for parent |
| Complete, out of order | Bismillah said at end instead of start | Soft — note sequence |
| Complete, with substitution | `يَحْسَبُ` recited as `أَيَحْسَبُ` — intent clear but word altered | Soft — note for teacher |
| Partial | Specific words missing within an ayah | Hard — flag for practice |
| Missing | Full ayah not recited | Hard — flag for practice |
| Tajweed error | `مُوقَدَةُ` recited as `مُوَصَدَةُ` — wrong word entirely | Hard — flag for teacher |

The long pause finding is particularly valuable: it surfaces cases where a child was prompted mid-recitation — something a word-coverage check alone would never catch. This should be included in the parent-facing detail even in V1.

Gemini also spontaneously identifies Tajweed errors without being prompted — e.g. flagging `ض` pronounced as `د`, or a missing shadda. This is layer 2 emerging from layer 1 without additional engineering. These should be captured and surfaced to parents as "check with your teacher" items, not penalised in the main score.

### 5.4 POC gates — status

| Gate | Status |
|------|--------|
| Does Gemini correctly assess a complete recitation? | ✓ Passed — multiple surahs |
| Does Gemini catch a missing Bismillah? | ✓ Passed |
| Does Gemini catch dropped words mid-ayah? | ✓ Passed |
| Does Gemini catch a deliberately skipped full ayah? | ✓ Passed — Al-Kafirun ayah 6 |
| Does Gemini handle longer surahs (8–10 ayahs)? | ✓ Passed — Al-Humaza, Al-Maun |
| Is Gemini consistent across multiple runs on same audio? | △ Partial — subtle errors show non-determinism |

All core POC gates are passed. The POC is complete.

### 5.5 Non-determinism finding

Running the same Al-Humaza recording twice produced different results:

- **Run 1** — caught the `مُوقَدَةُ`→`مُوَصَدَةُ` substitution in one assessment but not the other
- **Run 2** — caught the substitution plus a missing shadda and a missing suffix

This is expected LLM behaviour — Gemini is probabilistic, not deterministic. Implications for the product:

- Full missing ayahs and complete/missing assessments are likely consistent across runs
- Subtle word-level errors (especially partial word differences, single missing letters) may not be caught every time
- For V1: surface what Gemini finds, but frame uncertain flags as "worth checking" rather than definitive errors
- For V1+: consider running 2–3 passes on the same recording and taking a consensus for higher-confidence results

### 5.6 Scoring decisions

- **Ayah-level only** — the numeric score is calculated from section 2 (AYAH COVERAGE) statuses only. Word-level detail from section 3 informs the qualitative output but does not affect the number.
- **Bismillah excluded** — Bismillah (Ayah 1) is optional. It is noted separately but not counted in the score.
- **Scoring formula** — Complete = 1.0, Partial = 0.5, Missing = 0.0. Score = sum / scorable ayahs × 100.

---

## 6. Model landscape

> **Updated in v3.1.**

| Model | Tested? | Result | Status |
|-------|---------|--------|--------|
| tarteel-ai/whisper-base-ar-quran | Yes | Failed on child speech | Dropped |
| Gemini 2.5 Flash | Yes | Reliable across all tests | **Selected** |
| OpenAI gpt-4o-mini-transcribe | No — access blocked | Unknown | Test if Gemini has cost/latency issues |
| openai/whisper-large-v3 | No | Unknown | Unlikely needed given Gemini results |

**Audio compression note:** Compressed audio (uploaded via Google Drive) scored meaningfully lower than uncompressed (AirDrop). For production, capture audio directly in the browser and send it straight to the API — do not route through file sharing or cloud storage.

**Tarteel AI note:** Tarteel does not offer a public API. The HuggingFace models are open-source models trained on Tarteel's published dataset, not Tarteel's production system.

---

## 7. What reference audio is and is not for

Reference audio has two legitimate uses in V1:

- **Playback UX** — child and parent can listen to a correct recitation to compare. Valuable, should be included.
- **Duration sanity check (weak signal only)** — if a surah takes 25 seconds normally and the recording is 8 seconds, something was clearly skipped. Blunt heuristic only.

Reference audio does not reliably detect dropped ayahs or skipped words. Gemini + the expected text is the detection mechanism.

---

## 8. Scoring and feedback philosophy

The system may calculate detailed internal scores but user-facing output must stay human and supportive. Do not show percentages, grades, or pass/fail labels to the child.

### 8.1 Hard issues (affect main result)

- Missing ayah
- Missing word
- Stopping before the surah is complete

### 8.2 Soft issues (flag for review, do not penalize heavily)

- Partial ayah (some words present, some missing)
- Unclear pronunciation
- Very fast recitation that may have dropped words
- Low audio quality

### 8.3 Output language

| Instead of this | Use this |
|-----------------|----------|
| 82% | "You remembered the whole surah." |
| 3.5 / 5 | "Great effort. Let's practice these small parts." |
| Failed | "Nice try. Let's listen and try again." |
| Word error rate: 3 | "A few words to check — listen here." |
| Ayah 5: Partial | "Almost! Let's go over the last part together." |

---

## 9. Open questions

> **Updated in v3.0. Several v2.0 questions are now answered.**

**Answered by the POC:**
- ~~Does constrained Whisper reliably detect dropped ayahs?~~ → No. Gemini is the approach.
- ~~Which model to use?~~ → Gemini 2.5 Flash.
- ~~Does audio compression matter?~~ → Yes. Capture directly in browser, not via file sharing.
- ~~Does Gemini catch a deliberately skipped full ayah?~~ → Yes, correctly flagged and quoted the missing text.
- ~~Does Gemini work on longer surahs (8–10 ayahs)?~~ → Yes, tested on Al-Humaza and Al-Maun.

**Still open — must answer before V1 build:**

| Question | Why it matters |
|----------|---------------|
| ~~Does Gemini correctly flag a deliberately skipped full ayah?~~ | ✓ Answered — yes, caught and quoted the missing text. |
| How consistent is Gemini across multiple runs on the same recording? | Non-determinism observed on subtle errors. Run 2–3 passes for higher confidence. |
| What is the Gemini API cost per recitation attempt? | Need to model cost before committing to architecture. |
| What is Gemini response latency on a short surah? | If 10+ seconds, UX needs a loading state and expectation setting. |
| Should Bismillah always be expected? | Some children omit it. Currently flagged as missing. Needs a decision. |
| Full-surah recording only, or ayah-by-ayah mode? | Ayah-by-ayah changes UX significantly but may reduce scope per API call. |
| What minimum audio quality triggers a re-record prompt? | Too sensitive = frustrating. Too lenient = garbage in. |
| How should long pauses be surfaced to parents? | POC showed Gemini detects them. Needs a UX decision on how to present this. |
| Browser recording, file upload, or both for V1? | Browser recording is simpler but has quality/permission issues on some devices. |

**Eval framework — tracked separately:**

The POC has produced a small set of recordings with known ground truth. These should be formalised into an eval set before V1 build begins. The goal is to be able to run any prompt change or model change against the full set and immediately see whether things regressed.

The eval set needs at minimum:
- 2–3 complete correct recitations per surah (different speeds, styles)
- 1 recording with a missing Bismillah per surah
- 1 recording with a deliberately skipped full ayah per surah
- 1 recording with partial ayah (words dropped mid-ayah)
- 1 recording with out-of-order content
- 1 noisy or low-quality recording (quality gate test)

The eval script should run all recordings through Pass D, compare Gemini's output against the known ground truth, and report a pass/fail per recording. This creates a regression harness: if a prompt change causes a previously-passing recording to fail, you know immediately.

LLM-as-judge is a viable approach here — use Claude or Gemini to automatically score Gemini's output against ground truth and produce a structured report. The expected outputs are well-defined enough to make automated scoring reliable.

---

## 10. Out of scope for V1

- Full Tajweed grading
- Phoneme-level pronunciation diagnosis
- Open-ended Arabic speech understanding
- More than 36 surahs
- Multi-child support
- Cloud storage of recordings
- Integration with Surah Mission Control data (may connect later)

---

## 11. Relationship to Surah Mission Control

| | Surah Mission Control | Recitation Practice Aid |
|--|----------------------|------------------------|
| Purpose | Track memorization progress | Practice recitation between sessions |
| Primary user | Child + parent | Child (parent reviews results) |
| Tech stack | Single HTML file, localStorage | Gemini API, browser audio capture |
| Data | Device-local only | Audio sent to Gemini API, not stored |
| Status | Live, has users | POC complete, pre-build |
| Repo | surah-tracker / surah-tracker-staging | recitation-poc/ in staging |

These may eventually connect — for example, a recitation result could update the Re-test dots on a Mission Control card. Not in scope for V1 of either product.

---

## 12. Immediate next steps

> **Updated in v3.1.**

1. **Run the skipped-ayah test** — record Kawthar where the child skips ayah 2 entirely. Run Pass D. Confirm Gemini flags it as Missing. This is the last POC gate before building.
2. **Fix the numeric scoring** — rewrite the coverage score parser to extract ayah status from Gemini's structured output properly rather than counting words in the response text.
3. **Measure cost and latency** — run 10 requests against the Gemini API and log response time and token cost per request.
4. **Harden the Gemini prompt** — define an exact output format (structured JSON or consistent markdown) so results can be parsed reliably rather than interpreted from natural language.
5. **Decide on Bismillah handling** — whether to always expect it, make it optional, or exclude it from scoring entirely.
6. **Design the recording UI** — single screen: surah selector, record button, playback before submit, results view. Child-first, large touch targets, Arabic text display.

---

*Quran Recitation Practice Aid — PRD v3.0 — March 2026*
