import json
import requests

# File path to save image data
image_data_file_path = "imagedata.json"

# Endpoint URL
endpoint_url = "https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game"

def fetch_api_data():
    """Fetch data from the API endpoint."""
    try:
        response = requests.get(endpoint_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

def extract_image_urls(data):
    """Extract image URLs from the API data."""
    urls = []
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

    def find_urls(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                find_urls(value)
        elif isinstance(obj, list):
            for item in obj:
                find_urls(item)
        elif isinstance(obj, str) and obj.startswith("http") and any(ext in obj for ext in image_extensions):
            urls.append(obj)
    
    find_urls(data)
    return list(set(urls))  # Remove duplicates by converting to a set and back to a list

def save_image_urls(image_urls):
    """Save image URLs to the imagedata.json file."""
    with open(image_data_file_path, 'w') as file:
        json.dump(image_urls, file, indent=4)

# Main logic
api_data = fetch_api_data()
if api_data:
    image_urls = extract_image_urls(api_data)
    if image_urls:
        save_image_urls(image_urls)
        print(f"Extracted and saved {len(image_urls)} image URLs to {image_data_file_path}.")
    else:
        print("No image URLs found in the API data.")
else:
    print("Failed to fetch or process API data.")
