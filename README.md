[README.md](https://github.com/user-attachments/files/28459867/README.md)
# Link Archive

개인 링크 아카이빙 및 검색/관리 시스템입니다.  
사용자가 저장하고 싶은 웹 링크를 한곳에 모아 관리하고, 각 링크의 메타데이터를 자동으로 수집하여 이후 검색, 태그 관리, 컬렉션 구성, 요약 및 추천 기능으로 확장하는 것을 목표로 합니다.

## 1. Project Overview

일상적으로 저장하는 링크는 블로그, 뉴스, 유튜브, 쇼핑몰, SNS, 문서 등 다양한 출처에 흩어져 있습니다.  
본 프로젝트는 사용자가 여러 플랫폼에서 발견한 링크를 하나의 저장소에 모으고, 단순 URL 저장을 넘어 제목, 설명, 썸네일, 도메인, 콘텐츠 타입 등의 메타데이터를 함께 관리할 수 있도록 설계되었습니다.

현재 프로젝트의 핵심 목표는 다음과 같습니다.

- 사용자가 링크를 저장할 수 있는 백엔드 API 구현
- 저장된 링크의 메타데이터 자동 수집 구조 설계
- 링크 저장과 크롤링 작업을 분리한 안정적인 처리 흐름 구축
- 태그 및 컬렉션 기반 링크 관리 기능 확장
- 프론트엔드와 백엔드가 연동 가능한 API 구조 정리
- GCP 기반 배포 환경 구성

## 2. Main Features

### Implemented / In Progress

- 링크 저장 API
- 저장된 링크 목록 조회 API
- 링크 정보 수정 API
- 링크 상태 관리
- 크롤링 작업 상태 관리 구조
- MySQL 기반 데이터베이스 스키마 설계
- FastAPI 기반 백엔드 서버 구성
- React/Vite 프론트엔드와 연동 가능한 API 구조 설계
- GCP VM 기반 배포 환경 구성 검토

### Planned

- 링크 메타데이터 자동 추출
  - title
  - description
  - thumbnail
  - favicon
  - canonical URL
  - domain
  - content type
- 태그 기능
- 컬렉션 기능
- 크롤링 worker 분리
- 자연어 검색
- LLM 기반 링크 요약
- 추천 기능
- Chrome Extension을 통한 링크 저장
- 모바일 앱 확장

## 3. Tech Stack

### Frontend

- React
- Vite
- JavaScript / TypeScript
- Environment variables using `.env.local`

### Backend

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Uvicorn

### Database

- MySQL
- Google Cloud SQL

### Infrastructure

- Google Cloud Platform VM
- Nginx
- systemd
- Static external IP
- Cloud SQL

### Development Tools

- Git / GitHub
- VS Code
- uv
- cURL
- MySQL client

## 4. System Architecture

```text
User
  |
  v
Frontend Web App
  |
  v
FastAPI Backend Server
  |
  +----------------------+
  |                      |
  v                      v
MySQL / Cloud SQL     Crawl Job Queue
                         |
                         v
                    Crawl Worker
                         |
                         v
              Metadata Extraction
                         |
                         v
                  Update Link Data
```

## 5. Link Saving Workflow

링크 저장 과정은 사용자의 저장 요청과 메타데이터 크롤링 작업을 분리하는 방식으로 설계되었습니다.

```text
1. 사용자가 URL 저장 요청
2. 백엔드가 URL을 우선 DB에 저장
3. 링크 상태를 pending 또는 queued로 설정
4. 크롤링 작업 생성
5. worker가 URL에 접근하여 메타데이터 추출
6. 추출 성공 시 링크 상태를 success 또는 done으로 변경
7. 실패 시 failed 상태로 저장하고 원본 URL은 유지
```

이 구조를 사용하는 이유는 크롤링 실패가 링크 저장 실패로 이어지지 않도록 하기 위함입니다.  
사용자의 저장 요청은 빠르게 처리하고, 메타데이터 추출은 별도의 작업으로 관리합니다.

## 6. Database Design

현재 데이터베이스는 링크 저장, 크롤링 상태 관리, 태그 및 컬렉션 확장을 고려하여 설계하고 있습니다.

### links

| Field | Description |
|---|---|
| id | 링크 고유 ID |
| user_id | 사용자 ID |
| original_url | 사용자가 입력한 원본 URL |
| canonical_url | 정규화된 URL |
| url_hash | 중복 확인용 URL 해시 |
| title | 링크 제목 |
| description | 링크 설명 |
| domain | 도메인 |
| thumbnail_url | 썸네일 URL |
| favicon_url | 파비콘 URL |
| content_type | 콘텐츠 타입 |
| status | 링크 처리 상태 |
| crawl_status | 크롤링 상태 |
| memo | 사용자 메모 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

### crawl_jobs

| Field | Description |
|---|---|
| id | 크롤링 작업 ID |
| link_id | 대상 링크 ID |
| status | 작업 상태 |
| error_message | 실패 시 에러 메시지 |
| retry_count | 재시도 횟수 |
| created_at | 생성 시간 |
| updated_at | 수정 시간 |

### tags

| Field | Description |
|---|---|
| id | 태그 ID |
| name | 태그 이름 |
| created_at | 생성 시간 |

### collections

| Field | Description |
|---|---|
| id | 컬렉션 ID |
| name | 컬렉션 이름 |
| description | 컬렉션 설명 |
| created_at | 생성 시간 |

## 7. API Design

현재 FastAPI 기반으로 링크 저장 및 조회 API를 구성하고 있습니다.

### Link API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/links` | 새 링크 저장 |
| GET | `/api/links` | 저장된 링크 목록 조회 |
| GET | `/api/links/{link_id}` | 특정 링크 상세 조회 |
| PATCH | `/api/links/{link_id}` | 링크 정보 수정 |
| DELETE | `/api/links/{link_id}` | 링크 삭제 |

### Crawl Job API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/crawl-jobs` | 크롤링 작업 생성 |
| GET | `/api/crawl-jobs` | 크롤링 작업 목록 조회 |
| GET | `/api/crawl-jobs/{job_id}` | 특정 크롤링 작업 조회 |

## 8. Example API Request

### Create Link

```bash
curl -X POST http://127.0.0.1:8000/api/links \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com/article",
    "memo": "나중에 읽을 글"
  }'
```

### Example Response

```json
{
  "id": "link_id",
  "original_url": "https://example.com/article",
  "title": null,
  "description": null,
  "status": "pending",
  "crawl_status": "queued",
  "created_at": "2026-06-01T00:00:00"
}
```

## 9. Environment Variables

### Backend

`.env`

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DB_NAME
APP_ENV=development
```

### Frontend

`.env.local`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

배포 환경에서는 `VITE_API_BASE_URL`을 실제 API 서버 주소로 변경해야 합니다.

## 10. Local Development

### Backend Setup

```bash
cd backend

uv venv --python 3.11
source .venv/bin/activate

uv pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

## 11. Deployment Plan

현재 배포는 GCP VM 기반으로 구성하는 것을 목표로 하고 있습니다.

배포 시 고려하는 구성은 다음과 같습니다.

- GCP VM에서 FastAPI 서버 실행
- Nginx를 reverse proxy로 사용
- systemd를 통해 FastAPI 서버를 서비스로 관리
- Cloud SQL을 MySQL 데이터베이스로 사용
- 외부 IP를 정적 IP로 설정
- 프론트엔드와 백엔드의 API base URL 고정
- HTTPS 적용 검토

## 12. Technical Issues and Risks

현재 개발 중 확인한 주요 기술적 이슈는 다음과 같습니다.

### 1. Frontend-Backend API Integration

프론트엔드와 백엔드의 API 경로, 요청 형식, 응답 형식이 일치해야 합니다.  
이를 위해 API endpoint와 request/response schema를 문서화하고, 프론트엔드에서는 `VITE_API_BASE_URL`을 통해 API 주소를 관리합니다.

### 2. GCP VM External IP

GCP VM의 외부 IP가 임시 IP일 경우 VM 재시작 시 주소가 변경될 수 있습니다.  
이를 방지하기 위해 정적 외부 IP를 사용하는 방향으로 설정합니다.

### 3. Database Schema Management

개발 중 DB 스키마가 계속 변경될 수 있으므로 SQL 파일 또는 migration 도구를 통해 변경 이력을 관리할 필요가 있습니다.

### 4. Metadata Crawling Instability

웹사이트마다 HTML 구조와 메타데이터 제공 방식이 다르기 때문에 모든 링크에서 안정적으로 title, description, thumbnail을 추출하기 어렵습니다.  
따라서 크롤링 실패 상태를 별도로 저장하고, 원본 URL은 항상 유지하는 방식으로 처리합니다.

### 5. Background Job Processing

크롤링과 메타데이터 추출을 API 요청 안에서 직접 처리하면 응답 시간이 길어질 수 있습니다.  
따라서 링크 저장과 크롤링 작업을 분리하고, 추후 별도 worker 프로세스로 확장할 계획입니다.

## 13. Future Work

향후 개발 계획은 다음과 같습니다.

- 태그 API 구현
- 컬렉션 API 구현
- 크롤링 worker 분리
- 메타데이터 추출 정확도 개선
- 링크 중복 저장 방지
- 자연어 검색 기능 추가
- LLM 기반 요약 기능 추가
- 사용자별 링크 관리 기능 추가
- Chrome Extension과 API 연동
- 배포 자동화 및 운영 모니터링 구축

## 14. Project Status

현재 프로젝트는 백엔드 API, 데이터베이스 구조, 크롤링 처리 흐름, GCP 배포 환경을 중심으로 개발 중입니다.  
MVP 단계에서는 사용자가 링크를 저장하고, 저장된 링크를 조회하며, 이후 메타데이터 수집과 태그/컬렉션 관리 기능을 확장하는 것을 목표로 합니다.
