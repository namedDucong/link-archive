# Link Archive

Link Archive는 사용자가 저장한 웹 링크를 사용자 계정 단위로 관리하고, 각 링크에 대한 메타데이터 크롤링 작업을 큐 형태로 처리하기 위한 FastAPI 기반 백엔드 프로젝트입니다.

현재 저장소는 프론트엔드보다 **백엔드 API, 인증, 데이터베이스 모델링, 링크 저장/관리, 크롤링 작업 처리 흐름**에 초점을 두고 있습니다.

## 주요 기능

### 인증 및 사용자 관리

- 회원가입 API
- 로그인 API
- JWT access token 발급
- 현재 로그인한 사용자 조회
- 인증이 필요한 API에서 `Authorization: Bearer <token>` 기반 사용자 식별
- 사용자별 리소스 접근 제어

### 링크 저장 및 관리

- 로그인한 사용자의 링크 저장
- 저장된 링크 목록 조회
- 저장된 링크 상세 조회
- 링크 메모 수정
- 링크 상태 변경
  - `active`
  - `archived`
  - `deleted`
- 링크 삭제
- 링크 재크롤링 작업 생성
- 사용자별 중복 URL 저장 방지

### 크롤링 작업 관리

- 링크 저장 시 `crawl_jobs` 작업 자동 생성
- queued 상태의 크롤링 작업 1개 처리
- 크롤링 작업 목록 조회
- 크롤링 상태 필터링
- 크롤링 성공/실패 상태 저장
- 실패 시 에러 메시지 저장

### 메타데이터 추출

현재 크롤러는 URL에 접속한 뒤 HTML을 파싱하여 다음 정보를 추출합니다.

- canonical URL
- title
- description
- domain
- author
- page language

메타데이터 추출에는 `httpx`와 `BeautifulSoup`를 사용합니다.

### 태그 관리

- 로그인한 사용자의 태그 생성
- 사용자 태그 목록 조회
- 저장된 링크에 태그 연결
- 저장된 링크의 태그 목록 조회
- 저장된 링크에서 태그 제거
- 사용자별 태그 중복 방지

### 컬렉션 관리

- 로그인한 사용자의 컬렉션 생성
- 컬렉션 목록 조회
- 컬렉션 상세 조회
- 컬렉션 이름/설명 수정
- 컬렉션 삭제
- 컬렉션에 저장 링크 추가
- 컬렉션에 포함된 링크 목록 조회
- 컬렉션에서 저장 링크 제거
- 사용자별 컬렉션 중복 방지

## 기술 스택

- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy
- MySQL / PyMySQL
- Pydantic
- python-jose
- passlib[bcrypt]
- httpx
- BeautifulSoup4
- python-dotenv
- uv

## 프로젝트 구조

```text
link-archive/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── deps.py
│   ├── models.py
│   ├── schemas.py
│   ├── utils.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── saved_links.py
│   │   ├── crawl_jobs.py
│   │   ├── tags.py
│   │   └── collections.py
│   └── services/
│       ├── auth.py
│       ├── crawler.py
│       └── crawl_job_runner.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## 실행 흐름

### 1. 사용자 인증

```text
회원가입 또는 로그인
→ JWT access token 발급
→ 이후 인증이 필요한 API 요청 시 Authorization header에 token 포함
```

### 2. 링크 저장

```text
POST /api/me/links
→ saved_links에 원본 URL과 메모 저장
→ crawl_jobs에 queued 상태의 크롤링 작업 생성
→ 사용자에게 저장된 링크 정보 반환
```

### 3. 크롤링 처리

```text
POST /api/crawl-jobs/run-once
→ queued 상태의 crawl job 1개 조회
→ saved_links.original_url 접속
→ HTML 메타데이터 추출
→ crawled_pages에 메타데이터 저장 또는 기존 page 재사용
→ saved_links.page_id 연결
→ saved_links.crawl_status, crawl_jobs.status 업데이트
```

## 데이터베이스 모델

### users

사용자 계정 정보를 저장합니다.

| 필드 | 설명 |
|---|---|
| id | 사용자 UUID |
| email | 사용자 이메일 |
| name | 사용자 이름 |
| password_hash | bcrypt 기반 비밀번호 해시 |
| created_at | 생성 시각 |

### saved_links

사용자가 저장한 링크를 저장합니다.

| 필드 | 설명 |
|---|---|
| id | 저장 링크 UUID |
| user_id | 링크를 저장한 사용자 ID |
| page_id | 연결된 crawled page ID |
| original_url | 사용자가 저장한 원본 URL |
| original_url_hash | URL 중복 확인용 hash |
| memo | 사용자 메모 |
| status | 링크 상태 |
| crawl_status | 크롤링 상태 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |
| archived_at | 아카이브 처리 시각 |

### crawled_pages

크롤링을 통해 추출한 페이지 메타데이터를 저장합니다.

| 필드 | 설명 |
|---|---|
| id | 크롤링 페이지 UUID |
| canonical_url | canonical URL |
| canonical_url_hash | canonical URL hash |
| title | 페이지 제목 |
| description | 페이지 설명 |
| domain | 도메인 |
| author | 작성자 |
| published_at | 발행 시각 |
| page_language | 페이지 언어 |
| raw_html_path | 원본 HTML 저장 경로 |
| extracted_text_path | 추출 텍스트 저장 경로 |
| screenshot_path | 스크린샷 저장 경로 |
| thumbnail_path | 썸네일 저장 경로 |
| crawl_status | 페이지 크롤링 상태 |
| crawled_at | 크롤링 완료 시각 |
| created_at | 생성 시각 |
| updated_at | 수정 시각 |

### crawl_jobs

링크 크롤링 작업 큐를 관리합니다.

| 필드 | 설명 |
|---|---|
| id | 크롤링 작업 UUID |
| saved_link_id | 대상 저장 링크 ID |
| status | 작업 상태 |
| attempt_count | 시도 횟수 |
| last_error | 마지막 에러 메시지 |
| created_at | 생성 시각 |
| started_at | 시작 시각 |
| finished_at | 종료 시각 |

### tags / saved_link_tags

사용자별 태그와 저장 링크-태그 관계를 관리합니다.

### collections / collection_saved_links

사용자별 컬렉션과 컬렉션-저장 링크 관계를 관리합니다.

## API 개요

### Health Check

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| GET | `/api/health` | 서버 상태 확인 | X |

### Auth

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/auth/signup` | 회원가입 및 token 발급 | X |
| POST | `/api/auth/login` | 로그인 및 token 발급 | X |
| GET | `/api/me` | 현재 로그인한 사용자 조회 | O |

### Users

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/users` | 테스트용 사용자 생성 | X |
| GET | `/api/users` | 테스트용 사용자 목록 조회 | X |

### Saved Links

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/me/links` | 현재 사용자 링크 저장 | O |
| GET | `/api/me/links` | 현재 사용자 링크 목록 조회 | O |
| GET | `/api/saved-links/{saved_link_id}` | 저장 링크 상세 조회 | O |
| PATCH | `/api/saved-links/{saved_link_id}` | 저장 링크 수정 | O |
| DELETE | `/api/saved-links/{saved_link_id}` | 저장 링크 삭제 | O |
| POST | `/api/saved-links/{saved_link_id}/recrawl` | 재크롤링 작업 생성 | O |

### Crawl Jobs

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/crawl-jobs/run-once` | queued 크롤링 작업 1개 처리 | X |
| GET | `/api/crawl-jobs` | 크롤링 작업 목록 조회 | X |

### Tags

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/me/tags` | 현재 사용자 태그 생성 | O |
| GET | `/api/me/tags` | 현재 사용자 태그 목록 조회 | O |
| POST | `/api/saved-links/{saved_link_id}/tags` | 저장 링크에 태그 연결 | O |
| GET | `/api/saved-links/{saved_link_id}/tags` | 저장 링크의 태그 조회 | O |
| DELETE | `/api/saved-links/{saved_link_id}/tags/{tag_id}` | 저장 링크에서 태그 제거 | O |

### Collections

| Method | Endpoint | 설명 | 인증 |
|---|---|---|---|
| POST | `/api/me/collections` | 현재 사용자 컬렉션 생성 | O |
| GET | `/api/me/collections` | 현재 사용자 컬렉션 목록 조회 | O |
| GET | `/api/collections/{collection_id}` | 컬렉션 상세 조회 | O |
| PATCH | `/api/collections/{collection_id}` | 컬렉션 수정 | O |
| DELETE | `/api/collections/{collection_id}` | 컬렉션 삭제 | O |
| POST | `/api/collections/{collection_id}/links/{saved_link_id}` | 컬렉션에 링크 추가 | O |
| GET | `/api/collections/{collection_id}/links` | 컬렉션 내 링크 조회 | O |
| DELETE | `/api/collections/{collection_id}/links/{saved_link_id}` | 컬렉션에서 링크 제거 | O |

## 환경 변수

프로젝트 루트에 `.env` 파일을 생성하고 아래 값을 설정합니다.

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DB_NAME
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## 로컬 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/namedDucong/link-archive.git
cd link-archive
```

### 2. 가상환경 생성 및 패키지 설치

```bash
uv venv --python 3.11
source .venv/bin/activate
uv sync
```

Windows PowerShell 환경에서는 다음과 같이 활성화할 수 있습니다.

```powershell
.venv\Scripts\Activate.ps1
uv sync
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env.example` 파일이 없다면 위의 환경 변수 예시를 참고하여 `.env` 파일을 직접 생성합니다.

### 4. 서버 실행

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

## 사용 예시

### 회원가입

```bash
curl -X POST http://127.0.0.1:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "Yewon"
  }'
```

### 로그인

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

응답으로 받은 `access_token`을 이후 요청의 `Authorization` header에 사용합니다.

```text
Authorization: Bearer <access_token>
```

### 링크 저장

```bash
curl -X POST http://127.0.0.1:8000/api/me/links \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "original_url": "https://example.com/article",
    "memo": "나중에 읽을 글"
  }'
```

### 내 링크 목록 조회

```bash
curl -X GET "http://127.0.0.1:8000/api/me/links?limit=50" \
  -H "Authorization: Bearer <access_token>"
```

### 크롤링 작업 1개 실행

```bash
curl -X POST http://127.0.0.1:8000/api/crawl-jobs/run-once
```

### 태그 생성

```bash
curl -X POST http://127.0.0.1:8000/api/me/tags \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name": "research"
  }'
```

### 컬렉션 생성

```bash
curl -X POST http://127.0.0.1:8000/api/me/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "name": "읽을 논문",
    "description": "나중에 읽을 논문과 자료 모음"
  }'
```

## 현재 구현 상태

현재 구현된 범위는 다음과 같습니다.

- FastAPI 앱 구성
- MySQL 연동용 SQLAlchemy 설정
- SQLAlchemy ORM 모델 정의
- JWT 기반 회원가입/로그인
- 현재 사용자 조회
- 사용자별 링크 저장/조회/수정/삭제
- 링크 저장 시 crawl job 자동 생성
- 크롤링 job 수동 실행 API
- HTML 메타데이터 추출 로직
- 사용자별 태그 관리
- 저장 링크-태그 연결 관리
- 사용자별 컬렉션 관리
- 컬렉션-저장 링크 연결 관리
- CORS 설정

## 향후 개선 계획

- 크롤링 작업을 API 요청이 아닌 별도 worker 프로세스로 분리
- 주기적으로 queued crawl job을 처리하는 background worker 구현
- Alembic 기반 DB migration 정리
- 크롤링 실패 링크 재시도 정책 개선
- Open Graph image, favicon 등 추가 메타데이터 추출
- raw HTML, extracted text, screenshot 저장 로직 구현
- 검색 기능 추가
- 태그/컬렉션 기반 필터링 API 확장
- 프론트엔드 또는 브라우저 확장 프로그램 연동
- 배포 환경에서 Nginx, systemd, HTTPS 구성

## 개발 메모

현재 일부 API는 테스트 또는 이전 구현 흐름을 위해 남아 있습니다.

- `/api/users` 계열 API는 테스트용 사용자 생성/조회 성격이 강합니다.
- 실제 사용자별 리소스 접근은 `/api/me/...` 계열과 JWT 인증을 기준으로 사용하는 것이 적절합니다.
- `/api/crawl-jobs/run-once`는 개발/테스트용 수동 실행 API이며, 운영 환경에서는 별도 worker로 분리하는 것이 적절합니다.
