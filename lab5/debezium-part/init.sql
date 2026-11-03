CREATE DATABASE IF NOT EXISTS college;

CREATE TABLE IF NOT EXISTS college.students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

INSERT INTO college.students (id, name, department)
SELECT 1, 'Asha', 'Computer Engineering'
WHERE NOT EXISTS (SELECT 1 FROM college.students WHERE id = 1);

-- Example credentials for this loopback-only lab; also used in register.json.
CREATE USER IF NOT EXISTS 'debezium'@'localhost' IDENTIFIED BY 'debezium';
CREATE USER IF NOT EXISTS 'debezium'@'127.0.0.1' IDENTIFIED BY 'debezium';
ALTER USER 'debezium'@'localhost' IDENTIFIED BY 'debezium';
ALTER USER 'debezium'@'127.0.0.1' IDENTIFIED BY 'debezium';

GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT,
    LOCK TABLES ON *.* TO 'debezium'@'localhost';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT,
    LOCK TABLES ON *.* TO 'debezium'@'127.0.0.1';
