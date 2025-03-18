import os
import requests

# Set your Groq API key
GROQ_API_KEY = "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"

def call_groq_api(prompt, model="llama-3.3-70b-versatile"):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }

    # Make the API request
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
    response_data = response.json()

        # Debugging: Print the full response for inspection
    print("Full API Response:", response_data)

        # Extract the content from the response
    if "choices" in response_data and len(response_data["choices"]) > 0:
        enhanced_query = response_data["choices"][0]["message"]["content"]
        return enhanced_query.strip()  # Return the enhanced query
    else:
        print("Unexpected response structure:", response_data)
        return None  # Return None if the response is invalid
