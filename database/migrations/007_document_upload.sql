-- AI Study Copilot: private study-material uploads and owner-only document access.

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY documents_select_own
    ON public.documents
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id = documents.subject_id
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY documents_insert_own
    ON public.documents
    FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id = documents.subject_id
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY documents_update_own
    ON public.documents
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id = documents.subject_id
              AND subjects.user_id = (SELECT auth.uid())
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id = documents.subject_id
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY documents_delete_own
    ON public.documents
    FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id = documents.subject_id
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

GRANT SELECT, INSERT, DELETE
ON TABLE public.documents
TO authenticated;

INSERT INTO storage.buckets (id, name, public)
VALUES ('study-materials', 'study-materials', FALSE)
ON CONFLICT (id) DO UPDATE
SET public = EXCLUDED.public;

CREATE POLICY study_materials_select_own
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'study-materials'
        AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
        AND EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id::text = (storage.foldername(name))[2]
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY study_materials_insert_own
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'study-materials'
        AND array_length(storage.foldername(name), 1) = 3
        AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
        AND EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id::text = (storage.foldername(name))[2]
              AND subjects.user_id = (SELECT auth.uid())
        )
    );

CREATE POLICY study_materials_delete_own
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'study-materials'
        AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
        AND EXISTS (
            SELECT 1
            FROM public.subjects
            WHERE subjects.id::text = (storage.foldername(name))[2]
              AND subjects.user_id = (SELECT auth.uid())
        )
    );
