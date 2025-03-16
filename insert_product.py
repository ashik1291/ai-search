from sentence_transformers import SentenceTransformer
import weaviate
from PIL import Image
import os
import streamlit as st

# Create an images folder if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Use the multi-modal CLIP model for both text and image embeddings.
model = SentenceTransformer('clip-ViT-B-32')

def preprocess_and_save_image(image_path, output_folder="images", size=(500, 500)):
    """Resize an image and save it to the output folder."""
    with Image.open(image_path) as img:
        img = img.resize(size)
        output_path = os.path.join(output_folder, os.path.basename(image_path))
        img.save(output_path)
        print(f"Processed image saved to {output_path}")
        return output_path

def insert_product(image_path, name, category, price):
    """
    Inserts a product with both text and image embeddings.
    Computes a composite embedding by averaging the text and image embeddings.
    """
    # Preprocess the image and get the saved path.
    saved_image_path = preprocess_and_save_image(image_path)
    
    # Compute embeddings for the product name (text) and the image.
    text_embedding = model.encode(name)            # e.g. 512-dim vector
    image_embedding = model.encode(Image.open(saved_image_path).convert("RGB"))

    # Adjust weights for text and image embeddings
    text_weight = 0.7  # Higher weight for text
    image_weight = 0.3  # Lower weight for image

    composite_embedding = (text_weight * text_embedding + image_weight * image_embedding).tolist()
    
    # Composite embedding: for example, the average of both embeddings.
    # composite_embedding = ((text_embedding + image_embedding) / 2).tolist()
    
    # Connect to Weaviate and insert the product with the composite vector.
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        product_collection.data.insert(
            properties={
                "name": name,
                "category": category,
                "price": price,
                "image_path": saved_image_path
            },
            vector=composite_embedding
        )
        print(f"Stored product: {name}")
        st.write(f"Stored product: {name}")
    finally:
        client.close()

if __name__ == "__main__":
    insert_product("images/men_shoe.jpg", "Red running shoes for men", "shoes", 78.99)
    insert_product("images/women_shoe.jpg", "Blue trail running shoes for women", "shoes", 88.99)
    insert_product("images/white_headphone.jpg", "Ergonomic white headphones for office use", "headphone", 20.99)
