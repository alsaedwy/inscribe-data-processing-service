"""
Unit tests for the Inscribe Customer Data Service
"""

import base64
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.main import app  # noqa: E402

# Test client
client = TestClient(app)

# Test credentials
test_credentials = base64.b64encode(b"test_user:test_password").decode("ascii")
test_headers = {"Authorization": f"Basic {test_credentials}"}


class TestCustomerService:
    """Test class for customer service endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        with patch("app.database.manager.db_manager.get_connection") as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.return_value.__enter__.return_value = mock_connection

            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert "timestamp" in response.json()

    def test_create_customer_success(self):
        """Test successful customer creation"""
        customer_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "+1-555-0123",
            "address": "123 Test St",
            "date_of_birth": "1990-01-01",
        }

        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            # Mock cursor behavior
            mock_cursor.lastrowid = 1
            mock_cursor.fetchone.return_value = {
                "id": 1,
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone": "+1-555-0123",
                "address": "123 Test St",
                "date_of_birth": "1990-01-01",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }

            response = client.post("/customers", json=customer_data, headers=test_headers)
            assert response.status_code == 200
            assert response.json()["first_name"] == "Test"
            assert response.json()["email"] == "test@example.com"

    def test_create_customer_invalid_data(self):
        """Test customer creation with invalid data"""
        invalid_data = {
            "first_name": "",  # Empty name
            "last_name": "User",
            "email": "invalid-email",  # Invalid email
        }

        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422  # Validation error

    def test_create_customer_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_data = {
            "first_name": "'; DROP TABLE customers; --",
            "last_name": "User",
            "email": "test@example.com",
        }

        # The malicious input should be rejected by validation
        response = client.post("/customers", json=malicious_data, headers=test_headers)
        # Should be rejected with validation error due to invalid characters
        assert response.status_code == 422

    def test_get_customers(self):
        """Test getting customers list"""
        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            mock_cursor.fetchall.return_value = [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": None,
                    "address": None,
                    "date_of_birth": None,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                }
            ]

            response = client.get("/customers", headers=test_headers)
            assert response.status_code == 200
            assert len(response.json()) == 1
            assert response.json()[0]["first_name"] == "John"

    def test_get_customer_by_id(self):
        """Test getting a specific customer by ID"""
        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            mock_cursor.fetchone.return_value = {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": None,
                "address": None,
                "date_of_birth": None,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }

            response = client.get("/customers/1", headers=test_headers)
            assert response.status_code == 200
            assert response.json()["id"] == 1
            assert response.json()["first_name"] == "John"

    def test_get_customer_not_found(self):
        """Test getting a non-existent customer"""
        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            mock_cursor.fetchone.return_value = None

            response = client.get("/customers/999", headers=test_headers)
            assert response.status_code == 404

    def test_update_customer(self):
        """Test updating a customer"""
        update_data = {"first_name": "Updated", "email": "updated@example.com"}

        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            mock_cursor.rowcount = 1
            mock_cursor.fetchone.return_value = {
                "id": 1,
                "first_name": "Updated",
                "last_name": "Doe",
                "email": "updated@example.com",
                "phone": None,
                "address": None,
                "date_of_birth": None,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00",
            }

            response = client.put("/customers/1", json=update_data, headers=test_headers)
            assert response.status_code == 200
            assert response.json()["first_name"] == "Updated"
            assert response.json()["email"] == "updated@example.com"

    def test_delete_customer(self):
        """Test deleting a customer"""
        with patch("app.database.manager.db_manager.get_cursor") as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

            mock_cursor.rowcount = 1

            response = client.delete("/customers/1", headers=test_headers)
            assert response.status_code == 200
            assert response.json()["message"] == "Customer deleted successfully"

    def test_authentication_required(self):
        """Test that authentication is required"""
        response = client.get("/customers")
        assert response.status_code == 401

    def test_invalid_authentication(self):
        """Test invalid authentication"""
        invalid_headers = {"Authorization": "Basic aW52YWxpZDppbnZhbGlk"}  # invalid:invalid
        response = client.get("/customers", headers=invalid_headers)
        assert response.status_code == 401


class TestInputValidation:
    """Test input validation"""

    def test_name_validation(self):
        """Test name validation"""
        # Test empty name
        invalid_data = {
            "first_name": "",
            "last_name": "User",
            "email": "test@example.com",
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422

        # Test name too long
        invalid_data = {
            "first_name": "A" * 101,
            "last_name": "User",
            "email": "test@example.com",
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422

        # Test invalid characters
        invalid_data = {
            "first_name": "Test123",
            "last_name": "User",
            "email": "test@example.com",
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422

    def test_email_validation(self):
        """Test email validation"""
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "invalid-email",
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422

    def test_phone_validation(self):
        """Test phone validation"""
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "123",  # Too short
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422

    def test_date_validation(self):
        """Test date validation"""
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "date_of_birth": "invalid-date",
        }
        response = client.post("/customers", json=invalid_data, headers=test_headers)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
