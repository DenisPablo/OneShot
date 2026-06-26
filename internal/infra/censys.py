from internal.infra.base import BaseOSINTAdapter
from internal.infra.exceptions import AdapterError


class CensysOSINT(BaseOSINTAdapter):
    def __init__(self, api_token: str):
        super().__init__("Censys", "https://api.platform.censys.io/v3/global")
        self.api_token = api_token

    def verify_connection(self) -> bool:
        """Verifica que la conexión con Censys funciona correctamente."""
        try:
            url = f"{self.base_url}/asset/host/8.8.8.8"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            self._safe_request_json(url, "Connection Test", timeout=10, headers=headers)
            return True
        except Exception:
            return False

    def fetch(self, target: str, limit: int = 20) -> str:
        """Busca información de un host por IP usando Censys Platform API (plan gratuito)."""
        markdown_resultado = f"# Información de host en Censys para: {target}\n\n"
        markdown_resultado += self._obtener_host(target, limit)
        return markdown_resultado

    def _obtener_host(self, ip: str, limit: int) -> str:
        url = f"{self.base_url}/asset/host/{ip}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        try:
            data = self._safe_request_json(url, "Host Lookup", timeout=30, headers=headers)

            if not data or "result" not in data:
                return f"## Censys: No se encontró información para {ip}\n\n"

            resource = data["result"].get("resource", {})

            if not resource:
                return f"## Censys: No se encontró información para {ip}\n\n"

            md = f"## Censys: Información para {ip}\n\n"

            # Información básica
            md += f"**IP:** {resource.get('ip', ip)}\n"

            location = resource.get("location", {})
            if location:
                country = location.get("country", "N/A")
                city = location.get("city", "N/A")
                continent = location.get("continent", "N/A")
                md += f"**Ubicación:** {city}, {country} ({continent})\n"

            autonomous_system = resource.get("autonomous_system", {})
            if autonomous_system:
                asn = autonomous_system.get("asn", "N/A")
                name = autonomous_system.get("name", "N/A")
                description = autonomous_system.get("description", "")
                md += f"**AS:** AS{asn} - {name}"
                if description and description != name:
                    md += f" ({description})"
                md += "\n"

            service_count = resource.get("service_count", 0)
            md += f"**Servicios detectados:** {service_count}\n\n"

            # Servicios
            services = resource.get("services", [])
            if services:
                md += "### Puertos y Servicios Abiertos\n\n"
                md += "| Puerto | Protocolo | Transporte | Banner |\n"
                md += "|--------|-----------|------------|--------|\n"

                for service in services[:limit]:
                    port = service.get("port", "N/A")
                    protocol = service.get("protocol", service.get("service_name", "unknown"))
                    transport = service.get("transport_protocol", "tcp")
                    banner = service.get("banner", "")

                    # Truncar banner si es muy largo
                    if banner and len(banner) > 50:
                        banner = banner[:47] + "..."

                    md += f"| {port} | {protocol} | {transport} | {banner} |\n"

                if len(services) > limit:
                    md += f"\n*Mostrando {limit} de {len(services)} servicios*\n"

            # DNS reverse
            dns = resource.get("dns", {})
            reverse_dns = dns.get("reverse_dns", {})
            if reverse_dns and reverse_dns.get("names"):
                names = reverse_dns["names"]
                md += f"\n### DNS Reverse\n\n"
                for name in names[:10]:
                    md += f"- {name}\n"

            md += "\n"
            return md

        except AdapterError as e:
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                return f"## Censys: Error de autenticación\n\nEl token de Censys es inválido o ha expirado.\n\n**Solución:**\n1. Ve a https://accounts.censys.io/settings/personal-access-tokens\n2. Genera un nuevo Personal Access Token\n3. Actualiza CENSYS_API_TOKEN en tu archivo .env\n\nEl token debe empezar con 'censys_'\n\n"
            elif "404" in error_str:
                return f"## Censys: No se encontró información para {ip}\n\n"
            raise
