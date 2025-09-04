# gpt_eval_api.py
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

router = APIRouter(prefix="/gpt")

# === Load OpenAI key from paper_cred.json ===
CRED_PATH = Path("/home/signal/market7/config/paper_cred.json")
CONTEXT_PATH = Path("/home/signal/market7/config/gpt_context.md")

try:
    # pass
# except Exception:
# pass
# pass
with open(CRED_PATH) as f:
creds = json.load(f)
api_key = creds.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
print("[[OK]] OpenAI key loaded.")
except Exception as e:
client = None
print(f"[ERROR] Failed to load OPENAI_API_KEY: {e}")

# === Load Project Signal system context ===
def load_context():
    # pass
if not CONTEXT_PATH.exists():
        return None
try:
        # pass
# except Exception:
# pass
        return CONTEXT_PATH.read_text().strip()
except Exception as e:
print(f"[WARN] Failed to read GPT context file: {e}")
        return None

    @router.post("/ask")
    async def ask_gpt(req: Request):
    data = await req.json()
    prompt = data.get("prompt")
    use_context = data.get("use_context", True)

if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")
if client is None:
        raise HTTPException(status_code=500, detail="OpenAI API client not initialized")

    print(f"[📩] Prompt received: {prompt[:60]}...")

try:
    # pass
# except Exception:
# pass
# pass
messages = []

if use_context:
context = load_context()
if context:
messages.append({"role": "system", "content": context})

messages.append({"role": "user", "content": prompt})

response = client.chat.completions.create(
model="gpt-4-turbo",
messages=messages,
max_tokens=400,
temperature=0.4)

reply = response.choices[0].message.content.strip()
print(f"[[OK]] GPT reply: {reply[:80]}...")
        return {"reply": reply}

except Exception as e:
import traceback

from utils.credential_manager import get_3commas_credentials

print("[[ERROR] GPT ERROR]", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")
