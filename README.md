# 🔍 OneShot

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OSINT](https://img.shields.io/badge/type-OSINT%20Tool-orange.svg)]()

> **Herramienta OSINT (Open Source Intelligence)** para reconocimiento pasivo de dominios. Recopila información pública de múltiples fuentes y genera reportes estructurados en Markdown, con análisis opcional mediante IA.

![OneShot Banner](https://img.shields.io/badge/OneShot-OSINT%20Reconnaissance-2ea44f?style=for-the-badge)

---

## ✨ Características

- 🔎 **Reconocimiento pasivo** sin interactuar directamente con el target
- 📡 **Múltiples fuentes**: HackerTarget, Censys, EmailRep, RDAP/WHOIS
- 🧠 **Análisis con IA** mediante OpenRouter (router gratuito disponible)
- 📄 **Reportes en Markdown** bien estructurados y fáciles de leer
- 🏗️ **Clean Architecture** con inyección de dependencias
- 🔑 **API keys gestionadas** mediante variables de entorno
- ⚡ **Rápida y ligera**, solo dependencias esenciales

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd OneShot
```

### 2. Crear y activar entorno virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y completa tus API keys:

```bash
cp .env.example .env
```

Edita el archivo `.env`:

```env
# Censys - Lookup de hosts por IP (plan gratuito)
CENSYS_API_TOKEN=censys_tu_token_aqui

# OpenRouter - Análisis con IA (router gratuito)
OPENROUTER_API_KEY=sk-or-v1-tu_key_aqui

# EmailRep - Reputación de emails (opcional)
EMAILREP_API_KEY=
```

> 🔑 Obtén tus API keys en:
> - **Censys**: https://accounts.censys.io/settings/personal-access-tokens
> - **OpenRouter**: https://openrouter.ai/keys
> - **EmailRep**: https://emailrep.io/

---

## 🎯 Uso

### Escaneo básico

```bash
python main.py -d example.com -o ./reports
```

### Escaneo con límite de resultados

```bash
python main.py -d example.com -o ./reports -l 20
```

### Escaneo + análisis con IA

```bash
python main.py -d example.com -o ./reports --analyze
```

### Ayuda

```bash
python main.py --help
```

---

## 📂 Estructura de reportes

Tras ejecutar un escaneo, se generan los siguientes archivos en el directorio de salida:

| Archivo | Descripción |
|---|---|
| `report_{dominio}_hackertarget.md` | Subdominios, DNS, GeoIP, Reverse IP, WHOIS |
| `report_{dominio}_censys.md` | Información del host por IP (requiere CENSYS_API_TOKEN) |
| `analysis_{dominio}.md` | Análisis ejecutivo generado por IA (requiere OPENROUTER_API_KEY y `--analyze`) |

---

## 🎬 Escenarios de uso

### Escenario 1: Auditoría de seguridad básica

Un analista de seguridad necesita conocer la superficie de exposición de un dominio antes de una auditoría autorizada.

```bash
python main.py -d empresa.com -o ./auditorias/empresa -l 30
```

**Salida esperada:**
```text
[+] Iniciando escaneo en: empresa.com
[*] Usando proveedor: HackerTargetOSINT
[*] Ejecutando reconocimiento con HackerTargetOSINT...
[*] Guardando reporte de HackerTargetOSINT...
[+] Reporte guardado: report_empresa.com_hackertarget.md
[*] Censys: deshabilitado (CENSYS_API_TOKEN no configurado)
[+] Escaneo completado
[*] Reporte guardado en: ./auditorias/empresa/report_empresa.com_hackertarget.md
```

---

### Escenario 2: Investigación con Censys

Se cuenta con una API key de Censys y se desea obtener información del host asociado a la IP principal del dominio.

```bash
python main.py -d github.com -o ./investigaciones -l 25
```

**Salida esperada:**
```text
[+] Iniciando escaneo en: github.com
[*] Usando proveedor: HackerTargetOSINT
[*] Ejecutando reconocimiento con HackerTargetOSINT...
[*] Guardando reporte de HackerTargetOSINT...
[+] Reporte guardado: report_github.com_hackertarget.md
[+] Censys: habilitado y conectado
[*] Consultando IP 140.82.121.4 en Censys...
[+] Reporte Censys guardado: report_github.com_censys.md
[+] Escaneo completado
[*] Reporte guardado en: ./investigaciones/report_github.com_hackertarget.md
```

---

### Escenario 3: Generación de informe ejecutivo con IA

Se requiere un resumen ejecutivo con recomendaciones de seguridad a partir de los datos recolectados.

```bash
python main.py -d render.com -o ./reports --analyze
```

**Salida esperada:**
```text
[+] Iniciando escaneo en: render.com
[*] Usando proveedor: HackerTargetOSINT
[*] Ejecutando reconocimiento con HackerTargetOSINT...
[+] Reporte guardado: report_render.com_hackertarget.md
[+] Censys: habilitado y conectado
[*] Consultando IP 216.24.57.1 en Censys...
[+] Reporte Censys guardado: report_render.com_censys.md
[+] Análisis IA: habilitado
[*] Analizando reportes con IA...
[+] Análisis guardado en: analysis_render.com.md
[+] Escaneo completado
```

---

### Escenario 4: Análisis de email sospechoso

Para investigar la reputación de una dirección de email, se puede usar EmailRep (aún no integrado en el flujo principal del CLI, pero disponible como adaptador).

```python
from internal.container import create_default_container
from internal.infra.emailrep import EmailRepOSINT

provider = EmailRepOSINT(api_key="tu_emailrep_key")
resultado = provider.fetch("sospechoso@dominio.com")
print(resultado)
```

---

## ⚠️ Consideraciones importantes

- Esta herramienta realiza **reconocimiento pasivo** únicamente.
- Asegúrate de contar con **autorización explícita** antes de escanear sistemas que no te pertenecen.
- Las API keys deben mantenerse seguras y nunca subirse a repositorios públicos.
- El archivo `.env` está incluido en `.gitignore` por defecto.

---

## 🛠️ Desarrollo

### Ejecutar tests

```bash
pytest tests/
```

> Nota: Actualmente el proyecto no incluye tests. Se recomienda agregarlos al extender funcionalidades.

### Arquitectura

```
main.py (CLI)
    ↓
internal/usecases/scan.py (Application)
    ↓
internal/domain/ (Domain - solo stdlib)
    ↑
internal/infra/ (Infrastructure - adaptadores)
```

---

## 📦 Dependencias

| Librería | Uso |
|---|---|
| `requests` | Peticiones HTTP a APIs externas |
| `python-dotenv` | Carga de variables de entorno desde `.env` |

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si deseas agregar un nuevo proveedor OSINT:

1. Crea una clase en `internal/infra/` que herede de `BaseOSINTAdapter`
2. Implementa el método `fetch(target, limit) -> str`
3. Regístrala en `internal/container.py`

---

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

---

<p align="center">
  <strong>OneShot</strong> — Reconocimiento OSINT rápido, pasivo y ordenado.
</p>
