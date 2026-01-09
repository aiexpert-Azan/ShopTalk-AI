import azure.functions as func
import os
import json
import logging
from openai import AzureOpenAI

# 1. Multi-Business Profiles
BUSINESS_PROFILES = {
    "grocery": {
        "name": "Al-Madina Grocery Store",
        "info": "Opening hours: 9 AM to 9 PM. Items: Flour (10kg: 1400), Sugar (1kg: 150), and Milk. Free delivery in Gulberg.",
        "style": "Polite and helpful grocery store owner."
    },
    "hotel": {
        "name": "Pindi Dhaba",
        "info": "Opening hours: 12 PM to 12 AM. Today's special: Chicken Karahi (700) and Daal (200). Family seating is available.",
        "style": "Energetic and welcoming hotel waiter."
    }
}

app = func.FunctionApp()

@app.route(route="chat", methods=["POST"])
def chat_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a chat request.')

    try:
        # 2. Parse request
        req_body = req.get_json()
        user_message = req_body.get('message')
        biz_type = req_body.get('business_type', 'grocery')

        if not user_message:
            return func.HttpResponse(json.dumps({"bot_reply": "No message provided"}), status_code=400)

        profile = BUSINESS_PROFILES.get(biz_type, BUSINESS_PROFILES["grocery"])
        
        # 3. Initialize Azure OpenAI Client
        client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT").strip().rstrip('/')
        )

        # 4. STRICT LANGUAGE PROTOCOL PROMPT
        # This ensures the AI does not default to Roman Urdu when asked in English
        system_content = f"""
        You are the professional owner/manager of {profile['name']}. 
        Business Facts: {profile['info']}. 
        Personality: {profile['style']}.

        STRICT LANGUAGE RULES:
        1. If the user speaks in ENGLISH, you MUST respond ONLY in professional English.
        2. If the user speaks in ROMAN URDU or URDU, you MUST respond in natural Roman Urdu.
        3. Do not mix languages unless the user mixes them. 
        4. Always stay in character and only provide information based on the Business Facts above.
        """

        # 5. Call AI Model
        response = client.chat.completions.create(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3 # Lower temperature for higher factual consistency
        )

        bot_reply = response.choices[0].message.content

        # 6. Return structured JSON for React
        return func.HttpResponse(
            json.dumps({"bot_reply": bot_reply}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"bot_reply": f"System Error: {str(e)}"}),
            mimetype="application/json",
            status_code=500
        )