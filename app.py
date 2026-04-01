import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
from streamlit_sortables import sort_items

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
    /* Fix for streamlit-sortables visibility in Dark Mode */
    .sortable-item {
        color: #ffffff !important;
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 5px !important;
        padding: 10px !important;
        margin-bottom: 5px !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.title("🎮 Steam Workshop ID Extractor")
st.markdown("""
Extract **Workshop IDs** and **Mod IDs** from Steam Workshop pages in bulk. 
Paste your URLs below (one per line) and click **Process URLs**.
""")

# Session State Initializations
if 'urls_input' not in st.session_state:
    st.session_state.urls_input = ""
if 'all_results' not in st.session_state:
    st.session_state.all_results = []

def clear_text():
    st.session_state.urls_input = ""

def reset_results():
    st.session_state.all_results = []

# Sidebar / Instructions
with st.sidebar:
    st.header("How to use")
    st.info("1. Paste Steam Workshop URLs into the text area.\n2. Click 'Process URLs'.\n3. Copy the semicolon-separated lists or download the CSV.")
    
    st.markdown("### 🛠 Tools")
    st.button("🗑️ Clear URL Input", on_click=clear_text)
    st.button("🧹 Reset Results List", on_click=reset_results)
    
    if st.session_state.all_results:
        # Count enabled vs total
        enabled_count = sum(1 for r in st.session_state.all_results if r.get('Enabled', True))
        st.success(f"Total results: {len(st.session_state.all_results)} ({enabled_count} enabled)")

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
        
        mod_ids = []
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
                        # Find ALL Mod IDs
                        mod_ids = re.findall(r"(?:Mod ID:|ModID:)\s*([^\s\r\n|]+)", desc_text, re.IGNORECASE)
                    
                    if not mod_ids:
                        # Fallback: check raw text
                        mod_ids = re.findall(r"(?:Mod ID:|ModID:)\s*([^\s\r\n|]+)", response.text, re.IGNORECASE)
                    
                    if not mod_ids:
                        mod_ids = ["Not Found"]
                elif response.status_code == 429:
                    mod_ids = ["Error: Rate Limited (429). Wait 1 min."]
                    st.error(f"Steam is rate-limiting your requests (URL: {url}). I'll pause extra long.")
                    time.sleep(5) 
                else:
                    mod_ids = [f"Error: HTTP {response.status_code}"]
            except Exception as e:
                mod_ids = [f"Error: {str(e)}"]
        else:
            mod_ids = ["N/A"]

        # 4. Add a record for EACH Mod ID found (Duplicates Workshop ID if needed)
        for mid in mod_ids:
            results.append({
                "Enabled": True,
                "Order": len(st.session_state.all_results) + len(results) + 1,
                "Workshop ID": workshop_id,
                "Mod ID": mid.strip(),
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
        new_results = extract_ids(urls_list)
        st.session_state.all_results.extend(new_results)
        st.toast(f"✅ Added {len(new_results)} results to the list!")
        st.rerun()

# Display logic for accumulated results
if st.session_state.all_results:
    df = pd.DataFrame(st.session_state.all_results)
    
    # Result Displays
    st.divider()
    st.subheader("🛠 Mod Management Table")
    st.markdown("Use the **'Enabled'** checkbox to toggle mods. They will stay in this list but be **omitted** from the final output below.")
    
    # Use data_editor for interactive reordering and deletion
    edited_df = st.data_editor(
        df,
        width="stretch",
        num_rows="dynamic",
        column_order=["Enabled", "Order", "Workshop ID", "Mod ID", "URL"],
        disabled=["Workshop ID", "URL"], # Keep these fixed
        key="results_editor"
    )
    
    # Check for changes in the data editor
    if not edited_df.equals(df):
        old_results = st.session_state.all_results
        new_results_df = edited_df.copy()
        
        # 1. Handle Deletions/Additions implicitly or explicitly? 
        # Actually, let's just use the current edited_df as the source of truth
        # and re-normalize if needed.
        
        if len(edited_df) != len(df):
            # Row was deleted
            new_results = new_results_df.to_dict('records')
            # Reset order numbers to be sequential
            for idx, r in enumerate(new_results):
                r["Order"] = idx + 1
            st.session_state.all_results = new_results
            st.rerun()
            
        else:
            # Check for specific row Order changes to apply "Smart Shifting"
            changed_idx = -1
            new_order_val = -1
            
            for i in range(len(df)):
                if edited_df.iloc[i]["Order"] != df.iloc[i]["Order"]:
                    changed_idx = i
                    new_order_val = int(edited_df.iloc[i]["Order"])
                    break
            
            if changed_idx != -1:
                # Mod 8 was changed to 3:
                # 1. Pop the item at changed_idx
                # 2. Insert it at new_order_val - 1
                temp_results = old_results.copy()
                moved_item = temp_results.pop(changed_idx)
                
                # Target index is based on the new order value
                target_idx = max(0, min(len(temp_results), new_order_val - 1))
                temp_results.insert(target_idx, moved_item)
                
                # 3. Re-normalize all order numbers
                for idx, r in enumerate(temp_results):
                    r["Order"] = idx + 1
                    
                st.session_state.all_results = temp_results
                st.rerun()
            else:
                # Other edits (like toggling 'Enabled' or changing 'Mod ID')
                st.session_state.all_results = edited_df.to_dict('records')
                st.rerun()

    # --- DRAG AND DROP REORDERING (Commented Out for now) ---
    # st.subheader("🔃 Drag-and-Drop Reorder")
    # with st.expander("Open Reorder Menu"):
    #     st.info("Grab a mod and drag it to swap positions. This will automatically update your table and final lists!")
    #     sortable_items = [f"{r['Mod ID']} (Workshop ID: {r['Workshop ID']})" for r in st.session_state.all_results if r.get('Enabled', True)]
    #     new_sorted_labels = sort_items(sortable_items, direction="vertical", key="drag_reorder")
    #     if new_sorted_labels != sortable_items:
    #         lookup = {f"{r['Mod ID']} (Workshop ID: {r['Workshop ID']})": r for r in st.session_state.all_results}
    #         new_all_results = []
    #         for idx, label in enumerate(new_sorted_labels):
    #             record = lookup[label]
    #             record["Order"] = idx + 1
    #             new_all_results.append(record)
    #         st.session_state.all_results = new_all_results
    #         st.rerun()

    # Final Display Logic (Filter by Enabled)
    df = pd.DataFrame(st.session_state.all_results)
    active_df = df[df["Enabled"] == True]
    
    # Semicolon-separated lists
    st.subheader("📋 Final Formatted Lists")
    if not active_df.empty:
        workshop_list_str = ";".join(active_df['Workshop ID'].astype(str).tolist()) + ";"
        mod_list_str = ";".join(active_df['Mod ID'].astype(str).tolist()) + ";"
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Workshop list:**")
            st.code(workshop_list_str, language="text")
            
        with col2:
            st.markdown("**ModID list:**")
            st.code(mod_list_str, language="text")
            
        # CSV Download Button
        csv = active_df.to_dict('records')
        csv_df = pd.DataFrame(csv)
        st.download_button(
            label="📥 Download Enabled Mods (CSV)",
            data=csv_df.to_csv(index=False).encode('utf-8'),
            file_name='enabled_steam_workshop_ids.csv',
            mime='text/csv',
        )
    else:
        st.warning("No mods are currently enabled. Check the 'Enabled' box in the table above to include them.")

st.divider()
st.caption("Developed with ❤️ for Steam Workshop enthusiasts.")
