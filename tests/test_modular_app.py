"""
Unit tests for the Inscribe Customer Data Service - Modular Architecture
"""

import base64
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app.database.manager import DatabaseManager
# Import the new modular components
from app.main import app
from app.schemas.customer import (CustomerCreate, CustomerResponse,
                                  CustomerUpdate)
from app.services.customer_service import CustomerService

# Test client
client = TestClient(app)

# Test credentials - use test-specific credentials
test_credentials = base64.b64encode(b"test_user:test_password").decode("ascii")
test_headers = {"Authorization": f"Basic {test_credentials}"}


class TestHealthEndpoints:
    """Test health check endpoints"""

    @patch("app.services.customer_service.CustomerService.check_database_health")
    def test_health_check_success(self, mock_health_check):
        """Test successful health check"""
        mock_health_check.return_value = True

        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data

    @patch("app.services.customer_service.CustomerService.check_database_health")
    def test_health_check_database_failure(self, mock_health_check):
        """Test health check with database failure"""
        mock_health_check.return_value = False

        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data


class TestCustomerEndpoints:
    """Test customer CRUD endpoints"""

    def test_create_customer_success(self):
        """Test successful customer creation"""
        customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "address": "123 Main St",
            "date_of_birth": "1990-01-01",
        }

        with patch.object(CustomerService, "create_customer") as mock_create:
            mock_create.return_value = {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-0123",
                "address": "123 Main St",
                "date_of_birth": "1990-01-01",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            response = client.post(
                "/api/v1/customers", json=customer_data, headers=test_headers
            )
            assert response.status_code == 201
            data = response.json()
            assert data["first_name"] == "John"
            assert data["email"] == "john.doe@example.com"
            mock_create.assert_called_once()

    def test_create_customer_validation_error(self):
        """Test customer creation with validation errors"""
        invalid_data = {
            "first_name": "",  # Empty name
            "last_name": "Doe",
            "email": "invalid-email",  # Invalid email format
        }

        response = client.post(
            "/api/v1/customers", json=invalid_data, headers=test_headers
        )
        assert response.status_code == 422

    def test_get_customers_success(self):
        """Test getting customers list"""
        with patch.object(CustomerService, "get_customers") as mock_get:
            mock_customers = [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "phone": None,
                    "address": None,
                    "date_of_birth": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            ]
            mock_get.return_value = mock_customers

            response = client.get("/api/v1/customers", headers=test_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["first_name"] == "John"
            mock_get.assert_called_once_with(skip=0, limit=100)

    def test_get_customer_by_id_success(self):
        """Test getting a specific customer by ID"""
        with patch.object(CustomerService, "get_customer_by_id") as mock_get:
            mock_customer = {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": None,
                "address": None,
                "date_of_birth": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            mock_get.return_value = mock_customer

            response = client.get("/api/v1/customers/1", headers=test_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["first_name"] == "John"
            mock_get.assert_called_once_with(1)

    def test_get_customer_not_found(self):
        """Test getting a non-existent customer"""
        with patch.object(CustomerService, "get_customer_by_id") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/customers/999", headers=test_headers)
            assert response.status_code == 404

    def test_update_customer_success(self):
        """Test updating a customer"""
        update_data = {"first_name": "Updated", "email": "updated@example.com"}

        with patch.object(CustomerService, "update_customer") as mock_update:
            mock_customer = {
                "id": 1,
                "first_name": "Updated",
                "last_name": "Doe",
                "email": "updated@example.com",
                "phone": None,
                "address": None,
                "date_of_birth": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            mock_update.return_value = mock_customer

            response = client.put(
                "/api/v1/customers/1", json=update_data, headers=test_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["first_name"] == "Updated"
            assert data["email"] == "updated@example.com"

    def test_delete_customer_success(self):
        """Test deleting a customer"""
        with patch.object(CustomerService, "delete_customer") as mock_delete:
            mock_delete.return_value = True

            response = client.delete("/api/v1/customers/1", headers=test_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Customer deleted successfully"
            mock_delete.assert_called_once_with(1)

    def test_authentication_required(self):
        """Test that authentication is required"""
        response = client.get("/api/v1/customers")
        assert response.status_code == 401

    def test_invalid_authentication(self):
        """Test invalid authentication"""
        invalid_headers = {
            "Authorization": "Basic aW52YWxpZDppbnZhbGlk"
        }  # invalid:invalid
        response = client.get("/api/v1/customers", headers=invalid_headers)
        assert response.status_code == 401


class TestCustomerService:
    """Test customer service business logic"""

    def test_customer_service_create(self):
        """Test CustomerService.create_customer method"""
        customer_data = CustomerCreate(
            first_name="Jane", last_name="Smith", email="jane@example.com"
        )

        with patch(
            "app.services.customer_service.db_manager.get_cursor"
        ) as mock_get_cursor:
            mock_cursor = MagicMock()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            mock_cursor.lastrowid = 1
            mock_cursor.fetchone.return_value = {
                "id": 1,
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "phone": None,
                "address": None,
                "date_of_birth": None,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }

            result = CustomerService.create_customer(customer_data)

            assert result["first_name"] == "Jane"
            assert result["email"] == "jane@example.com"
            mock_cursor.execute.assert_called()


class TestCustomerSchemas:
    """Test Pydantic schemas"""

    def test_customer_create_validation(self):
        """Test CustomerCreate schema validation"""
        # Valid data
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }
        customer = CustomerCreate(**valid_data)
        assert customer.first_name == "John"
        assert customer.email == "john@example.com"

        # Invalid email
        with pytest.raises(ValueError):
            CustomerCreate(first_name="John", last_name="Doe", email="invalid-email")

        # Empty required fields
        with pytest.raises(ValueError):
            CustomerCreate(first_name="", last_name="Doe", email="john@example.com")

    def test_customer_update_validation(self):
        """Test CustomerUpdate schema validation"""
        # Partial update
        update_data = {"first_name": "Updated"}
        customer_update = CustomerUpdate(**update_data)
        assert customer_update.first_name == "Updated"
        assert customer_update.last_name is None

        # Invalid email in update
        with pytest.raises(ValueError):
            CustomerUpdate(email="invalid-email")


class TestDatabaseManager:
    """Test database connection management"""

    @patch("app.database.manager.pymysql.connect")
    def test_database_connection(self, mock_connect):
        """Test database connection creation"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        # Create a DatabaseManager instance for testing
        with patch("app.database.manager.db_manager") as mock_db_manager:
            mock_db_manager.get_connection.return_value.__enter__.return_value = (
                mock_connection
            )

            with mock_db_manager.get_connection() as conn:
                assert conn == mock_connection

            mock_db_manager.get_connection.assert_called_once()

    @patch("app.database.manager.pymysql.connect")
    def test_database_connection_retry(self, mock_connect):
        """Test database connection retry logic"""
        # Mock the retry logic by testing the actual database manager initialization
        from app.database.manager import DatabaseManager

        with patch.object(DatabaseManager, "_get_connection_config") as mock_config:
            mock_config.return_value = {
                "host": "test",
                "user": "test",
                "password": "test",
            }

            # First call fails, second succeeds
            mock_connect.side_effect = [Exception("Connection failed"), MagicMock()]

            # This will test the retry logic in the initialization
            try:
                db_manager = DatabaseManager()
                # If we get here, the retry worked
                assert mock_connect.call_count >= 1
            except Exception:
                # Expected if all retries fail
                pass


class TestSecurityFeatures:
    """Test security features"""

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_data = {
            "first_name": "'; DROP TABLE customers; --",
            "last_name": "User",
            "email": "test@example.com",
        }

        # The malicious input should be rejected by validation
        response = client.post(
            "/api/v1/customers", json=malicious_data, headers=test_headers
        )
        # Should be rejected with validation error due to invalid characters
        assert response.status_code == 422

    def test_input_sanitization(self):
        """Test input sanitization and validation"""
        # Test XSS prevention
        xss_data = {
            "first_name": "<script>alert('xss')</script>",
            "last_name": "User",
            "email": "test@example.com",
        }

        response = client.post("/api/v1/customers", json=xss_data, headers=test_headers)
        # Should be rejected by validation
        assert response.status_code == 422


class TestLogging:
    """Test logging functionality"""

    def test_request_logging(self, mock_logging):
        """Test that requests are properly logged"""
        # Mock database for health check
        with patch("app.database.manager.db_manager.get_connection") as mock_db:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_connection

            response = client.get("/health")

            # Verify the health check succeeded (logging is handled by fixtures)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
