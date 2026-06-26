from dataclasses import dataclass


@dataclass(frozen=True)
class ScanResult:
    markdown_data: str
    filename: str
    output_path: str

    @property
    def full_path(self) -> str:
        return f"{self.output_path}/{self.filename}"
