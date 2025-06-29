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
if 'seen_facts' not in st.session_state:
    st.session_state.seen_facts = set()
if 'current_fact' not in st.session_state:
    st.session_state.current_fact = None
if 'server_status' not in st.session_state:
    st.session_state.server_status = "unknown"

# UI Layout
st.set_page_config(
    page_title="Amazing Fact Generator",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 Amazing Fact Generator")
st.caption("Powered by MCP Server • Learn something new every time")

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
            categories = ["science", "history", "animal", "random"]
    except:
        st.session_state.server_status = "offline"
        categories = ["science", "history", "animal", "random"]
    
    # Status display
    if st.session_state.server_status == "online":
        st.success("✔️ Server Online")
    elif st.session_state.server_status == "unstable":
        st.warning("⚠️ Server Unstable")
    else:
        st.error("❌ Server Offline - Using limited functionality")
    
    category = st.selectbox(
        "Fact Category",
        categories,
        index=categories.index("random") if "random" in categories else 0
    )
    
    auto_refresh = st.checkbox("Auto-refresh every 45 seconds", False)
    
    st.header("Favorites")
    if st.session_state.favorites:
        for i, fact in enumerate(st.session_state.favorites):
            cols = st.columns([4, 1])
            cols[0].caption(f"{i+1}. {fact}")
            if cols[1].button("❌", key=f"remove_{i}"):
                st.session_state.favorites.pop(i)
                st.rerun()
    else:
        st.caption("No favorites yet")
    
    if st.button("Clear All Favorites"):
        st.session_state.favorites = []
        st.rerun()

# Main content area
st.subheader("Today's Fascinating Fact")
fact_placeholder = st.empty()
status_placeholder = st.empty()

# History section
with st.expander("📜 Recent Facts"):
    if st.session_state.history:
        for i, fact in enumerate(reversed(st.session_state.history)):
            st.caption(f"{len(st.session_state.history)-i}. {fact}")
    else:
        st.caption("No history yet")

def generate_fact():
    try:
        status_placeholder.info("🔍 Discovering a new fact...")
        
        response = requests.post(
            f"{MCP_SERVER_URL}/generate",
            json={
                "category": category,
                "exclude_facts": list(st.session_state.seen_facts)
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                fact = data["fact"]
                
                # Update UI and state
                fact_placeholder.success(f"**{fact}**")
                st.session_state.current_fact = fact
                st.session_state.history.append(fact)
                st.session_state.seen_facts.add(fact)
                
                # Keep only last 15 facts in history
                if len(st.session_state.history) > 15:
                    old_fact = st.session_state.history.pop(0)
                    if old_fact in st.session_state.seen_facts:
                        st.session_state.seen_facts.remove(old_fact)
                
                status_placeholder.empty()
                return True
            else:
                fact_placeholder.warning(f"⚠️ {data.get('fallback', 'Fact generation failed')}")
                status_placeholder.error(f"Error: {data.get('error', 'Unknown error')}")
        else:
            error_data = response.json()
            fact_placeholder.warning(f"⚠️ {error_data.get('fallback', 'The average person will spend 6 months of their life waiting for red lights to turn green.')}")
            status_placeholder.error(f"Server error: {error_data.get('error', 'Unknown')}")
            
    except requests.exceptions.RequestException as e:
        fact_placeholder.warning("⚠️ Did you know? The first computer bug was an actual moth stuck in a Harvard Mark II computer in 1947!")
        status_placeholder.error(f"Connection error: {str(e)}")
    except Exception as e:
        fact_placeholder.warning("⚠️ Fun fact: The shortest war in history lasted only 38 minutes!")
        status_placeholder.error(f"Unexpected error: {str(e)}")
    
    return False

# Generate fact button
if st.button("Discover New Fact", type="primary", use_container_width=True):
    generate_fact()

# Add to favorites button
if st.session_state.current_fact and st.session_state.current_fact not in st.session_state.favorites:
    if st.button("❤️ Add to Favorites", use_container_width=True):
        st.session_state.favorites.append(st.session_state.current_fact)
        st.rerun()

# Auto-refresh logic
if auto_refresh:
    last_refresh = time.time()
    refresh_placeholder = st.empty()
    
    while True:
        current_time = time.time()
        if current_time - last_refresh >= 45:
            if generate_fact():
                last_refresh = current_time
            st.rerun()
        
        refresh_placeholder.caption(f"⏳ Next refresh in {45 - int(current_time - last_refresh)}s")
        time.sleep(1)