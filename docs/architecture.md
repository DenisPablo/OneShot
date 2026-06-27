# OneShot - Arquitectura del Proyecto

## Descripcion General

OneShot es una herramienta OSINT (Open Source Intelligence) escrita en Python, disenada para realizar reconocimiento pasivo de dominios. Recopila informacion publica de multiples fuentes (HackerTarget, Censys, LeakCheck, RDAP/WHOIS) y genera reportes estructurados en formato Markdown.

El proyecto sigue los principios de **Clean Architecture** con separacion clara de responsabilidades, inversion de dependencias e inyeccion de dependencias mediante un container DIY.

---

## Estructura de Directorios

```
OneShot/
├── main.py                         # Punto de entrada CLI (Presentacion)
├── analyze.py                      # Script de auto-analisis de arquitectura
├── .env                            # Variables de entorno (API keys)
├── .gitignore
├── docs/                           # Documentacion del proyecto
├── tests/                          # Suite de tests
│   ├── __init__.py
│   ├── test_email_usecase_unit.py  # Tests unitarios del use case de email
│   ├── test_email_integration.py   # Tests de integracion
│   └── test_cli_e2e.py             # Tests end-to-end del CLI
├── internal/                       # Codigo fuente principal
│   ├── __init__.py
│   ├── container.py                # Container de Inyeccion de Dependencias
│   ├── domain/                     # Capa de Dominio
│   │   ├── __init__.py
│   │   ├── ports.py                # Protocolos/Interfaces
│   │   ├── entities.py             # Entidades de dominio
│   │   └── exceptions.py           # Excepciones de dominio
│   ├── usecases/                   # Capa de Aplicacion (Casos de Uso)
│   │   ├── __init__.py
│   │   ├── scan.py                 # Caso de uso de escaneo de dominios
│   │   └── email.py                # Caso de uso de investigacion de emails
│   └── infra/                      # Capa de Infraestructura (Adaptadores)
│       ├── __init__.py
│       ├── base.py                 # Adaptador base con metodos HTTP seguros
│       ├── exceptions.py           # Excepciones de infraestructura
│       ├── hackertarget.py         # Adaptador HackerTarget API
│       ├── censys.py               # Adaptador Censys API
│       ├── leakcheck.py            # Adaptador LeakCheck API (brechas de email)
│       ├── openrouter.py           # Adaptador OpenRouter AI (analisis)
│       └── markdown.py             # Repositorio de reportes Markdown
└── venv/                           # Entorno virtual Python
```

---

## Capas de la Arquitectura

### 1. Capa de Dominio (`internal/domain/`)

La capa mas interna. Define las reglas de negocio y abstracciones sin depender de ninguna implementacion externa. Solo importa la biblioteca estandar de Python.

#### Puertos / Interfaces (`ports.py`)

Define los contratos que deben cumplir las implementaciones externas usando `typing.Protocol`:

| Protocolo | Metodo | Descripcion |
|---|---|---|
| `OSINTProvider` | `fetch(target, limit)` | Obtiene informacion OSINT de un target y la devuelve en Markdown |
| `IAProvider` | `analyze(raw_markdown)` | Analiza un reporte Markdown y genera un informe estructurado |
| `ReportRepository` | `save_report(content, output, filename)` | Persiste el informe en un archivo y retorna la ruta |

#### Entidades (`entities.py`)

| Entidad | Campos | Descripcion |
|---|---|---|
| `ScanResult` | `markdown_data`, `filename`, `output_path` | Dataclass inmutable (`frozen=True`) que encapsula el resultado de un escaneo. Incluye la propiedad `full_path` |

#### Excepciones de Dominio (`exceptions.py`)

| Excepcion | Descripcion |
|---|---|
| `ScanAbortedException` | Se lanza cuando el usuario decide abortar el escaneo |

---

### 2. Capa de Aplicacion / Casos de Uso (`internal/usecases/`)

Orquesta el flujo principal de la aplicacion. Depende **unicamente** de las abstracciones del dominio (puertos), nunca de implementaciones concretas.

#### `ScanUseCaseSimple`

```
Entrada: target (str), output (str), limit (int)
Salida:  ScanResult
```

**Flujo interno:**
1. Invoca `osint_provider.fetch()` para recolectar datos del target
2. Genera un nombre de archivo basado en el target y el proveedor
3. Invoca `report_service.save_report()` para persistir el reporte
4. Retorna un `ScanResult` con los datos del escaneo

> **Principio clave:** Recibe sus dependencias por constructor (Inyeccion de Dependencias), lo que permite sustituir cualquier proveedor o repositorio sin modificar el caso de uso.

#### `EmailInvestigationUseCase`

```
Entrada: email (str), output (str)
Salida:  ScanResult
```

**Flujo interno:**
1. Valida el formato del email (presencia de `@`)
2. Invoca `email_provider.fetch()` para obtener reputacion del email
3. Genera un nombre de archivo basado en el email
4. Invoca `report_service.save_report()` para persistir el reporte
5. Retorna un `ScanResult` con los datos de la investigacion

**Dependencias:**
- `LeakCheckOSINT` — Adaptador concreto para la API de LeakCheck
- `ReportRepository` — Puerto del dominio para persistencia

**Manejo de errores:**
- `ValueError` — Email con formato invalido
- `AdapterError` — Error de la API de LeakCheck (se propaga al caller)

---

### 3. Capa de Infraestructura (`internal/infra/`)

Contiene las implementaciones concretas de los puertos del dominio. Son los **adaptadores** que conectan la logica de negocio con servicios externos.

#### Adaptador Base (`base.py`)

`BaseOSINTAdapter` provee funcionalidad comun para todos los adaptadores OSINT:

| Metodo | Descripcion |
|---|---|
| `_safe_request(url, step_name, timeout, method)` | Realiza peticiones HTTP seguras con manejo de errores y timeout. Retorna texto plano |
| `_safe_request_json(url, step_name, timeout, method)` | Igual que el anterior pero parsea la respuesta como JSON |

Caracteristicas de seguridad:
- Timeouts configurables en todas las operaciones de red
- Deteccion de cuota API excedida
- Manejo especifico de errores por adaptador
- Soporte para metodos GET y POST

#### Adaptadores OSINT Implementados

| Adaptador | API | Puerto que implementa | Requiere API Key |
|---|---|---|---|
| `HackerTargetOSINT` | HackerTarget + RDAP | `OSINTProvider` | No |
| `CensysOSINT` | Censys | `OSINTProvider` | Si |
| `LeakCheckOSINT` | LeakCheck | N/A (uso directo) | No |
| `OpenRouterIAProvider` | OpenRouter | `IAProvider` | Si |

**HackerTargetOSINT** (proveedor por defecto) recolecta:
- Subdominios e IPs asociadas (`hostsearch`)
- Registros DNS (`dnslookup`)
- Informacion GeoIP (`geoip`)
- Reverse IP lookup (`reverseiplookup`)
- Informacion de registro WHOIS/RDAP (`rdap.org`)

**LeakCheckOSINT** (investigacion de emails) analiza:
- Brechas donde el email fue encontrado
- Fecha de cada brecha
- Campos expuestos (username, password, etc.)
- Numero total de brechas encontradas

#### Repositorios

| Adaptador | Puerto que implementa | Descripcion |
|---|---|---|
| `MarkdownReportRepository` | `ReportRepository` | Persiste reportes como archivos `.md` en disco |

#### Excepciones de Infraestructura (`exceptions.py`)

| Excepcion | Descripcion |
|---|---|
| `AdapterError` | Error generico de adaptador. Incluye nombre del adaptador y detalle del error |

---

### 4. Capa de Presentacion / CLI (`main.py`)

Interfaz de linea de comandos construida con `argparse` (biblioteca estandar).

#### Argumentos CLI

| Flag | Argumento | Requerido | Default | Descripcion |
|---|---|---|---|---|
| `-d` | `--domain` | No* | - | Target (dominio) a escanear |
| `-e` | `--email` | No* | - | Email a investigar (reputacion) |
| `-o` | `--output` | Si | - | Directorio de salida para el reporte |
| `-l` | `--limit` | No | 15 | Limite de resultados por seccion |

*\*Al menos uno de `--domain` o `--email` es requerido. Ambos pueden usarse juntos.*

#### Modos de ejecucion

| Comando | Comportamiento |
|---|---|
| `python main.py -d example.com -o report/` | Solo escaneo de dominio |
| `python main.py -e user@example.com -o report/` | Solo investigacion de email |
| `python main.py -d example.com -e admin@example.com -o report/` | Ambos: email primero, dominio despues |

#### Flujo de ejecucion:
1. Parsea argumentos de linea de comandos
2. Valida que al menos un target este presente (`--domain` o `--email`)
3. Crea el container DI con `create_default_container()`
4. Si `--email` presente:
   - Resuelve `LeakCheckOSINT` y `ReportRepository`
   - Instancia `EmailInvestigationUseCase` con las dependencias
   - Ejecuta la investigacion de email
5. Si `--domain` presente:
   - Resuelve `OSINTProvider` y `ReportRepository`
   - Instancia `ScanUseCaseSimple` con las dependencias
   - Ejecuta el escaneo de dominio
6. Muestra resultados o captura errores con codigos de salida apropiados

---

### 5. Inyeccion de Dependencias (`internal/container.py`)

`Container` es un contenedor DI ligero que centraliza la creacion y resolucion de dependencias.

#### API del Container

| Metodo | Descripcion |
|---|---|
| `register(interface, implementation)` | Registra una clase factory para una interfaz |
| `register_instance(interface, instance)` | Registra una instancia ya creada (singleton) |
| `resolve(interface)` | Resuelve y retorna la implementacion (crea si es necesario, cachea después) |
| `reset()` | Limpia todos los registros e instancias |

#### Configuracion por defecto (`create_default_container`)

```
OSINTProvider     --> HackerTargetOSINT
LeakCheckOSINT    --> LeakCheckOSINT()
ReportRepository  --> MarkdownReportRepository
```

> El container permite sustituir implementaciones sin modificar el codigo de los casos de uso, facilitando testing y extension.

---

## Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (CLI)                        │
│                                                          │
│  1. Parsea argumentos (domain, email, output, limit)     │
│  2. Valida: al menos un target requerido                 │
│  3. Crea Container                                       │
│  4. Resuelve dependencias                                │
│  5. Ejecuta caso(s) de uso                               │
└──────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Container (DI Container)                    │
│                                                          │
│  OSINTProvider    ──►  HackerTargetOSINT                 │
│  LeakCheckOSINT   ──►  LeakCheckOSINT()                  │
│  ReportRepository ──►  MarkdownReportRepository          │
└──────────────────────┬──────────────────────────────────┘
                        │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
┌────────────────────────┐  ┌─────────────────────────────┐
│  --domain presente?    │  │  --email presente?          │
│                        │  │                             │
│  ScanUseCaseSimple     │  │  EmailInvestigationUseCase  │
│                        │  │                             │
│  1. fetch(target)      │  │  1. Validar formato email   │
│  2. save_report()      │  │  2. fetch(email)            │
│  3. ScanResult         │  │  3. save_report()           │
└───────────┬────────────┘  │  4. ScanResult              │
            │               └──────────────┬──────────────┘
            │                              │
            ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│  HackerTargetOSINT   │    │  LeakCheckOSINT              │
│  (OSINTProvider)     │    │  (Email Breach Lookup)       │
│                      │    │                              │
│  - Subdominios       │    │  - Brechas encontradas       │
│  - DNS               │    │  - Fechas de brechas         │
│  - GeoIP             │    │  - Campos expuestos          │
│  - Reverse IP        │    │  - Servicios afectados       │
│  - WHOIS/RDAP        │    │                              │
└──────────────────────┘    └──────────────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
            ┌──────────────────────────────┐
            │ MarkdownReportRepository     │
            │ (ReportRepository)           │
            │                              │
            │  - Crea directorio           │
            │  - Escribe archivo .md       │
            │  - Retorna ruta completa     │
            └──────────────────────────────┘
```

---

## Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Flujo de Dominio                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Target (dominio)                                                    │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────┐     Markdown string     ┌──────────────────┐   │
│  │  OSINTProvider   │ ──────────────────────► │ ReportRepository  │   │
│  │  (fetch)         │                         │ (save_report)     │   │
│  └─────────────────┘                         └──────────────────┘   │
│         │                                              │             │
│         ▼                                              ▼             │
│     API Externas                                 Archivo .md         │
│     (HackerTarget, Censys)                       (domain_report)     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Flujo de Email                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Target (email)                                                      │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────┐   Validacion    ┌───────────────────────┐  │
│  │ EmailInvestigation   │ ──────────────► │ @ presente?           │  │
│  │ UseCase              │                 │ Si → continuar        │  │
│  └──────────┬──────────┘                 │ No → ValueError       │  │
│             │                            └───────────────────────┘  │
│             ▼                                                        │
│  ┌─────────────────┐     Markdown string     ┌──────────────────┐   │
│  │  LeakCheckOSINT   │ ──────────────────────► │ ReportRepository  │   │
│  │  (fetch)          │                         │ (save_report)     │   │
│  └─────────────────┘                         └──────────────────┘   │
│         │                                              │             │
│         ▼                                              ▼             │
│     LeakCheck API                                Archivo .md         │
│                                                  (email_report)     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Principios de Diseno Aplicados

| Principio | Implementacion |
|---|---|
| **Clean Architecture** | Separacion en 4 capas: Dominio, Aplicacion, Infraestructura, Presentacion |
| **Dependency Inversion** | Los casos de uso dependen de protocolos (abstracciones), no de implementaciones |
| **Interface Segregation** | Protocolos especificos: `OSINTProvider`, `IAProvider`, `ReportRepository` |
| **Single Responsibility** | Cada archivo tiene una responsabilidad unica y bien definida |
| **Open/Closed** | Nuevos proveedores OSINT se agregan creando nuevos adaptadores sin modificar existentes |
| **Dependency Injection** | Container DI que registra y resuelve dependencias |
| **Inmutabilidad** | `ScanResult` es una dataclass frozen (inmutable) |

---

## Extension y Nuevos Proveedores

### Agregar un nuevo proveedor OSINT

1. Crear una nueva clase en `internal/infra/` que herede de `BaseOSINTAdapter`
2. Implementar el metodo `fetch(target, limit) -> str`
3. Registrarlo en el container: `container.register(OSINTProvider, NuevoProvider)`

### Agregar un nuevo caso de uso

1. Crear una nueva clase en `internal/usecases/`
2. Definir dependencias via constructor (preferir puertos del dominio cuando sea posible)
3. Implementar metodo `execute()` que retorne `ScanResult`
4. Agregar argumento CLI correspondiente en `main.py`
5. Wirear la resolucion de dependencias en el flujo principal

**Ejemplo:** `EmailInvestigationUseCase` fue agregado siguiendo este patron:
- Nuevo archivo `internal/usecases/email.py`
- Depende de `LeakCheckOSINT` (adaptador concreto) y `ReportRepository` (puerto)
- Flag CLI `--email`/`-e` agregado a `main.py`
- Puede combinarse con `--domain` en la misma ejecucion

### Agregar un nuevo formato de reporte

1. Crear una nueva clase en `internal/infra/` que implemente `save_report()`
2. Registrarlo en el container: `container.register(ReportRepository, NuevoRepository)`

---

## Dependencias Externas

| Libreria | Uso | Capa |
|---|---|---|
| `requests` | Peticiones HTTP a APIs externas | Infraestructura |
| `argparse` | Parsing de argumentos CLI (stdlib) | Presentacion |
| `dataclasses` | Entidades de dominio (stdlib) | Dominio |
| `typing` | Protocolos y type hints (stdlib) | Dominio |

---

## Testing

El proyecto incluye una suite de tests organizada por nivel:

| Archivo | Tipo | Descripcion |
|---|---|---|
| `tests/test_email_usecase_unit.py` | Unit | Tests del `EmailInvestigationUseCase` (validacion, fetch, manejo de errores) |
| `tests/test_email_integration.py` | Integration | Tests con repositorio real y provider mockeado |
| `tests/test_cli_e2e.py` | E2E | Tests del CLI completo via subprocess |

### Cobertura

- Validacion de formato de email
- Integracion con `LeakCheckOSINT`
- Propagacion de `AdapterError`
- Generacion de reportes Markdown
- Escenarios CLI: solo email, solo dominio, ambos, ninguno, email invalido

---

## Consideraciones de Seguridad

- Las API keys se gestionan via variables de entorno (`.env`), nunca hardcodeadas
- Todas las peticiones HTTP tienen timeouts configurables
- El `.gitignore` excluye `.env` y credenciales
- Los errores de API se manejan con excepciones especificas (`AdapterError`)
- La herramienta realiza solo reconocimiento **pasivo** (no interactua directamente con el target)
