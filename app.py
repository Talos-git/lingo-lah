import streamlit as st
import google.generativeai as genai
from lingo_data import lingo_terms_by_category
import os
import time # Import time for simulating streaming

# --- Page Configuration ---
st.set_page_config(
    page_title="Lingo-Lah",
    page_icon="🗣️",
    layout="wide"
)

# --- Title and Description ---
st.title("Lingo-Lah: Your Local Lingo Decoder")
st.write("Explore and understand Malaysian slang and colloquialisms.")

# --- State Management ---
if 'selected_term' not in st.session_state:
    st.session_state.selected_term = None

# Get category names
category_names = list(lingo_terms_by_category.keys())

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = category_names[0] # Set default active tab

# Helper function to update selected term
def select_term(term):
    st.session_state.selected_term = term

# --- Display Category Tabs ---
tabs = st.tabs(category_names)

for i, category_name in enumerate(category_names):
    with tabs[i]:
        st.subheader(category_name)
        terms = lingo_terms_by_category[category_name]

        # Create columns for the grid layout
        cols = st.columns(4) # Adjust number of columns as needed

        # Display lingo term buttons (cards)
        for j, term in enumerate(terms):
            with cols[j % 4]: # Distribute buttons across columns
                # Using a unique key for each button
                if st.button(term, key=f"{category_name}_{term}"):
                    select_term(term)

# --- API Integration and Caching ---
@st.cache_data(show_spinner=False) # Show spinner manually
def get_lingo_details(term: str, country_code: str = "MY"):
    """Fetches lingo details from the LLM with caching."""
    try:
        # Ensure API key is available
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("Google API key not found. Please add it to `.streamlit/secrets.toml`.")
            return {"error": "API key missing"}

        api_key = st.secrets["GEMINI_API_KEY"]
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash') # Using a suitable model

        prompt = f"""Explain the {country_code} slang term '{term}'.
                        Include:
                        1. Meaning
                        2. Typical usage context
                        3. Three example sentences.

                        Format the response clearly with headings for each section."""

        # Use streaming for potentially faster perceived response
        response = model.generate_content(prompt, stream=True)

        # Process streaming response
        full_response = ""
        for chunk in response:
            full_response += chunk.text
            # Simulate streaming display (optional, Streamlit handles this somewhat)
            # time.sleep(0.05) # Small delay to visualize streaming

        # Basic parsing (can be improved based on expected LLM output format)
        # This is a simple split, a more robust parser might be needed
        sections = full_response.split('\n\n')
        details = {}
        current_section = None
        for section in sections:
            lines = section.strip().split('\n')
            if lines:
                header = lines[0].strip().replace(':', '')
                if header in ["Meaning", "Typical usage context", "Example sentences"]:
                     current_section = header
                     details[current_section] = "\n".join(lines[1:]).strip()
                elif current_section:
                     details[current_section] += "\n" + section.strip()


        return details

    except Exception as e:
        st.error(f"An error occurred while fetching details: {e}")
        return {"error": str(e)}


# --- Conditional Display of Details Section ---
if st.session_state.selected_term:
    st.write("---") # Separator
    st.subheader(f"Details for: {st.session_state.selected_term}")

    # Fetch and display details
    with st.spinner("Fetching details..."):
        lingo_details = get_lingo_details(st.session_state.selected_term)

    if "error" in lingo_details:
        st.error(f"Could not fetch details for {st.session_state.selected_term}.")
    else:
        if "Meaning" in lingo_details:
            st.write("**Meaning:**")
            st.write(lingo_details["Meaning"])
        if "Typical usage context" in lingo_details:
            st.write("**Typical Usage Context:**")
            st.write(lingo_details["Typical usage context"])
        if "Example sentences" in lingo_details:
            st.write("**Example Sentences:**")
            # Split example sentences by line for better formatting
            examples = lingo_details["Example sentences"].split('\n')
            for example in examples:
                if example.strip(): # Avoid empty lines
                    st.write(f"- {example.strip()}")

