#app.py
import streamlit as st
import google.generativeai as genai
from lingo_data import lingo_terms_by_category # Assuming this file exists and is structured correctly
import os
# Removed time import as it's not used

# --- Page Configuration ---
st.set_page_config(
    page_title="Lingo-Lah",
    page_icon="🗣️",
    layout="wide"
)

# --- REMOVED CSS for Horizontal Scrolling Buttons ---
# The previous CSS block targeting stHorizontalBlock is removed as it's no longer needed.

# --- Title and Description ---
st.title("Lingo-Lah: Your Local Lingo Guide")
st.write("Explore and understand Malaysian slang or lingo that locals use in their everyday life.")

# --- State Management ---
# REMOVED 'selected_term' state - selection is handled by active tab
# if 'selected_term' not in st.session_state:
#     st.session_state.selected_term = None

# Initialize the cache dictionary in session state if it doesn't exist
if 'lingo_cache' not in st.session_state:
    st.session_state.lingo_cache = {} # Use this to store term -> explanation

# Get category names from your data structure
category_names = list(lingo_terms_by_category.keys())

# REMOVED 'active_tab' state - not needed for this structure
# REMOVED select_term function - no longer needed

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
        model = genai.GenerativeModel('gemini-2.0-flash') 
        return model
    except Exception as e:
        st.error(f"Failed to initialize Gemini model: {e}")
        return None

# Get the model (will be cached after the first run)
model = get_gemini_model()

# --- Display Category Tabs ---
if category_names: # Only display tabs if there are categories
    category_tabs = st.tabs(category_names) # Renamed for clarity

    for i, category_name in enumerate(category_names):
        with category_tabs[i]:
            # Optional: Keep subheader for category context if desired
            # st.subheader(category_name)
            terms = lingo_terms_by_category.get(category_name, []) # Safely get terms

            # --- Implement Nested Term Tabs ---
            if terms: # Check if there are terms in this category
                term_tabs = st.tabs(terms) # Create nested tabs using term names

                for j, term in enumerate(terms): # Loop through terms and their corresponding tabs
                    with term_tabs[j]: # Define content for *this specific term tab*
                        # --- Display of Details Section MOVED INSIDE Term Tab ---
                        # st.write("---") # Separator is optional here
                        # st.subheader(f"Details for: {term}") # Subheader might be redundant as tab name = term

                        # Placeholder for display specific to this term tab
                        details_placeholder = st.empty()
                        country_code = "MY" # Assuming Malaysian context

                        # Logic to display details for 'term' (from the current tab loop)

                        # 1. Check if the result is already in the session cache
                        if term in st.session_state.lingo_cache:
                            # --- Cache Hit ---
                            details_placeholder.markdown(st.session_state.lingo_cache[term])
                            # st.caption("Displayed from session cache.") # Optional debug info

                        # 2. If not cached AND the model is available, fetch from API
                        elif model:
                            # --- Cache Miss ---
                            try:
                                # --- Define the Prompt (uses 'term' from the loop) ---
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
            else:
                st.caption("No terms listed in this category yet.") # Handle empty categories within the main tab

else:
    st.warning("No lingo categories found in the data.") # Message if data is empty

# --- Conditional Display of Details Section REMOVED FROM HERE ---
# The logic is now inside the nested term tabs