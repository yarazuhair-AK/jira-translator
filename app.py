import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate_jira():
    data = request.get_json() or {}
    issue_key = data.get('issue_key')
    text_to_translate = data.get('text')

    if not text_to_translate or not issue_key:
        return jsonify({"error": "Missing text or issue_key"}), 400

    try:
        # 1. Direct REST Call to Google Gemini API
        gemini_key = os.environ.get("GEMINI_API_KEY")
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_key}"
        
        prompt = f"Translate the following text into natural, professional Arabic. Output ONLY the Arabic translation, nothing else:\n\n{text_to_translate}"
        
        gemini_payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        g_res = requests.post(gemini_url, json=gemini_payload, headers={"Content-Type": "application/json"})
        g_data = g_res.json()

        if g_res.status_code != 200:
            return jsonify({"error": "Gemini API Error", "details": g_data}), 500

        arabic_translation = g_data['candidates'][0]['content']['parts'][0]['text'].strip()

        # 2. Post Comment to Jira API
        jira_domain = os.environ.get("JIRA_DOMAIN")
        jira_email = os.environ.get("JIRA_EMAIL")
        jira_token = os.environ.get("JIRA_API_TOKEN")

        jira_url = f"https://{jira_domain}/rest/api/3/issue/{issue_key}/comment"
        auth = (jira_email, jira_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

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
                                "text": f"🌐 Arabic Translation:\n\n{arabic_translation}"
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
