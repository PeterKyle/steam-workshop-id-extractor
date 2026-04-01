import requests
from bs4 import BeautifulSoup
import re

WORKSHOP_ID_REGEX = re.compile(r"id=(\d+)")
MOD_ID_REGEX = re.compile(r"(?:Mod ID:|ModID:)\s*(.+)", re.IGNORECASE)

def test_extraction(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 1. Extract Workshop ID from URL
    workshop_id_match = WORKSHOP_ID_REGEX.search(url)
    workshop_id = workshop_id_match.group(1) if workshop_id_match else "N/A"
    print(f"Workshop ID: {workshop_id}")
    
    if workshop_id != "N/A":
        try:
            # 2. Fetch Page Content
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 3. Scrape Workshop Item Description
                desc_div = soup.find(id='workshopItemDescription')
                if desc_div:
                    desc_text = desc_div.get_text()
                    print(f"Description sample: {desc_text[:100]}...")
                    mod_id_match = MOD_ID_REGEX.search(desc_text)
                    if mod_id_match:
                        mod_id = mod_id_match.group(1).strip()
                        print(f"Mod ID Found: {mod_id}")
                    else:
                        print("Mod ID not found in description.")
                else:
                    print("Description div not found.")
            else:
                print(f"Error fetching page: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

# Example Project Zomboid Mod (known to have Mod ID)
test_url = "https://steamcommunity.com/sharedfiles/filedetails/?id=2313387159" # Common Sense
test_extraction(test_url)
