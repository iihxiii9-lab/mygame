import pandas as pd
import streamlit as st

st.set_page_config(page_title="Tic-Tac-Toe", layout="centered")


# --- SCORE MANAGEMENT ---
def load_scores():
    if "local_scores" not in st.session_state:
        st.session_state.local_scores = [
            {"Name": "ProBot", "Score": 5},
            {"Name": "Player 1", "Score": 3},
        ]
    df = pd.DataFrame(st.session_state.local_scores)
    return df.sort_values(by="Score", ascending=False).reset_index(drop=True)


def save_score(name):
    if "local_scores" not in st.session_state:
        st.session_state.local_scores = []

    # Update score if player exists, otherwise add new record
    found = False
    for entry in st.session_state.local_scores:
        if entry["Name"] == name:
            entry["Score"] += 1
            found = True
            break
    if not found:
        st.session_state.local_scores.append({"Name": name, "Score": 1})


# --- GAME LOGIC ---
def check_winner(board):
    wins = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],  # Rows
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],  # Columns
        [0, 4, 8],
        [2, 4, 6],  # Diagonals
    ]
    for w in wins:
        if board[w[0]] == board[w[1]] == board[w[2]] != "":
            return board[w[0]]
    if "" not in board:
        return "Tie"
    return None


def bot_move(board):
    # 1. Try to win
    for i in range(9):
        if board[i] == "":
            board[i] = "O"
            if check_winner(board) == "O":
                return
            board[i] = ""

    # 2. Block player from winning
    for i in range(9):
        if board[i] == "":
            board[i] = "X"
            if check_winner(board) == "X":
                board[i] = "O"
                return
            board[i] = ""

    # 3. Pick center or first open space
    if board[4] == "":
        board[4] = "O"
        return

    for i in range(9):
        if board[i] == "":
            board[i] = "O"
            return


def reset_board():
    st.session_state.board = [""] * 9
    st.session_state.turn = "X"
    st.session_state.winner = None
    st.session_state.game_started = True


# --- INITIAL SESSION STATE ---
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "board" not in st.session_state:
    st.session_state.board = [""] * 9
if "turn" not in st.session_state:
    st.session_state.turn = "X"
if "winner" not in st.session_state:
    st.session_state.winner = None


# --- UI LAYOUT ---
st.title("❌⭕ Tic-Tac-Toe")

if not st.session_state.game_started:
    p1_name = st.text_input("Player 1 (X) Name:", value="Player 1")
    mode = st.radio("Opponent Mode:", ["vs Computer Bot", "2 Player (Shared Keyboard)"])
    p2_name = "Computer Bot" if "Bot" in mode else st.text_input("Player 2 (O) Name:", value="Player 2")

    if st.button("🚀 Start Game", use_container_width=True):
        st.session_state.p1_name = p1_name
        st.session_state.p2_name = p2_name
        st.session_state.vs_bot = "Bot" in mode
        reset_board()
        st.rerun()

else:
    p1_name = st.session_state.p1_name
    p2_name = st.session_state.p2_name
    vs_bot = st.session_state.vs_bot

    # Current turn indicator
    if not st.session_state.winner:
        current_player = p1_name if st.session_state.turn == "X" else p2_name
        st.info(f"Turn: **{current_player} ({st.session_state.turn})**")

    # Render 3x3 Grid
    board = st.session_state.board
    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            label = board[idx] if board[idx] != "" else " "

            # Button click handling
            if cols[col].button(
                label,
                key=f"btn_{idx}",
                use_container_width=True,
                disabled=bool(st.session_state.winner or board[idx] != ""),
            ):
                # Player Move
                board[idx] = st.session_state.turn
                st.session_state.winner = check_winner(board)

                # Switch turn or trigger Bot
                if not st.session_state.winner:
                    if vs_bot:
                        bot_move(board)
                        st.session_state.winner = check_winner(board)
                    else:
                        st.session_state.turn = "O" if st.session_state.turn == "X" else "X"

                st.rerun()

    # Game Result Banner
    if st.session_state.winner:
        if st.session_state.winner == "Tie":
            st.warning("🤝 It's a Tie!")
        else:
            winner_name = p1_name if st.session_state.winner == "X" else p2_name
            st.balloons()
            st.success(f"🎉 **{winner_name} ({st.session_state.winner}) Wins!**")
            save_score(winner_name)

        if st.button("🔄 Play Again", use_container_width=True):
            reset_board()
            st.rerun()

        if st.button("⚙️ Change Mode / Names"):
            st.session_state.game_started = False
            st.rerun()

# Leaderboard
st.markdown("---")
st.subheader("🏆 Leaderboard (Total Wins)")
st.dataframe(load_scores(), use_container_width=True)
