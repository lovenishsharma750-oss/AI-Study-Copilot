-- AI Study Copilot: allow authenticated users to exercise subject RLS policies.

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE public.subjects
TO authenticated;
