import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import datetime
import urllib.parse
import urllib.request
import io
from PIL import Image, ImageDraw, ImageFont

# Load local logo image for favicon and sidebar
try:
    logo_img = Image.open("logo.png")
except Exception:
    logo_img = "💰"

def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

logo_b64 = get_logo_base64()
logo_img_html = f"<img src='data:image/png;base64,{logo_b64}' style='height: 48px; width: auto; object-fit: contain; margin-right: 12px; border-radius: 6px;' />" if logo_b64 else ""

def generate_individual_card_png(selected_person, user_type_label, user_status_eval, total_savings, base_savings, active_loans_count, total_loan_balance, user_loans):
    width = 900
    base_height = 340
    loan_extra = len(user_loans) * 75 if user_loans else 0
    height = base_height + loan_extra
    
    img = Image.new("RGB", (width, height), color=(15, 23, 42)) # #0f172a
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([15, 15, width - 15, height - 15], fill=(30, 41, 59), outline=(51, 65, 85), width=2)
    
    try:
        logo = Image.open("logo.png").convert("RGBA")
        logo = logo.resize((55, 55))
        img.paste(logo, (35, 30), logo)
    except Exception:
        pass

    font_main = ImageFont.load_default()
    
    draw.text((105, 30), "FONDO DE VECINOS - GESTION TRANSPARENTE", fill=(255, 255, 255), font=font_main)
    draw.text((105, 48), f"Ficha de Resumen Individual: {selected_person}", fill=(147, 197, 253), font=font_main)
    draw.text((105, 66), f"Tipo: {user_type_label}  |  Fecha: {datetime.date.today().strftime('%d/%m/%Y')}", fill=(203, 213, 225), font=font_main)
    
    status_str = "AL DIA" if user_status_eval['overall_status'] == 'AL_DIA' else ("RETIRADO" if user_status_eval['overall_status'] == 'RETIRADO' else "INACTIVO / MORA")
    banner_bg = (6, 95, 70) if user_status_eval['overall_status'] == 'AL_DIA' else ((71, 85, 105) if user_status_eval['overall_status'] == 'RETIRADO' else (153, 27, 27))
    draw.rectangle([35, 95, width - 35, 128], fill=banner_bg)
    draw.text((48, 105), f"ESTADO DEL PARTICIPANTE: {status_str}", fill=(255, 255, 255), font=font_main)
    
    # 1. Total Ahorrado
    draw.rectangle([35, 142, 230, 222], fill=(15, 23, 42), outline=(16, 185, 129), width=2)
    draw.text((45, 152), "Total Ahorrado", fill=(148, 163, 184), font=font_main)
    sav_str = fmt_money(total_savings) if total_savings > 0 else "N/A"
    draw.text((45, 182), sav_str, fill=(52, 211, 153), font=font_main)
    
    # 2. Aporte Mensual
    draw.rectangle([250, 142, 440, 222], fill=(15, 23, 42), outline=(59, 130, 246), width=2)
    draw.text((260, 152), "Aporte Mensual", fill=(148, 163, 184), font=font_main)
    base_str = fmt_money(base_savings) if total_savings > 0 else "N/A"
    draw.text((260, 182), base_str, fill=(96, 165, 250), font=font_main)

    # 3. Creditos Activos
    draw.rectangle([460, 142, 650, 222], fill=(15, 23, 42), outline=(245, 158, 11), width=2)
    draw.text((470, 152), "Creditos Activos", fill=(148, 163, 184), font=font_main)
    draw.text((470, 182), str(active_loans_count), fill=(251, 191, 36), font=font_main)

    # 4. Saldo Pendiente
    draw.rectangle([670, 142, 865, 222], fill=(15, 23, 42), outline=(239, 68, 68), width=2)
    draw.text((680, 152), "Saldo Pendiente", fill=(148, 163, 184), font=font_main)
    draw.text((680, 182), fmt_money(total_loan_balance, show_decimals=True), fill=(248, 113, 113), font=font_main)

    y_cursor = 240
    if user_loans:
        draw.text((35, y_cursor), "DETALLE DE CREDITOS:", fill=(255, 255, 255), font=font_main)
        y_cursor += 22
        for i, l in enumerate(user_loans):
            loan_id = l.get('ID', '')
            monto = float(l.get('Monto', 0)) if pd.notna(l.get('Monto')) else 0.0
            saldo = float(l.get('Saldo Pendiente', 0)) if pd.notna(l.get('Saldo Pendiente')) else 0.0
            cuota_val = float(l.get('Cuota Fija', l.get('Cuota', 0))) if pd.notna(l.get('Cuota Fija', l.get('Cuota'))) else 0.0
            tasa_raw = l.get('Tasa (%)', l.get('Tasa', 0))
            if pd.notna(tasa_raw):
                try:
                    t_num = float(tasa_raw)
                    tasa_val = t_num * 100 if t_num < 1 else t_num
                except (ValueError, TypeError):
                    tasa_val = 0.0
            else:
                tasa_val = 0.0
            estado = l.get('Estado del credito', l.get('Estado', 'Activo'))
            
            draw.rectangle([35, y_cursor, width - 35, y_cursor + 62], fill=(15, 23, 42), outline=(71, 85, 105), width=1)
            draw.text((48, y_cursor + 10), f"Credito #{loan_id} - Estado: {estado}", fill=(251, 191, 36), font=font_main)
            line2 = f"Monto: {fmt_money(monto)} | Cuota Mensual: {fmt_money(cuota_val, show_decimals=True)} | Tasa: {tasa_val:g}% | Saldo: {fmt_money(saldo, show_decimals=True)}"
            draw.text((48, y_cursor + 32), line2, fill=(226, 232, 240), font=font_main)
            y_cursor += 72

    draw.text((35, height - 32), "Fondo de Vecinos - Reporte Oficial Generado Automáticamente", fill=(100, 116, 139), font=font_main)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_fund_card_png(fondo_total_val, tot_ahorros_val, cap_prestado_val, disponible_banco_val, int_ganados_val, util_eventos_val, caja_efectivo_val, gastos_op_val):
    width = 900
    height = 330
    
    img = Image.new("RGB", (width, height), color=(15, 23, 42)) # #0f172a
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([15, 15, width - 15, height - 15], fill=(30, 41, 59), outline=(51, 65, 85), width=2)
    
    try:
        logo = Image.open("logo.png").convert("RGBA")
        logo = logo.resize((55, 55))
        img.paste(logo, (35, 30), logo)
    except Exception:
        pass

    font_main = ImageFont.load_default()
    
    draw.text((105, 30), "FONDO DE VECINOS - GESTION TRANSPARENTE", fill=(255, 255, 255), font=font_main)
    draw.text((105, 48), "Ficha de Estado General Consolidado del Fondo", fill=(147, 197, 253), font=font_main)
    draw.text((105, 66), f"Fecha de emision: {datetime.date.today().strftime('%d/%m/%Y')}", fill=(203, 213, 225), font=font_main)
    
    # 1. Fondo Total
    draw.rectangle([35, 95, 230, 175], fill=(15, 23, 42), outline=(168, 85, 247), width=2)
    draw.text((45, 105), "Fondo Total Acumulado", fill=(148, 163, 184), font=font_main)
    draw.text((45, 135), fmt_money(fondo_total_val, show_decimals=True), fill=(192, 132, 252), font=font_main)

    # 2. Total Ahorros
    draw.rectangle([250, 95, 440, 175], fill=(15, 23, 42), outline=(16, 185, 129), width=2)
    draw.text((260, 105), "Total Ahorros Socios", fill=(148, 163, 184), font=font_main)
    draw.text((260, 135), fmt_money(tot_ahorros_val), fill=(52, 211, 153), font=font_main)

    # 3. Capital Prestado
    draw.rectangle([460, 95, 650, 175], fill=(15, 23, 42), outline=(239, 68, 68), width=2)
    draw.text((470, 105), "Capital Prestado", fill=(148, 163, 184), font=font_main)
    draw.text((470, 135), fmt_money(cap_prestado_val, show_decimals=True), fill=(248, 113, 113), font=font_main)

    # 4. Disponible en Banco
    draw.rectangle([670, 95, 865, 175], fill=(15, 23, 42), outline=(59, 130, 246), width=2)
    draw.text((680, 105), "Disponible en Banco", fill=(148, 163, 184), font=font_main)
    draw.text((680, 135), fmt_money(disponible_banco_val, show_decimals=True), fill=(96, 165, 250), font=font_main)

    # 5. Intereses Cobrados
    draw.rectangle([35, 190, 230, 270], fill=(15, 23, 42), outline=(71, 85, 105), width=1)
    draw.text((45, 200), "Intereses Cobrados", fill=(148, 163, 184), font=font_main)
    draw.text((45, 230), fmt_money(int_ganados_val, show_decimals=True), fill=(52, 211, 153), font=font_main)

    # 6. Eventos / Rifas
    draw.rectangle([250, 190, 440, 270], fill=(15, 23, 42), outline=(71, 85, 105), width=1)
    draw.text((260, 200), "Utilidad Eventos/Rifas", fill=(148, 163, 184), font=font_main)
    draw.text((260, 230), fmt_money(util_eventos_val, show_decimals=True), fill=(96, 165, 250), font=font_main)

    # 7. Caja Efectivo
    draw.rectangle([460, 190, 650, 270], fill=(15, 23, 42), outline=(71, 85, 105), width=1)
    draw.text((470, 200), "Caja Efectivo", fill=(148, 163, 184), font=font_main)
    draw.text((470, 230), fmt_money(caja_efectivo_val, show_decimals=True), fill=(203, 213, 225), font=font_main)

    # 8. Gastos Operativos
    draw.rectangle([670, 190, 865, 270], fill=(15, 23, 42), outline=(71, 85, 105), width=1)
    draw.text((680, 200), "Gastos Operativos", fill=(148, 163, 184), font=font_main)
    draw.text((680, 230), fmt_money(gastos_op_val, show_decimals=True), fill=(248, 113, 113), font=font_main)

    draw.text((35, height - 32), "Fondo de Vecinos - Balance General de Patrimonio", fill=(100, 116, 139), font=font_main)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# Set page config for maximum legibility and mobile responsiveness
st.set_page_config(
    page_title="Fondo de Vecinos - Dashboard",
    page_icon=logo_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high contrast, high legibility for adults, glassmorphism & mobile screenshot optimization
st.markdown("""
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Main background */
    .stApp {
        background-color: #0b1329;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111c38;
        border-right: 1px solid #1e293b;
    }
    
    /* Main Headers */
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Target container for Mobile Screenshot / Ficha Resumen */
    .screenshot-card {
        background: linear-gradient(145deg, #132247 0%, #1a2c5b 100%);
        border: 2px solid #3b82f6;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        margin-bottom: 25px;
    }
    
    .screenshot-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.15);
        padding-bottom: 14px;
        margin-bottom: 18px;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .screenshot-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
    }

    /* Summary Card Cards - High Legibility for Older Adults */
    .summary-card {
        background: #162447;
        border: 1px solid #2a3e6e;
        border-radius: 16px;
        padding: 18px 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        margin-bottom: 12px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .summary-card:hover {
        transform: translateY(-2px);
        border-color: #60a5fa;
    }

    .summary-card-green {
        border-top: 5px solid #10b981;
        background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, #162447 100%);
    }

    .summary-card-blue {
        border-top: 5px solid #3b82f6;
        background: linear-gradient(180deg, rgba(59, 130, 246, 0.08) 0%, #162447 100%);
    }

    .summary-card-purple {
        border-top: 5px solid #8b5cf6;
        background: linear-gradient(180deg, rgba(139, 92, 246, 0.08) 0%, #162447 100%);
    }

    .summary-card-red {
        border-top: 5px solid #f43f5e;
        background: linear-gradient(180deg, rgba(244, 63, 94, 0.08) 0%, #162447 100%);
    }

    .card-icon {
        font-size: 1.6rem;
        margin-bottom: 4px;
        display: block;
    }

    .card-label {
        color: #94a3b8;
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }

    .card-value {
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 4px;
    }

    .val-green { color: #34d399; }
    .val-blue { color: #60a5fa; }
    .val-purple { color: #a78bfa; }
    .val-red { color: #fb7185; }
    .val-gray { color: #cbd5e1; }

    .card-subtext {
        font-size: 0.82rem;
        color: #cbd5e1;
        font-weight: 500;
        margin: 0;
    }

    /* Badges */
    .badge-socio {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
    }
    
    .badge-tercero {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: #ffffff;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        display: inline-block;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
    }
    
    .badge-status-activo {
        background-color: rgba(16, 185, 129, 0.25);
        color: #34d399;
        border: 1.5px solid #10b981;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 800;
    }

    .badge-status-cancelado {
        background-color: rgba(148, 163, 184, 0.2);
        color: #94a3b8;
        border: 1.5px solid #94a3b8;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 800;
    }

    .badge-status-inactivo {
        background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%);
        color: #ffffff;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
        display: inline-block;
    }

    .badge-status-aldia {
        background: linear-gradient(135deg, #065f46 0%, #10b981 100%);
        color: #ffffff;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
        display: inline-block;
    }

    /* Section titles */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-top: 22px;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 2px solid #2a3e6e;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Alert / Notice box */
    .alert-card {
        background: rgba(30, 58, 110, 0.4);
        border-left: 4px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 6px 12px 12px 6px;
        margin: 14px 0;
        color: #e2e8f0;
        font-weight: 500;
        font-size: 0.95rem;
    }

    .alert-card-danger {
        background: linear-gradient(135deg, rgba(153, 27, 27, 0.35) 0%, rgba(220, 38, 38, 0.2) 100%);
        border-left: 5px solid #ef4444;
        border-top: 1px solid rgba(239, 68, 68, 0.3);
        border-right: 1px solid rgba(239, 68, 68, 0.3);
        border-bottom: 1px solid rgba(239, 68, 68, 0.3);
        padding: 18px 20px;
        border-radius: 12px;
        margin: 16px 0 22px 0;
        color: #fecdd3;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.25);
    }

    .alert-card-success {
        background: linear-gradient(135deg, rgba(6, 95, 70, 0.35) 0%, rgba(16, 185, 129, 0.2) 100%);
        border-left: 5px solid #10b981;
        border-top: 1px solid rgba(16, 185, 129, 0.3);
        border-right: 1px solid rgba(16, 185, 129, 0.3);
        border-bottom: 1px solid rgba(16, 185, 129, 0.3);
        padding: 16px 20px;
        border-radius: 12px;
        margin: 16px 0 22px 0;
        color: #a7f3d0;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2);
    }

    .alert-card-info {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(59, 130, 246, 0.2) 100%);
        border-left: 5px solid #3b82f6;
        border-top: 1px solid rgba(59, 130, 246, 0.3);
        border-right: 1px solid rgba(59, 130, 246, 0.3);
        border-bottom: 1px solid rgba(59, 130, 246, 0.3);
        padding: 16px 20px;
        border-radius: 12px;
        margin: 16px 0 22px 0;
        color: #bfdbfe;
    }

    /* Enhanced Amortization Table Styling */
    .amort-table-wrapper {
        overflow-x: auto;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.14);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.35);
        margin: 14px 0 22px 0;
        background: rgba(15, 23, 42, 0.6);
    }

    .custom-amort-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.93rem;
        color: #f1f5f9;
        text-align: right;
    }

    .custom-amort-table th {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: #ffffff;
        font-weight: 700;
        padding: 12px 14px;
        text-transform: uppercase;
        font-size: 0.82rem;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #3b82f6;
    }

    .custom-amort-table th:first-child, .custom-amort-table td:first-child {
        text-align: left;
        font-weight: 600;
    }

    .custom-amort-table td {
        padding: 10px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }

    .custom-amort-table tbody tr:nth-child(even) {
        background: rgba(30, 41, 59, 0.45);
    }

    .custom-amort-table tbody tr:nth-child(odd) {
        background: rgba(15, 23, 42, 0.45);
    }

    .custom-amort-table tbody tr:hover {
        background: rgba(59, 130, 246, 0.18);
    }

    .custom-amort-table tr.row-desembolso {
        background: rgba(16, 185, 129, 0.18) !important;
        font-weight: 700;
        color: #6ee7b7;
    }

    /* Mobile media query tweaks for WhatsApp screenshot sharing */
    @media (max-width: 768px) {
        .screenshot-card {
            padding: 16px;
            border-width: 1px;
            margin-bottom: 15px;
        }
        
        .screenshot-title {
            font-size: 1.25rem;
        }
        
        .card-value {
            font-size: 1.55rem;
        }

        .card-label {
            font-size: 0.85rem;
        }

        .card-subtext {
            font-size: 0.78rem;
        }

        .summary-card {
            padding: 14px 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Google Sheet Export Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZL5aORQJ7C00YgpMUOfoXyKYtMkB2PRfbKUNrCGQPMc/export?format=xlsx"

# Helper for Colombian COP Currency Formatting (Clear for older adults)
def fmt_money(val, show_decimals=False):
    if pd.isna(val) or val is None:
        return "$ 0"
    try:
        v = float(val)
        if show_decimals:
            formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"$ {formatted}"
        else:
            formatted = f"{v:,.0f}".replace(",", ".")
            return f"$ {formatted}"
    except Exception:
        return str(val)

# Name Normalization Function
def normalize_name(name):
    if not name or pd.isna(name):
        return ""
    n = str(name).upper().strip()
    n = re.sub(r'\s*\d+$', '', n)         # Remove trailing digits
    n = re.sub(r'\s+[A-Z]\.?$', '', n)     # Remove trailing single letter
    n = " ".join(n.split())                # Remove extra internal spaces
    
    # Manual maps for spelling variations
    if "JUN" in n and "BAQUERO" in n:
        return "JUAN C BAQUERO"
    if "ANDRES" in n and "HERNAND" in n:
        return "ANDRES HERNANDEZ"
    if "ORLANDO" in n and "TORRE" in n:
        return "ORLANDO TORRES"
    if "YULI" in n and "MENDEZ" in n:
        return "YULI MENDEZ PINILLA"
    return n

spanish_months_map = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

def get_column_display_name(col):
    if isinstance(col, (pd.Timestamp, datetime.datetime)):
        m_name = spanish_months_map.get(col.month, str(col.month))
        return f"{m_name} {col.year}"
    col_str = str(col).strip()
    if col_str.endswith('.1'):
        base_name = col_str[:-2]
        return f"{base_name} 2026"
    return col_str

# Helper to reliably parse metrics from Resumen General sheet
def parse_fund_metrics(df_resumen):
    resumen_dict = {}
    if df_resumen is not None and not df_resumen.empty:
        for r_idx in range(len(df_resumen)):
            concept = str(df_resumen.iloc[r_idx, 1]).strip()
            val = df_resumen.iloc[r_idx, 2]
            if pd.notna(val) and concept and concept.lower() not in ["nan", "concepto", "none", ""]:
                try:
                    resumen_dict[concept] = float(val)
                except (ValueError, TypeError):
                    pass

    def get_resumen_val(keywords, default=0.0):
        for k, v in resumen_dict.items():
            k_lower = k.lower().strip()
            if any(kw in k_lower for kw in keywords):
                return v
        return default

    tot_ahorros_val = get_resumen_val(['ahorro', 'ahorros'], 0.0)
    int_ganados_val = get_resumen_val(['intereses ganados', 'intereses cobrados'], 0.0)
    util_eventos_val = get_resumen_val(['eventos', 'rifas'], 0.0)
    fondo_total_val = get_resumen_val(['fondo total'], tot_ahorros_val + int_ganados_val + util_eventos_val)
    cap_prestado_val = get_resumen_val(['capital prestado', 'en calle'], 0.0)
    gastos_op_val = get_resumen_val(['gastos operativos'], 0.0)
    disponible_banco_val = get_resumen_val(['en banco', 'bancos', 'banco'], 0.0)
    caja_efectivo_val = get_resumen_val(['caja efectivo', 'caja'], 0.0)

    return {
        'tot_ahorros_val': tot_ahorros_val,
        'int_ganados_val': int_ganados_val,
        'util_eventos_val': util_eventos_val,
        'fondo_total_val': fondo_total_val,
        'cap_prestado_val': cap_prestado_val,
        'gastos_op_val': gastos_op_val,
        'disponible_banco_val': disponible_banco_val,
        'caja_efectivo_val': caja_efectivo_val
    }

# Helper to evaluate participant activity status (Avisos de inactividad / Mora)
def evaluate_participant_status(person_name, df_ahorros, df_flujo):
    norm = normalize_name(person_name)
    socio_rows = df_ahorros[df_ahorros['NormalizedSocio'] == norm] if 'NormalizedSocio' in df_ahorros.columns else df_ahorros[df_ahorros['Socio'].apply(normalize_name) == norm]
    is_socio = len(socio_rows) > 0
    loans = df_flujo[df_flujo['NormalizedNombre'] == norm].to_dict('records') if 'NormalizedNombre' in df_flujo.columns else df_flujo[df_flujo['Nombre'].apply(normalize_name) == norm].to_dict('records')
    
    ignore_cols = ['Socio', 'Aporte Base', 'Total Anual', 'NormalizedSocio']
    month_cols = [c for c in df_ahorros.columns if c not in ignore_cols and not str(c).startswith('Unnamed:')]
    
    # Calcular el índice del mes activo más reciente con pagos en la planilla
    max_paid_idx = -1
    for idx_m, m in enumerate(month_cols):
        col_vals = df_ahorros[m]
        has_any = any(pd.notna(v) and str(v).strip() not in ['', '0', '0.0', ' '] and float(v) > 0 for v in col_vals if pd.notna(v) and str(v).strip().replace('.', '').isdigit())
        if has_any:
            max_paid_idx = idx_m

    ahorro_status = 'AL_DIA'
    ahorro_reasons = []
    
    if is_socio:
        r = socio_rows.iloc[0]
        notes = str(r.get('Unnamed: 20', '')).lower() + " " + str(r.get('Unnamed: 21', '')).lower()
        if 'retiro' in notes:
            ahorro_status = 'RETIRADO'
            ahorro_reasons.append("Socio retirado oficialmente del Fondo de Vecinos.")
        else:
            last_paid_label = None
            last_paid_idx = -1
            
            for idx_m, m in enumerate(month_cols):
                v = r.get(m, 0)
                if pd.notna(v) and str(v).strip() not in ['', '0', '0.0', ' ']:
                    try:
                        if float(v) > 0:
                            last_paid_label = get_column_display_name(m)
                            last_paid_idx = idx_m
                    except ValueError:
                        pass
            
            if last_paid_idx < max_paid_idx - 1:
                ahorro_status = 'INACTIVO'
                if last_paid_label:
                    ahorro_reasons.append(f"Dejó de aportar su cuota mensual de ahorro (Último aporte registrado: <b>{last_paid_label}</b>).")
                else:
                    ahorro_reasons.append("No registra ningún aporte de ahorro realizado en las planillas.")
    else:
        ahorro_status = 'N_A'

    loan_status = 'AL_DIA'
    loan_reasons = []
    
    for l in loans:
        st_loan = str(l.get('Estado del credito', l.get('Estado', ''))).upper()
        if 'MORA' in st_loan or 'INACTIVO' in st_loan:
            monto = float(l.get('Monto', 0)) if pd.notna(l.get('Monto')) else 0.0
            loan_id = l.get('ID', '')
            loan_status = 'INACTIVO'
            loan_reasons.append(f"Crédito <b>ID #{loan_id}</b> ({fmt_money(monto)}) registra estado de mora en planillas.")

    is_inactive = (ahorro_status == 'INACTIVO') or (loan_status == 'INACTIVO')
    
    if ahorro_status == 'RETIRADO':
        overall_status_label = "RETIRADO"
        overall_badge = "<span class='badge-status-cancelado'>⚪ SOCIO RETIRADO</span>"
    elif is_inactive:
        overall_status_label = "INACTIVO"
        badge_text = "🔴 PARTICIPANTE INACTIVO"
        if ahorro_status == 'INACTIVO' and loan_status == 'INACTIVO':
            badge_text = "🔴 INACTIVO (AHORRO Y CRÉDITO)"
        elif ahorro_status == 'INACTIVO':
            badge_text = "🔴 INACTIVO (MORA APORTES)"
        elif loan_status == 'INACTIVO':
            badge_text = "🔴 INACTIVO (MORA CRÉDITO)"
        overall_badge = f"<span class='badge-status-inactivo'>{badge_text}</span>"
    else:
        overall_status_label = "AL_DIA"
        overall_badge = "<span class='badge-status-aldia'>🟢 AL DÍA / ACTIVO</span>"

    return {
        'overall_status': overall_status_label,
        'overall_badge': overall_badge,
        'is_inactive': is_inactive,
        'ahorro_status': ahorro_status,
        'ahorro_reasons': ahorro_reasons,
        'loan_status': loan_status,
        'loan_reasons': loan_reasons
    }

# Helper to flexibly find exact sheet name in Excel workbook (case-insensitive & whitespace tolerant)
def find_sheet_name(excel_file, target_names):
    available = excel_file.sheet_names
    # 1. Exact match case-insensitive
    for target in target_names:
        target_clean = target.strip().upper()
        for s in available:
            if s.strip().upper() == target_clean:
                return s
    # 2. Substring / partial match case-insensitive
    for target in target_names:
        target_clean = target.strip().upper()
        for s in available:
            s_clean = s.strip().upper()
            if target_clean in s_clean or s_clean in target_clean:
                return s
    raise ValueError(f"No se encontró la pestaña {target_names} en el archivo Excel. Hojas disponibles: {available}")

# Helper function to parse amortization schedules
@st.cache_data(ttl=30)
def parse_amortization_tables(_url_or_excel):
    if isinstance(_url_or_excel, pd.ExcelFile):
        excel_file = _url_or_excel
    else:
        req = urllib.request.Request(_url_or_excel, headers={'User-Agent': 'Mozilla/5.0'})
        content = urllib.request.urlopen(req).read()
        excel_file = pd.ExcelFile(io.BytesIO(content))
        
    sheet_name = find_sheet_name(excel_file, ['AMORTIZACIONES', 'Amortizaciones'])
    df = excel_file.parse(sheet_name, header=None)
    tables = {}
    loan_idx = 1
    r = 0
    num_rows = len(df)
    
    while r < num_rows:
        val_0 = df.iloc[r, 0]
        val_str = str(val_0).strip().upper() if not pd.isna(val_0) else ""
        if val_str in ['#', 'FECHA / #', 'FECHA'] or val_str.startswith('#') or 'NOMBRE:' in val_str:
            r_init = r + 1
            init_bal = df.iloc[r_init, 4] if r_init < num_rows else 0.0
            init_fecha_col0 = df.iloc[r_init, 0] if r_init < num_rows else ""
            
            # Try extracting name or ID from header
            clean_name = re.sub(r'[\#\-\d]|(\(CRÉDITO\))|(\(SOCIO\))|(\(CREDITO\))', '', val_str, flags=re.IGNORECASE).strip().upper()
            match_id = re.search(r'#\s*(\d+)', val_str)
            extracted_id = int(match_id.group(1)) if match_id else None
            
            payments = []
            r_pay = r + 2
            cuota_counter = 1
            while r_pay < num_rows:
                p_col0 = df.iloc[r_pay, 0]
                val_cuota = df.iloc[r_pay, 1]
                
                if pd.isna(val_cuota) or str(val_cuota).strip() == '':
                    break
                
                if isinstance(p_col0, (pd.Timestamp, datetime.datetime)):
                    label_col0 = p_col0.strftime('%d/%m/%Y')
                elif not pd.isna(p_col0) and str(p_col0).strip() != '':
                    label_col0 = str(p_col0).strip()
                    if label_col0.endswith('.0'):
                        label_col0 = label_col0[:-2]
                else:
                    label_col0 = f"Cuota {cuota_counter}"
                
                try:
                    v_cuota = float(val_cuota)
                except (ValueError, TypeError):
                    v_cuota = 0.0
                    
                try:
                    v_abono = float(df.iloc[r_pay, 2])
                except (ValueError, TypeError):
                    v_abono = 0.0
                    
                try:
                    v_int = float(df.iloc[r_pay, 3])
                except (ValueError, TypeError):
                    v_int = 0.0
                    
                try:
                    v_saldo = float(df.iloc[r_pay, 4])
                except (ValueError, TypeError):
                    v_saldo = 0.0

                payments.append({
                    'Cuota / Fecha': label_col0,
                    'Valor Cuota': v_cuota,
                    'Abono a Capital': v_abono,
                    'Intereses': v_int,
                    'Saldo Pendiente': v_saldo
                })
                cuota_counter += 1
                r_pay += 1
                
            total_interest = None
            if r_pay < num_rows:
                interest_val = df.iloc[r_pay, 3]
                if not pd.isna(interest_val):
                    try:
                        total_interest = float(interest_val)
                    except ValueError:
                        pass
            
            df_table = pd.DataFrame(payments)
            init_label = "0 (Inicio)"
            if isinstance(init_fecha_col0, (pd.Timestamp, datetime.datetime)):
                init_label = init_fecha_col0.strftime('%d/%m/%Y')
            elif not pd.isna(init_fecha_col0) and str(init_fecha_col0).strip() != '':
                init_label = str(init_fecha_col0).strip()
                if init_label.endswith('.0'): init_label = init_label[:-2]

            try:
                init_bal_float = float(init_bal) if not pd.isna(init_bal) else 0.0
            except (ValueError, TypeError):
                init_bal_float = 0.0

            init_row = pd.DataFrame([{
                'Cuota / Fecha': init_label,
                'Valor Cuota': np.nan,
                'Abono a Capital': np.nan,
                'Intereses': np.nan,
                'Saldo Pendiente': init_bal_float
            }])
            df_table = pd.concat([init_row, df_table], ignore_index=True)
            
            table_entry = {
                'initial_balance': init_bal_float,
                'total_interest_calculated': total_interest,
                'schedule': df_table
            }
            
            tables[loan_idx] = table_entry
            if extracted_id is not None:
                tables[extracted_id] = table_entry
            if clean_name:
                tables[clean_name] = table_entry
            
            loan_idx += 1
            r = r_pay
        else:
            r += 1
            
    return tables

# Helper functions for WhatsApp Integration
def clean_phone(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    s = re.sub(r'\D', '', s)
    if not s:
        return None
    if len(s) == 10 and s.startswith('3'):
        s = '57' + s
    return s

def get_phone_for_person(person_name, df_whatsapp):
    if df_whatsapp is None or df_whatsapp.empty:
        return None
    norm = normalize_name(person_name)
    match = df_whatsapp[df_whatsapp['NormalizedNombre'] == norm]
    if not match.empty:
        val = match.iloc[0].get('numero')
        return clean_phone(val)
    return None

def generate_whatsapp_message(selected_person, user_type_label, user_status_eval, total_savings, base_savings, active_loans_count, total_loan_balance, user_loans, df_resumen, df_ahorros, df_flujo):
    status_str = "🟢 AL DÍA" if user_status_eval['overall_status'] == 'AL_DIA' else ("⚪ RETIRADO" if user_status_eval['overall_status'] == 'RETIRADO' else "🔴 INACTIVO / MORA")
    today_str = datetime.date.today().strftime('%d/%m/%Y')
    
    # Calculate general fund metrics
    metrics = parse_fund_metrics(df_resumen)
    tot_ahorros_val = metrics['tot_ahorros_val']
    fondo_total_val = metrics['fondo_total_val']
    cap_prestado_val = metrics['cap_prestado_val']

    msg = f"📅 *Fecha:* {today_str}\n"
    msg += f"-----------------------------------------\n"
    msg += f"👤 *Participante:* {selected_person}\n"
    msg += f"🏷️ *Tipo:* {user_type_label}\n"
    msg += f"📊 *Estado:* {status_str}\n\n"
    
    msg += f"💵 *RESUMEN INDIVIDUAL:*\n"
    if total_savings > 0:
        msg += f"• Total Ahorrado: {fmt_money(total_savings)}\n"
        msg += f"• Aporte Mensual: {fmt_money(base_savings)}\n"
    else:
        msg += f"• Ahorro Registrado: N/A\n"
        
    msg += f"• Créditos Activos: {active_loans_count}\n"
    msg += f"• Saldo Pendiente Total: {fmt_money(total_loan_balance, show_decimals=True)}\n"
    
    if user_loans:
        msg += f"\n📋 *DETALLE DE CRÉDITOS:*\n"
        for i, l in enumerate(user_loans):
            loan_id = l.get('ID', '')
            monto = float(l.get('Monto', 0)) if pd.notna(l.get('Monto')) else 0.0
            saldo = float(l.get('Saldo Pendiente', 0)) if pd.notna(l.get('Saldo Pendiente')) else 0.0
            cuota_val = float(l.get('Cuota Fija', l.get('Cuota', 0))) if pd.notna(l.get('Cuota Fija', l.get('Cuota'))) else 0.0
            
            tasa_raw = l.get('Tasa (%)', l.get('Tasa', 0))
            if pd.notna(tasa_raw):
                try:
                    t_num = float(tasa_raw)
                    tasa_val = t_num * 100 if t_num < 1 else t_num
                except (ValueError, TypeError):
                    tasa_val = 0.0
            else:
                tasa_val = 0.0
                
            estado = l.get('Estado del credito', l.get('Estado', 'Activo'))
            tasa_str = f"{tasa_val:g}%"
            msg += f" 🔹 *Crédito {i+1} (ID #{loan_id})*\n"
            msg += f"    - Monto Inicial: {fmt_money(monto)}\n"
            msg += f"    - Cuota Fija Mensual: {fmt_money(cuota_val, show_decimals=True)}\n"
            msg += f"    - Tasa Interés: {tasa_str}\n"
            msg += f"    - Saldo Pendiente: {fmt_money(saldo, show_decimals=True)}\n"
            msg += f"    - Estado: {estado}\n"

    msg += f"\n📊 *ESTADO GENERAL DEL FONDO:*\n"
    msg += f"• Fondo Total Acumulado: {fmt_money(fondo_total_val, show_decimals=True)}\n"
    msg += f"• Total Ahorro Socios: {fmt_money(tot_ahorros_val)}\n"
    msg += f"• Capital en Créditos Activos: {fmt_money(cap_prestado_val, show_decimals=True)}\n"

    msg += f"\n-----------------------------------------\n"
    msg += f"_Fondo de Vecinos - Gestión Transparente_"
    return msg

# Load Data from Google Sheet
@st.cache_data(ttl=60)
def load_data(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urllib.request.urlopen(req).read()
    excel_file = pd.ExcelFile(io.BytesIO(content))
    
    resumen_sheet = find_sheet_name(excel_file, ['Resumen General', 'RESUMEN GENERAL'])
    df_resumen = excel_file.parse(resumen_sheet)
    
    ahorros_sheet = find_sheet_name(excel_file, ['Control Ahorros', 'CONTROL AHORRO', 'CONTROL AHORROS'])
    df_ahorros_raw = excel_file.parse(ahorros_sheet, skiprows=3)
    
    df_ahorros = df_ahorros_raw[
        df_ahorros_raw['Socio'].notna() & 
        (df_ahorros_raw['Socio'].astype(str).str.strip() != '') & 
        (~df_ahorros_raw['Socio'].astype(str).str.upper().str.contains('TOTAL'))
    ].copy()
        
    df_ahorros['Socio'] = df_ahorros['Socio'].astype(str).str.strip()
    df_ahorros['NormalizedSocio'] = df_ahorros['Socio'].apply(normalize_name)
    
    flujo_sheet = find_sheet_name(excel_file, ['Flujo prestamos', 'FLUJO PRESTAMOS', 'FLUJO PRESTAMO'])
    df_flujo = excel_file.parse(flujo_sheet)
    df_flujo = df_flujo.dropna(subset=['Nombre']).copy()
    df_flujo['Nombre'] = df_flujo['Nombre'].astype(str).str.strip()
    df_flujo['NormalizedNombre'] = df_flujo['Nombre'].apply(normalize_name)
    df_flujo['Tipo'] = df_flujo['Tipo'].astype(str).str.lower().str.strip()
    
    for col in df_flujo.columns:
        if 'ESTADO' in str(col).upper():
            df_flujo['Estado'] = df_flujo[col]
            break
    if 'Estado' not in df_flujo.columns:
        df_flujo['Estado'] = 'Activo'
        
    # Auto-correct tiny floating point residual balances (<= 5.0 COP)
    if 'Saldo Pendiente' in df_flujo.columns:
        saldos_num = pd.to_numeric(df_flujo['Saldo Pendiente'], errors='coerce').fillna(0)
        df_flujo.loc[saldos_num <= 5.0, 'Estado'] = 'Cancelado'
        if 'Estado del credito' in df_flujo.columns:
            df_flujo.loc[saldos_num <= 5.0, 'Estado del credito'] = 'Cancelado'
    
    # Try reading whatsapp sheet
    df_whatsapp = pd.DataFrame()
    for s_name in ['whatsapp #', 'whatsapp 3', 'whatsapp', 'WhatsApp #', 'WHATSAPP']:
        try:
            matched_wa_sheet = find_sheet_name(excel_file, [s_name])
            df_wa = excel_file.parse(matched_wa_sheet)
            if 'nombre' in df_wa.columns:
                df_wa['nombre'] = df_wa['nombre'].astype(str).str.strip()
                df_wa['NormalizedNombre'] = df_wa['nombre'].apply(normalize_name)
                df_whatsapp = df_wa
                break
        except Exception:
            continue

    amort_tables = parse_amortization_tables(excel_file)
    
    return df_resumen, df_ahorros, df_flujo, df_whatsapp, amort_tables

# Run data loading
try:
    df_resumen, df_ahorros, df_flujo, df_whatsapp, amort_tables = load_data(SHEET_URL)
    data_loaded = True
except Exception as e:
    st.error(f"Error al cargar los datos de Google Sheets: {e}")
    data_loaded = False

if data_loaded:
    socios_list = [str(s).strip() for s in df_ahorros['Socio'].dropna() if str(s).strip()]
    flujo_names = [str(n).strip() for n in df_flujo['Nombre'].dropna() if str(n).strip()]
    
    seen_names = set()
    full_people_list = []
    for name in socios_list + flujo_names:
        norm = normalize_name(name)
        if norm not in seen_names and name != "":
            full_people_list.append(name)
            seen_names.add(norm)
    full_people_list = sorted(full_people_list)
    
    # Sidebar Logo & Branding
    sb_col1, sb_col2, sb_col3 = st.sidebar.columns([1, 3, 1])
    with sb_col2:
        st.image("logo.png", use_container_width=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 👤 Seleccionar Persona:")
    selected_person = st.sidebar.selectbox(
        label="Persona",
        options=full_people_list,
        label_visibility="collapsed"
    )
    
    norm_selected = normalize_name(selected_person)
    user_loans_for_type = df_flujo[df_flujo['NormalizedNombre'] == norm_selected].to_dict('records')
    is_socio = (selected_person in socios_list) or any(l['Tipo'] == 'socio' for l in user_loans_for_type)
    user_type_label = "SOCIO DEL FONDO" if is_socio else "PARTICULAR / TERCERO"
    user_badge_class = "badge-socio" if is_socio else "badge-tercero"
    
    # Evaluate activity status
    user_status_eval = evaluate_participant_status(selected_person, df_ahorros, df_flujo)
    
    st.sidebar.markdown(f"<div style='text-align: center; margin-top: 10px; display: flex; flex-direction: column; gap: 6px; align-items: center;'><span class='{user_badge_class}'>{user_type_label}</span>{user_status_eval['overall_badge']}</div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 🔗 Accesos:")
    st.sidebar.markdown(f"[📂 Planilla Excel Drive](https://docs.google.com/spreadsheets/d/1ZL5aORQJ7C00YgpMUOfoXyKYtMkB2PRfbKUNrCGQPMc/edit?usp=sharing)")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    # Main Header
    st.markdown(f"<h1 style='margin-bottom: 0px;'>💰 Estado de Cuenta: {selected_person}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94a3b8; font-size: 1.05rem; margin-top: 4px; margin-bottom: 20px;'>Resumen financiero individual y del Fondo de Vecinos</p>", unsafe_allow_html=True)
    
    # Main Tabs: Individual Analysis & Fund Status
    tab_individual, tab_fund = st.tabs(["👤 ANÁLISIS INDIVIDUAL", "📊 ESTADO GENERAL DEL FONDO"])
    
    # ==========================================
    # --- TAB 1: INDIVIDUAL ANALYSIS ---
    # ==========================================
    with tab_individual:
        norm_selected = normalize_name(selected_person)
        user_loans = df_flujo[df_flujo['NormalizedNombre'] == norm_selected].to_dict('records')
        
        total_loan_balance = sum(loan['Saldo Pendiente'] for loan in user_loans if not pd.isna(loan['Saldo Pendiente']))
        active_loans_count = sum(1 for loan in user_loans if 'ACTIVO' in str(loan.get('Estado', '')).upper())
        
        socio_savings_df = df_ahorros[df_ahorros['NormalizedSocio'] == norm_selected]
        has_savings = len(socio_savings_df) > 0
        
        total_savings = 0
        base_savings = 0
        if is_socio and has_savings:
            socio_savings_row = socio_savings_df.iloc[0]
            total_savings = socio_savings_row['Total Anual'] if not pd.isna(socio_savings_row['Total Anual']) else 0
            base_savings = socio_savings_row['Aporte Base'] if not pd.isna(socio_savings_row['Aporte Base']) else 0

        # WhatsApp Message & Phone Number Generator
        phone_num = get_phone_for_person(selected_person, df_whatsapp)
        wa_msg = generate_whatsapp_message(
            selected_person, user_type_label, user_status_eval, 
            total_savings, base_savings, active_loans_count, total_loan_balance, 
            user_loans, df_resumen, df_ahorros, df_flujo
        )
        encoded_wa_msg = urllib.parse.quote(wa_msg)
        if phone_num:
            wa_url = f"https://api.whatsapp.com/send?phone={phone_num}&text={encoded_wa_msg}"
            btn_wa_label = f"📲 Enviar Resumen a {selected_person} (+{phone_num})"
        else:
            wa_url = f"https://api.whatsapp.com/send?text={encoded_wa_msg}"
            btn_wa_label = f"📲 Enviar Resumen por WhatsApp (Elegir Contacto)"

        # Display WhatsApp Action Card with 2 Options
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%); border: 1.5px solid #10b981; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;'>
            <div style='font-size: 1.05rem; font-weight: 700; color: #34d399; margin-bottom: 4px;'>
                💬 Opciones para Enviar Estado de Cuenta por WhatsApp
            </div>
            <div style='color: #cbd5e1; font-size: 0.88rem;'>
                Elige cómo deseas enviar el estado de cuenta a <b>{selected_person}</b> (Texto directo o Imagen / Pantallazo con el logo oficial):
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        wa_tab_text, wa_tab_img = st.tabs(["📝 Opción 1: Enviar como Texto", "📸 Opción 2: Enviar Pantallazo (Imágenes)"])
        
        with wa_tab_text:
            st.link_button(btn_wa_label, wa_url, use_container_width=True)
            with st.expander("👁️ Ver texto sin encabezado ni link (Listo para enviar)"):
                st.code(wa_msg, language="markdown")
                
        with wa_tab_img:
            # Generate 1-click downloadable PNG card image
            card1_buf = generate_individual_card_png(
                selected_person, user_type_label, user_status_eval, 
                total_savings, base_savings, active_loans_count, total_loan_balance, user_loans
            )
            safe_person_filename = re.sub(r'[^a-zA-Z0-9]', '_', selected_person)
            file_name_1 = f"Ficha1_Resumen_{safe_person_filename}.png"
            
            st.download_button(
                label=f"📥 1. Descargar Imagen de la Ficha en PNG ({selected_person})",
                data=card1_buf,
                file_name=file_name_1,
                mime="image/png",
                use_container_width=True
            )
            
            if phone_num:
                wa_img_url = f"https://api.whatsapp.com/send?phone={phone_num}"
                btn_wa_img_label = f"📲 2. Abrir Chat de WhatsApp con {selected_person} (+{phone_num})"
            else:
                wa_img_url = "https://api.whatsapp.com/send"
                btn_wa_img_label = "📲 2. Abrir WhatsApp (Elegir Contacto)"
                
            st.markdown("""
            <div style='background: rgba(30, 41, 59, 0.7); border-left: 4px solid #3b82f6; border-radius: 8px; padding: 12px 16px; margin-top: 10px; margin-bottom: 12px; font-size: 0.88rem; color: #e2e8f0;'>
                <b>💡 Pasos para enviar la Ficha en Imagen con 1 Clic:</b><br/>
                1. Presiona el botón azul <b>"📥 1. Descargar Imagen de la Ficha en PNG"</b> para guardar la foto directamente en tu celular o equipo.<br/>
                2. Presiona el botón verde <b>"📲 2. Abrir Chat de WhatsApp"</b>.<br/>
                3. En WhatsApp, toca el ícono de adjuntar 📎 / galería y envía la imagen descargada. ¡Así no tienes que tomar pantallazos!
            </div>
            """, unsafe_allow_html=True)
            st.link_button(btn_wa_img_label, wa_img_url, use_container_width=True)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

        # --- AVISO DE INACTIVIDAD / AL DÍA BANNER ---
        if user_status_eval['is_inactive']:
            reasons_li = ""
            for r in user_status_eval['ahorro_reasons']:
                reasons_li += f"<li style='margin-bottom: 4px;'><b>Ahorro de Socios:</b> {r}</li>"
            for r in user_status_eval['loan_reasons']:
                reasons_li += f"<li style='margin-bottom: 4px;'><b>Cuotas de Crédito:</b> {r}</li>"
                
            st.markdown(f"""
            <div class='alert-card-danger'>
                <div style='font-size: 1.15rem; font-weight: 800; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;'>
                    <span>⚠️</span> <span>AVISO IMPORTANTE: PARTICIPANTE INACTIVO / EN MORA</span>
                </div>
                <div style='font-size: 0.95rem; line-height: 1.5;'>
                    Estimado(a) <b>{selected_person}</b>, el sistema detecta que tu cuenta registra <b>novedad de inactividad</b> por las siguientes razones:
                    <ul style='margin-top: 8px; margin-bottom: 10px; padding-left: 22px;'>
                        {reasons_li}
                    </ul>
                    <span style='font-size: 0.88rem; color: #fca5a5;'><i>Por favor, ponte en contacto con la administración del Fondo de Vecinos para regularizar los pagos pendientes.</i></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif user_status_eval['overall_status'] == 'RETIRADO':
            st.markdown(f"""
            <div class='alert-card-info'>
                ℹ️ <b>Estado del Participante:</b> <b>{selected_person}</b> figura como socio retirado del Fondo de Vecinos.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='alert-card-success'>
                <div style='display: flex; align-items: center; gap: 8px;'>
                    <span>🟢</span> <span><b>ESTADO AL DÍA:</b> <b>{selected_person}</b> se encuentra al día con sus cuotas de ahorro mensual y pagos de préstamos. ¡Gracias por mantener tu cuenta activa y puntual!</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 4 Core KPI Cards Grid (Clear, big fonts, intuitive for adults)
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            val_savings_str = fmt_money(total_savings) if (is_socio and has_savings) else "N/A"
            val_class = "val-green" if (is_socio and has_savings) else "val-gray"
            st.markdown(f"""
            <div class='summary-card summary-card-green'>
                <span class='card-icon'>💰</span>
                <div class='card-label'>Total Ahorrado</div>
                <div class='card-value {val_class}'>{val_savings_str}</div>
                <p class='card-subtext'>Ahorro total acumulado</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            val_base_str = fmt_money(base_savings) if (is_socio and has_savings) else "N/A"
            val_class_b = "val-blue" if (is_socio and has_savings) else "val-gray"
            st.markdown(f"""
            <div class='summary-card summary-card-blue'>
                <span class='card-icon'>📅</span>
                <div class='card-label'>Aporte Mensual</div>
                <div class='card-value {val_class_b}'>{val_base_str}</div>
                <p class='card-subtext'>Cuota fija mensual de ahorro</p>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class='summary-card summary-card-purple'>
                <span class='card-icon'>💳</span>
                <div class='card-label'>Número de Créditos</div>
                <div class='card-value val-purple'>{active_loans_count}</div>
                <p class='card-subtext'>Préstamos activos actuales</p>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            val_loan_str = fmt_money(total_loan_balance, show_decimals=True)
            val_class_l = "val-red" if total_loan_balance > 0 else "val-green"
            st.markdown(f"""
            <div class='summary-card summary-card-red'>
                <span class='card-icon'>⚠️</span>
                <div class='card-label'>Saldo Pendiente</div>
                <div class='card-value {val_class_l}'>{val_loan_str}</div>
                <p class='card-subtext'>Total deuda por saldar</p>
            </div>
            """, unsafe_allow_html=True)

        # --- SAVINGS BREAKDOWN (Clear tabular view without graph, clean for mobile) ---
        if is_socio and has_savings:
            st.markdown("<div class='section-title'>📁 Historial de Ahorros Mensuales</div>", unsafe_allow_html=True)
            
            socio_savings_row = socio_savings_df.iloc[0]
            ignore_cols = ['Socio', 'Aporte Base', 'Total Anual', 'NormalizedSocio']
            months_cols = [c for c in df_ahorros.columns if c not in ignore_cols and not str(c).startswith('Unnamed:')]
            
            savings_records = []
            for col_name in months_cols:
                val = socio_savings_row.get(col_name, 0) if col_name in socio_savings_row else 0
                val_num = 0.0
                if pd.notna(val) and str(val).strip() not in ['', '0', '0.0', ' ']:
                    try:
                        val_num = float(val)
                    except (ValueError, TypeError):
                        val_num = 0.0
                
                label = get_column_display_name(col_name)
                if val_num > 0:
                    savings_records.append({
                        'Mes / Periodo': label,
                        'Monto Ahorrado': fmt_money(val_num),
                        'Estado': '✅ Registrado'
                    })
                elif len(savings_records) > 0 and len(savings_records) < 18:
                    savings_records.append({
                        'Mes / Periodo': label,
                        'Monto Ahorrado': fmt_money(val_num),
                        'Estado': '⚪ Pendiente'
                    })
            
            if not savings_records:
                for col_name in months_cols[:12]:
                    savings_records.append({
                        'Mes / Periodo': get_column_display_name(col_name),
                        'Monto Ahorrado': fmt_money(0),
                        'Estado': '⚪ Pendiente'
                    })

            df_savings_view = pd.DataFrame(savings_records)
            
            with st.expander("🔍 Ver Detalle Mensual de Ahorros completos", expanded=False):
                st.dataframe(df_savings_view, hide_index=True, use_container_width=True)

        elif not is_socio:
            st.markdown("""
            <div class='alert-card'>
                ℹ️ <b>Nota:</b> Esta persona está registrada como <b>TERCERO / PARTICULAR</b>, por lo que no posee aportes de ahorro en el fondo. Únicamente registra préstamos/créditos.
            </div>
            """, unsafe_allow_html=True)

        # --- LOANS & AMORTIZATION TABLE SUMMARY ---
        st.markdown("<div class='section-title'>📋 Resumen de Créditos y Tabla de Amortizaciones</div>", unsafe_allow_html=True)
        
        if not user_loans:
            st.info("💡 Esta persona no tiene créditos registrados o activos en el fondo actualmente.")
        else:
            if len(user_loans) > 1:
                loan_tabs = st.tabs([f"Crédito {i+1} ({fmt_money(loan['Monto'])} - {str(loan.get('Estado', '')).upper()})" for i, loan in enumerate(user_loans)])
            else:
                loan_tabs = [st.container()]
                
            for idx, loan in enumerate(user_loans):
                with loan_tabs[idx]:
                    is_active = 'ACTIVO' in str(loan.get('Estado', '')).upper()
                    loan_status_badge = "<span class='badge-status-activo'>CRÉDITO ACTIVO</span>" if is_active else "<span class='badge-status-cancelado'>CANCELADO / PAGADO</span>"
                    
                    st.markdown(f"### Detalles del Crédito ID #{loan.get('ID', idx+1)} {loan_status_badge}", unsafe_allow_html=True)
                    
                    # Credit Specific Cards Row
                    col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
                    with col_l1:
                        st.markdown(f"""
                        <div class='summary-card'>
                            <div class='card-label'>Monto Prestado</div>
                            <div class='card-value val-gray'>{fmt_money(loan['Monto'])}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_l2:
                        st.markdown(f"""
                        <div class='summary-card'>
                            <div class='card-label'>Cuota Mensual Fija</div>
                            <div class='card-value val-purple'>{fmt_money(loan['Cuota Fija'], show_decimals=True)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_l3:
                        tasa_val = float(loan['Tasa (%)']) * 100 if isinstance(loan['Tasa (%)'], float) and loan['Tasa (%)'] < 1 else loan['Tasa (%)']
                        st.markdown(f"""
                        <div class='summary-card'>
                            <div class='card-label'>Tasa de Interés</div>
                            <div class='card-value val-blue'>{tasa_val}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_l4:
                        st.markdown(f"""
                        <div class='summary-card'>
                            <div class='card-label'>Interés Pactado</div>
                            <div class='card-value val-green'>{fmt_money(loan['Total Interés'], show_decimals=True)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_l5:
                        st.markdown(f"""
                        <div class='summary-card summary-card-red'>
                            <div class='card-label'>Saldo Pendiente</div>
                            <div class='card-value val-red'>{fmt_money(loan['Saldo Pendiente'], show_decimals=True)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Amortization Table Summary
                    st.markdown("<h4 style='margin-top: 18px;'>📑 Tabla de Amortización (Control de Cuotas)</h4>", unsafe_allow_html=True)
                    try:
                        loan_id = int(loan['ID']) if 'ID' in loan and not pd.isna(loan['ID']) else None
                    except (ValueError, TypeError):
                        loan_id = None
                        
                    loan_person_name = str(loan.get('Nombre', selected_person)).strip().upper()
                    clean_person_name = re.sub(r'[\#\-\d]|(\(CRÉDITO\))|(\(SOCIO\))|(\(CREDITO\))', '', loan_person_name, flags=re.IGNORECASE).strip().upper()
                    
                    # Compute sequential loan index for this row in df_flujo
                    flujo_loan_idx = None
                    try:
                        # Find 1-based row index in df_flujo
                        flujo_loan_idx = int(df_flujo[df_flujo['ID'] == loan_id].index[0]) + 1 if loan_id is not None and len(df_flujo[df_flujo['ID'] == loan_id]) > 0 else None
                    except Exception:
                        flujo_loan_idx = None

                    matched_table = None
                    if loan_id is not None and loan_id in amort_tables:
                        matched_table = amort_tables[loan_id]
                    elif clean_person_name in amort_tables:
                        matched_table = amort_tables[clean_person_name]
                    elif loan_person_name in amort_tables:
                        matched_table = amort_tables[loan_person_name]
                    elif flujo_loan_idx is not None and flujo_loan_idx in amort_tables:
                        matched_table = amort_tables[flujo_loan_idx]
                    elif (idx + 1) in amort_tables:
                        matched_table = amort_tables[idx + 1]
                    
                    if matched_table:
                        schedule_df = matched_table['schedule'].copy()
                        
                        html_rows = []
                        for idx_p, r_item in schedule_df.iterrows():
                            f_val = str(r_item.get('Cuota / Fecha', '')).strip()
                            v_cuota = r_item.get('Valor Cuota', 0)
                            v_abono = r_item.get('Abono a Capital', 0)
                            v_int = r_item.get('Intereses', 0)
                            v_saldo = r_item.get('Saldo Pendiente', 0)
                            
                            try:
                                v_cuota_num = float(v_cuota) if not pd.isna(v_cuota) else 0.0
                                v_abono_num = float(v_abono) if not pd.isna(v_abono) else 0.0
                                v_int_num = float(v_int) if not pd.isna(v_int) else 0.0
                                v_saldo_num = float(v_saldo) if not pd.isna(v_saldo) else 0.0
                            except (ValueError, TypeError):
                                v_cuota_num = v_abono_num = v_int_num = v_saldo_num = 0.0

                            is_desembolso = (v_cuota_num == 0 and v_abono_num == 0 and v_int_num == 0) or f_val in ['0', '0.0', 'Desembolso']
                            row_class = "class='row-desembolso'" if is_desembolso else ""
                            lbl_cuota = f"🟢 Desembolso ({f_val})" if is_desembolso else f"📅 {f_val}"
                            
                            html_rows.append(
                                f"<tr {row_class}>"
                                f"<td>{lbl_cuota}</td>"
                                f"<td>{fmt_money(v_cuota_num, show_decimals=True)}</td>"
                                f"<td>{fmt_money(v_abono_num, show_decimals=True)}</td>"
                                f"<td>{fmt_money(v_int_num, show_decimals=True)}</td>"
                                f"<td><b>{fmt_money(v_saldo_num, show_decimals=True)}</b></td>"
                                f"</tr>"
                            )

                        rows_str = "".join(html_rows)
                        table_html = (
                            f"<div class='amort-table-wrapper'>"
                            f"<table class='custom-amort-table'>"
                            f"<thead>"
                            f"<tr>"
                            f"<th>N° / Fecha Cuota</th>"
                            f"<th>Valor Cuota</th>"
                            f"<th>Abono a Capital</th>"
                            f"<th>Intereses</th>"
                            f"<th>Saldo Pendiente</th>"
                            f"</tr>"
                            f"</thead>"
                            f"<tbody>{rows_str}</tbody>"
                            f"</table>"
                            f"</div>"
                        )
                        st.markdown(table_html, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ No se encontró la tabla de amortización detallada para este ID en la planilla de Google Sheets.")

    # ==========================================
    # --- TAB 2: GENERAL FUND STATUS ---
    # ==========================================
    with tab_fund:
        st.markdown("<h2 style='margin-bottom: 0px;'>📊 Estado Consolidado del Fondo de Vecinos</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8; font-size: 1rem; margin-top: 4px;'>Balance general de capitales, créditos y utilidades acumuladas</p>", unsafe_allow_html=True)
        
        # Parse Fund summary metrics
        metrics = parse_fund_metrics(df_resumen)
        tot_ahorros_val = metrics['tot_ahorros_val']
        int_ganados_val = metrics['int_ganados_val']
        util_eventos_val = metrics['util_eventos_val']
        fondo_total_val = metrics['fondo_total_val']
        cap_prestado_val = metrics['cap_prestado_val']
        gastos_op_val = metrics['gastos_op_val']
        disponible_banco_val = metrics['disponible_banco_val']
        caja_efectivo_val = metrics['caja_efectivo_val']
        active_loans_mask = df_flujo['Estado del credito'].astype(str).str.upper().str.contains('ACTIVO') if 'Estado del credito' in df_flujo.columns else df_flujo['Estado'].astype(str).str.upper().str.contains('ACTIVO')

        # Main Fund Metric Cards
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            st.markdown(f"""
            <div class='summary-card summary-card-purple'>
                <span class='card-icon'>🏛️</span>
                <div class='card-label'>Fondo Total Acumulado</div>
                <div class='card-value val-purple'>{fmt_money(fondo_total_val, show_decimals=True)}</div>
                <p class='card-subtext'>Patrimonio global del fondo</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f2:
            st.markdown(f"""
            <div class='summary-card summary-card-green'>
                <span class='card-icon'>🏦</span>
                <div class='card-label'>Total Ahorros Socios</div>
                <div class='card-value val-green'>{fmt_money(tot_ahorros_val)}</div>
                <p class='card-subtext'>Capital aportado por socios</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f3:
            st.markdown(f"""
            <div class='summary-card summary-card-red'>
                <span class='card-icon'>📢</span>
                <div class='card-label'>Capital Prestado</div>
                <div class='card-value val-red'>{fmt_money(cap_prestado_val, show_decimals=True)}</div>
                <p class='card-subtext'>Dinero en créditos activos</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f4:
            st.markdown(f"""
            <div class='summary-card summary-card-blue'>
                <span class='card-icon'>💵</span>
                <div class='card-label'>Disponible en Banco</div>
                <div class='card-value val-blue'>{fmt_money(disponible_banco_val, show_decimals=True)}</div>
                <p class='card-subtext'>Liquidez en cuenta bancaria</p>
            </div>
            """, unsafe_allow_html=True)

        # Secondary Fund Cards
        col_f5, col_f6, col_f7, col_f8 = st.columns(4)
        with col_f5:
            st.markdown(f"""
            <div class='summary-card'>
                <span class='card-icon'>📈</span>
                <div class='card-label'>Intereses Cobrados</div>
                <div class='card-value val-green'>{fmt_money(int_ganados_val, show_decimals=True)}</div>
                <p class='card-subtext'>Ganancias reales cobradas</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f6:
            st.markdown(f"""
            <div class='summary-card'>
                <span class='card-icon'>🎟️</span>
                <div class='card-label'>Utilidad Eventos / Rifas</div>
                <div class='card-value val-blue'>{fmt_money(util_eventos_val, show_decimals=True)}</div>
                <p class='card-subtext'>Ingresos extraordinarios</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f7:
            st.markdown(f"""
            <div class='summary-card'>
                <span class='card-icon'>💼</span>
                <div class='card-label'>Caja Efectivo</div>
                <div class='card-value val-gray'>{fmt_money(caja_efectivo_val, show_decimals=True)}</div>
                <p class='card-subtext'>Dinero físico en caja</p>
            </div>
            """, unsafe_allow_html=True)

        with col_f8:
            st.markdown(f"""
            <div class='summary-card summary-card-red'>
                <span class='card-icon'>🧾</span>
                <div class='card-label'>Gastos Operativos</div>
                <div class='card-value val-red'>{fmt_money(gastos_op_val, show_decimals=True)}</div>
                <p class='card-subtext'>Egresos y costos del fondo</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 1-Click Download Button for Ficha 2 PNG Image
        card2_buf = generate_fund_card_png(
            fondo_total_val, tot_ahorros_val, cap_prestado_val, disponible_banco_val,
            int_ganados_val, util_eventos_val, caja_efectivo_val, gastos_op_val
        )
        st.download_button(
            label="📥 Descargar Ficha 2 - Estado General del Fondo (Imagen PNG)",
            data=card2_buf,
            file_name="Ficha2_Estado_General_Fondo.png",
            mime="image/png",
            use_container_width=True
        )
        
        st.markdown("---")

        # Visual layout for Fund assets and overview
        col_pie, col_details = st.columns([1, 1])
        
        with col_pie:
            assets = ['📢 Capital Prestado', '💵 Disponible en Banco', '🧾 Gastos Operativos', '💼 Caja efectivo']
            asset_values = [cap_prestado_val, disponible_banco_val, gastos_op_val, caja_efectivo_val]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=assets,
                values=asset_values,
                hole=0.55,
                marker=dict(
                    colors=['#f43f5e', '#3b82f6', '#ef4444', '#94a3b8'],
                    line=dict(color='#1e293b', width=2)
                ),
                textinfo='percent',
                textposition='auto',
                hovertemplate="<b>%{label}</b><br>Monto: $ %{value:,.2f}<br>Porcentaje: %{percent}<extra></extra>",
                textfont=dict(size=13, color='#f8fafc')
            )])
            fig_pie.update_layout(
                title=dict(
                    text="<b>🏛️ Distribución del Patrimonio del Fondo</b>",
                    font=dict(size=17, color='#f8fafc'),
                    x=0.5,
                    xanchor='center'
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.22,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#cbd5e1", size=12)
                ),
                margin=dict(l=20, r=20, t=50, b=120),
                annotations=[dict(
                    text=f"<b>FONDO TOTAL<br>{fmt_money(fondo_total_val)}</b>",
                    x=0.5, y=0.5,
                    font=dict(size=13, color="#38bdf8"),
                    showarrow=False
                )]
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_details:
            st.markdown("### 📋 Resumen del Balance General")
            balance_items = [
                {'Concepto': 'Total Ahorros Socios', 'Valor ($)': fmt_money(tot_ahorros_val, show_decimals=True)},
                {'Concepto': 'Intereses Ganados (Cobrados)', 'Valor ($)': fmt_money(int_ganados_val, show_decimals=True)},
                {'Concepto': 'Utilidad Eventos/Rifas', 'Valor ($)': fmt_money(util_eventos_val, show_decimals=True)},
                {'Concepto': 'Fondo Total Acumulado', 'Valor ($)': fmt_money(fondo_total_val, show_decimals=True)},
                {'Concepto': 'Capital Prestado (En calle)', 'Valor ($)': fmt_money(cap_prestado_val, show_decimals=True)},
                {'Concepto': 'Disponible en Banco', 'Valor ($)': fmt_money(disponible_banco_val, show_decimals=True)},
                {'Concepto': 'Gastos Operativos', 'Valor ($)': fmt_money(gastos_op_val, show_decimals=True)},
                {'Concepto': 'Caja Efectivo', 'Valor ($)': fmt_money(caja_efectivo_val, show_decimals=True)}
            ]
            st.dataframe(pd.DataFrame(balance_items), hide_index=True, use_container_width=True)
            
            total_active_loans_amt = cap_prestado_val
            total_active_loans_count = len(df_flujo[active_loans_mask])
            
            # Global Activity Summary
            all_evals = [evaluate_participant_status(p, df_ahorros, df_flujo) for p in full_people_list]
            count_aldia = sum(1 for e in all_evals if e['overall_status'] == 'AL_DIA')
            count_inactivo = sum(1 for e in all_evals if e['overall_status'] == 'INACTIVO')
            count_retirado = sum(1 for e in all_evals if e['overall_status'] == 'RETIRADO')
            
            st.markdown(f"""
            <div class='alert-card' style='margin-top: 15px;'>
                💼 <b>Préstamos activos totales:</b> {total_active_loans_count}<br>
                💵 <b>Monto en préstamos en la calle:</b> {fmt_money(total_active_loans_amt, show_decimals=True)}<br>
                👥 <b>Estatus Participantes:</b> <span style='color: #34d399;'>{count_aldia} Al día</span> | <span style='color: #fb7185;'>{count_inactivo} Inactivos / Mora</span> | <span style='color: #94a3b8;'>{count_retirado} Retirados</span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🚨 Ver Lista de Participantes Inactivos / En Mora", expanded=False):
                inactivos_list = []
                for p, ev in zip(full_people_list, all_evals):
                    if ev['overall_status'] == 'INACTIVO':
                        reasons = " | ".join(ev['ahorro_reasons'] + ev['loan_reasons'])
                        inactivos_list.append({
                            'Participante': p,
                            'Detalle Novedad': reasons.replace('<b>', '').replace('</b>', '')
                        })
                if inactivos_list:
                    st.dataframe(pd.DataFrame(inactivos_list), hide_index=True, use_container_width=True)
                else:
                    st.success("🎉 ¡No hay participantes inactivos!")

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>Fondo de Vecinos Dashboard © 2026. Optimizado para celulares y lectura de adultos.</p>",
        unsafe_allow_html=True
    )
