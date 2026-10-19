# Global Local Pulse v1.1

한국·미국·일본·영국·독일·프랑스의 최근 현지 뉴스와 검색 급상승 신호를 비교하는 **Python 3.12 / Streamlit MVP**입니다. 조회 기간 기본값은 한국시간 기준 최근 5개 달력일입니다. API 키 없이 실행할 수 있습니다.

## 제공되는 두 화면

- **실제 애플리케이션**: `app.py`. 수집, 날짜 조회, 새로고침, SQLite 캐시, 상세·비교·Plotly 차트, 선택적 AI 요약을 실행합니다.
- **웹 열람 화면**: `web/`. 이번에 실제 수집한 `data/latest.json`을 보여주는 별도의 정적 스냅샷입니다. 웹 링크는 Streamlit 서버가 아니며 재수집·새 날짜 조회를 수행하지 않습니다. 게시 시각 이후의 뉴스를 자동 반영하지 않습니다.

Work 클라우드에서 Python 앱을 실행하고 HTTP 및 Streamlit AppTest로 검증했습니다. 이 환경의 웹 게시 기능은 장기 실행 Python 서버를 호스팅하지 않으므로 Streamlit의 상시 접속 URL은 발급하지 않았습니다. 아래 방법으로 PC나 Python 서버에서 실행할 수 있습니다. 예약 수집은 설정하지 않았습니다.

## 빠른 실행

Python 3.12 설치 후 ZIP을 풀고 그 폴더에서 실행합니다. Windows는 `run_windows.bat`, macOS/Linux는 `bash run.sh`도 사용할 수 있습니다.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다. 기본 6개국 데이터를 자동 수집하며, 동일 조건의 캐시는 30분간 사용합니다. 원천 서버가 느리면 첫 수집에 약 1~3분이 걸릴 수 있습니다. 수동 새로고침은 캐시를 우회합니다. JSON 내려받기와 원문 링크는 화면에서 사용할 수 있습니다.

## 사용 순서

1. 기준일·기간·국가를 고른 뒤 **조회 · 캐시 사용**을 누릅니다. 조건 변경만으로 오래된 결과가 바뀐 것처럼 표시하지 않습니다.
2. 국가 카드의 이슈를 누르면 화면 아래 상세 분석이 열립니다.
3. **국가 비교**에서 상위 이슈와 카테고리 구성을 비교합니다.
4. **데이터 상태·산정 기준**에서 원천별 성공/오류/비어 있음, 정확한 수집 시각, 점수 산정법을 확인합니다.
5. 최신 수집이 필요하면 **데이터 새로고침**을 누릅니다.

한국어 제목·요약은 API 키가 있을 때 생성됩니다. 키가 없으면 원문 제목, 한국어 지표 설명, 실제 수치를 표시합니다. 빈 자료를 생성해서 TOP 5를 채우지 않습니다. 검색 급상승만 있는 항목은 단일 신호로 표시하며, 날짜가 없는 Trends 연결 기사는 보도량에서 제외합니다.

## 선택적 AI 설정

`.env.example`을 `.env`로 복사하고 서버 환경변수 또는 파일에만 값을 넣으세요. 화면이나 소스코드에 키를 넣지 마세요.

```dotenv
OPENAI_API_KEY=본인의_API_키
OPENAI_MODEL=gpt-4.1-mini
ENABLE_EMBEDDINGS=1
EMBEDDING_MODEL=text-embedding-3-small
```

- API 과금이 발생할 수 있습니다. 사용할 수 있는 모델명으로 변경 가능합니다.
- `ENABLE_EMBEDDINGS=0`(기본값)이면 문자 n-gram TF-IDF 유사도를 사용합니다. 이것을 의미 기반 분석이라고 표시하지 않습니다.
- 임베딩 옵션은 국가 내 사건 묶음과 국가 간 공통 후보 탐지에 사용됩니다. API 실패 시 보수적인 기본 방식으로 돌아갑니다.
- AI는 GDELT·현지 RSS 제목만 근거로 구조화 JSON을 생성합니다. 출처 ID, 원문 인용 문자열, 필드 길이 등을 검증하고 실패한 생성물은 버립니다. 제목에 없는 배경·인과관계는 ‘근거 부족’으로 출력하도록 요구합니다.
- 이 검증은 인용 일치 검사이며 문장 의미의 완전한 사실 검증을 보장하지 않습니다. 실제 API 호출은 키가 없어 이번 검증 범위에서 제외했습니다.

## 수집 소스와 관측 한계

1. **Google Trends**: `https://trends.google.com/trending/rss?geo=KR` 등 국가별 현재 RSS. 실제 6개국 응답을 확인했습니다. 검색량은 원천 제공 구간/하한이고 정확한 횟수가 아닙니다. 관련 검색어 필드는 원천 미제공 시 빈 배열입니다.
2. **GDELT DOC**: Google News를 대체하는 주 뉴스 집계원입니다. 국가별 `sourcecountry` 기사 목록을 수집해 후보·출처 다양성·보도 확산 맥락에 사용합니다. GDELT의 `seendate`는 최초 관측 시각이므로 발행 시각과 구분합니다. 이번 Work 네트워크에서는 API 요청이 HTTP 503으로 실패해 오류 상태를 숨기지 않습니다.
3. **현지 언론 RSS**: 국가별 공개 RSS 두 곳을 원문 링크·교차검증용으로 수집합니다. GDELT 실패 시에도 독립 뉴스 후보를 확보합니다. 오래된 NHK 항목 등 기간 밖 자료는 제거하며 공개 RSS 메타데이터만 사용합니다.
4. **Media Cloud(선택적 확장)**: `MEDIACLOUD_API_KEY`가 설정된 운영 환경에서 넓은 매체 검색을 추가할 수 있도록 다음 단계 확장 지점으로 남겨두었습니다. API 키 없이 임의 호출하거나 성공으로 표시하지 않습니다.

GDELT·RSS는 전수 수집이 아니고 매체 구성·언어·국가 필터 편향이 있습니다. 결과는 탐색용 후보이며 국민 전체 관심도 순위가 아닙니다. 매체 도메인/명칭 수는 독립적 소유주 수와 같지 않습니다. 검색어는 여러 사건을 포함할 수 있어 명시적 연결이 애매하면 사건에 배분하지 않습니다.

## 점수 및 날짜

설정은 `config/countries.yaml`, `config/scoring.yaml`에 있습니다. 국가 추가는 countries.yaml 항목을 추가하면 UI·CLI에 반영됩니다.

- **대중 관심도**를 주 순위로 사용합니다: 검색 급상승 70%, 검색 후보 폭 30%. Google Trends가 제공하는 최근 검색 행동을 기준으로 하며 국민 전체의 절대 관심도 조사가 아닙니다.
- **언론 보도 확산도**는 별도 표시합니다: GDELT·RSS 수집 보도량 60%, 매체 다양성 25%, 관측일 지속성 15%. 언론 표본은 사건 설명과 교차검증에 사용하며 주 순위를 지배하지 않습니다.
- 각 수치에 국가 내부 `log(1+x)/log(1+국가 내 최대값)` 적용. 확보된 가중치 합으로 재정규화합니다. 결측 지표는 0점이 아닙니다. 검색량 미제공이면 검색 지표도 결측으로 두지만 급상승 존재 태그는 보존합니다.
- 같은 매체는 이슈당 최대 2건만 보도량 점수에 기여합니다. URL·제목 중복 제거와 같은 매체 유사 제목 제거를 먼저 수행합니다. 완전히 같은 신디케이션 제목을 중복 제거하므로 매체 다양성은 보수적으로 계산됩니다.
- 복수 매체+검색 신호: ‘복수 신호 확인’. 검색만: ‘검색 신호’. 복수 매체만: ‘언론 신호’. 단일 기사만: ‘근거 부족’으로 TOP 5 제외.
- 가중치가 서로 다른 후보의 점수에는 불확실성이 있습니다. 신호 종류·가중치 확보율과 함께 해석해야 하며 국가 간 점수 비교는 금지합니다.
- 뉴스 시각은 **발행 시각**, 수집 시각은 **접속 시각**입니다. 실제 사건 발생 시각은 추정하지 않습니다.
- 최근 N일은 한국시간 기준 당일 포함 N개 달력일, ±5일은 기준일 포함 11개 달력일입니다. 끝은 현재 시각에서 잘라 미래를 제외합니다. DB는 UTC, 화면은 KST입니다.
- 과거 Trends는 SQLite에 저장한 자료만 제공합니다. 날짜 없는 연결 기사는 참고 링크로만 남깁니다. 미관측 날짜를 0으로 채우거나 추세선을 만들지 않습니다.
- 이전 기간과 동일한 표본을 확보하지 못했으므로 **보도량 증가율은 현재 미구현(결측)** 입니다. 언론 확산도는 검색 기반 대중 관심도와 별도로 표시합니다.

## 저장·CLI·테스트

SQLite 기본 경로는 `data/pulse.sqlite3`; `PULSE_DB`로 변경할 수 있습니다. 원본 메타데이터, 산출 스냅샷, AI 생성 결과를 별도 테이블에 저장합니다. 같은 국가·조회 조건의 마지막 정상 결과로만 장애 대체합니다. 다른 날짜 결과를 현재 결과인 것처럼 표시하지 않습니다.

```bash
python scripts/refresh.py --force
python scripts/refresh.py --countries KR US JP --days 3
python scripts/refresh.py --date 2026-10-18 --around --output data/history.json
python scripts/refresh.py --ai
python -m pytest -q
python scripts/export_web.py
```

ZIP에는 이번 수집의 실제 원본 메타데이터 JSON과 테스트 결과가 들어 있습니다. 처음 기본 DB를 생성할 때 data/seed.json의 실제 관측 자료를 SQLite에 복원합니다. 테스트용 합성 데이터는 `tests/`에만 있고 실제 스냅샷에는 섞이지 않습니다. 단위 테스트는 외부 API를 모의 처리하고 UI 테스트는 저장된 실제 스냅샷을 사용합니다. `scripts/reprocess.py`는 저장된 원본을 다시 분석하며 수집 시각을 바꾸지 않습니다.

## 배포

Python 3.12 서버에서 위 설치 후 다음으로 실행하세요. 인터넷에 공개하는 경우 서버/프록시에서 접근 제어를 별도로 적용하세요. 이 저장소의 Streamlit 앱은 별도 사용자 인증을 구현하지 않습니다.

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Docker 배포 파일도 포함했습니다. Docker 자체 실행은 이번 환경에서 검증하지 않았습니다.

```bash
docker build -t global-local-pulse .
docker run --rm -p 8501:8501 --env-file .env -v pulse-data:/app/data global-local-pulse
```

API 키가 없으면 `--env-file .env`를 생략하세요. 운영 환경에서는 영속 볼륨을 사용해야 합니다. PostgreSQL/Supabase 전환과 자동 예약 수집은 미구현입니다. 현재 소스는 [GitHub 저장소](https://github.com/KOJH-archive/Global-Local-Pulse)에 포함되어 있지만, GitHub 자체는 Python/Streamlit 서버를 상시 실행하지 않습니다. Streamlit Cloud, Codespaces, Docker 호스트 또는 별도 Python 서버에서 실행해야 합니다.

### GitHub Actions와 Pages

`.github/workflows/ci.yml`은 `main` 푸시·Pull Request마다 테스트와 Python 컴파일 검사를 실행합니다. `.github/workflows/refresh-pages.yml`은 6시간마다(또는 Actions의 **Run workflow**로 수동) 실제 데이터를 수집하고 `dist/` 정적 대시보드를 GitHub Pages에 배포합니다. 이 페이지는 수집 시점의 스냅샷이며 Streamlit처럼 브라우저에서 재수집하지 않습니다.

처음 한 번 저장소 **Settings → Pages → Build and deployment → Source: GitHub Actions**를 선택하세요. AI 요약을 사용하려면 저장소 **Settings → Secrets and variables → Actions**에 `OPENAI_API_KEY`를 등록합니다. Actions의 `with_ai`를 켜지 않으면 키가 있어도 요약을 호출하지 않습니다. Pages 배포가 완료되면 보통 `https://kojh-archive.github.io/Global-Local-Pulse/`에서 열 수 있습니다.

검증 결과와 미완료 항목은 `DEVELOPMENT_REPORT.md`에서 확인하세요.

