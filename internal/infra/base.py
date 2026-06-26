import requests
from internal.infra.exceptions import AdapterError


class BaseOSINTAdapter:
    def __init__(self, adapter_name: str, base_url: str):
        self.adapter_name = adapter_name
        self.base_url = base_url

    def _safe_request(self, url: str, step_name: str, timeout: int = 10, method: str = "GET", **kwargs) -> str:
        try:
            if method == "GET":
                res = requests.get(url, timeout=timeout, **kwargs)
            elif method == "POST":
                res = requests.post(url, timeout=timeout, **kwargs)
            else:
                raise AdapterError(self.adapter_name, f"Metodo HTTP no soportado: {method}")

            res.raise_for_status()
            text = res.text.strip()

            if "api count exceeded" in text.lower():
                raise AdapterError(self.adapter_name, "API quota exceeded")

            return text
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(self.adapter_name, f"Error en {step_name}: {e}")

    def _safe_request_json(self, url: str, step_name: str, timeout: int = 10, method: str = "GET", **kwargs) -> dict:
        try:
            if method == "GET":
                res = requests.get(url, timeout=timeout, **kwargs)
            elif method == "POST":
                res = requests.post(url, timeout=timeout, **kwargs)
            else:
                raise AdapterError(self.adapter_name, f"Metodo HTTP no soportado: {method}")

            res.raise_for_status()
            return res.json()
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(self.adapter_name, f"Error en {step_name}: {e}")
