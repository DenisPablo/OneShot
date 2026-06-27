"""
Integration test for EmailInvestigationUseCase (task 3.4).

Mocks LeakCheckOSINT.fetch to return canned data, then verifies
that MarkdownReportRepository.save_report is called correctly.

Run: python -m tests.test_email_integration
"""
import sys
import os
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from internal.usecases.email import EmailInvestigationUseCase
from internal.infra.markdown import MarkdownReportRepository
from internal.domain.entities import ScanResult


class TestEmailIntegration(unittest.TestCase):
    """Integration test: mocked provider, real report repo."""

    def test_mocked_fetch_saves_report_via_real_repo(self):
        """
        Given a mocked LeakCheckOSINT.fetch returning canned data,
        when execute() is called,
        then MarkdownReportRepository saves a report to disk.
        """
        # Use a real MarkdownReportRepository with a temp directory
        import tempfile

        mock_provider = Mock()
        mock_provider.fetch.return_value = (
            "# Resultado de reconocimiento de email para: user@example.com\n\n"
            "## LeakCheck: Análisis de brechas para user@example.com\n\n"
            "**Estado:** Exitoso\n\n"
            "**Brechas encontradas:** 3\n\n"
            "### Fuentes de brechas\n\n"
            "| Servicio | Fecha |\n"
            "|----------|-------|\n"
            "| **Evony.com** | 2016-07 |\n"
            "| **I-Dressup.com** | 2016-08 |\n"
            "| **Zynga.com** | 2019-09 |\n"
        )

        report_repo = MarkdownReportRepository()

        with tempfile.TemporaryDirectory() as tmpdir:
            use_case = EmailInvestigationUseCase(
                email_provider=mock_provider,
                report_service=report_repo,
            )

            result = use_case.execute("user@example.com", tmpdir)

            # Verify ScanResult is returned correctly
            self.assertIsInstance(result, ScanResult)
            self.assertIn("_leakcheck.md", result.filename)
            self.assertEqual(result.output_path, tmpdir)
            self.assertTrue(os.path.exists(result.full_path),
                            f"Report file was not created at {result.full_path}")

            # Read back and verify content
            with open(result.full_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("LeakCheck", content)
            self.assertIn("Evony.com", content)
            self.assertIn("3", content)


if __name__ == "__main__":
    unittest.main()
