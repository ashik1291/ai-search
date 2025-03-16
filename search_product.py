from sentence_transformers import SentenceTransformer
import weaviate
from PIL import Image
import streamlit as st

import call_gemini as cg

from PIL import Image
import io

def preprocess_image(image_file, max_size=(500, 500)):
    """
    Resize the image to reduce its size without losing quality.
    """
    img = Image.open(image_file)
    
    # Resize while maintaining aspect ratio
    img.thumbnail(max_size, Image.Resampling.LANCZOS)  # Use LANCZOS instead of ANTIALIAS
    
    # Save the resized image to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)  # Adjust quality as needed
    buffer.seek(0)
    
    return buffer

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
        "Keep the response under 75 characters. Return just the enhanced query."
        "Do not include lists, multiple options, or bullet points—only one sentence."
    )

    response = cg.call_gemini_api(prompt)
    enhanced_query = response["candidates"][0]["content"]["parts"][0]["text"]
    return enhanced_query

# Use the same CLIP model for search
model = SentenceTransformer('clip-ViT-B-32')

def search_products(query, search_type, threshold):
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        
        # Handle text-based search
        if search_type == "text":
            text_query = enhance_query_with_gemini(query)
            print(f"Enhanced Text Query: {text_query}")
            query_embedding = model.encode(text_query)  # Use the original query
        
        # Handle image-based search
        elif search_type == "image":
            # Preprocess the image
            image_buffer = preprocess_image(query)
            
            # Generate a text query from the image using Gemini
            text_query = generate_text_query_from_image(image_buffer)
            print(f"Generated Text Query: {text_query}")
            
            # Encode the generated text query
            query_embedding = model.encode(text_query)
        
        else:
            raise ValueError("Invalid search_type. Use 'text' or 'image'.")
        
        query_vector = query_embedding.tolist()
        
        # Perform the vector search.
        results = product_collection.query.near_vector(
            near_vector=query_vector,
            limit=5,
            certainty=threshold
        )
        
        st.write(f"Search Results ({search_type}):")
        if not results.objects:
            st.write("No results found above the threshold.")
        else:
            # Display the results
            for idx, result in enumerate(results.objects, start=1):
                props = result.properties
                st.write(f"Result {idx}: {props['name']} ({props['category']}) - Price: {props['price']}")
                st.image(props['image_path'], caption=props['name'], width=200)
    finally:
        client.close()

if __name__ == "__main__":
    # Example: Text-based search
    search_products(query="blue", search_type="text", threshold=0.5)
    
    # Example: Image-based search
    # search_products(query="images/black_sandals_women.jpg", search_type="image", threshold=0.7)
