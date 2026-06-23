import argparse
import sys
from internal.domain.ports import OSINTProvider, ReportRepository
from internal.infra.markdown import MarkdownReportRepository
from internal.infra.hackertarget import HackerTargetOSINT, ScanAbortedException


class ScanUseCaseSimple:
    """
    Caso de uso simplificado para orquestar el escaneo inicial de un dominio
    Recibe los adaptadores
    """

    def __init__(self, osint_provider: OSINTProvider, report_service: ReportRepository):
        """
        Inicializa el caso de uso
        """
        self.osint_provider = osint_provider
        self.report_service = report_service

    def execute(self, target: str, output: str, limit: int = 15) -> None:
        """
        Ejecuta el escaneo inicial
        """
        print(f"[+] Iniciando escaneo en: {target}")
        print(f"[*] Usando proveedor: {self.osint_provider.__class__.__name__}")

        markdown_data = self.osint_provider.fetch(target, limit=limit) 

        provider_suffix = self.osint_provider.__class__.__name__.lower().replace("osint", "")
        filename = f"report_{target}_{provider_suffix}.md" 

        self.report_service.save_report(markdown_data, output=output, filename=filename)

        print(f"[+] Escaneo completado")
        print(f"[*] Reporte guardado en: {output}/{filename}")
        print("[!] Recuerda que esto es solo la recoleccion de informacion, no el analisis")


def main():
    parser = argparse.ArgumentParser(
        description="OneShot - OSINT Tool"
    )

    parser.add_argument("-d", "--domain",
                        required=True,
                        help="Target a escanear"
                        )

    parser.add_argument("-o", "--output",
                        required=True,
                        help="Directorio de salida para el reporte"
                        )

    parser.add_argument("-l", "--limit",
                        type=int,
                        default=15,
                        help="Límite de resultados a mostrar en las secciones del reporte (por defecto: 15)"
                        )

    args = parser.parse_args()

    osint = HackerTargetOSINT()
    report_service = MarkdownReportRepository()

    use_case = ScanUseCaseSimple(osint, report_service)
    
    try:
        use_case.execute(args.domain, args.output, limit=args.limit)
    except ScanAbortedException as e:
        print(f"\n[!] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error inesperado al escanear el dominio: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()