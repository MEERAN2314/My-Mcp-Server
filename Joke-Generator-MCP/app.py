import streamlit as st
import requests
import time
from datetime import datetime

# Configuration
MCP_SERVER_URL = "http://localhost:8000"

# Initialize session state
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'seen_jokes' not in st.session_state:
    st.session_state.seen_jokes = set()
if 'current_joke' not in st.session_state:
    st.session_state.current_joke = None
if 'server_status' not in st.session_state:
    st.session_state.server_status = "unknown"

# UI Layout
st.set_page_config(
    page_title="Fresh Joke Generator",
    page_icon="😂",
    layout="centered"
)

st.title("😂 Fresh Joke Generator")
st.caption("Powered by Free Joke APIs • MCP Server")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    
    # Get available categories
    try:
        response = requests.get(f"{MCP_SERVER_URL}/categories", timeout=5)
        if response.status_code == 200:
            categories = response.json().get("categories", ["random"])
            st.session_state.server_status = "online"
        else:
            st.session_state.server_status = "unstable"
            categories = ["general", "dad", "programming", "random"]
    except:
        st.session_state.server_status = "offline"
        categories = ["general", "dad", "programming", "random"]
    
    # Status display
    if st.session_state.server_status == "online":
        st.success("✔️ Server Online")
    elif st.session_state.server_status == "unstable":
        st.warning("⚠️ Server Unstable")
    else:
        st.error("❌ Server Offline - Using limited functionality")
    
    category = st.selectbox(
        "Joke Category",
        categories,
        index=categories.index("random") if "random" in categories else 0
    )
    
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", False)
    
    st.header("Favorites")
    if st.session_state.favorites:
        for i, joke in enumerate(st.session_state.favorites):
            cols = st.columns([4, 1])
            cols[0].caption(f"{i+1}. {joke}")
            if cols[1].button("❌", key=f"remove_{i}"):
                st.session_state.favorites.pop(i)
                st.rerun()
    else:
        st.caption("No favorites yet")
    
    if st.button("Clear All Favorites"):
        st.session_state.favorites = []
        st.rerun()

# Main content area
st.subheader("Your Fresh Joke")
joke_placeholder = st.empty()
status_placeholder = st.empty()

# History section
with st.expander("📜 Recent Jokes"):
    if st.session_state.history:
        for i, joke in enumerate(reversed(st.session_state.history)):
            st.caption(f"{len(st.session_state.history)-i}. {joke}")
    else:
        st.caption("No history yet")

def generate_joke():
    try:
        status_placeholder.info("🎭 Fetching a fresh joke...")
        
        response = requests.post(
            f"{MCP_SERVER_URL}/generate",
            json={
                "category": category,
                "exclude_jokes": list(st.session_state.seen_jokes)
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                joke = data["joke"]
                
                # Update UI and state
                joke_placeholder.success(f"**{joke}**")
                st.session_state.current_joke = joke
                st.session_state.history.append(joke)
                st.session_state.seen_jokes.add(joke)
                
                # Keep only last 20 jokes in history
                if len(st.session_state.history) > 20:
                    old_joke = st.session_state.history.pop(0)
                    if old_joke in st.session_state.seen_jokes:
                        st.session_state.seen_jokes.remove(old_joke)
                
                status_placeholder.empty()
                return True
            else:
                joke_placeholder.warning(f"⚠️ {data.get('fallback', 'Joke generation failed')}")
                status_placeholder.error(f"Error: {data.get('error', 'Unknown error')}")
        else:
            error_data = response.json()
            joke_placeholder.warning(f"⚠️ {error_data.get('fallback', 'Why did the chicken cross the road? To get to the other side!')}")
            status_placeholder.error(f"Server error: {error_data.get('error', 'Unknown')}")
            
    except requests.exceptions.RequestException as e:
        joke_placeholder.warning("⚠️ Why did the web server break up with the database? It needed more connection!")
        status_placeholder.error(f"Connection error: {str(e)}")
    except Exception as e:
        joke_placeholder.warning("⚠️ How many programmers does it take to fix a bug? Just one, but they need 5 hours to find it!")
        status_placeholder.error(f"Unexpected error: {str(e)}")
    
    return False

# Generate joke button
if st.button("Generate New Joke", type="primary", use_container_width=True):
    generate_joke()

# Add to favorites button
if st.session_state.current_joke and st.session_state.current_joke not in st.session_state.favorites:
    if st.button("❤️ Add to Favorites", use_container_width=True):
        st.session_state.favorites.append(st.session_state.current_joke)
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    last_refresh = time.time()
    refresh_placeholder = st.empty()
    
    while True:
        current_time = time.time()
        if current_time - last_refresh >= 30:
            if generate_joke():
                last_refresh = current_time
            st.rerun()
        
        refresh_placeholder.caption(f"⏳ Next refresh in {30 - int(current_time - last_refresh)}s")
        time.sleep(1)