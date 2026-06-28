#!/usr/bin/env python3
"""
Génère un document HTML bilingue à partir de /output/transcript.txt :
chaque paragraphe arabe (aligné à droite, RTL) est suivi de sa traduction
française (alignée à gauche, LTR). Traduction segment par segment via DeepL
pour un appariement exact.

Variables d'environnement : DEEPL_API_KEY, SOURCE_LANG (ar), TARGET_LANG (fr)
"""

import os
import html
from pathlib import Path
import deepl

SOURCE_LANG   = os.getenv("SOURCE_LANG", "ar")
TARGET_LANG   = os.getenv("TARGET_LANG", "fr")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
OUTPUT_DIR    = Path("/output")

if not DEEPL_API_KEY:
    raise ValueError("❌ DEEPL_API_KEY manquant dans le .env")

transcript_path = OUTPUT_DIR / "transcript.txt"
if not transcript_path.exists():
    raise FileNotFoundError("❌ /output/transcript.txt introuvable. Lancez d'abord la transcription.")

# --- Lire les paragraphes arabes (un par ligne non vide) ---
with open(transcript_path, encoding="utf-8") as f:
    paragraphs = [ln.strip() for ln in f if ln.strip()]

print(f"📄 {len(paragraphs)} paragraphes à traduire ({SOURCE_LANG} → {TARGET_LANG})")

translator = deepl.Translator(DEEPL_API_KEY)

pairs = []
for i, ar in enumerate(paragraphs, 1):
    print(f"  Traduction {i}/{len(paragraphs)}...")
    fr = translator.translate_text(
        ar, source_lang=SOURCE_LANG.upper(), target_lang=TARGET_LANG.upper()
    ).text
    pairs.append((ar, fr))

# --- Construire le HTML ---
blocks = "\n".join(
    f"""    <section class="pair">
      <p class="ar" dir="rtl" lang="ar">{html.escape(ar)}</p>
      <p class="fr" dir="ltr" lang="fr">{html.escape(fr)}</p>
    </section>"""
    for ar, fr in pairs
)

doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Transcription bilingue — Arabe / Français</title>
<style>
  :root {{ --accent: #1f6f8b; --line: #e2e2e2; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.7; color: #1a1a1a; background: #fafafa;
    margin: 0; padding: 2.5rem 1rem;
  }}
  .container {{ max-width: 820px; margin: 0 auto; }}
  h1 {{ text-align: center; color: var(--accent); font-size: 1.6rem; margin-bottom: 2.5rem; }}
  .pair {{
    background: #fff; border: 1px solid var(--line); border-radius: 10px;
    padding: 1.4rem 1.6rem; margin-bottom: 1.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
  }}
  .ar {{
    direction: rtl; text-align: right; unicode-bidi: isolate;
    font-family: "Traditional Arabic", "Amiri", "Scheherazade New", "Times New Roman", serif;
    font-size: 1.65rem; line-height: 2.1; margin: 0 0 1rem 0; color: #111;
  }}
  .fr {{
    direction: ltr; text-align: left; unicode-bidi: isolate;
    font-size: 1.08rem; margin: 0; color: #333;
    padding-top: 1rem; border-top: 1px dashed var(--line);
  }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .pair {{ box-shadow: none; break-inside: avoid; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <h1>Transcription bilingue — Arabe / Français</h1>
{blocks}
  </div>
</body>
</html>
"""

out_path = OUTPUT_DIR / "bilingual.html"
out_path.write_text(doc, encoding="utf-8")
print(f"✅ Document bilingue généré : {out_path}")
print(f"   {len(pairs)} paragraphes appariés.")
