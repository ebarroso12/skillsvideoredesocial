#!/usr/bin/env bash
# Instala as skills "video-caricatura-social" e "video-rabisco-lapis" no Claude Code, Codex e/ou outras pastas de skills.
# Uso:
#   ./install.sh                  # instala no Claude Code (~/.claude/skills)
#   ./install.sh --target codex   # Codex (~/.codex/skills)
#   ./install.sh --target agents  # pasta generica ~/.agents/skills
#   ./install.sh --target all     # os tres acima
#   ./install.sh --dest /caminho  # pasta de skills personalizada
#   ./install.sh --project        # na pasta .claude/skills do projeto atual
set -euo pipefail

SKILLS=("video-caricatura-social" "video-rabisco-lapis")
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for SKILL in "${SKILLS[@]}"; do
  [ -f "$HERE/skills/$SKILL/SKILL.md" ] || { echo "ERRO: $HERE/skills/$SKILL/SKILL.md nao encontrado. Rode o script dentro do repositorio clonado." >&2; exit 1; }
done

targets=()
while [ $# -gt 0 ]; do
  case "$1" in
    --target) shift
      case "${1:-claude}" in
        claude) targets+=("$HOME/.claude/skills");;
        codex)  targets+=("$HOME/.codex/skills");;
        agents) targets+=("$HOME/.agents/skills");;
        all)    targets+=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills");;
        *) echo "Alvo desconhecido: $1 (use claude, codex, agents ou all)" >&2; exit 1;;
      esac;;
    --dest) shift; targets+=("${1:?informe a pasta}");;
    --project) targets+=("$PWD/.claude/skills");;
    -h|--help) sed -n '2,10p' "$0"; exit 0;;
    *) echo "Opcao desconhecida: $1" >&2; exit 1;;
  esac
  shift
done
[ ${#targets[@]} -gt 0 ] || targets=("$HOME/.claude/skills")

for dest in "${targets[@]}"; do
  mkdir -p "$dest"
  for SKILL in "${SKILLS[@]}"; do
    rm -rf "$dest/$SKILL"
    cp -R "$HERE/skills/$SKILL" "$dest/$SKILL"
    find "$dest/$SKILL" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
    echo "Instalada em: $dest/$SKILL"
  done
done

echo
echo "Verificando requisitos..."
command -v python3 >/dev/null || echo "  FALTA: python3"
python3 -c "import PIL" 2>/dev/null || echo "  FALTA: Pillow  ->  pip install pillow"
python3 -c "import numpy, scipy, skimage, cv2" 2>/dev/null || echo "  FALTA (skill rabisco): pip install numpy scipy scikit-image opencv-python-headless"
command -v ffmpeg  >/dev/null || echo "  FALTA: ffmpeg  ->  https://ffmpeg.org/download.html"
echo "Pronto. Abra uma nova sessao e peca, por exemplo: 'Crie um video caricatura de 45 segundos sobre solidao' ou 'Crie um video rabisco a lapis preto e branco sobre ansiedade'."
