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

# === HUMANIZER v4.0 — CHOPPY ACADEMIC MODE ===
PROMPT = (
    "Rewrite the following academic content to sound like it was written by a real, slightly tired student."
    " Keep the tone academic, but break up the sentences as much as possible."
    " Chop long sentences into short, blunt ones. Some sentence fragments are okay."
    " Repeat ideas for emphasis if needed. Keep transitions plain."
    " Vary sentence length randomly."
    " Insert awkward phrasing, redundancy, and comma splices."
    " Do NOT smooth the flow. Do NOT write like an AI."
    " Keep in-text citations and references untouched."
    " Don't add new ideas. Just restructure."
)

SYNONYMS = {
    "utilize": "use",
    "therefore": "so",
    "subsequently": "then",
    "prioritize": "focus on",
    "implementation": "doing",
    "prohibit": "stop",
    "facilitate": "help",
    "demonstrate": "show"
}

def chop_and_roughen(text):
    text = re.sub(r'(?<=[a-zA-Z0-9]),', '.', text)
    chunks = re.split(r'(?<=[.!?])\s+', text)
    output = []
    for chunk in chunks:
        if len(chunk.split()) > 18:
            parts = re.split(r'(,|;|:| and | but | because )', chunk)
            small = ""
            for p in parts:
                small += p
                if len(small.split()) > 9:
                    output.append(small.strip())
                    small = ""
            if small:
                output.append(small.strip())
        else:
            output.append(chunk.strip())
    return " ".join(output)

def repeat_some_lines(text):
    lines = re.split(r'(?<=[.!?])\s+', text)
    out = []
    for line in lines:
        out.append(line)
        if random.random() < 0.2 and len(line.split()) > 5:
            first = line.strip().split()[0]
            out.append(f"This shows how {first.lower()} matters.")
    return " ".join(out)

def downgrade_vocab(text):
    for word, simple in SYNONYMS.items():
        text = re.sub(rf'\b{word}\b', simple, text, flags=re.IGNORECASE)
    return text

def inject_disfluency(text):
    fragments = ["Even then.", "Because of that.", "That changed things.", "Still.", "But not really.", "Not always."]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    mixed = []
    for s in sentences:
        mixed.append(s)
        if random.random() < 0.2:
            mixed.append(random.choice(fragments))
    return " ".join(mixed)

def humanize_text(text):
    input_hash = hashlib.sha256(text.strip().encode()).hexdigest()
    if st.session_state.previous_inputs.get(input_hash):
        return st.session_state.human_output

    rough = downgrade_vocab(text)
    chopped = chop_and_roughen(rough)
    echoed = repeat_some_lines(chopped)
    broken = inject_disfluency(echoed)

    full_prompt = f"{PROMPT}\n\n{broken}\n\nReword this accordingly. Maintain academic tone but prioritize realism and sentence fragmentation."

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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer v4.0</h1><p>Academic writing with real, raw, choppy human energy.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text"):
    if input_text.strip():
        with st.spinner("Ripping it apart like a real student would..."):
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
st.markdown("#### ⚡ InfiniAi-Humanizer v4.0 – Choppy Academic Edition")
st.markdown("""
This version transforms AI-generated content into:
- ✂️ Sentence fragments and hard breaks
- 🧱 Deliberate rhythm variation
- 🔁 Repetitions and imperfections
- 📚 Citation-safe restructuring
Built to beat AI detectors and sound like real academic writing — tired, real, and raw.
""")