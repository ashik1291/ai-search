import streamlit as st
import insert_product as ip
import search_product as sp
from PIL import Image
import os
import requests
from io import BytesIO
import weaviate

# Set the browser tab title and favicon
st.set_page_config(
    page_title="AI Powered Search",
    page_icon="🔍",  # Use a search emoji as the favicon
    layout="wide"  # Use a wide layout for better UI
)

def fetch_all_products():
    """
    Fetch all products from the Weaviate database.
    """
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        response = product_collection.query.fetch_objects()
        return response.objects
    finally:
        client.close()

def fetch_products_paginated(page, page_size=5):
    """
    Fetch paginated products from Weaviate.
    """
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        offset = (page - 1) * page_size  # Calculate offset based on the page number

        response = product_collection.query.fetch_objects(
            limit=page_size,
            offset=offset
        )

        return response.objects
    finally:
        client.close()

def delete_product(product_id):
    """
    Delete a product from the Weaviate database by its ID.
    """
    client = weaviate.connect_to_local()
    try:
        product_collection = client.collections.get("Product")
        product_collection.data.delete_by_id(product_id)
        st.success(f"Product with ID {product_id} deleted successfully!")
    except Exception as e:
        st.error(f"Error deleting product: {e}")
    finally:
        client.close()

def main():
    # Disable file watcher for better performance
    os.environ["STREAMLIT_WATCHFILE"] = "false"
    # st.cache_data.clear()
    
    # Custom CSS for better UI
    st.markdown(
        """
        <style>
        /* General styling */
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
        }
        .stButton button {
            background-color: #6c5ce7;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            transition: background-color 0.3s ease;
        }
        .stButton button:hover {
            background-color: #5a4acf;
        }
        .stTextInput input, .stNumberInput input {
            border-radius: 8px;
            padding: 10px;
            border: 1px solid #ddd;
        }
        .stFileUploader label {
            font-size: 16px;
        }
        .stMarkdown h1 {
            color: #2d3436;
        }
        .stMarkdown h2 {
            color: #6c5ce7;
        }
        /* Product card styling */
        .product-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
        }
        .product-image {
            flex: 1;
            max-width: 200px;
            margin-right: 20px;
        }
        .product-details {
            flex: 3;
        }
        .product-details h3 {
            margin: 0;
            color: #2d3436;
        }
        .product-details p {
            margin: 5px 0;
            color: #636e72;
        }
        .delete-button {
            background-color: #ff7675 !important;  /* Custom red color */
            color: white !important;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            transition: background-color 0.3s ease;
        }
        .delete-button:hover {
            background-color: #e84343 !important;  /* Darker red on hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    
    # Main title
    st.title("🛍️ Manage Products with AI")
    
    # Define the menu options
    menu = ["Insert Product", "Search Product", "View Products"]
    
    # Display the menu in the sidebar
    st.sidebar.title("Menu")
    
    # Use session state to track the current page
    if "current_page" not in st.session_state:
        st.session_state.current_page = menu[1]  # Default to "Search Product"
    
    # Display menu options as buttons in the sidebar
    for option in menu:
        if st.sidebar.button(option, key=f"menu_{option}"):
            st.session_state.current_page = option  # Update the current page
    
    # Display the selected page content
    if st.session_state.current_page == "Insert Product":
        st.subheader("📤 Insert Product")
        name = st.text_input("Product Name")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        uploaded_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])
        
        if st.button("Insert"):
            if uploaded_file is not None and name and category and price:
                image_path = os.path.join("images/product", uploaded_file.name)
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                ip.insert_product(image_path, name, category, price)
                st.success("Product inserted successfully!")
            else:
                st.error("Please fill all fields and upload an image.")
    
    elif st.session_state.current_page == "Search Product":

        st.subheader("🔍 Search Product")
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
                if uploaded_file:
                    image_path = os.path.join("images/searched", uploaded_file.name)
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
    
    elif st.session_state.current_page == "View Products":
        if "page" not in st.session_state:
            st.session_state.page = 1
        if "page_size" not in st.session_state:
            st.session_state.page_size = 2
        st.subheader("📦 View Products")
        products = fetch_products_paginated(st.session_state.page, st.session_state.page_size)
        
        if not products:
            st.write("No products found.")
        else:
            for product in products:
                # Create a card-like layout for each product
                col1, col2, col3 = st.columns([2, 4, 1])
                
                with col1:
                    # Display the product image
                    st.image(product.properties['image_path'], width=150)
                
                with col2:
                    # Display product details
                    st.write(f"**Name:** {product.properties['name']}")
                    st.write(f"**Category:** {product.properties['category']}")
                    st.write(f"**Price:** ${product.properties['price']:.2f}")
                
                with col3:
                    # Add a delete button with custom red color
                    if st.button(
                        "Delete",
                        key=f"delete_{product.uuid}",
                        help=f"Delete {product.properties['name']}",
                        type="primary",  # Makes the button red
                    ):
                        delete_product(product.uuid)
                        st.rerun()  # Refresh the page after deletion
                
                st.write("---")
                # Pagination Controls
                col_prev, col_next = st.columns(2)

                with col_prev:
                    if st.session_state.page > 1:
                        if st.button("⬅️ Previous Page"):
                            st.session_state.page -= 1
                            st.rerun()

                with col_next:
                    if len(products) == st.session_state.page_size:  # Check if more results exist
                        if st.button("Next Page ➡️"):
                            st.session_state.page += 1
                            st.rerun()

if __name__ == "__main__":
    main()