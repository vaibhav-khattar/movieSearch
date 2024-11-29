import json
import pandas as pd
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# Initialize Elasticsearch and SBERT
es = Elasticsearch("http://localhost:9200")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load the mapping
with open("./mappings/movies_mappings.json") as f:
    mapping = json.load(f)

# Create the index if it doesn't already exist
if es.indices.exists(index="movies-idx"):
    es.indices.delete(index="movies-idx")

es.indices.create(index="movies-idx", body={
    "settings": {
        "analysis": {
            "analyzer": {
                "title_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "title_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "overview": {"type": "text"},
            "genre": {"type": "keyword"},
            "release_year": {"type": "integer"},
            "rating": {"type": "float"},
            "embedding": {
                "type": "dense_vector", 
                "dims": 384  # Dimension of all-MiniLM-L6-v2 model
            }
        }
    }
})

# Load TMDB data
df = pd.read_csv("movies.csv")

# Preprocess data
df['overview'] = df['overview'].fillna("No description available.")
df['release_year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
df['rating'] = df['vote_average']

# Index documents
for idx, row in df.iterrows():
    try:
        # Generate embedding for overview
        overview_embedding = model.encode(row['overview']).tolist()
        
        # Generate additional embedding for title to improve search
        title_embedding = model.encode(row['title']).tolist()
        
        doc = {
            "title": row["title"],
            "overview": row["overview"],
            "genre": row.get("genres", "Unknown"),
            "release_year": row['release_year'] if pd.notnull(row['release_year']) else None,
            "rating": row['rating'] if pd.notnull(row['rating']) else 0,
            "embedding": overview_embedding,
            "title_embedding": title_embedding
        }
        
        es.index(index="movies-idx", document=doc)
    except Exception as e:
        print(f"Error processing row {idx}: {e}")

print("Data indexed successfully!")