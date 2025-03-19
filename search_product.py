from sentence_transformers import SentenceTransformer
import weaviate
from PIL import Image
import streamlit as st
import call_gemini as cg
import call_grog_cloud as cgc
import io
import os
import json
import re

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
        f"Rephrase or refine the following search query to better match the user's intent for product search. "
        f"Focus on the key intent and context of the query. "
        f"Ensure the response is clear and under 75 characters. "
        f"Return only the enhanced query in plain text, without special characters, lists, or multiple options.\n\n"
        f"Query: {query}"
    )

    response = cg.call_gemini_api(prompt)
    enhanced_query = response["candidates"][0]["content"]["parts"][0]["text"].strip()
    return enhanced_query

def enhance_query_with_grog(query):
    """
    Use Gemini to rephrase or expand the user's query for better search results.
    """
    prompt = (
        f"Rephrase or refine this search query for better with intent base search: {query}. "
        "Keep the response under 75 characters. Return just the enhanced query in plain text, no special characters."
        "Do not include lists, no multiple options, or no bullet points—only one sentence."
    )

    response = cgc.call_groq_api(prompt)
    return response

def detect_and_translate_query(query):
    """
    Uses Gemini to detect the language of the query and translate it into English.
    """
    # Step 1: Detect Language
    detect_prompt = (
        f"Detect the language of the following text and return only the language name: '{query}'"
    )
    detect_response = cg.call_gemini_api(detect_prompt)
    detected_language = detect_response["candidates"][0]["content"]["parts"][0]["text"].strip().lower()

    print(f"Detected Language: {detected_language}")

    # Step 2: Translate to English if necessary
    if detected_language != "english":
        translate_prompt = (
            f"Translate the following text into English only. No other response.:\n\n'{query}'"
        )
        translate_response = cg.call_gemini_api(translate_prompt)
        translated_query = translate_response["candidates"][0]["content"]["parts"][0]["text"].strip()
    else:
        translated_query = query  # No translation needed

    return translated_query

def validate_query_with_gemini_for_content_moderation(query):
    """
    Use Gemini to check if the query contains prohibited content.
    """
    prompt = (
        f"Does the following text contain any prohibited content, such as slang, prohibited drugs or drugs name, or inappropriate language, or scam usage? "
        f"Respond with 'yes' or 'no' only:\n\n'{query}'"
    )
    response = cg.call_gemini_api(prompt)
    validation_result = response["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
    return validation_result == "yes"

def process_query_with_gemini(query):
    """
    Use a single Gemini API call to:
    1. Detect the language of the query.
    2. Translate the query into English (if necessary).
    3. Check if the query contains prohibited content.
    """
    # Combined prompt for all tasks
    prompt = (
        f"Perform the following tasks for the text below:\n\n"
        f"1. Detect the language of the text and return only the language name.\n"
        f"2. If the language is not English, translate the text into English.\n"
        f"3. Check if the text contains prohibited content, such as slang, prohibited drugs, inappropriate language, or scam usage. Respond with 'yes' or 'no'.\n\n"
        f"Text: '{query}'\n\n"
        f"Return the response in the following JSON format:\n"
        f'{{"detected_language": "<language>", "translated_query": "<translated_text>", "contains_prohibited_content": "<yes_or_no>"}}'
    )

    # Call Gemini API
    response = cg.call_gemini_api(prompt)
    print(response["candidates"])

    try:
        # Extract the JSON string from the Markdown code block
        response_text = response["candidates"][0]["content"]["parts"][0]["text"].strip()
        json_str = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL).group(1)

        # Parse the JSON string
        response_data = json.loads(json_str)

        # Extract the results
        detected_language = response_data["detected_language"]
        translated_query = response_data["translated_query"]
        contains_prohibited_content = response_data["contains_prohibited_content"] == "yes"

        print(f"Detected Language: {detected_language}")
        print(f"Translated Query: {translated_query}")
        print(f"Contains Prohibited Content: {contains_prohibited_content}")

        return {
            "detected_language": detected_language,
            "translated_query": translated_query,
            "contains_prohibited_content": contains_prohibited_content,
        }

    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Gemini response: {e}")
        return None

# Use a text-specific model for text embeddings
text_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight and efficient for text

# Use CLIP for image embeddings
image_model = SentenceTransformer('clip-ViT-B-32')

def search_products(query, search_type, threshold):

    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        
        if search_type == "text":

                # Step 1: Process the query with Gemini
            result = process_query_with_gemini(query)
            
            if not result:
                st.error("Failed to process the query. Please try again.")
                return
        
            # Step 2: Check for prohibited content
            if result["contains_prohibited_content"]:
                st.error("Your search contains prohibited content. Please refine your query.")
                return
        
            # Step 3: Use the translated query for search
            translated_query = result["translated_query"]
            print(f"Translated Query: {translated_query}")

            # Enhance the query with Gemini
            enhanced_query = enhance_query_with_gemini(translated_query)
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
            query_embedding = image_model.encode(Image.open(image_buffer).convert("RGB"))
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