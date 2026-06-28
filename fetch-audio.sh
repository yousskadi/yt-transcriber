#!/usr/bin/env bash
# ============================================================
#  fetch-audio.sh — mode HYBRIDE
#  1. Télécharge l'audio YouTube en local (pas de blocage datacenter)
#  2. L'envoie comme asset de release GitHub
#  3. Déclenche le workflow CI qui transcrit + traduit
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  echo "Usage : ./fetch-audio.sh <youtube_url> [--model medium] [--lang ar] [--target fr] [--engine deepl]"
  exit 0
fi

URL="$1"; shift
MODEL=medium; LANG=ar; TARGET=fr; ENGINE=deepl
while [ $# -gt 0 ]; do
  case "$1" in
    --model)  MODEL="$2";  shift 2 ;;
    --lang)   LANG="$2";   shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --engine) ENGINE="$2"; shift 2 ;;
    *) echo -e "${RED}Option inconnue : $1${NC}"; exit 1 ;;
  esac
done

REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
TAG="audio-input"

echo -e "${CYAN}📥 1/3 — Téléchargement de l'audio en local...${NC}"
mkdir -p output
rm -f output/audio.*
YOUTUBE_URL="$URL" AUDIO_FORMAT=mp3 docker compose run --rm downloader
AUDIO=$(ls output/audio.* | head -1)
echo -e "${GREEN}✅ Audio : $AUDIO${NC}"

echo -e "${CYAN}☁️  2/3 — Envoi sur GitHub (release '$TAG')...${NC}"
gh release create "$TAG" -t "Audio input" \
  -n "Audio d'entrée pour la transcription (écrasé à chaque exécution)" 2>/dev/null || true
gh release upload "$TAG" "$AUDIO" --clobber
ASSET_URL=$(gh release view "$TAG" --json assets \
  --jq '.assets[] | select(.name|startswith("audio")) | .url' | head -1)
echo -e "${GREEN}✅ Asset : $ASSET_URL${NC}"

echo -e "${CYAN}🚀 3/3 — Déclenchement du workflow CI...${NC}"
gh workflow run transcribe-audio.yml \
  -f audio_url="$ASSET_URL" \
  -f model="$MODEL" \
  -f source_language="$LANG" \
  -f target_lang="$TARGET" \
  -f engine="$ENGINE"

echo ""
echo -e "${GREEN}✅ Pipeline lancé sur GitHub.${NC}"
echo -e "   Suivi  : https://github.com/$REPO/actions"
echo -e "   CLI    : ${YELLOW}gh run watch${NC}"
echo -e "   Résultat : onglet Actions → run → section ${YELLOW}Artifacts${NC}"
