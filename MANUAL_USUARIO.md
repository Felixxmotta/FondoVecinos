# 🏛️ SISTEMA DIGITAL DE GESTIÓN FINANCIERA
## FONDO DE VECINOS DE LA MESA — MANUAL DE USUARIO

> **Versión:** 2.0 | **Fecha:** Septiembre 2026  
> **Administrado por:** Tesorero / Administrador del Fondo  
> **Dashboard:** https://chatbotwap-production-e2a3.up.railway.app/

---

## GUÍA DE USO: CÓMO OPERAR EL SISTEMA COMPLETO

Este manual explica paso a paso cómo usar **el Dashboard Web** y **la Planilla de Google Sheets**, las dos herramientas centrales del sistema. Están conectadas en tiempo real: lo que se registra en la planilla se refleja automáticamente en el Dashboard.

---

## 🗺️ ARQUITECTURA DEL SISTEMA (CÓMO ESTÁ CONECTADO TODO)

```
PLANILLA GOOGLE SHEETS (fuente de datos)
        ↓  (conexión automática en tiempo real)
DASHBOARD WEB (visualización y gestión)
        ↓  (botón de 1 clic)
WHATSAPP (notificaciones a socios)
```

| Componente | Función | ¿Quién lo usa? |
|---|---|---|
| **Google Sheets** | Registro de pagos, socios, créditos | Administrador / Tesorero |
| **Dashboard Web** | Visualización, consultas, envío WA | Administrador / Directivos |
| **Apps Script** | Automatización de fórmulas y registros | Sistema automático |

---

## 📋 PESTAÑAS DEL EXCEL Y SU FUNCIÓN

El archivo de Google Sheets tiene las siguientes pestañas. **No se debe cambiar el nombre de ninguna:**

| Pestaña | Función | ¿Se puede editar manualmente? |
|---|---|---|
| **RESUMEN GENERAL** | Balance consolidado del fondo (totales) | 🟡 Solo columna C de valores |
| **CONTROL AHORRO** | Aportes mensuales de cada socio | 🟢 Sí — Columnas de meses (C a AJ) |
| **FLUJO PRESTAMOS** | Registro de todos los créditos | 🟡 Solo columna J (Abonos) |
| **AMORTIZACIONES** | Tablas de cuotas generadas automáticamente | 🔴 NO TOCAR |
| **REGISTRO NUEVO** | Formulario para inscribir socios o créditos | 🟢 Sí — Celdas C4 a C16 |
| **whatsapp #** | Teléfonos de participantes para envío WA | 🟢 Sí — Agregar / actualizar teléfonos |
| **LIQUIDADOR** | Calculadora de liquidación de socios retirados | 🟡 Solo columna C de datos del socio |
| **HISTORIAL LIQUIDACIONES** | Registro histórico de retiros | 🔴 No modificar manualmente |

---

## 🛑 REGLA DE ORO: ¿QUÉ SE PUEDE TOCAR Y QUÉ NO?

| Pestaña / Columna | ¿Editable? | Razón |
|---|---|---|
| REGISTRO NUEVO → Celdas C4 a C16 | ✅ SÍ | Es el formulario de entrada oficial |
| FLUJO PRESTAMOS → Columna J (Abonos) | ✅ SÍ | Aquí se registra lo que ha pagado el deudor |
| FLUJO PRESTAMOS → Columnas K, L, M | 🔴 NO | Tienen fórmulas automáticas: saldo, estado, intereses |
| CONTROL AHORRO → Columnas de meses (C-AJ) | ✅ SÍ | Se digita el aporte mensual de cada socio |
| CONTROL AHORRO → Columna AK (Total Anual) | 🔴 NO | Suma automática del año |
| AMORTIZACIONES → Toda la hoja | 🔴 NO | Se genera automáticamente desde REGISTRO NUEVO |

---

## 📝 OPERACIÓN 1: REGISTRAR UN CRÉDITO O SOCIO NUEVO

**Regla fundamental:** NUNCA escribir directamente al final de las tablas de FLUJO PRESTAMOS o CONTROL AHORRO. Siempre usar la pestaña **REGISTRO NUEVO**.

### Pasos:

1. **Ir a la pestaña REGISTRO NUEVO** en Google Sheets.

2. **Completar la ficha** (todas las celdas de la columna C):

| Celda | Campo | Ejemplo |
|---|---|---|
| **C4** | Tipo de Registro | `Nuevo Crédito` o `Nuevo Socio` |
| **C6** | Nombre Completo | `MARÍA GONZÁLEZ` (en mayúsculas) |
| **C8** | Tipo de Participante | `socio` o `tercero` |
| **C10** | Monto del Préstamo o Aporte Base | `1000000` |
| **C12** | Tasa de Interés mensual (%) | `2` (para 2% mensual) |
| **C14** | Plazo en meses | `6` |
| **C16** | Fecha de Inicio (formato DD/MM/YYYY) | `05/09/2026` |

3. **Ejecutar el registro** de una de estas dos formas:
   - Hacer clic en el botón **"✅ Registrar Nuevo"** que aparece en la planilla.
   - O ir al menú superior: **⚡ Fondo Vecinos → Registrar Nuevo**.

4. **Resultado automático:**
   - Se crea una nueva fila con ID consecutivo en **FLUJO PRESTAMOS**.
   - Se genera la tabla de amortización con fechas exactas en **AMORTIZACIONES**.
   - Las fórmulas de saldo, estado e intereses quedan configuradas automáticamente.

> **Nota para nuevo Socio:** Si en C4 selecciona "Nuevo Socio", el script además agrega la fila del socio en **CONTROL AHORRO** con el aporte del mes actual ya diligenciado.

---

## 💳 OPERACIÓN 2: REGISTRAR ABONOS DE UN CRÉDITO

Cuando un deudor realiza un pago parcial o total de su préstamo:

1. Ir a la pestaña **FLUJO PRESTAMOS**.
2. Ubicar la fila del participante (se puede usar Ctrl+F para buscar por nombre).
3. Ir a la **Columna J** (llamada "Abonos Iniciales / Abonos Realizados").
4. **Digitar el total acumulado pagado hasta el momento** (no solo el último pago, sino la suma total).

**Ejemplo práctico:**

| Situación | Valor en Columna J |
|---|---|
| Primer pago: $200.000 | `200000` |
| Segundo pago: otros $200.000 | `400000` (suma acumulada) |
| Pago total del saldo | Valor igual al Total a Pagar (col. I) |

**Qué pasa automáticamente:**
- La **Columna K** (Saldo Pendiente) = Total a Pagar − Abonos.
- La **Columna L** (Estado): Permanece en **Activo** (verde) mientras haya saldo. Cambia a **Cancelado** (gris) cuando el saldo llega a ≤ $5.
- La **Columna M** (Intereses Cobrados): Se registra automáticamente cuando el crédito se cancela.

---

## 💰 OPERACIÓN 3: REGISTRAR EL AHORRO MENSUAL DE UN SOCIO

1. Ir a la pestaña **CONTROL AHORRO**.
2. Ubicar la fila del socio (los nombres están en la **Columna A**).
3. Buscar la columna del mes actual (las columnas C a AJ corresponden a los meses del año).
4. **Digitar el monto aportado** por el socio ese mes (ej: `50000`).
5. La columna **AK (Total Anual)** se actualizará automáticamente.

> **Importante:** Si un socio paga doble cuota o paga meses vencidos, digitar el valor correspondiente al mes que está cubriendo, en la columna de ese mes específico.

---

## 🔄 OPERACIÓN 4: LIQUIDAR UN SOCIO RETIRADO

Cuando un socio decide retirarse del fondo:

1. Ir a la pestaña **LIQUIDADOR**.
2. Completar los datos del socio:
   - **C4:** Nombre del socio a liquidar.
   - **C5:** Fecha de la liquidación.
   - **C6:** Motivo del retiro.
3. El LIQUIDADOR calculará automáticamente:
   - Total de aportes a devolver (C11).
   - Utilidad por rifas que corresponde (C12).
   - Intereses ganados proporcionales (C13).
   - Deducciones si aplica (C21).
   - **Neto a pagar al socio retirado (C23)** — este es el valor oficial.
4. Una vez confirmado, ejecutar desde el menú: **⚡ Fondo Vecinos → 🔘 Aplicar Liquidación a Resumen General (C23)**.
5. El sistema pedirá confirmación y luego:
   - Registrará el comprobante en **HISTORIAL LIQUIDACIONES**.
   - Creará/actualizará la fila "LIQUIDACIONES PAGADAS" en **RESUMEN GENERAL**.
   - El total del fondo restará automáticamente el valor liquidado.

---

## 🖥️ EL DASHBOARD WEB: GUÍA DE NAVEGACIÓN COMPLETA

**Enlace:** https://chatbotwap-production-e2a3.up.railway.app/

### Barra Lateral (Menú Principal)

| Elemento | Función |
|---|---|
| **Logo del Fondo** | Identificación visual |
| **🏠 Inicio y Resumen General** | Vista principal con bandeja WhatsApp y balance del fondo |
| **👤 Consulta Individual** | Ficha detallada de un participante específico |
| **Selector de persona** (solo en Consulta Individual) | Desplegable con todos los participantes |
| **📂 Planilla Excel Drive** | Acceso directo a Google Sheets |
| **🔄 Actualizar Datos** | Fuerza la recarga de datos desde la planilla |

---

### PANTALLA 1: 🏠 INICIO Y RESUMEN GENERAL

Esta es la pantalla principal del Dashboard. Tiene dos sub-pestañas:

#### Sub-pestaña: 💬 BANDEJA DE DESPACHO MASIVO WHATSAPP

Permite enviar el estado de cuenta a todos los participantes sin buscarlos uno a uno.

**Cómo usar:**
1. **Filtrar** por categoría (todos, solo socios, con mora, con teléfono, etc.).
2. **Buscar** un participante específico por nombre.
3. Para cada participante se muestra:
   - Nombre, tipo (Socio / Tercero), estado (Al día / Inactivo / Retirado).
   - Teléfono registrado o aviso si no tiene.
   - Total ahorrado y deuda actual.
4. **Botón "📲 Enviar WhatsApp"**: Abre WhatsApp directamente con el mensaje de estado de cuenta ya redactado y listo para enviar.
5. **Botón "👁️ Ver Mensaje"**: Previsualiza el texto del mensaje antes de enviarlo.
6. **Botón "🔍 Ver Ficha"**: Lleva directamente a la Consulta Individual de esa persona.
7. **"📋 Ver y Copiar Todos los Mensajes"**: Muestra todos los mensajes de la lista en un solo bloque (para copiar masivamente).

#### Sub-pestaña: 📊 BALANCE CONSOLIDADO Y MÉTRICAS

Muestra el estado financiero global del fondo.

**Métricas principales (tarjetas superiores):**

| Tarjeta | Qué muestra |
|---|---|
| 🏛️ **Fondo Total Acumulado** | Patrimonio global del fondo |
| 🏦 **Total Ahorros Socios** | Capital aportado por todos los socios |
| 📢 **Capital Prestado** | Dinero actualmente en créditos activos |
| 💵 **Disponible en Banco** | Dinero en cuenta bancaria |
| 📈 **Intereses Cobrados** | Ganancias reales cobradas a deudores |
| 🎟️ **Utilidad Eventos/Rifas** | Ingresos de rifas y eventos |
| 💼 **Caja Efectivo** | Dinero físico disponible |
| 🧾 **Gastos Operativos** | Egresos y costos del fondo |

**Gráfico de torta:** Distribución visual del patrimonio entre capital prestado, banco, gastos y caja.

**Resumen de actividad:**
- Cantidad de préstamos activos y monto total en la calle.
- Conteo de participantes: Al día / Inactivos / Retirados.
- Lista expandible de participantes en mora.

**Botón 📥 Descargar Ficha 2:** Genera y descarga una imagen PNG oficial con el balance general del fondo (ideal para compartir en grupos).

---

### PANTALLA 2: 👤 CONSULTA INDIVIDUAL

Ficha completa de un participante. Se activa seleccionando una persona en el menú lateral.

Tiene dos sub-pestañas:

#### Sub-pestaña: 👤 ANÁLISIS INDIVIDUAL

**Sección de WhatsApp:** Dos opciones para enviar el estado de cuenta:

- **📝 Opción 1 — Enviar como Texto:** Abre WhatsApp con el mensaje de estado de cuenta completo ya escrito.
- **📸 Opción 2 — Enviar Pantallazo (Imagen):**
  1. Descargar la **Ficha PNG** del participante (botón azul).
  2. Abrir WhatsApp (botón verde).
  3. En WhatsApp, adjuntar la imagen descargada desde galería.

**Banner de estado:**
- 🟢 **AL DÍA / ACTIVO:** El participante está al corriente con sus pagos.
- 🔴 **INACTIVO / EN MORA:** Muestra el detalle de qué pagos están pendientes.
- ⚪ **RETIRADO:** El socio ya fue liquidado.

**4 Tarjetas KPI individuales:**

| Tarjeta | Qué muestra |
|---|---|
| 💰 **Total Ahorrado** | Suma de todos los aportes del socio en el año |
| 📅 **Aporte Mensual** | Cuota base mensual de ahorro |
| 💳 **Número de Créditos** | Cantidad de préstamos activos |
| ⚠️ **Saldo Pendiente** | Deuda total actual |

**Historial de Ahorros:** Tabla expandible con el aporte registrado mes a mes y estado (✅ Registrado / ⚪ Pendiente).

**Tabla de Créditos y Amortizaciones:** Para cada crédito del participante:
- Detalles: Monto, cuota mensual, tasa, interés total, saldo pendiente.
- Tabla de amortización completa (Fecha, Cuota, Abono a Capital, Intereses, Saldo).

#### Sub-pestaña: 📊 ESTADO GENERAL DEL FONDO

Muestra el mismo balance consolidado del fondo (idéntico a la sub-pestaña de Inicio).

---

## 📲 CÓMO FUNCIONA EL ENVÍO POR WHATSAPP

El sistema genera automáticamente un mensaje de estado de cuenta con:
- Fecha de corte.
- Nombre, tipo y estado del participante.
- Resumen de ahorros.
- Detalle de cada crédito activo.
- Estado general del fondo.

**Para enviar con número registrado:** El mensaje se abre directamente en el chat del participante.  
**Para enviar sin número registrado:** Se abre WhatsApp para que el administrador elija el contacto manualmente.

> **Para registrar o actualizar teléfonos:** Ir a la pestaña **"whatsapp #"** en Google Sheets. La columna "nombre" debe tener el nombre exacto como aparece en las demás pestañas, y la columna "numero" debe tener el teléfono en formato colombiano de 10 dígitos (ej: `3001234567`).

---

## 🛠️ BOTÓN DE EMERGENCIA: REPARAR FÓRMULAS

Si por error alguien borra o modifica las fórmulas de las columnas K, L o M en FLUJO PRESTAMOS:

1. Ir al menú superior de Google Sheets: **⚡ Fondo Vecinos → Reparar Fórmulas Flujo Préstamos**.
2. El script reconstruirá **instantáneamente** todas las fórmulas de saldos, estados y colores.
3. No se perderá ningún dato previamente ingresado en las columnas editables.

---

## 🔄 ¿CÓMO SE ACTUALIZA EL DASHBOARD?

El Dashboard lee la información directamente de Google Sheets. Tiene un caché de 5 segundos.

**Para forzar la actualización inmediata:**
- Hacer clic en el botón **"🔄 Actualizar Datos"** en la barra lateral del Dashboard.
- Los datos se actualizarán en 1–2 segundos.

---

## 📞 SOPORTE Y CONTACTO

En caso de problemas técnicos con el sistema, contactar al desarrollador.

---

*FONDO DE VECINOS DE LA MESA — Sistema de Gestión Transparente © 2026*
