#!/usr/bin/env python3
"""
Script de traduction du transcript via DeepL ou LibreTranslate
Variables d'environnement :
  TRANSLATE_ENGINE      : libretranslate | deepl
  SOURCE_LANG           : langue source (ar, fr, en, ...)
  TARGET_LANG           : langue cible (fr, en, ...)
  DEEPL_API_KEY         : clé API DeepL (si engine=deepl)
  LIBRETRANSLATE_URL    : URL de l'instance LibreTranslate
"""

import os
import time
import requests
from pathlib import Path

# --- Config ---
ENGINE              = os.getenv("TRANSLATE_ENGINE", "libretranslate")
SOURCE_LANG         = os.getenv("SOURCE_LANG", "ar")
TARGET_LANG         = os.getenv("TARGET_LANG", "fr")
DEEPL_API_KEY       = os.getenv("DEEPL_API_KEY", "")
LIBRETRANSLATE_URL  = os.getenv("LIBRETRANSLATE_URL", "http://libretranslate:5000")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL        = os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
OUTPUT_DIR          = Path("/output")

# Noms de langues lisibles pour le prompt Claude
LANG_NAMES = {
    "ar": "arabe", "fr": "français", "en": "anglais", "es": "espagnol",
    "de": "allemand", "it": "italien", "pt": "portugais", "tr": "turc",
}

# --- Trouver le fichier transcript ---
transcript_files = list(OUTPUT_DIR.glob("transcript.*"))
if not transcript_files:
    raise FileNotFoundError("❌ Aucun fichier transcript trouvé. Lancez d'abord la transcription.")

# Priorité : txt > json > srt > vtt
priority = {"txt": 0, "json": 1, "srt": 2, "vtt": 3}
transcript_path = sorted(transcript_files, key=lambda f: priority.get(f.suffix.lstrip("."), 99))[0]
print(f"📄 Fichier source : {transcript_path.name}")
print(f"🔧 Moteur : {ENGINE}")
print(f"🌐 Traduction : {SOURCE_LANG} → {TARGET_LANG}")


def translate_deepl(text: str) -> str:
    """Traduction via l'API DeepL"""
    import deepl
    translator = deepl.Translator(DEEPL_API_KEY)
    result = translator.translate_text(
        text,
        source_lang=SOURCE_LANG.upper(),
        target_lang=TARGET_LANG.upper(),
    )
    return result.text


def translate_libretranslate(text: str) -> str:
    """Traduction via LibreTranslate (self-hosted)"""
    # Attendre que le service soit prêt
    for attempt in range(10):
        try:
            r = requests.get(f"{LIBRETRANSLATE_URL}/languages", timeout=5)
            if r.status_code == 200:
                break
        except Exception:
            pass
        print(f"⏳ LibreTranslate pas encore prêt, tentative {attempt+1}/10...")
        time.sleep(10)

    # Découper en chunks (LibreTranslate a une limite par requête)
    CHUNK_SIZE = 3000
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    translated_chunks = []

    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  Traduction chunk {i+1}/{len(chunks)}...")
        resp = requests.post(
            f"{LIBRETRANSLATE_URL}/translate",
            json={
                "q": chunk,
                "source": SOURCE_LANG,
                "target": TARGET_LANG,
                "format": "text",
            },
            timeout=60,
        )
        resp.raise_for_status()
        translated_chunks.append(resp.json()["translatedText"])

    return "\n".join(translated_chunks)


def translate_claude(text: str) -> str:
    """Traduction via Claude (Anthropic) — qualité supérieure pour l'arabe
    littéraire et les textes religieux ; corrige aussi les erreurs évidentes
    de transcription en s'appuyant sur le contexte."""
    import anthropic

    if not ANTHROPIC_API_KEY:
        raise ValueError("❌ ANTHROPIC_API_KEY manquant dans le .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    src = LANG_NAMES.get(SOURCE_LANG, SOURCE_LANG)
    tgt = LANG_NAMES.get(TARGET_LANG, TARGET_LANG)

    system_prompt = (
        f"Tu es un traducteur professionnel du {src} vers le {tgt}, "
        "spécialisé dans les textes religieux islamiques et l'arabe littéraire (fusha). "
        "On te fournit la transcription automatique (Whisper) d'une vidéo, qui peut "
        "contenir des erreurs de reconnaissance vocale ou des fragments parasites. "
        "Traduis fidèlement le sens en t'appuyant sur le contexte pour corriger "
        "silencieusement les erreurs de transcription évidentes. Rends un texte "
        f"fluide et naturel en {tgt}, en conservant le découpage en paragraphes. "
        "Pour les citations coraniques ou les hadiths, traduis-les fidèlement. "
        f"Réponds UNIQUEMENT avec la traduction en {tgt}, sans préambule ni commentaire."
    )

    # Découper en chunks sur les sauts de ligne pour borner la sortie
    CHUNK_SIZE = 6000
    lines = text.split("\n")
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) + 1 > CHUNK_SIZE and current:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current)

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"  Traduction chunk {i+1}/{len(chunks)} (Claude {CLAUDE_MODEL})...")
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": chunk}],
        ) as stream:
            message = stream.get_final_message()
        translated_chunks.append(
            "".join(b.text for b in message.content if b.type == "text").strip()
        )

    return "\n".join(translated_chunks)


# --- Lire le contenu ---
with open(transcript_path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"📊 Taille du transcript : {len(content)} caractères")

# --- Traduire ---
print("⏳ Traduction en cours...")
if ENGINE == "deepl":
    if not DEEPL_API_KEY:
        raise ValueError("❌ DEEPL_API_KEY manquant dans le .env")
    translated = translate_deepl(content)
elif ENGINE == "libretranslate":
    translated = translate_libretranslate(content)
elif ENGINE == "claude":
    translated = translate_claude(content)
else:
    raise ValueError(f"❌ Moteur inconnu : {ENGINE}. Utilisez 'claude', 'deepl' ou 'libretranslate'")

# --- Sauvegarder ---
output_path = OUTPUT_DIR / f"translation_{SOURCE_LANG}_to_{TARGET_LANG}.txt"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(translated)

print(f"✅ Traduction sauvegardée : {output_path}")
print(f"\n{'━'*50}")
print(f"📁 Fichiers générés dans ./output/ :")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        print(f"   {f.name:<40} ({size_kb:.1f} KB)")
print(f"{'━'*50}")