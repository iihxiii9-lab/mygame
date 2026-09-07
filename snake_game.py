import time
import pandas as pd
import streamlit as st

# --- CONFIGURATION ---
TRACK_LENGTH = 20

st.set_page_config(
    page_title="Snake Jumper - Auto Matchmaking", layout="centered"
)


# --- SHARED MATCHMAKING QUEUE (Cross-Session) ---
@st.cache_resource
def get_global_matchmaking():
    return {"waiting_player": None, "rooms": {}}


global_data = get_global_matchmaking()


# --- LOCAL SCORE MANAGEMENT ---
def load_scores():
    try:
        if not st.session_state.get("local_scores"):
            st.session_state.local_scores = [
                {"Name": "ProBot", "Score": 120},
                {"Name": "Player 1", "Score": 80},
            ]
        df = pd.DataFrame(st.session_state.local_scores)
        return df.sort_values(by="Score", ascending=False).reset_index(
            drop=True
        )
    except Exception:
        return pd.DataFrame(columns=["Name", "Score"])


def save_score(name, score):
    if "local_scores" not in st.session_state:
        st.session_state.local_scores = []
    st.session_state.local_scores.append({"Name": name, "Score": score})


# --- SESSION STATE INITIALIZATION ---
if "searching" not in st.session_state:
    st.session_state.searching = False
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "room_id" not in st.session_state:
    st.session_state.room_id = None
if "player_role" not in st.session_state:
    st.session_state.player_role = "p1"


def init_room(p1_name, p2_name, is_bot=False):
    return {
        "p1_name": p1_name,
        "p2_name": p2_name,
        "is_bot": is_bot,
        "p1_y": 0,
        "p2_y": 0,
        "obstacles": [15],
        "p1_score": 0,
        "p2_score": 0,
        "game_over": False,
    }


def step(room):
    if room["game_over"]:
        return

    # Reset Jump States after frame
    if room["p1_y"] == 1:
        room["p1_y"] = 0

    # Computer AI Logic if Bot
    if room["is_bot"]:
        incoming = any(obs in [3, 4] for obs in room["obstacles"])
        room["p2_y"] = 1 if incoming else 0
    elif room["p2_y"] == 1:
        room["p2_y"] = 0

    # Move Obstacles
    new_obstacles = []
    for obs in room["obstacles"]:
        next_pos = obs - 1

        p1_hit = next_pos == 2 and room["p1_y"] == 0
        p2_hit = next_pos == 2 and room["p2_y"] == 0

        if p1_hit or p2_hit:
            room["game_over"] = True
            save_score(room["p1_name"], room["p1_score"])
            save_score(room["p2_name"], room["p2_score"])
            return
        elif next_pos >= 0:
            new_obstacles.append(next_pos)
        else:
            room["p1_score"] += 10
            room["p2_score"] += 10

    if not new_obstacles or (TRACK_LENGTH - 1 - new_obstacles[-1] >= 6):
        new_obstacles.append(TRACK_LENGTH - 1)

    room["obstacles"] = new_obstacles


# --- UI LAYOUT ---
st.title("🐍 Snake Jumper")

player_name = st.text_input("Enter Your Name:", value="Player 1").strip()

# --- LOBBY & MATCHMAKING ---
if not st.session_state.game_started:

    if not st.session_state.searching:
        if st.button("🎮 Start Game / Find Match"):
            if not player_name:
                st.warning("Please enter your name first!")
            else:
                waiting = global_data["waiting_player"]

                # Case A: Real player is already in queue -> Pair instantly
                if waiting and waiting["name"] != player_name:
                    room_id = f"room_{waiting['name']}_{player_name}"
                    global_data["rooms"][room_id] = init_room(
                        waiting["name"], player_name, is_bot=False
                    )
                    global_data["waiting_player"] = None

                    st.session_state.room_id = room_id
                    st.session_state.player_role = "p2"
                    st.session_state.game_started = True
                    st.rerun()

                # Case B: Queue empty -> Wait for someone or launch Bot
                else:
                    global_data["waiting_player"] = {
                        "name": player_name,
                        "time": time.time(),
                    }
                    st.session_state.searching = True
                    st.rerun()

    else:
        st.info("🔍 Searching for an online player...")

        # Check if matched by another player
        matched = False
        for r_id, r_data in list(global_data["rooms"].items()):
            if r_data["p1_name"] == player_name:
                st.session_state.room_id = r_id
                st.session_state.player_role = "p1"
                st.session_state.game_started = True
                st.session_state.searching = False
                matched = True
                st.rerun()
                break

        if not matched:
            waiting = global_data["waiting_player"]
            # Check if 4 seconds passed while waiting
            if waiting and (time.time() - waiting["time"] > 4):
                global_data["waiting_player"] = None
                room_id = f"bot_room_{player_name}"
                global_data["rooms"][room_id] = init_room(
                    player_name, "Computer Bot", is_bot=True
                )
                st.session_state.room_id = room_id
                st.session_state.player_role = "p1"
                st.session_state.game_started = True
                st.session_state.searching = False
                st.rerun()
            else:
                # Refresh page to check matchmaking status
                time.sleep(1)
                st.rerun()

# --- ACTIVE GAME ENGINE ---
if st.session_state.game_started and st.session_state.room_id:
    room_id = st.session_state.room_id
    room = global_data["rooms"].get(room_id)

    if room:
        role = st.session_state.player_role
        p1_name = room["p1_name"]
        p2_name = room["p2_name"]

        c1, c2 = st.columns(2)
        with c1:
            st.metric(f"🟢 {p1_name}", f"Score: {room['p1_score']}")
        with c2:
            opponent_icon = "🤖" if room["is_bot"] else "🔵"
            st.metric(
                f"{opponent_icon} {p2_name}", f"Score: {room['p2_score']}"
            )

        # Build Track Displays
        p1_air, p1_ground = ["⬜"] * TRACK_LENGTH, ["⬜"] * TRACK_LENGTH
        p2_air, p2_ground = ["⬜"] * TRACK_LENGTH, ["⬜"] * TRACK_LENGTH

        for obs in room["obstacles"]:
            if 0 <= obs < TRACK_LENGTH:
                p1_ground[obs] = "🌵"
                p2_ground[obs] = "🌵"

        if room["p1_y"] == 1:
            p1_air[2] = "🟢"
        else:
            p1_ground[2] = "🟢"

        if room["p2_y"] == 1:
            p2_air[2] = "🤖" if room["is_bot"] else "🔵"
        else:
            p2_ground[2] = "🤖" if room["is_bot"] else "🔵"

        st.markdown(f"**{p1_name}'s Track:**")
        st.text("".join(p1_air) + "\n" + "".join(p1_ground))

        st.markdown(f"**{p2_name}'s Track:**")
        st.text("".join(p2_air) + "\n" + "".join(p2_ground))

        # Game Controls
        if not room["game_over"]:
            if st.button("🦘 JUMP (Space / Enter)", key="jump_btn"):
                if role == "p1":
                    room["p1_y"] = 1
                else:
                    room["p2_y"] = 1

                step(room)
                st.rerun()

            st.html(
                """
                <script>
                const doc = window.parent.document;
                const win = window.parent;
                if (!win.snakeMatchmakingHandler) {
                    win.snakeMatchmakingHandler = true;
                    win.addEventListener('keydown', function(e) {
                        if (e.key === ' ' || e.key === 'Enter') {
                            e.preventDefault();
                            const btn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('JUMP'));
                            if (btn) btn.click();
                        }
                    }, { passive: false });
                }
                </script>
                """
            )
        else:
            st.error(
                f"💥 Game Over! Final Scores — {p1_name}: {room['p1_score']} |"
                f" {p2_name}: {room['p2_score']}"
            )
            if st.button("Play Again"):
                st.session_state.game_started = False
                st.session_state.searching = False
                st.session_state.room_id = None
                st.rerun()

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard")
st.dataframe(load_scores(), width="stretch")
