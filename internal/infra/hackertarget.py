from decimal import ROUND_HALF_UP
import sys
import requests
from internal.infra import markdown
from datetime import timezone

class ScanAbortedException(Exception):
    """Excepción para cuando el usuario decide abortar el escaneo."""
    pass

class HackerTargetOSINT:
    """
    Adaptador de infraestructura para la API de HackerTarget.
    Cumple implícitamente con el protocolo OSINTProvider del dominio.
    """

    def __init__(self):
        """
        Inicializa el adaptador
        """
        self.base_url = "https://api.hackertarget.com"

    def _handle_error(self, step_name: str, exception: Exception) -> str:
        """
        Muestra el error en la consola y pregunta al usuario si desea continuar.
        Si decide no continuar, lanza una excepción para interrumpir el proceso.
        Si decide continuar, devuelve una cadena vacía para que no se guarde en el reporte.
        """
        print(f"\n[!] Error al obtener {step_name}: {exception}", file=sys.stderr)
        while True:
            try:
                respuesta = input(f"¿Desea continuar con el proceso a pesar del error en {step_name}? (s/n): ").strip().lower()
                if respuesta in ('s', 'si', 'y', 'yes', ''):
                    return ""  # Continuar, devolviendo vacío para el reporte
                elif respuesta in ('n', 'no'):
                    raise ScanAbortedException(f"Escaneo abortado por el usuario tras error en {step_name}")
                else:
                    print("Por favor, responda 's' (sí) o 'n' (no).")
            except (EOFError, KeyboardInterrupt):
                raise ScanAbortedException(f"Escaneo interrumpido por señal del usuario.")

    def fetch(self, target: str, limit: int = 15) -> str:
        """
        Obtiene los subdominios y registros usando la API de HackerTarget y los devuelve en formato MD.
        """
        markdown_resultado = f'# Resultado de reconocimiento pasivo para: {target}\n\n'

        #Subdominios e IPs
        print("\n### 🔍 Obteniendo subdominios e IPs...")
        markdown_resultado += self._obtener_subdominios(target, limit=limit)

        #Registros DNS
        print("\n### 🔍 Obteniendo registros DNS...")
        markdown_resultado += self._obtener_dns(target)

        #Registros GeoIP
        print("\n### 🔍 Obteniendo registros GeoIP...")
        markdown_resultado += self._obtener_geoip(target)

        #Registros Reverse IP
        print("\n### 🔍 Obteniendo registros Reverse IP...")
        markdown_resultado += self._obtener_reverse_ip(target, limit=limit)

        #Whois
        print("\n### 🔍 Obteniendo Whois...")
        markdown_resultado += self._obtener_whois(target)

        return markdown_resultado

    def _obtener_subdominios(self, target: str, limit: int) -> str:
        url = f'{self.base_url}/hostsearch/?q={target}'
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            text = res.text.strip()
            
            if "api count exceeded" in text.lower():
                raise Exception("API count exceeded - Increase Quota with Membership")
            
            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Subdominios para {target}\nNo se encontraron subdominios.\n\n"
                else:
                    raise Exception(text)

            md = f"## Subdominios encontrados para {target}\n\n| Subdominio | Dirección IP |\n| --- | --- |\n"
            lines = text.split("\n")

            for line in lines[:limit]:
                if "," in line:
                    sub, ip = line.split(",", 1)
                    md += f"| {sub.strip()} | {ip.strip()} |\n"
            
            if len(lines) > limit:
                md += f"\n**Se muestran solo los primeros {limit} resultados**\n\n"
            else:
                md += "\n"

            return md
        except Exception as e:
            return self._handle_error("Subdominios e IPs", e)

    def _obtener_dns(self, target: str) -> str:
        url = f"{self.base_url}/dnslookup/?q={target}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            text = res.text.strip()
            
            if "api count exceeded" in text.lower():
                raise Exception("API count exceeded - Increase Quota with Membership")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros DNS para {target}\nNo se encontraron registros DNS.\n\n"
                else:
                    raise Exception(text)

            md = f"## Registros DNS para {target}\n\n"
            md += "```text\n" + text + "\n```\n\n"
            return md
        except Exception as e:
            return self._handle_error("Registros DNS", e)

    def _obtener_geoip(self, target: str) -> str:
        url = f"{self.base_url}/geoip/?q={target}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            text = res.text.strip()

            if "api count exceeded" in text.lower():
                raise Exception("API count exceeded - Increase Quota with Membership")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros GeoIP para {target}\nNo se encontraron registros GeoIP.\n\n"
                else:
                    raise Exception(text)

            md = f"## Registros GeoIP para {target}\n\n"
            for line in text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    md += f"**{key.strip()}:** {value.strip()}\n"
            md += "\n"
            return md
        except Exception as e:
            return self._handle_error("Registros GeoIP", e)

    def _obtener_reverse_ip(self, target: str, limit: int) -> str:
        url = f"{self.base_url}/reverseiplookup/?q={target}"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            text = res.text.strip()
            
            if "api count exceeded" in text.lower():
                raise Exception("API count exceeded - Increase Quota with Membership")

            if not text or "error" in text.lower():
                if "no records" in text.lower():
                    return f"## Registros Reverse IP para {target}\nNo se encontraron registros Reverse IP.\n\n"
                else:
                    raise Exception(text)

            md = f"## Registros Reverse IP para {target}\n\n"
            lines = text.split('\n')

            for line in lines[:limit]:
                md += f"- {line.strip()}\n"
            
            if len(lines) > limit:
                md += f"\n**Se muestran solo los primeros {limit} resultados**\n\n"
            else:
                md += "\n"
            
            return md
        except Exception as e:
            return self._handle_error("Registros Reverse IP", e)

    def _obtener_whois(self, target: str) -> str:
        # Endpoint público y gratuito de la ICANN para RDAP
        url = f"https://rdap.org/domain/{target}"
        try:
            res = requests.get(url, timeout=30)
            
            if res.status_code == 404:
                return f"## 📝 Registro de Dominio (RDAP)\n\nEl dominio `{target}` no parece estar registrado o no se encontraron datos públicos.\n"
                
            res.raise_for_status()
            data = res.json()

            # Extraemos el Registrador (ej: GoDaddy, Namecheap)
            entities = data.get("entities", [])
            registrar = "Desconocido"
            for entity in entities:
                if "registrar" in entity.get("roles", []):
                    # Buscamos el nombre público en las vcards
                    vcard = entity.get("vcardArray", [None, []])[1]
                    for prop in vcard:
                        if prop[0] == "fn":
                            registrar = prop[3]
                            break

            # Extraemos las fechas críticas (Creación y Expiración)
            events = data.get("events", [])
            fecha_creacion = "N/A"
            fecha_expiracion = "N/A"
            
            for event in events:
                action = event.get("eventAction")
                date_str = event.get("eventDate", "").split("T")[0] # Limpiamos la hora
                if action == "registration":
                    fecha_creacion = date_str
                elif action == "expiration":
                    fecha_expiracion = date_str

            # Construimos la tablita limpia en Markdown para la IA
            md = f"## 📝 Información de Registro de Dominio (RDAP/WHOIS)\n\n"
            md += f"| Parámetro | Detalle |\n"
            md += f"|---|---|\n"
            md += f"| **Proveedor (Registrar)** | {registrar} |\n"
            md += f"| **Fecha de Creación** | {fecha_creacion} |\n"
            md += f"| **Fecha de Expiración** | {fecha_expiracion} |\n"
            
            return md

        except Exception as e:
            # Si el servidor de RDAP falla o cambia el JSON, devolvemos el error prolijo
            return self._handle_error("Registro de Dominio", e)