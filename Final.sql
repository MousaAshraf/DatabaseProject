-- ============================================
-- CAIRO METRO SYSTEM 
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metro lines
CREATE TABLE lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(20)
);

-- Metro stations
CREATE TABLE stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    line_id INT,
    station_order INT NOT NULL,
    zone INT DEFAULT 1,
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
    payment_method ENUM('card', 'cash', 'mobile') NOT NULL,
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

-- Insert metro lines (IDs will be auto-generated)
INSERT INTO lines (name, color) VALUES 
('Line 1 (Red)', 'Red'),
('Line 2 (Yellow)', 'Yellow'),
('Line 3 (Green)', 'Green'),
('Line 4 (Blue)', 'Blue');

-- LINE 1: Helwan - New El Marg (35 stations)
INSERT INTO stations (name, line_id, station_order, zone) VALUES 
('Helwan', 1, 1, 1),
('Ain Helwan', 1, 2, 1),
('Helwan University', 1, 3, 1),
('Wadi Hof', 1, 4, 1),
('Hadayek Helwan', 1, 5, 1),
('El Maasara', 1, 6, 1),
('Tora El Asmant', 1, 7, 1),
('Kozzika', 1, 8, 1),
('Tora El Balad', 1, 9, 1),
('Sakanat El Maadi', 1, 10, 2),
('Maadi', 1, 11, 2),
('Hadayek El Maadi', 1, 12, 2),
('Dar El Salam', 1, 13, 2),
('El Zahraa', 1, 14, 2),
('Mar Girgis', 1, 15, 2),
('El Malek El Saleh', 1, 16, 2),
('Al Sayeda Zeinab', 1, 17, 3),
('Saad Zaghloul', 1, 18, 3),
('Sadat', 1, 19, 3),
('Nasser', 1, 20, 3),
('Orabi', 1, 21, 3),
('Al Shohadaa', 1, 22, 3),
('Ghamra', 1, 23, 3),
('El Demerdash', 1, 24, 3),
('Manshiet El Sadr', 1, 25, 4),
('Kobri El Qobba', 1, 26, 4),
('Hammamat El Qobba', 1, 27, 4),
('Saray El Qobba', 1, 28, 4),
('Hadayeq El Zeitoun', 1, 29, 4),
('Helmeyet El Zeitoun', 1, 30, 4),
('El Matareyya', 1, 31, 4),
('Ain Shams', 1, 32, 4),
('Ezbet El Nakhl', 1, 33, 5),
('El Marg', 1, 34, 5),
('New El Marg', 1, 35, 5);

-- LINE 2: Shubra El Kheima - Monib (20 stations)
INSERT INTO stations (name, line_id, station_order, zone) VALUES 
('Shubra El Kheima', 2, 1, 1),
('Koliet El Zeraa', 2, 2, 1),
('Mezallat', 2, 3, 1),
('Khalafawy', 2, 4, 1),
('St. Teresa', 2, 5, 1),
('Rod El Farag', 2, 6, 2),
('Masarra', 2, 7, 2),
('Al Shohadaa L2', 2, 8, 3),
('Attaba', 2, 9, 3),
('Mohamed Naguib', 2, 10, 3),
('Sadat L2', 2, 11, 3),
('Opera', 2, 12, 3),
('Dokki', 2, 13, 3),
('Bohooth', 2, 14, 3),
('Cairo University', 2, 15, 4),
('Faisal', 2, 16, 4),
('Giza', 2, 17, 4),
('Omm El Masryeen', 2, 18, 4),
('Sakiat Mekki', 2, 19, 5),
('Monib', 2, 20, 5);

-- LINE 3: Adly Mansour - Kit Kat (34 stations) 
INSERT INTO stations (name, line_id, station_order, zone) VALUES 
('Adly Mansour', 3, 1, 6),
('El Haykestep', 3, 2, 6),
('Omar Ibn El Khattab', 3, 3, 6),
('Qobaa', 3, 4, 6),
('Hesham Barakat', 3, 5, 6),
('El Nozha', 3, 6, 6),
('Nadi El Shams', 3, 7, 5),
('Alf Maskan', 3, 8, 5),
('Heliopolis Square', 3, 9, 5),
('Haroun', 3, 10, 5),
('Al Ahram', 3, 11, 5),
('Koleyet El Banat', 3, 12, 4),
('Stadium', 3, 13, 4),
('Fair Zone', 3, 14, 4),
('Abbassia', 3, 15, 4),
('Abdou Pasha', 3, 16, 4),
('El Geish', 3, 17, 4),
('Bab El Shaaria', 3, 18, 4),
('Attaba L3', 3, 19, 3),
('Nasser L3', 3, 20, 3),
('Maspero', 3, 21, 3),
('Safaa Hegazy', 3, 22, 3),
('Kit Kat', 3, 23, 3),
('Sudan', 3, 24, 3),
('Imbaba', 3, 25, 3),
('El Bohy', 3, 26, 2),
('El Kawmeya El Arabeya', 3, 27, 2),
('El Tariq El Daery', 3, 28, 2),
('El Mounib L3', 3, 29, 2),
('Gizet El Arab', 3, 30, 2),
('El Malek El Saleh L3', 3, 31, 2),
('Wadi Hof L3', 3, 32, 1),
('Hadayek Helwan L3', 3, 33, 1),
('Helwan L3', 3, 34, 1);

-- LINE 4: Stadium - New Administrative Capital (12 stations)
INSERT INTO stations (name, line_id, station_order, zone) VALUES 
('Stadium L4', 4, 1, 4),
('Medical City', 4, 2, 4),
('El Fustat', 4, 3, 3),
('El Malek El Saleh L4', 4, 4, 3),
('El Bassatine', 4, 5, 3),
('El Zahraa L4', 4, 6, 2),
('New Maadi', 4, 7, 2),
('Maadi El Gadida', 4, 8, 2),
('Saray El Qobba L4', 4, 9, 4),
('New Cairo', 4, 10, 5),
('El Rehab', 4, 11, 6),
('New Administrative Capital', 4, 12, 6);

-- Create sample users
INSERT INTO users (name, phone, email, password) VALUES 
('Mousa Ashraf', '+201207919519', 'mousaashraf88@gmail.com', '12345'),
('Ahmed Mohamed', '+201234567890', 'ahmed@example.com', 'hashed_password_123'),
('Sara Ali', '+201098765432', 'sara.ali@example.com', 'secure_pass_456'),
('Omar Hassan', '+201555444333', 'omar.hassan@example.com', 'my_password_789');

-- Sample subscriptions
INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, price, is_active) VALUES 
(1, 'monthly', '2025-05-01', '2025-05-31', 180.00, TRUE),
(2, 'quarterly', '2025-04-01', '2025-06-30', 500.00, TRUE),
(3, 'yearly', '2025-01-01', '2025-12-31', 1800.00, TRUE);

-- Sample tickets
INSERT INTO tickets (user_id, from_station_id, to_station_id, fare, status, expires_at) VALUES 
(4, 11, 19, 8.00, 'active', DATE_ADD(NOW(), INTERVAL 2 HOUR)),
(4, 35, 1, 20.00, 'used', DATE_ADD(NOW(), INTERVAL -1 DAY)),
(1, 50, 55, 10.00, 'active', DATE_ADD(NOW(), INTERVAL 3 HOUR));

-- Sample payments
INSERT INTO payments (user_id, subscription_id, amount, payment_method, status) VALUES 
(1, 1, 180.00, 'card', 'completed'),
(2, 2, 500.00, 'mobile', 'completed'),
(3, 3, 1800.00, 'card', 'completed');

INSERT INTO payments (user_id, ticket_id, amount, payment_method, status) VALUES 
(4, 1, 8.00, 'cash', 'completed'),
(4, 2, 20.00, 'card', 'completed'),
(1, 3, 10.00, 'mobile', 'completed');

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

-- Get station zone by ID
CREATE FUNCTION get_station_zone(station_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE station_zone INT DEFAULT 1;
    
    SELECT zone INTO station_zone
    FROM stations 
    WHERE id = station_id;
      
    RETURN station_zone;
END//

DELIMITER ;

-- ============================================
-- 5.  VIEWS 
-- ============================================

-- Original: Active tickets view
CREATE VIEW active_tickets AS
SELECT 
    t.id,
    u.name as user_name,
    u.phone as user_phone,
    s1.name as from_station,
    s2.name as to_station,
    l.name as line_name,
    t.fare,
    t.status,
    t.created_at,
    t.expires_at
FROM tickets t
JOIN users u ON t.user_id = u.id
JOIN stations s1 ON t.from_station_id = s1.id
JOIN stations s2 ON t.to_station_id = s2.id
JOIN lines l ON s1.line_id = l.id
WHERE t.status = 'active';

-- Original: Subscription summary view
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
        WHEN CURDATE() BETWEEN s.start_date AND s.end_date THEN 'Active'
        WHEN CURDATE() > s.end_date THEN 'Expired'
        ELSE 'Future'
    END as status
FROM subscriptions s
JOIN users u ON s.user_id = u.id;

-- NEW VIEW 1: Daily revenue summary
CREATE VIEW daily_revenue AS
SELECT 
    DATE(payment_date) as payment_day,
    payment_method,
    COUNT(*) as transaction_count,
    SUM(amount) as total_revenue,
    AVG(amount) as average_amount
FROM payments 
WHERE status = 'completed'
GROUP BY DATE(payment_date), payment_method
ORDER BY payment_day DESC, payment_method;

-- NEW VIEW 2: Station popularity (most used stations)
CREATE VIEW station_popularity AS
SELECT 
    s.name as station_name,
    l.name as line_name,
    s.zone,
    COUNT(t1.id) + COUNT(t2.id) as total_usage,
    COUNT(t1.id) as used_as_source,
    COUNT(t2.id) as used_as_destination
FROM stations s
JOIN lines l ON s.line_id = l.id
LEFT JOIN tickets t1 ON s.id = t1.from_station_id
LEFT JOIN tickets t2 ON s.id = t2.to_station_id
GROUP BY s.id, s.name, l.name, s.zone
ORDER BY total_usage DESC;

-- NEW VIEW 3: User travel patterns
CREATE VIEW user_travel_patterns AS
SELECT 
    u.name as user_name,
    u.phone,
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
GROUP BY u.id, u.name, u.phone
ORDER BY total_trips DESC;

-- ============================================
-- 6. TEST QUERIES
-- ============================================

-- Find route between two stations (same line only)
-- SELECT * FROM stations WHERE line_id = 1 AND station_order BETWEEN 11 AND 19;

-- Get user's ticket history
-- SELECT * FROM active_tickets WHERE user_name = 'Ahmed Mohamed';

-- Check subscription status
-- SELECT * FROM subscription_summary WHERE user_name = 'Ahmed Mohamed';

-- Calculate fare for a journey
-- SELECT calculate_fare(ABS(19 - 11) + 1) as fare;

-- View daily revenue
-- SELECT * FROM daily_revenue WHERE payment_day >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);

-- Find most popular stations
-- SELECT * FROM station_popularity LIMIT 10;

-- Analyze user travel patterns
-- SELECT * FROM user_travel_patterns WHERE total_trips > 5;

-- Find users without active subscriptions who travel frequently
-- SELECT * FROM user_travel_patterns 
-- WHERE user_type = 'Pay-per-ride' AND total_trips > 10
-- ORDER BY total_spent_on_tickets DESC;