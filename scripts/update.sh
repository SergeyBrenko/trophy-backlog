#!/bin/sh
# Обновляет статистику со stratege и публикует сайт без участия Claude:
#   ./scripts/update.sh
# 1) профиль владельца: кубки, игры, процент завершения (sync_profile.py);
# 2) игры из «Списка» и «Кандидатов»: трофеи, сложность и длительность, время платины, владельцы и доля платин
#    (fetch_stratege.py --stats; трофейные листы перечитываются, только если изменились);
# 3) пересчёт производных полей (recalc.py), commit и push.
# Итоговую оценку, описания и DLC-карточки скрипт не трогает: это делает полная актуализация.
# Занимает 10–15 минут: stratege ограничивает частоту запросов.
set -eu
cd "$(dirname "$0")/.."
git pull --rebase --autostash --quiet
python3 scripts/sync_profile.py || echo "!! профиль не обновлён (ошибка выше), продолжаю с играми"
python3 scripts/fetch_stratege.py --stats
python3 scripts/recalc.py
git add data img
if git diff --cached --quiet; then
  echo "Изменений нет"
  exit 0
fi
git commit --quiet -m "Статистика со stratege: $(date +%Y-%m-%d)"
git push --quiet
echo "Опубликовано: https://sergeybrenko.github.io/trophy-backlog/"
