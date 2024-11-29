import os

os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from flask import Flask, request, render_template, jsonify
from elasticsearch import Elasticsearch
import openai
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)


es = Elasticsearch("http://localhost:9200")
model = SentenceTransformer('all-MiniLM-L6-v2')



load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
#model = genai.GenerativeModel('gemini-1.5-flash')

es = Elasticsearch("http://localhost:9200")
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_ai_response(context, query):
    """
    Generate a response using Google Gemini with improved error handling
    """
    try:
        # Truncate context to prevent excessive input
        truncated_context = context[:1000]
        
        # Prepare the prompt with clear instructions and truncated context
        full_prompt = f"""You are a helpful movie assistant. Provide a concise and informative response.

Context of Relevant Movies:
{truncated_context}

User Query: {query}

Response:"""
        
        # Use Gemini Pro model
        generation_config = {
            "temperature": 0.7,
            "max_output_tokens": 200,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate response
        response = model.generate_content(
            full_prompt, 
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Check for blocked content or errors
        if response.prompt_feedback.block_reason:
            return "I cannot generate a response due to safety concerns."
        
        # Return the generated text, truncating if necessary
        generated_text = response.text[:500].strip()
        return generated_text or "I'm having trouble generating a meaningful response."
    
    except Exception as e:
        # Comprehensive error handling
        import logging
        import traceback
        
        logging.error(f"Error in Gemini AI Response Generation: {e}")
        logging.error(traceback.format_exc())
        
        return "I encountered a technical issue while generating a response."


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/movie_chat', methods=['POST'])
def movie_chat():
    """
    Handle movie-related chat queries using a combination of 
    semantic search and Gemini AI response generation
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        # Perform semantic search to get relevant movie context
        semantic_search_query = {
            "query": query,
            "size": 5  # Get top 5 most relevant movies
        }
        
        # Perform semantic search using the helper function
        search_response = perform_semantic_search(semantic_search_query)
        
        # Prepare context from search results
        context = ""
        if search_response:
            context = "Relevant Movies:\n"
            for movie in search_response:
                context += f"Title: {movie['title']}\n"
                context += f"Description: {movie['description']}\n"
                context += f"Genre: {movie['genre']}\n"
                context += f"Year: {movie['release_year']}\n"
                context += f"Rating: {movie['rating']}\n\n"
        
        # Generate AI response using Gemini
        ai_response = generate_ai_response(context, query)
        
        return jsonify({
            "response": ai_response,
            "context_movies": search_response
        })
    
    except Exception as e:
        # More detailed error logging
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e)
        }), 500

def perform_semantic_search(data=None):
    """
    Helper method to perform semantic search 
    Allow optional data parameter with a default of None
    """
    # If no data is provided, return an empty list
    if data is None:
        return []
    
    query = data['query']
    
    # Generate query embedding
    query_embedding = model.encode(query).tolist()
    
    # Hybrid search combining semantic and keyword search
    es_query = {
        "size": data.get('size', 3),
        "query": {
            "bool": {
                "should": [
                    # Semantic search using k-NN
                    {
                        "knn": {
                            "field": "embedding",
                            "query_vector": query_embedding,
                            "k": 5,
                            "num_candidates": 50
                        }
                    },
                    # Keyword match with boosting
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "overview"],
                            "type": "best_fields"
                        }
                    }
                ]
            }
        }
    }
    
    response = es.search(index="movies-idx", body=es_query)
    
    results = [
        {
            "title": hit["_source"]["title"],
            "description": hit["_source"]["overview"],
            "genre": hit["_source"]["genre"],
            "rating": hit["_source"]["rating"],
            "release_year": hit["_source"]["release_year"]
        }
        for hit in response["hits"]["hits"]
    ]
    
    return results

@app.route('/advanced_search', methods=['POST'])
def advanced_search():
    data = request.get_json()
    
    # Base query
    es_query = {
        "query": {
            "bool": {
                "must": []
            }
        },
        "sort": [],
        "size": data.get('limit', 10)
    }
    
    # Genre filtering
    # Genre filtering for JSON-stored genres
    if data.get('genres'):
        genre_filters = []
        for genre in data['genres']:
            # Create multiple match conditions to handle JSON-stored genres
            genre_filters.extend([
                # Exact match for genre names
                {
                    "wildcard": {
                        "genre": f"*{genre}*"
                    }
                },
                # Match within JSON string
                {
                    "regexp": {
                        "genre": f".*\"name\":\\s*\"{genre}\".*"
                    }
                }
            ])
        
        # Use should with minimum_should_match to allow flexible genre matching
        es_query['query']['bool']['must'].append({
            "bool": {
                "should": genre_filters,
                "minimum_should_match": 1
            }
        })
    
    # Year range filtering
    if data.get('min_year') or data.get('max_year'):
        year_range = {}
        if data.get('min_year'):
            year_range['gte'] = data['min_year']
        if data.get('max_year'):
            year_range['lte'] = data['max_year']
        
        es_query['query']['bool']['must'].append({
            "range": {
                "release_year": year_range
            }
        })
    
    # Rating filter
    if data.get('min_rating'):
        es_query['query']['bool']['must'].append({
            "range": {
                "rating": {
                    "gte": data['min_rating']
                }
            }
        })
    
    # Sorting
    if data.get('sort_by'):
        sort_options = {
            "title_asc": {"title.keyword": {"order": "asc"}},
            "title_desc": {"title.keyword": {"order": "desc"}},
            "rating_asc": {"rating": {"order": "asc"}},
            "rating_desc": {"rating": {"order": "desc"}},
            "year_asc": {"release_year": {"order": "asc"}},
            "year_desc": {"release_year": {"order": "desc"}}
        }
        
        if data['sort_by'] in sort_options:
            es_query['sort'].append(sort_options[data['sort_by']])
    
    # Perform search
    response = es.search(index="movies-idx", body=es_query)
    
    results = [
        {
            "title": hit["_source"]["title"],
            "description": hit["_source"]["overview"],
            "genre": hit["_source"]["genre"],
            "rating": hit["_source"]["rating"],
            "release_year": hit["_source"]["release_year"]
        }
        for hit in response["hits"]["hits"]
    ]
    
    return jsonify({
        "results": results,
        "total": response["hits"]["total"]["value"]
    })

@app.route('/semantic_search', methods=['POST'])
def semantic_search():
    data = request.get_json()
    query = data['query']
    
    # Generate query embedding
    query_embedding = model.encode(query).tolist()
    
    # Hybrid search combining semantic and keyword search
    es_query = {
        "size": 10,
        "query": {
            "bool": {
                "should": [
                    # Semantic search using k-NN
                    {
                        "knn": {
                            "field": "embedding",
                            "query_vector": query_embedding,
                            "k": 5,
                            "num_candidates": 50
                        }
                    },
                    # Keyword match with boosting
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "overview"],
                            "type": "best_fields"
                        }
                    }
                ]
            }
        },
        # Highlight matching text
        "highlight": {
            "fields": {
                "overview": {
                    "fragment_size": 100,
                    "number_of_fragments": 1
                }
            }
        }
    }
    
    response = es.search(index="movies-idx", body=es_query)
    
    results = [
        {
            "title": hit["_source"]["title"],
            "description": hit["_source"]["overview"],
            "highlighted_text": hit.get("highlight", {}).get("overview", [""])[0],
            "semantic_score": hit["_score"]
        }
        for hit in response["hits"]["hits"]
    ]
    
    return jsonify(results)

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json()
    movie_title = data['title']
    
    # Find the base movie's embedding
    base_movie_query = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": movie_title}},
                    {"match": {"title.keyword": movie_title}}
                ]
            }
        }
    }
    
    base_movie_response = es.search(index="movies-idx", body=base_movie_query)
    
    if not base_movie_response["hits"]["hits"]:
        return jsonify({"error": f"Movie '{movie_title}' not found"}), 404
    
    base_movie = base_movie_response["hits"]["hits"][0]["_source"]
    base_movie_overview_embedding = base_movie["embedding"]
    
    # Find similar movies using semantic similarity on overview
    recommendation_query = {
        "size": 6,  # 5 recommendations (excluding the base movie)
        "query": {
            "bool": {
                "must_not": [
                    {"match": {"title.keyword": movie_title}}
                ],
                "should": [
                    # Semantic similarity on overview embedding
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": base_movie_overview_embedding}
                            }
                        }
                    },
                    # Genre matching
                    {
                        "match": {
                            "genre": base_movie["genre"]
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    }
    
    response = es.search(index="movies-idx", body=recommendation_query)
    
    recommendations = [
        {
            "title": hit["_source"]["title"],
            "description": hit["_source"]["overview"],
            "genre": hit["_source"]["genre"],
            "similarity_score": hit["_score"] - 1  # Subtract the added 1.0
        }
        for hit in response["hits"]["hits"]
    ]
    
    return jsonify(recommendations)



@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data['query']
    
    # Simplified hybrid search query
    es_query = {
        "size": 10,
        "query": {
            "bool": {
                "should": [
                    # Exact title match with high boost
                    {
                        "match_phrase": {
                            "title": {
                                "query": query,
                                "boost": 5
                            }
                        }
                    },
                    # Fuzzy title match
                    {
                        "match": {
                            "title": {
                                "query": query,
                                "fuzziness": "AUTO",
                                "boost": 3
                            }
                        }
                    },
                    # Overview text match
                    {
                        "match": {
                            "overview": {
                                "query": query,
                                "fuzziness": "AUTO",
                                "boost": 1.5
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        # Highlight matching text
        "highlight": {
            "fields": {
                "title": {},
                "overview": {
                    "fragment_size": 100,
                    "number_of_fragments": 1
                }
            }
        }
    }
    
    response = es.search(index="movies-idx", body=es_query)
    
    results = []
    for hit in response["hits"]["hits"]:
        result = {
            "title": hit["_source"]["title"],
            "description": hit["_source"]["overview"],
            "genre": hit["_source"]["genre"],
            "rating": hit["_source"]["rating"],
            "release_year": hit["_source"]["release_year"],
            "score": hit["_score"]
        }
        
        # Add highlights if available
        if "highlight" in hit:
            if "title" in hit["highlight"]:
                result["title_highlight"] = hit["highlight"]["title"][0]
            if "overview" in hit["highlight"]:
                result["description_highlight"] = hit["highlight"]["overview"][0]
        
        results.append(result)
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(port=6006, debug=True)