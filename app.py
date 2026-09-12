import os
from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI

app = Flask(__name__)

# Config - Set these in your hosting environment
JIRA_DOMAIN = os.environ.get("JIRA_DOMAIN")  # e.g., "yourcompany.atlassian.net"
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")    # Your Jira account email
JIRA_TOKEN = os.environ.get("JIRA_TOKEN")    # Your Jira API Token
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)

@app.route('/translate', methods=['POST'])
def translate_jira():
    data = request.json
    issue_key = data.get('issue_key')
    text_to_translate = data.get('text')
    feedback = data.get('feedback', '')
    platform = data.get('platform', 'Social Media') # LinkedIn or Instagram

    if not text_to_translate or not issue_key:
        return jsonify({"error": "Missing issue_key or text"}), 400

    # Build Creative Translation Prompt
    system_prompt = (
        f"You are an expert social media copywriter specializing in localized Arabic content for {platform}. "
        "Translate English content into catchy, natural, highly engaging Arabic suitable for social media. "
        "Do not translate word-for-word. Adapt idioms, tone, and formatting for Arabic audiences."
    )
    
    user_prompt = f"Original English Text:\n{text_to_translate}"
    if feedback:
        user_prompt += f"\n\nReviewer Feedback/Improvement Request:\n{feedback}"

    # Call AI Model
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    translated_text = response.choices[0].message.content

    # Post back to Jira as a Comment
    comment_body = (
        f"🤖 **Automated Arabic Translation ({platform})**\n\n"
        f"{translated_text}\n\n"
        "--- \n"
        "*(Reviewers: Move status to 'Approved' to deliver, or reply with feedback to request a retry.)*"
    )
    
    jira_url = f"https://{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/comment"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"text": comment_body, "type": "text"}]
            }]
        }
    }
    
    requests.post(jira_url, json=payload, headers=headers, auth=auth)
    return jsonify({"status": "success", "translation": translated_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)