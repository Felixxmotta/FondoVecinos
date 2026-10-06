#!/usr/bin/env python3
"""
Script para convertir los manuales Markdown a PDF profesional usando fpdf2
con fuentes DejaVu (Unicode completo — soporta tildes, emojis, símbolos).
"""
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Paths a fuentes DejaVu instaladas en el sistema
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
FONT_REGULAR = FONT_DIR + "DejaVuSans.ttf"
FONT_BOLD    = FONT_DIR + "DejaVuSans-Bold.ttf"
FONT_ITALIC  = FONT_DIR + "DejaVuSans-Oblique.ttf"
FONT_MONO    = FONT_DIR + "DejaVuSansMono.ttf"
FONT_MONO_BOLD = FONT_DIR + "DejaVuSansMono-Bold.ttf"

# Sustitución mínima de emojis que DejaVu no soporta bien en PDF básico
# (los emojis de bloque U+1Fxxx). Los de bloque BMP sí los maneja.
EMOJI_MAP = {
    '\U0001f3db': '[FONDO]',    '\U0001f4ca': '[GRAFICO]', '\U0001f4b0': '[DINERO]',
    '\U0001f4c8': '[UP]',       '\U0001f527': '[HERRAMIENTA]', '\U0001f4cb': '[LISTA]',
    '\U0001f4dd': '[NOTA]',     '\U0001f4de': '[TEL]',     '\U0001f512': '[LOCK]',
    '\U0001f4cc': '[PIN]',      '\U0001f6a8': '[ALERTA]',  '\U0001f9fe': '[RECIBO]',
    '\U0001f4e6': '[CAJA]',     '\U0001f5fa': '[MAPA]',    '\U0001f4f2': '[MOVIL]',
    '\U0001f4a1': '[IDEA]',     '\U0001f5a5': '[PC]',      '\U0001f517': '[LINK]',
    '\U0001f3e6': '[BANCO]',    '\U0001f4b3': '[TARJETA]', '\U0001f4b5': '[BILLETE]',
    '\U0001f465': '[SOCIOS]',   '\U0001f4bc': '[MALETIN]', '\U0001f4c5': '[CALENDARIO]',
    '\U0001f4c4': '[DOC]',      '\U0001f4c2': '[CARPETA]', '\U0001f4c1': '[FOLDER]',
    '\U0001f4e2': '[AVISO]',    '\U0001f4e3': '[MEGAFONO]','\U0001f4f8': '[CAMARA]',
    '\U0001f50d': '[BUSCAR]',   '\U0001f4af': '[100%]',    '\U0001f4aa': '[FUERZA]',
    '\U0001f44d': '[OK]',       '\U0001f6ab': '[NO]',      '\U0001f527': '[LLAVE]',
    '\u2705': '[OK]',           '\u274c': '[X]',           '\u2611': '[V]',
    '\u2610': '[ ]',            '\u2714': '[V]',           '\u2718': '[X]',
    '\U0001f4f1': '[MOVIL]',    '\U0001f310': '[WEB]',     '\U0001f4e7': '[EMAIL]',
    '\U0001f4f9': '[VIDEO]',    '\U0001f3a5': '[CAMARA2]', '\U0001f4fc': '[CINTA]',
    '\U0001f9e0': '[CEREBRO]',  '\U0001f916': '[ROBOT]',   '\U0001f4bb': '[LAPTOP]',
    '\U0001f4be': '[DISCO]',    '\U0001f5c4': '[ARCHIVO]', '\U0001f4df': '[FAX]',
    '\U0001f4f3': '[VIBRACION]','\U0001f4f4': '[SILENCIO]',
}

def sanitize(text):
    """Reemplaza emojis fuera de BMP con texto equivalente."""
    for char, rep in EMOJI_MAP.items():
        text = text.replace(char, rep)
    # Filtrar cualquier carácter fuera del rango que DejaVu maneje (>U+FFFF como safety)
    return ''.join(c if ord(c) <= 0xFFFF else '?' for c in text)


class ManualPDF(FPDF):
    def __init__(self, title, subtitle):
        super().__init__()
        self.title_str = sanitize(title)
        self.subtitle_str = sanitize(subtitle)
        self.set_auto_page_break(auto=True, margin=20)
        # Registrar fuentes Unicode
        self.add_font('Regular', '', FONT_REGULAR)
        self.add_font('Regular', 'B', FONT_BOLD)
        self.add_font('Regular', 'I', FONT_ITALIC)
        self.add_font('Mono', '', FONT_MONO)
        self.add_font('Mono', 'B', FONT_MONO_BOLD)

    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 18, 'F')
        self.set_text_color(147, 197, 253)
        self.set_font('Regular', 'B', 9)
        self.set_xy(10, 5)
        self.cell(0, 8, 'FONDO DE VECINOS DE LA MESA \u2014 ' + self.title_str.upper(), align='L')
        self.set_text_color(100, 116, 139)
        self.set_font('Regular', '', 8)
        self.set_xy(0, 5)
        self.cell(-10, 8, f'Pag. {self.page_no()}', align='R')
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(15, 23, 42)
        self.rect(0, 282, 210, 15, 'F')
        self.set_text_color(100, 116, 139)
        self.set_font('Regular', '', 8)
        self.set_xy(10, 284)
        self.cell(0, 6, 'Sistema Digital de Gesti\u00f3n Financiera \u2014 Fondo de Vecinos de La Mesa \u00a9 2026', align='L')

    def cover_page(self):
        self.add_page()
        # Fondo oscuro
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 297, 'F')
        # Barra azul
        self.set_fill_color(59, 130, 246)
        self.rect(0, 75, 210, 6, 'F')
        # T\u00edtulo principal
        self.set_text_color(255, 255, 255)
        self.set_font('Regular', 'B', 26)
        self.set_xy(15, 95)
        self.multi_cell(180, 13, 'FONDO DE VECINOS\nDE LA MESA', align='C')
        # Subt\u00edtulo del documento
        self.set_text_color(147, 197, 253)
        self.set_font('Regular', 'B', 15)
        self.set_xy(15, 148)
        self.multi_cell(180, 9, self.title_str, align='C')
        # Divisor
        self.set_fill_color(59, 130, 246)
        self.rect(40, 172, 130, 2, 'F')
        # Descripci\u00f3n
        self.set_text_color(203, 213, 225)
        self.set_font('Regular', '', 11)
        self.set_xy(15, 178)
        self.multi_cell(180, 7, self.subtitle_str, align='C')
        # Versi\u00f3n
        self.set_text_color(100, 116, 139)
        self.set_font('Regular', '', 10)
        self.set_xy(15, 250)
        self.cell(180, 7, 'Versi\u00f3n 2.0  |  Septiembre 2026', align='C')
        # URL
        self.set_text_color(96, 165, 250)
        self.set_font('Regular', 'I', 9)
        self.set_xy(15, 260)
        self.cell(180, 7, 'https://chatbotwap-production-e2a3.up.railway.app/', align='C')


def strip_md_inline(text):
    """Elimina formato Markdown inline (negrita, it\u00e1lica, c\u00f3digo, enlaces)."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def md_to_pdf(md_path, pdf_path, title, subtitle):
    pdf = ManualPDF(title, subtitle)
    pdf.cover_page()
    pdf.add_page()

    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_table = False
    in_code = False
    code_lines = []
    table_rows = []
    first_h1_skipped = False

    def flush_table(p):
        if not table_rows:
            return
        data = [row for row in table_rows if not re.match(r'^[\|\s\-:]+$', row)]
        if not data:
            return

        col_count = max(len(r.split('|')) - 2 for r in data)
        if col_count < 1:
            col_count = 1
        col_w = min(58, 180 // col_count)

        for i, row in enumerate(data):
            cols = [c.strip() for c in row.strip('|').split('|')]
            while len(cols) < col_count:
                cols.append('')
            cols = cols[:col_count]

            if i == 0:
                p.set_fill_color(30, 58, 138)
                p.set_text_color(255, 255, 255)
                p.set_font('Regular', 'B', 8)
            else:
                p.set_fill_color(240, 244, 255) if i % 2 == 0 else p.set_fill_color(255, 255, 255)
                p.set_text_color(30, 41, 59)
                p.set_font('Regular', '', 8)

            row_h = 7
            for col in cols:
                clean = sanitize(strip_md_inline(col))
                # Truncar si es muy largo para la celda
                while p.get_string_width(clean) > col_w - 2 and len(clean) > 3:
                    clean = clean[:-1]
                if len(clean) < len(sanitize(strip_md_inline(col))):
                    clean = clean[:-2] + '..'
                p.cell(col_w, row_h, clean, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
            p.ln(row_h)

        p.set_text_color(30, 41, 59)
        p.ln(3)

    def flush_code(p, lines_buf):
        if not lines_buf:
            return
        p.set_fill_color(20, 30, 48)
        p.set_text_color(134, 239, 172)
        p.set_font('Mono', '', 7.5)
        for ln in lines_buf:
            text = sanitize(ln.rstrip('\n'))
            if text == '':
                p.ln(2)
            else:
                p.set_x(12)
                p.multi_cell(183, 4.5, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        p.set_text_color(30, 41, 59)
        p.ln(3)

    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip('\n')

        # Bloque de c\u00f3digo
        if raw.startswith('```'):
            if in_code:
                flush_code(pdf, code_lines)
                code_lines = []
                in_code = False
            else:
                if in_table:
                    flush_table(pdf)
                    table_rows = []
                    in_table = False
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(raw + '\n')
            i += 1
            continue

        # Fila de tabla
        if raw.startswith('|'):
            in_table = True
            table_rows.append(raw)
            i += 1
            continue
        else:
            if in_table:
                flush_table(pdf)
                table_rows = []
                in_table = False

        # L\u00ednea en blanco
        if raw.strip() == '':
            pdf.ln(3)
            i += 1
            continue

        # Regla horizontal
        if re.match(r'^---+$', raw.strip()):
            pdf.set_draw_color(59, 130, 246)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            i += 1
            continue

        # Alerta estilo GitHub (> [!NOTE] / [!WARNING] etc.)
        if raw.startswith('> [!'):
            m = re.match(r'> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', raw)
            if m:
                level = m.group(1)
                colors = {
                    'NOTE':      (219, 234, 254, 30, 64, 175,  '[NOTA]'),
                    'TIP':       (220, 252, 231, 21, 128, 61,  '[TIP]'),
                    'IMPORTANT': (250, 245, 255, 109, 40, 217, '[IMPORTANTE]'),
                    'WARNING':   (254, 249, 195, 133, 77, 14,  '[AVISO]'),
                    'CAUTION':   (254, 226, 226, 185, 28, 28,  '[PRECAUCION]'),
                }
                bg = colors.get(level, (219, 234, 254, 30, 64, 175, '[INFO]'))
                pdf.set_fill_color(bg[0], bg[1], bg[2])
                pdf.set_text_color(bg[3], bg[4], bg[5])
                pdf.set_font('Regular', 'B', 8.5)
                pdf.set_x(12)
                pdf.cell(0, 6, bg[6], fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                # Leer l\u00edneas subsiguientes del bloque
                i += 1
                while i < len(lines):
                    nxt = lines[i].rstrip('\n')
                    if not nxt.startswith('>'):
                        break
                    content = strip_md_inline(nxt.lstrip('> '))
                    if content:
                        pdf.set_font('Regular', 'I', 8.5)
                        pdf.set_x(14)
                        pdf.multi_cell(176, 5.5, sanitize(content), fill=True,
                                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                    i += 1
                pdf.set_text_color(30, 41, 59)
                pdf.ln(2)
                continue

        # Blockquote normal
        if raw.startswith('>'):
            text = sanitize(strip_md_inline(raw.lstrip('> ')))
            pdf.set_fill_color(219, 234, 254)
            pdf.set_text_color(30, 64, 175)
            pdf.set_font('Regular', 'I', 9)
            pdf.set_x(15)
            pdf.multi_cell(175, 6, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(2)
            i += 1
            continue

        # H1
        if raw.startswith('# ') and not raw.startswith('## '):
            text = sanitize(strip_md_inline(raw[2:]))
            if not first_h1_skipped:
                first_h1_skipped = True
                i += 1
                continue  # Ya est\u00e1 en la portada
            pdf.set_fill_color(15, 23, 42)
            pdf.set_text_color(147, 197, 253)
            pdf.set_font('Regular', 'B', 15)
            pdf.set_x(10)
            pdf.multi_cell(190, 10, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(3)
            i += 1
            continue

        # H2
        if raw.startswith('## '):
            text = sanitize(strip_md_inline(raw[3:]))
            pdf.set_fill_color(30, 58, 138)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Regular', 'B', 12)
            pdf.set_x(10)
            pdf.multi_cell(190, 9, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(2)
            i += 1
            continue

        # H3
        if raw.startswith('### '):
            text = sanitize(strip_md_inline(raw[4:]))
            pdf.set_text_color(59, 130, 246)
            pdf.set_font('Regular', 'B', 11)
            pdf.set_x(10)
            pdf.multi_cell(190, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(1)
            i += 1
            continue

        # H4
        if raw.startswith('#### '):
            text = sanitize(strip_md_inline(raw[5:]))
            pdf.set_text_color(96, 165, 250)
            pdf.set_font('Regular', 'B', 10)
            pdf.set_x(10)
            pdf.multi_cell(190, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(30, 41, 59)
            pdf.ln(1)
            i += 1
            continue

        # Checkbox (- [ ] o - [x])
        if re.match(r'^\s*- \[[ xX]\]', raw):
            checked = '[x]' in raw.lower()
            text = sanitize(strip_md_inline(re.sub(r'- \[[ xX]\]\s*', '', raw)))
            symbol = '\u2611' if checked else '\u2610'
            pdf.set_font('Regular', '', 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(12)
            pdf.cell(8, 6, symbol)
            pdf.set_x(20)
            pdf.multi_cell(175, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        # Lista con viñetas / numerada
        if re.match(r'^(\s*[-*]\s|\s*\d+\.\s)', raw):
            indent = len(raw) - len(raw.lstrip())
            text = sanitize(strip_md_inline(re.sub(r'^(\s*[-*]\s|\s*\d+\.\s)', '', raw)))
            x_pos = 12 + indent * 0.5
            pdf.set_font('Regular', '', 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(x_pos)
            num_m = re.match(r'^\s*(\d+\.)', raw)
            bullet = num_m.group(1) if num_m else '\u2022'
            pdf.cell(7, 6, bullet)
            pdf.set_x(x_pos + 7)
            pdf.multi_cell(183 - x_pos, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        # P\u00e1rrafo normal
        text = sanitize(strip_md_inline(raw))
        if text:
            pdf.set_font('Regular', '', 9.5)
            pdf.set_text_color(30, 41, 59)
            pdf.set_x(10)
            pdf.multi_cell(190, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        i += 1

    # Vaciar buffers restantes
    if in_table:
        flush_table(pdf)
    if in_code:
        flush_code(pdf, code_lines)

    pdf.output(pdf_path)
    print(f"✅ PDF generado: {pdf_path}")


# ─── Generar ambos manuales ───────────────────────────────────────────────────
md_to_pdf(
    'MANUAL_USUARIO.md',
    'Manual_Usuario_FONDO_DE_AHORRO_AMIGOS_DE_LA_MESA.pdf',
    'MANUAL DE USUARIO',
    'Guía de Operación para el Administrador / Tesorero'
)

md_to_pdf(
    'GUIA_MANTENIMIENTO.md',
    'Guia_Mantenimiento_FONDO_DE_AHORRO_AMIGOS_DE_LA_MESA.pdf',
    'GUÍA DE MANTENIMIENTO TÉCNICO',
    'Manual Técnico para el Administrador del Sistema'
)

print("\n✅ ¡Ambos PDFs generados exitosamente!")
