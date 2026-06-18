from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tiktoken

# Import your custom data mapping
from Data import ENCODING_MAP, PRICE_MAP, fetch_realtime_pricing

app = FastAPI(title="Tokenizer API")

# 1. Initialize pricing on server startup
active_prices = PRICE_MAP.copy()
live_price_data = fetch_realtime_pricing(ENCODING_MAP.keys())

if live_price_data:
    active_prices.update(live_price_data)
    print("Live pricing updated successfully.")
else:
    print("Running with default offline pricing schema.")

#database for CRUD operations
db_history = []

class TokenizeRequest(BaseModel):
    text: str
    model: str

@app.get("/models")
def get_models():
    """Provides the frontend with the list of available models."""
    return {"models": list(ENCODING_MAP.keys())}

@app.post("/tokenize")
def tokenize_text(payload: TokenizeRequest):
    if payload.model not in ENCODING_MAP:
        raise HTTPException(status_code=400, detail="Invalid model selected")
    
    try:
        #calculation logic
        encoding = tiktoken.encoding_for_model(payload.model)
        tokens = encoding.encode(payload.text)
        num_tokens = len(tokens)
        
        #Total cost calculation
        cost_per_token = active_prices.get(payload.model, {}).get("input", 0)
        total_cost = cost_per_token * num_tokens
        
        # Save to CRUD history
        record = {
            "id": len(db_history) + 1,
            "text": payload.text[:50] + "...", # Storing a snippet to save memory
            "model": payload.model,
            "token_count": num_tokens,
            "cost": round(total_cost, 8)
        }
        db_history.append(record)
        return record
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    return {"history": db_history}

@app.delete("/history/{item_id}")
def delete_history(item_id: int):
    for i, record in enumerate(db_history):
        if record["id"] == item_id:
            deleted_record = db_history.pop(i)
            return {"message": "Record deleted", "record": deleted_record}
    raise HTTPException(status_code=404, detail="Record not found")