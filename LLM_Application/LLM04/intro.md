---
title: qc-analysis-workflow
sdk: gradio
sdk_version: 6.9.0
app_file: app.py
pinned: false
---

# QC Analysis Workflow

QC 시험 데이터의 이상치를 탐지하고, 반복 패턴 분석을 통해 root cause 가설과 CAPA를 추천하는 Gradio 기반 분석 워크플로우 프로젝트입니다.

## 1. 프로젝트 개요

이 프로젝트는 바이오/제약 QC 현장에서 자주 발생하는 OOS 및 이상치 대응 흐름을 반영했습니다. 단순히 이상치를 표시하는 데서 끝나지 않고, `Detection -> Root Cause -> CAPA -> Report` 단계로 이어지는 업무형 분석 경험을 제공합니다.

## 2. 문제 정의

QC 데이터 검토는 보통 다음과 같은 어려움을 가집니다.

- spec 기준 이탈 여부만으로는 우선 점검 포인트를 빠르게 좁히기 어렵습니다.
- analyst, equipment, raw material lot, batch 등 여러 차원의 반복 패턴을 동시에 보기 어렵습니다.
- 분석 결과가 보고서와 CAPA 초안으로 바로 연결되지 않으면 실제 실무 활용성이 떨어집니다.

이 프로젝트는 이런 문제를 해결하기 위해 규칙 기반 분석 워크플로우 구조를 사용합니다.

## 3. 주요 기능

- CSV 파일 업로드
- 샘플 QC 데이터 자동 로드
- 필수 컬럼 검증 및 전처리
- spec 기반 OOS 탐지
- z-score / IQR 기반 통계 이상치 탐지
- batch / analyst / equipment / raw material lot / test item 기준 패턴 분석
- 규칙 기반 root cause 가설 생성
- QC/QA 실무 문체의 CAPA 추천
- PDF 리포트 저장 및 다운로드
- Gradio Blocks 기반 단일 화면 데모

## 4. 시스템 흐름도

```text
CSV Upload or Sample Data
        ↓
Data Loader / Column Validation
        ↓
Preprocessing
        ↓
Anomaly Detection
  - Spec OOS
  - Z-score / IQR
        ↓
Pattern Analysis
  - analyst
  - equipment
  - batch
  - raw_material_lot
  - test_item
        ↓
Root Cause Hypotheses
        ↓
CAPA Recommendation
        ↓
PDF Report Generation
        ↓
Gradio UI / Download
```

## 5. 폴더 구조

```text
qc-analysis-workflow/
├─ app.py
├─ requirements.txt
├─ README.md
├─ sample_data/
│  └─ sample_qc_data.csv
├─ reports/
│  └─ .gitkeep
└─ src/
   ├─ __init__.py
   ├─ data_loader.py
   ├─ preprocess.py
   ├─ anomaly_detection.py
   ├─ pattern_analysis.py
   ├─ root_cause.py
   ├─ capa_recommender.py
   ├─ report_generator.py
   └─ llm_interface.py
```

## 6. 샘플 데이터 설명

`sample_data/sample_qc_data.csv`는 다음 상황이 보이도록 설계된 mock 데이터입니다.

- 정상 QC 결과
- spec 하한/상한 이탈 OOS
- 통계적 이상치
- 특정 equipment 반복 이상
- 특정 analyst 편향 가능성
- 특정 raw material lot 연계 이상
- batch 단위의 특이 사례

필수 컬럼:

- `date`
- `product_name`
- `batch_no`
- `test_item`
- `value`
- `spec_min`
- `spec_max`
- `analyst`
- `equipment_id`
- `raw_material_lot`

## 7. 예시 실행 결과

예상되는 데모 흐름:

1. 샘플 데이터 미리보기 버튼 클릭
2. 직접 CSV 업로드 또는 샘플 파일 사용
3. 분석 실행 버튼 클릭
4. 아래 결과 확인

- Summary 카드
- Analysis Briefing
- 이상치 테이블
- 반복 이상 패턴 테이블
- Root cause 가설
- CAPA 추천
- PDF 리포트 다운로드

예시 해석:

- `EQ-03`, `EQ-04`, `EQ-05`에서 반복 이상이 관찰되면 장비 상태 점검 우선순위를 높게 제안
- 특정 analyst의 이상 비율이 높으면 시험자 편차 가능성 검토 제안
- 특정 raw material lot 연계 이상이 보이면 원료 이력 검토 제안

## 8. 향후 확장 방향

- *** LLM 연동
  - `src/llm_interface.py`에 OpenAI/Gemini API 연결
  - root cause 문장과 CAPA를 더 정교하게 생성
- RAG로 SOP 연결
  - 시험 항목별 SOP, OOS SOP, 장비 점검 SOP를 벡터 검색으로 연결
  - 이상 유형별 관련 문서 추천
- 이메일/슬랙 알림 자동화
  - 이상 비율 임계치 초과 시 자동 알림
  - CAPA 초안을 QA 담당자에게 전달하는 워크플로우 확장 가능

## 기술 포인트

- 외부 API 없이 동작하는 규칙 기반 분석 워크플로우
- QC 도메인 흐름을 반영한 해석 중심 분석
- 유지보수 가능한 함수 중심 구조
- GitHub 포트폴리오 및 면접 설명에 적합한 파일 분리
