import streamlit as st
import google.generativeai as genai
from lingo_data import lingo_terms_by_category
import os
# Removed time import as it's not used for simulation anymore

# --- Page Configuration ---
st.set_page_config(
    page_title="Lingo-Lah",
    page_icon="🗣️",
    layout="wide"
)

# --- Title and Description ---
st.title("Lingo-Lah: Your Local Lingo Guide")
st.write("Explore and understand Malaysian slang or lingo that locals use in their everyday life.")

# --- State Management ---
# Initialize selected term state
if 'selected_term' not in st.session_state:
    st.session_state.selected_term = None

# Initialize the cache dictionary in session state if it doesn't exist
if 'lingo_cache' not in st.session_state:
    st.session_state.lingo_cache = {} # Use this to store term -> explanation

# Get category names
category_names = list(lingo_terms_by_category.keys())

# Set default active tab state (optional, but good practice)
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = category_names[0]

# Helper function to update selected term
def select_term(term):
    st.session_state.selected_term = term
    # Optional: could clear cache here if needed, but usually not for this use case
    # if 'lingo_cache' in st.session_state:
    #     del st.session_state.lingo_cache

# --- API Configuration (Using @st.cache_resource for the model) ---
@st.cache_resource # Cache the model resource initialization
def get_gemini_model():
    """Initializes and returns the Gemini model client."""
    try:
        # Ensure API key is available via Streamlit secrets
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("Google API key not found. Please add it to `.streamlit/secrets.toml`.")
            return None # Indicate failure

        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # Consider using a specific model version if needed
        # Using gemini-1.5-flash as it's often a good balance of speed and capability
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model
    except Exception as e:
        st.error(f"Failed to initialize Gemini model: {e}")
        return None

# Get the model (will be cached after the first run)
model = get_gemini_model()

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

# --- Conditional Display of Details Section (with Session State Caching) ---
if st.session_state.selected_term:
    st.write("---") # Separator
    st.subheader(f"Details for: {st.session_state.selected_term}")

    # Placeholder for display
    details_placeholder = st.empty()
    term = st.session_state.selected_term
    country_code = "MY" # Assuming Malaysian context

    # 1. Check if the result is already in the session cache
    if term in st.session_state.lingo_cache:
        # --- Cache Hit ---
        # Display cached result instantly
        details_placeholder.markdown(st.session_state.lingo_cache[term])
        # Optional: Indicate it came from cache for debugging/info
        # st.caption("Displayed from session cache.")

    # 2. If not cached AND the model is available, fetch from API
    elif model:
        # --- Cache Miss ---
        try:
            # --- Define the Prompt ---
            prompt = f"""Explain the {country_code} slang term '{term}'.

                        Structure the response using Markdown:
                        ### Meaning
                        Provide the definition here.

                        ### Typical Usage Context
                        Describe when and how it's typically used.

                        ### Example Sentences
                        Provide three numbered example sentences:
                        1. Example 1
                        2. Example 2
                        3. Example 3

                        Keep the explanation clear and concise.
                        """

            # --- Streaming Call and Display Update ---
            response = model.generate_content(prompt, stream=True)

            full_response = ""
            for chunk in response:
                # Check if the chunk has text content
                if hasattr(chunk, 'text') and chunk.text:
                    full_response += chunk.text
                    # Update placeholder on each chunk for visual streaming effect
                    details_placeholder.markdown(full_response + "▌") # Add cursor

            # Final update to remove the cursor
            details_placeholder.markdown(full_response)

            # --- Store the successful result in the session cache ---
            st.session_state.lingo_cache[term] = full_response

        except Exception as e:
            details_placeholder.error(f"An error occurred while fetching details for {term}: {e}")
            # Optionally clear the failed term from cache if needed
            # if term in st.session_state.lingo_cache:
            #     del st.session_state.lingo_cache[term]

    # 3. Handle case where the model failed to initialize
    else:
         details_placeholder.error("Lingo details cannot be fetched because the Gemini model is not available.")