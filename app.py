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

@st.cache_data(show_spinner=False)
def get_lingo_details_raw(term: str, country_code: str = "MY"):
    """Fetches lingo details as a raw string from the LLM with caching."""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("Google API key not found. Please add it to `.streamlit/secrets.toml`.")
            return {"error": "API key missing"}

        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # Consider using cache_resource for the model if removing cache_data
        model = genai.GenerativeModel('gemini-2.0-flash') 

        # --- Modified Prompt ---
        prompt = f"""Explain the {country_code} slang term '{term}'.

                    Structure the response using Markdown:
                    ## Meaning
                    Provide the definition here.

                    ## Typical Usage Context
                    Describe when and how it's typically used.

                    ## Example Sentences
                    Provide three numbered example sentences:
                    1. Example 1
                    2. Example 2
                    3. Example 3

                    Keep the explanation clear and concise.
                    """

        response = model.generate_content(prompt, stream=True)

        full_response = ""
        for chunk in response:
             # Add check for text attribute
            if hasattr(chunk, 'text') and chunk.text:
                full_response += chunk.text
            # If you want *visual* streaming like app2, you can't use cache_data easily
            # and need to update a placeholder here. See note below.

        return {"response": full_response} # Return the full response string

    except Exception as e:
        st.error(f"An error occurred while fetching details: {e}")
        return {"error": str(e)}

# --- Conditional Display of Details Section ---
if st.session_state.selected_term:
    st.write("---") # Separator
    st.subheader(f"Details for: {st.session_state.selected_term}")

    # Placeholder for potential streaming display (optional)
    details_placeholder = st.empty()

    with st.spinner(f"Fetching details for '{st.session_state.selected_term}'..."):
        # Call the modified function
        result = get_lingo_details_raw(st.session_state.selected_term)

    if "error" in result:
        details_placeholder.error(f"Could not fetch details for {st.session_state.selected_term}. Error: {result['error']}")
    elif "response" in result:
        # Display the raw response using markdown
        details_placeholder.markdown(result["response"])
    else:
         details_placeholder.error(f"Received an unexpected result for {st.session_state.selected_term}.")

    # Optional: Add rerun if you experience state issues,
    # though likely not needed with this simpler display logic.
    # st.rerun()
