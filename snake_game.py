import os
import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
SCORE_FILE = "game.txt"
TRACK_LENGTH = 20

st.set_page_config(page_title="Snake Jumper", layout="centered")

# Ensure game.txt exists
if not os.path.exists(SCORE_FILE):
    open(SCORE_FILE, "w").close()


def load_scores():
    if not os.path.exists(SCORE_FILE):
        return pd.DataFrame(columns=["Name", "Score"])

    scores = []
    with open(SCORE_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and "," in line:
                parts = line.rsplit(",", 1)
                name = parts[0]
                try:
                    score = int(parts[1])
                    scores.append({"Name": name, "Score": score})
                except ValueError:
                    continue

    df = pd.DataFrame(scores)
    if not df.empty:
        df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    return df


def save_score(player_name, score):
    with open(SCORE_FILE, "a") as f:
        f.write(f"{player_name},{score}\n")


# Initialize session state
if "snake_y" not in st.session_state:
    st.session_state.snake_y = 0  # 0 = Ground, 1 = Jumping
if "obstacles" not in st.session_state:
    st.session_state.obstacles = [15]  # Positions of obstacles on the track
if "score" not in st.session_state:
    st.session_state.score = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_started" not in st.session_state:
    st.session_state.game_started = False


def reset_game():
    st.session_state.snake_y = 0
    st.session_state.obstacles = [15]
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.game_started = True


def step(should_jump=False):
    if st.session_state.game_over or not st.session_state.game_started:
        return

    # Process Jump Logic
    if should_jump or st.session_state.snake_y > 0:
        if st.session_state.snake_y == 0 and should_jump:
            st.session_state.snake_y = 1
        else:
            st.session_state.snake_y = 0  # Land back down

    # Move obstacles left
    new_obstacles = []
    for obs in st.session_state.obstacles:
        next_pos = obs - 1
        if next_pos == 2 and st.session_state.snake_y == 0:
            # Collision detected at snake position (index 2) while grounded
            st.session_state.game_over = True
            save_score(st.session_state.player_name, st.session_state.score)
            return
        elif next_pos >= 0:
            new_obstacles.append(next_pos)
        else:
            # Successfully passed obstacle
            st.session_state.score += 10

    # Spawn new obstacles randomly
    if not new_obstacles or (TRACK_LENGTH - 1 - new_obstacles[-1] >= 6 and random.random() < 0.4):
        new_obstacles.append(TRACK_LENGTH - 1)

    st.session_state.obstacles = new_obstacles


# --- UI LAYOUT ---
st.title("🐍 Snake Jumper")

player_name = st.text_input(
    "Enter Player Name:",
    value=st.session_state.get("player_name", ""),
    disabled=st.session_state.game_started and not st.session_state.game_over,
)
st.session_state.player_name = player_name

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Start / Restart Game"):
        if not player_name.strip():
            st.warning("Please enter your name first!")
        else:
            reset_game()
            st.rerun()

with col_btn2:
    st.metric("Score", st.session_state.score)

# Render Track
air_row = ["⬜"] * TRACK_LENGTH
ground_row = ["⬜"] * TRACK_LENGTH

# Render Obstacles
for obs in st.session_state.obstacles:
    if 0 <= obs < TRACK_LENGTH:
        ground_row[obs] = "🌵"

# Render Snake (fixed at horizontal index 2)
if st.session_state.game_started:
    if st.session_state.snake_y == 1:
        air_row[2] = "🐍"
    else:
        ground_row[2] = "🐍"

track_display = "".join(air_row) + "\n" + "".join(ground_row)
st.text(track_display)

# Jump Controls
st.markdown("**Controls:** Press **Spacebar** or **Enter** (or click below) to Jump!")

if st.button("🦘 JUMP", key="btn_jump"):
    step(should_jump=True)
    st.rerun()

# Global Event Listener for Spacebar & Enter Key
if st.session_state.game_started and not st.session_state.game_over:
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const win = window.parent;

        if (!win.snakeJumpHandlerAttached) {
            win.snakeJumpHandlerAttached = true;
            win.addEventListener('keydown', function(e) {
                if (e.key === ' ' || e.key === 'Enter') {
                    e.preventDefault();
                    const btn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('JUMP'));
                    if (btn) {
                        btn.click();
                    }
                }
            }, { passive: false });
        }
        </script>
        """,
        height=0,
        width=0,
    )

if st.session_state.game_over:
    st.error(f"Game Over! You crashed into an obstacle. Final Score: {st.session_state.score}")

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard")
st.dataframe(load_scores(), use_container_width=True)
