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

# --- Title and Description ---
st.title("Lingo-Lah: Your Local Lingo Guide")
st.write("Explore and understand Malaysian slang or lingo that locals use in their everyday life.")

# --- State Management ---
# Initialize the cache dictionary in session state if it doesn't exist
if 'lingo_cache' not in st.session_state:
    st.session_state.lingo_cache = {} # Use this to store term -> explanation

# Initialize streaming state flag
if 'is_streaming' not in st.session_state:
    st.session_state.is_streaming = False

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
# Note: st.tabs itself cannot be easily disabled. We disable the radio buttons inside.
if category_names: # Only display tabs if there are categories
    category_tabs = st.tabs(category_names)

    for i, category_name in enumerate(category_names):
        with category_tabs[i]:
            terms = lingo_terms_by_category.get(category_name, []) # Safely get terms

            # --- Use st.radio for Term Selection ---
            if terms: # Check if there are terms in this category
                radio_key = f"radio_{category_name}" # Unique key per category

                # Set a default selection (first term) if state doesn't exist
                if radio_key not in st.session_state:
                    # Avoid setting default if streaming is happening during initial load
                    if not st.session_state.get('is_streaming', False):
                         st.session_state[radio_key] = terms[0]

                # Disable radio buttons if streaming is active
                is_disabled = st.session_state.get('is_streaming', False)

                selected_term = st.radio(
                    label=f"Select term in {category_name}", # Label for accessibility
                    options=terms,
                    key=radio_key, # Links radio state to st.session_state
                    horizontal=True,
                    label_visibility="collapsed", # Hides the label visually
                    disabled=is_disabled # Disable based on streaming state
                )

                # --- Details Logic - Runs ONLY for the 'selected_term' from radio ---
                # Ensure a term is selected AND we are not currently streaming elsewhere
                if selected_term and not is_disabled:
                    details_placeholder = st.empty()
                    country_code = "MY"

                    # 1. Check cache first (only proceed to API if not cached)
                    if selected_term in st.session_state.lingo_cache:
                        details_placeholder.markdown(st.session_state.lingo_cache[selected_term])

                    # 2. If not cached AND model is available, fetch from API
                    elif model:
                        try:
                            # --- SET STREAMING STATE ---
                            st.session_state.is_streaming = True
                            # We don't rerun here, disabling happens on next interaction pass

                            # Show loading indicator
                            with details_placeholder.container():
                                 st.info(f"Fetching details for '{selected_term}'...")

                            # --- Define the Prompt ---
                            prompt = f"""Explain the {country_code} slang term '{selected_term}'.

                                        Structure the response using Markdown:
                                        ### Meaning, Typical Usage Context, Example Sentences (3x)
                                        Keep the explanation clear and concise.
                                        """ # Shortened for brevity

                            # --- Streaming Call ---
                            response = model.generate_content(prompt, stream=True)

                            # Process stream
                            full_response = ""
                            with details_placeholder.container():
                                stream_display = st.empty()
                                for chunk in response:
                                    if hasattr(chunk, 'text') and chunk.text:
                                        full_response += chunk.text
                                        stream_display.markdown(full_response + "▌")
                                stream_display.markdown(full_response) # Final update

                            # Cache the result
                            st.session_state.lingo_cache[selected_term] = full_response

                        except Exception as e:
                            details_placeholder.error(f"An error occurred: {e}")
                            # Error occurred, finally block will reset state

                        finally:
                            # --- RESET STREAMING STATE ---
                            st.session_state.is_streaming = False
                            # Rerun to immediately re-enable the radio buttons
                            st.rerun()

                    # 3. Handle case where the model failed to initialize
                    elif not model:
                         details_placeholder.error("Gemini model not available.")

                # Display cached content passively if term is selected but streaming is active elsewhere
                # (prevents blank space if user switches tabs while another stream runs)
                elif selected_term and is_disabled and selected_term in st.session_state.lingo_cache:
                     details_placeholder.markdown(st.session_state.lingo_cache[selected_term])
                     st.caption("_Loading other term..._")


            else:
                st.caption("No terms listed in this category yet.")

else:
    st.warning("No lingo categories found in the data.")