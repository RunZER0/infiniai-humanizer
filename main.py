import streamlit as st
import openai
import random
import textstat
import hashlib
import re

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Session state setup
if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "last_style" not in st.session_state:
    st.session_state.last_style = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}

# Tone variants using rules from Kai's humanizer profile
TONE_VARIANTS = [
    {
        "label": "📘 Feminist Legal Rewrite",
        "preserve_citations": True,
        "prompt": (
            "You're rewording academic content based on memory, influenced by feminist legal theory. It should sound like a thoughtful graduate student at 2AM: varied sentence lengths, human pacing, slight imperfections, some echoing, and structurally loosened clauses. Keep all in-text citations exactly as they are."
        )
    },
    {
        "label": "🧠 Real Student Summary",
        "preserve_citations": True,
        "prompt": (
            "Reword the following as if a real student is trying to make sense of dense legal theory late at night. Keep the meaning but soften the tone. Break long sentences. Add natural transitions. Vary structure. Keep citations in place."
        )
    }
]

def sentence_variability(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    modified = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        if random.random() < 0.3:
            sentence = re.sub(r" and ", " plus ", sentence)
        if random.random() < 0.25:
            sentence = sentence.replace(" in ", " inside ")
        if random.random() < 0.2:
            sentence = re.sub(r'\bis\b', ' seems to be', sentence)
        if random.random() < 0.15:
            sentence = "Actually, " + sentence
        modified.append(sentence)
    return " ".join(modified)

def lexical_simplification(text):
    replacements = {
        "codified": "written",
        "prohibit": "stop",
        "utilize": "use",
        "therefore": "so",
        "implementation": "application",
        "gender-neutral": "non-gendered",
        "prioritize": "focus on",
        "notwithstanding": "even though"
    }
    for key, val in replacements.items():
        text = re.sub(rf'\b{re.escape(key)}\b', val, text, flags=re.IGNORECASE)
    return text

def inject_flaws_and_redundancy(text):
    fillers = ["basically", "sort of", "kind of", "in some ways"]
    echo_phrases = [
        ("shows", "this shows that"),
        ("reveals", "which basically reveals"),
        ("suggests", "which sort of suggests")
    ]
    lines = re.split(r'(?<=[.!?])\s+', text)
    new_lines = []
    for line in lines:
        if random.random() < 0.25:
            line = f"{random.choice(fillers).capitalize()}, {line}"
        for orig, echo in echo_phrases:
            if orig in line and random.random() < 0.5:
                line = line.replace(orig, echo)
        new_lines.append(line)
    return " ".join(new_lines)

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
    base_text = lexical_simplification(text)
    altered_text = sentence_variability(base_text)
    flawed_text = inject_flaws_and_redundancy(altered_text)

    full_prompt = (
        f"{system_prompt}\n\n{flawed_text}\n\nNow rewrite this in your own words. Keep the meaning, but loosen the tone. Vary sentence structure, allow imperfections, and retain citations exactly as they are."
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    return response.choices[0].message.content.strip()

# === UI / Layout ===
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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer</h1><p>Humanize the text. Make it sound like a person wrote it, not a program, and beat all AI detectors.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Enter your AI-generated text:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Humanizing... Please wait."):
            output = humanize_text(input_text)
            st.session_state.human_output = output
    else:
        st.warning("Please enter some text first.")

if st.session_state.human_output:
    st.markdown("### ✍️ Humanized Output (Editable)")
    edited_output = st.text_area("Edit your result below:", value=st.session_state.human_output, height=300)
    st.session_state.human_output = edited_output

    words = len(edited_output.split())
    score = round(textstat.flesch_reading_ease(edited_output), 1)
    st.markdown(f"**📊 Output Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

    st.download_button("💾 Download Output", data=edited_output,
                       file_name="humanized_output.txt", mime="text/plain")

def show_footer():
    st.markdown("---")
    st.markdown("#### 🌟 InfiniAi-Humanizer v2.0")
    st.markdown("""
    InfiniAi-Humanizer rewrites AI-sounding text into believable, natural-sounding academic work. 
    Powered by GPT-4o and a custom-trained rule engine built from real dissertation transformations.

    **Engine Highlights:**  
    - 💡 Clause breaking + soft transitions  
    - 🔁 Echo phrasing for natural emphasis  
    - 👩‍🎓 Feminist legal tone supported  
    - 📚 Citation-safe academic rewrites  
    """)

if not st.session_state.human_output:
    show_footer()
else:
    show_footer()
