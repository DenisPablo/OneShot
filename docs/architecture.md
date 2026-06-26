# OneShot - Arquitectura del Proyecto

## Descripcion General

OneShot es una herramienta OSINT (Open Source Intelligence) escrita en Python, disenada para realizar reconocimiento pasivo de dominios. Recopila informacion publica de multiples fuentes (HackerTarget, Censys, EmailRep, RDAP/WHOIS) y genera reportes estructurados en formato Markdown.

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
│   │   └── scan.py                 # Caso de uso principal de escaneo
│   └── infra/                      # Capa de Infraestructura (Adaptadores)
│       ├── __init__.py
│       ├── base.py                 # Adaptador base con metodos HTTP seguros
│       ├── exceptions.py           # Excepciones de infraestructura
│       ├── hackertarget.py         # Adaptador HackerTarget API
│       ├── censys.py               # Adaptador Censys API
│       ├── emailrep.py             # Adaptador EmailRep API
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
| `EmailRepOSINT` | EmailRep | `OSINTProvider` | Opcional |
| `OpenRouterIAProvider` | OpenRouter | `IAProvider` | Si |

**HackerTargetOSINT** (proveedor por defecto) recolecta:
- Subdominios e IPs asociadas (`hostsearch`)
- Registros DNS (`dnslookup`)
- Informacion GeoIP (`geoip`)
- Reverse IP lookup (`reverseiplookup`)
- Informacion de registro WHOIS/RDAP (`rdap.org`)

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
| `-d` | `--domain` | Si | - | Target (dominio) a escanear |
| `-o` | `--output` | Si | - | Directorio de salida para el reporte |
| `-l` | `--limit` | No | 15 | Limite de resultados por seccion |

#### Flujo de ejecucion:
1. Parsea argumentos de linea de comandos
2. Crea el container DI con `create_default_container()`
3. Resuelve las dependencias (`OSINTProvider`, `ReportRepository`)
4. Instancia el caso de uso `ScanUseCaseSimple` con las dependencias inyectadas
5. Ejecuta el escaneo
6. Muestra el resultado o captura errores con codigos de salida apropiados

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
ReportRepository  --> MarkdownReportRepository
```

> El container permite sustituir implementaciones sin modificar el codigo de los casos de uso, facilitando testing y extension.

---

## Diagrama de Flujo Principal

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (CLI)                        │
│                                                          │
│  1. Parsea argumentos (domain, output, limit)            │
│  2. Crea Container                                       │
│  3. Resuelve dependencias                                │
│  4. Ejecuta caso de uso                                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Container (DI Container)                    │
│                                                          │
│  OSINTProvider    ──►  HackerTargetOSINT                 │
│  ReportRepository ──►  MarkdownReportRepository          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          ScanUseCaseSimple (Caso de Uso)                 │
│                                                          │
│  1. osint_provider.fetch(target, limit)                  │
│  2. Genera nombre de archivo                             │
│  3. report_service.save_report(data, output, filename)   │
│  4. Retorna ScanResult                                   │
└───────┬─────────────────────────────────┬───────────────┘
        │                                 │
        ▼                                 ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│  HackerTargetOSINT   │    │ MarkdownReportRepository     │
│  (OSINTProvider)     │    │ (ReportRepository)           │
│                      │    │                              │
│  - Subdominios       │    │  - Crea directorio           │
│  - DNS               │    │  - Escribe archivo .md       │
│  - GeoIP             │    │  - Retorna ruta completa     │
│  - Reverse IP        │    │                              │
│  - WHOIS/RDAP        │    │                              │
└──────────────────────┘    └──────────────────────────────┘
```

---

## Flujo de Datos

```
Target (dominio)
       │
       ▼
┌─────────────────┐     Markdown string     ┌──────────────────┐
│  OSINTProvider   │ ──────────────────────► │ ReportRepository  │
│  (fetch)         │                         │ (save_report)     │
└─────────────────┘                         └──────────────────┘
       │                                              │
       ▼                                              ▼
   API Externas                                 Archivo .md en disco
   (HackerTarget,
    Censys, etc.)
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

Para agregar un nuevo proveedor OSINT:

1. Crear una nueva clase en `internal/infra/` que herede de `BaseOSINTAdapter`
2. Implementar el metodo `fetch(target, limit) -> str`
3. Registrarlo en el container: `container.register(OSINTProvider, NuevoProvider)`

Para agregar un nuevo formato de reporte:

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

## Consideraciones de Seguridad

- Las API keys se gestionan via variables de entorno (`.env`), nunca hardcodeadas
- Todas las peticiones HTTP tienen timeouts configurables
- El `.gitignore` excluye `.env` y credenciales
- Los errores de API se manejan con excepciones especificas (`AdapterError`)
- La herramienta realiza solo reconocimiento **pasivo** (no interactua directamente con el target)
