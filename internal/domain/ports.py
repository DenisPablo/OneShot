from typing import Protocol, List

class OSINTProvider(Protocol):
    """
    Puerto(Inteface) para cualquier proveedor de informacion OSINT.
    """
    def fetch(self , target: str, limit: int = 15) -> str:
        """
        Obtiene la informacion del target y la devuelve formateada en markdown
        """
        ...

class IAProvider(Protocol):
    def AIService(Protocol):
        """
        Puerto (Interface) para cualquier servicio de IA.
        """
        def analyze(self, raw_markdown: str) -> str:
            """
            Analiza el markdown y devuelve un informe estructurado.
            """
            ...

class ReportRepository(Protocol):
    """
    Puerto(Interface) para cualquier proveedor de persistencia de informes.
    """
    def save_report(self, content: str, output: str = "./reports", filename: str = "report_crtsh.md") -> None:
            """
            Guarda el informe en un archivo.
            """
            ... 