# 에이전트 작업 이관 및 프로토콜 지시서 (docs/AGENTS-HANDOFF.md)

본 지시서는 kumdofetch 프로젝트의 아키텍처, 텔레그램 슈퍼그룹 토픽 연동, Docker 배포 현황 및 인수인계 지침을 정리한 문서입니다.

## 1. 프로젝트 정체성 및 기본 원칙

- **목적**: 대한검도회 및 산하 기관 게시판의 신규 공지를 자동 수집하여 텔레그램 슈퍼그룹 토픽으로 브로드캐스팅하는 알림 봇.
- **에이전트 행동 지침**: [AGENTS.md](../AGENTS.md) 참조.
- **실행 환경**: Python 3.11, Docker, Docker Compose (Linux).

## 2. 프로젝트 아키텍처 및 단일 원천 (SSOT)

### 디렉토리 구조
- `main.py`: 게시판 크롤링, 메시지 생성, 텔레그램 스케줄러 및 명령어 핸들러 통합 진입점.
- `bot.json`: 텔레그램 봇 토큰 및 대상 슈퍼그룹/토픽 설정 (`.gitignore` 대상).
- `old_articles.pickle`: 기발송 게시물 ID 영속 저장 파일.
- `Dockerfile` / `docker-compose.yml`: 컨테이너 빌드 및 런타임 배포 정의.
- `PROJECT-DESCRIPTION.md`: 프로젝트 명세서.

## 3. 실행 및 배포 프로토콜

- **로컬 가상환경 실행**:
  ```bash
  uv run python main.py
  ```
- **도커 빌드 및 배포 (sjx 원격 서버)**:
  ```bash
  ssh sjx "cd /home/x/Workspace/kumdofetch && git pull && docker compose up -d --build"
  ```
- **로그 확인**:
  ```bash
  ssh sjx "docker logs -f kumdofetch"
  ```

## 4. 파이프라인 및 전문 분과 지침

- **지휘 및 최종 승인**: Mike 디렉터 (Managing Director)
- **S.P.I.R.E. 코어 엔지니어링 랩**:
  - 설계 (Leo): 워크플로우 명세 및 핸드오프 문서화.
  - 백엔드 (Kai): 텔레그램 토픽(`message_thread_id`) 발송 로직 및 에러 처리.
  - QA/테스트 (Noah): 메시지 발송 API 및 크롤링 파이프라인 검증.
- **O.R.B.I.T. DevOps 랩**:
  - 배포 & 보안 (Chloe): Docker 컨테이너 패키징 및 원격 서버(`sjx`) 배포.

## 5. 현재 작업 상태 및 진행 이력 (2026-10-05)

- **최근 완료 커밋**: `a684cb8` (`feat: dockerize kumdofetch with topic support`)
- **주요 해결 사항**:
  1. **텔레그램 포럼 슈퍼그룹 토픽 연동**:
     - `https://t.me/c/4422316688/10/141` 규격에 맞춰 `chat_id: -1004422316688`, `message_thread_id: 10` 지원.
     - `fetch_articles`, `job_check`, `callback_check` 함수에 `message_thread_id` 인자 전달 구현.
  2. **kumdofetch 전용 봇 연결**:
     - `@kumdofetch_bot` 토큰 등록 및 그룹 초대 완료, 발송 검증 성공.
  3. **브랜치 정리**:
     - 과거 분기되었던 임시 `sj_index_scrapper` 브랜치 삭제 및 `main` 브랜치 최신화.
  4. **도커라이징 및 원격 서버 배포**:
     - `Dockerfile`, `docker-compose.yml`, `.gitignore` 생성.
     - 의존성 경량화(`requirements.txt`: `setuptools<70`으로 `pkg_resources` 호환 보장).
     - `sjx` 서버(`/home/x/Workspace/kumdofetch`)로 코드 및 `bot.json` 동기화 후 `docker compose up -d --build` 실행 완료 (컨테이너 정상 동작 중).

## 6. 다음 세션 작업자 행동 지침

1. **원격 컨테이너 상태 모니터링**:
   - `ssh sjx "docker ps --filter name=kumdofetch"`로 컨테이너 상태 확인.
   - 2시간 주기로 게시판 공지가 정상 체크되는지 `docker logs` 확인.
2. **주의사항**:
   - `bot.json` 및 `old_articles.pickle`은 민감정보 및 운영 상태 데이터이므로 Git 커밋에 포함하지 말 것 (`.gitignore` 유지).
   - 레거시 `python-telegram-bot` 13.15는 Python 3.12+에서 `imghdr`/`pkg_resources` 이슈가 있으므로 반드시 Python 3.11 환경 유지할 것.
