import streamlit as st
import openai
import os
import random
import textstat
import hashlib

# Use Streamlit secrets to store the API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]
# Initialize session state defaults
if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "last_style" not in st.session_state:
    st.session_state.last_style = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}

# Balanced personality pool: academic, semi-academic, light casual
TONE_VARIANTS = [
    {
        "label": "📘 Academic Research Editor",
        "preserve_citations": True,
        "prompt": "You are an academic editor improving formal writing for clarity and tone. Use formal, objective language and preserve all in-text citations exactly."
    },
    {
        "label": "🎓 Graduate Summary Writer",
        "preserve_citations": True,
        "prompt": "You are a graduate student summarizing academic material. Maintain a clear, concise, and professional tone. Preserve all citations."
    },
    {
        "label": "📊 Technical Report Style",
        "preserve_citations": True,
        "prompt": "You're writing a technical report for a professional audience. Use structured, semi-formal tone. Maintain all citations and formal clarity."
    },
    {
        "label": "🧑‍🏫 Educated Blogger",
        "preserve_citations": True,
        "prompt": "You're an educated blogger explaining academic ideas to a wide audience. Use accessible, semi-formal tone with examples and preserve citations."
    },
    {
        "label": "👧 4th Grade Academic Explainer",
        "preserve_citations": True,
        "prompt": "You are rewriting academic text using 4th grade English, while keeping it factually accurate. Preserve all in-text citations exactly."
    },
    {
        "label": "📚 Friendly Explainer",
        "preserve_citations": False,
        "prompt": "You're a friendly teacher explaining something to a smart 13-year-old. Use natural transitions and helpful comparisons. You can simplify or reword citations."
    },
    {
        "label": "🧑‍💻 Conversational Analyst",
        "preserve_citations": False,
        "prompt": "You're a conversational analyst writing for a casual newsletter. Use clear logic but add a relaxed tone. Feel free to paraphrase citations."
    },
    {
        "label": "😎 Chill Blogger",
        "preserve_citations": False,
        "prompt": "You're a chill blogger breaking down an idea in a super natural way. Add slight personality, occasional asides, and relaxed flow. Citations can be removed or reworded."
    }
]

# Helper: Track tone per input hash
def get_input_hash(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()

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
        "You may rephrase or remove citations naturally if needed."
    )

    full_prompt = f"""{system_prompt}

{text}

Now rewrite this in a way that sounds truly human. Vary structure, tone, and flow. {citation_instruction}
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

# UI Styling (unchanged layout)
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

# Title
st.markdown('<div class="centered-container"><h1>🤖 Infiniai-Humanizer</h1><p>Rewrite the machine. Own the voice.</p></div>', unsafe_allow_html=True)

# Input
input_text = st.text_area("Enter your AI-generated text:", height=250)

# Input Stats
if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

# Button
if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Transforming AI text into human brilliance... ✨"):
            output, style_used = humanize_text(input_text)
            st.session_state.human_output = output
            st.session_state.last_style = style_used
    else:
        st.warning("Please enter some text first.")

# Output
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

# Footer (static)
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
