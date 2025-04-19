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

# --- CORE HUMANIZATION INSTRUCTIONS ---
# This system emulates the structural and tonal transformation observed in a real, humanized dissertation
# without copying its content. Every output must follow these detailed rules:
# 1. Break long sentences at natural pauses (commas, semicolons, conjunctions)
# 2. Vary sentence length across each paragraph to avoid uniform rhythm
# 3. Insert redundant phrasing or mirrored ideas one or two lines apart
# 4. Use synonyms to downgrade overly academic/formal words
# 5. Inject light structural imperfection (comma splices, awkward transitions)
# 6. Mimic how a student writes under pressure—clarity > polish
# 7. Preserve all in-text citations, quotes, dates, names, and formatting
# 8. Sound human enough to fool AI detectors, while remaining academically acceptable
# 9. Tone = graduate-level student voice; slightly unpolished, but coherent and serious

PROMPT = (
    "Rewrite the following academic content to sound like it was written by a real student, not AI. "
    "Follow all of these rules strictly: 
     (1) Break long sentences into 2-3 shorter ones using commas or periods. 
     (2) Vary the length of sentences within each paragraph. Avoid repeating rhythm. 
     (3) Add a redundant echo line 1-2 sentences later that rephrases a key idea. 
     (4) Replace elevated vocabulary with simpler synonyms where possible. 
     (5) Keep slight structural imperfections like plain transitions, uneven sentence sizes, or minor comma splices. 
     (6) Do NOT add new information. Do NOT change names, citations, or references. 
     (7) The final tone must sound like a graduate student writing under pressure, not a polished AI model.")

# --- SYNONYM SWAP LAYER ---
SYNONYMS = {
    "utilize": "use",
    "therefore": "so",
    "subsequently": "then",
    "prioritize": "focus on",
    "implementation": "application",
    "prohibit": "stop",
    "facilitate": "help",
    "significant": "major",
    "demonstrate": "show",
    "moreover": "also",
    "methodology": "approach"
}

def downgrade_vocab(text):
    for word, alt in SYNONYMS.items():
        text = re.sub(rf"\b{word}\b", alt, text, flags=re.IGNORECASE)
    return text

# --- STRUCTURAL RANDOMIZER ---
def human_sentence_breaker(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    new_sentences = []
    for sent in sentences:
        if len(sent.split()) > 25:
            parts = re.split(r'(,|;|:| and | but )', sent)
            chunk = ""
            for p in parts:
                chunk += p
                if len(chunk.split()) > 12:
                    new_sentences.append(chunk.strip())
                    chunk = ""
            if chunk:
                new_sentences.append(chunk.strip())
        else:
            new_sentences.append(sent)
    return " ".join(new_sentences)

# --- REDUNDANCY LAYER ---
def insert_human_redundancy(text):
    echo_starters = ["This shows that", "In other words,", "To put it simply,", "That meant"]
    lines = re.split(r'(?<=[.!?])\s+', text)
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if random.random() < 0.3 and len(line.split()) > 6:
            phrase = random.choice(echo_starters)
            first_word = line.split()[0].lower()
            new_lines.append(f"{phrase} {first_word}...")
    return " ".join(new_lines)

# --- IMPERFECTION LAYER ---
def inject_flaws(text):
    if random.random() < 0.4:
        text = re.sub(r'(\bhowever\b|\bfurthermore\b|\badditionally\b)', 'also', text, flags=re.IGNORECASE)
    text = re.sub(r'(\.\s)([A-Z])', lambda m: random.choice(['. ', ', ', '; ']) + m.group(2), text, count=1)
    return text

# --- FINAL HUMANIZATION LOGIC ---
def humanize_text(text):
    input_hash = hashlib.sha256(text.strip().encode()).hexdigest()
    if st.session_state.previous_inputs.get(input_hash):
        return st.session_state.human_output

    simplified = downgrade_vocab(text)
    broken = human_sentence_breaker(simplified)
    echoed = insert_human_redundancy(broken)
    flawed = inject_flaws(echoed)

    full_prompt = f"{PROMPT}\n\n{flawed}\n\nReword this to match all conditions above without changing facts."

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

# --- UI ---
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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer v3.0</h1><p>Turn any AI-generated academic text into realistic student-style writing.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Rewriting with human-like logic and flow..."):
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
st.markdown("#### 🧠 InfiniAi-Humanizer v3.0 – Academic Mode")
st.markdown("""
This tool restructures any AI-generated academic content using:
- ✂️ Sentence splitting & rebalancing
- 🔁 Echo phrasing for natural emphasis
- 💬 Mild structural flaws & transition variation
- 📚 Citation preservation
Designed to sound human, pass AI detection, and meet academic tone.
""")
