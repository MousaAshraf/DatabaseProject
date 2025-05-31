-- ============================================
-- CAIRO METRO SYSTEM - CORRECTED VERSION
-- ============================================

CREATE DATABASE IF NOT EXISTS cairo_metro_simple;
USE cairo_metro_simple;

-- ============================================
-- 1. CORE TABLES
-- ============================================

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metro lines
CREATE TABLE lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(20)
);

-- Metro stations (removed zone field)
CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    line_id INT,
    station_order INT NOT NULL,
    FOREIGN KEY (line_id) REFERENCES lines(id)
);

-- User subscriptions
CREATE TABLE subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plan_type ENUM('monthly', 'quarterly', 'yearly') NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Tickets
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    from_station_id INT,
    to_station_id INT,
    fare DECIMAL(6,2) NOT NULL,
    status ENUM('active', 'used', 'expired') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (from_station_id) REFERENCES stations(id),
    FOREIGN KEY (to_station_id) REFERENCES stations(id)
);

-- Payments
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    ticket_id INT NULL,
    subscription_id INT NULL,
    amount DECIMAL(8,2) NOT NULL,
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);

-- ============================================
-- 2. INDEXES 
-- ============================================

-- Index on station name for quick searches
CREATE INDEX idx_stations_name ON stations(name);

-- Index on station line_id and order for route calculations
CREATE INDEX idx_stations_line_order ON stations(line_id, station_order);

-- Index on user phone for login queries
CREATE INDEX idx_users_phone ON users(phone);

-- Index on ticket status and creation date
CREATE INDEX idx_tickets_status_date ON tickets(status, created_at);

-- Index on subscription dates for active subscription checks
CREATE INDEX idx_subscriptions_dates ON subscriptions(start_date, end_date, is_active);

-- Index on payments status and date
CREATE INDEX idx_payments_status_date ON payments(status, payment_date);

-- Index on user_id for faster user-related queries
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);

-- ============================================
-- 3. SAMPLE DATA
-- ============================================

-- Insert metro lines
INSERT INTO lines (name, color) VALUES 
('Line 1 (Red)', 'Red'),
('Line 2 (Yellow)', 'Yellow'),
('Line 3 (Green)', 'Green'),
('Line 4 (Blue)', 'Blue');

-- LINE 1: Helwan - New El Marg (35 stations)
INSERT INTO stations (name, line_id, station_order) VALUES 
('Helwan', 1, 1),
('Ain Helwan', 1, 2),
('Helwan University', 1, 3),
('Wadi Hof', 1, 4),
('Hadayek Helwan', 1, 5),
('El Maasara', 1, 6),
('Tora El Asmant', 1, 7),
('Kozzika', 1, 8),
('Tora El Balad', 1, 9),
('Sakanat El Maadi', 1, 10),
('Maadi', 1, 11),
('Hadayek El Maadi', 1, 12),
('Dar El Salam', 1, 13),
('El Zahraa', 1, 14),
('Mar Girgis', 1, 15),
('El Malek El Saleh', 1, 16),
('Al Sayeda Zeinab', 1, 17),
('Saad Zaghloul', 1, 18),
('Sadat', 1, 19),
('Nasser', 1, 20),
('Orabi', 1, 21),
('Al Shohadaa', 1, 22),
('Ghamra', 1, 23),
('El Demerdash', 1, 24),
('Manshiet El Sadr', 1, 25),
('Kobri El Qobba', 1, 26),
('Hammamat El Qobba', 1, 27),
('Saray El Qobba', 1, 28),
('Hadayeq El Zeitoun', 1, 29),
('Helmeyet El Zeitoun', 1, 30),
('El Matareyya', 1, 31),
('Ain Shams', 1, 32),
('Ezbet El Nakhl', 1, 33),
('El Marg', 1, 34),
('New El Marg', 1, 35);

-- LINE 2: Shubra El Kheima - Monib (20 stations)
INSERT INTO stations (name, line_id, station_order) VALUES 
('Shubra El Kheima', 2, 1),
('Koliet El Zeraa', 2, 2),
('Mezallat', 2, 3),
('Khalafawy', 2, 4),
('St. Teresa', 2, 5),
('Rod El Farag', 2, 6),
('Masarra', 2, 7),
('Al Shohadaa L2', 2, 8),
('Attaba', 2, 9),
('Mohamed Naguib', 2, 10),
('Sadat L2', 2, 11),
('Opera', 2, 12),
('Dokki', 2, 13),
('Bohooth', 2, 14),
('Cairo University', 2, 15),
('Faisal', 2, 16),
('Giza', 2, 17),
('Omm El Masryeen', 2, 18),
('Sakiat Mekki', 2, 19),
('Monib', 2, 20);

-- LINE 3: Adly Mansour - Helwan (34 stations)
INSERT INTO stations (name, line_id, station_order) VALUES 
('Adly Mansour', 3, 1),
('El Haykestep', 3, 2),
('Omar Ibn El Khattab', 3, 3),
('Qobaa', 3, 4),
('Hesham Barakat', 3, 5),
('El Nozha', 3, 6),
('Nadi El Shams', 3, 7),
('Alf Maskan', 3, 8),
('Heliopolis Square', 3, 9),
('Haroun', 3, 10),
('Al Ahram', 3, 11),
('Koleyet El Banat', 3, 12),
('Stadium', 3, 13),
('Fair Zone', 3, 14),
('Abbassia', 3, 15),
('Abdou Pasha', 3, 16),
('El Geish', 3, 17),
('Bab El Shaaria', 3, 18),
('Attaba L3', 3, 19),
('Nasser L3', 3, 20),
('Maspero', 3, 21),
('Safaa Hegazy', 3, 22),
('Kit Kat', 3, 23),
('Sudan', 3, 24),
('Imbaba', 3, 25),
('El Bohy', 3, 26),
('El Kawmeya El Arabeya', 3, 27),
('El Tariq El Daery', 3, 28),
('El Mounib L3', 3, 29),
('Gizet El Arab', 3, 30),
('El Malek El Saleh L3', 3, 31),
('Wadi Hof L3', 3, 32),
('Hadayek Helwan L3', 3, 33),
('Helwan L3', 3, 34);

-- LINE 4: Stadium - New Administrative Capital (12 stations)
INSERT INTO stations (name, line_id, station_order) VALUES 
('Stadium L4', 4, 1),
('Medical City', 4, 2),
('El Fustat', 4, 3),
('El Malek El Saleh L4', 4, 4),
('El Bassatine', 4, 5),
('El Zahraa L4', 4, 6),
('New Maadi', 4, 7),
('Maadi El Gadida', 4, 8),
('Saray El Qobba L4', 4, 9),
('New Cairo', 4, 10),
('El Rehab', 4, 11),
('New Administrative Capital', 4, 12);

-- Create sample users
INSERT INTO users (name, phone, email, password, is_admin) VALUES 
('Mousa Ashraf', '+201207919519', 'mousaashraf88@gmail.com', '12345', TRUE),
('Ahmed Mohamed', '+201234567890', 'ahmed@example.com', 'hashed_password_123', FALSE),
('Sara Ali', '+201098765432', 'sara.ali@example.com', 'secure_pass_456', TRUE),
('Omar Hassan', '+201555444333', 'omar.hassan@example.com', 'my_password_789', FALSE),
('Peter', '+201111222333', 'petro@cairometro.gov.eg', '1111', FALSE);

-- Sample subscriptions
INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, price, is_active) VALUES 
(1, 'monthly', '2025-05-01', '2025-05-31', 180.00, TRUE),
(2, 'quarterly', '2025-04-01', '2025-06-30', 500.00, TRUE),
(3, 'yearly', '2025-01-01', '2025-12-31', 1800.00, TRUE);

-- Sample tickets with corrected fare calculation
INSERT INTO tickets (user_id, from_station_id, to_station_id, fare, status, expires_at) VALUES 
-- From Maadi (station 11) to Sadat (station 19) = 9 stations difference = 8.00 EGP
(4, 11, 19, 8.00, 'active', DATE_ADD(NOW(), INTERVAL 2 HOUR)),
-- From New El Marg (station 35) to Helwan (station 1) = 35 stations difference = 20.00 EGP
(4, 35, 1, 20.00, 'used', DATE_ADD(NOW(), INTERVAL -1 DAY)),
-- From Shubra El Kheima (station 36) to Rod El Farag (station 41) = 6 stations difference = 8.00 EGP
(1, 36, 41, 8.00, 'active', DATE_ADD(NOW(), INTERVAL 3 HOUR));

-- Sample payments
INSERT INTO payments (user_id, subscription_id, amount, status) VALUES 
(1, 1, 180.00, 'completed'),
(2, 2, 500.00, 'completed'),
(3, 3, 1800.00, 'completed');

INSERT INTO payments (user_id, ticket_id, amount, status) VALUES 
(4, 1, 8.00, 'completed'),
(4, 2, 20.00, 'completed'),
(1, 3, 8.00, 'completed');

-- ============================================
-- 4. USEFUL FUNCTIONS
-- ============================================

DELIMITER //

-- Calculate fare based on number of stations
CREATE FUNCTION calculate_fare(stations_count INT) 
RETURNS DECIMAL(6,2)
DETERMINISTIC
BEGIN
    IF stations_count <= 9 THEN
        RETURN 8.00;
    ELSEIF stations_count <= 16 THEN
        RETURN 10.00;
    ELSEIF stations_count <= 23 THEN
        RETURN 15.00;
    ELSE
        RETURN 20.00;
    END IF;
END//

-- Calculate stations between two stations on the same line
CREATE FUNCTION calculate_stations_between(from_station_id INT, to_station_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE from_order INT DEFAULT 0;
    DECLARE to_order INT DEFAULT 0;
    DECLARE from_line INT DEFAULT 0;
    DECLARE to_line INT DEFAULT 0;
    DECLARE station_diff INT DEFAULT 0;
    
    -- Get station orders and line IDs
    SELECT station_order, line_id INTO from_order, from_line
    FROM stations WHERE id = from_station_id;
    
    SELECT station_order, line_id INTO to_order, to_line
    FROM stations WHERE id = to_station_id;
    
    -- Check if stations are on the same line
    IF from_line != to_line THEN
        RETURN -1; -- Invalid: different lines
    END IF;
    
    -- Calculate absolute difference + 1 (to include both stations)
    SET station_diff = ABS(to_order - from_order) + 1;
    
    RETURN station_diff;
END//

-- Calculate fare between two stations
CREATE FUNCTION calculate_fare_between_stations(from_station_id INT, to_station_id INT)
RETURNS DECIMAL(6,2)
READS SQL DATA
BEGIN
    DECLARE stations_count INT;
    
    SET stations_count = calculate_stations_between(from_station_id, to_station_id);
    
    -- If invalid route (different lines), return 0
    IF stations_count = -1 THEN
        RETURN 0.00;
    END IF;
    
    RETURN calculate_fare(stations_count);
END//

-- Check if user has active subscription
CREATE FUNCTION has_active_subscription(user_id INT)
RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE sub_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO sub_count
    FROM subscriptions 
    WHERE user_id = user_id 
      AND CURDATE() BETWEEN start_date AND end_date
      AND is_active = TRUE;
      
    RETURN sub_count > 0;
END//

-- Check if user is admin
CREATE FUNCTION is_user_admin(user_id INT)
RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE admin_status BOOLEAN DEFAULT FALSE;
    
    SELECT is_admin INTO admin_status
    FROM users 
    WHERE id = user_id;
      
    RETURN admin_status;
END//

DELIMITER ;

-- ============================================
-- 5. VIEWS 
-- ============================================

-- Active tickets view
CREATE VIEW active_tickets AS
SELECT 
    t.id,
    u.name as user_name,
    u.phone as user_phone,
    s1.name as from_station,
    s2.name as to_station,
    l1.name as from_line,
    l2.name as to_line,
    t.fare,
    t.status,
    t.created_at,
    t.expires_at,
    calculate_stations_between(t.from_station_id, t.to_station_id) as stations_traveled
FROM tickets t
JOIN users u ON t.user_id = u.id
JOIN stations s1 ON t.from_station_id = s1.id
JOIN stations s2 ON t.to_station_id = s2.id
JOIN lines l1 ON s1.line_id = l1.id
JOIN lines l2 ON s2.line_id = l2.id
WHERE t.status = 'active';

-- Subscription summary view
CREATE VIEW subscription_summary AS
SELECT 
    s.id,
    u.name as user_name,
    u.phone as user_phone,
    s.plan_type,
    s.start_date,
    s.end_date,
    s.price,
    CASE 
        WHEN CURDATE() BETWEEN s.start_date AND s.end_date AND s.is_active = TRUE THEN 'Active'
        WHEN CURDATE() > s.end_date THEN 'Expired'
        WHEN s.is_active = FALSE THEN 'Cancelled'
        ELSE 'Future'
    END as status
FROM subscriptions s
JOIN users u ON s.user_id = u.id;

-- Daily revenue summary
CREATE VIEW daily_revenue AS
SELECT 
    DATE(payment_date) as payment_day,
    COUNT(*) as transaction_count,
    SUM(amount) as total_revenue,
    AVG(amount) as average_amount
FROM payments 
WHERE status = 'completed'
GROUP BY DATE(payment_date)
ORDER BY payment_day DESC;

-- Station popularity (most used stations)
CREATE VIEW station_popularity AS
SELECT 
    s.name as station_name,
    l.name as line_name,
    COUNT(t1.id) + COUNT(t2.id) as total_usage,
    COUNT(t1.id) as used_as_source,
    COUNT(t2.id) as used_as_destination
FROM stations s
JOIN lines l ON s.line_id = l.id
LEFT JOIN tickets t1 ON s.id = t1.from_station_id
LEFT JOIN tickets t2 ON s.id = t2.to_station_id
GROUP BY s.id, s.name, l.name
ORDER BY total_usage DESC;

-- User travel patterns
CREATE VIEW user_travel_patterns AS
SELECT 
    u.name as user_name,
    u.phone,
    u.is_admin,
    COUNT(t.id) as total_trips,
    AVG(t.fare) as average_fare,
    SUM(t.fare) as total_spent_on_tickets,
    MIN(t.created_at) as first_trip,
    MAX(t.created_at) as last_trip,
    CASE 
        WHEN has_active_subscription(u.id) THEN 'Subscriber'
        ELSE 'Pay-per-ride'
    END as user_type
FROM users u
LEFT JOIN tickets t ON u.id = t.user_id
WHERE t.id IS NOT NULL
GROUP BY u.id, u.name, u.phone, u.is_admin
ORDER BY total_trips DESC;

-- Admin users view
CREATE VIEW admin_users AS
SELECT 
    id,
    name,
    phone,
    email,
    created_at
FROM users 
WHERE is_admin = TRUE
ORDER BY created_at DESC;



-- ============================================
-- 6. TEST QUERIES
-- ============================================

-- Test fare calculation functions
-- SELECT calculate_fare(5) as fare_5_stations;
-- SELECT calculate_fare(12) as fare_12_stations;
-- SELECT calculate_fare(25) as fare_25_stations;

-- Test stations between calculation
-- SELECT calculate_stations_between(11, 19) as stations_maadi_to_sadat;
-- SELECT calculate_fare_between_stations(11, 19) as fare_maadi_to_sadat;

-- Find route between two stations (same line only)
-- SELECT * FROM stations WHERE line_id = 1 AND station_order BETWEEN 11 AND 19;

-- Get user's ticket history
-- SELECT * FROM active_tickets WHERE user_name = 'Ahmed Mohamed';

-- Check subscription status
-- SELECT * FROM subscription_summary WHERE user_name = 'Ahmed Mohamed';

-- View daily revenue
-- SELECT * FROM daily_revenue WHERE payment_day >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);

-- Find most popular stations
-- SELECT * FROM station_popularity LIMIT 10;

-- Analyze user travel patterns
-- SELECT * FROM user_travel_patterns WHERE total_trips >= 1;

-- Check journey fare accuracy
-- SELECT * FROM journey_analysis;

-- Find users without active subscriptions who travel frequently
-- SELECT * FROM user_travel_patterns 
-- WHERE user_type = 'Pay-per-ride' AND total_trips > 2
-- ORDER BY total_spent_on_tickets DESC;

-- View all admin users
-- SELECT * FROM admin_users;

-- Check if a specific user is admin
-- SELECT is_user_admin(3) as is_admin;