"""
Recitation POC — Word Coverage Test
=====================================
Takes a child's audio recording and checks it against
the known Arabic text of a surah using three approaches:

  Pass A — OpenAI Whisper, no prompt (open transcription, baseline)
  Pass B — OpenAI Whisper, prompted with the expected surah text
  Pass C — tarteel-ai/whisper-base-ar-quran (Quran-tuned, runs locally, no API key needed)

Usage:
  python test_recitation.py --audio your_recording.m4a --surah ikhlas

  # Skip OpenAI passes if you only want to test the local Quran model:
  python test_recitation.py --audio your_recording.m4a --surah ikhlas --skip-openai

Requirements:
  pip install -r requirements.txt
"""

import argparse
import json
import os
import sys
import traceback

# ---------------------------------------------------------------------------
# Surah text
# ---------------------------------------------------------------------------
SURAHS = {
    "ikhlas": {
        "name": "Al-Ikhlas (112)",
        "ayahs": [
            "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "اللَّهُ الصَّمَدُ",
            "لَمْ يَلِدْ وَلَمْ يُولَدْ",
            "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
        ],
    },
    "kawthar": {
        "name": "Al-Kawthar (108)",
        "ayahs": [
            "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ",
            "فَصَلِّ لِرَبِّكَ وَانْحَرْ",
            "إِنَّ شَانِئَكَ هُوَ الْأَبْتَرُ",
        ],
    },
    "asr": {
        "name": "Al-Asr (103)",
        "ayahs": [
            "وَالْعَصْرِ",
            "إِنَّ الْإِنسَانَ لَفِي خُسْرٍ",
            "إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ وَتَوَاصَوْا بِالْحَقِّ وَتَوَاصَوْا بِالصَّبْرِ",
        ],
    },
}


def get_full_text(surah):
    return " ".join(surah["ayahs"])


def get_all_words(surah):
    words = []
    for ayah in surah["ayahs"]:
        words.extend(ayah.split())
    return words


def word_coverage(transcript, expected_words):
    transcript_words = set(transcript.split())
    matched = [w for w in expected_words if w in transcript_words]
    missing = [w for w in expected_words if w not in transcript_words]
    return {
        "total_expected": len(expected_words),
        "matched": len(matched),
        "missing_count": len(missing),
        "missing_words": missing,
        "coverage_pct": round(len(matched) / len(expected_words) * 100, 1) if expected_words else 0,
    }


def print_section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_coverage(coverage):
    print(f"  Coverage : {coverage['coverage_pct']}%  ({coverage['matched']}/{coverage['total_expected']} words matched)")
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
                    "model": "whisper-1",
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
            print("  Fix: check your internet connection and try again.")
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
            print(f"\n  ERROR ({pass_label}) — Unexpected error during OpenAI transcription.")
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
        print("  Note: torch can be large (~2GB). Install guide: https://pytorch.org/get-started/locally/")
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
            asr = pipeline(
                "automatic-speech-recognition",
                model=model_id,
                device=device,
            )
        except OSError as e:
            print(f"\n  ERROR — Could not download model from HuggingFace.")
            print(f"  Detail: {e}")
            print("  Fix: check your internet connection. Model is fetched on first use.")
            return None
        except RuntimeError as e:
            print(f"\n  ERROR — Model failed to load (possible memory issue).")
            print(f"  Detail: {e}")
            print("  Fix: close other applications to free memory, then retry.")
            return None
        except Exception as e:
            print(f"\n  ERROR — Unexpected failure loading model pipeline.")
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
            print("  If the format is right, try: pip install soundfile audioread")
            return None

        print("  Running transcription...")
        try:
            result = asr({"array": audio, "sampling_rate": 16000})
            transcript = result["text"].strip()
        except Exception as e:
            print(f"\n  ERROR — Transcription failed during model inference.")
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
# Summary
# ---------------------------------------------------------------------------

def print_summary(result_a, result_b, result_c):
    print_section("Summary")

    passes = [
        ("Pass A — Whisper, no prompt  ", result_a),
        ("Pass B — Whisper, with prompt", result_b),
        ("Pass C — Quran-tuned (local) ", result_c),
    ]

    any_completed = False
    for label, result in passes:
        if result:
            any_completed = True
            print(f"  {label}: {result['coverage']['coverage_pct']}%")
        else:
            print(f"  {label}: — (did not complete)")

    if not any_completed:
        print("\n  No passes completed. Review the errors above before retrying.")
        return

    completed = [(label, r) for label, r in passes if r]
    best_label, best = max(completed, key=lambda x: x[1]["coverage"]["coverage_pct"])
    best_pct = best["coverage"]["coverage_pct"]

    print(f"\n  Best result : {best_label.strip()} at {best_pct}%")
    print()

    if best_pct >= 80:
        print("  ✓ Strong signal. The model is picking up most of the surah.")
        print("    Next: record a version where the child deliberately skips an ayah.")
        print("    If that ayah shows as missing words — the detection mechanic works.")
    elif best_pct >= 50:
        print("  △ Partial signal. Some words detected but reliability is unclear.")
        print("    Try a cleaner recording (quieter room, closer to mic).")
        print("    Compare which pass scored higher — lean on that model going forward.")
    else:
        print("  ✗ Low coverage. The models are struggling with this recording.")
        print("    First check: is the child clearly audible when you play it back?")
        print("    If yes: child's voice may need further investigation.")
        print("    If no: re-record in a quieter room, closer to the mic.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_poc(audio_path, surah_key, skip_openai):
    if not os.path.exists(audio_path):
        print(f"\nERROR — Audio file not found: {audio_path}")
        print("  Check the path and try again.")
        sys.exit(1)

    if surah_key not in SURAHS:
        print(f"\nERROR — Unknown surah: '{surah_key}'")
        print(f"  Available: {', '.join(SURAHS.keys())}")
        sys.exit(1)

    surah = SURAHS[surah_key]
    expected_words = get_all_words(surah)

    print(f"\n🎙  Recitation POC")
    print(f"   Surah  : {surah['name']}")
    print(f"   Audio  : {audio_path}")
    print(f"   Words  : {len(expected_words)} expected across {len(surah['ayahs'])} ayahs")

    result_a, result_b = None, None
    if skip_openai:
        print("\n  Skipping Passes A & B (--skip-openai flag set).")
    else:
        result_a, result_b = run_openai_passes(audio_path, surah, expected_words)

    result_c = run_tarteel_pass(audio_path, expected_words)

    print_summary(result_a, result_b, result_c)

    output = {
        "surah": surah["name"],
        "audio": audio_path,
        "expected_words": expected_words,
        "pass_a": result_a,
        "pass_b": result_b,
        "pass_c": result_c,
    }

    out_path = "poc_results.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n  Full results saved to: {out_path}")
    except Exception as e:
        print(f"\n  WARNING — Could not save results file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recitation POC — word coverage test")
    parser.add_argument("--audio", required=True, help="Path to audio file (m4a, mp3, wav, webm)")
    parser.add_argument("--surah", default="ikhlas", help="Surah to test: ikhlas, kawthar, asr")
    parser.add_argument("--skip-openai", action="store_true", help="Run Pass C only (no OpenAI API key needed)")
    args = parser.parse_args()
    run_poc(args.audio, args.surah, args.skip_openai)
