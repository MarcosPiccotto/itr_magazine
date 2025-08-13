import os
import json
import requests
import re
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2 import service_account

# =========================================================
# CONFIGURACIÓN
# =========================================================
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'driveCredentials.json'
ROOT_FOLDER_ID = '1uz-MJd-7stYBuNF-fHyOBOhHof0xSYa-'
OUTPUT_DOCS_DIR = './docs'
OUTPUT_STATIC_IMG_DIR = './static/img'
IMAGE_CACHE_FILE = 'image_cache.json'

# =========================================================
# AUTENTICACIÓN Y SERVICIO
# =========================================================
def get_drive_service():
    """Configura y retorna el servicio de Google Drive."""
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return None

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def ensure_directory(path):
    """Crea un directorio si no existe."""
    os.makedirs(path, exist_ok=True)

def load_image_cache():
    """Carga el registro de imágenes desde un archivo JSON."""
    if os.path.exists(IMAGE_CACHE_FILE):
        with open(IMAGE_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_image_cache(cache):
    """Guarda el registro de imágenes en un archivo JSON."""
    with open(IMAGE_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

def download_image(url, local_path):
    """Descarga una imagen solo si no existe localmente."""
    ensure_directory(os.path.dirname(local_path))
    if not os.path.exists(local_path):
        try:
            r = requests.get(url, stream=True, timeout=10)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                print(f"🖼️ Guardada imagen: {local_path}")
                return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al descargar imagen de {url}: {e}")
    return False

def create_category_json(folder_path, label):
    """Crea o actualiza _category_.json solo si hay cambios."""
    path_json = os.path.join(folder_path, "_category_.json")
    
    new_data = {
        "label": label,
        "position": 0,
        "link": {
            "type": "generated-index",
            "description": f"Contenido de {label}"
        }
    }
    
    if os.path.exists(path_json):
        with open(path_json, 'r', encoding='utf-8') as f:
            try:
                current_data = json.load(f)
                if current_data == new_data:
                    print(f"⚡ Sin cambios en _category_.json en {folder_path}")
                    return
            except json.JSONDecodeError:
                pass

    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print(f"📁 Creado/Actualizado _category_.json en {folder_path}")

def save_if_changed(file_path, content):
    """Guarda el archivo solo si su contenido ha cambiado."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            if f.read().strip() == content.strip():
                print(f"⚡ Sin cambios: {file_path}")
                return False
    
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Guardado: {file_path}")
    return True

# =========================================================
# CONVERSIÓN DE HTML A MDX
# =========================================================
def convert_to_mdx(element, img_subfolder, image_cache):
    """Convierte un elemento HTML y sus hijos a MDX, gestionando el registro de imágenes."""
    md_content = ""
    if element.name is None:
        return element.string if element.string else ""
    
    # Manejar elementos de bloque
    if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        text = element.get_text(strip=True)
        return f"{'#' * int(element.name[1])} {text}\n"
    elif element.name == "p":
        content = "".join([convert_to_mdx(child, img_subfolder, image_cache) for child in element.children])
        return f"{content}\n"
    elif element.name == "blockquote":
        text = element.get_text(strip=True)
        return f"> {text}\n"
    elif element.name in ["ul", "ol"]:
        list_items = ""
        for li in element.find_all("li", recursive=False):
            prefix = "- " if element.name == "ul" else f"{element.find_all('li', recursive=False).index(li) + 1}. "
            list_items += f"{prefix}{''.join([convert_to_mdx(child, img_subfolder, image_cache) for child in li.children])}\n"
        return list_items
    elif element.name == "table":
        return process_table(element)
    elif element.name == "img":
        src = element.get("src", "")
        alt = element.get("alt", "")
        
        if src in image_cache:
            img_name = image_cache[src]
            print(f"⚡ Imagen ya en caché: {img_name}")
        else:
            img_hash = abs(hash(src)) % (10**8)
            img_name = f"img_{img_hash}.png"
            local_img_path = os.path.join(OUTPUT_STATIC_IMG_DIR, img_subfolder, img_name)
            download_image(src, local_img_path)
            image_cache[src] = img_name
        
        return f"![{alt}](/img/{img_subfolder}/{img_name})\n"
    
    # Manejar elementos de texto en línea
    elif element.name == "a":
        text = element.get_text(strip=True)
        url = element.get('href', '#')
        return f"[{text}]({url})"
    elif element.name in ["strong", "b"]:
        return f"**{''.join([convert_to_mdx(child, img_subfolder, image_cache) for child in element.children])}**"
    elif element.name in ["em", "i"]:
        return f"*_{''.join([convert_to_mdx(child, img_subfolder, image_cache) for child in element.children])}_*"
    elif element.name == "span" and element.has_attr("style"):
        color_code_match = re.search(r"color:\s*([^;]+)", element["style"])
        if color_code_match:
            color_code = color_code_match.group(1).strip()
            content = "".join([convert_to_mdx(child, img_subfolder, image_cache) for child in element.children])
            return f"<ColorText color=\"{color_code}\">{content}</ColorText>"
    
    # Si el elemento no es reconocido, procesar sus hijos
    return "".join([convert_to_mdx(child, img_subfolder, image_cache) for child in element.children])

def process_table(table_tag):
    """Convierte una tabla HTML a Markdown."""
    rows = table_tag.find_all("tr")
    if not rows:
        return ""
    
    md_lines = []
    
    headers = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for row in rows[1:]:
        cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
        md_lines.append("| " + " | ".join(cells) + " |")
        
    return "\n".join(md_lines) + "\n"

def convert_html_to_mdx_final(html_data, img_subfolder, image_cache):
    """Punto de entrada principal para la conversión de HTML a MDX."""
    soup = BeautifulSoup(html_data, "lxml")
    mdx_content_parts = []
    
    for element in soup.body.find_all(True, recursive=False):
        mdx_content = convert_to_mdx(element, img_subfolder, image_cache)
        if mdx_content:
            mdx_content_parts.append(mdx_content)
            
    return "\n".join(mdx_content_parts)

# =========================================================
# PROCESAMIENTO DE ARCHIVOS EN GOOGLE DRIVE
# =========================================================
def process_drive_folder(service, folder_id, path_parts=[]):
    """Recorre de forma recursiva una carpeta de Google Drive, con soporte para .docx."""
    image_cache = load_image_cache()
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)"
        ).execute()
    except Exception as e:
        print(f"❌ Error al listar archivos de la carpeta {folder_id}: {e}")
        return

    for item in results.get('files', []):
        item_name = item['name']
        item_mime = item['mimeType']
        item_id = item['id']
        
        if item_mime == 'application/vnd.google-apps.folder':
            current_path = os.path.join(OUTPUT_DOCS_DIR, *path_parts, item_name)
            ensure_directory(current_path)
            create_category_json(current_path, item_name)
            process_drive_folder(service, item_id, path_parts + [item_name])
            
        elif item_mime in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            
            doc_id_to_process = item_id
            
            # Convierte .docx a Google Doc si es necesario
            if item_mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                try:
                    print(f"🔄 Convirtiendo .docx a Google Doc: {item_name}")
                    converted_file = service.files().copy(
                        fileId=item_id,
                        body={'name': item_name, 'mimeType': 'application/vnd.google-apps.document'}
                    ).execute()
                    doc_id_to_process = converted_file['id']
                except Exception as e:
                    print(f"❌ Error al convertir .docx {item_name}: {e}")
                    continue

            doc_path = os.path.join(OUTPUT_DOCS_DIR, *path_parts)
            ensure_directory(doc_path)
            
            safe_name = item_name.replace(" ", "-").replace("/", "-").lower()
            if safe_name.endswith('.docx'):
                safe_name = safe_name.replace('.docx', '')
            
            mdx_path = os.path.join(doc_path, f"{safe_name}.mdx")
            img_subfolder = "/".join(path_parts + [safe_name])

            try:
                print(f"⬇️ Descargando documento: {item_name}")
                html_data = service.files().export(fileId=doc_id_to_process, mimeType='text/html').execute()
                mdx_content = convert_html_to_mdx_final(html_data, img_subfolder, image_cache)
                
                frontmatter = f"""---
title: {item_name}
sidebar_position: 1
---

import ColorText from '@site/src/components/ColorText';

"""
                save_if_changed(mdx_path, frontmatter + mdx_content)
            except Exception as e:
                print(f"❌ Error al procesar documento {item_name}: {e}")
            
            # Elimina el archivo temporal de Google Doc si fue creado
            if item_mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                 try:
                    service.files().delete(fileId=doc_id_to_process).execute()
                    print(f"🗑️ Eliminado archivo temporal de Google Doc para {item_name}")
                 except Exception as e:
                    print(f"⚠️ No se pudo eliminar el archivo temporal para {item_name}: {e}")

    save_image_cache(image_cache)
# =========================================================
# INICIO DEL SCRIPT
# =========================================================
if __name__ == "__main__":
    drive_service = get_drive_service()
    if drive_service:
        ensure_directory(OUTPUT_DOCS_DIR)
        create_category_json(OUTPUT_DOCS_DIR, "Revista del Colegio")
        print("🚀 Iniciando sincronización de Google Drive a Docusaurus...")
        process_drive_folder(drive_service, ROOT_FOLDER_ID)
        print("🎉 Conversión y sincronización completa.")