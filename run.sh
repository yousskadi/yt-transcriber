#!/usr/bin/env bash
# ============================================================
#  run.sh — Helper CLI pour le pipeline YouTube
# ============================================================
#  Usage :
#    ./run.sh "https://youtube.com/watch?v=..."
#    ./run.sh "URL" --model large --lang ar --target fr
#    ./run.sh --translate-only          (si audio déjà téléchargé)
#    ./run.sh --transcribe-only         (si audio déjà téléchargé)
# ============================================================

set -euo pipefail

# Couleurs
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

print_header() {
  echo -e "\n${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${CYAN}  🎬  YouTube Transcription & Translation Pipeline${NC}"
  echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_usage() {
  echo -e "${BOLD}Usage :${NC}"
  echo -e "  ${GREEN}./run.sh${NC} <youtube_url> [options]"
  echo -e "  ${GREEN}./run.sh${NC} --translate-only"
  echo -e "  ${GREEN}./run.sh${NC} --transcribe-only"
  echo ""
  echo -e "${BOLD}Options :${NC}"
  echo -e "  ${YELLOW}--model${NC}     <tiny|base|small|medium|large>   (défaut: medium)"
  echo -e "  ${YELLOW}--lang${NC}      <code_iso>   langue source         (défaut: ar)"
  echo -e "  ${YELLOW}--target${NC}    <code_iso>   langue cible          (défaut: fr)"
  echo -e "  ${YELLOW}--format${NC}    <txt|srt|vtt|json>                (défaut: txt)"
  echo -e "  ${YELLOW}--engine${NC}    <libretranslate|deepl>            (défaut: libretranslate)"
  echo ""
  echo -e "${BOLD}Exemples :${NC}"
  echo -e "  ./run.sh 'https://youtube.com/watch?v=abc123'"
  echo -e "  ./run.sh 'https://youtube.com/watch?v=abc123' --model large --target en"
  echo -e "  ./run.sh --translate-only --target en"
}

# Vérifier .env
if [ ! -f ".env" ]; then
  echo -e "${RED}❌ Fichier .env manquant. Copiez .env.example en .env${NC}"
  exit 1
fi

# Charger .env
set -a; source .env; set +a

# Valeurs par défaut
MODE="pipeline"
MODEL="${WHISPER_MODEL:-medium}"
LANG="${SOURCE_LANGUAGE:-ar}"
TARGET="${TARGET_LANG:-fr}"
FORMAT="${OUTPUT_FORMAT:-txt}"
ENGINE="${TRANSLATE_ENGINE:-libretranslate}"

# Parser les arguments
if [ $# -eq 0 ]; then
  print_usage; exit 0
fi

# Premier argument = URL ou flag
if [[ "$1" != --* ]]; then
  export YOUTUBE_URL="$1"
  shift
fi

# Options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)    MODEL="$2"; shift 2 ;;
    --lang)     LANG="$2"; shift 2 ;;
    --target)   TARGET="$2"; shift 2 ;;
    --format)   FORMAT="$2"; shift 2 ;;
    --engine)   ENGINE="$2"; shift 2 ;;
    --pipeline)         MODE="pipeline"; shift ;;
    --transcribe-only)  MODE="transcribe"; shift ;;
    --translate-only)   MODE="translate"; shift ;;
    --help|-h)  print_usage; exit 0 ;;
    *)          echo -e "${RED}Option inconnue : $1${NC}"; print_usage; exit 1 ;;
  esac
done

# Exporter les variables
export WHISPER_MODEL="$MODEL"
export SOURCE_LANGUAGE="$LANG"
export TARGET_LANG="$TARGET"
export OUTPUT_FORMAT="$FORMAT"
export TRANSLATE_ENGINE="$ENGINE"

# Créer le dossier output
mkdir -p output

print_header

echo -e "${BOLD}Configuration :${NC}"
echo -e "  URL      : ${CYAN}${YOUTUBE_URL:-<non définie>}${NC}"
echo -e "  Modèle   : ${CYAN}${MODEL}${NC}"
echo -e "  Langue   : ${CYAN}${LANG} → ${TARGET}${NC}"
echo -e "  Format   : ${CYAN}${FORMAT}${NC}"
echo -e "  Moteur   : ${CYAN}${ENGINE}${NC}"
echo -e "  Mode     : ${CYAN}${MODE}${NC}"
echo ""

case "$MODE" in
  pipeline)
    if [ -z "${YOUTUBE_URL:-}" ]; then
      echo -e "${RED}❌ YOUTUBE_URL manquant. Passez l'URL en premier argument.${NC}"
      exit 1
    fi
    echo -e "${YELLOW}🚀 Démarrage du pipeline complet...${NC}\n"
    if [ "$ENGINE" = "libretranslate" ]; then
      docker compose up -d libretranslate
    fi
    docker compose run --rm pipeline
    ;;
  transcribe)
    echo -e "${YELLOW}🎙️  Transcription uniquement...${NC}\n"
    docker compose run --rm --no-deps transcribe
    ;;
  translate)
    echo -e "${YELLOW}🌍 Traduction uniquement...${NC}\n"
    if [ "$ENGINE" = "libretranslate" ]; then
      docker compose up -d libretranslate
      docker compose run --rm translate
    else
      docker compose run --rm --no-deps translate
    fi
    ;;
esac

echo -e "\n${GREEN}${BOLD}✅ Terminé ! Consultez le dossier ./output/${NC}"
ls -lh output/ 2>/dev/null || true