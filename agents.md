# OneShot - Agent Instructions

## Quick Start

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Ejecutar escaneo
python main.py -d example.com -o ./reports -l 15
```

## Architecture

Clean Architecture con 4 capas. **Regla de oro**: las dependencias apuntan hacia adentro.

```
main.py (CLI)
    ↓
internal/usecases/ (Application)
    ↓
internal/domain/ (Domain - solo stdlib)
    ↑
internal/infra/ (Infrastructure - adaptadores)
```

### Capas

- **domain/**: Protocolos (`OSINTProvider`, `ReportRepository`, `IAProvider`), entidades (`ScanResult`), excepciones. **Solo importa stdlib**.
- **usecases/**: `ScanUseCaseSimple` - orquesta fetch + save. Recibe dependencias por constructor.
- **infra/**: Adaptadores concretos (`HackerTargetOSINT`, `CensysOSINT`, `EmailRepOSINT`, `GeminiIAProvider`, `MarkdownReportRepository`). Heredan de `BaseOSINTAdapter`.
- **container.py**: DI container simple. Registra interfaces → implementaciones.

### Agregar nuevo proveedor OSINT

1. Crear clase en `internal/infra/` que herede `BaseOSINTAdapter`
2. Implementar `fetch(target, limit) -> str` retornando Markdown
3. Registrar en `container.py`: `container.register(OSINTProvider, TuClase)`

## Conventions

- Código en **inglés**, outputs/logs en **español**
- Type hints obligatorios en funciones públicas
- Docstrings Google style
- Nombres: `snake_case` (funciones/variables), `PascalCase` (clases)
- Máximo 200-300 líneas por archivo

## Security Rules

- API keys via `.env` (gitignored), nunca hardcodeadas
- Timeouts obligatorios en todas las peticiones HTTP
- Herramienta de reconocimiento **pasivo** - no interactúa con target
- `AdapterError` para errores de adaptadores, `ScanAbortedException` para abortos de usuario

## What's Missing

- **No hay tests** - si agregas funcionalidad, crea `tests/` con pytest
- **No hay linter/formatter** - usa black/ruff manualmente si quieres
- **No hay package manager** - dependencias en `venv/`, sin requirements.txt ni pyproject.toml
- **Python 3.14+** requerido

## Common Pitfalls

- `main.py` usa `argparse` (stdlib), no Click/Typer
- El container DI es DIY, no uses frameworks externos
- `BaseOSINTAdapter._safe_request()` ya maneja timeouts y errores - no reinventes
- Los reportes se generan como Markdown, no JSON/HTML
- `.env` está vacío por defecto - copia `.env.example` a `.env` y completa las keys

## API Keys y Servicios Externos

### Censys
- **Plan gratuito "Free"** - créditos limitados por mes
- Busca hosts y servicios expuestos en Internet
- Requiere **Personal Access Token** (un solo token, autenticación Bearer)
- El plan gratuito **solo permite lookup por IP** (`/v3/global/asset/host/{ip}`), no búsqueda por dominio
- El plan gratuito no tiene acceso al endpoint de búsqueda (`/v3/global/search/query`)
- La IP se extrae automáticamente de los resultados de HackerTarget
- Obtén tu token en: https://accounts.censys.io/settings/personal-access-tokens

### EmailRep
- Funciona con API key gratuita (tier gratuito)
- Sin API key también funciona pero con límites más estrictos

### OpenRouter
- Requiere API key de OpenRouter
- Usa el router gratuito que selecciona automáticamente el mejor modelo
- Endpoint: `/api/v1/chat/completions`
- Obtén tu API key en: https://openrouter.ai/keys
