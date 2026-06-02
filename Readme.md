# 🚀 FastAPI Project

FastAPI + Jinja2 템플릿 기반의 웹 애플리케이션입니다.  
JWT 인증, 비동기 DB 연동, 서비스 레이어 분리 구조로 설계되었습니다.

---

## 📁 프로젝트 구조

<table>
<tr>
<td width="62%" valign="top">

<pre>
<br><br>
app/
├── core/                   # 공통 핵심 모듈
├── model/                  # SQLAlchemy ORM 모델
├── schema/                 # Pydantic 스키마 (요청/응답 검증)
├── service/                # 비즈니스 로직 레이어
├── router/                 # FastAPI 라우터 (엔드포인트 정의)
├── static/                 # 정적 파일 (CSS, JS, 이미지)
├── templates/              # Jinja2 HTML 템플릿
└── main.py                 # 앱 진입점 (FastAPI 인스턴스, 라우터 등록)
<br><br>
</pre>

</td>
<td width="38%" valign="top" align="center">

<img src="./app.png" alt="프로젝트 폴더 구조" width="200" />

</td>
</tr>
</table>

---

## 🏛️ 아키텍처 개요

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)** 를 따릅니다.

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

**`core/`** 는 모든 레이어에서 공통으로 사용하는 모듈입니다.

![core](gen4.png)

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

## 📌 네이밍 컨벤션

도메인별로 router / schema / service 파일을 동일한 접두사로 묶습니다.

```
user_router.py  /  user_schema.py  /  user_service.py
product_router.py  /  product_schema.py  /  product_service.py
cart_router.py  /  cart_schema.py  /  cart_service.py
```
