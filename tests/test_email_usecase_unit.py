"""
Unit tests for EmailInvestigationUseCase (tasks 3.1, 3.2, 3.3).

Run: python -m tests.test_email_usecase_unit
"""
import sys
import os
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from internal.usecases.email import EmailInvestigationUseCase
from internal.domain.entities import ScanResult
from internal.infra.exceptions import AdapterError


class TestEmailInvestigationUseCase(unittest.TestCase):
    """Unit tests for EmailInvestigationUseCase."""

    def setUp(self):
        self.mock_provider = Mock()
        self.mock_repo = Mock()
        self.use_case = EmailInvestigationUseCase(
            email_provider=self.mock_provider,
            report_service=self.mock_repo,
        )

    # --- Task 3.1: Valid email passes validation and proceeds to fetch ---
    def test_valid_email_proceeds_to_fetch(self):
        """Valid email with @ proceeds to provider.fetch()."""
        self.mock_provider.fetch.return_value = "# Markdown report"
        self.mock_repo.save_report.return_value = "report/user@example.com_leakcheck.md"

        result = self.use_case.execute("user@example.com", "report/")

        self.mock_provider.fetch.assert_called_once_with("user@example.com", limit=15)
        self.mock_repo.save_report.assert_called_once()
        self.assertEqual(result.markdown_data, "# Markdown report")

    # --- Task 3.2: Email without @ raises ValueError ---
    def test_invalid_email_raises_value_error(self):
        """Email without @ raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.use_case.execute("notanemail", "report/")
        self.assertIn("inválida", str(ctx.exception))
        self.mock_provider.fetch.assert_not_called()

    def test_empty_email_raises_value_error(self):
        """Empty string raises ValueError."""
        with self.assertRaises(ValueError):
            self.use_case.execute("", "report/")
        self.mock_provider.fetch.assert_not_called()

    # --- Task 3.3: execute returns ScanResult with correct full_path ---
    def test_execute_returns_scan_result_with_correct_path(self):
        """execute returns ScanResult with full_path matching output/filename."""
        email = "user@example.com"
        output = "test_reports"
        expected_filename = f"report_{email}_leakcheck.md"
        expected_full_path = f"{output}/{expected_filename}"

        self.mock_provider.fetch.return_value = "# Test report"
        self.mock_repo.save_report.return_value = expected_full_path

        result = self.use_case.execute(email, output)

        self.assertIsInstance(result, ScanResult)
        self.assertEqual(result.filename, expected_filename)
        self.assertEqual(result.output_path, output)
        self.assertEqual(result.full_path, expected_full_path)

    # --- Verify warning: AdapterError propagation ---
    def test_adapter_error_propagates(self):
        """AdapterError from provider.fetch propagates through execute."""
        self.mock_provider.fetch.side_effect = AdapterError("LeakCheck", "API failure")
        with self.assertRaises(AdapterError):
            self.use_case.execute("user@example.com", "report/")
        self.mock_provider.fetch.assert_called_once_with("user@example.com", limit=15)
        self.mock_repo.save_report.assert_not_called()

    def test_save_report_called_with_correct_args(self):
        """save_report receives content, output directory, and email-based filename."""
        email = "test@domain.com"
        output = "output_dir"
        markdown = "# LeakCheck Report"

        self.mock_provider.fetch.return_value = markdown

        self.use_case.execute(email, output)

        self.mock_repo.save_report.assert_called_once_with(
            markdown,
            output=output,
            filename=f"report_{email}_leakcheck.md",
        )


if __name__ == "__main__":
    unittest.main()
