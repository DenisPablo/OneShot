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

class OSINTProviderWithIP(Protocol):
    """
    Puerto para proveedor OSINT que puede extraer IPs de sus resultados.
    """
    def fetch(self, target: str, limit: int = 15) -> str:
        ...

    def extract_main_ip(self, target: str) -> str | None:
        """Extrae la IP principal del dominio de los resultados."""
        ...

class IAProvider(Protocol):
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
    def save_report(self, content: str, output: str = "./reports", filename: str = "report_crtsh.md") -> str:
            """
            Guarda el informe en un archivo y retorna la ruta completa.
            """
            ... 