-- migrate:up

CREATE TABLE IF NOT EXISTS "items" (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    price INT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    short_description TEXT NOT NULL,
    images text[] NOT NULL,
    is_sold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "sessions" (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "sessionsitems" (
    item_id UUID NOT NULL REFERENCES "items" ("id") ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES "sessions" ("id") ON DELETE CASCADE,
    PRIMARY KEY (item_id, session_id) 
);

-- migrate:down

DROP TABLE IF EXISTS "sessionsitems";
DROP TABLE IF EXISTS "items";
DROP TABLE IF EXISTS "sessions";
