import os
import json
import typing_extensions as typing
import google.generativeai as genai
from pydantic import BaseModel, Field

class HandWrittenEntry(BaseModel):
    date: str = Field(description="The date of the entry, if available. Use N/A if missing.")
    name: str = Field(description="The name of the item, person, or description. Translate to English if written in Hindi or Marathi, but keep the original intent.")
    amount: float = Field(description="The numerical amount or quantity.")
    status: str = Field(description="Any status, notes, or remarks. Translate to English if written in Hindi or Marathi.")

class LedgerExtraction(BaseModel):
    is_valid_ledger: bool = Field(description="True if the image contains a handwritten ledger or list of records. False if it's a random image like a dog or landscape.")
    error_message: str = Field(description="If is_valid_ledger is false, explain why. Otherwise, leave empty.")
    entries: list[HandWrittenEntry] = Field(description="The list of extracted entries.")

def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "":
        raise ValueError("GEMINI_API_KEY is missing! Please paste your key inside the d:\\AirStore\\backend\\.env file and restart the server.")
    genai.configure(api_key=api_key)

def extract_ledger_data(image_path: str) -> dict:
    """
    Extracts structured data from a handwritten ledger image using Gemini 2.5 Flash.
    Supports English, Hindi, and Marathi handwriting.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # Upload the file to the Gemini API (better for images)
    sample_file = genai.upload_file(path=image_path)
    
    prompt = (
        "You are an expert data entry assistant. "
        "Read the attached handwritten log/ledger. The writing might be in English, Hindi, or Marathi. "
        "Extract the Date, Name/Description, Amount/Quantity, and Status. "
        "If the handwritten text is in Hindi or Marathi, please accurately translate the meaning to English for the final JSON. "
        "If the image is not a ledger or list of records, set is_valid_ledger to false and provide an error message."
    )
    
    # Requesting structured output native to the Gemini API
    response = model.generate_content(
        [prompt, sample_file],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=LedgerExtraction,
            temperature=0.1
        )
    )
    
    # Clean up the uploaded file from Google's servers
    genai.delete_file(sample_file.name)
    
    # The response should strictly be the JSON string matching our schema
    return json.loads(response.text)
