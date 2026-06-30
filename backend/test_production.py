import requests
import json

base_url = "https://ai-based-smart-doubt-management-system.onrender.com/api/v1/auth"

def test_production():
    payload = {
        "email": "test.malli.reddy@university.edu",
        "first_name": "malli",
        "last_name": "reddy",
        "password": "testpassword123",
        "role_names": ["student"]
    }
    print("Testing Registration...")
    res = requests.post(f"{base_url}/register", json=payload)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test_production()
