import pandas as pd
import streamlit as st

# --- CONFIGURATION ---
TRACK_LENGTH = 20

st.set_page_config(page_title="Snake Jumper", layout="centered")


# --- SCORE MANAGEMENT ---
def load_scores():
    if "local_scores" not in st.session_state:
        st.session_state.local_scores = [
            {"Name": "ProBot", "Score": 120},
            {"Name": "Player 1", "Score": 80},
        ]
    df = pd.DataFrame(st.session_state.local_scores)
    return df.sort_values(by="Score", ascending=False).reset_index(drop=True)


def save_score(name, score):
    st.session_state.local_scores.append({"Name": name, "Score": score})


# --- SESSION STATE INITIALIZATION ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "p1_y" not in st.session_state:
    st.session_state.p1_y = 0
if "p2_y" not in st.session_state:
    st.session_state.p2_y = 0
if "obstacles" not in st.session_state:
    st.session_state.obstacles = [15]
if "score" not in st.session_state:
    st.session_state.score = 0


def reset_game():
    st.session_state.p1_y = 0
    st.session_state.p2_y = 0
    st.session_state.obstacles = [15]
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.game_started = True


def step(vs_bot, p1_jump, p2_jump):
    if st.session_state.game_over:
        return

    # Apply manual jump inputs
    st.session_state.p1_y = 1 if p1_jump else 0

    if vs_bot:
        incoming = any(obs in [3, 4] for obs in st.session_state.obstacles)
        st.session_state.p2_y = 1 if incoming else 0
    else:
        st.session_state.p2_y = 1 if p2_jump else 0

    # Move Obstacles
    new_obstacles = []
    for obs in st.session_state.obstacles:
        next_pos = obs - 1

        p1_hit = next_pos == 2 and st.session_state.p1_y == 0
        p2_hit = next_pos == 2 and st.session_state.p2_y == 0

        if p1_hit or p2_hit:
            st.session_state.game_over = True
            save_score(st.session_state.p1_name, st.session_state.score)
            return
        elif next_pos >= 0:
            new_obstacles.append(next_pos)
        else:
            st.session_state.score += 10

    if not new_obstacles or (TRACK_LENGTH - 1 - new_obstacles[-1] >= 6):
        new_obstacles.append(TRACK_LENGTH - 1)

    st.session_state.obstacles = new_obstacles


# --- UI LAYOUT ---
st.title("🐍 Simple Snake Jumper")

if not st.session_state.game_started:
    p1_name = st.text_input("Player 1 Name:", value="Player 1")
    mode = st.radio("Select Mode:", ["vs Computer Bot", "2 Player"])

    if st.button("🚀 Start Game"):
        st.session_state.p1_name = p1_name
        st.session_state.vs_bot = "Bot" in mode
        reset_game()
        st.rerun()

else:
    vs_bot = st.session_state.vs_bot
    p1_name = st.session_state.p1_name
    p2_name = "Bot" if vs_bot else "Player 2"

    st.metric("Score", st.session_state.score)

    # Build Tracks
    p1_air, p1_ground = ["⬜"] * TRACK_LENGTH, ["⬜"] * TRACK_LENGTH
    p2_air, p2_ground = ["⬜"] * TRACK_LENGTH, ["⬜"] * TRACK_LENGTH

    for obs in st.session_state.obstacles:
        if 0 <= obs < TRACK_LENGTH:
            p1_ground[obs] = "🌵"
            p2_ground[obs] = "🌵"

    p1_ground[2] = "🟢" if st.session_state.p1_y == 0 else "⬜"
    p1_air[2] = "🟢" if st.session_state.p1_y == 1 else "⬜"

    p2_icon = "🤖" if vs_bot else "🔵"
    p2_ground[2] = p2_icon if st.session_state.p2_y == 0 else "⬜"
    p2_air[2] = p2_icon if st.session_state.p2_y == 1 else "⬜"

    st.markdown(f"**{p1_name}:**")
    st.text("".join(p1_air) + "\n" + "".join(p1_ground))

    st.markdown(f"**{p2_name}:**")
    st.text("".join(p2_air) + "\n" + "".join(p2_ground))

    # Turn Controls
    if not st.session_state.game_over:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            p1_jump = st.checkbox(f"🦘 {p1_name} Jump Next Turn")

        p2_jump = False
        if not vs_bot:
            with col2:
                p2_jump = st.checkbox("🦘 Player 2 Jump Next Turn")

        if st.button("▶️ Next Frame / Advance Track", use_container_width=True):
            step(vs_bot, p1_jump, p2_jump)
            st.rerun()
    else:
        st.error(f"💥 Game Over! Final Score: {st.session_state.score}")
        if st.button("🔄 Play Again"):
            st.session_state.game_started = False
            st.rerun()

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard")
st.dataframe(load_scores(), width="stretch")
