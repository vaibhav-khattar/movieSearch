# from transformers import AutoTokenizer, AutoModel
# import torch

# # Example using a transformer model
# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)

# # Generate an embedding for a sample sentence
# sample_text = "This is a test sentence."
# inputs = tokenizer(sample_text, return_tensors="pt")
# with torch.no_grad():
#     embedding = model(**inputs).pooler_output

# print(embedding.shape)  # Verify the output dimensions


import openai

def check_openai_api_key(api_key):
    client = openai.OpenAI(api_key=api_key)
    try:
        client.models.list()
    except openai.AuthenticationError:
        return False
    else:
        return True


OPENAI_API_KEY = "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"

if check_openai_api_key(OPENAI_API_KEY):
    print("Valid OpenAI API key.")
else:
    print("Invalid OpenAI API key.")