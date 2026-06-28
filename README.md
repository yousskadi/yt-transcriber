# 🎬 YouTube Transcription & Translation Pipeline

Pipeline Docker pour **télécharger → transcrire → traduire** des vidéos YouTube.
Idéal pour l'arabe → français, mais supporte 98+ langues.

## 📦 Stack

| Service | Outil | Description |
|---|---|---|
| Téléchargement | `yt-dlp` | Extraction audio YouTube |
| Transcription | `faster-whisper` | Whisper optimisé CPU (OpenAI) |
| Traduction | `LibreTranslate` | Self-hosted, gratuit |
| Traduction (alt) | `DeepL API` | Meilleure qualité, API payante |

## 🚀 Démarrage rapide

```bash
# 1. Copier et configurer l'environnement
cp .env .env.backup
nano .env   # Renseigner YOUTUBE_URL

# 2. Lancer le pipeline complet
chmod +x run.sh
./run.sh "https://www.youtube.com/watch?v=VOTRE_ID"

# Ou directement avec docker compose
docker compose run --rm pipeline
```

## ⚙️ Variables d'environnement (.env)

| Variable | Défaut | Description |
|---|---|---|
| `YOUTUBE_URL` | — | URL de la vidéo YouTube |
| `AUDIO_FORMAT` | `mp3` | Format audio (mp3, wav, m4a) |
| `WHISPER_MODEL` | `medium` | Modèle Whisper (tiny→large) |
| `SOURCE_LANGUAGE` | `ar` | Langue de la vidéo |
| `TARGET_LANG` | `fr` | Langue de traduction |
| `OUTPUT_FORMAT` | `txt` | Format transcript (txt, srt, vtt, json) |
| `TRANSLATE_ENGINE` | `libretranslate` | Moteur (libretranslate ou deepl) |
| `DEEPL_API_KEY` | — | Clé API DeepL (si engine=deepl) |
| `LT_LOAD_ONLY` | `ar,fr,en` | Langues LibreTranslate à charger |

## 🎛️ Modèles Whisper — Guide de choix

| Modèle | RAM | Précision arabe | Vitesse |
|---|---|---|---|
| `tiny` | ~1 GB | ⭐⭐ | ⚡⚡⚡⚡ |
| `base` | ~1 GB | ⭐⭐⭐ | ⚡⚡⚡ |
| `small` | ~2 GB | ⭐⭐⭐ | ⚡⚡⚡ |
| `medium` | ~5 GB | ⭐⭐⭐⭐ | ⚡⚡ |
| `large` | ~10 GB | ⭐⭐⭐⭐⭐ | ⚡ |

> Pour l'arabe : **`medium` minimum recommandé**, `large` pour les dialectes.

## 📁 Fichiers générés

```
output/
├── audio.mp3                      # Audio téléchargé
├── transcript.txt                 # Transcription (arabe)
└── translation_ar_to_fr.txt       # Traduction finale
```

## 🔧 Commandes utiles

```bash
# Pipeline complet avec options
./run.sh "URL" --model large --lang ar --target fr

# Transcription seulement (audio déjà téléchargé)
./run.sh --transcribe-only --model large

# Traduction seulement (transcript déjà généré)
./run.sh --translate-only --target en

# Voir les logs LibreTranslate
docker compose logs -f libretranslate

# Nettoyer les fichiers output
rm -rf output/*
```

## 💡 Conseils pour l'arabe

- **Arabe moderne standard (MSA)** : `medium` suffit
- **Dialectes** (égyptien, marocain, etc.) : utiliser `large`
- **Mauvaise qualité audio** : activer le filtre VAD (déjà activé par défaut)
- **Traduction** : LibreTranslate est gratuit mais moins précis que DeepL pour l'arabe dialectal