import streamlit as st
import insert_product as ip
import search_product as sp
from PIL import Image
import os
import requests
from io import BytesIO

# Set the browser tab title
st.set_page_config(page_title="AI Powered Search")

def main():
    # Disable file watcher for better performance
    os.environ["STREAMLIT_WATCHFILE"] = "false"
    
    st.title("Product Search and Insert")
    
    # Define the menu options
    menu = ["Insert Product", "Search Product"]
    
    # Display the menu in the sidebar
    st.sidebar.title("Menu")
    
    # Use session state to track the current page
    if "current_page" not in st.session_state:
        st.session_state.current_page = menu[0]  # Default to "Insert Product"
    
    # Display menu options as buttons in the sidebar
    for option in menu:
        if st.sidebar.button(option, disabled=(st.session_state.current_page == option)):
            st.session_state.current_page = option
    
    # Display the selected page content
    if st.session_state.current_page == "Insert Product":
        st.subheader("Insert Product")
        name = st.text_input("Product Name")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])
        
        if st.button("Insert"):
            if uploaded_file is not None and name and category and price:
                image_path = os.path.join("images", uploaded_file.name)
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                ip.insert_product(image_path, name, category, price)
            else:
                st.error("Please fill all fields and upload an image.")
    
    elif st.session_state.current_page == "Search Product":
        st.subheader("Search Product")
        search_type = st.radio("Search by", ["Text", "Image Upload", "Image URL"])
        threshold = st.slider("Certainty Threshold", min_value=0.0, max_value=1.0, value=0.5)
        
        if search_type == "Text":
            query = st.text_input("Enter search text")
            if st.button("Search"):
                if query:
                    sp.search_products(query, "text", threshold)
                else:
                    st.error("Please enter a search query.")
        
        elif search_type == "Image Upload":
            uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
            if st.button("Search"):
                if uploaded_file is not None:
                    image_path = os.path.join("images", uploaded_file.name)
                    with open(image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    sp.search_products(image_path, "image", threshold)
                else:
                    st.error("Please upload an image.")
        
        elif search_type == "Image URL":
            image_url = st.text_input("Enter image URL")
            if st.button("Search"):
                if image_url:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image = Image.open(BytesIO(response.content))
                        image_path = os.path.join("images", "temp_image.jpg")
                        image.save(image_path)
                        sp.search_products(image_path, "image", threshold)
                    else:
                        st.error("Failed to download image from URL.")
                else:
                    st.error("Please enter an image URL.")

if __name__ == "__main__":
    main()