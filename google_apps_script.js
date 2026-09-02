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
    var newSocioRow = [nombre];
    for (var m = 0; m < 16; m++) newSocioRow.push("");
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
    var formulaInteresCobrado = '=IF(ISBLANK(A' + targetRow + '), "", IF(OR(REGEXMATCH(UPPER(L' + targetRow + '), "CANCEL|PAGAD|FINALIZ"), AND(ISNUMBER(K' + targetRow + '), K' + targetRow + '<=5)), H' + targetRow + ', 0))';
    
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
      var headerNombre = "# - " + nombre + " (" + tipo.toUpperCase() + ")";
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
    var formulaM = '=IF(ISBLANK(A' + r + '), "", IF(OR(REGEXMATCH(UPPER(L' + r + '), "CANCEL|PAGAD|FINALIZ"), AND(ISNUMBER(K' + r + '), K' + r + '<=5)), H' + r + ', 0))';
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
