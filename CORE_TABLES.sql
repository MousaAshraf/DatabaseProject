-- ============================================
-- CAIRO METRO SYSTEM - SECURE DATABASE SCHEMA
-- ============================================

CREATE DATABASE IF NOT EXISTS cairo_metro;
USE cairo_metro;

-- ============================================
-- 1. CORE TABLES WITH ENHANCED SECURITY
-- ============================================

-- Users table with password security
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL COMMENT 'BCrypt hashed password',
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_password_change TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    INDEX idx_user_credentials (username, email, phone)
) ENGINE=InnoDB;

-- Metro line
CREATE TABLE line(
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_line_name (name)
) ENGINE=InnoDB;

-- Metro stations with security constraints
CREATE TABLE stations (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL,
    zone INT NOT NULL DEFAULT 1 CHECK (zone BETWEEN 1 AND 6),
    station_order INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    line_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (line_id) REFERENCES line(id) ON DELETE RESTRICT,
    UNIQUE KEY uk_line_station_order (line_id, station_order),
    INDEX idx_station_zone (zone),
    INDEX idx_station_line (line_id)
) ENGINE=InnoDB;

-- User subscriptions with validation
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    plan_type ENUM('monthly', 'quarterly', 'yearly') NOT NULL,
    zone_coverage INT NOT NULL DEFAULT 6 CHECK (zone_coverage BETWEEN 1 AND 6),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_subscription_dates (start_date, end_date),
    INDEX idx_active_subscriptions (user_id, is_active),
    CONSTRAINT chk_dates CHECK (end_date > start_date)
) ENGINE=InnoDB;

-- Main tickets table with validation
CREATE TABLE tickets (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    qr_code VARCHAR(255) NOT NULL UNIQUE,
    start_station_id VARCHAR(36) NOT NULL,
    end_station_id VARCHAR(36) NOT NULL,
    stations_count INT NOT NULL CHECK (stations_count > 0),
    fare_paid DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('active', 'used_entry', 'completed', 'expired', 'paid') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entry_time TIMESTAMP NULL,
    exit_time TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (start_station_id) REFERENCES stations(id),
    FOREIGN KEY (end_station_id) REFERENCES stations(id),
    INDEX idx_ticket_status (status),
    INDEX idx_ticket_expiry (expires_at),
    INDEX idx_ticket_user (user_id),
    CONSTRAINT chk_stations CHECK (start_station_id != end_station_id)
) ENGINE=InnoDB;

-- Secure payment processing table (PCI compliant design)
CREATE TABLE payments (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    ticket_id VARCHAR(36),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    payment_method ENUM('credit_card', 'mobile_wallet', 'cash', 'voucher') NOT NULL,
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    transaction_id VARCHAR(255) UNIQUE,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_four_digits CHAR(4) COMMENT 'For card payments only',
    payment_gateway VARCHAR(50) COMMENT 'Gateway used for processing',
    gateway_reference VARCHAR(255) COMMENT 'Gateway transaction ID',
    ip_address VARCHAR(45) COMMENT 'User IP at time of payment',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE SET NULL,
    INDEX idx_payment_status (status),
    INDEX idx_payment_user (user_id),
    INDEX idx_payment_date (payment_date)
) ENGINE=InnoDB COMMENT='PCI compliant payment storage';

-- Payment audit log for security
CREATE TABLE payment_audit_log (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    payment_id VARCHAR(36) NOT NULL,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    changed_by VARCHAR(36) COMMENT 'User or system that changed status',
    change_reason VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    INDEX idx_audit_payment (payment_id),
    INDEX idx_audit_timestamp (changed_at)
) ENGINE=InnoDB;

-- Scan logs for security monitoring
CREATE TABLE scan_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    ticket_id VARCHAR(36) NOT NULL,
    station_id VARCHAR(36) NOT NULL,
    scan_type ENUM('entry', 'exit') NOT NULL,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    failure_reason VARCHAR(255),
    device_id VARCHAR(100) COMMENT 'Scanner device identifier',
    operator_id VARCHAR(36) COMMENT 'Staff who performed scan if manual',
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    INDEX idx_scan_ticket (ticket_id),
    INDEX idx_scan_time (scan_time),
    INDEX idx_scan_station (station_id)
) ENGINE=InnoDB;

-- ============================================
-- 2. SECURE STORED PROCEDURES
-- ============================================

DELIMITER //

-- Secure payment processing with validation
CREATE PROCEDURE process_payment(
    IN p_user_id VARCHAR(36),
    IN p_ticket_id VARCHAR(36),
    IN p_amount DECIMAL(10,2),
    IN p_payment_method VARCHAR(50),
    IN p_last_four_digits VARCHAR(4),
    IN p_ip_address VARCHAR(45),
    OUT p_payment_id VARCHAR(36),
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255)
    )
BEGIN
    DECLARE v_ticket_fare DECIMAL(10,2);
    DECLARE v_ticket_status VARCHAR(20);
    DECLARE v_user_exists BOOLEAN;
    DECLARE v_payment_gateway VARCHAR(50) DEFAULT 'internal';
    
    -- Start transaction for atomic operation
    START TRANSACTION;
    
    -- Verify user exists and is not locked
    SELECT COUNT(*) > 0 INTO v_user_exists
    FROM users 
    WHERE id = p_user_id AND account_locked = FALSE;
    
    IF NOT v_user_exists THEN
        SET p_success = FALSE;
        SET p_message = 'User not found or account locked';
        ROLLBACK;
    ELSE
        -- Get ticket info with lock to prevent concurrent payments
        SELECT fare_paid, status INTO v_ticket_fare, v_ticket_status
        FROM tickets 
        WHERE id = p_ticket_id AND user_id = p_user_id
        FOR UPDATE;
        
        -- Validate ticket
        IF v_ticket_fare IS NULL THEN
            SET p_success = FALSE;
            SET p_message = 'Ticket not found or not owned by user';
            ROLLBACK;
        ELSEIF v_ticket_status NOT IN ('active', 'paid') THEN
            SET p_success = FALSE;
            SET p_message = 'Ticket is not in a payable state';
            ROLLBACK;
        ELSEIF p_amount < v_ticket_fare THEN
            SET p_success = FALSE;
            SET p_message = 'Payment amount is less than ticket fare';
            ROLLBACK;
        ELSE
            -- Generate payment ID
            SET p_payment_id = UUID();
            
            -- In production, this would call an external payment gateway
            -- For simulation, we'll just mark as completed
            
            -- Create payment record
            INSERT INTO payments (
                id, user_id, ticket_id, amount, 
                payment_method, status, transaction_id,
                last_four_digits, payment_gateway, gateway_reference,
                ip_address
            ) VALUES (
                p_payment_id, p_user_id, p_ticket_id, p_amount,
                p_payment_method, 'completed', 
                CONCAT('txn_', UNIX_TIMESTAMP()),
                p_last_four_digits, v_payment_gateway, 
                CONCAT('sim_', FLOOR(RAND() * 1000000)),
                p_ip_address
            );
            
            -- Create audit log
            INSERT INTO payment_audit_log (
                payment_id, old_status, new_status,
                changed_by, change_reason
            ) VALUES (
                p_payment_id, NULL, 'completed',
                'system', 'Initial payment processing'
            );
            
            -- Update ticket status
            UPDATE tickets 
            SET status = 'paid',
                fare_paid = p_amount
            WHERE id = p_ticket_id;
            
            SET p_success = TRUE;
            SET p_message = 'Payment processed successfully';
            COMMIT;
        END IF;
    END IF;
END//

-- Secure subscription renewal with validation
CREATE PROCEDURE renew_subscription(
    IN p_user_id VARCHAR(36),
    IN p_subscription_id VARCHAR(36),
    IN p_payment_method VARCHAR(50),
    IN p_ip_address VARCHAR(45),
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255))
BEGIN
    DECLARE v_plan_type VARCHAR(20);
    DECLARE v_end_date DATE;
    DECLARE v_amount DECIMAL(10,2);
    DECLARE v_payment_id VARCHAR(36);
    
    -- Start transaction
    START TRANSACTION;
    
    -- Get subscription info with lock
    SELECT plan_type, end_date INTO v_plan_type, v_end_date
    FROM subscriptions
    WHERE id = p_subscription_id AND user_id = p_user_id
    FOR UPDATE;
    
    -- Validate subscription
    IF v_plan_type IS NULL THEN
        SET p_success = FALSE;
        SET p_message = 'Subscription not found or not owned by user';
        ROLLBACK;
    ELSE
        -- Calculate renewal amount based on plan type
        IF v_plan_type = 'monthly' THEN
            SET v_amount = 300.00; -- 300 EGP
            SET v_end_date = DATE_ADD(IF(v_end_date < CURDATE(), CURDATE(), v_end_date), INTERVAL 1 MONTH);
        ELSEIF v_plan_type = 'quarterly' THEN
            SET v_amount = 800.00; -- 800 EGP
            SET v_end_date = DATE_ADD(IF(v_end_date < CURDATE(), CURDATE(), v_end_date), INTERVAL 3 MONTH);
        ELSEIF v_plan_type = 'yearly' THEN
            SET v_amount = 2500.00; -- 2500 EGP
            SET v_end_date = DATE_ADD(IF(v_end_date < CURDATE(), CURDATE(), v_end_date), INTERVAL 1 YEAR);
        END IF;
        
        -- Process payment (in real app this would call payment gateway)
        SET v_payment_id = UUID();
        
        INSERT INTO payments (
            id, user_id, amount, payment_method, 
            status, transaction_id, payment_gateway,
            gateway_reference, ip_address
        ) VALUES (
            v_payment_id, p_user_id, v_amount, p_payment_method,
            'completed', CONCAT('sub_', UNIX_TIMESTAMP()),
            'internal', CONCAT('sub_', FLOOR(RAND() * 1000000)),
            p_ip_address
        );
        
        -- Update subscription
        UPDATE subscriptions
        SET end_date = v_end_date,
            is_active = TRUE
        WHERE id = p_subscription_id;
        
        SET p_success = TRUE;
        SET p_message = CONCAT('Subscription renewed until ', v_end_date);
        COMMIT;
    END IF;
END//

-- Secure ticket booking with validation
CREATE PROCEDURE book_ticket(
    IN p_user_id VARCHAR(36),
    IN p_start_station_id VARCHAR(36),
    IN p_end_station_id VARCHAR(36),
    OUT p_ticket_id VARCHAR(36),
    OUT p_qr_code VARCHAR(255),
    OUT p_fare DECIMAL(10,2),
    OUT p_needs_payment BOOLEAN,
    OUT p_line_name VARCHAR(100))
BEGIN
    DECLARE v_start_order INT;
    DECLARE v_end_order INT;
    DECLARE v_station_count INT;
    DECLARE v_max_zone INT;
    DECLARE v_start_line_id VARCHAR(36);
    DECLARE v_end_line_id VARCHAR(36);
    DECLARE v_user_exists BOOLEAN;
    
    -- Verify user exists and is active
    SELECT COUNT(*) > 0 INTO v_user_exists
    FROM users 
    WHERE id = p_user_id AND account_locked = FALSE;
    
    IF NOT v_user_exists THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User not found or account locked';
    END IF;
    
    -- Get station orders and line info with validation
    SELECT station_order, line_id INTO v_start_order, v_start_line_id 
    FROM stations 
    WHERE id = p_start_station_id AND is_active = TRUE;
    
    IF v_start_order IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Start station not found or inactive';
    END IF;
    
    SELECT station_order, line_id INTO v_end_order, v_end_line_id 
    FROM stations 
    WHERE id = p_end_station_id AND is_active = TRUE;
    
    IF v_end_order IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'End station not found or inactive';
    END IF;
    
    -- Check if both stations are on the same line
    IF v_start_line_id != v_end_line_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stations must be on the same line';
    END IF;
    
    -- Get line name
    SELECT name INTO p_line_name FROM line WHERE id = v_start_line_id;
    
    -- Calculate stations count
    SET v_station_count = ABS(v_end_order - v_start_order) + 1;
    
    -- Calculate fare
    SET p_fare = calculate_fare(v_station_count);
    
    -- Check max zone for subscription
    SELECT GREATEST(s1.zone, s2.zone) INTO v_max_zone
    FROM stations s1, stations s2
    WHERE s1.id = p_start_station_id AND s2.id = p_end_station_id;
    
    -- Check if user has valid subscription
    SET p_needs_payment = NOT has_subscription(p_user_id, v_max_zone);
    
    -- Generate ticket ID and QR code
    SET p_ticket_id = UUID();
    SET p_qr_code = CONCAT('metro_', SHA2(CONCAT(p_ticket_id, UNIX_TIMESTAMP(), RAND()), 256));
    
    -- Create ticket
    INSERT INTO tickets (
        id, user_id, qr_code, start_station_id, end_station_id,
        stations_count, fare_paid, expires_at, status
    ) VALUES (
        p_ticket_id, p_user_id, p_qr_code, p_start_station_id, p_end_station_id,
        v_station_count,
        CASE WHEN p_needs_payment THEN 0.00 ELSE p_fare END,
        DATE_ADD(NOW(), INTERVAL 2 HOUR),
        CASE WHEN p_needs_payment THEN 'active' ELSE 'paid' END
    );
END//

-- Secure fare calculation function
CREATE FUNCTION calculate_fare(station_count INT) 
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    IF station_count <= 9 THEN
        RETURN 8.00;
    ELSEIF station_count <= 16 THEN
        RETURN 10.00;
    ELSEIF station_count <= 23 THEN
        RETURN 15.00;
    ELSE
        RETURN 20.00;
    END IF;
END//

-- Secure subscription check function
CREATE FUNCTION has_subscription(user_id VARCHAR(36), max_zone INT)
RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE sub_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO sub_count
    FROM subscriptions 
    WHERE user_id = user_id 
      AND CURDATE() BETWEEN start_date AND end_date
      AND is_active = TRUE 
      AND zone_coverage >= max_zone;
      
    RETURN sub_count > 0;
END//

DELIMITER ;

-- ============================================
-- 3. SECURITY VIEWS AND INDEXES
-- ============================================

-- Payment summary view (masked for security)
CREATE VIEW payment_summary AS
SELECT 
    p.id,
    p.user_id,
    p.amount,
    p.payment_method,
    CONCAT('****', p.last_four_digits) AS masked_card,
    p.status,
    p.payment_date
FROM payments p;

-- Active subscriptions view
CREATE VIEW active_subscriptions AS
SELECT 
    s.id,
    s.user_id,
    u.username,
    s.plan_type,
    s.zone_coverage,
    s.start_date,
    s.end_date
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = TRUE
AND CURDATE() BETWEEN s.start_date AND s.end_date;

-- Ticket validation view
CREATE VIEW valid_tickets AS
SELECT 
    t.id,
    t.user_id,
    t.qr_code,
    s1.name AS start_station,
    s2.name AS end_station,
    t.status,
    t.expires_at
FROM tickets t
JOIN stations s1 ON t.start_station_id = s1.id
JOIN stations s2 ON t.end_station_id = s2.id
WHERE t.status IN ('active', 'paid')
AND t.expires_at > NOW();

-- ============================================
-- 4. SECURITY TRIGGERS
-- ============================================

DELIMITER //

-- Payment status change audit trigger
CREATE TRIGGER payment_status_audit
AFTER UPDATE ON payments
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO payment_audit_log (
            payment_id, old_status, new_status,
            changed_by, change_reason
        ) VALUES (
            NEW.id, OLD.status, NEW.status,
            'system', 'Status changed by system'
        );
    END IF;
END//

-- User account lock after failed attempts
CREATE TRIGGER user_failed_login
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    IF NEW.failed_login_attempts >= 5 AND OLD.failed_login_attempts < 5 THEN
        UPDATE users 
        SET account_locked = TRUE 
        WHERE id = NEW.id;
        
        INSERT INTO security_events (user_id, event_type, description)
        VALUES (NEW.id, 'account_lock', 'Account locked due to multiple failed login attempts');
    END IF;
END//

DELIMITER ;

-- ============================================
-- 5. SAMPLE DATA WITH SECURE VALUES
-- ============================================

-- Insert sample stations

-- LINE 1: Helwan - New El Marg (35 stations)
-- Insert metro line first
INSERT INTO line (name, description) VALUES 
('Line 1', 'Helwan - New El Marg (Red Line)'),
('Line 2', 'Shubra El Kheima - Monib (Yellow Line)'),
('Line 3', 'Adly Mansour - Kit Kat (Green Line)'),
('Line 4', 'Stadium - New Administrative Capital (Blue Line)');

-- Insert stations with Arabic names

-- LINE 1: Helwan - New El Marg (35 stations)
INSERT INTO stations (name, zone, station_order, line_id) VALUES 
('Helwan', 1, 1, (SELECT id FROM line WHERE name = 'Line 1')),
('Ain Helwan', 1, 2, (SELECT id FROM line WHERE name = 'Line 1')),
('Helwan University', 1, 3, (SELECT id FROM line WHERE name = 'Line 1')),
('Wadi Hof', 1, 4, (SELECT id FROM line WHERE name = 'Line 1')),
('Hadayek Helwan', 1, 5, (SELECT id FROM line WHERE name = 'Line 1')),
('El Maasara', 1, 6, (SELECT id FROM line WHERE name = 'Line 1')),
('Tora El Asmant', 1, 7, (SELECT id FROM line WHERE name = 'Line 1')),
('Kozzika', 1, 8, (SELECT id FROM line WHERE name = 'Line 1')),
('Tora El Balad', 1, 9, (SELECT id FROM line WHERE name = 'Line 1')),
('Sakanat El Maadi', 2, 10, (SELECT id FROM line WHERE name = 'Line 1')),
('Maadi', 2, 11, (SELECT id FROM line WHERE name = 'Line 1')),
('Hadayek El Maadi', 2, 12, (SELECT id FROM line WHERE name = 'Line 1')),
('Dar El Salam', 2, 13, (SELECT id FROM line WHERE name = 'Line 1')),
('El Zahraa', 2, 14, (SELECT id FROM line WHERE name = 'Line 1')),
('Mar Girgis', 2, 15, (SELECT id FROM line WHERE name = 'Line 1')),
('El Malek El Saleh', 2, 16, (SELECT id FROM line WHERE name = 'Line 1')),
('Al Sayeda Zeinab', 3, 17, (SELECT id FROM line WHERE name = 'Line 1')),
('Saad Zaghloul', 3, 18, (SELECT id FROM line WHERE name = 'Line 1')),
('Sadat', 3, 19, (SELECT id FROM line WHERE name = 'Line 1')),
('Nasser', 3, 20, (SELECT id FROM line WHERE name = 'Line 1')),
('Orabi', 3, 21, (SELECT id FROM line WHERE name = 'Line 1')),
('Al Shohadaa', 3, 22, (SELECT id FROM line WHERE name = 'Line 1')),
('Ghamra', 3, 23, (SELECT id FROM line WHERE name = 'Line 1')),
('El Demerdash', 3, 24, (SELECT id FROM line WHERE name = 'Line 1')),
('Manshiet El Sadr', 4, 25, (SELECT id FROM line WHERE name = 'Line 1')),
('Kobri El Qobba', 4, 26, (SELECT id FROM line WHERE name = 'Line 1')),
('Hammamat El Qobba', 4, 27, (SELECT id FROM line WHERE name = 'Line 1')),
('Saray El Qobba', 4, 28, (SELECT id FROM line WHERE name = 'Line 1')),
('Hadayeq El Zeitoun', 4, 29, (SELECT id FROM line WHERE name = 'Line 1')),
('Helmeyet El Zeitoun', 4, 30, (SELECT id FROM line WHERE name = 'Line 1')),
('El Matareyya', 4, 31, (SELECT id FROM line WHERE name = 'Line 1')),
('Ain Shams', 4, 32, (SELECT id FROM line WHERE name = 'Line 1')),
('Ezbet El Nakhl', 5, 33, (SELECT id FROM line WHERE name = 'Line 1')),
('El Marg', 5, 34, (SELECT id FROM line WHERE name = 'Line 1')),
('New El Marg', 5, 35, (SELECT id FROM line WHERE name = 'Line 1')),

-- LINE 2: Shubra El Kheima - Monib (20 stations)
('Shubra El Kheima', 1, 101, (SELECT id FROM line WHERE name = 'Line 2')),
('Koliet El Zeraa', 1, 102, (SELECT id FROM line WHERE name = 'Line 2')),
('Mezallat', 1, 103, (SELECT id FROM line WHERE name = 'Line 2')),
('Khalafawy', 1, 104, (SELECT id FROM line WHERE name = 'Line 2')),
('St. Teresa', 1, 105, (SELECT id FROM line WHERE name = 'Line 2')),
('Rod El Farag', 2, 106, (SELECT id FROM line WHERE name = 'Line 2')),
('Masarra', 2, 107, (SELECT id FROM line WHERE name = 'Line 2')),
('Al Shohadaa L2', 3, 108, (SELECT id FROM line WHERE name = 'Line 2')), 
('Attaba', 3, 109, (SELECT id FROM line WHERE name = 'Line 2')),
('Mohamed Naguib', 3, 110, (SELECT id FROM line WHERE name = 'Line 2')),
('Sadat L2', 3, 111, (SELECT id FROM line WHERE name = 'Line 2')), 
('Opera', 3, 112, (SELECT id FROM line WHERE name = 'Line 2')),
('Dokki', 3, 113, (SELECT id FROM line WHERE name = 'Line 2')),
('Bohooth', 3, 114, (SELECT id FROM line WHERE name = 'Line 2')),
('Cairo University', 4, 115, (SELECT id FROM line WHERE name = 'Line 2')),
('Faisal', 4, 116, (SELECT id FROM line WHERE name = 'Line 2')),
('Giza', 4, 117, (SELECT id FROM line WHERE name = 'Line 2')),
('Omm El Masryeen', 4, 118, (SELECT id FROM line WHERE name = 'Line 2')),
('Sakiat Mekki', 5, 119, (SELECT id FROM line WHERE name = 'Line 2')),
('Monib', 5, 120, (SELECT id FROM line WHERE name = 'Line 2')),

-- LINE 3: Adly Mansour - Kit Kat (34 stations)
('Adly Mansour', 6, 201, (SELECT id FROM line WHERE name = 'Line 3')),
('El Haykestep', 6, 202, (SELECT id FROM line WHERE name = 'Line 3')),
('Omar Ibn El Khattab', 6, 203, (SELECT id FROM line WHERE name = 'Line 3')),
('Qobaa', 6, 204, (SELECT id FROM line WHERE name = 'Line 3')),
('Hesham Barakat', 6, 205, (SELECT id FROM line WHERE name = 'Line 3')),
('El Nozha', 6, 206, (SELECT id FROM line WHERE name = 'Line 3')),
('Nadi El Shams', 5, 207, (SELECT id FROM line WHERE name = 'Line 3')),
('Alf Maskan', 5, 208, (SELECT id FROM line WHERE name = 'Line 3')),
('Heliopolis Square', 5, 209, (SELECT id FROM line WHERE name = 'Line 3')),
('Haroun', 5, 210, (SELECT id FROM line WHERE name = 'Line 3')),
('Al Ahram', 5, 211, (SELECT id FROM line WHERE name = 'Line 3')),
('Koleyet El Banat', 4, 212, (SELECT id FROM line WHERE name = 'Line 3')),
('Stadium', 4, 213, (SELECT id FROM line WHERE name = 'Line 3')),
('Fair Zone', 4, 214, (SELECT id FROM line WHERE name = 'Line 3')),
('Abbassia', 4, 215, (SELECT id FROM line WHERE name = 'Line 3')),
('Abdou Pasha', 4, 216, (SELECT id FROM line WHERE name = 'Line 3')),
('El Geish', 4, 217, (SELECT id FROM line WHERE name = 'Line 3')),
('Bab El Shaaria', 4, 218, (SELECT id FROM line WHERE name = 'Line 3')),
('Attaba L3', 3, 219, (SELECT id FROM line WHERE name = 'Line 3')), 
('Nasser L3', 3, 220, (SELECT id FROM line WHERE name = 'Line 3')), 
('Maspero', 3, 221, (SELECT id FROM line WHERE name = 'Line 3')),
('Safaa Hegazy', 3, 222, (SELECT id FROM line WHERE name = 'Line 3')),
('Kit Kat', 3, 223, (SELECT id FROM line WHERE name = 'Line 3')),
('Sudan', 3, 224, (SELECT id FROM line WHERE name = 'Line 3')),
('Imbaba', 3, 225, (SELECT id FROM line WHERE name = 'Line 3')),
('El Bohy', 2, 226, (SELECT id FROM line WHERE name = 'Line 3')),
('El Kawmeya El Arabeya', 2, 227, (SELECT id FROM line WHERE name = 'Line 3')),
('El Tariq El Daery', 2, 228, (SELECT id FROM line WHERE name = 'Line 3')),
('El Mounib L3', 2, 229, (SELECT id FROM line WHERE name = 'Line 3')),
('Gizet El Arab', 2, 230, (SELECT id FROM line WHERE name = 'Line 3')),
('El Malek El Saleh L3', 2, 231, (SELECT id FROM line WHERE name = 'Line 3')),
('Wadi Hof L3', 1, 232, (SELECT id FROM line WHERE name = 'Line 3')),
('Hadayek Helwan L3', 1, 233, (SELECT id FROM line WHERE name = 'Line 3')),
('Helwan L3', 1, 234, (SELECT id FROM line WHERE name = 'Line 3')),

-- LINE 4 (NEW ADMINISTRATIVE CAPITAL): Stadium - New Capital (12 stations)
('Stadium L4', 4, 301, (SELECT id FROM line WHERE name = 'Line 4')), 
('Medical City', 4, 302, (SELECT id FROM line WHERE name = 'Line 4')),
('El Fustat', 3, 303, (SELECT id FROM line WHERE name = 'Line 4')),
('El Malek El Saleh L4', 3, 304, (SELECT id FROM line WHERE name = 'Line 4')), 
('El Bassatine', 3, 305, (SELECT id FROM line WHERE name = 'Line 4')),
('El Zahraa L4', 2, 306, (SELECT id FROM line WHERE name = 'Line 4')), 
('New Maadi', 2, 307, (SELECT id FROM line WHERE name = 'Line 4')),
('Maadi El Gadida', 2, 308, (SELECT id FROM line WHERE name = 'Line 4')),
('Saray El Qobba L4', 4, 309, (SELECT id FROM line WHERE name = 'Line 4')), 
('New Cairo', 5, 310, (SELECT id FROM line WHERE name = 'Line 4')),
('El Rehab', 6, 311, (SELECT id FROM line WHERE name = 'Line 4')),
('New Administrative Capital', 6, 312, (SELECT id FROM line WHERE name = 'Line 4'));

-- Create test user
INSERT INTO users (username, firstname, lastname, phone, email, password_hash) VALUES 
('AhmedMohamed', 'ahmed', 'mohamed','+201234567890', 'ahmed@example.com', SHA2('password123', 256));

-- Create security events table for logging
CREATE TABLE security_events (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_security_event_type (event_type),
    INDEX idx_security_event_time (created_at)
) ENGINE=InnoDB;

-- Create indexes for performance and security monitoring
CREATE INDEX idx_user_login_attempts ON users(failed_login_attempts, account_locked);
CREATE INDEX idx_payment_card ON payments(last_four_digits) COMMENT 'PCI compliant partial index';
CREATE INDEX idx_ticket_usage ON tickets(entry_time, exit_time, status);