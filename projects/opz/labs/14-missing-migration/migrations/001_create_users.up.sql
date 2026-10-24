CREATE TABLE users (
    id    serial PRIMARY KEY,
    name  text NOT NULL,
    email text NOT NULL
);

INSERT INTO users (name, email) VALUES
    ('Amina', 'amina@example.com'),
    ('Bilal', 'bilal@example.com');
