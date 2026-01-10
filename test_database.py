"""
Test script to verify database connection and API endpoints
Run this after starting docker-compose
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_signup():
    """Test user signup"""
    print("\n2. Testing User Signup...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json={
                "email": "test@example.com",
                "name": "Test User",
                "password": "password123"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 400]  # 400 if user already exists
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n3. Testing User Login...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/json",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
        if response.status_code == 200:
            return data.get("access_token")
        return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def test_get_me(token):
    """Test get current user"""
    print("\n4. Testing Get Current User...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_create_patient(token):
    """Test create patient"""
    print("\n5. Testing Create Patient...")
    try:
        response = requests.post(
            f"{BASE_URL}/patients/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_hn": "HN001",
                "name": "Jane Doe",
                "age": "45 Years",
                "sex": "Female",
                "phone": "1234567890",
                "email": "jane@example.com"
            }
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 400]  # 400 if patient already exists
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_get_patients(token):
    """Test get patients"""
    print("\n6. Testing Get Patients...")
    try:
        response = requests.get(
            f"{BASE_URL}/patients/",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_dashboard(token):
    """Test dashboard stats"""
    print("\n7. Testing Dashboard Stats...")
    try:
        response = requests.get(
            f"{BASE_URL}/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 50)
    print("DATABASE & API TEST SCRIPT")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ Health check failed. Is the backend running?")
        return
    
    # Test signup
    test_signup()
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Login failed. Cannot continue tests.")
        return
    
    print(f"\n✅ Got access token: {token[:50]}...")
    
    # Test authenticated endpoints
    test_get_me(token)
    test_create_patient(token)
    test_get_patients(token)
    test_dashboard(token)
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 50)
    print("\nAPI Documentation: http://localhost:8001/docs")

if __name__ == "__main__":
    main()
