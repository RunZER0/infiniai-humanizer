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
if "last_input_text" not in st.session_state:
    st.session_state.last_input_text = ""

# === HUMANIZER v4.4 — Balanced Burst+Flow Engine ===
PROMPT = (
    "Rewrite the following academic content like a real student would:"
    " Maintain a strong balance between punchy bursts and fluid, complete sentences."
    " Use short fragments, sentence drops, and emphasis strategically—1 to 2 per paragraph only."
    " The rest should be longer, thought-out student-style sentences."
    " Introduce mild imperfections and occasional transitions like 'Still,' or 'Even so,' to keep the flow natural."
    " Avoid robotic rhythm or stacking too many short bursts."
    " Preserve all citations, formatting, and academic structure."
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
            if len(s_clean.split()) > 18:
                buffer.append(s_clean)
            elif chop_count < 2:
                buffer.append(s_clean)
                chop_count += 1
            else:
                combined = s_clean + (" " + random.choice(["Still.", "This matters.", "Even then.", "Even so.", "That said.", "Which is why it matters."]) if random.random() < 0.3 else "")
                buffer.append(combined)
        balanced.append(" ".join(buffer))
    return "\n\n".join(balanced)

def insert_redundancy(text):
    lines = re.split(r'(?<=[.!?])\s+', text)
    output = []
    for i, line in enumerate(lines):
        output.append(line)
        if random.random() < 0.12 and len(line.split()) > 6:
            output.append(f"This shows that {line.strip().split()[0].lower()} is important.")
    return " ".join(output)

def inject_choppy_fragments(text):
    additions = ["This matters.", "Big risk.", "Still.", "Not always.", "A serious problem.", "That’s the issue.", "Even that’s not enough.", "Which is why it matters.", "Even so.", "That said."]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    chop_limit = 0
    for s in sentences:
        result.append(s)
        if random.random() < 0.15 and chop_limit < 2:
            result.append(random.choice(additions))
            chop_limit += 1
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

st.markdown('<div class="centered-container"><h1>🤖 InfiniAi-Humanizer v4.4</h1><p>Balanced bursts with flowing clarity. Undetectable. Sharp. Real.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below (Max: 10,000 characters):", height=280, max_chars=10000)

if len(input_text) > 10000:
    st.warning("⚠️ Your input is over 10,000 characters. Only the first 10,000 characters will be used.")
st.markdown(f"**✍️ Characters Entered:** {len(input_text)} / 10000  ")
st.markdown(f"**📗 Word Count (est.):** {len(input_text.split())} words")

if st.button("🔁 Humanize / Re-Humanize Text"):
    if input_text.strip():
        trimmed_input = input_text[:10000]  # ✅ Enforce 10,000-character max
        with st.spinner("Humanizing academic text..."):
            output = humanize_text(trimmed_input)
            st.session_state.human_output = output
            st.session_state.last_input_text = trimmed_input
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
st.markdown("#### 🧠 InfiniAi-Humanizer v4.4 — Balanced Burst+Flow Engine")
st.markdown("""
Features:
- ✂️ Controlled sentence bursts (1–2 per paragraph)
- 🧱 Realistic academic rhythm with occasional transitions
- 📚 Maintains clarity, urgency, and citation safety
- 🎯 Undetectable by major AI detectors
- 🚫 Input capped at 10,000 characters for optimal output quality
""")
