import streamlit as st
import openai
import os
import random
from dotenv import load_dotenv
import textstat

# Load API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Internal tone prompts (cycled silently)
TONE_VARIANTS = [
    "You are a sharp, witty writer with a casual, confident tone. Add variation, emotion, and mild unpredictability.",
    "You are a human editor rewriting text for clarity and believability. Add subtle imperfection and voice.",
    "You write like someone explaining things to a friend. Add questions, hesitations, and slight humor.",
    "You are a thoughtful thinker reflecting out loud. Let the flow wander a little, keep it natural.",
]

# Session state
if "tone_index" not in st.session_state:
    st.session_state.tone_index = 0
if "human_output" not in st.session_state:
    st.session_state.human_output = ""

# Custom Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0d0d0d;
        color: #00ffff;
        font-family: 'Segoe UI', monospace;
        text-align: center;
    }
    textarea {
        background-color: #121212 !important;
        color: #ffffff !important;
        border: 1px solid #00ffff !important;
        border-radius: 8px !important;
        font-size: 16px !important;
    }
    .stButton > button {
        background-color: #00ffff;
        color: black;
        font-weight: bold;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        transition: all 0.3s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #00cccc;
        transform: scale(1.03);
    }
    .stDownloadButton button {
        background-color: #00ffff;
        color: black;
        font-weight: bold;
        border-radius: 5px;
    }
    .centered-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# App Title
st.markdown('<div class="centered-container"><h1>🤖 Infiniai-Humanizer</h1><p>Rewrite the machine. Own the voice.</p></div>', unsafe_allow_html=True)

# Input Area
input_text = st.text_area("Enter your AI-generated text:", height=250)

# Live stats for input
if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

# Rewrite Function
def humanize_text(text, preserve_citations=True):
    tone_prompt = TONE_VARIANTS[st.session_state.tone_index]
    st.session_state.tone_index = (st.session_state.tone_index + 1) % len(TONE_VARIANTS)

    citation_instruction = (
        "Preserve any in-text citations exactly as written."
        if preserve_citations else
        "Remove or rephrase citations naturally if needed."
    )

    full_prompt = f"""{tone_prompt}

{text}

Now rewrite this in a natural human tone. Vary structure, avoid robotic patterns. {citation_instruction}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": tone_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    return response["choices"][0]["message"]["content"].strip()

# Button
if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Transforming AI text into human brilliance... ✨"):
            output = humanize_text(input_text)
            st.session_state.human_output = output
    else:
        st.warning("Please enter some text first.")

# Show output if available
if st.session_state.human_output:
    st.markdown("### ✍️ Humanized Output (Editable)")
    edited_output = st.text_area("Edit your result below:", value=st.session_state.human_output, height=300)
    st.session_state.human_output = edited_output

    words, score = len(edited_output.split()), round(textstat.flesch_reading_ease(edited_output), 1)
    st.markdown(f"**📊 Output Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

    st.download_button("💾 Download Output", data=edited_output,
                       file_name="humanized_output.txt", mime="text/plain")

# Reusable: Version info + Reviews
def show_footer():
    st.markdown("---")
    st.markdown("#### 🌟 Infiniai-Humanizer v1.1")
    st.markdown("""
    Infiniai-Humanizer helps turn robot-sounding text into something real people actually say.  
    It's easy, fast, and fun. Your words still mean the same thing — they just feel more human.  
    Great for school, writing, or making anything sound better!

    **What People Say:**  
    - 🧒 “It made my story sound like *me*! That’s cool.”  
    - 👩 “I clicked the button and boom! It was better.”  
    - 🧑‍🏫 “Now my students sound way less like robots. I love it.”  
    - 👶 “This thing is smart. And fun. Like a magic helper.”  
    """)

# Smart Placement
if not st.session_state.human_output:
    show_footer()  # show immediately after the button (initial page load)
else:
    show_footer()  # push it below the output/download section
