"""
Customer business logic and database operations
"""

from typing import Any, Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor

from app.core.logging import get_logger
from app.database.manager import db_manager
from app.schemas.customer import (CustomerCreate, CustomerResponse,
                                  CustomerUpdate)

logger = get_logger(__name__)


class CustomerService:
    """Service layer for customer operations"""

    @staticmethod
    def create_customer(customer_data: CustomerCreate) -> Dict[str, Any]:
        """Create a new customer"""
        insert_sql = """
        INSERT INTO customers (first_name, last_name, email, phone, address, date_of_birth)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        try:
            with db_manager.get_cursor() as cursor:
                # Use parameterized query to prevent SQL injection
                cursor.execute(
                    insert_sql,
                    (
                        customer_data.first_name,
                        customer_data.last_name,
                        customer_data.email,
                        customer_data.phone,
                        customer_data.address,
                        customer_data.date_of_birth,
                    ),
                )

                customer_id = cursor.lastrowid

                # Fetch the created customer
                select_sql = "SELECT * FROM customers WHERE id = %s"
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()

                if result:
                    logger.info(f"Customer created successfully: ID {customer_id}")
                    return result
                else:
                    raise Exception("Failed to retrieve created customer")

        except pymysql.IntegrityError as e:
            if "Duplicate entry" in str(e):
                raise ValueError("Customer with this email already exists")
            else:
                logger.error(f"Database integrity error: {e}")
                raise ValueError("Data integrity violation")
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            raise

    @staticmethod
    def get_customers(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all customers with pagination"""
        if limit > 1000:
            limit = 1000  # Prevent excessive data retrieval

        select_sql = """
        SELECT * FROM customers 
        ORDER BY created_at DESC 
        LIMIT %s OFFSET %s
        """

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(select_sql, (limit, skip))
                results = cursor.fetchall()
                return results

        except Exception as e:
            logger.error(f"Error retrieving customers: {e}")
            raise

    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific customer by ID"""
        select_sql = "SELECT * FROM customers WHERE id = %s"

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()
                return result

        except Exception as e:
            logger.error(f"Error retrieving customer {customer_id}: {e}")
            raise

    @staticmethod
    def update_customer(
        customer_id: int, customer_data: CustomerUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update a customer"""
        # Build dynamic update query based on provided fields
        update_fields = []
        update_values = []

        update_mapping = {
            "first_name": customer_data.first_name,
            "last_name": customer_data.last_name,
            "email": customer_data.email,
            "phone": customer_data.phone,
            "address": customer_data.address,
            "date_of_birth": customer_data.date_of_birth,
        }

        for field, value in update_mapping.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if not update_fields:
            raise ValueError("No fields to update")

        update_sql = f"""
        UPDATE customers 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        update_values.append(customer_id)

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(update_sql, update_values)

                if cursor.rowcount == 0:
                    return None  # Customer not found

                # Fetch updated customer
                select_sql = "SELECT * FROM customers WHERE id = %s"
                cursor.execute(select_sql, (customer_id,))
                result = cursor.fetchone()

                logger.info(f"Customer updated successfully: ID {customer_id}")
                return result

        except pymysql.IntegrityError as e:
            if "Duplicate entry" in str(e):
                raise ValueError("Customer with this email already exists")
            else:
                logger.error(f"Database integrity error: {e}")
                raise ValueError("Data integrity violation")
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            raise

    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        """Delete a customer"""
        delete_sql = "DELETE FROM customers WHERE id = %s"

        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute(delete_sql, (customer_id,))

                if cursor.rowcount == 0:
                    return False  # Customer not found

                logger.info(f"Customer deleted successfully: ID {customer_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            raise

    @staticmethod
    def check_database_health() -> bool:
        """Check database connectivity for health checks"""
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
