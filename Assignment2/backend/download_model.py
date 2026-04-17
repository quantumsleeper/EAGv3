import socket
# Set global socket timeout to 1000 seconds to prevent the slow download from failing!
socket.setdefaulttimeout(1000)

import chromadb
from chromadb.utils import embedding_functions
print("Downloading ChromaDB model... this will take a few minutes. Do not cancel.")
ef = embedding_functions.DefaultEmbeddingFunction()
# Running it once triggers the download and extraction
ef(["test"])
print("Download and extraction completed successfully!")
