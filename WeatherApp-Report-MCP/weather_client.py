import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"  # Update if hosted elsewhere

st.set_page_config(page_title="Weather UI", page_icon="⛅", layout="centered")

st.title("🌤️ Weather Report")

city = st.text_input("Enter city name", placeholder="e.g. London")

if st.button("Get Weather"):
    if not city.strip():
        st.warning("Please enter a valid city name.")
    else:
        with st.spinner("Fetching weather..."):
            try:
                response = requests.get(f"{BASE_URL}/weather", params={"city": city})
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        st.error(f"Error: {data['error']}")
                    else:
                        st.success(f"Weather in {data['city']}")
                        st.metric(label="🌡️ Temperature", value=f"{data['temperature_C']} °C")
                        st.write(f"🌥️ Condition: {data['weather'].title()}")
                else:
                    st.error(f"Request failed with status code {response.status_code}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
