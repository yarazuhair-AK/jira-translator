import os
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize Gemini Client
ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/translate', methods=['POST'])
def translate_jira():
    data = request.get_json() or {}
    issue_key = data.get('issue_key')
    text_to_translate = data.get('text')

    if not text_to_translate or not issue_key:
        return jsonify({"error": "Missing text or issue_key"}), 400

    # Call Gemini Free API
    prompt = f"Translate the following text into natural, professional Arabic. Output only the Arabic translation:\n\n{text_to_translate}"
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    arabic_translation = response.text.strip()

    # Post Comment back to Jira
    jira_domain = os.environ.get("JIRA_DOMAIN")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_token = os.environ.get("JIRA_API_TOKEN")

    jira_url = f"https://{jira_domain}/rest/api/3/issue/{issue_key}/comment"
    auth = (jira_email, jira_token)
    headers = {"Content-Type": "application/json"}

    comment_payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": f"🌐 **Arabic Translation:**\n\n{arabic_translation}"
                        }
                    ]
                }
            ]
        }
    }

    jira_res = requests.post(jira_url, json=comment_payload, auth=auth, headers=headers)
    
    if jira_res.status_code in [200, 201]:
        return jsonify({"status": "success", "translation": arabic_translation}), 200
    else:
        return jsonify({"error": "Failed to post comment to Jira", "details": jira_res.text}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
