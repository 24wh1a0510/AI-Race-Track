import os
import time
import base64
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from main import ask, MODELS

st.set_page_config(page_title="AI Race Track", page_icon="🏁", layout="wide")

# ---- Background image: prefer a local file, else a hosted fallback ----
# Drop your own image at  assets/bg.jpg  (a humanoid AI robot / neural-net scene)
# and it will be used automatically. Otherwise a futuristic stock image is loaded.
LOCAL_BG = os.path.join("assets", "bg.jpg")
FALLBACK_BG = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1920&q=80"

def background_css_value():
    """Return a CSS url(...) for the background — base64 local file if present, else remote."""
    if os.path.exists(LOCAL_BG):
        with open(LOCAL_BG, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"url('data:image/jpeg;base64,{encoded}')"
    return f"url('{FALLBACK_BG}')"

BG_IMAGE = background_css_value()

# ---- Friendly racer identities for each model id ----
RACERS = {
    "openai/gpt-5.5":                {"name": "GPT",     "emoji": "🟢", "car": "🏎️"},
    "anthropic/claude-opus-4.8":     {"name": "Claude",  "emoji": "🟣", "car": "🚗"},
    "google/gemini-3.1-flash-lite":  {"name": "Gemini",  "emoji": "🔵", "car": "🏎️"},
    "deepseek/deepseek-v4-flash":    {"name": "DeepSeek","emoji": "🐋", "car": "🚙"},
}

def racer_of(model):
    return RACERS.get(model, {"name": model, "emoji": "⚪", "car": "🏎️"})

# ---------------- Background image (own block so CSS braces don't clash with f-string) ----------------
st.markdown(
    f"""
    <style>
    .stApp {{
        /* dark overlay gradient ON TOP of the image keeps the UI readable */
        background:
            linear-gradient(180deg, rgba(5,7,15,0.82) 0%, rgba(5,7,15,0.92) 100%),
            {BG_IMAGE};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #e8eefc;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Styling ----------------
st.markdown(
    """
    <style>
    h1, h2, h3, h4, p, label, .stMarkdown { color: #e8eefc !important; }

    /* neon title */
    .race-title {
        font-size: 3rem; font-weight: 900; letter-spacing: 2px; text-align: center;
        background: linear-gradient(90deg, #00e5ff, #ff00e5, #ffe600);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: hue 6s linear infinite;
    }
    @keyframes hue { from { filter: hue-rotate(0deg); } to { filter: hue-rotate(360deg); } }

    /* checkered divider */
    .checker {
        height: 14px; margin: 8px 0 22px 0; border-radius: 6px;
        background-image:
            linear-gradient(45deg, #fff 25%, transparent 25%),
            linear-gradient(-45deg, #fff 25%, transparent 25%),
            linear-gradient(45deg, transparent 75%, #fff 75%),
            linear-gradient(-45deg, transparent 75%, #fff 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0;
        background-color: #111;
        opacity: 0.8;
    }

    /* race lane */
    .lane {
        position: relative; height: 46px; margin: 10px 0;
        border-radius: 23px;
        background: repeating-linear-gradient(90deg, #11203c, #11203c 28px, #16294b 28px, #16294b 56px);
        border: 1px solid rgba(0,229,255,0.25);
        overflow: hidden;
    }
    .car {
        position: absolute; top: 6px; font-size: 1.7rem;
        transition: left 0.4s ease;
        filter: drop-shadow(0 0 8px rgba(0,229,255,0.7));
    }
    .lane-label { position: absolute; left: 14px; top: 11px; font-weight: 700; opacity: 0.85; }

    /* glass cards */
    [data-testid="column"] { }
    .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(0,229,255,0.25);
        border-radius: 16px; padding: 16px; margin-top: 8px;
        backdrop-filter: blur(6px);
        box-shadow: 0 0 18px rgba(0,229,255,0.12);
    }
    .badge {
        display:inline-block; padding:4px 12px; border-radius:999px; font-weight:700;
        margin: 2px; font-size: 0.95rem;
    }
    .badge-fast  { background: rgba(0,229,255,0.18);  border:1px solid #00e5ff; }
    .badge-cheap { background: rgba(124,252,0,0.16);  border:1px solid #7CFC00; }

    .stButton > button {
        border-radius: 14px; font-weight: 800; font-size: 1.1rem;
        padding: 0.6rem 1.6rem;
        background: linear-gradient(90deg, #00e5ff, #ff00e5);
        color: #05070f; border: none;
        box-shadow: 0 0 22px rgba(255,0,229,0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="race-title">🏁 AI Race Track</div>', unsafe_allow_html=True)
st.markdown('<div class="checker"></div>', unsafe_allow_html=True)
st.caption("Four AI models. One prompt. Who finishes first — and cheapest? 🏆")

if "running" not in st.session_state:
    st.session_state["running"] = False

prompt = st.text_area(
    "🎤 Race prompt",
    placeholder="Type the challenge for all four racers… e.g. Explain machine learning in simple terms.",
    height=130,
)

start = st.button("🚦 Start Race", type="primary", disabled=st.session_state["running"])
st.caption("💡 Costs are illustrative estimates — see OpenRouter for live pricing.")


def render_lane(placeholder, model, pct, done=False):
    r = racer_of(model)
    left = f"calc({pct}% - 22px)" if pct > 4 else "8px"
    flag = " 🏁" if done else ""
    placeholder.markdown(
        f"""
        <div>
          <div style="font-weight:700; margin-bottom:2px;">{r['emoji']} {r['name']}{flag}</div>
          <div class="lane">
            <span class="car" style="left:{left};">{r['car']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if start:
    if not prompt.strip():
        st.warning("🚧 Please enter a race prompt before starting!")
    else:
        st.session_state["running"] = True
        st.subheader("🏎️ Race in progress…")

        lane_slots = {m: st.empty() for m in MODELS}
        progress = {m: 5 for m in MODELS}
        for m in MODELS:
            render_lane(lane_slots[m], m, progress[m])

        results = {}
        with ThreadPoolExecutor(max_workers=len(MODELS)) as executor:
            futures = {executor.submit(ask, prompt, m): m for m in MODELS}

            # Animate lanes until every racer crosses the line
            while len(results) < len(MODELS):
                for fut, m in futures.items():
                    if m in results:
                        continue
                    if fut.done():
                        results[m] = fut.result()
                        render_lane(lane_slots[m], m, 100, done=True)
                    else:
                        progress[m] = min(progress[m] + 7, 90)  # creep forward
                        render_lane(lane_slots[m], m, progress[m])
                time.sleep(0.15)

        # store in original MODELS order
        st.session_state["results"] = [results[m] for m in MODELS]
        st.session_state["running"] = False
        st.balloons()


# ---------------- Results ----------------
if "results" in st.session_state:
    results = st.session_state["results"]
    ok = [r for r in results if "error" not in r]

    st.markdown('<div class="checker"></div>', unsafe_allow_html=True)
    st.header("🏆 Leaderboard")

    if ok:
        fastest = min(ok, key=lambda r: r["latency"])
        cheapest = min(ok, key=lambda r: r["cost"])

        c1, c2 = st.columns(2)
        with c1:
            r = racer_of(fastest["model"])
            st.markdown(
                f'<div class="card"><span class="badge badge-fast">🏆 Fastest</span><br>'
                f'<h3>{r["emoji"]} {r["name"]}</h3>'
                f'<p>⚡ {fastest["latency"]:.2f}s</p></div>',
                unsafe_allow_html=True,
            )
        with c2:
            r = racer_of(cheapest["model"])
            st.markdown(
                f'<div class="card"><span class="badge badge-cheap">💰 Cheapest</span><br>'
                f'<h3>{r["emoji"]} {r["name"]}</h3>'
                f'<p>💵 ${cheapest["cost"]:.6f}</p></div>',
                unsafe_allow_html=True,
            )

        # ranked table by latency
        st.markdown("#### 📊 Standings (by speed)")
        ranking = sorted(ok, key=lambda r: r["latency"])
        rows = []
        for i, r in enumerate(ranking, start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}")
            racer = racer_of(r["model"])
            rows.append({
                "Rank": medal,
                "Racer": f'{racer["emoji"]} {racer["name"]}',
                "Latency (s)": round(r["latency"], 2),
                "Cost (USD)": f'${r["cost"]:.6f}',
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.error("All racers crashed 💥 — no successful responses.")

    # ---- Answer cards ----
    st.markdown('<div class="checker"></div>', unsafe_allow_html=True)
    st.header("📝 Answers")
    columns = st.columns(len(results))
    for column, result in zip(columns, results):
        with column:
            r = racer_of(result["model"])
            st.markdown(f"### {r['emoji']} {r['name']}")
            if "error" in result:
                st.error(result["error"])
            else:
                m1, m2 = st.columns(2)
                m1.metric("⚡ Latency", f"{result['latency']:.2f}s")
                m2.metric("💵 Cost", f"${result['cost']:.6f}")
                st.markdown(f'<div class="card">{result["answer"]}</div>', unsafe_allow_html=True)
