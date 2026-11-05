#!/usr/bin/env python3
"""
InvoiceFlow Pro API Test Script
Comprehensive API testing script with automated test cases
"""

import requests
import json
import time
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class InvoiceFlowAPITester:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_customer_id = None
        self.test_invoice_id = None
        self.results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}: {details}")

    def test_user_registration_and_login(self):
        """Test user registration and login"""
        print("\n🔐 Testing Authentication...")
        
        # Test user registration
        test_user = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/register", json=test_user)
            if response.status_code == 201:
                self.log_test("User Registration", True, f"User registered: {test_user['email']}")
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False

        # Test user login
        try:
            login_data = {
                "username": test_user['email'],
                "password": test_user['password']
            }
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                self.log_test("User Login", True, "Access token received")
                return True
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    def test_customer_operations(self):
        """Test customer CRUD operations"""
        print("\n👥 Testing Customer Management...")
        
        # Test customer creation
        test_customer = {
            "name": "Test Customer API",
            "email": "test.customer@example.com",
            "phone": "+1-555-0199",
            "company": "Test Company API",
            "address_line_1": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
            "payment_terms": 30
        }
        
        try:
            response = self.session.post(f"{self.base_url}/customers/", json=test_customer)
            if response.status_code == 201:
                customer_data = response.json()
                self.test_customer_id = customer_data['customer']['id']
                self.log_test("Customer Creation", True, f"Customer ID: {self.test_customer_id}")
            else:
                self.log_test("Customer Creation", False, f"Status: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Customer Creation", False, str(e))
            return False

        # Test customer retrieval
        try:
            response = self.session.get(f"{self.base_url}/customers/{self.test_customer_id}")
            if response.status_code == 200:
                customer = response.json()['customer']
                if customer['name'] == test_customer['name']:
                    self.log_test("Customer Retrieval", True, f"Retrieved: {customer['name']}")
                else:
                    self.log_test("Customer Retrieval", False, "Data mismatch")
            else:
                self.log_test("Customer Retrieval", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Customer Retrieval", False, str(e))

        # Test customer update
        try:
            update_data = {"phone": "+1-555-0200", "notes": "Updated via API test"}
            response = self.session.put(f"{self.base_url}/customers/{self.test_customer_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("Customer Update", True, "Customer updated successfully")
            else:
                self.log_test("Customer Update", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Customer Update", False, str(e))

        # Test customer list
        try:
            response = self.session.get(f"{self.base_url}/customers/")
            if response.status_code == 200:
                customers = response.json()
                self.log_test("Customer List", True, f"Retrieved {len(customers.get('customers', []))} customers")
            else:
                self.log_test("Customer List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Customer List", False, str(e))

        return True

    def test_invoice_operations(self):
        """Test invoice CRUD operations"""
        print("\n📄 Testing Invoice Management...")
        
        if not self.test_customer_id:
            self.log_test("Invoice Operations", False, "No customer ID available")
            return False

        # Test invoice creation
        test_invoice = {
            "customer_id": self.test_customer_id,
            "invoice_number": f"TEST-{int(time.time())}",
            "issue_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "currency": "USD",
            "items": [
                {
                    "description": "API Testing Service",
                    "quantity": 5,
                    "unit_price": 100.00,
                    "subtotal": 500.00,
                    "total": 500.00,
                    "sort_order": 0
                },
                {
                    "description": "Additional Testing",
                    "quantity": 2,
                    "unit_price": 75.00,
                    "subtotal": 150.00,
                    "total": 150.00,
                    "sort_order": 1
                }
            ],
            "subtotal": 650.00,
            "tax_rate": 8.5,
            "tax_amount": 55.25,
            "total": 705.25,
            "notes": "Test invoice created via API"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/invoices/", json=test_invoice)
            if response.status_code == 201:
                invoice_data = response.json()
                self.test_invoice_id = invoice_data['invoice']['id']
                self.log_test("Invoice Creation", True, f"Invoice ID: {self.test_invoice_id}")
            else:
                self.log_test("Invoice Creation", False, f"Status: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            self.log_test("Invoice Creation", False, str(e))
            return False

        # Test invoice retrieval
        try:
            response = self.session.get(f"{self.base_url}/invoices/{self.test_invoice_id}")
            if response.status_code == 200:
                invoice = response.json()['invoice']
                if len(invoice['items']) == 2:
                    self.log_test("Invoice Retrieval", True, f"Retrieved invoice with {len(invoice['items'])} items")
                else:
                    self.log_test("Invoice Retrieval", False, "Items count mismatch")
            else:
                self.log_test("Invoice Retrieval", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invoice Retrieval", False, str(e))

        # Test invoice status update
        try:
            update_data = {"status": "sent"}
            response = self.session.put(f"{self.base_url}/invoices/{self.test_invoice_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("Invoice Status Update", True, "Status changed to sent")
            else:
                self.log_test("Invoice Status Update", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invoice Status Update", False, str(e))

        return True

    def test_bulk_operations(self):
        """Test bulk operations"""
        print("\n📦 Testing Bulk Operations...")
        
        # Test CSV export
        try:
            response = self.session.get(f"{self.base_url}/bulk/export/customers")
            if response.status_code == 200:
                # Check if it's valid CSV
                csv_content = response.text
                csv_reader = csv.reader(io.StringIO(csv_content))
                rows = list(csv_reader)
                if len(rows) > 0 and 'Name' in rows[0]:
                    self.log_test("CSV Export", True, f"Exported {len(rows)-1} customers")
                else:
                    self.log_test("CSV Export", False, "Invalid CSV format")
            else:
                self.log_test("CSV Export", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("CSV Export", False, str(e))

        # Test template download
        try:
            response = self.session.get(f"{self.base_url}/bulk/template/customers")
            if response.status_code == 200:
                self.log_test("Template Download", True, "Template downloaded successfully")
            else:
                self.log_test("Template Download", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Template Download", False, str(e))

        # Test bulk invoice operations (if we have invoices)
        if self.test_invoice_id:
            try:
                bulk_update_data = {
                    "invoice_ids": [self.test_invoice_id],
                    "updates": {
                        "notes": "Updated via bulk operation API test"
                    }
                }
                response = self.session.put(f"{self.base_url}/bulk/invoices/update", json=bulk_update_data)
                if response.status_code == 200:
                    results = response.json()['results']
                    self.log_test("Bulk Invoice Update", True, f"Updated {results.get('updated_invoices', 0)} invoices")
                else:
                    self.log_test("Bulk Invoice Update", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Bulk Invoice Update", False, str(e))

    def test_recurring_invoices(self):
        """Test recurring invoice operations"""
        print("\n🔄 Testing Recurring Invoices...")
        
        if not self.test_customer_id:
            self.log_test("Recurring Invoices", False, "No customer ID available")
            return

        # Test recurring invoice creation
        recurring_invoice = {
            "customer_id": self.test_customer_id,
            "invoice_number": f"REC-{int(time.time())}",
            "issue_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "currency": "USD",
            "recurrence_interval": "monthly",
            "recurrence_count": 6,
            "items": [
                {
                    "description": "Monthly Subscription Service",
                    "quantity": 1,
                    "unit_price": 99.99,
                    "subtotal": 99.99,
                    "total": 99.99,
                    "sort_order": 0
                }
            ],
            "subtotal": 99.99,
            "total": 99.99,
            "notes": "Monthly recurring service"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/recurring/", json=recurring_invoice)
            if response.status_code == 201:
                recurring_data = response.json()
                recurring_id = recurring_data['invoice']['id']
                self.log_test("Recurring Invoice Creation", True, f"Recurring ID: {recurring_id}")
                
                # Test recurring invoice retrieval
                response = self.session.get(f"{self.base_url}/recurring/{recurring_id}")
                if response.status_code == 200:
                    self.log_test("Recurring Invoice Retrieval", True, "Retrieved recurring invoice")
                else:
                    self.log_test("Recurring Invoice Retrieval", False, f"Status: {response.status_code}")
                    
            else:
                self.log_test("Recurring Invoice Creation", False, f"Status: {response.status_code}, {response.text}")
        except Exception as e:
            self.log_test("Recurring Invoice Creation", False, str(e))

        # Test recurring invoices list
        try:
            response = self.session.get(f"{self.base_url}/recurring/")
            if response.status_code == 200:
                recurring_invoices = response.json()
                self.log_test("Recurring Invoice List", True, f"Retrieved {len(recurring_invoices.get('invoices', []))} recurring invoices")
            else:
                self.log_test("Recurring Invoice List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Recurring Invoice List", False, str(e))

    def test_analytics(self):
        """Test analytics endpoints"""
        print("\n📊 Testing Analytics...")
        
        # Test revenue analytics
        try:
            params = {
                'period': 'last_30_days'
            }
            response = self.session.get(f"{self.base_url}/analytics/revenue", params=params)
            if response.status_code == 200:
                analytics_data = response.json()
                self.log_test("Revenue Analytics", True, f"Retrieved analytics data")
            else:
                self.log_test("Revenue Analytics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Revenue Analytics", False, str(e))

        # Test performance metrics
        try:
            response = self.session.get(f"{self.base_url}/analytics/performance")
            if response.status_code == 200:
                self.log_test("Performance Analytics", True, "Retrieved performance metrics")
            else:
                self.log_test("Performance Analytics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Performance Analytics", False, str(e))

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n⚠️  Testing Error Handling...")
        
        # Test unauthorized access (without token)
        temp_headers = self.session.headers.copy()
        self.session.headers.pop('Authorization', None)
        
        try:
            response = self.session.get(f"{self.base_url}/customers/")
            if response.status_code == 401:
                self.log_test("Unauthorized Access", True, "Correctly returned 401")
            else:
                self.log_test("Unauthorized Access", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Unauthorized Access", False, str(e))
        
        # Restore headers
        self.session.headers.update(temp_headers)
        
        # Test invalid customer ID
        try:
            response = self.session.get(f"{self.base_url}/customers/99999")
            if response.status_code == 404:
                self.log_test("Invalid Customer ID", True, "Correctly returned 404")
            else:
                self.log_test("Invalid Customer ID", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Customer ID", False, str(e))

        # Test invalid data
        try:
            invalid_customer = {"name": "", "email": "invalid-email"}
            response = self.session.post(f"{self.base_url}/customers/", json=invalid_customer)
            if response.status_code in [400, 422]:
                self.log_test("Invalid Data Validation", True, f"Correctly returned {response.status_code}")
            else:
                self.log_test("Invalid Data Validation", False, f"Expected 400/422, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Data Validation", False, str(e))

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test invoice
        if self.test_invoice_id:
            try:
                response = self.session.delete(f"{self.base_url}/invoices/{self.test_invoice_id}")
                if response.status_code in [200, 204]:
                    self.log_test("Invoice Cleanup", True, "Test invoice deleted")
                else:
                    self.log_test("Invoice Cleanup", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Invoice Cleanup", False, str(e))

        # Delete test customer
        if self.test_customer_id:
            try:
                response = self.session.delete(f"{self.base_url}/customers/{self.test_customer_id}")
                if response.status_code in [200, 204]:
                    self.log_test("Customer Cleanup", True, "Test customer deleted")
                else:
                    self.log_test("Customer Cleanup", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Customer Cleanup", False, str(e))

    def generate_report(self):
        """Generate test report"""
        print("\n📋 Test Report")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        # Save detailed report
        with open('test_report.json', 'w') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: test_report.json")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting InvoiceFlow Pro API Tests")
        print("=" * 50)
        
        try:
            # Authentication tests
            if not self.test_user_registration_and_login():
                print("❌ Authentication failed - stopping tests")
                return
            
            # Core functionality tests
            self.test_customer_operations()
            self.test_invoice_operations()
            self.test_bulk_operations()
            self.test_recurring_invoices()
            self.test_analytics()
            
            # Error handling tests
            self.test_error_handling()
            
            # Cleanup
            self.cleanup_test_data()
            
        except KeyboardInterrupt:
            print("\n⚡ Tests interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
        finally:
            # Generate report
            self.generate_report()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='InvoiceFlow Pro API Tester')
    parser.add_argument('--url', default='http://localhost:8000/api/v1', help='API base URL')
    parser.add_argument('--skip-cleanup', action='store_true', help='Skip cleanup of test data')
    
    args = parser.parse_args()
    
    tester = InvoiceFlowAPITester(args.url)
    tester.run_all_tests()