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

# --- CSS for Horizontal Scrolling Radio Buttons ---
st.markdown("""
<style>
/* Target the container holding the horizontal radio buttons */
/* This selector might need adjustment based on Streamlit version */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;          /* Ensure flex layout */
    overflow-x: auto !important;       /* Enable horizontal scrolling */
    white-space: nowrap !important;    /* Prevent wrapping */
    padding-bottom: 10px;   /* Add space for scrollbar if needed */
    padding-top: 5px;       /* Optional: Add some space above */
}

/* Optional: Style individual radio items for spacing */
div[data-testid="stRadio"] > div[role="radiogroup"] > label {
    margin-right: 15px; /* Adjust spacing between radio options */
    display: inline-block; /* Ensure proper layout */
}

/* Optional: Hide scrollbar visually (scrolling still works) */
div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera */
}
div[data-testid="stRadio"] > div[role="radiogroup"] {
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
}
</style>
""", unsafe_allow_html=True)

# --- Title and Description ---
st.title("Lingo-Lah: Your Local Lingo Guide")
st.write("Explore and understand Malaysian slang or lingo that locals use in their everyday life.")

# --- State Management ---
# Initialize the cache dictionary in session state if it doesn't exist
if 'lingo_cache' not in st.session_state:
    st.session_state.lingo_cache = {} # Use this to store term -> explanation
# Session state for radio buttons will be managed via their keys directly

# Get category names from your data structure
category_names = list(lingo_terms_by_category.keys())

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
    category_tabs = st.tabs(category_names)

    for i, category_name in enumerate(category_names):
        with category_tabs[i]:
            # Optional: Keep subheader for category context if desired
            # st.subheader(category_name)
            terms = lingo_terms_by_category.get(category_name, []) # Safely get terms

            # --- Use st.radio for Term Selection ---
            if terms: # Check if there are terms in this category
                radio_key = f"radio_{category_name}" # Unique key per category

                # Set a default selection (first term) if state doesn't exist for this radio group
                if radio_key not in st.session_state:
                    st.session_state[radio_key] = terms[0]

                # Display radio buttons horizontally, selected value stored in session_state[radio_key]
                selected_term = st.radio(
                    label=f"Select term in {category_name}", # Label for accessibility
                    options=terms,
                    key=radio_key, # Links radio state to st.session_state
                    horizontal=True,
                    label_visibility="collapsed" # Hides the label visually
                )

                # --- Details Logic - Runs ONLY for the 'selected_term' from radio ---
                if selected_term:
                    # Placeholder for display specific to this selected term
                    details_placeholder = st.empty()
                    country_code = "MY" # Assuming Malaysian context

                    # Logic to display details for 'selected_term'

                    # 1. Check if the result is already in the session cache
                    if selected_term in st.session_state.lingo_cache:
                        # --- Cache Hit ---
                        details_placeholder.markdown(st.session_state.lingo_cache[selected_term])
                        # st.caption("Displayed from session cache.") # Optional debug info

                    # 2. If not cached AND the model is available, fetch from API
                    elif model:
                        # --- Cache Miss ---
                        try:
                            # Show loading indicator while fetching
                            with details_placeholder.container():
                                 st.info(f"Fetching details for '{selected_term}'...") # Simple text indicator

                            # --- Define the Prompt ---
                            prompt = f"""Explain the {country_code} slang term '{selected_term}'.

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
                            # Use the same placeholder to display streaming response
                            with details_placeholder.container():
                                stream_display = st.empty() # Inner placeholder for stream
                                for chunk in response:
                                    if hasattr(chunk, 'text') and chunk.text:
                                        full_response += chunk.text
                                        stream_display.markdown(full_response + "▌") # Update stream

                                stream_display.markdown(full_response) # Final update

                            # --- Store the successful result in the session cache ---
                            st.session_state.lingo_cache[selected_term] = full_response

                        except Exception as e:
                            # Use the same placeholder to show the error
                            details_placeholder.error(f"An error occurred while fetching details for {selected_term}: {e}")
                            # Optionally clear the failed term from cache if needed
                            # if selected_term in st.session_state.lingo_cache:
                            #     del st.session_state.lingo_cache[selected_term]

                    # 3. Handle case where the model failed to initialize
                    else:
                         # Use the same placeholder to show the error
                         details_placeholder.error("Lingo details cannot be fetched because the Gemini model is not available.")
                # --- End of Details Logic ---
            else:
                st.caption("No terms listed in this category yet.") # Handle empty categories within the main tab

else:
    st.warning("No lingo categories found in the data.") # Message if data is empty