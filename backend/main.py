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
from services.sheets_service import append_to_sheet

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
             
        append_to_sheet(sheet_id, "Sheet1!A:D", sheet_rows)
        
        # Mark as confirmed
        cursor.execute("UPDATE records SET status = 'CONFIRMED', data = ? WHERE id = ?", (json.dumps(verified_data), record_id))
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": "Data saved to Google Sheets"}
        
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
async def receive_whatsapp_message(request: Request):
    """
    Meta sends POST requests here whenever someone messages the WhatsApp bot.
    """
    body = await request.json()
    print("Incoming WhatsApp Event:", body)
    
    # We will build out the extraction logic here after we verify the webhook!
    return {"status": "success"}
