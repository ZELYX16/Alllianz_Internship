from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import csv
import os
import ollama
from ollama import AsyncClient

app = FastAPI()

class InferenceRequest(BaseModel):
    prompt: str
    model: str = "mistral" # Default fallback
    temperature: float = 0.7
    num_predict: int = 512
    num_ctx: int = 2048
    repeat_penalty: float = 1.1
    top_k: int = 40
    top_p: float = 0.9

LOG_FILE = "llm_logs.csv"

#function for logging data to csv
def log_to_csv(log_data: dict):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=log_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_data)

#Endpoint to generater response
@app.post("/generate")
async def run_inference(data: InferenceRequest):

    #Start time for calculating the elapsed time.
    start_time = time.time()
    
    try:
        response = await AsyncClient().generate(
            model=data.model,
            prompt=data.prompt,
            options={
                "temperature": data.temperature,
                "num_predict": data.num_predict,
                "num_ctx": data.num_ctx,
                "repeat_penalty": data.repeat_penalty,
                "top_k": data.top_k,
                "top_p": data.top_p
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama generation failed: {str(e)}")

    elapsed_time = time.time() - start_time
    
    input_tokens = response.get("prompt_eval_count", 0)
    output_tokens = response.get("eval_count", 0)
    tps = output_tokens / elapsed_time if elapsed_time > 0 else 0

    log_entry = {
        "Input_Tokens": input_tokens,
        "Output_Tokens": output_tokens,
        "Elapsed_Time_sec": round(elapsed_time, 2),
        "Inference_Cost": 0.00
    }
    
    log_to_csv(log_entry)

    return {
        "response": response.get('response', '').strip(),
        "metrics": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed_time": elapsed_time,
            "tps": tps,
            "cost": 0.00
        }
    }