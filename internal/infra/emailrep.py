from internal.infra.base import BaseOSINTAdapter
from internal.infra.exceptions import AdapterError


class EmailRepOSINT(BaseOSINTAdapter):
    def __init__(self, api_key: str = None):
        super().__init__("EmailRep", "https://emailrep.io")
        self.api_key = api_key

    def fetch(self, target: str, limit: int = 15) -> str:
        markdown_resultado = f"# Resultado de reconocimiento de email para: {target}\n\n"
        markdown_resultado += self._obtener_info_email(target)
        return markdown_resultado

    def _obtener_info_email(self, email: str) -> str:
        url = f"{self.base_url}/{email}"
        headers = {}

        if self.api_key:
            headers["Key"] = self.api_key

        try:
            data = self._safe_request_json(url, "Info Email", timeout=15, headers=headers)

            md = f"## EmailRep: Análisis de {email}\n\n"
            md += f"| Parámetro | Detalle |\n"
            md += f"|---|---|\n"
            md += f"| **Reputación** | {data.get('reputation', 'N/A')} |\n"
            md += f"| **Puntuación** | {data.get('suspicious', 'N/A')} |\n"
            md += f"| **Dominio** | {data.get('details', {}).get('domain', 'N/A')} |\n"
            md += f"| **Proveedor** | {data.get('details', {}).get('provider', 'N/A')} |\n"
            md += f"| **País** | {data.get('details', {}).get('country', 'N/A')} |\n"
            md += f"| **Descripción** | {data.get('summary', 'N/A')} |\n"

            return md
        except AdapterError:
            raise
