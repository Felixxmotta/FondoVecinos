# 🏛️ SISTEMA DIGITAL DE GESTIÓN FINANCIERA
## FONDO DE VECINOS DE LA MESA — GUÍA DE MANTENIMIENTO TÉCNICO

> **Versión:** 2.0 | **Fecha:** Septiembre 2026  
> **Público objetivo:** Administrador técnico / Desarrollador  
> **Estado del sistema:** 🟢 100% OPERATIVO

---

## 📋 INFORME DE AUDITORÍA TÉCNICA DEL SISTEMA

| Componente | Estado | Detalle Técnico |
|---|---|---|
| Descarga Google Sheets | 🟢 OK | Conexión SSL exitosa. Descarga en formato XLSX. |
| Carga de Datos (app.py) | 🟢 OK | 12 métricas de Resumen, socios en Ahorros, créditos en Flujo. |
| Mapeo de Amortizaciones | 🟢 OK | Créditos emparejados exitosamente por ID/Nombre/Monto. |
| Formato de Fechas | 🟢 OK | Todas las fechas convertidas a DD/MM/YYYY. |
| Generación de Fichas PNG | 🟢 OK | Generador Pillow operativo con branding y logo. |
| Infraestructura Railway | 🟢 OK | Servidor activo 24/7 con reinicio automático. |
| Apps Script (Google Sheets) | 🟢 OK | Menú automatización operativo con 3 funciones. |
| Integración WhatsApp | 🟢 OK | Envío por texto e imagen desde el Dashboard. |
| Módulo de Liquidaciones | 🟢 OK | Cálculo y registro en historial operativo. |

---

## 🏗️ ARQUITECTURA TÉCNICA DEL SISTEMA

```
┌─────────────────────────────────────────────────┐
│              GOOGLE SHEETS (Datos)               │
│  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ RESUMEN      │  │ CONTROL AHORRO           │  │
│  │ GENERAL      │  │ (socios + meses)         │  │
│  ├──────────────┤  ├──────────────────────────┤  │
│  │ FLUJO        │  │ AMORTIZACIONES           │  │
│  │ PRESTAMOS    │  │ (tablas de cuotas)       │  │
│  ├──────────────┤  ├──────────────────────────┤  │
│  │ REGISTRO     │  │ whatsapp # / LIQUIDADOR  │  │
│  │ NUEVO        │  │ HISTORIAL LIQUIDACIONES  │  │
│  └──────────────┘  └──────────────────────────┘  │
│  + Google Apps Script (automatización)            │
└───────────────────┬─────────────────────────────┘
                    │ HTTPS / XLSX export
                    ▼
┌─────────────────────────────────────────────────┐
│         DASHBOARD WEB (app.py + Streamlit)       │
│  • Hosted en Railway (24/7)                      │
│  • Python 3.x + Streamlit + Plotly + Pillow      │
│  • URL: chatbotwap-production-e2a3.up.railway.app │
└───────────────────┬─────────────────────────────┘
                    │ WhatsApp API links
                    ▼
┌─────────────────────────────────────────────────┐
│         WHATSAPP WEB (Notificaciones)            │
│  • Mensajes de texto preformateados              │
│  • Fichas PNG descargables y compartibles        │
└─────────────────────────────────────────────────┘
```

---

## 📁 ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
fondo_vecinos/code/
│
├── app.py                    # Aplicación principal Streamlit (2004 líneas)
├── google_apps_script.js     # Script de automatización para Google Sheets
├── logo.png                  # Logo oficial del fondo (branding)
│
├── requirements.txt          # Dependencias Python
├── Procfile                  # Comando de inicio para Railway
├── railway.toml              # Configuración de Railway
├── render.yaml               # Configuración alternativa (Render.com)
│
├── MANUAL_USUARIO.md         # Manual de operación para el tesorero
├── GUIA_MANTENIMIENTO.md     # Este documento
│
└── .streamlit/               # Configuración de Streamlit
```

### Dependencias Python (requirements.txt)

```
streamlit
pandas
numpy
plotly
pillow
openpyxl
```

---

## 🔑 VARIABLES Y CONFIGURACIONES CLAVE

### URL de Google Sheets (en app.py, línea 581)

```python
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZL5aORQJ7C00YgpMUOfoXyKYtMkB2PRfbKUNrCGQPMc/export?format=xlsx"
```

> **⚠️ IMPORTANTE:** Si se cambia la planilla de Google Sheets (por ejemplo, se crea una nueva), se debe actualizar esta URL en `app.py` y hacer un nuevo despliegue en Railway.

### Nombres de Pestañas que el Sistema Busca (NO CAMBIAR)

El sistema busca las pestañas de forma flexible (insensible a mayúsculas y coincidencia parcial), pero los nombres recomendados son:

| Nombre Oficial | Alias Aceptados |
|---|---|
| `RESUMEN GENERAL` | `Resumen General` |
| `CONTROL AHORRO` | `Control Ahorros`, `CONTROL AHORROS` |
| `FLUJO PRESTAMOS` | `Flujo prestamos`, `FLUJO PRESTAMO` |
| `AMORTIZACIONES` | `Amortizaciones` |
| `REGISTRO NUEVO` | (exacto) |
| `whatsapp #` | `whatsapp 3`, `WHATSAPP` |
| `LIQUIDADOR` | (exacto) |
| `HISTORIAL LIQUIDACIONES` | (exacto, se crea automáticamente) |

### Caché del Dashboard

```python
@st.cache_data(ttl=5)  # Los datos se cachean por 5 segundos
```

Esto significa que el Dashboard refresca datos cada 5 segundos automáticamente, o de forma inmediata al presionar el botón **"🔄 Actualizar Datos"**.

---

## 📌 REGLAS DE MANTENIMIENTO PREVENTIVO

### 📌 Regla 1: Permisos de Google Sheets (CRÍTICO)

Para que el Dashboard pueda leer los datos, el archivo DEBE estar público:

1. En Google Sheets: **Compartir → Acceso General → Cualquier persona con el enlace → Lector**.
2. Si se cambia a privado, el Dashboard mostrará un error rojo de conexión.

> **Verificación:** Abrir la URL de SHEET_URL en modo incógnito. Si carga el archivo, está público. Si pide login, está privado.

### 📌 Regla 2: Encabezados y Estructura del Excel

El sistema lee datos usando nombres de columnas específicos. Si se agregan columnas o se cambian encabezados, el sistema puede fallar.

**Columnas críticas en FLUJO PRESTAMOS:**

| Columna | Letra | Nombre Requerido |
|---|---|---|
| A | ID del crédito | `ID` |
| B | Nombre del deudor | `Nombre` |
| C | Tipo | `Tipo` |
| D | Monto prestado | `Monto` |
| E | Tasa de interés | `Tasa (%)` |
| F | Plazo en meses | `Plazo` |
| G | Cuota fija mensual | `Cuota Fija` |
| H | Total de intereses | `Total Interés` |
| I | Total a pagar | `Total a Pagar` |
| J | Abonos realizados | `Abonos Iniciales` |
| K | Saldo pendiente | `Saldo Pendiente` ← **FÓRMULA AUTOMÁTICA** |
| L | Estado del crédito | `Estado del credito` ← **FÓRMULA AUTOMÁTICA** |
| M | Intereses cobrados | `Intereses Cobrados` ← **FÓRMULA AUTOMÁTICA** |

**Columnas críticas en CONTROL AHORRO:**

| Columna | Nombre | Nota |
|---|---|---|
| A | `Socio` | Nombre del socio |
| B | `Aporte Base` | Cuota mensual base |
| C a AJ | Meses del año | Fechas en fila 3 |
| AK | `Total Anual` | Fórmula `=SUM(C:AJ)` |

### 📌 Regla 3: Política de Respaldos Mensuales

**El primer día de cada mes:**

1. Abrir Google Sheets.
2. Ir a: **Archivo → Hacer una copia**.
3. Nombre del backup: `fondo_vecinos_backup_AAAA_MM.xlsx` (ej: `fondo_vecinos_backup_2026_09.xlsx`).
4. Guardar en la misma carpeta de Google Drive.

> Esto garantiza un histórico de seguridad ante cualquier borrado o modificación accidental.

### 📌 Regla 4: Mantenimiento de Railway (Hosting)

El servicio está alojado en Railway con reinicio automático 24/7.

**Si el Dashboard no responde:**
1. Ir a [Railway.app](https://railway.app) e iniciar sesión.
2. Buscar el proyecto del fondo.
3. Hacer clic en **"Redeploy"**.
4. Esperar 1–2 minutos para que el servidor reinicie.

**El código fuente está respaldado en GitHub** en la rama `main`. Si se necesita desplegar desde cero, hacer un nuevo "Deploy from GitHub repo".

### 📌 Regla 5: Mantenimiento del Apps Script

El script de automatización en Google Sheets (google_apps_script.js) tiene las siguientes funciones activas:

| Función | Activación | Descripción |
|---|---|---|
| `registrarNuevo()` | Botón en planilla / Menú | Inscribe nuevo socio o crédito |
| `repararTodasLasFormulas()` | Menú → Reparar Fórmulas | Reconstruye fórmulas K, L, M |
| `aplicarLiquidacionAResumen()` | Menú → Aplicar Liquidación | Procesa retiro de socio |
| `colorearFlujoPrestamos()` | Automática al editar | Colorea columna L por estado |
| `onEdit(e)` | Automática | Dispara colorearFlujo al editar |
| `onOpen()` | Al abrir la planilla | Crea el menú ⚡ Fondo Vecinos |

**Para actualizar el Apps Script:**
1. En Google Sheets: **Extensiones → Apps Script**.
2. Copiar el contenido de `google_apps_script.js` al editor.
3. Guardar y ejecutar `onOpen()` para registrar el nuevo menú.

---

## 🚨 CHECKLIST SOLUCIÓN DE PROBLEMAS

| Síntoma | Causa Probable | Solución |
|---|---|---|
| Dashboard muestra error rojo de conexión | Google Sheets cambió a privado o cayó el enlace | Verificar que el archivo esté en "Cualquier persona con el enlace – Lector" |
| Los datos no se actualizan tras ingresar un pago | Caché de Streamlit activo | Hacer clic en **"🔄 Actualizar Datos"** en la barra lateral |
| Un crédito nuevo no muestra fechas en amortización | Fecha ingresada en formato incorrecto en C16 | Asegurarse de que C16 esté en formato `DD/MM/YYYY` (ej: 05/09/2026) |
| Las fórmulas de columna K o L desaparecieron | Modificación manual accidental en FLUJO PRESTAMOS | Ir al menú: **⚡ Fondo Vecinos → Reparar Fórmulas Flujo Préstamos** |
| Un participante no aparece en el Dashboard | Nombre en planilla con caracteres especiales o espacios | Normalizar el nombre en la planilla (mayúsculas, sin acentos extra) |
| El menú ⚡ Fondo Vecinos no aparece en Sheets | El Apps Script no se ha activado | Ir a Extensiones → Apps Script → Ejecutar `onOpen()` manualmente |
| Dashboard no carga y Railway muestra error | El servidor se cayó o hubo un deploy fallido | Hacer "Redeploy" desde Railway |
| Un socio en WhatsApp no recibe el mensaje directo | Número no registrado en pestaña "whatsapp #" | Agregar el teléfono de 10 dígitos en la columna "numero" de la pestaña whatsapp # |
| La imagen PNG (Ficha) no se genera | Librería Pillow no instalada correctamente | Verificar que `pillow` esté en requirements.txt y hacer Redeploy |
| El crédito aparece como Activo aunque está pagado | Saldo residual >$5 por redondeo | Ingresar el valor exacto en columna J hasta que K quede ≤ $5, o ajustar manualmente J |

---

## 🔒 LÓGICA DE NEGOCIO — CÓMO FUNCIONAN LAS FÓRMULAS AUTOMÁTICAS

### Saldo Pendiente (Columna K)
```
=I{fila} - J{fila}
(Total a Pagar) - (Abonos Realizados)
```

### Estado del Crédito (Columna L)
```
=IF(ISBLANK(A{fila}), "", IF(K{fila}<=5, "Cancelado", "Activo"))
```
- Si el saldo (K) es ≤ $5 COP → **"Cancelado"** (fondo gris #e2e8f0).
- Si el saldo (K) es > $5 COP → **"Activo"** (fondo verde #d1fae5).
- El umbral de $5 cubre diferencias de redondeo en centavos.

### Intereses Cobrados (Columna M)
```
=IF(ISBLANK(A{fila}), "", IF(OR(
  REGEXMATCH(UPPER(L{fila}), "CANCEL|PAGAD|FINALIZ"),
  AND(ISNUMBER(K{fila}), K{fila}<=5)
), H{fila}, 0))
```
- Los intereses se registran como cobrados **solo cuando el crédito está cancelado**.
- Mientras el crédito esté activo, la columna M muestra $0 (los intereses aún no se han cobrado).

### Detección de Estado del Participante en el Dashboard

El Dashboard evalúa el estado de cada participante comparando:
1. **Ahorro:** Detecta el último mes con pagos en la planilla y compara con el mes activo máximo. Si hay 2+ meses de retraso → INACTIVO.
2. **Créditos:** Si algún crédito tiene estado "MORA" o "INACTIVO" en la columna L → INACTIVO.
3. **Retiro:** Si en las columnas de notas de CONTROL AHORRO aparece la palabra "retiro" → RETIRADO.

---

## 🔧 PROCEDIMIENTOS DE MANTENIMIENTO PROGRAMADOS

### Mensual (Primer día del mes)

- [ ] Hacer backup de Google Sheets (ver Regla 3).
- [ ] Revisar que el Dashboard cargue correctamente.
- [ ] Verificar que los nuevos créditos del mes aparezcan en el Dashboard.
- [ ] Confirmar que la columna del mes actual en CONTROL AHORRO esté activa.

### Trimestral

- [ ] Verificar el plan de Railway (puede haber cambios en el hosting).
- [ ] Revisar que el repositorio de GitHub esté actualizado.
- [ ] Probar el botón "Reparar Fórmulas" para confirmar que el Apps Script funciona.
- [ ] Actualizar el Apps Script si hubo cambios en la lógica de negocio.

### Anual (Al inicio del nuevo año)

- [ ] Crear una nueva columna en CONTROL AHORRO para el nuevo año (columnas de meses).
- [ ] Actualizar el año en el Apps Script si hay referencias hardcodeadas.
- [ ] Revisar si Railway necesita actualización de plan o configuración.
- [ ] Archivar la planilla del año anterior como backup histórico.

---

## 🛠️ CÓMO ACTUALIZAR EL CÓDIGO DEL DASHBOARD

Si es necesario modificar `app.py`:

1. **Clonar o actualizar el repositorio GitHub** donde está alojado el código.
2. **Hacer los cambios en `app.py`** localmente.
3. **Hacer commit y push a la rama `main`** en GitHub.
4. Railway detecta automáticamente el cambio y hace deploy en 1–2 minutos.
5. **Verificar el Dashboard** para confirmar que los cambios funcionan correctamente.

**Si solo se cambia la URL de Google Sheets:**
1. Editar la línea 581 de `app.py`:
   ```python
   SHEET_URL = "https://docs.google.com/spreadsheets/d/NUEVO_ID/export?format=xlsx"
   ```
2. Hacer commit y push.
3. Railway hará redeploy automáticamente.

---

## 📊 MÉTRICAS DE RENDIMIENTO ESPERADAS

| Métrica | Valor Esperado |
|---|---|
| Tiempo de carga inicial del Dashboard | 3–6 segundos |
| Tiempo de actualización de datos (botón 🔄) | 1–3 segundos |
| Tiempo de generación de PNG (Ficha individual) | < 1 segundo |
| Disponibilidad del servidor Railway | 99.9% (reinicio automático) |
| Tamaño del archivo XLSX de Google Sheets | < 500 KB (óptimo) |

---

## 📝 HISTORIAL DE CAMBIOS Y VERSIONES

| Versión | Fecha | Cambios |
|---|---|---|
| 1.0 | 2026 | Versión inicial: dashboard básico + Google Sheets |
| 1.5 | 2026 | Integración WhatsApp, fichas PNG, bandeja de despacho |
| 1.8 | 2026 | Módulo de liquidaciones, historial de retiros |
| 2.0 | Sep 2026 | Versión final entregada: todos los módulos operativos, manuales actualizados |

---

*FONDO DE VECINOS DE LA MESA — Guía de Mantenimiento Técnico © 2026*
