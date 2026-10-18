# 에이전트 작업 이관 및 프로토콜 지시서 (docs/AGENTS-HANDOFF.md)

kumdofetch의 구조, 배포, 현재 상태를 다음 세션 작업자가 바로 이어받을 수 있게 정리한 문서입니다.

## 1. 프로젝트 정체성

- 대한검도회 중앙·연수원, 경기도검도회 게시판의 신규 공지를 2시간마다 수집해 텔레그램 슈퍼그룹 토픽으로 보내는 알림 봇.
- 실행 환경: Python 3.11, Docker / Docker Compose.
- 에이전트 행동 지침: [AGENTS.md](../AGENTS.md).

## 2. 구조 (SSOT)

| 파일 | 역할 |
|---|---|
| `main.py` | 크롤링, 메시지 생성, 스케줄러, `/check` 핸들러 통합 진입점 |
| `bot.json` | 봇 토큰, `chat_id(-1004422316688)`, `message_thread_id(10)` — git 제외 |
| `old_articles.pickle` | 기발송 게시글 키 영속 저장 — git 제외, 컨테이너 볼륨 |
| `Dockerfile`, `docker-compose.yml` | 컨테이너 빌드·배포 정의 |
| `tests.py` | 파싱 테스트 (저장소에 없는 `htmls.pickle` 필요) |
| `convert_event_to_ics.py`, `event-2023-*` | 일정 텍스트→ICS 변환 보조 도구 (요구사항에 `ics` 미기재) |

## 3. 실행 및 배포

- 로컬: `uv run python main.py`
- 로컬 재빌드: `docker compose up -d --build`
- 원격(sjx): `ssh sjx "cd /home/x/Workspace/kumdofetch && git pull && docker compose up -d --build"`
- 로그: `docker logs -f kumdofetch`

## 4. 파이프라인

- 지휘: Mike 디렉터
- S.P.I.R.E.: 설계 Leo, 백엔드 Kai, QA Noah
- O.R.B.I.T.: 배포·보안 Chloe

## 5. 작업 이력

### 2026-10-05 — Docker화 및 토픽 연동 (`a684cb8`)
- `message_thread_id` 를 `fetch_articles` / `job_check` / `callback_check` 에 전달.
- `@kumdofetch_bot` 연결, 그룹 초대, 발송 검증 완료.
- `Dockerfile`, `docker-compose.yml`, `.gitignore` 추가, `sjx` 배포 완료.

### 2026-10-18 — 안정성 보강
- `get_html`: `urlopen(..., timeout=30)` 추가 — 사이트 무응답 시 잡 정지 방지.
- `job_check`: 전체 `try/except` + `logging.exception` — 스케줄러 생존 보장.
- `make_message`: `str.maketrans` 대체, stdlib `html.escape` 로 제목·href 이스케이프 — `&` 포함 제목 발송 실패 해결.
- `html` 모듈 import 추가, 미사용 `urlencode`/`quote_plus` import 제거.
- 컨테이너 재빌드 및 원격 배포는 미실행.

## 6. 주의사항

- `bot.json`, `old_articles.pickle` 은 git 커밋 금지 (`.gitignore` 유지).
- `python-telegram-bot==13.15` 는 Python 3.12+ 에서 `imghdr`/`pkg_resources` 문제 → Python 3.11 유지.
- 남은 취약점: 게시판 `table` 인덱스 의존 파싱, pickle 무한 증가, `tests.py` 실질 미동작, `convert_event_to_ics.py` 의 `ics` 의존성 미기재.
