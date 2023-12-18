import chromadb
import mysql.connector

client = chromadb.HttpClient(host='<CHROMA SERVER IP>', port=8000)

OPENAI_API_KEY = "<YOUR OPENAI API KEY>"

EMBEDDING_MODEL = "text-embedding-ada-002"

GPT_MODEL = "gpt-3.5-turbo-16k"

SECRET_KEY="just some key Im using for testing"

DBCONN_STR="mysql+mysqlconnector://<USERNAME>:<PASSWORD>@<MYSQL IP ADDR>/<MYSQL DB NAME>"
