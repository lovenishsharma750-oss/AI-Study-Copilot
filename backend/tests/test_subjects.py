"""Mock-only tests for authenticated subject workspace operations."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.api.dependencies import CurrentUser, get_current_user
from app.main import app
from app.schemas.subject import SubjectResponse
from app.services.subjects import (
    create_subject,
    delete_subject,
    get_subject,
    list_subjects,
    update_subject,
)


USER_ID = "6e1dfde9-e9d4-47d0-aec9-f7c1b0b8d212"
OTHER_USER_ID = "b0625537-2d59-4ec2-9628-ae10c0da2fc6"
SUBJECT_ID = "59dbbf67-2a10-4c01-9b40-b0b4894c188d"
SUBJECT_RECORD = {
    "id": SUBJECT_ID,
    "name": "DBMS",
    "created_at": "2026-09-04T12:00:00+00:00",
}


class SubjectServiceTests(unittest.TestCase):
    @patch("app.services.subjects.get_authenticated_supabase_client")
    def test_create_subject_uses_authenticated_owner(self, get_client: Mock) -> None:
        client = Mock()
        client.table.return_value.insert.return_value.execute.return_value = SimpleNamespace(
            data=[SUBJECT_RECORD]
        )
        get_client.return_value = client

        result = create_subject(user_id=USER_ID, access_token="mock-token", name="DBMS")

        client.table.assert_called_once_with("subjects")
        client.table.return_value.insert.assert_called_once_with(
            {"user_id": USER_ID, "name": "DBMS"}
        )
        self.assertEqual(result.id, SUBJECT_ID)

    @patch("app.services.subjects.get_authenticated_supabase_client")
    def test_list_subjects_filters_by_authenticated_owner(self, get_client: Mock) -> None:
        client = Mock()
        query = client.table.return_value.select.return_value
        query.eq.return_value.order.return_value.execute.return_value = SimpleNamespace(
            data=[SUBJECT_RECORD]
        )
        get_client.return_value = client

        result = list_subjects(user_id=USER_ID, access_token="mock-token")

        query.eq.assert_called_once_with("user_id", USER_ID)
        self.assertEqual([subject.name for subject in result], ["DBMS"])

    @patch("app.services.subjects.get_authenticated_supabase_client")
    def test_get_subject_denies_another_users_subject(self, get_client: Mock) -> None:
        client = Mock()
        query = client.table.return_value.select.return_value
        query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])
        get_client.return_value = client

        result = get_subject(
            user_id=USER_ID, access_token="mock-token", subject_id=SUBJECT_ID
        )

        query.eq.assert_called_once_with("id", SUBJECT_ID)
        query.eq.return_value.eq.assert_called_once_with("user_id", USER_ID)
        self.assertIsNone(result)

    @patch("app.services.subjects.get_authenticated_supabase_client")
    def test_update_subject_filters_by_authenticated_owner(self, get_client: Mock) -> None:
        client = Mock()
        query = client.table.return_value.update.return_value
        query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
            data=[{**SUBJECT_RECORD, "name": "Operating Systems"}]
        )
        get_client.return_value = client

        result = update_subject(
            user_id=USER_ID,
            access_token="mock-token",
            subject_id=SUBJECT_ID,
            name="Operating Systems",
        )

        client.table.return_value.update.assert_called_once_with({"name": "Operating Systems"})
        query.eq.return_value.eq.assert_called_once_with("user_id", USER_ID)
        self.assertEqual(result.name, "Operating Systems")

    @patch("app.services.subjects.get_authenticated_supabase_client")
    def test_delete_subject_filters_by_authenticated_owner(self, get_client: Mock) -> None:
        client = Mock()
        query = client.table.return_value.delete.return_value
        query.eq.return_value.eq.return_value.execute.return_value = SimpleNamespace(
            data=[SUBJECT_RECORD]
        )
        get_client.return_value = client

        deleted = delete_subject(
            user_id=USER_ID, access_token="mock-token", subject_id=SUBJECT_ID
        )

        query.eq.return_value.eq.assert_called_once_with("user_id", USER_ID)
        self.assertTrue(deleted)


class SubjectRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id=USER_ID, access_token="mock-token"
        )
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_empty_subject_name_is_rejected(self) -> None:
        response = self.client.post("/api/subjects", json={"name": "   "})

        self.assertEqual(response.status_code, 422)

    @patch("app.api.subjects.create_subject")
    def test_create_subject_route(self, create_mock: Mock) -> None:
        create_mock.return_value = service_subject()

        response = self.client.post("/api/subjects", json={"name": "DBMS"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "DBMS")
        create_mock.assert_called_once_with(
            user_id=USER_ID, access_token="mock-token", name="DBMS"
        )

    @patch("app.api.subjects.get_subject")
    def test_getting_another_users_subject_returns_not_found(self, get_mock: Mock) -> None:
        get_mock.return_value = None

        response = self.client.get(f"/api/subjects/{SUBJECT_ID}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Subject not found.")


class SubjectAuthenticationTests(unittest.TestCase):
    def test_subject_routes_require_a_bearer_token(self) -> None:
        response = TestClient(app).get("/api/subjects")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication is required.")


def service_subject() -> SubjectResponse:
    """Return a subject service result without contacting Supabase."""
    return SubjectResponse.model_validate(SUBJECT_RECORD)


if __name__ == "__main__":
    unittest.main()
