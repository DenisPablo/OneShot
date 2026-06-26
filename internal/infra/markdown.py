import os


class MarkdownReportRepository:
    def save_report(self, content: str, output: str = "./reports", filename: str = "report_crtsh.md") -> str:
        os.makedirs(output, exist_ok=True)
        filepath = os.path.join(output, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath
