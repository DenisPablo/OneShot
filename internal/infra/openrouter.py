import requests
from internal.infra.exceptions import AdapterError


class OpenRouterIAProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openrouter/free"

    def analyze(self, raw_markdown: str) -> str:
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/oneshot",
            "X-Title": "OneShot OSINT Tool"
        }
        
        prompt = f"""Analiza el siguiente reporte de reconocimiento OSINT y genera un informe ejecutivo
con las siguientes secciones:
1. Resumen del objetivo
2. Subdominios críticos encontrados
3. Información DNS relevante
4. Ubicación geográfica
5. Información de registro
6. Recomendaciones de seguridad

Reporte a analizar:
{raw_markdown}
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise AdapterError("OpenRouter", f"Error en análisis IA: {e}")
        except (KeyError, IndexError) as e:
            raise AdapterError("OpenRouter", f"Error procesando respuesta: {e}")
