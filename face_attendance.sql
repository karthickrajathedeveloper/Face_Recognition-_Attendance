CREATE DATABASE IF NOT EXISTS face_attendance;
USE face_attendance;
show databases
-- Table for storing registered users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    face_encoding LONGBLOB NOT NULL
);

-- Table for storing attendance records
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    date DATE,
    time TIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
ALTER TABLE users ADD COLUMN photo LONGBLOB;

Select * from users;
DELETE FROM users WHERE id = 1;

set foreign_key_checks = 0;
