/**
 * AUTOMATIZACIÓN FONDO DE VECINOS - SCRIPT GOOGLE SHEETS
 * 
 * Novedades:
 * 1. Columna K ("Saldo Pendiente"): Fórmula (=I{fila}-J{fila})
 * 2. Columna L ("Estado del credito"): Fórmula automática (=IF(ISBLANK(A{fila}), "", IF(K{fila}<=5, "Cancelado", "Activo")))
 *    - Si el saldo pendiente es <= $5 pesos (redondeo/centavos), cambia a "Cancelado" y se pinta GRIS (#e2e8f0).
 *    - Si el saldo pendiente es > $5 pesos, se mantiene en "Activo" y se pinta VERDE (#d1fae5).
 * 3. Columna M ("Intereses Cobrados"): Fórmula inteligente
 *    (=IF(OR(REGEXMATCH(UPPER(L{fila}), "CANCEL|PAGAD|FINALIZ"), K{fila}<=5), H{fila}, 0))
 */

/**
 * HELPER PARA OBTENER PESTAÑAS DE FORMA FLEXIBLE (INSENSIBLE A MAYÚSCULAS Y PLURALES)
 */
function getSheetFlexible(ss, targetName) {
  if (!ss) return null;
  var sheets = ss.getSheets();
  var targetUpper = targetName.trim().toUpperCase();
  for (var i = 0; i < sheets.length; i++) {
    var sName = sheets[i].getName().trim().toUpperCase();
    if (sName === targetUpper) return sheets[i];
  }
  for (var i = 0; i < sheets.length; i++) {
    var sName = sheets[i].getName().trim().toUpperCase();
    if (sName.indexOf(targetUpper) !== -1 || targetUpper.indexOf(sName) !== -1) return sheets[i];
  }
  return null;
}

function registrarNuevo() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetForm = getSheetFlexible(ss, "REGISTRO NUEVO");
  
  if (!sheetForm) {
    SpreadsheetApp.getUi().alert("⚠️ Error: No se encontró la pestaña 'REGISTRO NUEVO'.");
    return;
  }
  
  var opcionRaw = sheetForm.getRange("C4").getValue().toString().trim();
  var nombre = sheetForm.getRange("C6").getValue().toString().trim().toUpperCase();
  var tipo = sheetForm.getRange("C8").getValue().toString().trim().toLowerCase();
  
  var monto = parseFloat(sheetForm.getRange("C10").getValue()) || 0;
  var tasaInput = parseFloat(sheetForm.getRange("C12").getValue()) || 0;
  var plazo = parseInt(sheetForm.getRange("C14").getValue()) || 0;
  
  var fechaInicioRaw = sheetForm.getRange("C16").getValue();
  var fechaInicio = parseFechaInicio(fechaInicioRaw);
  
  if (!nombre) {
    SpreadsheetApp.getUi().alert("⚠️ Por favor ingrese el Nombre Completo.");
    return;
  }
  
  var isCredito = (opcionRaw.toLowerCase().indexOf("credito") !== -1 || opcionRaw.toLowerCase().indexOf("crédito") !== -1);
  var isSocioNuevo = (opcionRaw.toLowerCase().indexOf("socio") !== -1);
  
  if (!isCredito && !isSocioNuevo) {
    SpreadsheetApp.getUi().alert("⚠️ Por favor seleccione el Tipo de Registro en C4.");
    return;
  }

  var tasaDecimal = (tasaInput > 1) ? (tasaInput / 100.0) : tasaInput;
  
  var sheetFlujo = getSheetFlexible(ss, "FLUJO PRESTAMOS");
  var sheetAmort = getSheetFlexible(ss, "AMORTIZACIONES");
  var sheetAhorros = getSheetFlexible(ss, "CONTROL AHORRO");
  
  if (isSocioNuevo && sheetAhorros) {
    var targetRow = sheetAhorros.getLastRow() + 1;
    var now = new Date();
    var currentYear = now.getFullYear();
    var currentMonth = now.getMonth(); // 0-indexed (8 = September)
    
    // Buscar la columna del mes actual en la fila 3 de encabezados
    var activeColIdx = 20; // Por defecto Columna T (1-indexed 20, Septiembre)
    try {
      var headers = sheetAhorros.getRange(3, 1, 1, 37).getValues()[0];
      for (var col = 2; col < 36; col++) {
        var hVal = headers[col];
        if (hVal instanceof Date && !isNaN(hVal.getTime())) {
          if (hVal.getFullYear() === currentYear && hVal.getMonth() === currentMonth) {
            activeColIdx = col + 1;
            break;
          }
        }
      }
    } catch (err) {}
    
    var newSocioRow = [];
    newSocioRow.push(nombre); // Col A: Socio
    newSocioRow.push(monto > 0 ? monto : ""); // Col B: Aporte Base
    
    // Col C (3) a Col AJ (36): Meses
    for (var c = 3; c <= 36; c++) {
      if (c === activeColIdx && monto > 0) {
        newSocioRow.push(monto);
      } else {
        newSocioRow.push("");
      }
    }
    
    // Col AK (37): Fórmula Total Anual
    var formulaTotalAnual = "=SUM(C" + targetRow + ":AJ" + targetRow + ")";
    newSocioRow.push(formulaTotalAnual);
    
    sheetAhorros.appendRow(newSocioRow);
  }

  if (isCredito && monto > 0 && plazo > 0) {
    var lastRowFlujo = sheetFlujo.getLastRow();
    var nextId = 1;
    if (lastRowFlujo >= 2) {
      var lastIdVal = sheetFlujo.getRange(lastRowFlujo, 1).getValue();
      nextId = (!isNaN(lastIdVal) && lastIdVal !== "") ? parseInt(lastIdVal) + 1 : lastRowFlujo;
    }
    
    var cuotaFija = (tasaDecimal > 0) ? (monto * tasaDecimal) / (1 - Math.pow(1 + tasaDecimal, -plazo)) : (monto / plazo);
    cuotaFija = Math.round(cuotaFija * 100) / 100;
    
    var totalAPagar = Math.round((cuotaFija * plazo) * 100) / 100;
    var totalInteres = Math.round((totalAPagar - monto) * 100) / 100;
    var abonosIniciales = 0;
    
    var targetRow = lastRowFlujo + 1;
    
    var formulaSaldoPendiente = "=I" + targetRow + "-J" + targetRow;
    var formulaEstadoCredito  = '=IF(ISBLANK(A' + targetRow + '), "", IF(K' + targetRow + '<=5, "Cancelado", "Activo"))';
    var condCancel = 'REGEXMATCH(UPPER(L' + targetRow + '), "CANCEL|PAGAD|FINALIZ")';
    var condSaldoK = 'AND(ISNUMBER(K' + targetRow + '), K' + targetRow + '<=5)';
    var formulaInteresCobrado = '=IF(ISBLANK(A' + targetRow + '), "", IF(OR(' + condCancel + ', ' + condSaldoK + '), H' + targetRow + ', 0))';
    
    var nuevaFilaFlujo = [
      nextId, nombre, tipo, monto, tasaDecimal, plazo,
      cuotaFija, totalInteres, totalAPagar, abonosIniciales,
      formulaSaldoPendiente, formulaEstadoCredito, formulaInteresCobrado
    ];
    
    sheetFlujo.appendRow(nuevaFilaFlujo);
    
    if (sheetAmort) {
      var lastRowAmort = sheetAmort.getLastRow();
      if (lastRowAmort > 1) {
        sheetAmort.appendRow([" ", " ", " ", " ", " "]);
        var blankRowIdx = sheetAmort.getLastRow();
        sheetAmort.getRange(blankRowIdx, 1, 1, 5).clearFormat().setBackground(null).setFontColor("#ffffff");
      }
      
      var startRowHeader = sheetAmort.getLastRow() + 1;
      var headerNombre = "# " + nextId + " - " + nombre + " (" + tipo.toUpperCase() + ")";
      sheetAmort.appendRow([headerNombre, "CUOTA", "ABONO A K", "INTERESES", "SALDO"]);
      
      var fechaDesembolsoStr = formatDateDDMMYYYY(fechaInicio);
      sheetAmort.appendRow([fechaDesembolsoStr, 0, 0, 0, totalAPagar]);
      
      var saldoActual = totalAPagar;
      var abonoCapitalBase = Math.round((monto / plazo) * 100) / 100;
      var interesBase = Math.round((totalInteres / plazo) * 100) / 100;
      
      for (var i = 1; i <= plazo; i++) {
        var fechaCuotaStr = getPaymentDate(fechaInicio, i);
        var abonoK = (i === plazo) ? Math.round((monto - (abonoCapitalBase * (plazo - 1))) * 100) / 100 : abonoCapitalBase;
        var intCuota = (i === plazo) ? Math.round((totalInteres - (interesBase * (plazo - 1))) * 100) / 100 : interesBase;
        saldoActual = (i === plazo) ? 0 : Math.round((saldoActual - cuotaFija) * 100) / 100;
        
        sheetAmort.appendRow([fechaCuotaStr, cuotaFija, abonoK, intCuota, Math.max(0, saldoActual)]);
      }
      
      var endRowTable = sheetAmort.getLastRow();
      var numTableRows = endRowTable - startRowHeader + 1;
      
      var headerRange = sheetAmort.getRange(startRowHeader, 1, 1, 5);
      headerRange.setBackground("#1e3a8a").setFontColor("#ffffff").setFontWeight("bold").setHorizontalAlignment("center");
      
      var dataRange = sheetAmort.getRange(startRowHeader + 1, 1, numTableRows - 1, 5);
      dataRange.setFontColor("#000000").setFontFamily("Roboto");
      sheetAmort.getRange(startRowHeader + 1, 1, numTableRows - 1, 1).setHorizontalAlignment("left");
      sheetAmort.getRange(startRowHeader + 1, 2, numTableRows - 1, 4).setHorizontalAlignment("right");
      
      sheetAmort.getRange(startRowHeader + 1, 1, 1, 5).setBackground("#e6f4ea").setFontWeight("bold");
      sheetAmort.setColumnWidth(1, 145);
      sheetAmort.setColumnWidth(2, 125);
      sheetAmort.setColumnWidth(3, 125);
      sheetAmort.setColumnWidth(4, 125);
      sheetAmort.setColumnWidth(5, 135);
    }
  }
  
  colorearFlujoPrestamos();
  
  SpreadsheetApp.getUi().alert("✅ ¡Registro completado con éxito!\n\nParticipante: " + nombre);
  sheetForm.getRange("C6").setValue("");
  sheetForm.getRange("C10").setValue("");
  sheetForm.getRange("C14").setValue("");
  sheetForm.getRange("C16").setValue("");
}

/**
 * COLOREAR ÚNICAMENTE LA COLUMNA L (ESTADO DEL CRÉDITO)
 */
function colorearFlujoPrestamos() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetFlujo = getSheetFlexible(ss, "FLUJO PRESTAMOS");
  if (!sheetFlujo) return;
  
  var ids = sheetFlujo.getRange("A2:A").getValues();
  var count = 0;
  for (var i = 0; i < ids.length; i++) {
    if (ids[i][0] !== "" && ids[i][0] !== null) count++;
    else break;
  }
  if (count === 0) return;
  
  var rangeColL = sheetFlujo.getRange(2, 12, count, 1);
  var valuesColL = rangeColL.getValues();
  var saldoValues = sheetFlujo.getRange(2, 11, count, 1).getValues();
  
  var backgroundColors = [];
  var fontColors = [];
  
  for (var i = 0; i < count; i++) {
    var estadoRaw = String(valuesColL[i][0] || "").toUpperCase().trim();
    var saldo = parseFloat(saldoValues[i][0]) || 0;
    
    if (
      estadoRaw.indexOf("CANCEL") !== -1 || 
      estadoRaw.indexOf("PAGAD") !== -1 || 
      estadoRaw.indexOf("FINALIZ") !== -1 || 
      (saldo <= 5 && estadoRaw.indexOf("ACTIVO") === -1)
    ) {
      backgroundColors.push(["#e2e8f0"]);
      fontColors.push(["#475569"]);
    } else if (estadoRaw.indexOf("MORA") !== -1 || estadoRaw.indexOf("INACTIV") !== -1) {
      backgroundColors.push(["#fee2e2"]);
      fontColors.push(["#991b1b"]);
    } else {
      backgroundColors.push(["#d1fae5"]);
      fontColors.push(["#065f46"]);
    }
  }
  
  rangeColL.setBackgrounds(backgroundColors);
  rangeColL.setFontColors(fontColors);
  rangeColL.setFontWeight("bold");
  rangeColL.setHorizontalAlignment("center");
}

/**
 * REPARAR TODAS LAS FÓRMULAS EN BLOQUE (COLUMNAS K, L Y M)
 */
function repararTodasLasFormulas() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetFlujo = getSheetFlexible(ss, "FLUJO PRESTAMOS");
  if (!sheetFlujo) return;
  
  var ids = sheetFlujo.getRange("A2:A").getValues();
  var count = 0;
  for (var i = 0; i < ids.length; i++) {
    if (ids[i][0] !== "" && ids[i][0] !== null) count++;
    else break;
  }
  if (count === 0) return;
  
  var formulasK = [];
  var formulasL = [];
  var formulasM = [];
  
  for (var i = 0; i < count; i++) {
    var r = i + 2;
    formulasK.push(["=I" + r + "-J" + r]);
    formulasL.push(['=IF(ISBLANK(A' + r + '), "", IF(K' + r + '<=5, "Cancelado", "Activo"))']);
    var condCancel = 'REGEXMATCH(UPPER(L' + r + '), "CANCEL|PAGAD|FINALIZ")';
    var condSaldoK = 'AND(ISNUMBER(K' + r + '), K' + r + '<=5)';
    var formulaM = '=IF(ISBLANK(A' + r + '), "", IF(OR(' + condCancel + ', ' + condSaldoK + '), H' + r + ', 0))';
    formulasM.push([formulaM]);
  }
  
  sheetFlujo.getRange(2, 11, count, 1).setFormulas(formulasK);
  sheetFlujo.getRange(2, 12, count, 1).setFormulas(formulasL);
  sheetFlujo.getRange(2, 13, count, 1).setFormulas(formulasM);
  
  colorearFlujoPrestamos();
  SpreadsheetApp.getUi().alert("✅ ¡Se actualizaron " + count + " registros en instantáneo!");
}

function onEdit(e) {
  if (!e || !e.range) return;
  var sheet = e.range.getSheet();
  if (sheet.getName() === "Flujo prestamos") {
    colorearFlujoPrestamos();
  }
}

function getSafeTimeZone() {
  try {
    var ssTz = SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone();
    if (typeof ssTz === "string" && ssTz.trim().length > 0) return ssTz.trim();
  } catch (e) {}
  try {
    var scriptTz = Session.getScriptTimeZone();
    if (typeof scriptTz === "string" && scriptTz.trim().length > 0) return scriptTz.trim();
  } catch (e) {}
  return "America/Bogota";
}

function parseFechaInicio(val) {
  var tz = getSafeTimeZone();
  if (val instanceof Date && !isNaN(val.getTime())) {
    var strDate = Utilities.formatDate(val, tz, "dd/MM/yyyy");
    var p = strDate.split("/");
    return new Date(parseInt(p[2], 10), parseInt(p[1], 10) - 1, parseInt(p[0], 10), 12, 0, 0);
  }
  if (typeof val === "string" && val.trim() !== "") {
    var parts = val.trim().split(/[\/\-\.]/);
    if (parts.length === 3) {
      if (parts[0].length <= 2 && parts[2].length === 4) {
        return new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10), 12, 0, 0);
      }
      if (parts[0].length === 4) {
        return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10), 12, 0, 0);
      }
    }
  }
  var now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12, 0, 0);
}

function getPaymentDate(startDate, monthOffset) {
  var year = startDate.getFullYear();
  var month = startDate.getMonth() + monthOffset;
  var originalDay = startDate.getDate();
  var d = new Date(year, month, originalDay, 12, 0, 0);
  if (d.getDate() !== originalDay) d.setDate(0);
  return formatDateDDMMYYYY(d);
}

function formatDateDDMMYYYY(d) {
  var tz = getSafeTimeZone();
  return Utilities.formatDate(d, tz, "dd/MM/yyyy");
}

/**
 * MENÚ PERSONALIZADO EN GOOGLE SHEETS
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu("⚡ Fondo Vecinos")
    .addItem("🔘 Aplicar Liquidación a Resumen General (C23)", "aplicarLiquidacionAResumen")
    .addSeparator()
    .addItem("Configurar Fila de Liquidaciones en RESUMEN GENERAL", "configurarFilaLiquidacionesManual")
    .addItem("Reparar Fórmulas Flujo Préstamos", "repararTodasLasFormulas")
    .addToUi();
}

/**
 * CREAR O ACTUALIZAR AUTOMÁTICAMENTE LA PESTAÑA 'LIQUIDADOR'
 */
function crearPestanaLiquidador() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetLiquidador = getSheetFlexible(ss, "LIQUIDADOR");
  
  if (sheetLiquidador) {
    var ui = SpreadsheetApp.getUi();
    var resp = ui.alert(
      "⚠️ Atención",
      "La pestaña 'LIQUIDADOR' ya existe en tu hoja de cálculo.\n\n¿Deseas restablecerla con la plantilla predeterminada? (Esto reemplazará los cálculos manuales actuales de esa pestaña).",
      ui.ButtonSet.YES_NO
    );
    if (resp !== ui.Button.YES) return;
  } else {
    sheetLiquidador = ss.insertSheet("LIQUIDADOR");
  }
  
  // Asegurar que la hoja tenga al menos 23 filas
  var maxRowsLiq = sheetLiquidador.getMaxRows();
  if (maxRowsLiq < 23) {
    sheetLiquidador.insertRowsAfter(maxRowsLiq, 23 - maxRowsLiq);
  }
  
  // Limpiar contenido previo para reconstruir ordenadamente
  sheetLiquidador.clear();
  
  // Anchos de columna
  sheetLiquidador.setColumnWidth(1, 35);  // Col A: margen
  sheetLiquidador.setColumnWidth(2, 340); // Col B: concepto
  sheetLiquidador.setColumnWidth(3, 210); // Col C: valor / entrada
  sheetLiquidador.setColumnWidth(4, 300); // Col D: notas / guía
  
  // Fila 2: Título Principal
  sheetLiquidador.getRange("B2:D2").merge();
  sheetLiquidador.getRange("B2").setValue("FONDO DE VECINOS - LIQUIDACIÓN DE SOCIO (RETIRO)");
  sheetLiquidador.getRange("B2:D2")
    .setBackground("#1e3a8a")
    .setFontColor("#ffffff")
    .setFontWeight("bold")
    .setFontSize(13)
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  sheetLiquidador.setRowHeight(2, 40);
  
  // Fila 3: Sección 1 - Datos Básicos
  sheetLiquidador.getRange("B3:D3").merge();
  sheetLiquidador.getRange("B3").setValue("1. DATOS DEL PARTICIPANTE");
  sheetLiquidador.getRange("B3:D3")
    .setBackground("#e2e8f0")
    .setFontColor("#1e293b")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("left");
  sheetLiquidador.setRowHeight(3, 26);
  
  // Fila 4: Nombre del Socio
  sheetLiquidador.getRange("B4").setValue("Nombre del Socio a Retirar:").setFontWeight("bold");
  sheetLiquidador.getRange("D4").setValue("👈 Seleccione el socio de la lista desplegable").setFontColor("#64748b").setFontStyle("italic");
  
  // Validación de datos en C4 (Lista desplegable con los socios de CONTROL AHORRO)
  var sheetAhorros = getSheetFlexible(ss, "CONTROL AHORRO");
  if (sheetAhorros) {
    var lastRowAhorros = sheetAhorros.getLastRow();
    if (lastRowAhorros >= 5) {
      var rule = SpreadsheetApp.newDataValidation()
        .requireValueInRange(sheetAhorros.getRange("A5:A" + lastRowAhorros), true)
        .setAllowInvalid(true)
        .build();
      sheetLiquidador.getRange("C4").setDataValidation(rule);
    }
    var primerSocio = sheetAhorros.getRange("A5").getValue();
    if (primerSocio) sheetLiquidador.getRange("C4").setValue(primerSocio);
  }
  
  // Fila 5: Fecha de Liquidación
  sheetLiquidador.getRange("B5").setValue("Fecha de Liquidación:").setFontWeight("bold");
  sheetLiquidador.getRange("C5").setFormula("=TODAY()");
  sheetLiquidador.getRange("C5").setNumberFormat("dd/MM/yyyy");
  sheetLiquidador.getRange("D5").setValue("Fecha actual (se actualiza automáticamente)").setFontColor("#64748b").setFontStyle("italic");
  
  // Fila 6: Motivo del Retiro
  var celdaB6 = sheetLiquidador.getRange("B6");
  celdaB6.setValue("Motivo del Retiro:");
  celdaB6.setFontWeight("bold");
  sheetLiquidador.getRange("C6").setValue("Retiro voluntario");
  var celdaD6 = sheetLiquidador.getRange("D6");
  celdaD6.setValue("Texto explicativo libre");
  celdaD6.setFontColor("#64748b");
  celdaD6.setFontStyle("italic");
  
  // Fila 7: Prorrateo Rifas y Eventos
  var celdaB7 = sheetLiquidador.getRange("B7");
  celdaB7.setValue("Cant. Socios Rifas y Eventos:");
  celdaB7.setFontWeight("bold");
  sheetLiquidador.getRange("C7").setValue(19);
  sheetLiquidador.getRange("C7").setNumberFormat("#,##0");
  var celdaD7 = sheetLiquidador.getRange("D7");
  celdaD7.setValue("Ajustar segun socios en rifas");
  celdaD7.setFontColor("#64748b");
  celdaD7.setFontStyle("italic");
  
  // Fila 8: Prorrateo Intereses Ganados
  var celdaB8 = sheetLiquidador.getRange("B8");
  celdaB8.setValue("Cant. Socios Intereses Ganados:");
  celdaB8.setFontWeight("bold");
  sheetLiquidador.getRange("C8").setValue(19);
  sheetLiquidador.getRange("C8").setNumberFormat("#,##0");
  var celdaD8 = sheetLiquidador.getRange("D8");
  celdaD8.setValue("Ajustar segun socios con intereses");
  celdaD8.setFontColor("#64748b");
  celdaD8.setFontStyle("italic");
  
  // Resaltar celdas de entrada del usuario (C4 a C8) en amarillo suave
  sheetLiquidador.getRange("C4:C8").setBackground("#fef9c3");
  
  // Fila 10: Sección 2 - Conceptos a Favor
  sheetLiquidador.getRange("B10:D10").merge();
  sheetLiquidador.getRange("B10").setValue("2. CONCEPTOS A FAVOR DEL SOCIO (+)");
  sheetLiquidador.getRange("B10:D10")
    .setBackground("#e2e8f0")
    .setFontColor("#1e293b")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("left");
  sheetLiquidador.setRowHeight(10, 26);
  
  // Fila 11: Total Aportes a la Fecha
  sheetLiquidador.getRange("B11").setValue("Total Aportes a la Fecha (Ahorros):");
  sheetLiquidador.getRange("C11").setFormula("=IF(ISBLANK(C4), 0, IFERROR(XLOOKUP(C4, 'CONTROL AHORRO'!A5:A, 'CONTROL AHORRO'!AK5:AK, 0), 0))");
  sheetLiquidador.getRange("D11").setValue("Suma de aportes en CONTROL AHORRO (Col AK)").setFontColor("#64748b").setFontStyle("italic");
  
  // Fila 12: Utilidad por Rifas y Eventos (Prorrateado con C7)
  sheetLiquidador.getRange("B12").setValue("Utilidad por Rifas y Eventos:");
  sheetLiquidador.getRange("C12").setFormula("=IF(OR(ISBLANK(C7), C7=0), 0, 'RESUMEN GENERAL'!C7 / C7)");
  sheetLiquidador.getRange("D12").setValue("RESUMEN GENERAL C7 dividido en participantes de rifas (C7)").setFontColor("#64748b").setFontStyle("italic");
  
  // Fila 13: Intereses Ganados (Cobrados) (Prorrateado con C8)
  sheetLiquidador.getRange("B13").setValue("Intereses Ganados (Cobrados):");
  sheetLiquidador.getRange("C13").setFormula("=IF(OR(ISBLANK(C8), C8=0), 0, 'RESUMEN GENERAL'!C6 / C8)");
  sheetLiquidador.getRange("D13").setValue("RESUMEN GENERAL C6 dividido en participantes de intereses (C8)").setFontColor("#64748b").setFontStyle("italic");
  
  // Fila 14: Subtotal a Favor
  sheetLiquidador.getRange("B14").setValue("SUBTOTAL A FAVOR:").setFontWeight("bold");
  sheetLiquidador.getRange("C14").setFormula("=SUM(C11:C13)").setFontWeight("bold");
  sheetLiquidador.getRange("B14:C14").setBackground("#f1f5f9");
  
  // Fila 16: Sección 3 - Deducciones
  sheetLiquidador.getRange("B16:D16").merge();
  sheetLiquidador.getRange("B16").setValue("3. DEDUCCIONES Y GASTOS COMPARTIDOS (-)");
  sheetLiquidador.getRange("B16:D16")
    .setBackground("#e2e8f0")
    .setFontColor("#1e293b")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("left");
  sheetLiquidador.setRowHeight(16, 26);
  
  // Filas 17-20: Descuentos
  sheetLiquidador.getRange("B17").setValue("Placa Conmemorativa Fondo:");
  sheetLiquidador.getRange("C17").setValue(0).setBackground("#fef9c3");
  sheetLiquidador.getRange("D17").setValue("Valor a descontar (manual)").setFontColor("#64748b").setFontStyle("italic");
  
  sheetLiquidador.getRange("B18").setValue("Almuerzo Socios:");
  sheetLiquidador.getRange("C18").setValue(0).setBackground("#fef9c3");
  sheetLiquidador.getRange("D18").setValue("Valor a descontar (manual)").setFontColor("#64748b").setFontStyle("italic");
  
  sheetLiquidador.getRange("B19").setValue("Colilla Préstamos:");
  sheetLiquidador.getRange("C19").setValue(0).setBackground("#fef9c3");
  sheetLiquidador.getRange("D19").setValue("Saldo pendiente / gastos colilla (manual)").setFontColor("#64748b").setFontStyle("italic");
  
  sheetLiquidador.getRange("B20").setValue("Otros Descuentos:");
  sheetLiquidador.getRange("C20").setValue(0).setBackground("#fef9c3");
  sheetLiquidador.getRange("D20").setValue("Cualquier otro concepto a descontar").setFontColor("#64748b").setFontStyle("italic");
  
  // Fila 21: Subtotal Deducciones
  sheetLiquidador.getRange("B21").setValue("TOTAL DEDUCCIONES:").setFontWeight("bold");
  sheetLiquidador.getRange("C21").setFormula("=SUM(C17:C20)").setFontWeight("bold");
  sheetLiquidador.getRange("B21:C21").setBackground("#f1f5f9");
  
  // Fila 23: TOTAL A FAVOR
  sheetLiquidador.getRange("B23").setValue("TOTAL A FAVOR (VALOR NETO A LIQUIDAR):").setFontWeight("bold").setFontSize(12);
  sheetLiquidador.getRange("C23").setFormula("=C14 - C21").setFontWeight("bold").setFontSize(12);
  sheetLiquidador.getRange("D23").setValue("Total neto a pagar al socio saliente").setFontWeight("bold").setFontColor("#065f46");
  sheetLiquidador.getRange("B23:D23").setBackground("#d1fae5").setFontColor("#065f46");
  sheetLiquidador.setRowHeight(23, 36);
  
  // Formato de moneda para valores monetarios
  var currencyRanges = ["C11", "C12", "C13", "C14", "C17", "C18", "C19", "C20", "C21", "C23"];
  for (var i = 0; i < currencyRanges.length; i++) {
    sheetLiquidador.getRange(currencyRanges[i]).setNumberFormat("$#,##0");
  }
  
  // Bordes finos y alineaciones
  sheetLiquidador.getRange("B4:D8").setBorder(true, true, true, true, true, true, "#cbd5e1", SpreadsheetApp.BorderStyle.SOLID);
  sheetLiquidador.getRange("B11:D14").setBorder(true, true, true, true, true, true, "#cbd5e1", SpreadsheetApp.BorderStyle.SOLID);
  sheetLiquidador.getRange("B17:D21").setBorder(true, true, true, true, true, true, "#cbd5e1", SpreadsheetApp.BorderStyle.SOLID);
  sheetLiquidador.getRange("B23:D23").setBorder(true, true, true, true, true, true, "#059669", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  
  sheetLiquidador.getRange("B4:B23").setHorizontalAlignment("left");
  sheetLiquidador.getRange("C4:C23").setHorizontalAlignment("right");
  sheetLiquidador.getRange("D4:D23").setHorizontalAlignment("left");
  sheetLiquidador.getRange("C4:C6").setHorizontalAlignment("left");
  
  // Asegurar también la fila de liquidación en RESUMEN GENERAL y la pestaña de HISTORIAL
  asegurarHistorialLiquidaciones(ss);
  asegurarFilaLiquidacionesEnResumen(ss);

  SpreadsheetApp.getUi().alert("Pestañas LIQUIDADOR, HISTORIAL y RESUMEN GENERAL configuradas con éxito.");
}

/**
 * ASEGURA QUE EXISTA LA PESTAÑA 'HISTORIAL LIQUIDACIONES'
 */
function asegurarHistorialLiquidaciones(ss) {
  var sheetHistorial = getSheetFlexible(ss, "HISTORIAL LIQUIDACIONES");
  if (!sheetHistorial) {
    sheetHistorial = ss.insertSheet("HISTORIAL LIQUIDACIONES");
    sheetHistorial.setTabColor("#dc2626");
    
    var headers = [
      "Fecha Liquidación",
      "Socio Retirado",
      "Motivo",
      "Aportes Devueltos",
      "Utilidad Rifas",
      "Intereses Ganados",
      "Total Deducciones",
      "Neto Pagado (Salida)",
      "Fecha Registro"
    ];
    
    sheetHistorial.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheetHistorial.getRange(1, 1, 1, headers.length)
      .setBackground("#1e293b")
      .setFontColor("#ffffff")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    sheetHistorial.setRowHeight(1, 32);
    
    sheetHistorial.setColumnWidth(1, 130);
    sheetHistorial.setColumnWidth(2, 220);
    sheetHistorial.setColumnWidth(3, 200);
    sheetHistorial.setColumnWidth(4, 140);
    sheetHistorial.setColumnWidth(5, 130);
    sheetHistorial.setColumnWidth(6, 140);
    sheetHistorial.setColumnWidth(7, 140);
    sheetHistorial.setColumnWidth(8, 160);
    sheetHistorial.setColumnWidth(9, 160);
    
    sheetHistorial.setFrozenRows(1);
  }
  return sheetHistorial;
}

/**
 * ASEGURA QUE EXISTA LA FILA 'LIQUIDACIONES PAGADAS' EN 'RESUMEN GENERAL'
 * Se posiciona exactamente después de 'CAJA EFECTIVO' y antes de 'TOTAL'.
 */
function asegurarFilaLiquidacionesEnResumen(ss) {
  var sheetResumen = getSheetFlexible(ss, "RESUMEN GENERAL");
  if (!sheetResumen) return null;
  
  var lastRow = sheetResumen.getLastRow();
  if (lastRow < 1) return null;
  var values = sheetResumen.getRange("B1:B" + lastRow).getValues();
  
  var filaCaja = -1;
  var filaLiq = -1;
  var filaTotal = -1;
  var filaBanco = -1;
  
  for (var i = 0; i < values.length; i++) {
    var val = (values[i][0] || "").toString().trim().toUpperCase();
    if (val.indexOf("EN BANCO") !== -1) filaBanco = i + 1;
    if (val.indexOf("CAJA EFECTIVO") !== -1) filaCaja = i + 1;
    if (val.indexOf("LIQUIDACI") !== -1) filaLiq = i + 1;
    if (val === "TOTAL") filaTotal = i + 1;
  }
  
  // Si la fila ya existe
  if (filaLiq !== -1) {
    sheetResumen.getRange("C" + filaLiq).setFormula("=IFERROR(SUM('HISTORIAL LIQUIDACIONES'!H2:H), 0)");
    sheetResumen.getRange("C" + filaLiq).setNumberFormat("$#,##0");
    if (filaTotal !== -1 && filaBanco !== -1 && filaCaja !== -1) {
      sheetResumen.getRange("C" + filaTotal).setFormula("=C" + filaBanco + "-C" + filaCaja + "-C" + filaLiq);
    }
    return filaLiq;
  }
  
  // Si no existe, determinar posición (justo antes de TOTAL o después de CAJA EFECTIVO)
  var insertAt = (filaTotal !== -1) ? filaTotal : ((filaCaja !== -1) ? filaCaja + 1 : 13);
  sheetResumen.insertRowBefore(insertAt);
  
  // Actualizar referencias tras la inserción
  filaBanco = (filaBanco >= insertAt) ? filaBanco + 1 : filaBanco;
  filaCaja = (filaCaja >= insertAt) ? filaCaja + 1 : filaCaja;
  var nuevaFilaTotal = insertAt + 1;
  
  // Configurar celda de liquidaciones
  sheetResumen.getRange("B" + insertAt).setValue("LIQUIDACIONES PAGADAS (SOCIOS RETIRADOS)")
    .setFontWeight("bold")
    .setFontColor("#991b1b");
  sheetResumen.getRange("C" + insertAt).setFormula("=IFERROR(SUM('HISTORIAL LIQUIDACIONES'!H2:H), 0)")
    .setNumberFormat("$#,##0")
    .setFontWeight("bold")
    .setBackground("#fee2e2")
    .setFontColor("#991b1b");
    
  // Configurar celda de TOTAL
  if (filaBanco === -1) filaBanco = insertAt - 2;
  if (filaCaja === -1) filaCaja = insertAt - 1;
  sheetResumen.getRange("B" + nuevaFilaTotal).setValue("TOTAL").setFontWeight("bold");
  sheetResumen.getRange("C" + nuevaFilaTotal).setFormula("=C" + filaBanco + "-C" + filaCaja + "-C" + insertAt)
    .setNumberFormat("$#,##0")
    .setFontWeight("bold");
    
  // Bordes
  sheetResumen.getRange("B" + insertAt + ":C" + nuevaFilaTotal).setBorder(true, true, true, true, true, true, "#cbd5e1", SpreadsheetApp.BorderStyle.SOLID);
  
  return insertAt;
}

/**
 * MENÚ: CONFIGURAR MANUALMENTE LA FILA DE LIQUIDACIONES EN RESUMEN GENERAL
 */
function configurarFilaLiquidacionesManual() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  asegurarHistorialLiquidaciones(ss);
  asegurarFilaLiquidacionesEnResumen(ss);
  SpreadsheetApp.getUi().alert("Configuración Exitosa", "La fila de 'LIQUIDACIONES PAGADAS' en RESUMEN GENERAL y la pestaña 'HISTORIAL LIQUIDACIONES' han sido verificadas y configuradas correctamente.", SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * APLICAR LIQUIDACIÓN AL RESUMEN GENERAL (BOTÓN EN PESTAÑA LIQUIDADOR)
 * 
 * 1. Toma exclusivamente el valor neto a liquidar de la celda C23 de LIQUIDADOR.
 * 2. Lee los datos informativos del socio (C4, C5, C6) para el comprobante.
 * 3. Solicita confirmación en pantalla antes de proceder.
 * 4. Guarda el comprobante contable en la pestaña 'HISTORIAL LIQUIDACIONES'.
 * 5. Crea o actualiza la fila de descuento en 'RESUMEN GENERAL' (debajo de CAJA EFECTIVO y antes del TOTAL).
 * 6. NO altera los nombres ni las fórmulas en CONTROL AHORRO, WHATSAPP ni en el LIQUIDADOR.
 */
function aplicarLiquidacionAResumen() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ui = SpreadsheetApp.getUi();
  
  var sheetLiq = getSheetFlexible(ss, "LIQUIDADOR");
  if (!sheetLiq) {
    ui.alert("⚠️ Error", "No se encontró la pestaña 'LIQUIDADOR'. Por favor verifique el nombre de la hoja.", ui.ButtonSet.OK);
    return;
  }
  
  // 1. Obtener y validar el valor neto a liquidar de la celda C23
  var valNetoRaw = sheetLiq.getRange("C23").getValue();
  var netoPagar = parseFloat(valNetoRaw);
  
  if (isNaN(netoPagar) || netoPagar <= 0) {
    ui.alert(
      "⚠️ Celda C23 Vacía o en Cero",
      "El valor neto a liquidar en la celda C23 es $0 o no contiene un valor numérico válido.\n\n" +
      "Por favor defina la liquidación del socio en la pestaña LIQUIDADOR antes de presionar el botón.",
      ui.ButtonSet.OK
    );
    return;
  }
  
  // 2. Datos informativos adicionales (para el comprobante e historial)
  var socioNombre = (sheetLiq.getRange("C4").getValue() || "").toString().trim();
  if (!socioNombre) socioNombre = "SOCIO NO ESPECIFICADO";
  
  var fechaLiqVal = sheetLiq.getRange("C5").getValue();
  var fechaLiqStr = "";
  if (fechaLiqVal instanceof Date && !isNaN(fechaLiqVal.getTime())) {
    fechaLiqStr = formatDateDDMMYYYY(fechaLiqVal);
  } else if (fechaLiqVal) {
    fechaLiqStr = fechaLiqVal.toString().trim();
  } else {
    fechaLiqStr = formatDateDDMMYYYY(new Date());
  }
  
  var motivo = (sheetLiq.getRange("C6").getValue() || "").toString().trim() || "Retiro voluntario / Liquidación";
  var totalAportes = parseFloat(sheetLiq.getRange("C11").getValue()) || 0;
  var utilRifas = parseFloat(sheetLiq.getRange("C12").getValue()) || 0;
  var intGanados = parseFloat(sheetLiq.getRange("C13").getValue()) || 0;
  var totalDeducciones = parseFloat(sheetLiq.getRange("C21").getValue()) || 0;
  
  var formattedNeto = Utilities.formatNumber(netoPagar, "es_CO", "$#,##0");
  
  // 3. Confirmación previa en pantalla
  var mensajeConfirmacion = "¿Desea aplicar y descontar esta liquidación en el Fondo?\n\n" +
    "👤 Socio: " + socioNombre + "\n" +
    "📅 Fecha: " + fechaLiqStr + "\n" +
    "📝 Motivo: " + motivo + "\n" +
    "💵 VALOR NETO A DESCONTAR (C23): " + formattedNeto + "\n\n" +
    "Efectos al confirmar:\n" +
    "• Se archivará el comprobante en 'HISTORIAL LIQUIDACIONES'.\n" +
    "• Se creará / actualizará la celda en 'RESUMEN GENERAL' debajo de 'CAJA EFECTIVO'.\n" +
    "• El Total del Fondo restará este valor automáticamente.\n" +
    "• Tus tablas de CONTROL AHORRO y préstamos no se modificarán.";
    
  var respuesta = ui.alert("🔘 Confirmar Aplicación de Liquidación", mensajeConfirmacion, ui.ButtonSet.YES_NO);
  if (respuesta !== ui.Button.YES) {
    ui.alert("Operación Cancelada", "No se realizó ninguna modificación.", ui.ButtonSet.OK);
    return;
  }
  
  // 4. Registrar en HISTORIAL LIQUIDACIONES
  var sheetHistorial = asegurarHistorialLiquidaciones(ss);
  var nextRowHistorial = sheetHistorial.getLastRow() + 1;
  var ahoraStr = Utilities.formatDate(new Date(), getSafeTimeZone(), "dd/MM/yyyy HH:mm:ss");
  
  sheetHistorial.getRange(nextRowHistorial, 1, 1, 9).setValues([[
    fechaLiqStr,
    socioNombre.toUpperCase(),
    motivo,
    totalAportes,
    utilRifas,
    intGanados,
    totalDeducciones,
    netoPagar,
    ahoraStr
  ]]);
  
  sheetHistorial.getRange(nextRowHistorial, 4, 1, 5).setNumberFormat("$#,##0");
  sheetHistorial.getRange(nextRowHistorial, 1, 1, 9).setHorizontalAlignment("left");
  sheetHistorial.getRange(nextRowHistorial, 4, 1, 5).setHorizontalAlignment("right");
  sheetHistorial.getRange(nextRowHistorial, 8).setFontWeight("bold").setFontColor("#991b1b");
  
  // 5. Asegurar y sincronizar fila en RESUMEN GENERAL (debajo de CAJA EFECTIVO y antes de TOTAL)
  asegurarFilaLiquidacionesEnResumen(ss);
  
  // 6. Mensaje de éxito
  var resumenExito = "✅ ¡Liquidación aplicada con éxito!\n\n" +
    "• Socio: " + socioNombre.toUpperCase() + "\n" +
    "• Monto Neto Liquidado: " + formattedNeto + "\n" +
    "• Se descontó en 'RESUMEN GENERAL' debajo de 'CAJA EFECTIVO'.\n" +
    "• El comprobante quedó registrado en 'HISTORIAL LIQUIDACIONES'.";
    
  ui.alert("Liquidación Aplicada", resumenExito, ui.ButtonSet.OK);
}

/**
 * ALIAS PARA COMPATIBILIDAD CON BOTONES PREVIOS O MENÚ
 */
function procesarLiquidacion() {
  aplicarLiquidacionAResumen();
}
