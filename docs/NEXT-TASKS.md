# 다음 작업

- `kumdofetch_bot` 봇 토큰 폐기 (BotFather). `bot.json`의 토큰은 더 이상 사용하지 않는다.
- `bot.json` 파일 제거 시점 결정 (현재 미사용, git 제외, 컨테이너 마운트 없음).
- href 검증 강화: 스킴 없는 `//host` 형태(프로토콜 상대 URL)를 차단하고, 상대 경로는 선행 단일 `/`만 허용.
- `scripts/check-code-quality.sh` 시크릿 스캔에서 `.agents/`, `.claude/` 제외 추가.
- `app/services/notifier.py`의 `MESSAGES_PATH`, `API_KEY_HEADER`를 config로 옮길지 결정 (현재 계획서상 코드 상수 유지).
