import chromadb
from config import CHROMA_PATH, COLLECTION_NAME

chat_history = {}
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
