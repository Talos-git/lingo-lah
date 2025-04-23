# Revised Project Plan: Lingo-Lah (Local Lingo Decoder)

**Goal:** Create an interactive Streamlit web application using tabs for categories, clickable cards for terms, and a separate details section below the tabs for LLM-generated explanations.

**Steps:**

1.  **Project Initialization:**
    *   Create a main Python file (`app.py`) for the Streamlit application.
    *   Create a Python file (`lingo_data.py`) to store the initial lingo terms as a dictionary, grouped by the categories you provided.
    *   Create a `requirements.txt` file listing `streamlit` and `google-generativeai`.
    *   Create a `.streamlit` directory and an empty `secrets.toml` file within it for API key management.

2.  **Data Loading:**
    *   In `lingo_data.py`, define a Python dictionary where keys are the category names and values are lists of lingo terms belonging to that category.
    *   In `app.py`, import the `lingo_terms_by_category` dictionary from `lingo_data.py`.

3.  **Streamlit App Structure (`app.py`):**
    *   Import necessary libraries (`streamlit`, `google.generativeai`, `lingo_data`).
    *   Set up the basic Streamlit page configuration (`st.set_page_config`).
    *   Add a title and brief description using `st.title` and `st.write`.

4.  **State Management:**
    *   Initialize `st.session_state.selected_term` to `None` if it doesn't exist.
    *   Initialize `st.session_state.active_tab` to the first category name if it doesn't exist, to keep track of the currently displayed tab.

5.  **Display Category Tabs:**
    *   Get the list of category names from the `lingo_terms_by_category` dictionary.
    *   Use `st.tabs(category_names)` to create tabs for each category.
    *   Inside the `with tab:` block for each tab, display the content for that category.

6.  **Display Lingo Cards within Tabs:**
    *   Inside the content block for each tab (from Step 5):
        *   Use `st.columns()` to create a responsive grid layout for the lingo term cards. Determine an appropriate number of columns.
        *   Iterate through the lingo terms within the current category.
        *   For each term, create a clickable element. While `st.button` is the standard Streamlit way, achieving complex flip/grow animations directly with `st.button` is challenging. A more flexible approach for animation might involve using `st.markdown` with custom HTML, CSS, and potentially JavaScript (though integrating complex JS with Streamlit state requires advanced techniques like `streamlit-component-template`). For a standard Streamlit approach, we will use `st.button` and handle the click event.
        *   Use the `on_click` parameter of `st.button` to update `st.session_state.selected_term` with the clicked term. A helper function can be used to set the state.

7.  **Conditional Display of Details Section (Below Tabs):**
    *   After the `st.tabs` block, check if `st.session_state.selected_term` is not `None`.
    *   If a term is selected, display a designated area for the details section below the tabs. This section will appear outside the tab container.

8.  **API Integration and Caching:**
    *   Define a function (e.g., `get_lingo_details(term, country_code)`) that takes the term and country code as input.
    *   Decorate this function with `@st.cache_data` to cache results based on term and country code, reducing redundant API calls and costs.
    *   Inside the function:
        *   Initialize the Google Gemini API client using the API key retrieved from `st.secrets["GOOGLE_API_KEY"]`.
        *   Construct a clear and specific prompt for the LLM asking for the meaning, typical usage context, and several example sentences for the given term in the Malaysian context.
        *   Call the Gemini API (e.g., `model.generate_content(prompt, stream=True)` for streaming).
        *   Process the LLM's response. If streaming, iterate through the chunks and display them as they arrive. Parse the final response to structure the output (meaning, usage, examples).
    *   In the details section (Step 7), call this function with the `st.session_state.selected_term` and 'MY' as the country code.
    *   Wrap the API call and parsing logic within `st.spinner("Fetching details...")` while waiting for the initial response. For streaming, the spinner can be shown until the first chunk arrives.

9.  **Display Lingo Details:**
    *   In the details section (Step 7), after fetching and processing the details:
        *   Display the selected term using `st.header` or `st.subheader`.
        *   Display the meaning, usage, and example sentences using `st.write` or `st.markdown` for formatting (e.g., using bullet points for examples).

10. **API Key Management:**
    *   Provide instructions to the user on how to add their Google API key to the `.streamlit/secrets.toml` file in the format `GOOGLE_API_KEY="YOUR_API_KEY"`.

11. **Animation Note:**
    *   Acknowledge the request for card flip/grow animation. Explain that while standard Streamlit components like `st.button` don't natively support complex animations, it might be possible using `st.markdown` with custom HTML/CSS/JS, or by exploring custom Streamlit components. For this plan, we will focus on the core functionality using standard Streamlit components, which will handle the click event and display the details, but without the complex animation. Implementing the animation would likely require a more advanced approach beyond basic Streamlit scripting.

12. **Refinement and Optional Features:**
    *   Review the UI layout and responsiveness across different screen sizes.
    *   (Optional) Implement `st.selectbox` for country selection to make the app expandable.
    *   (Optional) Implement `st.text_input` for searching/filtering terms within the active tab.
    *   (Optional) Enhance the visual appearance of the cards using `st.markdown` with basic CSS styling if complex animation is deferred.