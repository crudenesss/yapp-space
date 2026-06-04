#!/bin/bash

createdb ${PGDATABASE}

psql -c "\c ${PGDATABASE};"

# Create all tables 
psql -c "CREATE TABLE roles ( 
    role_id INTEGER PRIMARY KEY,
    role_name VARCHAR(16)
);"

psql -c "CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(32) NOT NULL,
    passwd VARCHAR(256) NOT NULL,
    email VARCHAR(320) NOT NULL,
    bio VARCHAR(256),
    profile_picture VARCHAR(40),
    role_id INTEGER,

    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);"

psql -c "CREATE TABLE messages (
    message_id VARCHAR(36) PRIMARY KEY,
    message_content VARCHAR(4096) NOT NULL,
    message_timestamp TIMESTAMPTZ NOT NULL,
    message_edited BOOLEAN NOT NULL,
    user_id VARCHAR(36),

    FOREIGN KEY (user_id) REFERENCES users(user_id)
);"

# Create user who will communicate with database
psql -c "CREATE ROLE \"${POSTGRES_USERNAME}\" LOGIN PASSWORD '${POSTGRES_PASSWORD}' INHERIT;"

# Set inly required permissions
psql -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"roles\" TO \"${POSTGRES_USERNAME}\";" \
    -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"users\" TO \"${POSTGRES_USERNAME}\";" \
    -c "GRANT SELECT, INSERT, UPDATE, DELETE ON \"messages\" TO \"${POSTGRES_USERNAME}\";"

# Insert starter data
PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USERNAME} -c \
    "INSERT INTO roles VALUES 
    (1, 'Admin'),
    (2, 'Moderator'),
    (3, 'User');"

# Set access rules into pg_hba.conf
echo "local ${PGDATABASE} ${POSTGRES_USERNAME} password
host ${PGDATABASE} ${POSTGRES_USERNAME} samenet password" > /var/lib/postgresql/data/pg_hba.conf