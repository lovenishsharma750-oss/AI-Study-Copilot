"""Mock-only tests for private study-material document uploads."""

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.dependencies import CurrentUser, get_current_user
from app.main import app
from app.schemas.document import DocumentResponse
from app.services.documents import (
    DocumentServiceError,
    DocumentValidationError,
    STUDY_MATERIALS_BUCKET,
    SubjectNotFoundError,
    delete_document,
    get_document,
    list_documents,
    upload_document,
)


USER_ID = "6e1dfde9-e9d4-47d0-aec9-f7c1b0b8d212"
OTHER_USER_ID = "b0625537-2d59-4ec2-9628-ae10c0da2fc6"
SUBJECT_ID = "59dbbf67-2a10-4c01-9b40-b0b4894c188d"
DOCUMENT_ID = "b01aebbb-28c9-41d3-8bbd-d93d3e6ab5fa"
DOCUMENT_RECORD = {
    "id": DOCUMENT_ID,
    "subject_id": SUBJECT_ID,
    "file_name": "notes.pdf",
    "storage_path": f"{USER_ID}/{SUBJECT_ID}/{DOCUMENT_ID}/notes.pdf",
    "mime_type": "application/pdf",
    "created_at": "2026-09-05T12:00:00+00:00",
}


def owned_client(*, document_data: list[dict] | None = None) -> tuple[MagicMock, MagicMock]:
    """Build a mock Supabase client whose subject query confirms ownership."""
    client = MagicMock()
    subject_table = MagicMock()
    subject_query = subject_table.select.return_value
    subject_query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
        data=[{"id": SUBJECT_ID}]
    )
    document_table = MagicMock()
    client.table.side_effect = [subject_table, document_table]
    if document_data is not None:
        document_table.select.return_value.eq.return_value.order.return_value.execute.return_value = (
            SimpleNamespace(data=document_data)
        )
    return client, document_table


class DocumentServiceTests(unittest.TestCase):
    @patch("app.services.documents.uuid4", return_value=UUID(DOCUMENT_ID))
    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_uploads_each_supported_file_type(self, get_client: Mock, _: Mock) -> None:
        for filename in ("notes.pdf", "slides.ppt", "slides.pptx", "outline.docx"):
            with self.subTest(filename=filename):
                record = {**DOCUMENT_RECORD, "file_name": filename}
                client, document_table = owned_client()
                document_table.insert.return_value.execute.return_value = SimpleNamespace(data=[record])
                get_client.return_value = client

                result = upload_document(
                    user_id=USER_ID,
                    access_token="mock-token",
                    subject_id=SUBJECT_ID,
                    filename=filename,
                    content=b"test file",
                )

                bucket = client.storage.from_.return_value
                client.storage.from_.assert_called_once_with(STUDY_MATERIALS_BUCKET)
                self.assertEqual(result.file_name, filename)
                self.assertTrue(bucket.upload.called)

    def test_rejects_unsupported_extension(self) -> None:
        with self.assertRaises(DocumentValidationError):
            upload_document(
                user_id=USER_ID,
                access_token="mock-token",
                subject_id=SUBJECT_ID,
                filename="notes.txt",
                content=b"not allowed",
            )

    def test_rejects_empty_file(self) -> None:
        with self.assertRaises(DocumentValidationError):
            upload_document(
                user_id=USER_ID,
                access_token="mock-token",
                subject_id=SUBJECT_ID,
                filename="notes.pdf",
                content=b"",
            )

    @patch("app.services.documents.uuid4", return_value=UUID(DOCUMENT_ID))
    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_cleans_up_storage_when_metadata_insert_fails(
        self, get_client: Mock, _: Mock
    ) -> None:
        client, document_table = owned_client()
        document_table.insert.return_value.execute.side_effect = RuntimeError("metadata failure")
        get_client.return_value = client

        with self.assertRaises(DocumentServiceError):
            upload_document(
                user_id=USER_ID,
                access_token="mock-token",
                subject_id=SUBJECT_ID,
                filename="notes.pdf",
                content=b"test file",
            )

        client.storage.from_.return_value.remove.assert_called_once_with(
            [DOCUMENT_RECORD["storage_path"]]
        )

    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_lists_documents_for_owned_subject(self, get_client: Mock) -> None:
        client, _ = owned_client(document_data=[DOCUMENT_RECORD])
        get_client.return_value = client

        result = list_documents(
            user_id=USER_ID, access_token="mock-token", subject_id=SUBJECT_ID
        )

        self.assertEqual([document.id for document in result], [DOCUMENT_ID])

    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_gets_document_metadata_for_owned_subject(self, get_client: Mock) -> None:
        client, document_table = owned_client()
        document_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[DOCUMENT_RECORD])
        )
        get_client.return_value = client

        result = get_document(
            user_id=USER_ID,
            access_token="mock-token",
            subject_id=SUBJECT_ID,
            document_id=DOCUMENT_ID,
        )

        self.assertEqual(result.storage_path, DOCUMENT_RECORD["storage_path"])

    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_deletes_storage_before_owned_metadata(self, get_client: Mock) -> None:
        client, lookup_table = owned_client()
        lookup_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[DOCUMENT_RECORD])
        )
        delete_table = MagicMock()
        delete_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[DOCUMENT_RECORD])
        )
        subject_table = MagicMock()
        subject_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[{"id": SUBJECT_ID}])
        )
        client.table.side_effect = [subject_table, lookup_table, delete_table]
        get_client.return_value = client

        deleted = delete_document(
            user_id=USER_ID,
            access_token="mock-token",
            subject_id=SUBJECT_ID,
            document_id=DOCUMENT_ID,
        )

        client.storage.from_.return_value.remove.assert_called_once_with(
            [DOCUMENT_RECORD["storage_path"]]
        )
        self.assertTrue(deleted)

    @patch("app.services.documents.get_authenticated_supabase_client")
    def test_rejects_document_access_for_unowned_subject(self, get_client: Mock) -> None:
        client = MagicMock()
        subject_table = MagicMock()
        subject_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[])
        )
        client.table.return_value = subject_table
        get_client.return_value = client

        with self.assertRaises(SubjectNotFoundError):
            list_documents(
                user_id=USER_ID, access_token="mock-token", subject_id=SUBJECT_ID
            )


class DocumentRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id=USER_ID, access_token="mock-token"
        )
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    @patch("app.api.documents.upload_document")
    def test_upload_route_accepts_pdf_multipart(self, upload_mock: Mock) -> None:
        upload_mock.return_value = DocumentResponse.model_validate(DOCUMENT_RECORD)

        response = self.client.post(
            f"/api/subjects/{SUBJECT_ID}/documents",
            files={"file": ("notes.pdf", b"pdf content", "application/pdf")},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], DOCUMENT_ID)

    @patch("app.api.documents.get_document")
    def test_foreign_document_is_not_found(self, get_mock: Mock) -> None:
        get_mock.side_effect = SubjectNotFoundError()

        response = self.client.get(f"/api/subjects/{SUBJECT_ID}/documents/{DOCUMENT_ID}")

        self.assertEqual(response.status_code, 404)


class DocumentAuthenticationTests(unittest.TestCase):
    def test_document_routes_require_authentication(self) -> None:
        response = TestClient(app).get(f"/api/subjects/{SUBJECT_ID}/documents")

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
