"""
Unit tests for ScanUseCaseSimple.

Run: python -m tests.test_scan_usecase_unit
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from internal.usecases.scan import ScanUseCaseSimple
from internal.domain.entities import ScanResult


class TestScanUseCaseSimple(unittest.TestCase):
    """Unit tests for ScanUseCaseSimple."""

    def setUp(self):
        self.mock_osint = Mock()
        self.mock_osint.__class__.__name__ = "HackerTargetOSINT"
        self.mock_repo = Mock()
        
        self.mock_osint.fetch.return_value = "# HackerTarget Report\nSubdomains found"
        self.mock_repo.save_report.return_value = "report/example.com_hackertarget.md"

    def _create_use_case(self, censys=None, ia=None):
        return ScanUseCaseSimple(
            osint_provider=self.mock_osint,
            report_service=self.mock_repo,
            censys_provider=censys,
            ia_provider=ia,
        )

    # --- Basic flow ---
    def test_basic_flow_calls_fetch_and_save(self):
        """Basic flow: fetch from provider, save report, return ScanResult."""
        use_case = self._create_use_case()
        
        result = use_case.execute("example.com", "output/")
        
        self.mock_osint.fetch.assert_called_once_with("example.com", limit=15)
        self.mock_repo.save_report.assert_called_once()
        self.assertIsInstance(result, ScanResult)
        self.assertEqual(result.filename, "report_example.com_hackertarget.md")
        self.assertEqual(result.output_path, "output/")

    def test_custom_limit_passed_to_fetch(self):
        """Custom limit parameter is passed to provider.fetch()."""
        use_case = self._create_use_case()
        
        use_case.execute("example.com", "output/", limit=30)
        
        self.mock_osint.fetch.assert_called_once_with("example.com", limit=30)

    def test_filename_uses_provider_class_name(self):
        """Filename includes provider class name (lowercase, without 'osint')."""
        self.mock_osint.__class__.__name__ = "CustomProviderOSINT"
        use_case = self._create_use_case()
        
        result = use_case.execute("test.com", "out/")
        
        self.assertEqual(result.filename, "report_test.com_customprovider.md")

    # --- Censys integration ---
    def test_censys_called_when_provider_and_ip_available(self):
        """Censys is called when provider exists and IP can be extracted."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.return_value = "# Censys Report\nPorts: 80, 443"
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        self.mock_osint.extract_main_ip.assert_called_once_with("example.com")
        mock_censys.fetch.assert_called_once_with("1.2.3.4", limit=20)
        # Both reports saved
        self.assertEqual(self.mock_repo.save_report.call_count, 2)
        # Combined data includes both
        self.assertIn("HackerTarget Report", result.markdown_data)
        self.assertIn("Censys Report", result.markdown_data)

    def test_censys_skipped_when_no_ip_extracted(self):
        """Censys is skipped when extract_main_ip returns None."""
        self.mock_osint.extract_main_ip = Mock(return_value=None)
        mock_censys = Mock()
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        mock_censys.fetch.assert_not_called()
        # Only main report saved
        self.assertEqual(self.mock_repo.save_report.call_count, 1)
        self.assertNotIn("---", result.markdown_data)

    def test_censys_skipped_when_provider_lacks_extract_method(self):
        """Censys is skipped when osint_provider has no extract_main_ip method."""
        # Use spec to restrict attributes — Mock without extract_main_ip
        mock_osint_no_extract = Mock(spec=["fetch", "__class__"])
        mock_osint_no_extract.__class__.__name__ = "HackerTargetOSINT"
        mock_osint_no_extract.fetch.return_value = "# Report"
        mock_censys = Mock()
        
        use_case = ScanUseCaseSimple(
            osint_provider=mock_osint_no_extract,
            report_service=self.mock_repo,
            censys_provider=mock_censys,
        )
        use_case.execute("example.com", "output/")
        
        mock_censys.fetch.assert_not_called()
        self.assertEqual(self.mock_repo.save_report.call_count, 1)

    def test_censys_no_info_message_skips_save(self):
        """Censys report not saved when response contains 'No se encontró información'."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.return_value = "No se encontró información para esta IP"
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        # Only main report saved, censys report skipped
        self.assertEqual(self.mock_repo.save_report.call_count, 1)
        self.assertNotIn("Censys", result.markdown_data)

    def test_censys_auth_error_skips_save(self):
        """Censys report not saved when response contains 'Error de autenticación'."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.return_value = "Error de autenticación: token inválido"
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        self.assertEqual(self.mock_repo.save_report.call_count, 1)

    def test_censys_exception_does_not_break_flow(self):
        """Censys exception is caught and does not break the main flow."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.side_effect = Exception("Network error")
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        # Main flow completes successfully
        self.assertIsInstance(result, ScanResult)
        self.assertEqual(self.mock_repo.save_report.call_count, 1)
        self.assertIn("HackerTarget Report", result.markdown_data)

    # --- IA analysis ---
    def test_ia_analysis_called_when_analyze_true(self):
        """IA analysis is called when analyze=True and ia_provider exists."""
        mock_ia = Mock()
        mock_ia.analyze.return_value = "# AI Analysis\nThreats detected"
        
        use_case = self._create_use_case(ia=mock_ia)
        result = use_case.execute("example.com", "output/", analyze=True)
        
        mock_ia.analyze.assert_called_once()
        # 2 saves: main report + analysis
        self.assertEqual(self.mock_repo.save_report.call_count, 2)
        # Check analysis filename
        calls = self.mock_repo.save_report.call_args_list
        analysis_call = calls[1]
        self.assertEqual(analysis_call[1]["filename"], "analysis_example.com.md")

    def test_ia_analysis_not_called_when_analyze_false(self):
        """IA analysis is NOT called when analyze=False."""
        mock_ia = Mock()
        
        use_case = self._create_use_case(ia=mock_ia)
        use_case.execute("example.com", "output/", analyze=False)
        
        mock_ia.analyze.assert_not_called()
        self.assertEqual(self.mock_repo.save_report.call_count, 1)

    def test_ia_analysis_not_called_when_no_provider(self):
        """IA analysis is NOT called when ia_provider is None."""
        use_case = self._create_use_case(ia=None)
        result = use_case.execute("example.com", "output/", analyze=True)
        
        # Only main report saved
        self.assertEqual(self.mock_repo.save_report.call_count, 1)

    # --- Combined: Censys + IA ---
    def test_combined_censys_and_ia(self):
        """Both Censys and IA analysis work together."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.return_value = "# Censys Data"
        mock_ia = Mock()
        mock_ia.analyze.return_value = "# AI Analysis"
        
        use_case = self._create_use_case(censys=mock_censys, ia=mock_ia)
        result = use_case.execute("example.com", "output/", analyze=True)
        
        # 3 saves: main + censys + analysis
        self.assertEqual(self.mock_repo.save_report.call_count, 3)
        # Combined data includes both main and censys
        self.assertIn("HackerTarget Report", result.markdown_data)
        self.assertIn("Censys Data", result.markdown_data)
        # IA was called with combined data
        mock_ia.analyze.assert_called_once()
        call_arg = mock_ia.analyze.call_args[0][0]
        self.assertIn("HackerTarget Report", call_arg)
        self.assertIn("Censys Data", call_arg)

    # --- Return value ---
    def test_returns_scan_result_with_combined_data(self):
        """Returns ScanResult with combined data when Censys is used."""
        self.mock_osint.extract_main_ip = Mock(return_value="1.2.3.4")
        mock_censys = Mock()
        mock_censys.fetch.return_value = "# Censys Info"
        
        use_case = self._create_use_case(censys=mock_censys)
        result = use_case.execute("example.com", "output/")
        
        self.assertIn("HackerTarget Report", result.markdown_data)
        self.assertIn("Censys Info", result.markdown_data)
        self.assertIn("---", result.markdown_data)  # Separator

    def test_returns_scan_result_without_censys(self):
        """Returns ScanResult with only main data when no Censys."""
        use_case = self._create_use_case()
        result = use_case.execute("example.com", "output/")
        
        self.assertEqual(result.markdown_data, "# HackerTarget Report\nSubdomains found")
        self.assertNotIn("---", result.markdown_data)


if __name__ == "__main__":
    unittest.main()
