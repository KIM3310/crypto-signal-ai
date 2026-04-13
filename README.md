# Crypto Signal AI

AI-powered crypto trading signal generator with backtesting engine and n8n workflow automation.

CoinGecko API에서 실시간 가격 데이터를 수집하고, 기술적 분석(RSI, MACD, Bollinger Bands)과 LLM 기반 감성 분석을 결합하여 매매 시그널을 생성합니다. 생성된 시그널을 과거 데이터에 대해 백테스트하여 Sharpe Ratio, Maximum Drawdown, 승률 등 정량적 성과 지표로 검증합니다. n8n 워크플로우와 Slack 웹훅을 통해 Non-Tech 팀도 즉시 사용 가능한 자동 알림 시스템을 제공합니다.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  CoinGecko  │────▶│  Technical       │────▶│   Signal    │
│  API        │     │  Analysis        │     │   Engine    │
└─────────────┘     │  RSI/MACD/BB     │     └──────┬──────┘
                    └──────────────────┘            │
                    ┌──────────────────┐            │
                    │  LLM Sentiment   │────────────┘
                    │  Analysis        │            │
                    └──────────────────┘     ┌──────▼──────┐
                                            │  Backtest   │
┌─────────────┐     ┌──────────────────┐    │  Engine     │
│  n8n        │◀───▶│  Webhook API     │    │  Sharpe/MDD │
│  Workflows  │     │  /webhook/alert  │    └──────┬──────┘
└─────────────┘     │  /webhook/prov.  │           │
                    └──────────────────┘    ┌──────▼──────┐
┌─────────────┐     ┌──────────────────┐   │  SQLite/SQL │
│  Slack      │◀────│  Scheduler       │◀──│  Analytics  │
│  Alerts     │     │  (6h interval)   │   └─────────────┘
└─────────────┘     └──────────────────┘
```

## Features

- **Data Collection**: CoinGecko API 기반 OHLCV 데이터 수집, 상위 코인 목록 조회
- **Technical Analysis**: RSI(14), MACD(12/26/9), Bollinger Bands(20/2σ) 자동 계산
- **AI Sentiment**: OpenAI GPT 기반 가격 액션 감성 분석 (bullish/bearish 스코어)
- **Signal Generation**: 기술적 지표 + 감성 분석 결합 → 5단계 시그널 (Strong Buy ~ Strong Sell)
- **Backtesting**: 과거 데이터 기반 전략 검증, Sharpe Ratio / MDD / 승률 산출
- **n8n Workflow Automation**: 매수/매도 시그널 자동 알림, Non-Tech 팀 온보딩 자동화
- **Webhook API**: n8n / Zapier 등 외부 워크플로우 도구와 즉시 연동
- **Slack Integration**: Strong Buy/Sell 시그널 발생 시 자동 Slack 알림
- **Scheduler**: 6시간 간격 자동 모니터링, 독립 실행 가능
- **SQL Analytics**: 시그널 분포, 최근 시그널, 백테스트 이력, 최고 성과 트레이드 조회
- **61 Tests**: 기술적 분석, 시그널 생성, 백테스트 엔진, DB 레이어, 감성 분석, API 검증, 스케줄러 전체 테스트 커버리지

## Quick Start

```bash
git clone https://github.com/KIM3310/crypto-signal-ai.git
cd crypto-signal-ai
pip install -r requirements.txt

# Run API server (sentiment analysis requires OPENAI_API_KEY)
export OPENAI_API_KEY=your-key-here  # optional, for AI sentiment
uvicorn src.api.routes:app --reload

# Run standalone scheduler (no n8n required)
python -m src.workflows.scheduler

# Run tests
python -m pytest tests/ -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/signals/{coin_id}` | 매매 시그널 생성 |
| GET | `/api/backtest/{coin_id}` | 백테스트 실행 |
| GET | `/api/analytics/{coin_id}` | 저장된 시그널/백테스트 분석 |
| GET | `/api/coins` | 시가총액 상위 코인 목록 |
| POST | `/api/webhook/alert` | n8n 연동 - 멀티코인 시그널 알림 |
| POST | `/api/webhook/provision` | Non-Tech 팀 워크스페이스 프로비저닝 |

## n8n Workflow Integration

`n8n/` 디렉토리에 즉시 임포트 가능한 워크플로우 JSON이 포함되어 있습니다:

- **`crypto_alert_workflow.json`**: 6시간 간격으로 BTC/ETH 시그널을 생성하고, 매수 시그널 감지 시 Slack 알림 + Google Sheets 로깅
- **`onboarding_automation.json`**: Non-Tech 팀의 AI 도구 프로비저닝을 웹훅으로 자동화

```
n8n에서 Import Workflow → JSON 파일 선택 → API URL만 수정하면 즉시 사용 가능
```

## Signal Logic

시그널은 기술적 지표와 감성 분석의 가중 합산으로 결정됩니다:

| Indicator | Buy Signal | Sell Signal |
|-----------|-----------|-------------|
| RSI | < 30 (과매도) | > 70 (과매수) |
| MACD | 골든크로스 (MACD > Signal) | 데드크로스 (MACD < Signal) |
| Bollinger | 하단 밴드 돌파 (%B < 0) | 상단 밴드 돌파 (%B > 1) |
| Sentiment | Score > 0.3 | Score < -0.3 |

## Backtest Metrics

- **Total Return (%)**: 총 수익률
- **Sharpe Ratio**: 연간화된 위험 조정 수익률
- **Max Drawdown (%)**: 최대 낙폭
- **Win Rate**: 승률
- **Trade Count**: 총 거래 횟수

## Tech Stack

Python · FastAPI · NumPy · Pandas · OpenAI API · SQLite · httpx · n8n · Slack Webhooks · Pydantic · pytest

## Configuration

All parameters are configurable via environment variables or `src/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | gpt-4o-mini | OpenAI model for sentiment analysis |
| `RSI_PERIOD` | 14 | RSI indicator period |
| `MACD_FAST/SLOW/SIGNAL` | 12/26/9 | MACD parameters |
| `BB_PERIOD` / `BB_STD` | 20 / 2.0 | Bollinger Bands parameters |
| `DEFAULT_COINS` | bitcoin,ethereum | Monitored coins (comma-separated) |
| `CHECK_INTERVAL` | 21600 | Scheduler interval in seconds (6h) |
| `DB_PATH` | data/signals.db | SQLite database path |
| `OPENAI_API_KEY` | - | Required for sentiment analysis |
| `SLACK_WEBHOOK_URL` | - | Slack incoming webhook URL |
| `N8N_WEBHOOK_URL` | - | n8n webhook trigger URL |
