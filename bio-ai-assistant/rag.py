import json
import os
from time import time
import ingest
import google.auth
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# Global Model Name 
MODEL_NAME = "gemini-1.5-flash-001" 

# Set up the API key and project ID for Gemini 
PROJECT_ID = os.environ['GCP_PROJECT_ID']

relative_path = "../pacific-ethos-428312-n5-eb4864ff3add.json"
container_path = "/app/pacific-ethos-428312-n5-eb4864ff3add.json"

if os.path.exists(relative_path):
    credentials_path = relative_path
else:
    credentials_path = container_path

credentials = service_account.Credentials.from_service_account_file(credentials_path)
vertexai.init(project=PROJECT_ID, credentials=credentials, location="us-central1")

#Load the indexed data
index = ingest.load_index()

def search(query):
    boost = {
          'abstract': 2.38,
          'authors': 0.03,
          'keywords': 0.52,
          'organization_affiliated': 1.33,
          'title': 0.20
    }

    results = index.search(
        query=query, filter_dict={}, boost_dict=boost, num_results=10
    )

    return results

prompt_template = """
You're an experienced biomedical researcher. Answer the QUESTION based only on the CONTEXT from our Biomedical Research database.
Use only the facts from the CONTEXT when answering the QUESTION. Your answer must be an accurate summary and not an exact copy of the text. 
However, article titles, authors, keywords, and organizations must be exact from the CONTEXT. 
Do NOT include any article that does NOT exist in the CONTEXT.
Do NOT include anything that does NOT answer the QUESTION.
Do NOT repeat ANYTHING that you have previously said in your response.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

entry_template = """
abstract: {abstract}
authors: {authors} 
keywords: {keywords} 
organization_affiliated: {organization_affiliated} 
title: {title}
""".strip()

def build_prompt(query, search_results):
    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt

def llm(prompt, model=MODEL_NAME):
    model = GenerativeModel(model)
    prompt_tokens = model.count_tokens(prompt)
    response = model.generate_content(prompt)
    response_tokens = model.count_tokens(response.text)
    usage_metadata = response.usage_metadata

    token_stats = {
            "prompt_tokens": prompt_tokens.total_tokens,
            "prompt_characters": prompt_tokens.total_billable_characters,
            "candidates_tokens": usage_metadata.candidates_token_count,
            "candidates_characters": response_tokens.total_billable_characters,
            "total_tokens": usage_metadata.total_token_count,

        }

    return response.text, token_stats


evaluation_prompt_template = """
You are an expert evaluator for a Biomedical research question answering system.
Your task is to analyze the relevance of the answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer_llm}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


def evaluate_relevance(question, answer):
    prompt = evaluation_prompt_template.format(question=question, answer_llm=answer)
    evaluation_llm, tokens = llm(prompt, model=MODEL_NAME)

    try:
        evaluation = evaluation_llm.strip().replace('json', '').replace('`', '')
        json_eval = json.loads(evaluation)
        return json_eval, tokens
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result, tokens


def calculate_gemini_cost(model, tokens):
    gemini_cost = 0

    if model == MODEL_NAME:
        gemini_cost = (
            tokens["prompt_characters"] * 0.00001875 + tokens["candidates_characters"] * 0.0000375
        ) / 1000
    else:
        print("Model not recognized. Gemini cost calculation failed.")

    return gemini_cost


def rag(query, model=MODEL_NAME):
    t0 = time()

    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer, token_stats = llm(prompt, model=model)

    relevance, rel_token_stats = evaluate_relevance(query, answer)

    t1 = time()
    took = t1 - t0

    gemini_cost_rag = calculate_gemini_cost(model, token_stats)
    gemini_cost_eval = calculate_gemini_cost(model, rel_token_stats)

    gemini_cost = gemini_cost_rag + gemini_cost_eval

    answer_data = {
        "answer": answer,
        "model_used": model,
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get(
            "Explanation", "Failed to parse evaluation"
        ),
        "prompt_characters": token_stats["prompt_characters"],
        "prompt_tokens": token_stats["prompt_tokens"],
        "candidates_characters": token_stats["candidates_characters"],
        "candidates_tokens": token_stats["candidates_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_characters": rel_token_stats["prompt_characters"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_candidates_characters": rel_token_stats["candidates_characters"],
        "eval_candidates_tokens": rel_token_stats["candidates_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
        "gemini_cost": gemini_cost,
    }

    return answer_data
