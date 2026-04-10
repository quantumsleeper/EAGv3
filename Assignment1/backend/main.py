from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import shutil
from processor import process_karaoke

app = FastAPI()

# Allow CORS since chrome extension will be calling this from a different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow any origin (the extension)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    url: str
    pitch_shift: int

def cleanup_files(directory: str):
    """Deletes temporary generated files after sending the response"""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    except Exception as e:
        print(f"Error cleaning up {directory}: {e}")

@app.post("/api/process")
async def process_media(req: ProcessRequest, background_tasks: BackgroundTasks):
    try:
        # Create a unique work directory for this request
        job_id = str(uuid.uuid4())
        work_dir = os.path.join(os.getcwd(), "temp_workspace", job_id)
        os.makedirs(work_dir, exist_ok=True)

        # Execute the pipeline (download -> spleeter -> pitch shift)
        output_file_path = process_karaoke(req.url, req.pitch_shift, work_dir)

        # After the file response is sent, cleanup the folder
        background_tasks.add_task(cleanup_files, work_dir)

        # Note: Return the path to the MP3, FastAPI will send it as a chunked download
        shift_str = f"_{req.pitch_shift}st" if req.pitch_shift != 0 else ""
        return FileResponse(
            path=output_file_path, 
            media_type='audio/mpeg', 
            filename=f"karaoke{shift_str}.mp3"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
