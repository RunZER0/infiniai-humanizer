import streamlit as st
import openai
import random
import textstat
import hashlib
import re

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}

# === HUMANIZER v4.1 — BALANCED ACADEMIC EDITION ===
PROMPT = (
    "Rewrite the following academic content to sound like it was written by a real student. "
    "Alternate between short, choppy, blunt sentences and longer, clearer ones for flow. "
    "Make some ideas direct. Fragmented. Abrupt. Others should elaborate clearly and academically. "
    "Allow sentence fragments and repetition for emphasis. Insert plain transitions. "
    "Avoid robotic structure. Vary rhythm naturally. Do not overpolish. Do not add new ideas. "
    "Preserve all in-text citations, quotes, names, and formatting."
)

SYNONYMS = {
    "utilize": "use",
    "therefore": "so",
    "subsequently": "then",
    "prioritize": "focus on",
    "implementation": "doing",
    "prohibit": "stop",
    "facilitate": "help",
    "demonstrate": "show",
    "significant": "big",
    "furthermore": "also"
}

def downgrade_vocab(text):
    for word, simple in SYNONYMS.items():
        text = re.sub(rf'\b{word}\b', simple, text, flags=re.IGNORECASE)
    return text

def balance_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for s in sentences:
        if len(s.split()) > 20 and random.random() < 0.5:
            split = re.split(r'(,|;| and | but | because )', s)
            small = ""
            for chunk in split:
                small += chunk
                if len(small.split()) >= random.randint(6, 12):
                    result.append(small.strip())
                    small = ""
            if small:
                result.append(small.strip())
        else:
            result.append(s.strip())
    return " ".join(result)

def insert_transitions(text):
    soft_transitions = ["Still.", "That matters.", "Also important.", "A big deal.", "Even then.", "Because of this.", "But not always."]
    lines = re.split(r'(?<=[.!?])\s+', text)
    output = []
    for line in lines:
        output.append(line)
        if random.random() < 0.25:
            output.append(random.choice(soft_transitions))
    return " ".join(output)

def echo_lines(text):
    echoes = ["This shows that", "To say it again:", "That proves one thing:", "We can tell from this that"]
    lines = re.split(r'(?<=[.!?])\s+', text)
    output = []
    for i, line in enumerate(lines):
        output.append(line)
        if random.random() < 0.2 and len(line.split()) > 6:
            output.append(f"{random.choice(echoes)} {line.strip().split()[0].lower()}...")
    return " ".join(output)

def humanize_text(text):
    input_hash = hashlib.sha256(text.strip().encode()).hexdigest()
    if st.session_state.previous_inputs.get(input_hash):
        return st.session_state.human_output

    basic = downgrade_vocab(text)
    structured = balance_sentences(basic)
    transitioned = insert_transitions(structured)
    echoed = echo_lines(transitioned)

    full_prompt = f"{PROMPT}\n\n{echoed}\n\nRewrite this following all rules above."

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.85,
        max_tokens=1600
    )

    result = response.choices[0].message.content.strip()
    st.session_state.previous_inputs[input_hash] = True
    return result

# === UI ===
st.markdown("""
<style>
.stApp { background-color: #0d0d0d; color: #00ffff; font-family: 'Segoe UI', monospace; text-align: center; }
textarea { background-color: #121212 !important; color: #ffffff !important; border: 1px solid #00ffff !important; border-radius: 8px !important; font-size: 16px !important; }
.stButton > button { background-color: #00ffff; color: black; font-weight: bold; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; transition: all 0.3s ease-in-out; }
.stButton > button:hover { background-color: #00cccc; transform: scale(1.03); }
.stDownloadButton button { background-color: #00ffff; color: black; font-weight: bold; border-radius: 5px; }
.centered-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer v4.1</h1><p>Balanced academic writing: blunt + clear + detector-safe.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Humanizing using real student rhythm and structure..."):
            output = humanize_text(input_text)
            st.session_state.human_output = output
    else:
        st.warning("Please enter some text first.")

if st.session_state.human_output:
    st.markdown("### ✍️ Humanized Output")
    edited_output = st.text_area("Edit your result below:", value=st.session_state.human_output, height=300)
    st.session_state.human_output = edited_output

    words = len(edited_output.split())
    score = round(textstat.flesch_reading_ease(edited_output), 1)
    st.markdown(f"**📊 Output Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

    st.download_button("💾 Download Output", data=edited_output, file_name="humanized_output.txt", mime="text/plain")

st.markdown("---")
st.markdown("#### 🎓 InfiniAi-Humanizer v4.1 – Balanced Academic Flow")
st.markdown("""
This version blends:
- ✂️ Choppy sentence rhythm with flowing explanations
- 🧠 Real student imperfection with academic tone
- 📚 Citation-safe rewording
Designed to sound human, pass AI detectors, and keep your professors satisfied.
""")
