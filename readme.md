# Weather Agent (FSM-based)

A step-based AI weather agent built in Python using:
- Finite State Machine (START → PLAN → TOOL → OUTPUT)
- Manual tool calling
- Open Source Model API
- Works best with LLAMA models bacause of LLaMA models respond better to hard constraints early.

## Setup

```bash
git clone https://github.com/prakhar-singh09/AI-weather-agent.git
cd weather-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables
Create a .env file:
- MODEL_API_KEY=your_api_key_here
- MODEL_URL=your_model_url
- MODEL_NAME=your_model_name

## Run 

python main.py

## Demo
https://github.com/prakhar-singh09/AI-weather-Agent/raw/main/Recording%202026-01-11%20225742.mp4
