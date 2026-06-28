# Image dédiée du pipeline : ffmpeg + toutes les dépendances Python
# préinstallés, pour éviter de les réinstaller à chaque exécution.
# Les scripts sont montés en volume (./scripts) — pas besoin de rebuild
# quand on les modifie.
FROM python:3.11-slim

# ffmpeg : requis par yt-dlp (extraction/conversion audio)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Dépendances du pipeline (download, transcription, traduction)
RUN pip install --no-cache-dir \
    yt-dlp \
    faster-whisper \
    requests \
    deepl \
    anthropic

WORKDIR /app
