import time
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
SCORE_FILE = "game.txt"
TRACK_LENGTH = 20

st.set_page_config(page_title="Snake Jumper - Single & Multiplayer", layout="centered")


# --- LOCAL SCORE MANAGEMENT ---
def load_scores():
    try:
        if not st.session_state.get("local_scores"):
            st.session_state.local_scores = [
                {"Name": "ProBot", "Score": 120},
                {"Name": "Player 1", "Score": 80},
            ]
        df = pd.DataFrame(st.session_state.local_scores)
        return df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["Name", "Score"])


def save_score(name, score):
    if "local_scores" not in st.session_state:
        st.session_state.local_scores = []
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
if "p1_score" not in st.session_state:
    st.session_state.p1_score = 0
if "p2_score" not in st.session_state:
    st.session_state.p2_score = 0


def reset_game(player_name, opponent_type):
    st.session_state.p1_name = player_name
    st.session_state.p2_name = "Computer Bot" if opponent_type == "Computer" else "Player 2"
    st.session_state.opponent_type = opponent_type
    st.session_state.p1_y = 0
    st.session_state.p2_y = 0
    st.session_state.obstacles = [15]
    st.session_state.p1_score = 0
    st.session_state.p2_score = 0
    st.session_state.game_over = False
    st.session_state.game_started = True


def step():
    if not st.session_state.game_started or st.session_state.game_over:
        return

    # 1. Player 1 Jump Logic (resets to ground after 1 frame)
    if st.session_state.p1_y == 1:
        st.session_state.p1_y = 0

    # 2. Computer AI Logic (Auto-jumps when obstacle is near position 2)
    if st.session_state.opponent_type == "Computer":
        incoming_obstacle = any(obs in [3, 4] for obs in st.session_state.obstacles)
        st.session_state.p2_y = 1 if incoming_obstacle else 0
    elif st.session_state.p2_y == 1:
        st.session_state.p2_y = 0

    # 3. Move Obstacles
    new_obstacles = []
    for obs in st.session_state.obstacles:
        next_pos = obs - 1

        # Check Collision at Index 2
        p1_hit = (next_pos == 2 and st.session_state.p1_y == 0)
        p2_hit = (next_pos == 2 and st.session_state.p2_y == 0)

        if p1_hit or p2_hit:
            st.session_state.game_over = True
            save_score(st.session_state.p1_name, st.session_state.p1_score)
            save_score(st.session_state.p2_name, st.session_state.p2_score)
            return
        elif next_pos >= 0:
            new_obstacles.append(next_pos)
        else:
            st.session_state.p1_score += 10
            st.session_state.p2_score += 10

    # Spawn new obstacle
    if not new_obstacles or (TRACK_LENGTH - 1 - new_obstacles[-1] >= 6):
        new_obstacles.append(TRACK_LENGTH - 1)

    st.session_state.obstacles = new_obstacles


# --- UI LAYOUT ---
st.title("🐍 Snake Jumper (vs Computer / 2 Player)")

# Sidebar Setup
st.sidebar.header("Game Options")
player_name = st.sidebar.text_input("Your Name", value="Player 1").strip()
mode = st.sidebar.radio("Opponent Mode", ["vs Computer (Instant Play)", "2 Player Local"])

if st.sidebar.button("Start / Reset Game"):
    if not player_name:
        st.sidebar.warning("Please enter your name!")
    else:
        opp_type = "Computer" if "Computer" in mode else "Player 2"
        reset_game(player_name, opp_type)
        st.rerun()

# Engine Rendering
if st.session_state.game_started and not st.session_state.game_over:
    p1_name = st.session_state.p1_name
    p2_name = st.session_state.p2_name

    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"🟢 {p1_name}", f"Score: {st.session_state.p1_score}")
    with c2:
        st.metric(f"🤖 {p2_name}", f"Score: {st.session_state.p2_score}")

    # Build Tracks
    p1_air = ["⬜"] * TRACK_LENGTH
    p1_ground = ["⬜"] * TRACK_LENGTH
    p2_air = ["⬜"] * TRACK_LENGTH
    p2_ground = ["⬜"] * TRACK_LENGTH

    for obs in st.session_state.obstacles:
        if 0 <= obs < TRACK_LENGTH:
            p1_ground[obs] = "🌵"
            p2_ground[obs] = "🌵"

    if st.session_state.p1_y == 1:
        p1_air[2] = "🟢"
    else:
        p1_ground[2] = "🟢"

    if st.session_state.p2_y == 1:
        p2_air[2] = "🤖"
    else:
        p2_ground[2] = "🤖"

    st.markdown(f"**{p1_name}'s Track:**")
    st.text("".join(p1_air) + "\n" + "".join(p1_ground))

    st.markdown(f"**{p2_name}'s Track:**")
    st.text("".join(p2_air) + "\n" + "".join(p2_ground))

    # Controls
    if st.button("🦘 JUMP (Space / Enter)", key="jump_btn"):
        st.session_state.p1_y = 1
        step()
        st.rerun()

    # Keyboard Listener for Space / Enter
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const win = window.parent;
        if (!win.snakeJumpBotHandler) {
            win.snakeJumpBotHandler = true;
            win.addEventListener('keydown', function(e) {
                if (e.key === ' ' || e.key === 'Enter') {
                    e.preventDefault();
                    const btn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('JUMP'));
                    if (btn) btn.click();
                }
            }, { passive: false });
        }
        </script>
        """,
        height=0,
        width=0,
    )

elif st.session_state.game_over:
    st.error(f"💥 Game Over! Final Scores — {st.session_state.p1_name}: {st.session_state.p1_score} | {st.session_state.p2_name}: {st.session_state.p2_score}")
    st.info("Click 'Start / Reset Game' in the sidebar to try again.")

else:
    st.info("Enter your name in the sidebar and click 'Start / Reset Game' to jump in!")

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard")
st.dataframe(load_scores(), use_container_width=True)
