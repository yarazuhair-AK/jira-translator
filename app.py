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

    try:
        # Call Gemini API with valid model name
        prompt = f"Translate the following text into natural, professional Arabic. Output ONLY the Arabic translation:\n\n{text_to_translate}"
        
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        arabic_translation = response.text.strip()

        # Jira Credentials
        jira_domain = os.environ.get("JIRA_DOMAIN")
        jira_email = os.environ.get("JIRA_EMAIL")
        jira_token = os.environ.get("JIRA_API_TOKEN")

        jira_url = f"https://{jira_domain}/rest/api/3/issue/{issue_key}/comment"
        auth = (jira_email, jira_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Atlassian Document Format (ADF)
        comment_payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Arabic Translation:\n\n{arabic_translation}"
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
            return jsonify({"error": "Jira API Error", "status_code": jira_res.status_code, "details": jira_res.text}), 500

    except Exception as e:
        return jsonify({"error": "Server Exception", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
