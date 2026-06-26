from internal.infra.base import BaseOSINTAdapter
from internal.infra.exceptions import AdapterError


class HackerTargetOSINT(BaseOSINTAdapter):
    def __init__(self):
        super().__init__("HackerTarget", "https://api.hackertarget.com")
        self._last_subdomains_data: list[tuple[str, str]] = []

    def fetch(self, target: str, limit: int = 15) -> str:
        markdown_resultado = f'# Resultado de reconocimiento pasivo para: {target}\n\n'
        markdown_resultado += self._obtener_subdominios(target, limit=limit)
        markdown_resultado += self._obtener_dns(target)
        markdown_resultado += self._obtener_geoip(target)
        markdown_resultado += self._obtener_reverse_ip(target, limit=limit)
        markdown_resultado += self._obtener_whois(target)
        return markdown_resultado

    def extract_main_ip(self, target: str) -> str | None:
        """Extrae la IP principal del dominio de los resultados de subdominios."""
        if self._last_subdomains_data:
            for subdomain, ip in self._last_subdomains_data:
                if subdomain == target:
                    return ip
            return self._last_subdomains_data[0][1]
        return None

    def _obtener_subdominios(self, target: str, limit: int) -> str:
        url = f'{self.base_url}/hostsearch/?q={target}'
        try:
            text = self._safe_request(url, "Subdominios e IPs")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Subdominios para {target}\nNo se encontraron subdominios.\n\n"
                raise AdapterError(self.adapter_name, text)

            md = f"## Subdominios encontrados para {target}\n\n| Subdominio | Dirección IP |\n| --- | --- |\n"
            lines = text.split("\n")
            self._last_subdomains_data = []

            for line in lines[:limit]:
                if "," in line:
                    sub, ip = line.split(",", 1)
                    sub = sub.strip()
                    ip = ip.strip()
                    md += f"| {sub} | {ip} |\n"
                    self._last_subdomains_data.append((sub, ip))

            if len(lines) > limit:
                md += f"\n**Se muestran solo los primeros {limit} resultados**\n\n"
            else:
                md += "\n"

            return md
        except AdapterError:
            raise

    def _obtener_dns(self, target: str) -> str:
        url = f"{self.base_url}/dnslookup/?q={target}"
        try:
            text = self._safe_request(url, "Registros DNS")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros DNS para {target}\nNo se encontraron registros DNS.\n\n"
                raise AdapterError(self.adapter_name, text)

            md = f"## Registros DNS para {target}\n\n"
            md += "```text\n" + text + "\n```\n\n"
            return md
        except AdapterError:
            raise

    def _obtener_geoip(self, target: str) -> str:
        url = f"{self.base_url}/geoip/?q={target}"
        try:
            text = self._safe_request(url, "Registros GeoIP")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros GeoIP para {target}\nNo se encontraron registros GeoIP.\n\n"
                raise AdapterError(self.adapter_name, text)

            md = f"## Registros GeoIP para {target}\n\n"
            for line in text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    md += f"**{key.strip()}:** {value.strip()}\n"
            md += "\n"
            return md
        except AdapterError:
            raise

    def _obtener_reverse_ip(self, target: str, limit: int) -> str:
        url = f"{self.base_url}/reverseiplookup/?q={target}"
        try:
            text = self._safe_request(url, "Registros Reverse IP")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros Reverse IP para {target}\nNo se encontraron registros Reverse IP.\n\n"
                raise AdapterError(self.adapter_name, text)

            md = f"## Registros Reverse IP para {target}\n\n"
            lines = text.split('\n')

            for line in lines[:limit]:
                md += f"- {line.strip()}\n"

            if len(lines) > limit:
                md += f"\n**Se muestran solo los primeros {limit} resultados**\n\n"
            else:
                md += "\n"

            return md
        except AdapterError:
            raise

    def _obtener_whois(self, target: str) -> str:
        url = f"https://rdap.org/domain/{target}"
        try:
            data = self._safe_request_json(url, "Registro de Dominio", timeout=30)

            entities = data.get("entities", [])
            registrar = "Desconocido"
            for entity in entities:
                if "registrar" in entity.get("roles", []):
                    vcard = entity.get("vcardArray", [None, []])[1]
                    for prop in vcard:
                        if prop[0] == "fn":
                            registrar = prop[3]
                            break

            events = data.get("events", [])
            fecha_creacion = "N/A"
            fecha_expiracion = "N/A"

            for event in events:
                action = event.get("eventAction")
                date_str = event.get("eventDate", "").split("T")[0]
                if action == "registration":
                    fecha_creacion = date_str
                elif action == "expiration":
                    fecha_expiracion = date_str

            md = f"## 📝 Información de Registro de Dominio (RDAP/WHOIS)\n\n"
            md += f"| Parámetro | Detalle |\n"
            md += f"|---|---|\n"
            md += f"| **Proveedor (Registrar)** | {registrar} |\n"
            md += f"| **Fecha de Creación** | {fecha_creacion} |\n"
            md += f"| **Fecha de Expiración** | {fecha_expiracion} |\n"

            return md
        except AdapterError:
            raise
