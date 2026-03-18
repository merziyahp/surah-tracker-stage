"""
Recitation POC — Word Coverage Test
=====================================
Takes a child's audio recording and checks it against
the known Arabic text of a surah using four approaches:

  Pass A — OpenAI Whisper, no prompt (open transcription, baseline)
  Pass B — OpenAI Whisper, prompted with the expected surah text
  Pass C — tarteel-ai/whisper-base-ar-quran (Quran-tuned, runs locally, no API key needed)
  Pass D — Gemini (audio + expected text sent together for direct assessment)

Usage:
  python test_recitation.py --audio your_recording.m4a --surah ikhlas
  python test_recitation.py --audio your_recording.m4a --surah ikhlas --skip-openai
  python test_recitation.py --audio your_recording.m4a --surah ikhlas --skip-openai --skip-gemini

Requirements:
  pip install -r requirements.txt
"""

import argparse
import re
import json
import os
import sys
import traceback

# ---------------------------------------------------------------------------
# Surah text
# Bismillah is included as the first ayah since children recite it before each surah
# ---------------------------------------------------------------------------
BISMILLAH = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ"

# ---------------------------------------------------------------------------
# Model configuration — change these to adjust model behaviour
# ---------------------------------------------------------------------------
MODEL_GEMINI_PRIMARY   = "gemini-2.5-flash"
MODEL_GEMINI_LITE      = "gemini-2.0-flash"
MODEL_CLAUDE           = "claude-haiku-4-5"
TEMPERATURE            = 0.1
TOP_P                  = 0.9

SURAHS = {
    "fatiha": {
        "name": "Al-Fatiha (1)",
        "ayahs": [
            BISMILLAH,
            "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
            "الرَّحْمَنِ الرَّحِيمِ",
            "مَالِكِ يَوْمِ الدِّينِ",
            "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
            "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
            "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
        ],
    },
    "asr": {
        "name": "Al-Asr (103)",
        "ayahs": [
            BISMILLAH,
            "وَالْعَصْرِ",
            "إِنَّ الْإِنسَانَ لَفِي خُسْرٍ",
            "إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ وَتَوَاصَوْا بِالْحَقِّ وَتَوَاصَوْا بِالصَّبْرِ",
        ],
    },
    "humaza": {
        "name": "Al-Humaza (104)",
        "ayahs": [
            BISMILLAH,
            "وَيْلٌ لِّكُلِّ هُمَزَةٍ لُّمَزَةٍ",
            "الَّذِي جَمَعَ مَالًا وَعَدَّدَهُ",
            "يَحْسَبُ أَنَّ مَالَهُ أَخْلَدَهُ",
            "كَلَّا لَيُنبَذَنَّ فِي الْحُطَمَةِ",
            "وَمَا أَدْرَاكَ مَا الْحُطَمَةُ",
            "نَارُ اللَّهِ الْمُوقَدَةُ",
            "الَّتِي تَطَّلِعُ عَلَى الْأَفْئِدَةِ",
            "إِنَّهَا عَلَيْهِم مُّؤْصَدَةٌ",
            "فِي عَمَدٍ مُّمَدَّدَةٍ",
        ],
    },
    "fil": {
        "name": "Al-Fil (105)",
        "ayahs": [
            BISMILLAH,
            "أَلَمْ تَرَ كَيْفَ فَعَلَ رَبُّكَ بِأَصْحَابِ الْفِيلِ",
            "أَلَمْ يَجْعَلْ كَيْدَهُمْ فِي تَضْلِيلٍ",
            "وَأَرْسَلَ عَلَيْهِمْ طَيْرًا أَبَابِيلَ",
            "تَرْمِيهِم بِحِجَارَةٍ مِّن سِجِّيلٍ",
            "فَجَعَلَهُمْ كَعَصْفٍ مَّأْكُولٍ",
        ],
    },
    "quraysh": {
        "name": "Quraysh (106)",
        "ayahs": [
            BISMILLAH,
            "لِإِيلَافِ قُرَيْشٍ",
            "إِيلَافِهِمْ رِحْلَةَ الشِّتَاءِ وَالصَّيْفِ",
            "فَلْيَعْبُدُوا رَبَّ هَذَا الْبَيْتِ",
            "الَّذِي أَطْعَمَهُم مِّن جُوعٍ وَآمَنَهُم مِّنْ خَوْفٍ",
        ],
    },
    "maun": {
        "name": "Al-Maun (107)",
        "ayahs": [
            BISMILLAH,
            "أَرَأَيْتَ الَّذِي يُكَذِّبُ بِالدِّينِ",
            "فَذَلِكَ الَّذِي يَدُعُّ الْيَتِيمَ",
            "وَلَا يَحُضُّ عَلَى طَعَامِ الْمِسْكِينِ",
            "فَوَيْلٌ لِّلْمُصَلِّينَ",
            "الَّذِينَ هُمْ عَن صَلَاتِهِمْ سَاهُونَ",
            "الَّذِينَ هُمْ يُرَاءُونَ",
            "وَيَمْنَعُونَ الْمَاعُونَ",
        ],
    },
    "kawthar": {
        "name": "Al-Kawthar (108)",
        "ayahs": [
            BISMILLAH,
            "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ",
            "فَصَلِّ لِرَبِّكَ وَانْحَرْ",
            "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ",
        ],
    },
    "kafirun": {
        "name": "Al-Kafirun (109)",
        "ayahs": [
            BISMILLAH,
            "قُلْ يَا أَيُّهَا الْكَافِرُونَ",
            "لَا أَعْبُدُ مَا تَعْبُدُونَ",
            "وَلَا أَنتُمْ عَابِدُونَ مَا أَعْبُدُ",
            "وَلَا أَنَا عَابِدٌ مَّا عَبَدتُّمْ",
            "وَلَا أَنتُمْ عَابِدُونَ مَا أَعْبُدُ",
            "لَكُمْ دِينُكُمْ وَلِيَ دِينِ",
        ],
    },
    "nasr": {
        "name": "Al-Nasr (110)",
        "ayahs": [
            BISMILLAH,
            "إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ",
            "وَرَأَيْتَ النَّاسَ يَدْخُلُونَ فِي دِينِ اللَّهِ أَفْوَاجًا",
            "فَسَبِّحْ بِحَمْدِ رَبِّكَ وَاسْتَغْفِرْهُ إِنَّهُ كَانَ تَوَّابًا",
        ],
    },
    "masad": {
        "name": "Al-Masad (111)",
        "ayahs": [
            BISMILLAH,
            "تَبَّتْ يَدَا أَبِي لَهَبٍ وَتَبَّ",
            "مَا أَغْنَى عَنْهُ مَالُهُ وَمَا كَسَبَ",
            "سَيَصْلَى نَارًا ذَاتَ لَهَبٍ",
            "وَامْرَأَتُهُ حَمَّالَةَ الْحَطَبِ",
            "فِي جِيدِهَا حَبْلٌ مِّن مَّسَدٍ",
        ],
    },
    "ikhlas": {
        "name": "Al-Ikhlas (112)",
        "ayahs": [
            BISMILLAH,
            "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "اللَّهُ الصَّمَدُ",
            "لَمْ يَلِدْ وَلَمْ يُولَدْ",
            "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
        ],
    },
    "falaq": {
        "name": "Al-Falaq (113)",
        "ayahs": [
            BISMILLAH,
            "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ",
            "مِن شَرِّ مَا خَلَقَ",
            "وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ",
            "وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ",
            "وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ",
        ],
    },
    "nas": {
        "name": "Al-Nas (114)",
        "ayahs": [
            BISMILLAH,
            "قُلْ أَعُوذُ بِرَبِّ النَّاسِ",
            "مَلِكِ النَّاسِ",
            "إِلَهِ النَّاسِ",
            "مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ",
            "الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ",
            "مِنَ الْجِنَّةِ وَالنَّاسِ",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_full_text(surah):
    return " ".join(surah["ayahs"])


def get_all_words(surah):
    words = []
    for ayah in surah["ayahs"]:
        words.extend(ayah.split())
    return words


def strip_diacritics(text):
    """
    Remove Arabic diacritical marks (tashkeel) before word matching.
    The model and reference text may use different diacritics for the same word.
    Arabic diacritics are Unicode range U+064B to U+065F plus tatweel U+0640.
    """
    return re.sub(r'[\u064b-\u065f\u0640]', '', text)


def fuzzy_match(word, transcript_words, threshold=0.75):
    """
    Check if a word has a close enough match in the transcript.
    Uses character-level similarity to catch garbled versions of words.
    threshold=0.75 means 75% of characters must match.
    """
    if word in transcript_words:
        return True, word, 1.0

    best_score = 0
    best_match = None
    for t_word in transcript_words:
        w_chars = set(word)
        t_chars = set(t_word)
        if not w_chars or not t_chars:
            continue
        overlap = len(w_chars & t_chars)
        score = overlap / max(len(w_chars), len(t_chars))
        if score > best_score:
            best_score = score
            best_match = t_word

    if best_score >= threshold:
        return True, best_match, best_score
    return False, best_match, best_score


def word_coverage(transcript, expected_words):
    transcript_bare = strip_diacritics(transcript)
    transcript_words = set(transcript_bare.split())
    expected_bare = [strip_diacritics(w) for w in expected_words]

    exact_matches = []
    fuzzy_matches = []
    missing_orig = []

    for i, (orig, bare) in enumerate(zip(expected_words, expected_bare)):
        found, matched_word, score = fuzzy_match(bare, transcript_words)
        if found:
            if score == 1.0:
                exact_matches.append(orig)
            else:
                fuzzy_matches.append((orig, matched_word, round(score, 2)))
        else:
            missing_orig.append(orig)

    total_matched = len(exact_matches) + len(fuzzy_matches)

    return {
        "total_expected": len(expected_words),
        "matched": total_matched,
        "exact_matches": len(exact_matches),
        "fuzzy_matches": len(fuzzy_matches),
        "fuzzy_detail": fuzzy_matches,
        "missing_count": len(missing_orig),
        "missing_words": missing_orig,
        "coverage_pct": round(total_matched / len(expected_words) * 100, 1) if expected_words else 0,
    }


def print_section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_coverage(coverage):
    print(f"  Coverage : {coverage['coverage_pct']}%  ({coverage['matched']}/{coverage['total_expected']} words matched)")
    print(f"  Exact    : {coverage['exact_matches']}  |  Fuzzy: {coverage['fuzzy_matches']}")
    if coverage["fuzzy_detail"]:
        print("  Fuzzy matches (expected → heard):")
        for orig, heard, score in coverage["fuzzy_detail"]:
            print(f"    {orig} → {heard}  ({int(score*100)}% match)")
    if coverage["missing_words"]:
        print(f"  Missing  : {' | '.join(coverage['missing_words'])}")
    else:
        print("  Missing  : none — all words accounted for")


# ---------------------------------------------------------------------------
# Pass A & B — OpenAI Whisper via API
# ---------------------------------------------------------------------------

def run_openai_passes(audio_path, surah, expected_words):
    try:
        from openai import OpenAI, APIConnectionError, AuthenticationError, RateLimitError, APIStatusError
    except ImportError:
        print("\n  ERROR — openai package not installed.")
        print("  Fix: pip install openai")
        return None, None

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n  ERROR — OPENAI_API_KEY environment variable is not set.")
        print("  Fix: export OPENAI_API_KEY=your_key_here")
        print("  Get a key at: https://platform.openai.com/api-keys")
        return None, None

    client = OpenAI(api_key=api_key)

    def transcribe(prompt=None, pass_label=""):
        try:
            with open(audio_path, "rb") as f:
                kwargs = {
                    "model": "gpt-4o-mini-transcribe",
                    "file": f,
                    "language": "ar",
                    "response_format": "text",
                }
                if prompt:
                    kwargs["prompt"] = prompt
                result = client.audio.transcriptions.create(**kwargs)
            return result.strip() if isinstance(result, str) else str(result).strip()

        except AuthenticationError:
            print(f"\n  ERROR ({pass_label}) — OpenAI API key is invalid or expired.")
            print("  Fix: check your key at https://platform.openai.com/api-keys")
            return None
        except RateLimitError:
            print(f"\n  ERROR ({pass_label}) — OpenAI rate limit hit or insufficient credits.")
            print("  Fix: check usage at https://platform.openai.com/usage")
            return None
        except APIConnectionError as e:
            print(f"\n  ERROR ({pass_label}) — Could not connect to OpenAI.")
            print(f"  Detail: {e}")
            return None
        except APIStatusError as e:
            print(f"\n  ERROR ({pass_label}) — OpenAI returned an error.")
            print(f"  Status code : {e.status_code}")
            print(f"  Detail      : {e.message}")
            return None
        except FileNotFoundError:
            print(f"\n  ERROR ({pass_label}) — Audio file not found: {audio_path}")
            return None
        except Exception as e:
            print(f"\n  ERROR ({pass_label}) — Unexpected error.")
            print(f"  Detail: {e}")
            traceback.print_exc()
            return None

    print_section("Pass A — OpenAI Whisper (no prompt)")
    print("  Sending to OpenAI Whisper...")
    transcript_a = transcribe(prompt=None, pass_label="Pass A")
    result_a = None
    if transcript_a is not None:
        print(f"\n  Transcript:\n    {transcript_a}")
        coverage_a = word_coverage(transcript_a, expected_words)
        print_coverage(coverage_a)
        result_a = {"transcript": transcript_a, "coverage": coverage_a}
    else:
        print("  Skipping coverage — no transcript returned.")

    print_section("Pass B — OpenAI Whisper (prompted with surah text)")
    print("  Sending to OpenAI Whisper with prompt...")
    transcript_b = transcribe(prompt=get_full_text(surah), pass_label="Pass B")
    result_b = None
    if transcript_b is not None:
        print(f"\n  Transcript:\n    {transcript_b}")
        coverage_b = word_coverage(transcript_b, expected_words)
        print_coverage(coverage_b)
        result_b = {"transcript": transcript_b, "coverage": coverage_b}
    else:
        print("  Skipping coverage — no transcript returned.")

    return result_a, result_b


# ---------------------------------------------------------------------------
# Pass C — tarteel-ai/whisper-base-ar-quran (local, no API key)
# ---------------------------------------------------------------------------

def run_tarteel_pass(audio_path, expected_words):
    print_section("Pass C — tarteel-ai/whisper-base-ar-quran (Quran-tuned, local)")

    missing_packages = []
    for pkg in ["torch", "transformers", "librosa"]:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)

    if missing_packages:
        print(f"\n  ERROR — Missing packages: {', '.join(missing_packages)}")
        print(f"  Fix: pip install {' '.join(missing_packages)}")
        return None

    try:
        import torch
        import librosa
        from transformers import pipeline

        model_id = "tarteel-ai/whisper-base-ar-quran"
        print(f"  Model    : {model_id}")
        print("  Download : ~290MB on first run, cached after that")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Device   : {device}" + (" (GPU)" if device == "cuda" else " (CPU — works fine, just slower)"))

        try:
            asr = pipeline("automatic-speech-recognition", model=model_id, device=device)
        except OSError as e:
            print(f"\n  ERROR — Could not download model from HuggingFace.")
            print(f"  Detail: {e}")
            print("  Fix: check your internet connection.")
            return None
        except RuntimeError as e:
            print(f"\n  ERROR — Model failed to load (possible memory issue).")
            print(f"  Detail: {e}")
            return None
        except Exception as e:
            print(f"\n  ERROR — Unexpected failure loading model.")
            print(f"  Detail: {e}")
            traceback.print_exc()
            return None

        try:
            print(f"\n  Loading audio: {audio_path}")
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        except Exception as e:
            print(f"\n  ERROR — Could not load audio file.")
            print(f"  Detail: {e}")
            print("  Supported formats: m4a, mp3, wav, webm, ogg, flac")
            return None

        print("  Running transcription...")
        try:
            result = asr({"array": audio, "sampling_rate": 16000})
            transcript = result["text"].strip()
        except Exception as e:
            print(f"\n  ERROR — Transcription failed.")
            print(f"  Detail: {e}")
            traceback.print_exc()
            return None

        print(f"\n  Transcript:\n    {transcript}")
        coverage = word_coverage(transcript, expected_words)
        print_coverage(coverage)
        return {"transcript": transcript, "coverage": coverage}

    except Exception as e:
        print(f"\n  ERROR — Unexpected failure in Pass C.")
        print(f"  Detail: {e}")
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# Shared helpers for multimodal passes (D, E, F)
# ---------------------------------------------------------------------------

def _build_prompt(surah, ayah_list, full_text):
    """Shared prompt for all multimodal assessment passes."""
    return f"""You are a warm, experienced Quran teacher giving feedback after a child's recitation practice session.
You are speaking to the parent, with a final note directed at the child.

The child was supposed to recite {surah['name']}.
The expected Arabic text is:

{ayah_list}

Note: Ayah 0 is the Bismillah. It is optional — if the child did not recite it, mark it as Optional rather than Missing and do not treat it as an error.

Listen carefully to the audio recording and provide the following:

1. TRANSCRIPT: What you heard, written in Arabic script. (This section only should be in Arabic.)

2. AYAH COVERAGE: For each ayah, state Complete, Partial, or Missing.
   Use natural teacher language in your notes — e.g. "came through clearly" or "stumbled a little here".

3. WORDS TO WORK ON: Any specific words that were missing, substituted, or unclear — phrased as gentle guidance. E.g. "The word X wasn't quite there — worth drilling this one."

4. FOR THE PARENT: 2-3 sentences as a teacher speaking to a parent after class. What went well, what to focus on at home, any patterns worth noting (hesitations, rushing, prompting needed). Honest but encouraging.

5. FOR THE CHILD: One sentence spoken directly to the child. Warm, specific, and motivating. Reference something they actually did well.

Important: Respond entirely in English except for Arabic Quranic text when quoting specific words or ayahs.

Accuracy guidelines:
- Be strict about whether each word was present or absent. Do not assume a word was said if you did not clearly hear it.
- Be lenient only on natural child speech variations: soft voice, stretched vowels, slight accent.
- Do NOT be lenient on: missing words, substituted words, skipped ayahs, or dropped word endings that change meaning.
- If uncertain whether a word was said, mark it as unclear rather than assuming Complete.

Full expected text for reference: {full_text}"""


def _parse_coverage(assessment, surah):
    """
    Parse AYAH COVERAGE section from Gemini/Claude response.
    Returns (score, complete, partial, missing, bismillah_status).
    Bismillah (Ayah 0) is excluded from scoring.
    """
    import re as _re

    lines = assessment.split("\n")
    ayah_statuses = {}
    in_coverage = False
    for line in lines:
        if "AYAH COVERAGE" in line.upper():
            in_coverage = True
            continue
        if in_coverage:
            if _re.match(r"\s*\*{{0,2}}\s*\d+\.\s+[A-Z]", line) and "Ayah" not in line:
                break
            m = _re.search(r"Ayah\s+(\d+)", line, _re.IGNORECASE)
            if m:
                n = int(m.group(1))
                l = line.lower()
                if "complete" in l:   ayah_statuses[n] = "complete"
                elif "partial" in l:  ayah_statuses[n] = "partial"
                elif "missing" in l:  ayah_statuses[n] = "missing"
                elif "optional" in l or "skipped" in l: ayah_statuses[n] = "optional"

    scoring_statuses = {{n: s for n, s in ayah_statuses.items()
                         if n != 0 and s != "optional"}}
    ayah_count_scored = len(surah["ayahs"]) - 1

    complete = sum(1 for s in scoring_statuses.values() if s == "complete")
    partial  = sum(1 for s in scoring_statuses.values() if s == "partial")
    missing  = sum(1 for s in scoring_statuses.values() if s == "missing")

    # Fallback if section not found
    if complete + partial + missing == 0:
        for line in lines:
            l = line.lower()
            m = _re.search(r"ayah\s+(\d+)", l)
            if m and int(m.group(1)) != 0:
                if "complete" in l: complete += 1
                elif "partial" in l: partial += 1
                elif "missing" in l: missing += 1

    total = complete + partial + missing
    if total > 0:
        score = min(round(((complete * 1.0) + (partial * 0.5)) / ayah_count_scored * 100, 1), 100.0)
    else:
        score = None

    bismillah_status = ayah_statuses.get(0, "not recited")
    return score, complete, partial, missing, bismillah_status


# ---------------------------------------------------------------------------
# Pass D — Gemini (audio + expected text → direct assessment)
# ---------------------------------------------------------------------------

def run_gemini_pass(audio_path, surah, expected_words):
    print_section("Pass D — Gemini (audio + text → direct assessment)")

    try:
        from google import genai
    except ImportError:
        print("\n  ERROR — google-genai package not installed.")
        print("  Fix: pip install google-genai")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n  ERROR — GEMINI_API_KEY environment variable is not set.")
        print("  Fix: export GEMINI_API_KEY=your_key_here")
        print("  Get a free key at: https://aistudio.google.com/apikey")
        return None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"\n  ERROR — Could not create Gemini client.")
        print(f"  Detail: {e}")
        return None

    # Bismillah is Ayah 0, surah ayahs start at 1
    ayah_list = "\n".join(
        f"  Ayah {'0' if i == 0 else i}: {ayah}"
        for i, ayah in enumerate(surah["ayahs"])
    )
    full_text = get_full_text(surah)

    prompt = f"""You are a warm, experienced Quran teacher giving feedback after a child's recitation practice session.
You are speaking to the parent, with a final note directed at the child.

The child was supposed to recite {surah['name']}.
The expected Arabic text is:

{ayah_list}

Note: Ayah 0 is the Bismillah. It is optional — if the child did not recite it, mark it as Optional rather than Missing and do not treat it as an error.

Listen carefully to the audio recording and provide the following:

1. TRANSCRIPT: What you heard, written in Arabic script. (This section only should be in Arabic.)

2. AYAH COVERAGE: For each ayah, state Complete, Partial, or Missing.
   Use natural teacher language in your notes — e.g. "good, came through clearly" or "stumbled a little here" rather than clinical descriptions.

3. WORDS TO WORK ON: Any specific words that were missing, substituted, or unclear — phrased as gentle guidance, not a report. E.g. "The word X wasn't quite there — worth drilling this one."

4. FOR THE PARENT: 2-3 sentences as a teacher speaking to a parent after class. What went well, what to focus on at home, any patterns worth noting (hesitations, rushing, prompting needed). Honest but encouraging.

5. FOR THE CHILD: One sentence spoken directly to the child. Warm, specific, and motivating. Reference something they actually did well.

Important: Respond entirely in English except for Arabic Quranic text when quoting specific words or ayahs.

Accuracy guidelines:
- Be strict about whether each word was present or absent. Do not assume a word was said if you did not clearly hear it.
- Be lenient only on natural child speech variations: soft voice, stretched vowels, slight accent.
- Do NOT be lenient on: missing words, substituted words, skipped ayahs, or dropped word endings that change meaning.
- If uncertain whether a word was said, mark it as unclear rather than assuming Complete.

Expected full text for reference: {full_text}"""

    print(f"  Uploading audio to Gemini...")
    try:
        audio_file = client.files.upload(file=audio_path)
    except Exception as e:
        print(f"\n  ERROR — Could not upload audio file to Gemini.")
        print(f"  Detail: {e}")
        if "quota" in str(e).lower():
            print("  Fix: free tier quota exceeded. Wait a minute and retry.")
        elif "invalid" in str(e).lower() or "format" in str(e).lower():
            print("  Fix: try converting the audio to mp3 or wav first.")
        else:
            traceback.print_exc()
        return None

    print("  Sending to Gemini for assessment...")
    try:
        response = client.models.generate_content(
            model=MODEL_GEMINI_PRIMARY,
            contents=[prompt, audio_file],
            config={
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
            }
        )
        assessment = response.text.strip()
    except Exception as e:
        print(f"\n  ERROR — Gemini request failed.")
        print(f"  Detail: {e}")
        if "quota" in str(e).lower():
            print("  Fix: free tier quota exceeded. Wait a minute and retry.")
        elif "api_key" in str(e).lower() or "auth" in str(e).lower():
            print("  Fix: check your GEMINI_API_KEY at aistudio.google.com")
        else:
            traceback.print_exc()
        return None

    print(f"\n  Gemini assessment:\n")
    for line in assessment.split("\n"):
        print(f"    {line}")

    # Parse coverage from the AYAH COVERAGE section of Gemini's response.
    # - Only counts ayah-level statuses (Complete / Partial / Missing)
    # - Bismillah (Ayah 1) is optional — skipped from scoring if absent
    import re as _re

    lines = assessment.split("\n")

    # Extract per-ayah statuses from the AYAH COVERAGE block
    # Pattern: "Ayah N" ... Complete/Partial/Missing on the same line
    ayah_statuses = {}
    in_coverage = False
    for line in lines:
        if "AYAH COVERAGE" in line.upper():
            in_coverage = True
            continue
        if in_coverage:
            # Stop when we hit the next numbered section heading
            if _re.match(r"\s*\*{0,2}\s*\d+\.\s+[A-Z]", line) and "Ayah" not in line:
                break
            # Match "Ayah N" lines and extract status
            m = _re.search(r"Ayah\s+(\d+)", line, _re.IGNORECASE)
            if m:
                n = int(m.group(1))
                l = line.lower()
                if "complete" in l:
                    ayah_statuses[n] = "complete"
                elif "partial" in l:
                    ayah_statuses[n] = "partial"
                elif "missing" in l:
                    ayah_statuses[n] = "missing"
                elif "optional" in l or "skipped" in l:
                    ayah_statuses[n] = "optional"

    # Bismillah is Ayah 0 — exclude from scoring regardless of status
    scoring_statuses = {n: s for n, s in ayah_statuses.items()
                        if n != 0 and s != "optional"}

    ayah_count_scored = len(surah["ayahs"]) - 1  # exclude Bismillah

    complete = sum(1 for s in scoring_statuses.values() if s == "complete")
    partial  = sum(1 for s in scoring_statuses.values() if s == "partial")
    missing  = sum(1 for s in scoring_statuses.values() if s == "missing")

    # Fall back if parsing found nothing
    if complete + partial + missing == 0:
        ayah_count_scored = len(surah["ayahs"]) - 1
        for line in lines:
            l = line.lower()
            m = _re.search(r"ayah\s+(\d+)", l)
            if m and int(m.group(1)) != 0:
                if "complete" in l: complete += 1
                elif "partial" in l: partial += 1
                elif "missing" in l: missing += 1

    total = complete + partial + missing
    if total > 0:
        score = round(((complete * 1.0) + (partial * 0.5)) / ayah_count_scored * 100, 1)
        score = min(score, 100.0)
        # Bismillah status note
        bismillah_status = ayah_statuses.get(0, "not recited")
        bismillah_note = f"  Bismillah     : {bismillah_status}"
    else:
        score = None
        bismillah_note = ""

    if score is not None:
        print(f"\n  Coverage : {score}%  ({complete} complete, {partial} partial, {missing} missing / {ayah_count_scored} ayahs)")
        if bismillah_note:
            print(bismillah_note)
    else:
        print("\n  (Could not parse ayah coverage — check assessment text above)")

    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass

    return {
        "model": MODEL_GEMINI_PRIMARY,
        "temperature": TEMPERATURE,
        "assessment": assessment,
        "coverage_estimate": score,
        "ayah_breakdown": {"complete": complete, "partial": partial, "missing": missing},
    }


# ---------------------------------------------------------------------------
# Pass E — Gemini Flash Lite (cheaper Gemini, same approach as Pass D)
# ---------------------------------------------------------------------------

def run_gemini_lite_pass(audio_path, surah, expected_words):
    print_section(f"Pass E — {MODEL_GEMINI_LITE} (cheaper Gemini)")

    try:
        from google import genai
    except ImportError:
        print("\n  ERROR — google-genai package not installed.")
        print("  Fix: pip install google-genai")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n  ERROR — GEMINI_API_KEY not set.")
        print("  Fix: export GEMINI_API_KEY=your_key_here")
        return None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"\n  ERROR — Could not create Gemini client: {e}")
        return None

    ayah_list = "\n".join(
        f"  Ayah {'0' if i == 0 else i}: {ayah}"
        for i, ayah in enumerate(surah["ayahs"])
    )
    full_text = get_full_text(surah)
    prompt = _build_prompt(surah, ayah_list, full_text)

    print(f"  Uploading audio to Gemini Lite...")
    try:
        audio_file = client.files.upload(file=audio_path)
    except Exception as e:
        print(f"\n  ERROR — Could not upload audio: {e}")
        traceback.print_exc()
        return None

    print("  Sending to Gemini Lite for assessment...")
    try:
        response = client.models.generate_content(
            model=MODEL_GEMINI_LITE,
            contents=[prompt, audio_file],
            config={"temperature": TEMPERATURE, "top_p": TOP_P}
        )
        assessment = response.text.strip()
    except Exception as e:
        print(f"\n  ERROR — Gemini Lite request failed.")
        print(f"  Detail: {e}")
        if "quota" in str(e).lower():
            print("  Fix: free tier quota exceeded. Wait a minute and retry.")
        else:
            traceback.print_exc()
        return None

    print(f"\n  Gemini Lite assessment:\n")
    for line in assessment.split("\n"):
        print(f"    {line}")

    score, complete, partial, missing, bismillah_status = _parse_coverage(assessment, surah)

    if score is not None:
        print(f"\n  Coverage : {score}%  ({complete} complete, {partial} partial, {missing} missing / {len(surah['ayahs'])-1} ayahs)")
        print(f"  Bismillah     : {bismillah_status}")
    else:
        print("\n  (Could not parse ayah coverage — check assessment above)")

    try:
        client.files.delete(name=audio_file.name)
    except Exception:
        pass

    return {
        "model": MODEL_GEMINI_LITE,
        "temperature": TEMPERATURE,
        "assessment": assessment,
        "coverage_estimate": score,
        "ayah_breakdown": {"complete": complete, "partial": partial, "missing": missing},
    }


# ---------------------------------------------------------------------------
# Pass F — Claude Haiku (Anthropic multimodal)
# ---------------------------------------------------------------------------

def run_claude_pass(audio_path, surah, expected_words):
    print_section(f"Pass F — {MODEL_CLAUDE} (Anthropic)")

    try:
        import anthropic
    except ImportError:
        print("\n  ERROR — anthropic package not installed.")
        print("  Fix: pip install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  ERROR — ANTHROPIC_API_KEY not set.")
        print("  Fix: export ANTHROPIC_API_KEY=your_key_here")
        print("  Get a key at: https://console.anthropic.com")
        return None

    ayah_list = "\n".join(
        f"  Ayah {'0' if i == 0 else i}: {ayah}"
        for i, ayah in enumerate(surah["ayahs"])
    )
    full_text = get_full_text(surah)
    prompt = _build_prompt(surah, ayah_list, full_text)

    # Read and encode audio file
    print(f"  Reading audio: {audio_path}")
    try:
        import base64
        with open(audio_path, "rb") as f:
            audio_data = base64.standard_b64encode(f.read()).decode("utf-8")
        # Determine media type
        ext = audio_path.rsplit(".", 1)[-1].lower()
        media_type_map = {
            "mp3": "audio/mpeg", "wav": "audio/wav", "webm": "audio/webm",
            "m4a": "audio/mp4", "ogg": "audio/ogg", "flac": "audio/flac",
        }
        media_type = media_type_map.get(ext, "audio/mpeg")
    except Exception as e:
        print(f"\n  ERROR — Could not read audio file: {e}")
        return None

    print("  Sending to Claude for assessment...")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=MODEL_CLAUDE,
            max_tokens=2048,
            temperature=TEMPERATURE,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": audio_data,
                        },
                    }
                ]
            }]
        )
        assessment = message.content[0].text.strip()
    except anthropic.AuthenticationError:
        print("\n  ERROR — Anthropic API key invalid or expired.")
        print("  Fix: check key at https://console.anthropic.com")
        return None
    except anthropic.RateLimitError:
        print("\n  ERROR — Anthropic rate limit hit.")
        print("  Fix: wait a moment and retry.")
        return None
    except Exception as e:
        print(f"\n  ERROR — Claude request failed.")
        print(f"  Detail: {e}")
        traceback.print_exc()
        return None

    print(f"\n  Claude assessment:\n")
    for line in assessment.split("\n"):
        print(f"    {line}")

    score, complete, partial, missing, bismillah_status = _parse_coverage(assessment, surah)

    if score is not None:
        print(f"\n  Coverage : {score}%  ({complete} complete, {partial} partial, {missing} missing / {len(surah['ayahs'])-1} ayahs)")
        print(f"  Bismillah     : {bismillah_status}")
    else:
        print("\n  (Could not parse ayah coverage — check assessment above)")

    return {
        "model": MODEL_CLAUDE,
        "temperature": TEMPERATURE,
        "assessment": assessment,
        "coverage_estimate": score,
        "ayah_breakdown": {"complete": complete, "partial": partial, "missing": missing},
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(result_a, result_b, result_c, result_d, result_e=None, result_f=None):
    print_section("Summary")

    passes = [
        ("Pass A — Whisper, no prompt     ", result_a),
        ("Pass B — Whisper, with prompt   ", result_b),
        ("Pass C — Quran-tuned (local)    ", result_c),
        (f"Pass D — {MODEL_GEMINI_PRIMARY:<22}", result_d),
        (f"Pass E — {MODEL_GEMINI_LITE:<22}", result_e),
        (f"Pass F — {MODEL_CLAUDE:<22}", result_f),
    ]

    any_completed = False
    for label, result in passes:
        if result:
            any_completed = True
            if "coverage" in result:
                print(f"  {label}: {result['coverage']['coverage_pct']}%")
            elif "coverage_estimate" in result and result["coverage_estimate"] is not None:
                print(f"  {label}: ~{result['coverage_estimate']}% (estimated from ayah assessment)")
            else:
                print(f"  {label}: completed (see assessment above)")
        else:
            print(f"  {label}: — (did not complete)")

    if not any_completed:
        print("\n  No passes completed. Review the errors above before retrying.")
        return

    completed = [(label, r) for label, r in passes if r and "coverage" in r]
    if completed:
        best_label, best = max(completed, key=lambda x: x[1]["coverage"]["coverage_pct"])
        best_pct = best["coverage"]["coverage_pct"]
    else:
        best_pct = 0

    print()
    if best_pct >= 80:
        print("  ✓ Strong signal. The model is picking up most of the surah.")
        print("    Next: record a version where the child deliberately skips an ayah.")
        print("    If that ayah shows as missing — the detection mechanic works.")
    elif best_pct >= 50:
        print("  △ Partial signal. Some words detected but reliability is unclear.")
        print("    Try a cleaner recording (quieter room, closer to mic).")
    else:
        print("  ✗ Low coverage on transcription passes — check Gemini assessment above.")
        print("    Gemini's qualitative output may be more reliable than the numeric scores.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

PASS_DESCRIPTIONS = {
    "a": "OpenAI Whisper (no prompt)",
    "b": "OpenAI Whisper (prompted)",
    "c": "tarteel-ai/whisper-base-ar-quran (local)",
    "d": f"Gemini {MODEL_GEMINI_PRIMARY}",
    "e": f"Gemini {MODEL_GEMINI_LITE} (2.0)",
    "f": f"Claude {MODEL_CLAUDE}",
}


def run_poc(audio_path, surah_key, passes):
    if not os.path.exists(audio_path):
        print(f"\nERROR — Audio file not found: {audio_path}")
        print("  Check the path and try again.")
        sys.exit(1)

    if surah_key not in SURAHS:
        print(f"\nERROR — Unknown surah: '{surah_key}'")
        print(f"  Available: {', '.join(SURAHS.keys())}")
        sys.exit(1)

    if not passes:
        print("\nERROR — No passes selected. Specify at least one with --run-X.")
        print("\nAvailable passes:")
        for k, v in PASS_DESCRIPTIONS.items():
            print(f"  --run-{k}  {v}")
        sys.exit(1)

    surah = SURAHS[surah_key]
    expected_words = get_all_words(surah)

    print(f"\n🎙  Recitation POC")
    print(f"   Surah  : {surah['name']}")
    print(f"   Audio  : {audio_path}")
    print(f"   Words  : {len(expected_words)} expected across {len(surah['ayahs'])} ayahs")
    print(f"   Passes : {', '.join(passes.upper() for passes in sorted(passes))}")

    result_a, result_b = None, None
    if "a" in passes or "b" in passes:
        result_a, result_b = run_openai_passes(audio_path, surah, expected_words)
        if "a" not in passes: result_a = None
        if "b" not in passes: result_b = None

    result_c = run_tarteel_pass(audio_path, expected_words) if "c" in passes else None
    result_d = run_gemini_pass(audio_path, surah, expected_words) if "d" in passes else None
    result_e = run_gemini_lite_pass(audio_path, surah, expected_words) if "e" in passes else None
    result_f = run_claude_pass(audio_path, surah, expected_words) if "f" in passes else None

    print_summary(result_a, result_b, result_c, result_d, result_e, result_f)

    import datetime as _dt
    entry = {
        "timestamp": _dt.datetime.now().isoformat(),
        "surah": surah["name"],
        "audio": audio_path,
        "passes_run": sorted(passes),
        "pass_a": result_a,
        "pass_b": result_b,
        "pass_c": result_c,
        "pass_d": result_d,
        "pass_e": result_e,
        "pass_f": result_f,
    }

    # One log file per surah — each run appends a new entry
    # When a file exceeds MAX_FILE_SIZE_KB, it gets archived and a new file starts
    MAX_FILE_SIZE_KB = 500
    out_path = f"results_{surah_key}.json"
    results_dir = "results"

    try:
        os.makedirs(results_dir, exist_ok=True)
        out_path = os.path.join(results_dir, f"results_{surah_key}.json")

        # Load existing entries if file exists
        entries = []
        if os.path.exists(out_path):
            # Archive if file is getting large
            size_kb = os.path.getsize(out_path) / 1024
            if size_kb >= MAX_FILE_SIZE_KB:
                archive_path = os.path.join(
                    results_dir,
                    f"results_{surah_key}_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                os.rename(out_path, archive_path)
                print(f"\n  Log archived to: {archive_path}")
                entries = []
            else:
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                    if not isinstance(entries, list):
                        entries = [entries]  # migrate old single-entry files
                except Exception:
                    entries = []

        entries.append(entry)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        print(f"\n  Result logged to : {out_path}  ({len(entries)} total runs)")

    except Exception as e:
        print(f"\n  WARNING — Could not save results file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recitation POC — word coverage test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Passes (specify one or more with --run-X):
  --run-a   OpenAI Whisper, no prompt        (requires OPENAI_API_KEY)
  --run-b   OpenAI Whisper, prompted         (requires OPENAI_API_KEY)
  --run-c   tarteel-ai/whisper-base-ar-quran (local, no key needed, ~290MB download)
  --run-d   Gemini 2.5 Flash                 (requires GEMINI_API_KEY) ← recommended
  --run-e   Gemini 2.0 Flash Lite            (requires GEMINI_API_KEY, cheaper)
  --run-f   Claude Haiku                     (requires ANTHROPIC_API_KEY)

Examples:
  python3 test_recitation.py --audio recording.mp3 --surah ikhlas --run-d
  python3 test_recitation.py --audio recording.mp3 --surah kawthar --run-d --run-e --run-f
  python3 test_recitation.py --audio recording.mp3 --surah humaza --run-d --run-e
        """
    )
    parser.add_argument("--audio", required=True, help="Path to audio file (m4a, mp3, wav, webm)")
    parser.add_argument("--surah", default="ikhlas", help="Surah key: fatiha, asr, humaza, fil, quraysh, maun, kawthar, kafirun, nasr, masad, ikhlas, falaq, nas")
    parser.add_argument("--run-a", action="store_true", help="Run Pass A: OpenAI Whisper no prompt")
    parser.add_argument("--run-b", action="store_true", help="Run Pass B: OpenAI Whisper prompted")
    parser.add_argument("--run-c", action="store_true", help="Run Pass C: tarteel-ai local model")
    parser.add_argument("--run-d", action="store_true", help="Run Pass D: Gemini 2.5 Flash (recommended)")
    parser.add_argument("--run-e", action="store_true", help="Run Pass E: Gemini 2.0 Flash Lite (cheaper)")
    parser.add_argument("--run-f", action="store_true", help="Run Pass F: Claude Haiku")
    args = parser.parse_args()

    passes = set()
    if args.run_a: passes.add("a")
    if args.run_b: passes.add("b")
    if args.run_c: passes.add("c")
    if args.run_d: passes.add("d")
    if args.run_e: passes.add("e")
    if args.run_f: passes.add("f")

    run_poc(args.audio, args.surah, passes)
