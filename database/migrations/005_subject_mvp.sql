-- AI Study Copilot: protect each student's subject workspace.

ALTER TABLE public.subjects ENABLE ROW LEVEL SECURITY;

CREATE POLICY subjects_select_own
    ON public.subjects
    FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

CREATE POLICY subjects_insert_own
    ON public.subjects
    FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY subjects_update_own
    ON public.subjects
    FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY subjects_delete_own
    ON public.subjects
    FOR DELETE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);
