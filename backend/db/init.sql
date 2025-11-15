-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create discs table
CREATE TABLE IF NOT EXISTS discs (
    id SERIAL PRIMARY KEY,
    owner_name VARCHAR(255) NOT NULL,
    owner_contact VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'registered', -- 'registered', 'stolen', 'found'
    disc_model VARCHAR(255),
    disc_color VARCHAR(100),
    notes TEXT,
    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stolen_date TIMESTAMP,
    found_date TIMESTAMP,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create disc_images table
CREATE TABLE IF NOT EXISTS disc_images (
    id SERIAL PRIMARY KEY,
    disc_id INTEGER NOT NULL REFERENCES discs(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    image_path TEXT,
    model_name VARCHAR(50) NOT NULL, -- 'clip', 'dinov2', etc.
    embedding vector(768), -- Using max dimension (DINOv2), CLIP will be 512 with padding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast similarity search
CREATE INDEX IF NOT EXISTS clip_embeddings_idx
    ON disc_images USING ivfflat (embedding vector_cosine_ops)
    WHERE model_name = 'clip';

CREATE INDEX IF NOT EXISTS dinov2_embeddings_idx
    ON disc_images USING ivfflat (embedding vector_cosine_ops)
    WHERE model_name = 'dinov2';

-- Create index on disc_id for faster lookups
CREATE INDEX IF NOT EXISTS disc_images_disc_id_idx ON disc_images(disc_id);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS discs_status_idx ON discs(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_discs_updated_at BEFORE UPDATE ON discs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
