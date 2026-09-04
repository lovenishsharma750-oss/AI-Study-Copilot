-- AI Study Copilot: create public user profiles when Supabase Auth users are created.
-- The SECURITY DEFINER function runs as its owner, so it can insert while public.users
-- remains protected by row-level security for normal client requests.

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NULLIF(pg_catalog.btrim(NEW.raw_user_meta_data ->> 'full_name'), ''),
            'New user'
        )
    );

    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.handle_new_auth_user() FROM PUBLIC;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_auth_user();
