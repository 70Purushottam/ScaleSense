CREATE TABLE items (id INT PRIMARY KEY, val TEXT NOT NULL);
INSERT INTO items SELECT g, 'value-' || g FROM generate_series(0, 999) g;