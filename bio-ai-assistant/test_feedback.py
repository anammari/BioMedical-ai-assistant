import requests

# Prompt the user to input the conversation_id
conversation_id = input("Enter the conversation_id: ")

# Define the feedback value
feedback = 1  # You can also prompt the user to input the feedback value if needed

url = "http://localhost:5000/feedback"
headers = {"Content-Type": "application/json"}
data = {"conversation_id": conversation_id, "feedback": feedback}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.text)
