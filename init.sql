-- Initialize database schema
CREATE DATABASE IF NOT EXISTS inscribe_customers;
USE inscribe_customers;

CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_last_name (last_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data
INSERT INTO customers (first_name, last_name, email, phone, address, date_of_birth) VALUES
('John', 'Doe', 'john.doe@example.com', '+1-555-0101', '123 Main St, Anytown, ST 12345', '1985-06-15'),
('Jane', 'Smith', 'jane.smith@example.com', '+1-555-0102', '456 Oak Ave, Another City, ST 54321', '1990-03-22'),
('Mike', 'Johnson', 'mike.johnson@example.com', '+1-555-0103', '789 Pine Rd, Somewhere, ST 67890', '1988-11-08');
