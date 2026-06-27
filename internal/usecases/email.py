from internal.infra.leakcheck import LeakCheckOSINT
from internal.infra.exceptions import AdapterError
from internal.domain.ports import ReportRepository
from internal.domain.entities import ScanResult


class EmailInvestigationUseCase:
    """Use case for email breach investigation via LeakCheck.io."""

    def __init__(
        self,
        email_provider: LeakCheckOSINT,
        report_service: ReportRepository,
    ):
        self.email_provider = email_provider
        self.report_service = report_service

    def execute(self, email: str, output: str, limit: int = 15) -> ScanResult:
        """
        Validate email format, fetch breach data, and save a markdown report.

        Args:
            email: The email address to investigate.
            output: Directory path for the report file.
            limit: Maximum number of breach sources to include (default: 15).

        Returns:
            ScanResult with full_path pointing to the written report.

        Raises:
            ValueError: If email does not contain '@'.
            AdapterError: On API or transport failure (propagated from LeakCheckOSINT).
        """
        if "@" not in email:
            raise ValueError(f"Dirección de email inválida: {email}")

        markdown_data = self.email_provider.fetch(email, limit=limit)

        filename = f"report_{email}_leakcheck.md"
        self.report_service.save_report(markdown_data, output=output, filename=filename)

        return ScanResult(
            markdown_data=markdown_data,
            filename=filename,
            output_path=output,
        )
