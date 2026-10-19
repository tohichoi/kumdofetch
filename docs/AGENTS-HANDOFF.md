# 에이전트 작업 이관 및 프로토콜 지시서 (docs/AGENTS-HANDOFF.md)

kumdofetch의 구조, 배포, 현재 상태를 다음 세션 작업자가 바로 이어받을 수 있게 정리한 문서입니다.

## 1. 프로젝트 정체성

- 대한검도회 중앙·연수원, 경기도검도회 게시판의 신규 공지를 2시간마다 수집해 atd-alert를 통해 텔레그램 `대한검도회` 토픽으로 보내는 알림 봇.
- 실행 환경: Python 3.11, uv, Docker / Docker Compose.
- 에이전트 행동 지침: [AGENTS.md](../AGENTS.md).

## 2. 구조 (SSOT)

| 경로 | 역할 |
|---|---|
| `app/controllers/cli.py` | argparse(`--once`/`--test`/`--notify-empty`), 실행 루프 |
| `app/services/scraper.py` | 게시판 HTML 수집·파싱 |
| `app/services/notifier.py` | atd-alert `POST /v1/messages` 클라이언트 |
| `app/services/state.py` | `old_articles.pickle` 상태 저장·복원 |
| `app/models/article.py` | `Article` 데이터 모델 |
| `app/views/message.py` | HTML 링크 메시지 렌더링·길이 분할 |
| `config/config.toml` | 비밀이 아닌 설정 SSOT (URL·토픽·주기·경로·소스) |
| `config/settings.py` | tomllib + pydantic 로더, `ATD_ALERT_TOKEN` 환경변수 로드 |
| `scripts/run.py` | 엔트리 (`python -m scripts.run`) |
| `scripts/check-code-quality.sh` | 파일·함수 길이 및 시크릿/PII 스캔 |
| `tests/` | 메시지·파서·payload·설정 테스트 |
| `Dockerfile`, `docker-compose.yml` | 컨테이너 빌드·배포 정의 |
| `old_articles.pickle` | 기발송 게시글 키 영속 저장 — git 제외, 컨테이너 볼륨 |
| `convert_event_to_ics.py`, `event-2023-*` | 범위 밖 레거시 일정 변환 도구 |

## 3. 실행 및 배포

- 1회 수집: `uv run python -m scripts.run --once`
- 연결 테스트 발송: `uv run python -m scripts.run --test`
- 기본 실행: `uv run python -m scripts.run` (즉시 1회 후 `interval_seconds` 간격 반복)
- 품질 검사: `uv run ruff check .`, `uv run pytest -q`, `bash scripts/check-code-quality.sh`
- 로컬 재빌드: `docker compose up -d --build`
- 원격(sjx): `ssh sjx "cd /home/x/Workspace/kumdofetch && git pull && docker compose up -d --build"`
- 로그: `docker logs -f kumdofetch`

## 4. 설정·시크릿

- 비밀 아닌 설정은 `config/config.toml`만 수정한다. 코드에 URL·토픽·주기·경로를 하드코딩하지 않는다.
- `ATD_ALERT_TOKEN`은 `/home/x/.config/atd-alert/kumdofetch.env`에서 주입한다. 파일·문서·로그에 값을 남기지 않는다.
- atd-alert 연결: 내부 Docker 네트워크 `sjh2_default`의 `http://atd-alert:8099`.

## 5. 작업 이력

### 2026-10-19 — ATD 규격 전환 및 atd-alert 연동
- 텔레그램 직접 발송(`python-telegram-bot`) 제거, atd-alert HTTP 호출로 전환.
- `app/`·`config/`·`scripts/`·`tests/` 구조로 재편, `main.py`·`tests.py`·`requirements.txt` 제거.
- uv/pyproject 단일 표준, TOML+pydantic 설정, ruff, pytest, 시크릿 스캔 도입.
- Dockerfile uv 기반·비루트(1001) 유지, compose에 `sjh2_default` 외부 네트워크와 `env_file` 추가, `bot.json` 마운트 제거.

### 2026-10-18 — 안정성 보강
- 수집 타임아웃, 사이클 예외 격리, 제목·href HTML 이스케이프 적용.

### 2026-10-05 — Docker화 및 토픽 연동
- 컨테이너화, `sjx` 배포, 슈퍼그룹 토픽 발송 검증.

## 6. 주의사항

- `bot.json`, `old_articles.pickle`은 git 커밋 금지.
- `kumdofetch_bot` 봇 토큰 폐기는 후속 작업이다.
- `convert_event_to_ics.py`는 ATD 전환 범위 밖이며 `ics` 의존성이 선언돼 있지 않다.
