"""Tests for backend environment configuration."""

import unittest
from unittest.mock import patch

from app.core import config


class SupabaseConfigurationTests(unittest.TestCase):
    def test_missing_values_raise_clear_error(self) -> None:
        with patch.object(config, "SUPABASE_URL", None), patch.object(
            config, "SUPABASE_KEY", None
        ):
            with self.assertRaisesRegex(
                RuntimeError, "SUPABASE_URL, SUPABASE_KEY"
            ):
                config.get_supabase_settings()

    def test_values_are_loaded_without_network_access(self) -> None:
        with patch.object(config, "SUPABASE_URL", "https://example.supabase.co"), patch.object(
            config, "SUPABASE_KEY", "test-key"
        ):
            settings = config.get_supabase_settings()

        self.assertEqual(settings.url, "https://example.supabase.co")
        self.assertEqual(settings.key, "test-key")


if __name__ == "__main__":
    unittest.main()
