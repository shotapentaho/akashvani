-- Add user preference metadata to existing API call records.
ALTER TABLE public.api_calls
    ADD COLUMN IF NOT EXISTS language_of_choice VARCHAR(100),
    ADD COLUMN IF NOT EXISTS voice_speed VARCHAR(50),
    ADD COLUMN IF NOT EXISTS voice_gender VARCHAR(50),
    ADD COLUMN IF NOT EXISTS voice_duration VARCHAR(50);
