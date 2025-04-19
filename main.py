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

# === HUMANIZER v4.2.1 — Precision Student Mode ===
PROMPT = (
    "Rewrite the following academic content like a real student would:"
    " Maintain clarity and academic tone, but alternate between full, structured sentences and short, blunt ones."
    " Use 1–2 choppy lines per paragraph to emphasize key ideas."
    " Add mild imperfection: echo phrases, sentence fragments, and plain transitions like 'Still' or 'This matters.'"
    " Do not over-smooth. Let it feel like real writing."
    " Do not add new facts. Preserve all in-text citations and formatting."
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

def paragraph_balancer(text):
    paragraphs = text.split('\n')
    balanced = []
    for p in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', p)
        buffer = []
        chop_count = 0
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            if len(s_clean.split()) > 20:
                buffer.append(s_clean)
            elif chop_count < 2:
                buffer.append(s_clean)
                chop_count += 1
            else:
                combined = s_clean + (" " + random.choice(["Still.", "This matters.", "Even then."]) if random.random() < 0.3 else "")
                buffer.append(combined)
        balanced.append(" ".join(buffer))
    return "\n\n".join(balanced)

def insert_redundancy(text):
    lines = re.split(r'(?<=[.!?])\s+', text)
    output = []
    for i, line in enumerate(lines):
        output.append(line)
        if random.random() < 0.15 and len(line.split()) > 6:
            output.append(f"This shows that {line.strip().split()[0].lower()} is important.")
    return " ".join(output)

def inject_choppy_fragments(text):
    additions = ["This matters.", "Big risk.", "Still.", "Not always.", "A serious problem.", "That’s the issue.", "Even that’s not enough."]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for s in sentences:
        result.append(s)
        if random.random() < 0.18:
            result.append(random.choice(additions))
    return " ".join(result)

def humanize_text(text):
    simplified = downgrade_vocab(text)
    structured = paragraph_balancer(simplified)
    echoed = insert_redundancy(structured)
    chopped = inject_choppy_fragments(echoed)

    full_prompt = f"{PROMPT}\n\n{chopped}\n\nRewrite this with the tone and structure described above."

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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer v4.2.1</h1><p>Natural rhythm, real voice, academic confidence.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below:", height=250)

if input_text.strip():
    words = len(input_text.split())
    score = round(textstat.flesch_reading_ease(input_text), 1)
    st.markdown(f"**📊 Input Word Count:** {words} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; **🧠 Readability Score:** {score}%")

if st.button("🔁 Humanize Text") or (st.session_state.human_output and st.button("♻️ Re-Humanize Again")):
    if input_text.strip():
        with st.spinner("Finalizing balance of clarity and realism..."):
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
st.markdown("#### 🧠 InfiniAi-Humanizer v4.2.1 — Precision Student Mode")
st.markdown("""
Upgraded with:
- ⚖️ Clear-to-choppy balance
- ✂️ Natural fragments + echo phrasing
- 📚 Strict academic formatting
- 🔐 Safe for detectors and human eyes alike
Your writing. Refined. Human. Real.
""")