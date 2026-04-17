import os
import uuid
import base64
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chromadb
from processor import get_page_analysis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("screenshots", exist_ok=True)
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="semantic_history")

class IngestPayload(BaseModel):
    url: str
    title: str
    text_content: str
    base64_image: str

@app.post("/ingest")
def ingest_page(payload: IngestPayload):
    try:
        # Strip data URL prefix if present
        b64_data = payload.base64_image
        if "," in b64_data:
            b64_data = b64_data.split(",")[1]
            
        print(f"Ingesting: {payload.url}")
        
        # 1. Analyze with Gemini
        description = get_page_analysis(
            url=payload.url,
            text_content=payload.text_content,
            base64_image_data=b64_data
        )
        print("Obtained Gemini analysis.")
        
        doc_id = str(uuid.uuid4())
        
        # 2. Save screenshot to disk
        screenshot_path = os.path.join("screenshots", f"{doc_id}.jpg")
        with open(screenshot_path, "wb") as fh:
            fh.write(base64.b64decode(b64_data))
            
        screenshot_url = f"http://localhost:8000/screenshots/{doc_id}.jpg"
        
        # 3. Store in Vector DB
        collection.add(
            documents=[description],
            metadatas=[{
                "url": payload.url,
                "title": payload.title,
                "screenshot": screenshot_url,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": description
            }],
            ids=[doc_id]
        )
        
        print(f"Successfully indexed {payload.url}")
        return {"status": "success", "id": doc_id}
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search_history(q: str, limit: int = 10):
    try:
        results = collection.query(
            query_texts=[q],
            n_results=limit
        )
        
        formatted_results = []
        if results['metadatas'] and len(results['metadatas']) > 0:
            for i, meta in enumerate(results['metadatas'][0]):
                # ChromaDB also returns distances, we could add them
                formatted_results.append(meta)
                
        return {"results": formatted_results}
    except Exception as e:
        print(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
