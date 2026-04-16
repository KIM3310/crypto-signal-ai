from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.routes import app


client = TestClient(app)


class TestProvisionEndpoint:
    def test_provision_basic(self):
        resp = client.post(
            "/api/webhook/provision",
            json={
                "team_name": "Trading Desk",
                "use_case": "BTC monitoring",
                "coins": ["bitcoin"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["team_name"] == "Trading Desk"
        assert data["status"] == "active"
        assert "api_key_masked" in data
        assert "dashboard_url" in data
        assert data["slack_channel"] == "#crypto-alerts"

    def test_provision_custom_slack(self):
        resp = client.post(
            "/api/webhook/provision",
            json={
                "team_name": "Risk Team",
                "use_case": "Risk alerts",
                "slack_channel": "#risk-alerts",
                "admin_email": "risk@company.com",
            },
        )
        data = resp.json()
        assert data["slack_channel"] == "#risk-alerts"
        assert data["admin_email"] == "risk@company.com"

    def test_provision_empty_team_name_rejected(self):
        resp = client.post(
            "/api/webhook/provision",
            json={
                "team_name": "",
                "use_case": "test",
            },
        )
        assert resp.status_code == 422  # validation error


class TestCoinsEndpoint:
    """Test /api/coins - will fail without network but validates routing."""

    def test_coins_invalid_limit(self):
        resp = client.get("/api/coins?limit=0")
        assert resp.status_code == 422

    def test_coins_negative_limit(self):
        resp = client.get("/api/coins?limit=-5")
        assert resp.status_code == 422


class TestSignalsEndpoint:
    def test_signals_invalid_days(self):
        resp = client.get("/api/signals/bitcoin?days=0")
        assert resp.status_code == 422

    def test_signals_days_too_large(self):
        resp = client.get("/api/signals/bitcoin?days=999")
        assert resp.status_code == 422


class TestBacktestEndpoint:
    def test_backtest_invalid_hold(self):
        resp = client.get("/api/backtest/bitcoin?hold_periods=0")
        assert resp.status_code == 422

    def test_backtest_fee_too_high(self):
        resp = client.get("/api/backtest/bitcoin?fee_pct=10")
        assert resp.status_code == 422
