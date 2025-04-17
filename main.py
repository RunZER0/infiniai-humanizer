import streamlit as st
import openai
import os
import random
import textstat
import hashlib

# Set OpenAI key (via Streamlit secrets)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Distinct personality pool
TONE_VARIANTS = [
    {
        "label": "📚 Formal + Academic",
        "preserve_citations": True,
        "prompt": "You are an academic editor rewriting text for clarity and precision. Maintain in-text citations and use slightly formal tone. Vary sentence structure but keep professional polish."
    },
    {
        "label": "🧑‍🎤 Sarcastic Blogger",
        "preserve_citations": False,
        "prompt": "You are a sarcastic blogger with a dry sense of humor. Rewrite with casual phrasing, side comments, and occasional snark. Let it flow like a rant but still make sense."
    },
    {
        "label": "👶 Parent Explaining to a Kid",
        "preserve_citations": False,
        "prompt": "You’re a patient parent explaining this to a curious kid. Keep it simple, clear, and add playful tone. Avoid jargon. Relate to everyday things."
    },
    {
        "label": "🧑‍🎓 Sleep-Deprived Student at 2AM",
        "preserve_citations": False,
        "prompt": "You're a student finishing an assignment at 2AM. Let the thoughts wander a bit. Add mild rambling, hesitation, and very human flow — like someone just trying to make it readable."
    },
    {
        "label": "🎮 Reddit Forum Veteran",
        "preserve_citations": False,
        "prompt": "You're a casual forum veteran writing a reply post. Make it a mix of explanation, light rant, and informal tone. Add personal takes or anecdotes when relevant."
    }
]

# Hashing input to track style usage per input
def get_input_hash(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()

# Enhanced humanize engine
def humanize_text(text):
    input_hash = get_input_hash(text)

    if "previous_inputs" not in st.session_state:
        st.session_state.previous_inputs = {}

    used_variants = st.session_state.previous_inputs.get(input_hash, [])

    unused_variants = [i for i in range(len(TONE_VARIANTS)) if i not in used_variants]

    if not unused_variants:
        unused_variants = list(range(len(TONE_VARIANTS)))
        used_variants = []

    variant_index = random.choice(unused_variants)
    variant = TONE_VARIANTS[variant_index]

    used_variants.append(variant_index)
    st.session_state.previous_inputs[input_hash] = used_variants

    system_prompt = variant["prompt"]
    preserve_citations = variant["preserve_citations"]

    citation_instruction = (
        "Preserve any in-text citations exactly as written."
        if preserve_citations else
        "Feel free to remove or rephrase citations naturally."
    )

    full_prompt = f"""{system_prompt}

{text}

Now rewrite this with a natural human tone. Make it sound real, not robotic. {citation_instruction}
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    return response.choices[0].message.content.strip(), variant["label"]

# Custom CSS (unchanged layout)
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

# Input Text Area
input_text = st.text_area("Enter your AI-generated text:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Transforming AI text into human brilliance... ✨"):
            output, style_used = humanize_text(input_text)
            st.session_state.human_output = output
            st.session_state.last_style = style_used
    else:
        st.warning("Please enter some text first.")

if st.session_state.human_output:
    st.markdown("### ✍️ Humanized Output (Editable)")
    edited_output = st.text_area("Edit your result below:", value=st.session_state.human_output, height=300)
    st.session_state.human_output = edited_output

    words = len(edited_output.split())
    score = round(textstat.flesch_reading_ease(edited_output), 1)
    st.markdown(f"**📊 Output Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

    st.success(f"Writing Style Used: {st.session_state.last_style}")

    st.download_button("💾 Download Output", data=edited_output,
                       file_name="humanized_output.txt", mime="text/plain")

# Footer stays in place (layout untouched)
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

if not st.session_state.human_output:
    show_footer()
else:
    show_footer()
