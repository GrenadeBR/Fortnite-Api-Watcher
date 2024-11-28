import json
import requests
import time
import os
import logging
from colorama import Fore
from deepdiff import DeepDiff  # Import for comparing JSON objects


# Configure logging to print to both the terminal and a file
logging.basicConfig(
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.FileHandler('monitor.log'),  # File handler for logging to a file
        logging.StreamHandler()  # Stream handler for logging to the console
    ]
)

# File paths
data_file_path = "data.json"
image_data_file_path = "imagedata.json"
new_data_file_path = "newdata.json"  # File for saving only changes
images_folder = "images"

# Endpoint URL
endpoint_url = "https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game"

def load_local_data(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Return an empty structure if the file does not exist
        return [] if 'imagedata' in file_path else {}

def save_data(file_path, data):
    """Save data to a JSON file."""
    # Remove duplicates before saving
    if isinstance(data, list):
        data = list(set(data))
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def fetch_api_data():
    """Fetch data from the API endpoint."""
    try:
        response = requests.get(endpoint_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching data from API: {e}")
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
    return urls

def download_images(image_urls):
    """Download images and save them to the 'images' folder."""
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    for url in image_urls:
        image_name = url.split("/")[-1]
        image_path = os.path.join(images_folder, image_name)

        if not os.path.exists(image_path):
            try:
                img_response = requests.get(url)
                img_response.raise_for_status()
                with open(image_path, 'wb') as img_file:
                    img_file.write(img_response.content)
                logging.info(Fore.GREEN + "Downloaded " + Fore.WHITE + f"Image: {image_name}")
            except requests.RequestException as e:
                logging.error(f"Error downloading image {image_name}: {e}")
        else:
            logging.info(Fore.LIGHTBLUE_EX + f"Image {image_name} already exists. Skipping download.")


    
def get_differences(old_data, new_data):
    """Get the differences between the old and new JSON data."""
    diff = DeepDiff(old_data, new_data, ignore_order=True)
    changes = {}

    # Extract only meaningful changes (added, changed, values)
    if 'values_changed' in diff:
        changes.update(diff['values_changed'])

    if 'dictionary_item_added' in diff:
        for key_path in diff['dictionary_item_added']:
            keys = key_path.replace('root', '').strip('[]').split('][')
            value = new_data
            try:
                # Traverse the nested structure using the parsed keys
                for k in keys:
                    k = k.strip("'")
                    value = value[k]
                changes[key_path] = value
            except (KeyError, TypeError):
                logging.error(f"Failed to access nested path: {key_path}")
                continue

    return changes


def monitor_changes():
    """Monitor the API data for changes and handle image comparison."""
    while True:
        # Always load local data at the beginning of each loop iteration
        local_data = load_local_data(data_file_path)

        # Fetch the current data from the API
        api_data = fetch_api_data()

        if api_data is not None:
            if api_data != local_data:
                logging.info("New Changes found in" + Fore.GREEN + " API " + Fore.WHITE + "data!")
                
                # Get and save only the differences to newdata.json
                differences = get_differences(local_data, api_data)
                if differences:
                    save_data(new_data_file_path, differences)

                # Save new data to data.json
                save_data(data_file_path, api_data)

                # Load image data from imagedata.json
                current_image_data = load_local_data(image_data_file_path)

                # Extract image URLs from the updated data.json
                new_image_urls = extract_image_urls(api_data)

                # Remove duplicates from new image URLs
                new_image_urls = list(set(new_image_urls))

                # Compare with imagedata.json
                if set(new_image_urls) == set(current_image_data):
                    logging.info("Same images, nothing new.")
                else:
                    new_urls = [url for url in new_image_urls if url not in current_image_data]
                    if new_urls:
                        logging.info("New" + Fore.GREEN + " Images " + Fore.WHITE + "found:")
                        for url in new_urls:
                            logging.info(url)
                        download_images(new_urls)
                        # Update imagedata.json with unique URLs
                        updated_image_data = list(set(current_image_data + new_image_urls))
                        save_data(image_data_file_path, updated_image_data)

            else:
                logging.info("Watching for" + Fore.LIGHTBLUE_EX + " Changes " + Fore.WHITE + "in the" + Fore.GREEN + " API")
        
        # Wait for 5 seconds before checking again
        time.sleep(5)

# Start monitoring
monitor_changes()
