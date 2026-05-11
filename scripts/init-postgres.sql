CREATE DATABASE langfuse;
GRANT ALL PRIVILEGES ON DATABASE langfuse TO airflow;

\connect postgres

CREATE TABLE documents (
    id              VARCHAR(50) PRIMARY KEY,
    title           TEXT NOT NULL,
    url             TEXT,
    source_type     VARCHAR(20),
    published_date  DATE,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

CREATE TABLE creators (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    UNIQUE(name)
);

CREATE TABLE document_creators (
    document_id VARCHAR(50) REFERENCES documents(id),
    creator_id  INTEGER REFERENCES creators(id),
    PRIMARY KEY (document_id, creator_id)
);

CREATE TABLE chunks (
    id              SERIAL PRIMARY KEY,
    document_id     VARCHAR(50) REFERENCES documents(id),
    chunk_index     INTEGER,
    text            TEXT NOT NULL,
    token_count     INTEGER,
    opensearch_id   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
