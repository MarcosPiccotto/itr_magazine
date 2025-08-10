import os
import pypandoc
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
from bs4 import BeautifulSoup
    

# ===== CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'driveCredentials.json'  # Tu archivo JSON
FOLDER_ID = '1uz-MJd-7stYBuNF-fHyOBOhHof0xSYa-'  # Ej: '1A2B3C4D5E6F...'
OUTPUT_DIR = './docs'  # Carpeta donde Docusaurus guarda la doc

# ===== AUTENTICACIÓN =====
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# ===== CREAR CARPETA DESTINO =====
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== CONECTAR CON GOOGLE DRIVE =====
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build('drive', 'v3', credentials=creds)

def style_to_md(text, style):
    """Convierte estilos HTML en formato Markdown"""
    if not style:
        return text

    style = style.lower()

    # Detectar títulos por tamaño de fuente
    if "font-size:26pt" in style:
        return f"# {text}"
    if "font-size:22pt" in style:
        return f"## {text}"
    if "font-size:18pt" in style:
        return f"### {text}"

    # Negrita
    if "font-weight:700" in style or "bold" in style:
        return f"**{text}**"

    # Cursiva
    if "font-style:italic" in style:
        return f"*{text}*"

    return text

# ===== LISTAR ARCHIVOS EN LA CARPETA =====
print("📂 Obteniendo lista de documentos...")
results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.document'",
    fields="files(id, name)"
).execute()
files = results.get('files', [])

if not files:
    print("⚠ No se encontraron documentos en la carpeta.")
else:
    for file in files:
        file_id = file['id']
        name = file['name']
        safe_name = name.replace(" ", "_")
        print(f"⬇ Descargando: {name}")

        # Exportar a HTML
        html_data = service.files().export(
            fileId=file_id, mimeType='text/html'
        ).execute()

        html_path = f"/tmp/{safe_name}.html"
        with open(html_path, "wb") as f:
            f.write(html_data)

        # Parsear HTML
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        md_lines = []
        for elem in soup.find_all(["p", "span", "h1", "h2", "h3", "h4", "strong", "em"]):
            text = elem.get_text(strip=True)
            if not text:
                continue

            style = elem.get("style", "")
            md_text = style_to_md(text, style)
            md_lines.append(md_text)

        # Guardar como .md
        md_path = os.path.join(OUTPUT_DIR, f"{safe_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(md_lines))

        print(f"✅ Guardado con formato Markdown: {md_path}")

print("🎉 Conversión completa.")