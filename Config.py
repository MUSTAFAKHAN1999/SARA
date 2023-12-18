import chromadb

client = client = chromadb.PersistentClient(path="./database")

OPENAI_API_KEY = "<YOUR OPENAI API KEY>"

EMBEDDING_MODEL = "text-embedding-ada-002"

GPT_MODEL = "gpt-3.5-turbo-16k"
