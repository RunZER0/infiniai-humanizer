import streamlit as st
import openai
import random
import textstat
import re

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "human_output" not in st.session_state:
    st.session_state.human_output = ""
if "previous_inputs" not in st.session_state:
    st.session_state.previous_inputs = {}
if "last_input_text" not in st.session_state:
    st.session_state.last_input_text = ""

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
    additions = ["This matters.", "That’s significant.", "It’s worth noting.", "Don’t ignore this.", "Key point.",
    "Still.", "Even then.", "That said.", "On the other hand.", "Then again.",
    "Not always.", "Could be debated.", "That’s one view.", "It’s not that simple.", "There’s more to it.",
    "That’s the issue.", "Potential flaw.", "Risk worth considering.", "Could break under pressure.", "Weak point.",
    "Makes sense in context.", "That explains it.", "Fits the pattern.", "Shows something deeper.", "Hard to ignore."]
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

# === UI (v4.4 layout with v4.5 label) ===
st.markdown("""
<style>
.stApp { background-color: #0d0d0d; color: #00ffff; font-family: 'Segoe UI', monospace; text-align: center; }
textarea { background-color: #121212 !important; color: #ffffff !important; border: 1px solid #00ffff !important; border-radius: 8px !important; font-size: 16px !important; }
.stButton > button { background-color: #00ffff; color: black; font-weight: bold; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; transition: all 0.3s ease-in-out; }
.stButton > button:hover { background-color: #00cccc; transform: scale(1.03); }
.stDownloadButton button { background-color: #00ffff; color: black; font-weight: bold; border-radius: 5px; }
.centered-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
.features-grid { display: flex; justify-content: space-around; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #00ffff; }
.feature, .comment { width: 30%; text-align: left; font-size: 14px; }
.vertical-divider { border-left: 1px solid #00ffff; height: 100%; margin: 0 1rem; }
</style>
""", unsafe_allow_html=True)


# === Word Package Payment UI ===
from urllib.parse import urlencode

st.markdown(
    '<div style="display: flex; justify-content: space-between; align-items: center;">'
    '<h1 style="margin: 0;">🤖 InfiniAi-Humanizer</h1>'
    '<form action="?pay=1" method="get">'
    '<button style="background-color:#00ffff; color:black; font-weight:bold; border:none; padding:0.6rem 1.2rem; border-radius:8px; font-size:16px;">PAY</button>'
    '</form>'
    '</div>',
    unsafe_allow_html=True
)

# If user clicked the PAY button, show new page for payment
query_params = st.query_params
if 'pay' in query_params:
    st.markdown("### 📦 Select Your Word Package")
    words = st.slider("Choose your desired package size (in words):", min_value=100, max_value=100000, step=100)
    price = round((words * 0.00045), 2)
    st.markdown(f"**Estimated Price:** ${price:.2f}")

    if st.button("💰 Proceed to Pay with MPESA"):
        st.markdown(f""" 
        ### 🔐 How to Pay with MPESA (Send Money)

        - Open your MPESA menu on your phone.
        - Select **Send Money**.
        - Enter **0795191421** as the number.
        - Send **Ksh {price:.2f}** for **{words} words**.
        - Use your name as the reference.
        - After payment, wait for confirmation and return to the app.

        **Once payment is verified, full access will be granted.**
        """, unsafe_allow_html=True)
    st.stop()


st.markdown('<div class="centered-container"><p>Turn robotic AI text into real, natural, human-sounding writing.</p></div>', unsafe_allow_html=True)

input_text = st.text_area("Paste your AI-generated academic text below (Max: 10,000 characters):", height=280, max_chars=10000)

if len(input_text) > 10000:
    st.warning("⚠️ Your input is over 10,000 characters. Only the first 10,000 characters will be used.")
st.markdown(f"**{len(input_text.split())} Words, {len(input_text)} Characters**")

if st.button("🔁 Humanize / Re-Humanize Text"):
    if input_text.strip():
        trimmed_input = input_text[:10000]
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

st.markdown("**Version 4.5**")
st.markdown("---")
st.markdown("""
<div class='features-grid'>
    <div class='feature'>
        <strong>✍️ Natural Cadence:</strong><br>
        Your words flow like a real student — no rigid AI rhythm.
    </div>
    <div class='vertical-divider'></div>
    <div class='feature'>
        <strong>🔁 Structured Variance:</strong><br>
        Paragraphs are well balanced for human clarity.
    </div>
    <div class='vertical-divider'></div>
    <div class='feature'>
        <strong>📚 Academic Realism:</strong><br>
        The tone mimics thoughtful effort, not perfect computation.
    </div>
</div>

<div class='features-grid'>
    <div class='comment'>
        <em>"This actually sounds like I wrote it after a long study night."</em><br><strong>- Joseph</strong>
    </div>
    <div class='comment'>
        <em>"Passed the AI check with flying colors. And my professor said it felt authentic."</em><br><strong>- Kate</strong>
    </div>
</div>
""", unsafe_allow_html=True)
