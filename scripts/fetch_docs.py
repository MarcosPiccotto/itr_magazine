import os
import json
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# ===== CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'driveCredentials.json'
FOLDER_ID = '1uz-MJd-7stYBuNF-fHyOBOhHof0xSYa-'
OUTPUT_DIR = './docs'
STATIC_IMG_DIR = './static/img'  # Carpeta de imágenes para Docusaurus

# ===== AUTENTICACIÓN =====
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# ===== FUNCIONES =====
def download_image(url, local_path):
    """Descarga imagen si no existe o cambió"""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if os.path.exists(local_path):
        return  # No volver a descargar
    r = requests.get(url)
    if r.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(r.content)
        print(f"🖼 Guardada imagen: {local_path}")

def element_to_md(elem, img_subfolder):
    """Convierte elemento HTML a Markdown"""
    tag = elem.name.lower() if elem.name else ""
    text = elem.get_text(strip=True)

    # Encabezados
    if tag in ["h1","h2","h3","h4","h5","h6"]:
        return f"{'#' * int(tag[1])} {text}"

    # Listas
    if tag == "li":
        parent = elem.find_parent(["ol","ul"])
        prefix = "-" if parent.name == "ul" else f"{list(parent.find_all('li')).index(elem) + 1}."
        return f"{prefix} {text}"

    # Citas
    if tag == "blockquote":
        return "\n".join([f"> {line}" for line in text.splitlines()])

    # Código
    if tag == "code":
        return f"```\n{text}\n```" if elem.find_parent("pre") else f"`{text}`"

    # Párrafos
    if tag == "p":
        return text

    # Formato
    if tag in ["strong","b"]:
        return f"**{text}**"
    if tag in ["em","i"]:
        return f"*{text}*"

    # Links
    if tag == "a":
        return f"[{text}]({elem.get('href', '#')})"

    # Imágenes
    if tag == "img":
        src = elem.get("src", "")
        alt = elem.get("alt", "")
        img_name = os.path.basename(src.split("=")[0]) + ".png"
        local_img_path = os.path.join(STATIC_IMG_DIR, img_subfolder, img_name)
        download_image(src, local_img_path)
        return f"![{alt}](/img/{img_subfolder}/{img_name})"

    return text

def html_to_md(html_data, img_subfolder):
    """Convierte HTML a Markdown"""
    soup = BeautifulSoup(html_data, "lxml")
    md_lines = []

    for elem in soup.find_all([
        "h1","h2","h3","h4","h5","h6",
        "p","strong","em","b","i",
        "ol","ul","li",
        "blockquote","code","pre",
        "a","img","table","tr","th","td"
    ], recursive=True):

        # Tablas → Markdown
        if elem.name == "table":
            rows = elem.find_all("tr")
            if rows:
                headers = [cell.get_text(strip=True) for cell in rows[0].find_all(["th","td"])]
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in rows[1:]:
                    cells = [cell.get_text(strip=True) for cell in row.find_all(["th","td"])]
                    md_lines.append("| " + " | ".join(cells) + " |")
            continue

        md_text = element_to_md(elem, img_subfolder)
        if md_text:
            md_lines.append(md_text)

    return "\n\n".join(md_lines)

def get_drive_path(file_id):
    """Ruta desde carpeta raíz"""
    path_parts = []
    current_id = file_id
    while True:
        file = service.files().get(fileId=current_id, fields="id, name, parents").execute()
        if 'parents' not in file:
            break
        parent_id = file['parents'][0]
        if parent_id == FOLDER_ID:
            break
        parent_file = service.files().get(fileId=parent_id, fields="id, name, parents").execute()
        path_parts.insert(0, parent_file['name'])
        current_id = parent_file['id']
    return path_parts

def ensure_category_json(folder_path, label):
    """Crea _category_.json"""
    path_json = os.path.join(folder_path, "_category_.json")
    if not os.path.exists(path_json):
        data = {
            "label": label,
            "position": 0,
            "link": {
                "type": "generated-index",
                "description": f"Sección: {label}"
            }
        }
        with open(path_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"📁 Creado _category_.json en {folder_path}")

def save_if_changed(path, content):
    """Solo guarda si hay cambios"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            if f.read().strip() == content.strip():
                print(f"⚡ Sin cambios: {path}")
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Guardado: {path}")
    return True

def process_folder(folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType)"
    ).execute()

    for item in results.get('files', []):
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            sub_path = get_drive_path(item['id'])
            local_folder = os.path.join(OUTPUT_DIR, *sub_path, item['name'])
            os.makedirs(local_folder, exist_ok=True)
            ensure_category_json(local_folder, item['name'])
            process_folder(item['id'])
        elif item['mimeType'] == 'application/vnd.google-apps.document':
            drive_path = get_drive_path(item['id'])
            local_folder = os.path.join(OUTPUT_DIR, *drive_path)
            os.makedirs(local_folder, exist_ok=True)
            if drive_path:
                ensure_category_json(local_folder, drive_path[-1])

            safe_name = item['name'].replace(" ", "_")
            md_path = os.path.join(local_folder, f"{safe_name}.md")
            img_subfolder = "/".join([*drive_path, safe_name])

            print(f"⬇ Descargando: {item['name']}")
            html_data = service.files().export(fileId=item['id'], mimeType='text/html').execute()
            md_content = html_to_md(html_data, img_subfolder)
            save_if_changed(md_path, md_content)

# ===== INICIO =====
os.makedirs(OUTPUT_DIR, exist_ok=True)
ensure_category_json(OUTPUT_DIR, "Documentación")
process_folder(FOLDER_ID)
print("🎉 Conversión completa con imágenes.")
