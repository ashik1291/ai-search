import weaviate
import weaviate.classes as wvc

def create_schema():
    client = weaviate.connect_to_local()
    try:
        # Create the "Product" class with a property for the composite vector.
        # We store the product details and the composite embedding (as a NUMBER_ARRAY).
        product_collection = client.collections.create(
            name="Product",
            properties=[
                wvc.config.Property(name="name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="category", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="price", data_type=wvc.config.DataType.NUMBER),
                wvc.config.Property(name="image_path", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="embedding", data_type=wvc.config.DataType.NUMBER_ARRAY)
            ]
        )
        print("Schema created successfully!")
    finally:
        client.close()

if __name__ == "__main__":
    create_schema()
