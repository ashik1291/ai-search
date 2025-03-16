from sentence_transformers import SentenceTransformer
from PIL import Image
import torch
import os
from torchvision import models, transforms

# Create an images folder if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Load a pre-trained ResNet model for image embeddings
image_model = models.resnet50(pretrained=True)
image_model.eval()

# Preprocess the image for the model
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def preprocess_and_save_image(image_path, output_folder="images", size=(500, 500)):
    """
    Resize an image to the specified size and save it to the output folder.
    Returns the path to the saved image.
    """
    with Image.open(image_path) as img:
        img = img.resize(size)
        output_path = os.path.join(output_folder, os.path.basename(image_path))
        img.save(output_path)
        print(f"Processed image saved to {output_path}")
        return output_path

def generate_image_embedding(image_path):
    """
    Generate an embedding for an image using a pre-trained ResNet model.
    """
    with Image.open(image_path) as img:
        input_tensor = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            embedding = image_model(input_tensor)
        return embedding.squeeze().tolist()