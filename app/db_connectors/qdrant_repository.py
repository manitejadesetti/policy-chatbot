import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


class QdrantRepository:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_CLUSTER_ENDPOINT", "https://YOUR_CLUSTER_URL"),
            api_key=os.getenv("QDRANT_API_KEY", "YOUR_API_KEY"),
        )
        

    
    def create_collection(self, name="documents"):
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            ),
        )

    def get_collection(self, name):
        return self.client.get_collection(name)
    

    def get_or_create_collection(self, name) -> QdrantClient:
        
        exists = self.client.collection_exists(name)
        if exists:
            return self.get_collection(name)
        else:
            self.create_collection(name)
            return self.get_collection(name)
        
    
    def add(self, collection_name, ids, documents, embeddings):
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
        )

    def query(self, collection, query_embeddings, n_results):
        results = self.client.query_points(
            collection_name="documents",
            query=query_embeddings,
            limit=n_results
        )
        return results

        

