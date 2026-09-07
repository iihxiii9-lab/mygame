import time
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
# Replace this with your actual Firebase Realtime Database URL
FIREBASE_URL = "https://YOUR-FIREBASE-PROJECT.firebaseio.com/"
TRACK_LENGTH = 20

st.set_page_config(page_title="2-Player Snake Jumper", layout="centered")


# --- FIREBASE HELPERS ---
def get_room_data(room_code):
    try:
        r = requests.get(f"{FIREBASE_URL}rooms/{room_code}.json")
        return r.json() or {}
    except Exception:
        return {}


def update_room_data(room_code, data):
    try:
        requests.patch(f"{FIREBASE_URL}rooms/{room_code}.json", json=data)
    except Exception:
        pass


def save_high_score(name, score):
    try:
        requests.post(
            f"{FIREBASE_URL}leaderboard.json",
            json={"Name": name, "Score": score},
        )
    except Exception:
        pass


def get_leaderboard():
    try:
        r = requests.get(f"{FIREBASE_URL}leaderboard.json")
        data = r.json() or {}
        scores = list(data.values())
        df = pd.DataFrame(scores)
        if not df.empty:
            return df.sort_values(by="Score", ascending=False).reset_index(
                drop=True
            )
    except Exception:
        pass
    return pd.DataFrame(columns=["Name", "Score"])


# --- UI LAYOUT ---
st.title("🐍 2-Player Online Snake Jumper")

# Room & Player Setup
st.sidebar.header("Lobby Setup")
room_id = st.sidebar.text_input("Room Code", value="ROOM1").upper().strip()
player_name = st.sidebar.text_input("Your Name", value="Player 1").strip()
player_slot = st.sidebar.radio("Select Slot", ["p1", "p2"])

room = get_room_data(room_id)

if st.sidebar.button("Join / Reset Room"):
    initial_state = {
        "p1_name": player_name if player_slot == "p1" else room.get("p1_name", "Player 1"),
        "p2_name": player_name if player_slot == "p2" else room.get("p2_name", "Player 2"),
        "p1_y": 0,
        "p2_y": 0,
        "obstacles": [15],
        "p1_score": 0,
        "p2_score": 0,
        "game_over": False,
        "game_started": True,
    }
    update_room_data(room_id, initial_state)
    st.rerun()

# --- GAME ENGINE ---
if room.get("game_started") and not room.get("game_over"):
    st.caption(f"Connected to **Room: {room_id}** | Playing as **{player_slot.upper()}**")

    p1_name = room.get("p1_name", "Player 1")
    p2_name = room.get("p2_name", "Player 2")
    p1_y = room.get("p1_y", 0)
    p2_y = room.get("p2_y", 0)
    obstacles = room.get("obstacles", [15])

    # Display Scores
    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"🟢 {p1_name}", f"Score: {room.get('p1_score', 0)}")
    with c2:
        st.metric(f"🔵 {p2_name}", f"Score: {room.get('p2_score', 0)}")

    # Render Tracks
    p1_air = ["⬜"] * TRACK_LENGTH
    p1_ground = ["⬜"] * TRACK_LENGTH
    p2_air = ["⬜"] * TRACK_LENGTH
    p2_ground = ["⬜"] * TRACK_LENGTH

    for obs in obstacles:
        if 0 <= obs < TRACK_LENGTH:
            p1_ground[obs] = "🌵"
            p2_ground[obs] = "🌵"

    if p1_y == 1:
        p1_air[2] = "🟢"
    else:
        p1_ground[2] = "🟢"

    if p2_y == 1:
        p2_air[2] = "🔵"
    else:
        p2_ground[2] = "🔵"

    st.markdown(f"**{p1_name}'s Track (P1):**")
    st.text("".join(p1_air) + "\n" + "".join(p1_ground))

    st.markdown(f"**{p2_name}'s Track (P2):**")
    st.text("".join(p2_air) + "\n" + "".join(p2_ground))

    # Jump Action
    if st.button("🦘 JUMP (Space / Enter)", key="jump_btn"):
        current_y = room.get(f"{player_slot}_y", 0)
        new_y = 1 if current_y == 0 else 0
        update_room_data(room_id, {f"{player_slot}_y": new_y})

        # Obstacle physics and collision checking
        new_obstacles = []
        game_over = False
        p1_score = room.get("p1_score", 0)
        p2_score = room.get("p2_score", 0)

        for obs in obstacles:
            next_pos = obs - 1
            if (next_pos == 2 and p1_y == 0) or (next_pos == 2 and p2_y == 0):
                game_over = True
            elif next_pos >= 0:
                new_obstacles.append(next_pos)
            else:
                p1_score += 10
                p2_score += 10

        if not new_obstacles:
            new_obstacles.append(TRACK_LENGTH - 1)

        if game_over:
            save_high_score(p1_name, p1_score)
            save_high_score(p2_name, p2_score)
            update_room_data(room_id, {"game_over": True})
        else:
            update_room_data(
                room_id,
                {
                    "obstacles": new_obstacles,
                    "p1_score": p1_score,
                    "p2_score": p2_score,
                },
            )
        st.rerun()

    # Keyboard Listener for Space / Enter
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const win = window.parent;
        if (!win.multiplayerKeyHandler) {
            win.multiplayerKeyHandler = true;
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

elif room.get("game_over"):
    st.error("💥 Crash! Game Over for both players.")
    st.info("Click 'Join / Reset Room' in the sidebar to play again.")

else:
    st.info("Enter a Room Code and click 'Join / Reset Room' in the sidebar to start!")

# Global Leaderboard
st.markdown("---")
st.subheader("🏆 Global Leaderboard")
st.dataframe(get_leaderboard(), use_container_width=True)
