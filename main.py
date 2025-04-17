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

# Serious-tone personas only
TONE_VARIANTS = [
    {
        "label": "📘 Academic Reworded From Memory",
        "preserve_citations": True,
        "prompt": (
            "You just read this paragraph and now you're explaining it in your own words, from memory — not trying to be perfect, just accurate. "
            "It should feel like a real person recalling what they understood, not reciting or copying. Don’t smooth out the rough edges; slight pauses, "
            "varied structure, and natural transitions are good. Keep all citations exactly where they are."
        )
    },
    {
        "label": "🎓 Grad Student Late Rewrite",
        "preserve_citations": True,
        "prompt": (
            "You're a grad student rewriting a chunk of AI-generated text late at night. You’re tired, you get the gist, and you’re trying to make it sound human — "
            "not polished, not stiff, just real. Let the structure shift, vary sentence length, and don’t obsess over perfect grammar. Just sound like someone doing their best "
            "to rephrase what they remember. All in-text citations must stay exactly as they are."
        )
    },
    {
        "label": "📊 Technical Paraphrase",
        "preserve_citations": True,
        "prompt": (
            "You’re paraphrasing this technical explanation like a real person would after reading it once. Your job is to keep the technical accuracy and logic, "
            "but shift the tone and rhythm so it doesn’t feel machine-written. Use a more natural structure and make it sound like a thoughtful human summary. "
            "Keep all in-text citations exactly as they are."
        )
    },
    {
        "label": "🧑‍🏫 Semi-Formal Explanation",
        "preserve_citations": True,
        "prompt": (
            "You’ve read an AI-written paragraph and now you're rephrasing it like a human would explain it — semi-formally, but without that stiff or robotic tone. "
            "Aim for clarity and flow that sounds natural in real conversation or writing. Vary your pacing, use real-sounding phrasing, and don’t worry about perfection. "
            "All citations must stay intact."
        )
    },
    {
        "label": "👧 Simplified Academic Style",
        "preserve_citations": True,
        "prompt": (
            "You’re turning an academic paragraph into more accessible, plain English — the kind of writing a human might use when trying to make something understandable "
            "without dumbing it down. Avoid the mechanical feel of AI text. Focus on simplicity, rhythm, and meaning. Keep all in-text citations as they appear."
        )
    },
    {
        "label": "🧠 2AM Real Rewrite",
        "preserve_citations": True,
        "prompt": (
            "It's 2AM and you're rewriting an AI-generated section of your paper from memory. You remember the core ideas, but you're not trying to sound perfect — just real and intelligent. "
            "Let your sentence structure breathe, vary your rhythm, and use natural word choices. You’re thinking while writing, not copy-pasting. "
            "All citations need to remain in place, unchanged."
        )
    }
]

def weaken_academic_tone(text):
    replacements = {
        "therefore": "so",
        "moreover": "also",
        "additionally": "a next step",
        "cognitive": "thinking",
        "motor": "movement",
        "developmental outcomes": "growth results",
        "suggests": "shows",
        "predictor": "sign",
        "psychomotor": "movement and brain",
        "fetal": "baby's",
        "prenatal": "before birth",
        "utilize": "use",
        "researchers": "the people studying this",
        "in utero": "inside the womb"
    }
    for key, val in replacements.items():
        text = re.sub(rf'\b{re.escape(key)}\b', val, text, flags=re.IGNORECASE)
    return text

def break_and_variabilize(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    modified = []
    for sentence in sentences:
        if sentence:
            if random.random() < 0.3:
                sentence = sentence.replace(" and ", " along with ")
            if random.random() < 0.25:
                sentence = sentence.replace(" in ", " inside ")
            if random.random() < 0.2:
                sentence = re.sub(r'\bis\b', 'turns out to be', sentence)
            if random.random() < 0.15:
                sentence = "Actually, " + sentence
            modified.append(sentence)
    return " ".join(modified)

def inject_human_flaws(text):
    filler_phrases = [
        "in a way", "kind of", "basically", "to be clear", "actually", 
        "from what I understand", "this means", "sort of"
    ]
    clarifiers = [
        ("which means", "which basically means"),
        ("this shows", "this kind of shows"),
        ("it suggests", "it sort of suggests"),
        ("in conclusion", "so, in a way")
    ]
    lines = re.split(r'(?<=[.!?])\s+', text)
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        if random.random() < 0.25:
            line = f"{random.choice(filler_phrases).capitalize()}, {line}"
        for original, flawed in clarifiers:
            if original in line and random.random() < 0.5:
                line = line.replace(original, flawed)
        if random.random() < 0.2:
            line = re.sub(r'\b(the|a|an)\b ', '', line, flags=re.IGNORECASE)
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
    preserve_citations = variant["preserve_citations"]

    base_text = weaken_academic_tone(text)
    altered_text = break_and_variabilize(base_text)
    altered_text = inject_human_flaws(altered_text)

    citation_instruction = (
        "Preserve all in-text citations exactly as written."
        if preserve_citations else
        "You may reword or skip citations naturally if needed."
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"{altered_text}\n\n"
        "Now rewrite this as if you're explaining it in your own words, based on memory. "
        "Use simple, varied sentence lengths. Be accurate, but not polished. "
        f"{citation_instruction}"
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.85,
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
    st.markdown("#### 🌟 InfiniAi-Humanizer v1.4")
    st.markdown("""
    InfiniAi-Humanizer rewrites AI-sounding text into believable, natural-sounding content.  
    Built to pass AI detectors with human-style pacing, simplified structure, and citation-safe memory-based rephrasing.

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
