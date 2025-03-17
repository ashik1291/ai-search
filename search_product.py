from sentence_transformers import SentenceTransformer
import weaviate
from PIL import Image
import streamlit as st
import call_gemini as cg
import io
import os

# Create the "images/searched" folder if it doesn't exist
os.makedirs("images/searched", exist_ok=True)

def preprocess_image(image_file, max_size=(500, 500)):
    """
    Resize the image to reduce its size without losing quality.
    """
    try:
        # Open the image
        img = Image.open(image_file)
        
        # Resize while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality resizing
        
        # Save the resized image to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)  # Use high quality (95) for minimal loss
        buffer.seek(0)  # Rewind the buffer to the beginning
        
        return buffer
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def generate_text_query_from_image(image_buffer):
    """
    Use Gemini to generate a text-based query from the image.
    """
    # Prepare the prompt for Gemini
    prompt = "Describe this image as a concise search query in a single sentence. The response must be strictly less than 75 characters."
    
    # Call the Gemini API with the image
    response = cg.call_gemini_api(prompt, image_buffer)
    text_query = response["candidates"][0]["content"]["parts"][0]["text"]
    return text_query

def enhance_query_with_gemini(query):
    """
    Use Gemini to rephrase or expand the user's query for better search results.
    """
    prompt = (
        f"Rephrase or refine this search query for better matching: {query}. "
        "Keep the response under 75 characters. Return just the enhanced query in plain text, no special characters."
        "Do not include lists, no multiple options, or no bullet points—only one sentence."
    )

    response = cg.call_gemini_api(prompt)
    enhanced_query = response["candidates"][0]["content"]["parts"][0]["text"]
    return enhanced_query

# Use a text-specific model for text embeddings
text_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and efficient for text

# Use CLIP for image embeddings
image_model = SentenceTransformer('clip-ViT-B-32')

def search_products(query, search_type, threshold):
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        
        if search_type == "text":
            # Enhance the query with Gemini
            enhanced_query = enhance_query_with_gemini(query)
            print(f"Enhanced Text Query: {enhanced_query}")
            
            # Use the text-specific model for text-based search
            query_embedding = text_model.encode(enhanced_query)
            query_vector = query_embedding.tolist()
            
            # Perform vector search using text embeddings
            results = product_collection.query.near_vector(
                near_vector=query_vector,
                limit=5,
                certainty=threshold,
                target_vector="text_embedding"  # Search using text embeddings
            )
        
        elif search_type == "image":
            # Preprocess the image
            image_buffer = preprocess_image(query)
            
            # Use CLIP for image-based search
            query_embedding = image_model.encode(Image.open(query).convert("RGB"))
            query_vector = query_embedding.tolist()
            
            # Perform vector search using image embeddings
            results = product_collection.query.near_vector(
                near_vector=query_vector,
                limit=5,
                certainty=threshold, 
                target_vector="image_embedding"  # Search using image embeddings
            )
        
        else:
            raise ValueError("Invalid search_type. Use 'text' or 'image'.")
        
        st.write(f"Search Results ({search_type}):")
        if not results.objects:
            st.write("No results found above the threshold.")
        else:
            # Display the results in a card-like layout
            for idx, result in enumerate(results.objects, start=1):
                props = result.properties
                
                # Create a card-like layout using columns
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    # Display the product image
                    st.image(props['image_path'], caption='', width=150)
                
                with col2:
                    # Display product details
                    st.write(f"**Name:** {props['name']}")
                    st.write(f"**Category:** {props['category']}")
                    st.write(f"**Price:** ${props['price']:.2f}")
                
                # Add a divider between products
                st.write("---")

    finally:
        client.close()


if __name__ == "__main__":
    # Example: Text-based search
    search_products(query="blue", search_type="text", threshold=0.5)
    
    # Example: Image-based search
    # search_products(query="images/black_sandals_women.jpg", search_type="image", threshold=0.7)