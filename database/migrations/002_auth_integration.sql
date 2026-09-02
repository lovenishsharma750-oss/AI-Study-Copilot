-- AI Study Copilot: integrate public user profiles with Supabase Auth.
-- public.users.id is supplied from auth.users.id; passwords remain in Supabase Auth.

ALTER TABLE public.users
    DROP COLUMN IF EXISTS password_hash,
    ALTER COLUMN id DROP DEFAULT;

ALTER TABLE public.users
    ADD CONSTRAINT users_id_auth_users_fkey
    FOREIGN KEY (id)
    REFERENCES auth.users (id)
    ON DELETE CASCADE;
