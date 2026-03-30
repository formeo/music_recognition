from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from music import MusicService

app = FastAPI()


class ProcessAudioRequest(BaseModel):
    file_path: str
    output_directory_path: str


@app.post("/process-audio")
async def process_audio(request: ProcessAudioRequest):
    """
    Обрабатывает POST-запрос для обработки директории.
    """
    file_path = request.file_path
    try:
        music_service = MusicService()
        music_service.convert_files_to_mp3(file_path)
        return {"message": "Directory processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
