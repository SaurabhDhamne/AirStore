import os
import sqlite3
import uuid
import json
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Explicitly load environment variables from the absolute path of the backend directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

from services.gemini_service import init_gemini, extract_ledger_data
from services.sheets_service import append_to_sheet, create_and_append_sheet, export_sheet_to_xlsx
from services.whatsapp_service import get_media_url, download_media, send_whatsapp_message, upload_whatsapp_media, send_whatsapp_document
import datetime

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "airstore_secure_token_123")

# Initialize Gemini
init_gemini()

app = FastAPI(title="Handwritten Records to Google Sheets API")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL (e.g., http://localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "records.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            data TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"message": "Handwritten Records API is running"}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Receives an image, extracts data via Gemini, and stores it as PENDING.
    """
    # 1. Save uploaded file temporarily
    file_id = str(uuid.uuid4())
    temp_path = f"temp_{file_id}_{file.filename}"
    
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # 2. Process with Gemini
        extracted_data = extract_ledger_data(temp_path)
        
        # 3. Handle invalid images
        if not extracted_data.get("is_valid_ledger"):
             # Clean up
             os.remove(temp_path)
             return {"status": "error", "message": extracted_data.get("error_message")}
        
        # 4. Save to DB temporarily
        record_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO records (id, data, status) VALUES (?, ?, ?)", 
                       (record_id, json.dumps(extracted_data), "PENDING"))
        conn.commit()
        conn.close()
        
        # 5. Clean up local image file (Security/Privacy)
        os.remove(temp_path)
        
        return {
            "status": "success",
            "record_id": record_id,
            "data": extracted_data
        }
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/record/{record_id}")
def get_record(record_id: str):
    """
    Fetches a pending record for the frontend confirmation screen.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data, status FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")
        
    return {"record_id": record_id, "status": row[1], "data": json.loads(row[0])}

@app.post("/confirm/{record_id}")
def confirm_record(record_id: str, verified_data: dict):
    """
    Receives confirmed and potentially edited data from the user and appends to Google Sheets.
    """
    # Verify record is PENDING
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    
    if not row:
         conn.close()
         raise HTTPException(status_code=404, detail="Record not found")
         
    if row[0] == "CONFIRMED":
         conn.close()
         raise HTTPException(status_code=400, detail="Record already confirmed")
         
    # Format data for Sheets
    entries = verified_data.get("entries", [])
    if not entries:
        conn.close()
        raise HTTPException(status_code=400, detail="No entries provided to save")
        
    sheet_rows = []
    for entry in entries:
        sheet_rows.append([
            str(entry.get("date", "")),
            str(entry.get("name", "")),
            str(entry.get("amount", "")),
            str(entry.get("status", ""))
        ])
        
    try:
        # Get Sheet ID from env or frontend payload
        # For this prototype we will use an env variable
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id:
             raise ValueError("GOOGLE_SHEET_ID not set")
             
        timestamp_str = datetime.datetime.now().strftime("%Y-%b-%d_%H%M")
        new_tab_name = f"WebLog_{timestamp_str}"
        
        # Create a new tab uniquely for this web upload
        new_gid = create_and_append_sheet(sheet_id, new_tab_name, sheet_rows)
        
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={new_gid}"
        
        # Mark as confirmed
        cursor.execute("UPDATE records SET status = 'CONFIRMED', data = ? WHERE id = ?", (json.dumps(verified_data), record_id))
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Data saved to unique Google Sheets tab", "sheet_url": sheet_url, "entries": entries}
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# WHATSAPP WEBHOOK INTEGRATION
# ==========================================

from fastapi import Request
from fastapi.responses import PlainTextResponse

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta uses this endpoint to verify that you actually own this webhook URL.
    It sends a GET request with hub.mode, hub.challenge, and hub.verify_token.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Verification failed")
    
    raise HTTPException(status_code=400, detail="Bad Request")

@app.post("/webhook")
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    """
    Meta sends POST requests here whenever someone messages the WhatsApp bot.
    """
    body = await request.json()
    
    # 1. Parse incoming message structure
    try:
        entries = body.get("entry", [])
        if not entries: return {"status": "success"}
        
        changes = entries[0].get("changes", [])
        if not changes: return {"status": "success"}
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        if not messages: return {"status": "success"} # Could be a status update (read/delivered)
        
        message = messages[0]
        sender_phone = message.get("from")
        msg_type = message.get("type")
        
        if msg_type != "image":
            # Just reply saying we only accept images for now
            background_tasks.add_task(send_whatsapp_message, sender_phone, "👋 Welcome to AirStore! Please send a clear photo of your handwritten ledger/record to automatically digitize it into Google Sheets.")
            return {"status": "success"}
            
        print(f"Received Image from {sender_phone}...")
        image_data = message.get("image", {})
        media_id = image_data.get("id")
        
        # We process the heavy extraction in the background to not timeout Meta's webhook
        background_tasks.add_task(process_whatsapp_image, media_id, sender_phone)
        
    except Exception as e:
        print("Webhook Error:", e)
        
    return {"status": "success"}

def process_whatsapp_image(media_id: str, sender_phone: str):
    """
    Background worker to download, extract, and push the image to Sheets.
    """
    try:
        # A. Send "Processing" message
        send_whatsapp_message(sender_phone, "⏳ Extracting your ledger with AirStore AI... Please wait a moment.")
        
        # B. Download Media
        media_url = get_media_url(media_id)
        if not media_url: raise ValueError("Could not get media URL")
        
        local_image_path = download_media(media_url)
        if not local_image_path: raise ValueError("Could not download image")
        
        try:
            # C. Extract Data via Gemini
            extracted_data = extract_ledger_data(local_image_path)
            
            if not extracted_data.get("is_valid_ledger"):
                send_whatsapp_message(sender_phone, f"❌ Validation failed: {extracted_data.get('error_message')}")
                return
                
            entries = extracted_data.get("entries", [])
            if not entries:
                send_whatsapp_message(sender_phone, "⚠️ Could not find any valid entries in the image.")
                return
                
            # D. Push to Google Sheets in a NEW Tab
            sheet_rows = []
            for entry in entries:
                sheet_rows.append([
                    str(entry.get("date", "")),
                    str(entry.get("name", "")),
                    str(entry.get("amount", "")),
                    str(entry.get("status", ""))
                ])
                
            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            timestamp_str = datetime.datetime.now().strftime("%Y-%b-%d_%H%M")
            new_tab_name = f"Log_{timestamp_str}"
            
            # Create tab and append rows
            create_and_append_sheet(sheet_id, new_tab_name, sheet_rows)
            
            # E. Export the entire requested sheet (now with new tab) as Excel
            send_whatsapp_message(sender_phone, "📥 Data extracted! Downloading updated Excel file directly from Google Sheets...")
            
            excel_path = f"AirStore_Ledger_{timestamp_str}.xlsx"
            export_sheet_to_xlsx(sheet_id, excel_path)
            
            # F. Upload Media to WhatsApp Meta API
            media_id = upload_whatsapp_media(excel_path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if not media_id:
                raise ValueError("Failed to upload Excel file to WhatsApp")
            
            # G. Send Document
            total_items = len(entries)
            total_amount = sum([float(str(e.get("amount", 0)).replace(',','')) for e in entries if str(e.get("amount", 0)).replace(',','').replace('.','').isdigit()])
            caption = f"✅ *Extraction Complete!*\n\nProcessed {total_items} entries (Total: {total_amount}).\n\nHere is your full updated Google Sheet file."
            
            send_whatsapp_document(sender_phone, media_id, excel_path, caption)
            
        finally:
            # Always clean up temporary images and generated excel files
            if os.path.exists(local_image_path):
                os.remove(local_image_path)
            if 'excel_path' in locals() and os.path.exists(excel_path):
                os.remove(excel_path)
                
    except Exception as e:
        print("Processing Error:", e)
        send_whatsapp_message(sender_phone, "⚠️ Sorry, an error occurred while processing your image. Please try again.")
