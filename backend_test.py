import requests
import sys
import json
from datetime import datetime

class MarketIntelAPITester:
    def __init__(self, base_url="https://press-monitor-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        print(f"   Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: List with {len(response_data)} items")
                except:
                    print(f"   Response: Non-JSON or empty")
            else:
                self.tests_passed += 1 if response.status_code in [200, 201] else 0
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text[:200]}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "endpoint": endpoint
                })

            return success, response.json() if response.status_code in [200, 201] else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            self.failed_tests.append({"test": name, "error": "timeout", "endpoint": endpoint})
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            self.failed_tests.append({"test": name, "error": "connection_error", "endpoint": endpoint})
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({"test": name, "error": str(e), "endpoint": endpoint})
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_dashboard_overview(self):
        """Test dashboard overview endpoint"""
        return self.run_test("Dashboard Overview", "GET", "dashboard/overview", 200)

    def test_machines_list(self):
        """Test machines list endpoint"""
        return self.run_test("Machines List", "GET", "machines", 200)

    def test_machines_with_filters(self):
        """Test machines with various filters"""
        filters = [
            {"category": "Printing Press"},
            {"status": "Active"},
            {"search": "heidelberg"},
            {"sort_by": "price", "sort_order": "desc"}
        ]
        
        results = []
        for i, filter_params in enumerate(filters):
            success, data = self.run_test(
                f"Machines Filter {i+1}", 
                "GET", 
                "machines", 
                200, 
                params=filter_params
            )
            results.append(success)
        
        return all(results), {}

    def test_machine_detail(self):
        """Test machine detail endpoint - first get a machine ID"""
        # First get machines list to get a valid ID
        success, machines_data = self.run_test("Get Machines for Detail Test", "GET", "machines", 200, params={"limit": 1})
        
        if success and machines_data and len(machines_data) > 0:
            machine_id = machines_data[0].get('machine_id')
            if machine_id:
                return self.run_test("Machine Detail", "GET", f"machines/{machine_id}", 200)
            else:
                print("❌ No machine_id found in response")
                return False, {}
        else:
            print("❌ Could not get machines list for detail test")
            return False, {}

    def test_price_history(self):
        """Test price history endpoint"""
        # First get machines list to get a valid ID
        success, machines_data = self.run_test("Get Machines for Price History Test", "GET", "machines", 200, params={"limit": 1})
        
        if success and machines_data and len(machines_data) > 0:
            machine_id = machines_data[0].get('machine_id')
            if machine_id:
                return self.run_test("Price History", "GET", f"machines/{machine_id}/price-history", 200)
            else:
                print("❌ No machine_id found in response")
                return False, {}
        else:
            print("❌ Could not get machines list for price history test")
            return False, {}

    def test_scrapers_run(self):
        """Test scrapers run endpoint"""
        return self.run_test("Run Scrapers", "POST", "scrapers/run", 200)

    def test_scrapers_logs(self):
        """Test scrapers logs endpoint"""
        return self.run_test("Scrapers Logs", "GET", "scrapers/logs", 200)

    def test_filter_options(self):
        """Test filter options endpoint"""
        return self.run_test("Filter Options", "GET", "filters/options", 200)

def main():
    print("🚀 Starting MarketIntel API Testing...")
    print("=" * 60)
    
    tester = MarketIntelAPITester()
    
    # Run all tests
    test_methods = [
        tester.test_root_endpoint,
        tester.test_dashboard_overview,
        tester.test_machines_list,
        tester.test_machines_with_filters,
        tester.test_machine_detail,
        tester.test_price_history,
        tester.test_filter_options,
        tester.test_scrapers_logs,
        tester.test_scrapers_run,  # Run this last as it might take time
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            print(f"❌ Test {test_method.__name__} crashed: {e}")
            tester.failed_tests.append({
                "test": test_method.__name__,
                "error": f"Test crashed: {e}",
                "endpoint": "unknown"
            })
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for failed in tester.failed_tests:
            print(f"   - {failed['test']}: {failed.get('error', f\"Status {failed.get('actual')} vs {failed.get('expected')}\")}")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())