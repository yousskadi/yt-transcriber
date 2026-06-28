# 🎬 YouTube Transcription & Translation Pipeline

Pipeline **Docker** pour **télécharger → transcrire → traduire** des vidéos YouTube,
avec génération d'un **document bilingue** (texte source + traduction, côte à côte).
Optimisé pour l'**arabe littéraire → français**, mais supporte 98+ langues.

Deux modes d'utilisation :
- **Local** — tout tourne sur ta machine (`run.sh`).
- **Hybride (GitHub Actions)** — le download se fait en local, la transcription (lourde, CPU) tourne sur les serveurs GitHub (`fetch-audio.sh`).

## 📦 Stack

| Étape | Outil |
|---|---|
| Téléchargement audio | `yt-dlp` (+ `ffmpeg`) |
| Transcription | `faster-whisper` (Whisper optimisé CPU) |
| Traduction | **Claude** (Anthropic) · **DeepL** · **LibreTranslate** |

### Choix du moteur de traduction

| Moteur | Qualité (arabe→fr) | Coût | Notes |
|---|---|---|---|
| `claude` | ★★★★★ | Payant (API, ~1-2 centimes/vidéo en Opus) | Corrige les erreurs de transcription par le contexte ; idéal arabe littéraire/religieux |
| `deepl` | ★★★★ | Gratuit (plan Developer, 1M caractères) | Très bon, **défaut recommandé** |
| `libretranslate` | ★★ | Gratuit, self-hosted | Qualité moindre, aucun compte requis |

---

## ⚙️ Configuration

```bash
cp .env.example .env
nano .env   # renseigner les clés et préférences
```

> ⚠️ **Ne committez jamais `.env`** (il contient vos clés). Il est déjà dans `.gitignore`.

| Variable | Défaut | Description |
|---|---|---|
| `YOUTUBE_URL` | — | URL de la vidéo (mode local) |
| `AUDIO_FORMAT` | `mp3` | Format audio (mp3, wav, m4a, opus) |
| `WHISPER_MODEL` | `medium` | Modèle Whisper (tiny→large) |
| `SOURCE_LANGUAGE` | `ar` | Langue source (code ISO) |
| `TARGET_LANG` | `fr` | Langue cible |
| `OUTPUT_FORMAT` | `txt` | Format transcript (txt, srt, vtt, json) |
| `TRANSLATE_ENGINE` | `deepl` | `claude` · `deepl` · `libretranslate` |
| `ANTHROPIC_API_KEY` | — | Clé API si engine=claude ([console](https://console.anthropic.com/)) |
| `CLAUDE_MODEL` | `claude-opus-4-8` | Modèle Claude (ou `claude-sonnet-4-6`, `claude-haiku-4-5`) |
| `DEEPL_API_KEY` | — | Clé API si engine=deepl ([deepl.com/pro-api](https://www.deepl.com/pro-api)) |
| `LT_LOAD_ONLY` | `ar,fr,en` | Langues LibreTranslate à charger |

---

## 💻 Utilisation locale

```bash
chmod +x run.sh

# Pipeline complet (download → transcription → traduction)
./run.sh "https://www.youtube.com/watch?v=VOTRE_ID" --model medium --engine deepl

# Options
./run.sh "URL" --model large --lang ar --target fr --engine claude

# Étapes isolées (audio/transcript déjà présents)
./run.sh --transcribe-only --model medium
./run.sh --translate-only --engine deepl
```

### Document bilingue (arabe à droite / français à gauche)

Génère `output/bilingual.html` (un paragraphe source suivi de sa traduction, mis en
forme RTL/LTR, imprimable en PDF via `Ctrl+P` dans le navigateur) :

```bash
docker compose run --rm --no-deps translate \
  bash -c "pip install deepl -q && python /scripts/bilingual.py"
```

---

## ☁️ Utilisation hybride (GitHub Actions)

YouTube bloque souvent les IP des runners GitHub (« Sign in to confirm you're not a
bot »). Le mode hybride contourne ça : **download en local**, **transcription/traduction
sur GitHub**.

### Mise en place (une fois)

1. Pousser le repo sur GitHub.
2. Ajouter le secret dans **Settings → Secrets and variables → Actions** :
   - `DEEPL_API_KEY` (et/ou `ANTHROPIC_API_KEY` pour engine=claude).
3. `gh auth login` en local (GitHub CLI).

### Lancer

```bash
chmod +x fetch-audio.sh
./fetch-audio.sh "https://www.youtube.com/watch?v=VOTRE_ID" --model medium --engine deepl
```

Le script enchaîne automatiquement :
1. 📥 télécharge l'audio en local,
2. ☁️ l'envoie comme asset de release GitHub + déclenche le workflow,
3. ⏳ attend la fin du run (transcription + traduction sur GitHub),
4. 📦 récupère `transcript` / `translation` / `bilingual.html` dans **`./output/`**.

Option `--no-wait` : déclenche sans attendre (récupérer plus tard via
`gh run download -n transcription-<RUN_ID> --dir output`).

> Le contenu transite par une **release publique** si le repo est public.
> Pour la confidentialité, passe le repo en privé (2000 min Actions/mois gratuites).

---

## 🎛️ Modèles Whisper — guide de choix

| Modèle | RAM | Précision arabe | Vitesse | CI GitHub |
|---|---|---|---|---|
| `tiny` | ~1 GB | ⭐⭐ | ⚡⚡⚡⚡ | ✅ |
| `base` | ~1 GB | ⭐⭐⭐ | ⚡⚡⚡ | ✅ |
| `small` | ~2 GB | ⭐⭐⭐ | ⚡⚡⚡ | ✅ |
| `medium` | ~5 GB | ⭐⭐⭐⭐ | ⚡⚡ | ✅ (recommandé) |
| `large` | ~10 GB | ⭐⭐⭐⭐⭐ | ⚡ | ⚠️ risque OOM sur runner 7 GB |

> Arabe : **`medium` minimum**. `large` pour les dialectes. Le `tiny` est trop faible
> (erreurs + fragments latins parasites).

---

## 📁 Fichiers générés (`output/`)

```
output/
├── audio.mp3                  # Audio téléchargé
├── transcript.txt             # Transcription (langue source)
├── translation_ar_to_fr.txt   # Traduction
└── bilingual.html             # Document bilingue mis en forme
```

---

## 🔧 Commandes utiles

```bash
# Logs LibreTranslate (si engine=libretranslate)
docker compose logs -f libretranslate

# Nettoyer les sorties
rm -f output/*

# Suivre un run CI
gh run watch
```

---

## 💡 Conseils

- **Arabe littéraire / religieux** : `--model medium --engine claude` donne le meilleur
  résultat (Claude corrige les erreurs de transcription par le contexte).
- **Gratuit et bon** : `--model medium --engine deepl`.
- Les modèles Whisper se téléchargent dans des conteneurs jetables (`--rm`) : **rien ne
  s'accumule** sur le disque (ni en local, ni en CI).
- Filtre VAD (silences) activé par défaut côté transcription.
