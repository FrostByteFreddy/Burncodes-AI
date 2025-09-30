-- Add a vector_id column to the tenant_fine_tune table to store the reference to the vector in the vector database.
ALTER TABLE public.tenant_fine_tune ADD COLUMN vector_id TEXT;