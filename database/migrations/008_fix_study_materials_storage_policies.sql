-- Fix storage policies for the 4-part study-materials path:
-- <user_id>/<subject_id>/<document_id>/<filename>

DROP POLICY IF EXISTS study_materials_insert_own
ON storage.objects;

DROP POLICY IF EXISTS study_materials_select_own
ON storage.objects;

DROP POLICY IF EXISTS study_materials_delete_own
ON storage.objects;


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