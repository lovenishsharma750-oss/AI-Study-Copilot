"""Mock-only tests for the email/password authentication foundation."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import AuthResponse, AuthUserResponse, SessionResponse
from app.services.auth import AuthenticationError, login, signup


USER_ID = "6e1dfde9-e9d4-47d0-aec9-f7c1b0b8d212"


def auth_response(*, with_session: bool = True) -> SimpleNamespace:
    session = None
    if with_session:
        session = SimpleNamespace(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
            expires_at=1_800_000_000,
            expires_in=3600,
            token_type="bearer",
        )
    return SimpleNamespace(user=SimpleNamespace(id=USER_ID, email="learner@example.com"), session=session)


class AuthenticationServiceTests(unittest.TestCase):
    @patch("app.services.auth.get_supabase_client")
    def test_signup_sends_name_metadata_without_manual_profile_insert(self, get_client: Mock) -> None:
        client = Mock()
        client.auth.sign_up.return_value = auth_response(with_session=False)
        get_client.return_value = client

        result = signup(name="Learner Name", email="learner@example.com", password="safe-password")

        client.auth.sign_up.assert_called_once_with(
            {
                "email": "learner@example.com",
                "password": "safe-password",
                "options": {"data": {"full_name": "Learner Name"}},
            }
        )
        client.table.assert_not_called()
        self.assertEqual(result.user.id, USER_ID)
        self.assertIsNone(result.session)

    @patch("app.services.auth.get_supabase_client")
    def test_login_returns_safe_user_and_session(self, get_client: Mock) -> None:
        client = Mock()
        client.auth.sign_in_with_password.return_value = auth_response()
        get_client.return_value = client

        result = login(email="learner@example.com", password="safe-password")

        client.auth.sign_in_with_password.assert_called_once_with(
            {"email": "learner@example.com", "password": "safe-password"}
        )
        self.assertEqual(result.user.email, "learner@example.com")
        self.assertEqual(result.session.access_token, "mock-access-token")
        self.assertNotIn("password", result.model_dump())

    @patch("app.services.auth.get_supabase_client")
    def test_auth_failures_become_authentication_errors(self, get_client: Mock) -> None:
        client = Mock()
        client.auth.sign_in_with_password.side_effect = RuntimeError("network failure")
        get_client.return_value = client

        with self.assertRaises(AuthenticationError):
            login(email="learner@example.com", password="safe-password")

class AuthenticationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_signup_request_validation(self) -> None:
        response = self.client.post(
            "/api/auth/signup",
            json={"name": "", "email": "not-an-email", "password": "short"},
        )

        self.assertEqual(response.status_code, 422)

    def test_login_request_validation(self) -> None:
        response = self.client.post(
            "/api/auth/login", json={"email": "not-an-email", "password": "short"}
        )

        self.assertEqual(response.status_code, 422)

    @patch("app.api.auth.signup")
    def test_signup_route_returns_created_response(self, signup_mock: Mock) -> None:
        signup_mock.return_value = signup_result()

        response = self.client.post(
            "/api/auth/signup",
            json={"name": "Learner Name", "email": "learner@example.com", "password": "safe-password"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["id"], USER_ID)
        signup_mock.assert_called_once_with(
            name="Learner Name", email="learner@example.com", password="safe-password"
        )

    @patch("app.api.auth.login")
    def test_login_auth_failure_returns_safe_message(self, login_mock: Mock) -> None:
        login_mock.side_effect = AuthenticationError()

        response = self.client.post(
            "/api/auth/login", json={"email": "learner@example.com", "password": "safe-password"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid email or password.")

def signup_result() -> AuthResponse:
    """Build a service result without contacting Supabase."""
    return AuthResponse(
        user=AuthUserResponse(id=USER_ID, email="learner@example.com"),
        session=SessionResponse(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
            expires_at=1_800_000_000,
            expires_in=3600,
            token_type="bearer",
        ),
    )


if __name__ == "__main__":
    unittest.main()
