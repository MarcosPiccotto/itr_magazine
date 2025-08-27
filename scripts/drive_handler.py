import os
import json
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from mdx_converter import convert_html_to_mdx_final, get_document_sample, get_first_image_url, save_if_changed
from datetime import datetime

def get_drive_service(service_account_file, scopes):
    """Configura y retorna el servicio de Google Drive."""
    try:
        creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return None

def ensure_directory(path):
    """Crea un directorio si no existe."""
    os.makedirs(path, exist_ok=True)

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

def load_image_cache(file_path):
    """Carga el registro de imágenes desde un archivo JSON."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_image_cache(file_path, cache):
    """Guarda el registro de imágenes en un archivo JSON."""
    with open(file_path, 'w') as f:
        json.dump(cache, f, indent=4)

def download_image_utility(url, local_path):
    """Descarga una imagen solo si no existe localmente (función auxiliar para este módulo)."""
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

def detect_language_from_name(name):
    base, ext = os.path.splitext(name)
    return "en" if base.endswith("_en") else "es"

def process_drive_folder(service, folder_id, output_docs_dir, output_static_img_dir, output_translated_dir, image_cache_file, path_parts=[]):
    """Recorre de forma recursiva una carpeta de Google Drive, con soporte para .docx."""
    image_cache = load_image_cache(image_cache_file)
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
    except Exception as e:
        print(f"❌ Error al listar archivos de la carpeta {folder_id}: {e}")
        return

    for item in results.get('files', []):
        item_name = item['name']
        item_mime = item['mimeType']
        item_id = item['id']
        item_lang = detect_language_from_name(item_name)
        
        if item_mime == 'application/vnd.google-apps.folder':
            current_path = os.path.join(output_docs_dir, *path_parts, item_name)
            ensure_directory(current_path)
            create_category_json(current_path, item_name)
            process_drive_folder(service, item_id, output_docs_dir, output_static_img_dir, image_cache_file, path_parts + [item_name])
            
        elif item_mime in ['application/vnd.google-apps.document', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            
            doc_id_to_process = item_id
            
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

            output_dir = output_docs_dir if item_lang == 'es' else output_translated_dir
            doc_path = os.path.join(output_dir, *path_parts)
            ensure_directory(doc_path)
            
            safe_name = item_name.replace(" ", "-").replace("/", "-").lower()
            if safe_name.endswith('.docx'):
                safe_name = safe_name.replace('.docx', '')
            if safe_name.endswith('_en'):
                safe_name = safe_name[:-3]
            
            mdx_path = os.path.join(doc_path, f"{safe_name}.mdx")
            img_subfolder = "/".join(path_parts + [safe_name])

            try:
                print(f"⬇️ Descargando documento: {item_name}")
                html_data = service.files().export(fileId=doc_id_to_process, mimeType='text/html').execute()
                
                mdx_content = convert_html_to_mdx_final(html_data, img_subfolder, image_cache, output_static_img_dir)
                doc_sample = get_document_sample(html_data)

                first_img_url = get_first_image_url(html_data)
                
                # --- INICIO DE LA MODIFICACIÓN ---
                relative_image_path = 'default_thumbnail.png' # Imagen por defecto (debe estar en static/img/)
                if first_img_url:
                    img_hash = abs(hash(first_img_url)) % (10**8)
                    img_name = f"img_{img_hash}.png"
                    local_img_path = os.path.join(output_static_img_dir, img_subfolder, img_name)
                    if download_image_utility(first_img_url, local_img_path):
                        # Se guarda solo la ruta relativa, sin el '/img/'
                        relative_image_path = f"{img_subfolder}/{img_name}"

                # Se formatea la fecha a YYYY-MM-DD
                date_iso = datetime.fromisoformat(item['modifiedTime'].replace("Z", "+00:00"))
                formatted_date = date_iso.strftime('%Y-%m-%d')
                item_title = item_name if item_lang == 'es' else item_name[:-3]
                        
                frontmatter = f"""---
title: "{item_title}"
description: "{doc_sample}"
date: '{formatted_date}'
sidebar_position: 1
image: '{relative_image_path}'
---

import ColorText from '@site/src/components/ColorText';
import VideoPlayer from '@site/src/components/VideoPlayer';

"""
                # --- FIN DE LA MODIFICACIÓN ---

                save_if_changed(mdx_path, frontmatter + mdx_content)
            except Exception as e:
                print(f"❌ Error al procesar documento {item_name}: {e}")
            
            if item_mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                 try:
                    service.files().delete(fileId=doc_id_to_process).execute()
                    print(f"🗑️ Eliminado archivo temporal de Google Doc para {item_name}")
                 except Exception as e:
                    print(f"⚠️ No se pudo eliminar el archivo temporal para {item_name}: {e}")

    save_image_cache(image_cache_file, image_cache)