from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import whisper
from transformers import pipeline
import os

app = FastAPI()

# Initialize Whisper model
whisper_model = whisper.load_model("large-v2")

# Initialize summarization model
summarizer = pipeline("summarization")

# Directory to save results
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

async def transcribe_audio(file_path: str) -> str:
    try:
        result = whisper_model.transcribe(file_path)
        return result['text']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

def summarize_text(text: str) -> str:
    try:
        summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

def extract_timestamps(transcription: str, interval: int = 60) -> list:
    timestamps = []
    words = transcription.split()
    num_words = len(words)
    for i in range(0, num_words, interval):
        timestamps.append((i, ' '.join(words[i:i+interval])))
    return timestamps

def save_results(filename: str, transcription: str, summary: str, timestamps: list):
    try:
        base_path = os.path.join(RESULTS_DIR, filename)
        with open(f"{base_path}_transcription.txt", "w") as f:
            f.write(transcription)
        with open(f"{base_path}_summary.txt", "w") as f:
            f.write(summary)
        with open(f"{base_path}_timestamps.txt", "w") as f:
            for timestamp in timestamps:
                f.write(f"{timestamp[0]}: {timestamp[1]}\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save results: {str(e)}")

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Convert to wav format if necessary
        audio = AudioSegment.from_file(file_location)
        wav_path = f"{file.filename}.wav"
        audio.export(wav_path, format="wav")

        # Transcribe the audio
        transcription = await transcribe_audio(wav_path)

        # Summarize the transcription
        summary = summarize_text(transcription)

        # Extract timestamps
        timestamps = extract_timestamps(transcription)

        # Save results
        save_results(file.filename, transcription, summary, timestamps)

        # Clean up temporary files
        os.remove(file_location)
        os.remove(wav_path)

        return JSONResponse(content={
            "transcription": transcription,
            "summary": summary,
            "timestamps": timestamps
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")
