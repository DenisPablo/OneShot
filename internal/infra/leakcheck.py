from internal.infra.base import BaseOSINTAdapter
from internal.infra.exceptions import AdapterError


class LeakCheckOSINT(BaseOSINTAdapter):
    """OSINT adapter for LeakCheck.io public API - email breach lookup."""

    def __init__(self):
        super().__init__("LeakCheck", "https://leakcheck.io/api/public")

    def fetch(self, target: str, limit: int = 15) -> str:
        """
        Fetch breach data for an email from LeakCheck.io.

        Args:
            target: Email address to check
            limit: Maximum number of sources to include (default: 15)

        Returns:
            Markdown formatted report with breach information
        """
        markdown_resultado = f"# Resultado de reconocimiento de email para: {target}\n\n"
        markdown_resultado += self._obtener_info_email(target, limit)
        return markdown_resultado

    def _obtener_info_email(self, email: str, limit: int = 15) -> str:
        """
        Query LeakCheck API and format response as Markdown.

        Args:
            email: Email address to check
            limit: Maximum number of sources to include

        Returns:
            Markdown formatted breach report
        """
        url = f"{self.base_url}?check={email}"

        try:
            data = self._safe_request_json(url, "LeakCheck Email", timeout=15)

            md = f"## LeakCheck: Análisis de brechas para {email}\n\n"

            if not data.get("success", False):
                md += "**Estado:** Error en la consulta\n\n"
                return md

            found_count = data.get("found", 0)
            sources = data.get("sources", [])
            fields = data.get("fields", [])

            md += f"**Estado:** {'Exitoso' if found_count > 0 else 'Sin brechas encontradas'}\n\n"
            md += f"**Brechas encontradas:** {found_count}\n\n"

            if found_count > 0:
                # Table of sources
                md += "### Fuentes de brechas\n\n"
                md += "| Servicio | Fecha |\n"
                md += "|----------|-------|\n"

                # Apply limit
                sources_to_show = sources[:limit] if limit else sources

                for source in sources_to_show:
                    name = source.get("name", "N/A")
                    date = source.get("date", "N/A")
                    md += f"| **{name}** | {date} |\n"

                if limit and len(sources) > limit:
                    md += f"\n*Mostrando {limit} de {len(sources)} fuentes*\n"

                # Fields exposed
                if fields:
                    md += f"\n**Campos expuestos:** {', '.join(fields)}\n"

            return md

        except AdapterError:
            raise
