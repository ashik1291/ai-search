import weaviate
from weaviate.classes.config import Configure, Property, DataType

def create_schema():
    client = weaviate.connect_to_local()
    try:
        # Create the "Product" class with named vectors for text and image embeddings.
        client.collections.create(
            name="Product",
            properties=[
                Property(name="name", data_type=DataType.TEXT),
                Property(name="category", data_type=DataType.TEXT),
                Property(name="price", data_type=DataType.NUMBER),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="ratings", data_type=DataType.NUMBER)
            ],
            vectorizer_config=[
            # Set a named vector for your own uploaded vectors
            Configure.NamedVectors.none(
                name="name_embedding",
                vector_index_config=Configure.VectorIndex.hnsw()    # (Optional) Set vector index options
            ),
            Configure.NamedVectors.none(
                name="description_embedding",
                vector_index_config=Configure.VectorIndex.hnsw()    # (Optional) Set vector index options
            ),
            Configure.NamedVectors.none(
                name="category_embedding",
                vector_index_config=Configure.VectorIndex.hnsw()    # (Optional) Set vector index options
            )
            
    ],
        )
        print("Schema created successfully!")
    finally:
        client.close()

if __name__ == "__main__":
    create_schema()