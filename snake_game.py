import os
import random
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
SCORE_FILE = "game.txt"
BOARD_ROWS = 15
BOARD_COLS = 15

st.set_page_config(page_title="Streamlit Snake Game", layout="centered")

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


# Initialize session state variables
if "snake" not in st.session_state:
    st.session_state.snake = [(7, 7), (7, 6), (7, 5)]
if "direction" not in st.session_state:
    st.session_state.direction = "RIGHT"
if "food" not in st.session_state:
    st.session_state.food = (3, 3)
if "score" not in st.session_state:
    st.session_state.score = 0
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_started" not in st.session_state:
    st.session_state.game_started = False


def reset_game():
    st.session_state.snake = [(7, 7), (7, 6), (7, 5)]
    st.session_state.direction = "RIGHT"
    st.session_state.food = spawn_food([(7, 7), (7, 6), (7, 5)])
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.game_started = True


def spawn_food(snake):
    while True:
        food = (
            random.randint(0, BOARD_ROWS - 1),
            random.randint(0, BOARD_COLS - 1),
        )
        if food not in snake:
            return food


def step():
    if st.session_state.game_over or not st.session_state.game_started:
        return

    head_r, head_c = st.session_state.snake[0]

    if st.session_state.direction == "UP":
        new_head = (head_r - 1, head_c)
    elif st.session_state.direction == "DOWN":
        new_head = (head_r + 1, head_c)
    elif st.session_state.direction == "LEFT":
        new_head = (head_r, head_c - 1)
    elif st.session_state.direction == "RIGHT":
        new_head = (head_r, head_c + 1)

    # Collision with walls or self
    if not (
        0 <= new_head[0] < BOARD_ROWS and 0 <= new_head[1] < BOARD_COLS
    ) or new_head in st.session_state.snake:
        st.session_state.game_over = True
        save_score(st.session_state.player_name, st.session_state.score)
        return

    # Move snake
    st.session_state.snake.insert(0, new_head)

    # Food collision
    if new_head == st.session_state.food:
        st.session_state.score += 10
        st.session_state.food = spawn_food(st.session_state.snake)
    else:
        st.session_state.snake.pop()


def change_dir(new_dir):
    opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
    if new_dir != opposites.get(st.session_state.direction):
        st.session_state.direction = new_dir
        step()


# --- UI LAYOUT ---
st.title("🐍 Multi-User Snake Game")

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

# Display Game Grid
grid = [["⬜" for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]

if st.session_state.game_started:
    for r, c in st.session_state.snake:
        grid[r][c] = "🟩"
    fr, fc = st.session_state.food
    grid[fr][fc] = "🍎"

board_str = "\n".join(["".join(row) for row in grid])
st.text(board_str)

# Screen D-Pad Controls
st.markdown("**Controls (Use Keyboard Arrows / WASD or On-Screen Buttons):**")
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("⬆️ Up", key="btn_up"):
        change_dir("UP")
        st.rerun()

c4, c5, c6 = st.columns([1, 1, 1])
with c4:
    if st.button("⬅️ Left", key="btn_left"):
        change_dir("LEFT")
        st.rerun()
with c6:
    if st.button("➡️ Right", key="btn_right"):
        change_dir("RIGHT")
        st.rerun()

c7, c8, c9 = st.columns([1, 1, 1])
with c8:
    if st.button("⬇️ Down", key="btn_down"):
        change_dir("DOWN")
        st.rerun()

# Keyboard Event Listener (Prevents page scrolling & triggers movements)
if st.session_state.game_started and not st.session_state.game_over:
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const win = window.parent;

        if (!win.snakeKeyHandlerAttached) {
            win.snakeKeyHandlerAttached = true;
            win.addEventListener('keydown', function(e) {
                // Intercept arrow keys & prevent browser scrolling
                if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(e.key)) {
                    e.preventDefault();
                }

                let btn = null;
                const buttons = Array.from(doc.querySelectorAll('button'));

                if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') {
                    btn = buttons.find(b => b.innerText.includes('Up'));
                } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') {
                    btn = buttons.find(b => b.innerText.includes('Down'));
                } else if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
                    btn = buttons.find(b => b.innerText.includes('Left'));
                } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
                    btn = buttons.find(b => b.innerText.includes('Right'));
                }

                if (btn) {
                    btn.click();
                }
            }, { passive: false });
        }
        </script>
        """,
        height=0,
        width=0,
    )

if st.session_state.game_over:
    st.error(f"Game Over! Final Score: {st.session_state.score}")

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard")
st.dataframe(load_scores(), use_container_width=True)
