import streamlit as st
import openai
import random
import textstat
import hashlib
import re

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Init session state
if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "last_style" not in st.session_state:
    st.session_state.last_style = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}

# Tone pool
TONE_VARIANTS = [
    {
        "label": "📘 Academic Humanizer",
        "preserve_citations": True,
        "prompt": "You are rewriting academic content like a human — not perfect, but thoughtful. Preserve citations. Think out loud. It's okay to be a bit messy, just not robotic."
    },
    {
        "label": "🎓 Grad Student Voice",
        "preserve_citations": True,
        "prompt": "You're a grad student rewriting this late at night. Preserve citations. You think as you write. Vary sentence structure and drop the overly polished tone."
    },
    {
        "label": "🧑‍🏫 Semi-Academic Explainer",
        "preserve_citations": True,
        "prompt": "You are explaining this as a human who read it and rewrote it from memory. Preserve citations. Be confident but casual, not robotic."
    },
    {
        "label": "🧠 4th Grade Academic",
        "preserve_citations": True,
        "prompt": "You’re rewriting this in very simple academic language for a 4th grader. Use plain words but keep citations intact."
    },
    {
        "label": "💬 Conversational Clarity",
        "preserve_citations": False,
        "prompt": "You're a human explaining this to a friend. Rewrite naturally, like you're thinking aloud. It's okay to skip or paraphrase citations."
    },
    {
        "label": "😎 Real Blogger Energy",
        "preserve_citations": False,
        "prompt": "You're a chill blogger. Rewrite like you're talking to your readers casually. Slight humor, contractions, and random shifts are okay."
    }
]

# Light entropy: add hesitation/filler phrases randomly
def inject_entropy(text):
    fillers = ["To be honest,", "I mean,", "Honestly,", "In some ways,", "Not gonna lie,", "Actually,", "You could say,"]
    sentences = re.split(r'(?<=[.!?]) +', text)
    modified = []

    for sentence in sentences:
        if sentence and random.random() < 0.3:
            sentence = f"{random.choice(fillers)} {sentence}"
        modified.append(sentence)

    return " ".join(modified)

# Hash input to track variants
def get_input_hash(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()

def humanize_text(text):
    input_hash = get_input_hash(text)
    used_variants = st.session_state.previous_inputs.get(input_hash, [])
    unused = [i for i in range(len(TONE_VARIANTS)) if i not in used_variants]

    if not unused:
        unused = list(range(len(TONE_VARIANTS)))
        used_variants = []

    variant_index = random.choice(unused)
    variant = TONE_VARIANTS[variant_index]

    used_variants.append(variant_index)
    st.session_state.previous_inputs[input_hash] = used_variants

    system_prompt = variant["prompt"]
    preserve_citations = variant["preserve_citations"]

    text = inject_entropy(text)

    citation_instruction = (
        "Preserve in-text citations exactly as written."
        if preserve_citations else
        "Citations may be skipped or reworded naturally if they break flow."
    )

    full_prompt = f"""{system_prompt}

{text}

Now rewrite this in your own voice — imperfect, flowing, and human. Vary length, break patterns, and don't be robotic. {citation_instruction}
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

# Styling (unchanged)
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
st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer</h1><p>Rewrite the machine. Fool the machine.</p></div>', unsafe_allow_html=True)

# Input
input_text = st.text_area("Enter your AI-generated text:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

# Button logic
if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Injecting imperfection and rewriting like a real human..."):
            output, style_used = humanize_text(input_text)
            st.session_state.human_output = output
            st.session_state.last_style = style_used
    else:
        st.warning("Please enter some text first.")

# Output Display
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

# Footer
def show_footer():
    st.markdown("---")
    st.markdown("#### 🌟 InfiniAi-Humanizer v1.2")
    st.markdown("""
    InfiniAi-Humanizer rewrites robotic AI output using real human-like tone, rhythm, and messiness.  
    Built to pass detection tools and sound like you wrote it yourself.

    **What People Say:**  
    - 🧠 “Feels like a real person wrote it.”  
    - 📉 “Dropped my AI detection score from 98% to 12%.”  
    - 🔁 “Every click gives a whole new vibe. Love it.”  
    """)

if not st.session_state.human_output:
    show_footer()
else:
    show_footer()
