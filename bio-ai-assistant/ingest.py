import os
import pandas as pd

import minsearch

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

relative_path = "../data/bq-results-20240829-041517-1724904953827.jsonl"
container_path = "/app/data/bq-results-20240829-041517-1724904953827.jsonl"

if os.path.exists(relative_path):
    DATA_PATH = relative_path
else:
    DATA_PATH = container_path


def load_index(data_path=DATA_PATH):
    df = pd.read_json(data_path, lines=True)

    documents = df.to_dict(orient="records")

    index = minsearch.Index(
        text_fields=[
            'abstract', 
            'authors', 
            'keywords', 
            'organization_affiliated', 
            'title'
        ],
        keyword_fields=["id"],
    )

    index.fit(documents)
    return index