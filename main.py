import argparse
import os
import sys
from dotenv import load_dotenv
from internal.domain.ports import OSINTProvider, ReportRepository, IAProvider
from internal.infra.exceptions import AdapterError
from internal.infra.leakcheck import LeakCheckOSINT
from internal.container import create_default_container
from internal.usecases.scan import ScanUseCaseSimple
from internal.usecases.email import EmailInvestigationUseCase


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="OneShot - OSINT Tool"
    )

    parser.add_argument("-d", "--domain",
                        default=None,
                        help="Target a escanear"
                        )

    parser.add_argument("-e", "--email",
                        default=None,
                        help="Email a investigar via LeakCheck.io"
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

    parser.add_argument("--analyze",
                        action="store_true",
                        help="Analizar el reporte con IA (requiere OPENROUTER_API_KEY)"
                        )

    args = parser.parse_args()

    # Post-parse validation: at least one target required
    if not args.email and not args.domain:
        parser.error("Se requiere al menos --email/-e o --domain/-d")

    censys_api_token = os.getenv("CENSYS_API_TOKEN", "").strip() or None
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip() or None

    container = create_default_container(
        censys_api_token=censys_api_token,
        openrouter_api_key=openrouter_api_key
    )

    osint_provider = container.resolve(OSINTProvider)
    report_service = container.resolve(ReportRepository)

    censys_provider = None
    if censys_api_token:
        try:
            censys_provider = container.resolve("CensysOSINT")
            if not censys_provider.verify_connection():
                print(f"[!] Censys: token inválido o sin permisos")
                censys_provider = None
        except ValueError as e:
            print(f"[!] Error cargando Censys: {e}")
            censys_provider = None
    else:
        print("[*] Censys: deshabilitado (CENSYS_API_TOKEN no configurado)")

    ia_provider = None
    if args.analyze and openrouter_api_key:
        try:
            ia_provider = container.resolve(IAProvider)
            print("[+] Análisis IA: habilitado")
        except ValueError:
            print("[!] OpenRouter API key configurada pero no se pudo cargar el provider")

    # --- Email investigation (runs first if requested) ---
    if args.email:
        email_uc = EmailInvestigationUseCase(
            email_provider=container.resolve(LeakCheckOSINT),
            report_service=report_service,
        )
        try:
            print(f"[+] Investigando email: {args.email}")
            email_result = email_uc.execute(args.email, args.output)
            print(f"[+] Reporte email guardado en: {email_result.full_path}")
        except ValueError as e:
            print(f"\n[!] {e}")
            sys.exit(1)
        except AdapterError as e:
            print(f"\n[!] Error al investigar email: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[!] Error inesperado al investigar email: {e}")
            sys.exit(1)

    # --- Domain scan (runs second if requested) ---
    if args.domain:
        use_case = ScanUseCaseSimple(
            osint_provider=osint_provider,
            report_service=report_service,
            censys_provider=censys_provider,
            ia_provider=ia_provider,
        )
        try:
            print(f"[+] Iniciando escaneo en: {args.domain}")
            print(f"[*] Usando proveedor: {osint_provider.__class__.__name__}")

            result = use_case.execute(args.domain, args.output, limit=args.limit, analyze=args.analyze)

            print(f"[+] Escaneo completado")
            print(f"[*] Reporte guardado en: {result.full_path}")
            print("[!] Recuerda que esto es solo la recoleccion de informacion, no el analisis")
        except AdapterError as e:
            print(f"\n[!] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[!] Error inesperado al escanear el dominio: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
