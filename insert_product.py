from sentence_transformers import SentenceTransformer
import weaviate
from PIL import Image
import os
import streamlit as st

# Create an images folder if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")
os.makedirs("images/product", exist_ok=True)

# Use a text-specific model for text embeddings
text_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and efficient for text

# Use CLIP for image embeddings
image_model = SentenceTransformer('clip-ViT-B-32')


def preprocess_and_save_image(image_path, output_folder="images/product", size=(500, 500)):
    """
    """
    try:
        # Create the output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Open the image
        with Image.open(image_path) as img:
            # Resize while maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality resizing
            
            # Save the resized image to the output folder
            output_path = os.path.join(output_folder, os.path.basename(image_path))
            img.save(output_path, format="JPEG", quality=95)  # Use high quality (95) for minimal loss
            
            print(f"Processed image saved to {output_path}")
            return output_path
    except Exception as e:
        print(f"Error processing and saving image: {e}")
        return None

def insert_product(image_path, name, category, price):
    """
    Inserts a product with separate text and image embeddings.
    """
    # Preprocess the image and get the saved path.
    saved_image_path = preprocess_and_save_image(image_path)
    
    # Compute embeddings for the product name (text) and the image.
    text_embedding = text_model.encode(name)  # Use text-specific model for text embeddings
    image_embedding = image_model.encode(Image.open(saved_image_path).convert("RGB"))  # Use CLIP for image embeddings
    
    # Connect to Weaviate and insert the product with separate embeddings.
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        product_collection.data.insert(
            properties={
                "name": name,
                "category": category,
                "price": price,
                "image_path": saved_image_path,
            },
            vector={
                "text_embedding": text_embedding.tolist(),
                "image_embedding": image_embedding.tolist()
    }
        )
        print(f"Stored product: {name}")
        st.write(f"Stored product: {name}")
    finally:
        client.close()

if __name__ == "__main__":
    # insert_product("images/product/men_shoe.jpg", "Red running shoes for men", "shoes", 78.99)
    # insert_product("images/product/women_shoe.jpg", "Blue trail running shoes for women", "shoes", 88.99)
    # insert_product("images/product/white_headphone.jpg", "Ergonomic white headphones for office use", "headphone", 20.99)
    insert_product("images/product/blue_trail_shoes_women.jpg", "Blue Trail Running Shoes for Women", "shoes", 129.99)  
    insert_product("images/product/black_leather_shoes_men.jpg", "Black Leather Office Shoes for Men", "shoes", 89.99)  
    insert_product("images/product/red_sneakers_kids.jpg", "Red Lightweight Sneakers for Kids", "shoes", 59.99)  
    insert_product("images/product/white_headphones.jpg", "White Wireless Over-Ear Headphones", "electronics", 199.99)  
    insert_product("images/product/gray_office_chair.jpg", "Gray Adjustable Ergonomic Office Chair", "furniture", 249.99)  
    insert_product("images/product/black_road_bike.jpg", "Black Carbon Fiber Road Bike", "automotive", 1799.99)  
    insert_product("images/product/green_hiking_backpack.jpg", "Green Waterproof Hiking Backpack 40L", "accessories", 79.99)  
    insert_product("images/product/silver_smartwatch.jpg", "Silver Stainless Steel Smartwatch", "electronics", 349.99)  
    insert_product("images/product/pink_floral_dress.jpg", "Pink Floral Summer Dress for Women", "fashion", 59.99)  
    insert_product("images/product/brown_wallet_men.jpg", "Brown Leather RFID Wallet for Men", "accessories", 39.99)  
    insert_product("images/product/white_sleep_earbuds.jpg", "White Noise-Canceling Sleep Earbuds", "electronics", 129.99)  
    insert_product("images/product/black_rgb_keyboard.jpg", "Black Gaming Mechanical Keyboard RGB", "gaming", 99.99)  
    insert_product("images/product/blue_running_shoes_men.jpg", "Blue Lightweight Running Shoes for Men", "shoes", 109.99)   
    insert_product("images/product/red_gaming_mouse.jpg", "Red High-Performance Gaming Mouse", "gaming", 69.99)  
    insert_product("images/product/gray_compact_treadmill.jpg", "Gray Compact Foldable Treadmill", "fitness",349.99)  

