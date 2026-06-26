class AdapterError(Exception):
    def __init__(self, adapter_name: str, detail: str):
        self.adapter_name = adapter_name
        super().__init__(f"[{adapter_name}] {detail}")
