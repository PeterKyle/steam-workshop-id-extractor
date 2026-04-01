import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

# Page Configuration
st.set_page_config(
    page_title="Steam Workshop Extractor",
    page_icon="🎮",
    layout="wide",
)

# Custom CSS for Gaming Aesthetic
st.markdown("""
<style>
    /* Dark Gaming Theme */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stTextArea textarea {
        background-color: #161b22;
        color: #58a6ff;
        border: 1px solid #30363d;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border: none;
    }
    .stDataFrame {
        border: 1px solid #30363d;
    }
    h1, h2, h3 {
        color: #58a6ff;
    }
    .stProgress > div > div > div > div {
        background-color: #238636;
    }
    /* Custom ID lists styling */
    .id-list-container {
        background-color: #161b22;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #30363d;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("🎮 Steam Workshop ID Extractor")
st.markdown("""
Extract **Workshop IDs** and **Mod IDs** from Steam Workshop pages in bulk. 
Paste your URLs below (one per line) and click **Process URLs**.
""")

# Session State for Input
if 'urls_input' not in st.session_state:
    st.session_state.urls_input = ""

def clear_text():
    st.session_state.urls_input = ""

# Sidebar / Instructions
with st.sidebar:
    st.header("How to use")
    st.info("1. Paste Steam Workshop URLs into the text area.\n2. Click 'Process URLs'.\n3. Copy the semicolon-separated lists or download the CSV.")
    st.button("🗑️ Clear All", on_click=clear_text)

# Input Area
urls_text = st.text_area("Workshop URLs", value=st.session_state.urls_input, height=200, key="urls_input_area", help="One URL per line")

# Update session state if text area changes
if urls_text != st.session_state.urls_input:
    st.session_state.urls_input = urls_text

# Regex Patterns
WORKSHOP_ID_REGEX = re.compile(r"id=(\d+)")
MOD_ID_REGEX = re.compile(r"(?:Mod ID:|ModID:)\s*(.+)", re.IGNORECASE)

def extract_ids(urls):
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, url in enumerate(urls):
        url = url.strip()
        if not url:
            continue
            
        status_text.text(f"Processing ({i+1}/{len(urls)}): {url}")
        
        # 1. Extract Workshop ID from URL
        workshop_id_match = WORKSHOP_ID_REGEX.search(url)
        workshop_id = workshop_id_match.group(1) if workshop_id_match else "N/A"
        
        mod_id = "Not Found"
        if workshop_id != "N/A":
            try:
                # 2. Fetch Page Content
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 3. Scrape Workshop Item Description (using separator to prevent mashing)
                    desc_div = soup.find('div', class_='workshopItemDescription') or soup.find(id='workshopItemDescription')
                    if desc_div:
                        # Use separator to ensure words stay separate
                        desc_text = desc_div.get_text(separator=' ')
                        # Refined regex: capture text after "Mod ID:" until the next space or line break
                        mod_id_match = re.search(r"(?:Mod ID:|ModID:)\s*([^\s\r\n|]+)", desc_text, re.IGNORECASE)
                        if mod_id_match:
                            mod_id = mod_id_match.group(1).strip()
                        else:
                            # Fallback: check raw text
                            fallback_match = re.search(r"(?:Mod ID:|ModID:)\s*([^\s\r\n|]+)", response.text, re.IGNORECASE)
                            if fallback_match:
                                mod_id = fallback_match.group(1).strip()
                elif response.status_code == 429:
                    mod_id = "Error: Rate Limited (429). Wait 1 min."
                    st.error("Steam is rate-limiting your requests. I'll pause extra long between the next ones.")
                    time.sleep(5) # Extra pause on 429
                else:
                    mod_id = f"Error: HTTP {response.status_code}"
            except Exception as e:
                mod_id = f"Error: {str(e)}"
        
        results.append({
            "Workshop ID": workshop_id,
            "Mod ID": mod_id,
            "URL": url
        })
        
        progress_bar.progress((i + 1) / len(urls))
        # Rate limiting: 5-second pause to be extremely safe
        time.sleep(5.0)
        
    status_text.text("Extraction complete!")
    return results

if st.button("🚀 Process URLs"):
    urls_list = [u for u in urls_text.split("\n") if u.strip()]
    
    if not urls_list:
        st.warning("Please enter at least one URL.")
    else:
        results = extract_ids(urls_list)
        df = pd.DataFrame(results)
        
        # Result Displays
        st.subheader("Results Table")
        st.dataframe(df, use_container_width=True)
        
        # Semicolon-separated lists
        st.subheader("Formatted Lists")
        
        # Ensure correct order by iterating through the results
        workshop_ids = [str(r['Workshop ID']) for r in results if r['Workshop ID'] != "N/A"]
        mod_ids = [str(r['Mod ID']) for r in results if r['Mod ID'] != "Not Found" and not str(r['Mod ID']).startswith("Error")]
        
        # Note: The user said "Make sure Workshop ID1 and ModID1 are from the same URL"
        # Since I'm processing sequentially, I should probably keep them aligned.
        # If I filter out failures, they might get misaligned if one mod has a workshop ID but no mod ID.
        # Let's keep them perfectly aligned by including placeholders if necessary, OR
        # just join them based on the dataframe which is already ordered.
        
        workshop_list_str = ";".join(df['Workshop ID'].tolist()) + ";"
        mod_list_str = ";".join(df['Mod ID'].tolist()) + ";"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Workshop list:**")
            st.code(workshop_list_str, language="text")
            
        with col2:
            st.markdown("**ModID list:**")
            st.code(mod_list_str, language="text")
            
        # CSV Download Button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name='steam_workshop_ids.csv',
            mime='text/csv',
        )

st.divider()
st.caption("Developed with ❤️ for Steam Workshop enthusiasts.")
