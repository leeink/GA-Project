# 🚀 글로벌냉동식품 서비스

냉동식품 전문 온라인 쇼핑몰입니다.
데이터베이스를 활용해 상품·재고·주문 데이터를 통합 관리하며,
RPA를 통해 유통기한 임박 재고를 자동으로 파악해 담당자에게 알림을 발송하고,
유통기한이 마감된 재고는 폐기 처분 및 이력 기록까지 전 과정을 자동화한 서비스입니다.

## [🔄] Service Process

| 서비스 프로세스              | 주요 처리 기능                           |
|-----------------------|------------------------------------|
| **회원 서비스**            | 회원가입, 로그인, JWT 인증 처리               |
| **상품 조회**             | 메인페이지에서 상품 목록 조회                   |
| **장바구니 조회**           | 회원인 경우 장바구니 담기 가능                  |
| **상품 주문**             | 장바구니에 있는 상품 또는 상품 상세 페이지에서 바로 주문 가능 |
| **관리자 페이지 판매, 수익 분석** | 관리자 페이지에서 데이터 시각화를 통한 수익 분석        |
| **RPA 활용한 업무 자동화**    | 반복적인 업무(ex: 보고서 작성 후 메일 전송)들을 자동화  |

---

## 🏛️ 아키텍처 개요

![core](Architecture.jpg)

```
Request
  │
  ▼
[Router]       ← HTTP 요청 수신, 파라미터 파싱, 응답 반환
  │
  ▼
[Schema]       ← Pydantic으로 입력 데이터 유효성 검증
  │
  ▼
[Service]      ← 비즈니스 로직 처리
  │
  ▼
[Model]        ← SQLAlchemy ORM을 통해 DB 접근
  │
  ▼
[Database]     ← 실제 DB (Supabase)
```

---

## 🏛️ ERD

사용자, 상품, 재고, 판매 기록, 알림 로그를 중심으로 설계한 데이터베이스 구조입니다.  
상품 정보와 재고를 분리해 관리하고, 판매 및 알림 이력을 추적할 수 있도록 구성했습니다.

| 테이블 | 역할 |
|---|---|
| `siteuser` | 사용자 정보 관리 |
| `product` | 상품 기본 정보 관리 |
| `product_stock` | 상품별 재고 및 유통기한 관리 |
| `sales_record` | 상품 판매 이력 관리 |
| `notification_log` | 사용자 알림 발송 및 읽음 이력 관리 |

![ERD](erd.jpg)

---

## ⚙️ 기술 스택

FastAPI를 기반으로 비동기 ORM, JWT 인증, Pydantic 검증을 적용한 웹 애플리케이션입니다.

| 분류 | 기술 | 역할 |
|---|---|---|
| **웹 프레임워크** | <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/> | API 서버 및 웹 애플리케이션 구성 |
| **템플릿 엔진** | <img src="https://img.shields.io/badge/Jinja2-B41717?style=flat-square&logo=jinja&logoColor=white"/> | 서버 사이드 HTML 렌더링 |
| **ORM** | <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white"/> | 비동기 DB 접근 |
| **인증** | <img src="https://img.shields.io/badge/JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white"/> | 토큰 기반 사용자 인증 |
| **데이터 검증** | <img src="https://img.shields.io/badge/Pydantic_v2-E92063?style=flat-square&logo=pydantic&logoColor=white"/> | 요청/응답 데이터 검증 |
| **데이터베이스** | <img src="https://img.shields.io/badge/Supabase_PostgreSQL-3FCF8E?style=flat-square&logo=supabase&logoColor=white"/> | 데이터 저장 및 관리 |

---

## 🔐 인증 방식

JWT 기반 인증을 사용합니다.  
로그인 성공 시 Access Token을 발급하며, 보호된 엔드포인트 접근 시 아래 형식의 인증 헤더가 필요합니다.

```http
Authorization: Bearer <access_token>
```

| 항목 | 설명 |
|---|---|
| 인증 방식 | JWT |
| 토큰 발급 | 로그인 성공 시 Access Token 발급 |
| 토큰 검증 | `core/auth.py`에서 처리 |
| 보호 API | `Authorization` 헤더 필요 |

---

## 📁 프로젝트 구조

```
app/
├── core/                   # 공통 핵심 모듈
├── model/                  # SQLAlchemy ORM 모델
├── schema/                 # Pydantic 스키마 (요청/응답 검증)
├── service/                # 비즈니스 로직 레이어
├── router/                 # FastAPI 라우터 (엔드포인트 정의)
├── static/                 # 정적 파일 (CSS, JS, 이미지)
├── templates/              # Jinja2 HTML 템플릿
└── main.py                 # 앱 진입점 (FastAPI 인스턴스, 라우터 등록)
```

---

## 📌 네이밍 컨벤션

도메인별로 router / schema / service 파일을 동일한 접두사로 묶습니다.

```
user_router.py  /  user_schema.py  /  user_service.py
product_router.py  /  product_schema.py  /  product_service.py
cart_router.py  /  cart_schema.py  /  cart_service.py
```
