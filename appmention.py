#Required Library to install
# pip install slack_bolt
# pip instal python-dotenv

import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def send_to_customgpt(prompt):
    url = "https://app.customgpt.ai/api/v1/projects/18663/conversations/651eff24-95d4-4630-98fd-49775b0e2e6e/messages?stream=false&lang=en"

    payload = {
        "prompt": prompt,
        "custom_persona": "You are a custom chatbot assistant called *bot name*, a friendly *bot role* who works for *organization* and answers questions based on the given context. Be as helpful as possible. Always prioritize the customer. Escalate complex issues. Stay on topic. Use appropriate language, Acknowledge limitations.",
        "chatbot_model": "gpt-4",
        "response_source": "default"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer 2752|DzIV0GyaesV3SJeqsdWK9WSTTyS5Ivh5qIlzem2K"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.text


@app.event("app_mention")
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
@app.event("message")
def handle_message_events(body, logger):
    # Log the 'message' events
    logger.info(body)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
