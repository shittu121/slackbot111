from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

import requests
import json
import os

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
slack_handler = SlackRequestHandler(slack_app)

API_KEY = os.environ.get("API_KEY")
def send_to_customgpt(prompt):
    url = os.environ.get("GPT_URL")

    payload = {
        "prompt": prompt,
        "custom_persona": "You are a custom chatbot assistant called *bot name*, a friendly *bot role* who works for *organization* and answers questions based on the given context. Be as helpful as possible. Always prioritize the customer. Escalate complex issues. Stay on topic. Use appropriate language, Acknowledge limitations.",
        "chatbot_model": "gpt-4",
        "response_source": "default"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.text


@app.get("/")
async def index(request: Request):
    return {"message": "Hello"}


@app.post("/slack/events")
async def endpoint(request: Request):
    try:
        response = await slack_handler.handle(request.body())
        return JSONResponse(content=response.body, status_code=response.status)
    except HTTPException as e:
        return JSONResponse(content={"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@slack_app.event("app_mention")
def app_mention_handler(body, say, logger):
    user_message = body['event']['text']

    # Send the user's message to CustomGPT.AI
    customgpt_response = send_to_customgpt(user_message)

    if isinstance(customgpt_response, str):
        try:
            # Attempt to parse the string response as JSON
            json_response = json.loads(customgpt_response)

            # Access the 'data' field to get the 'openai_response'
            openai_response = json_response.get("data", {}).get("openai_response")

            # Send the extracted response back to the Slack channel
            if openai_response:
                say(openai_response)
            else:
                say("No valid response received from CustomGPT.AI")
        except json.JSONDecodeError as e:
            say(f"Failed to parse JSON response from CustomGPT.AI: {str(e)}")
    else:
        say("Unexpected response received from CustomGPT.AI")


# Handle 'message' events
@slack_app.event("message")
def handle_message_events(body, logger):
    # Log the 'message' events
    logger.info(body)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
