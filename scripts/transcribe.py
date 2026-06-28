#!/usr/bin/env python3
"""
Script de transcription audio → texte via faster-whisper (Whisper optimisé CPU)
Variables d'environnement :
  WHISPER_MODEL     : modèle Whisper (tiny/base/small/medium/large)
  SOURCE_LANGUAGE   : langue source (ar, fr, en, ...)
  OUTPUT_FORMAT     : format de sortie (txt, srt, vtt, json)
"""

import os
import json
import glob
from pathlib import Path
from faster_whisper import WhisperModel

# --- Config depuis les variables d'environnement ---
MODEL_SIZE     = os.getenv("WHISPER_MODEL", "medium")
LANGUAGE       = os.getenv("SOURCE_LANGUAGE", "ar")
OUTPUT_FORMAT  = os.getenv("OUTPUT_FORMAT", "txt")
OUTPUT_DIR     = Path("/output")

# --- Trouver le fichier audio ---
audio_files = list(OUTPUT_DIR.glob("audio.*"))
if not audio_files:
    raise FileNotFoundError("❌ Aucun fichier audio trouvé dans /output/. Lancez d'abord le downloader.")

audio_path = audio_files[0]
print(f"🎵 Fichier audio : {audio_path.name}")
print(f"🤖 Modèle Whisper : {MODEL_SIZE}")
print(f"🌐 Langue source : {LANGUAGE}")

# --- Chargement du modèle (CPU, int8 pour perf) ---
print("⏳ Chargement du modèle Whisper...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

# --- Transcription ---
print("🎙️  Transcription en cours...")
segments, info = model.transcribe(
    str(audio_path),
    language=LANGUAGE,
    beam_size=5,
    vad_filter=True,           # Filtre les silences
    vad_parameters=dict(min_silence_duration_ms=500),
)

segments = list(segments)  # Matérialiser le générateur
print(f"✅ {len(segments)} segments détectés | Durée : {info.duration:.1f}s")

# --- Export selon le format ---
output_base = OUTPUT_DIR / "transcript"

def format_timestamp(seconds: float) -> str:
    """Convertit les secondes en format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

if OUTPUT_FORMAT == "txt":
    output_path = output_base.with_suffix(".txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg.text.strip() + "\n")

elif OUTPUT_FORMAT == "srt":
    output_path = output_base.with_suffix(".srt")
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n")
            f.write(f"{seg.text.strip()}\n\n")

elif OUTPUT_FORMAT == "vtt":
    output_path = output_base.with_suffix(".vtt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = format_timestamp(seg.start).replace(",", ".")
            end   = format_timestamp(seg.end).replace(",", ".")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg.text.strip()}\n\n")

elif OUTPUT_FORMAT == "json":
    output_path = output_base.with_suffix(".json")
    data = [
        {
            "id": i,
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        }
        for i, seg in enumerate(segments, 1)
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f"📄 Transcript sauvegardé : {output_path}")