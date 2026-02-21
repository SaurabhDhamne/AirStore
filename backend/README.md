# Handwritten Records to Google Sheets - Backend

This backend is built with FastAPI. It handles image uploads, integrates with the Gemini API to extract handwritten lists (English, Hindi, Marathi), and connects to Google Sheets to save the confirmed data.

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   - Copy `.env.example` to `.env`.
   - Set `GEMINI_API_KEY` to your Gemini API key.
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the absolute path of your Google Cloud service account JSON file.
   - Set `GOOGLE_SHEET_ID` to the ID of the spreadsheet you want to log into (from its URL).

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

## User Flow
The process follows a two-step confirmation flow to ensure data accuracy before updating Google Sheets:

1. **Upload & Extract (Step 1)**
   - The user captures an image and uploads it via the frontend.
   - The frontend calls the backend `POST /upload`. 
   - The backend sends the image to Gemini. Gemini reads the image (in English, Marathi, or Hindi, automatically translating if instructed) and returns a JSON.
   - The backend temporarily saves this JSON in a local SQLite database with a state of "PENDING" and returns a `record_id` to the frontend.

2. **Review & Confirm (Step 2)**
   - The frontend displays the structured JSON to the user as a neat table.
   - The user verifies it for correctness and edits any mistakes.
   - The user clicks "Confirm". The frontend calls `POST /confirm/{record_id}` with the verified data.
   - The backend takes the final data, appends it to the Google Sheet, and marks the record as "CONFIRMED".
   - The Google Sheet is instantly updated!
