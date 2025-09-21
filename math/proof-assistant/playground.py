import streamlit as st
from pathlib import Path
from pygments import highlight
from pygments.lexers import LeanLexer
from pygments.formatters import HtmlFormatter

st.title("🔹 Proof Assistant Playground")
st.write("Exploring basic Lean4 proofs interactively.")

# Loading lean proofs
lean_file = Path("lean_playground/LeanPlayground.lean")
code = lean_file.read_text()

theorems = {
    "Identity of addition (n + 0 = n)": "add_zero",
    "Commutativity of addition (a + b = b + a)": "add_comm",
}

choice = st.selectbox("Choose a theorem:", list(theorems.keys()))

formatter = HtmlFormatter(style="friendly")
st.markdown(
    f"<style>{formatter.get_style_defs('.highlight')}</style>",
    unsafe_allow_html=True,
)

selected = theorems[choice]
proof_snippet = "\n".join(
    [
        line
        for line in code.splitlines()
        if selected in line or line.strip().startswith("theorem")
    ]
)

st.write("### Proof in Lean4")
st.markdown(highlight(proof_snippet, LeanLexer(), formatter), unsafe_allow_html=True)
