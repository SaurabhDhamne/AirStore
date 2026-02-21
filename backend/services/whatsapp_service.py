import os
import requests
import uuid

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

def get_media_url(media_id: str) -> str:
    """
    Calls WhatsApp Cloud API to get the temporary download URL for an image.
    """
    if not WHATSAPP_ACCESS_TOKEN:
        print("ERROR: WHATSAPP_ACCESS_TOKEN not set!")
        return ""
        
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("url")
    else:
        print("Failed to get media URL:", response.text)
        return ""

def download_media(media_url: str) -> str:
    """
    Downloads the actual binary image from Meta's servers.
    """
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    response = requests.get(media_url, headers=headers)
    
    if response.status_code == 200:
        file_path = f"temp_wa_{uuid.uuid4().hex}.jpg"
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    else:
        print("Failed to download media:", response.text)
        return ""

def send_whatsapp_message(to_number: str, message: str):
    """
    Sends a text message back to the user via WhatsApp.
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        print("ERROR: Missing WhatsApp credentials for sending message.")
        return
        
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Failed to send WhatsApp message:", response.text)

def upload_whatsapp_media(file_path: str, mime_type: str) -> str:
    """
    Uploads a local file to Meta's servers to get a media_id for sending.
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        print("ERROR: Missing WhatsApp credentials for uploading media.")
        return ""
        
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/media"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        data = {"messaging_product": "whatsapp"}
        response = requests.post(url, headers=headers, data=data, files=files)
        
    if response.status_code == 200:
        return response.json().get("id")
    else:
        print("Failed to upload media to WhatsApp:", response.text)
        return ""

def send_whatsapp_document(to_number: str, media_id: str, filename: str, caption: str = ""):
    """
    Sends a document message (like an Excel file) to the user.
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        print("ERROR: Missing WhatsApp credentials for sending document.")
        return
        
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": caption,
            "filename": filename
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Failed to send WhatsApp document:", response.text)
