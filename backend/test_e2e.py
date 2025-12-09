import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

def test_ocr_extract():
    # Replace with a valid test file path and endpoint
    url = f"{API_BASE_URL}/ocr/extract"
    files = {"file": ("test.png", open("test.png", "rb"), "image/png")}
    response = requests.post(url, files=files)
    assert response.status_code == 200
    assert "text" in response.json()

def test_scam_report():
    url = f"{API_BASE_URL}/scam/report"
    payload = {
        "email": "test@example.com",
        "description": "Test scam report",
        "scam_type": "phishing",
        "location": "Testville",
        "risk_level": "Low",
        "risk_score": 10,
        "created_at": "2025-12-09T00:00:00Z"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200 or response.status_code == 201
    assert "report_id" in response.json()

def test_auth_otp():
    url = f"{API_BASE_URL}/auth/send-otp"
    payload = {"email": "test@example.com"}
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    assert "message" in response.json()
