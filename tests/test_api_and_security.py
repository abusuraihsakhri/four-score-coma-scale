"""Clinical API and audit integrity regression tests."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail, SecurityException

client = TestClient(app)


def test_clinical_endpoint():
    response = client.post("/api/four-score", json={"eye": 4, "motor": 3, "brainstem": 2, "respiration": 1})
    assert response.status_code == 200
    assert response.json()["score"] == 10


@pytest.mark.parametrize("payload", [
    {"eye": 5, "motor": 3, "brainstem": 2, "respiration": 1},
    {"eye": -1, "motor": 3, "brainstem": 2, "respiration": 1},
    {"eye": 2.5, "motor": 3, "brainstem": 2, "respiration": 1},
    {"eye": "4", "motor": 3, "brainstem": 2, "respiration": 1},
    {"eye": True, "motor": 3, "brainstem": 2, "respiration": 1},
    {"eye": 4, "motor": 3, "brainstem": 2},
])
def test_api_rejects_invalid_payload(payload):
    assert client.post("/api/four-score", json=payload).status_code == 422


def test_hmac_detects_tampering():
    trail = AuditTrail(secret_key="test-only-secret")
    trail.log("actor", "tier", "event", {"status": "OK"})
    trail.log("actor", "tier", "event", {"status": "OK"})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "altered"
    assert not trail.verify_integrity()


def test_audit_entries_are_not_mutable_through_public_view():
    trail = AuditTrail(secret_key="test-only-secret")
    trail.log("actor", "tier", "event", {"status": "OK"})
    trail.get_trail()[0]["actor"] = "changed"
    assert trail.verify_integrity()
    assert trail.get_trail()[0]["actor"] == "actor"
