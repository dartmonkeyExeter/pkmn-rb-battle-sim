from PIL import Image
import os

# Input and output folder
input_folder = "assets/pokemon/back"  # Change this to your folder path
output_folder = "assets/pokemon/back"  # Change this to your folder path
os.makedirs(output_folder, exist_ok=True)

def remove_white_pixels(image_path, output_path):
    img = Image.open(image_path).convert("RGBA")
    data = img.getdata()
    
    new_data = [(248, 248, 248, a) if (r, g, b) == (255, 255, 255) else (r, g, b, a) for r, g, b, a in data]
    img.putdata(new_data)
    img.save(output_path, "PNG")

# Process all images in the input folder
for filename in os.listdir(input_folder):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename.rsplit(".", 1)[0] + ".png")
        remove_white_pixels(input_path, output_path)
        print(f"Processed: {filename}")

print("Done!")
