# 🚀 AirStore: AI Document Digitization to Google Sheets

![AirStore Banner](https://img.shields.io/badge/AirStore-Premium_Digitization-4F46E5?style=for-the-badge) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white) ![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white) 

**AirStore** is a modern, premium web application built to solve a very specific problem: **Automating the manual data entry of messy, handwritten ledgers into structured Google Sheets.** 

Using advanced multimodal LLMs (Google Gemini 1.5/2.5 Flash), AirStore can read messy handwriting in English, Hindi, and Marathi, translate it, format it, and sync it natively to your Google Drive. 

## ✨ Features 
- **Intelligent Handwriting Recognition:** Powered by Google's latest multimodal Gemini Flash models.
- **Multilingual Support:** Natively trained to decipher and translate localized scripts (Hindi & Marathi) into English data arrays.
- **Premium User Interface:** Dark-mode glassmorphism design built with Next.js, Framer Motion, and Tailwind CSS.
- **2-Step Verification:** Users visually confirm and edit the extracted tabular data *before* it gets pushed to production databases.
- **Headless Sync:** Direct OAuth 2.0 integration via Google Sheets API.

## 🛠️ Architecture 
1. **Frontend (`/frontend`)**: Next.js 15 (App Router Server Components + React Client Components), Tailwind v4, Axios, Framer Motion. 
2. **Backend (`/backend`)**: Python FastAPI server utilizing asynchronous file uploads, background processing, and temporary SQLite caching (`records.db`).
3. **AI Layer**: Google Generative AI (`gemini-2.5-flash`) leveraging strictly enforced JSON schema outputs.

---

## 💻 Local Setup & Installation

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- Google Cloud Platform Account (For Sheets API Service Account)
- Google AI Studio API Key (For Gemini)

### 1. Backend Setup
Navigate to the backend directory and set up your Python environment:
```bash
cd backend
pip install -r requirements.txt
```
Copy your Google Service Account JSON to `backend/credentials.json`.
Then, create a `.env` file inside the `backend/` directory:
```env
# backend/.env
GEMINI_API_KEY="your_api_key_here"
GOOGLE_APPLICATION_CREDENTIALS="credentials.json"
GOOGLE_SHEET_ID="your_google_sheet_id_from_url"
```

Start the FastAPI server:
```bash
uvicorn main:app --reload
```
*The API will run on `http://127.0.0.1:8000`*

### 2. Frontend Setup
Navigate to the frontend directory:
```bash
cd frontend
npm install
npm run dev
```
*The web app will run on `http://localhost:3000`*

---

## 🔒 Security & Data Privacy
- Uploaded ledger images are processed strictly in-memory or immediately purged from the `backend/` filesystem after the Gemini API finishes inference.
- The `.gitignore` at the project root aggressively prevents tracking of `.env` secret variables, `.db` caches, and raw `credentials.json` keystores.
