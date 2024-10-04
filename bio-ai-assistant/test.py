import pandas as pd
import json
import requests
import os

df = pd.read_csv("../data/ground-truth-retrieval.csv")
question = df.sample(n=1).iloc[0]['question']

print("question: ", question)

url = "http://localhost:5000/question"


data = {"question": question}

response = requests.post(url, json=data)
json_data = json.loads(response.text)

print(json_data)