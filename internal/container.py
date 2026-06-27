"""
Container de Inyección de Dependencias.
Centraliza la creación y gestión de adaptadores.
"""
from internal.domain.ports import OSINTProvider, ReportRepository, IAProvider
from internal.infra.hackertarget import HackerTargetOSINT
from internal.infra.markdown import MarkdownReportRepository
from internal.infra.censys import CensysOSINT
from internal.infra.leakcheck import LeakCheckOSINT
from internal.infra.openrouter import OpenRouterIAProvider


class Container:
    """
    Contenedor simple de dependencias.
    Registra y resuelve dependencias por tipo.
    """

    def __init__(self):
        self._factories = {}
        self._instances = {}

    def register(self, interface, implementation):
        """Registra una implementación para una interfaz."""
        self._factories[interface] = implementation

    def register_instance(self, key, instance):
        """Registra una instancia ya creada."""
        self._instances[key] = instance

    def resolve(self, key):
        """Resuelve y retorna la implementación registrada."""
        if key in self._instances:
            return self._instances[key]

        if key in self._factories:
            instance = self._factories[key]()
            self._instances[key] = instance
            return instance

        key_name = key.__name__ if hasattr(key, '__name__') else str(key)
        raise ValueError(f"No hay implementación registrada para {key_name}")

    def reset(self):
        """Limpia todas las registrations e instancias."""
        self._factories.clear()
        self._instances.clear()


def create_default_container(
    censys_api_token: str = None,
    openrouter_api_key: str = None
) -> Container:
    """
    Crea un container con las implementaciones por defecto.
    Las API keys son opcionales. Si no se proporcionan, los adaptadores
    usarán tier gratuito (donde aplique).
    """
    container = Container()

    # OSINT Provider - HackerTarget por defecto (no requiere API key)
    container.register_instance(OSINTProvider, HackerTargetOSINT())

    # Report Repository - Markdown por defecto
    container.register_instance(ReportRepository, MarkdownReportRepository())

    # Censys - requiere API Token (tiene plan gratuito)
    if censys_api_token:
        container.register_instance("CensysOSINT", CensysOSINT(censys_api_token))

    # LeakCheck - API pública, no requiere API key
    container.register_instance(LeakCheckOSINT, LeakCheckOSINT())

    # OpenRouter IA - requiere API key
    if openrouter_api_key:
        container.register_instance(IAProvider, OpenRouterIAProvider(openrouter_api_key))

    return container
