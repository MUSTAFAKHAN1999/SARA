import chromadb
import mysql.connector

client = chromadb.HttpClient(host='3.221.183.177', port=8000)

OPENAI_API_KEY = "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"

EMBEDDING_MODEL = "text-embedding-ada-002"

GPT_MODEL = "gpt-3.5-turbo-16k"

SECRET_KEY="just some key Im using for testing"

DBCONN_STR="mysql+mysqlconnector://sara:12347890@10.0.138.241/SARA_DB"

connection = mysql.connector.connect(
    host="10.0.138.241",
    user="sara",
    password="12347890",
    database="SARA_DB"
)
