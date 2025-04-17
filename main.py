import streamlit as st
import openai
import random
import textstat
import hashlib
import re

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Session state init
if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "last_style" not in st.session_state:
    st.session_state.last_style = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}

# Serious-tone personas only
TONE_VARIANTS = [
    {
        "label": "📘 Academic Research Editor",
        "preserve_citations": True,
        "prompt": "You are an academic editor improving formal writing for clarity and tone. Use formal, objective language and preserve all in-text citations exactly."
    },
    {
        "label": "🎓 Grad Student Voice",
        "preserve_citations": True,
        "prompt": "You're a grad student rewriting academic material under deadline pressure. Use clear, academic tone. Vary sentence structure. Preserve citations."
    },
    {
        "label": "📊 Technical Report Writer",
        "preserve_citations": True,
        "prompt": "You're rewriting a technical report for professional readability. Be structured, formal, and precise. Preserve all citations exactly."
    },
    {
        "label": "🧑‍🏫 Educated Blogger (Serious)",
        "preserve_citations": True,
        "prompt": "You're an informed blogger summarizing complex ideas seriously. Use semi-formal tone. Preserve all citations exactly."
    },
    {
        "label": "👧 Simplified Academic Style",
        "preserve_citations": True,
        "prompt": "You are simplifying academic text using plain English (4th-grade level). Preserve all citations exactly. Keep tone respectful and serious."
    },
    {
        "label": "🧠 Late-Night Student Rewrite",
        "preserve_citations": True,
        "prompt": "You're a student rewriting this at 2AM. Keep it thoughtful but slightly imperfect. Preserve citations. Let the tone feel like a real person under pressure."
    }
]

# Light human noise (entropy)
def inject_entropy(text):
    fillers = ["To be honest,", "In some ways,", "Interestingly,", "Actually,", "For what it's worth,", "That being said,"]
    sentences = re.split(r'(?<=[.!?]) +', text)
    modified = []

    for sentence in sentences:
        if sentence and random.random() < 0.25:
            sentence = f"{random.choice(fillers)} {sentence}"
        modified.append(sentence)

    return " ".join(modified)

# Hashing logic
def get_input_hash(text):
    return hashlib.sha256(text.strip().encode()).hexdigest()

# Main rewrite engine
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

    noisy_text = inject_entropy(text)

    citation_instruction = (
        "Preserve all in-text citations exactly as written."
        if preserve_citations else
        "You may reword or skip citations naturally if needed."
    )

    full_prompt = f"""{system_prompt}

{noisy_text}

Now rewrite this in a natural, believable human tone — suitable for academic settings. Vary sentence structure, break robotic rhythm. {citation_instruction}
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.85,
        max_tokens=1500
    )

    return response.choices[0].message.content.strip(), variant["label"]

# === UI STAYS UNTOUCHED ===
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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer</h1><p>Rewrite the machine. Fool the machine.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Enter your AI-generated text:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Rewriting with serious academic tone..."):
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

def show_footer():
    st.markdown("---")
    st.markdown("#### 🌟 InfiniAi-Humanizer v1.3")
    st.markdown("""
    InfiniAi-Humanizer rewrites stiff AI text into natural, academic-sounding work.  
    Built for serious use — student-safe, citation-aware, and detection-resistant.

    **Feedback from testers:**  
    - 🧑‍🎓 “Finally looks like *I* wrote it.”  
    - 📉 “Detection scores dropped big time.”  
    - 🧠 “Smart tone, not gimmicky. Feels legit.”  
    """)

if not st.session_state.human_output:
    show_footer()
else:
    show_footer()
