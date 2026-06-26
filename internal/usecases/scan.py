from internal.domain.ports import OSINTProvider, ReportRepository, IAProvider
from internal.domain.entities import ScanResult


class ScanUseCaseSimple:
    def __init__(
        self,
        osint_provider: OSINTProvider,
        report_service: ReportRepository,
        censys_provider: OSINTProvider = None,
        ia_provider: IAProvider = None
    ):
        self.osint_provider = osint_provider
        self.report_service = report_service
        self.censys_provider = censys_provider
        self.ia_provider = ia_provider

    def execute(self, target: str, output: str, limit: int = 15, analyze: bool = False) -> ScanResult:
        print(f"[*] Ejecutando reconocimiento con {self.osint_provider.__class__.__name__}...")
        hackertarget_data = self.osint_provider.fetch(target, limit=limit)

        ht_suffix = self.osint_provider.__class__.__name__.lower().replace("osint", "")
        ht_filename = f"report_{target}_{ht_suffix}.md"

        print(f"[*] Guardando reporte de {self.osint_provider.__class__.__name__}...")
        self.report_service.save_report(hackertarget_data, output=output, filename=ht_filename)
        print(f"[+] Reporte guardado: {ht_filename}")

        combined_data = hackertarget_data

        if self.censys_provider and hasattr(self.osint_provider, 'extract_main_ip'):
            ip = self.osint_provider.extract_main_ip(target)
            if ip:
                print(f"[*] Consultando IP {ip} en Censys...")
                try:
                    censys_data = self.censys_provider.fetch(ip, limit=20)

                    if censys_data and "No se encontró información" not in censys_data and "Error de autenticación" not in censys_data:
                        censys_filename = f"report_{target}_censys.md"
                        self.report_service.save_report(censys_data, output=output, filename=censys_filename)
                        print(f"[+] Reporte Censys guardado: {censys_filename}")
                        combined_data = hackertarget_data + "\n---\n\n" + censys_data
                    else:
                        print(f"[*] Censys: No se encontró información para la IP {ip}")
                except Exception as e:
                    print(f"[!] Error en Censys: {e}")
            else:
                print("[*] Censys: No se pudo extraer la IP del dominio")
        elif self.censys_provider:
            print("[*] Censys: omitido (no se puede extraer IP del proveedor principal)")
        else:
            print("[*] Censys: omitido (provider no disponible)")

        if analyze and self.ia_provider:
            print("[*] Analizando reportes con IA...")
            analysis = self.ia_provider.analyze(combined_data)
            analysis_filename = f"analysis_{target}.md"
            self.report_service.save_report(analysis, output=output, filename=analysis_filename)
            print(f"[+] Análisis guardado en: {analysis_filename}")

        return ScanResult(
            markdown_data=combined_data,
            filename=ht_filename,
            output_path=output,
        )
