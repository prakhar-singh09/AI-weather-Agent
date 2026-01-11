import os
import json
import time
import requests
from dotenv import load_dotenv

# --------------------------------------------------
# ENV
# --------------------------------------------------
load_dotenv()

MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# --------------------------------------------------
# TOOL
# --------------------------------------------------
def get_weather(city: str) -> str:
    url = f"https://wttr.in/{city.lower()}?format=%C+%t+Humidity:%h+Wind:%w"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return f"The weather in {city} is {r.text}"
    except Exception:
        pass
    return "Weather data unavailable."

TOOLS = {
    "get_weather": get_weather
}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def clean_json(text: str) -> str:
    """Remove markdown fences if model adds them"""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    return text

def call_llm(messages):
    headers = {
        "Authorization": f"Bearer {MODEL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.3,
        "top_p": 1,
        "stream": False
    }

    response = requests.post(
        MODEL_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return response.json()

# --------------------------------------------------
# SYSTEM PROMPT
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a step-based agent.

You MUST output ONLY raw JSON.
No markdown. No explanations. No extra text.

Allowed steps (strict order):
START → PLAN → TOOL → OUTPUT

JSON format:
{
  "step": "START | PLAN | TOOL | OUTPUT",
  "content": "string",
  "tool": "string (only for TOOL)"
}

Rules:
- One step per response
- TOOL must be followed by OUTPUT
- After TOOL_RESULT, OUTPUT is mandatory
- Never speak outside JSON

Tool input rules:
- For get_weather, the content MUST be a city name only
- Example valid inputs: "Kanpur", "Delhi", "Mumbai"
- Do NOT pass tool names, descriptions, or placeholders
- Extract the city name from the user query

Note:
- When Providing final OUTPUT, you can also suggest actions based on the weather.
"""



# --------------------------------------------------
# AGENT LOOP
# --------------------------------------------------
def run_agent():
  while True:  
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    history.append({"role": "user", "content": input("> ")})

    phase = "START"
    retries = 0
    MAX_RETRIES = 30
    while True:
        if retries >= MAX_RETRIES:
            print("❌ Too many retries. Aborting.")
            break

        try:
            response_json = call_llm(history)
        except Exception as e:
            print("⚠️ API error:", e)
            time.sleep(2)
            continue

        raw = response_json["choices"][0]["message"]["content"]
        print("\nRAW MODEL OUTPUT:")
        print(raw)

        if raw is None:
            retries += 1
            continue

        raw = clean_json(raw)

        if not raw.startswith("{"):
            retries += 1
            history.append({
                "role": "assistant",
                "content": "Respond ONLY with valid JSON."
            })
            continue

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            retries += 1
            history.append({
                "role": "assistant",
                "content": "Respond ONLY with valid JSON."
            })
            continue

        step = parsed.get("step")
        content = parsed.get("content")

        # -------- FSM ENFORCEMENT --------
        valid_next = {
            "START": ["START"],
            "PLAN": ["PLAN", "TOOL"],
            "TOOL": ["TOOL"],
            "OUTPUT": ["OUTPUT"]
        }

        if step not in valid_next.get(phase, []):
            retries += 1
            history.append({
                "role": "assistant",
                "content": "Follow the correct step order. Respond with valid JSON."
            })
            continue

        retries = 0
        history.append({"role": "assistant", "content": raw})

        # -------- HANDLE STEPS --------
        if step == "START":
            phase = "PLAN"
            print("🔥 START:", content)
            continue

        if step == "PLAN":
            phase = "PLAN"
            print("🧠 PLAN:", content)
            continue

        if step == "TOOL":
            phase = "OUTPUT"
            tool_name = parsed.get("tool")
            city = content.strip().split()[0].lower()

            print(f"🔧 TOOL CALL: {tool_name}({city})")

            if tool_name in TOOLS:
                result = TOOLS[tool_name](city)
            else:
                result = "Invalid tool."

            print("📡 TOOL RESULT:", result)

            history.append({
                "role": "assistant",
                "content": (
                    "TOOL_RESULT:\n"
                    f"{result}\n"
                    "Respond with OUTPUT step in JSON."
                )
            })
            continue

        if step == "OUTPUT":
            print("\n✅ FINAL OUTPUT:")
            print(content)
            break

# --------------------------------------------------
# ENTRY
# --------------------------------------------------
if __name__ == "__main__":
    run_agent()
