# 프로젝트 명세서 (PROJECT-DESCRIPTION.template.md)

## 1. Goal & Vision (목표 및 비전)

- 프로젝트 개요 및 핵심 해결 과제.
- 공식 가이드 및 문서 링크 목록.

## 2. Domain & System Mission (도메인 및 시스템 핵심 미션)

- 도메인 특화 비즈니스 로직 및 규칙.
- 시스템 주요 요구사항 및 제약조건.

## 2-1. Directory Structure & Layering (필수 기재)

표준 구조(SSOT: `.agents/code-quality.md` §10)를 따르는지, 다르면 사유와 실제 구조를 기재한다. 이 절이 비어 있으면 코드 착수를 개시하지 않는다.

- 백엔드 / 프론트엔드 분리 여부와 배포 단위: 단일 컨테이너 백엔드. 프론트엔드 없음.
- 프론트엔드 형태(웹 / CLI / TUI)와 그에 따른 구조: CLI. `app/controllers`(입력·실행 루프) / `app/services`(수집·발송·상태) / `app/views`(메시지 렌더링)로 계층 분리.
- MVC 레이어(백엔드·웹) 또는 계층 분리(CLI·TUI) 매핑: Controller=`app/controllers/cli.py`, Service=`app/services/*`, View=`app/views/message.py`, Model=`app/models/article.py`.
- 설정 SSOT: `config/config.toml` + `config/settings.py` (tomllib + pydantic) 사용. 시크릿은 `ATD_ALERT_TOKEN` 환경변수만 사용.
- 표준 구조와 다른 부분 및 사유: 없음.
- 구조 예외 대상(편입 프로젝트 등)과 사유: `convert_event_to_ics.py`는 과거 일정 변환용 단발 스크립트로 전환 범위 밖이며 ruff 검사에서 제외한다.

## 3. Workflows & Architecture (핵심 워크플로우 및 체계)

- 시스템 아키텍처 다이어그램 및 데이터 흐름.
- 5-Agent 파이프라인(설계-백엔드-프론트엔드-감사-QA) 연계 구조.
- 핵심 컴포넌트 계층 구조.

## 4. Architecture Roadmap (아키텍처 로드맵)

- 완료된 마일스톤 및 향후 개발 계획.
