import requests

def test_api_endpoint(url, description, method="GET", data=None):
    try:
        print(f"Testing {description}: {url} [Method: {method}]")
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return
            
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(f"Response: {response.json()}")
        else:
            print(f"Failed with status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    print("-" * 50)

if __name__ == "__main__":
    base_url = "http://localhost:8000"
    
    # Test health endpoints
    test_api_endpoint(f"{base_url}/health", "Health check endpoint")
    test_api_endpoint(f"{base_url}/healthz", "Simple health probe")
    
    # Test auth endpoints with correct method (POST)
    test_api_endpoint(f"{base_url}/api/v1/auth/logout", "Auth logout endpoint", method="POST")
    
    # Test me endpoint which should give 401 if not authenticated
    test_api_endpoint(f"{base_url}/api/v1/auth/me", "Auth me endpoint")
    
    # Test endpoints that need authentication
    test_api_endpoint(f"{base_url}/api/v1/calendar/events", "Calendar events endpoint") 