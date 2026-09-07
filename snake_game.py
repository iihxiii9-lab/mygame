import os
import random
import tkinter as tk
from tkinter import ttk, messagebox

# --- CONFIGURATION ---
SCORE_FILE = "game.txt"
GAME_WIDTH = 600
GAME_HEIGHT = 400
SPEED = 100  # Lower is faster (milliseconds per frame)
SPACE_SIZE = 20
BODY_PARTS = 3
SNAKE_COLOR = "#00FF00"
FOOD_COLOR = "#FF0000"
BG_COLOR = "#000000"


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-User Snake Game")
        self.root.resizable(False, False)

        self.player_name = ""
        self.score = 0
        self.direction = "down"
        self.snake = []
        self.food = None
        self.running = False

        # Ensure game.txt exists
        if not os.path.exists(SCORE_FILE):
            open(SCORE_FILE, "w").close()

        # --- UI LAYOUT ---
        top_frame = tk.Frame(root, bg="#222")
        top_frame.pack(fill=tk.X, ipadx=10, ipady=10)

        tk.Label(top_frame, text="Player Name:", fg="white", bg="#222", font=("Consolas", 12)).pack(side=tk.LEFT, padx=5)
        self.name_entry = tk.Entry(top_frame, font=("Consolas", 12), width=15)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        self.start_btn = tk.Button(top_frame, text="Start Game", command=self.start_game, font=("Consolas", 10, "bold"), bg="#4CAF50", fg="white")
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.score_label = tk.Label(top_frame, text="Score: 0", fg="white", bg="#222", font=("Consolas", 12, "bold"))
        self.score_label.pack(side=tk.RIGHT, padx=10)

        # Game Canvas
        self.canvas = tk.Canvas(root, bg=BG_COLOR, height=GAME_HEIGHT, width=GAME_WIDTH)
        self.canvas.pack()

        # Bottom Frame (Scoreboard Table)
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill=tk.BOTH, expand=True, ipadx=10, ipady=10)

        tk.Label(bottom_frame, text="--- LEADERBOARD ---", font=("Consolas", 12, "bold")).pack()

        # Treeview Widget for Score Table
        columns = ("Name", "Score")
        self.tree = ttk.Treeview(bottom_frame, columns=columns, show="headings", height=6)
        self.tree.heading("Name", text="Player Name")
        self.tree.heading("Score", text="Score")
        self.tree.column("Name", anchor=tk.CENTER, width=280)
        self.tree.column("Score", anchor=tk.CENTER, width=280)

        # Scrollbar for Table
        scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Key Bindings
        self.root.bind("<Left>", lambda event: self.change_direction("left"))
        self.root.bind("<Right>", lambda event: self.change_direction("right"))
        self.root.bind("<Up>", lambda event: self.change_direction("up"))
        self.root.bind("<Down>", lambda event: self.change_direction("down"))

        # Load initial scores into the table
        self.load_scores()

    def start_game(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Name Required", "Please enter your name before playing!")
            return

        self.player_name = name
        self.score = 0
        self.direction = "down"
        self.running = True
        self.score_label.config(text=f"Score: {self.score}")
        self.name_entry.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)

        self.canvas.delete(tk.ALL)

        # Initialize Snake Body
        self.snake = []
        for i in range(BODY_PARTS):
            self.snake.append([0, 0])

        for x, y in self.snake:
            self.canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR, tag="snake")

        self.spawn_food()
        self.next_turn()

    def spawn_food(self):
        x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
        y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
        self.food = [x, y]
        self.canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")

    def next_turn(self):
        if not self.running:
            return

        x, y = self.snake[0]

        if self.direction == "up":
            y -= SPACE_SIZE
        elif self.direction == "down":
            y += SPACE_SIZE
        elif self.direction == "left":
            x -= SPACE_SIZE
        elif self.direction == "right":
            x += SPACE_SIZE

        self.snake.insert(0, [x, y])
        square = self.canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR)

        # Check Food Collision
        if x == self.food[0] and y == self.food[1]:
            self.score += 10
            self.score_label.config(text=f"Score: {self.score}")
            self.canvas.delete("food")
            self.spawn_food()
        else:
            del self.snake[-1]
            self.canvas.delete(self.canvas.find_withtag("snake")[-1])

        # Check Collisions
        if self.check_collisions():
            self.game_over()
        else:
            self.root.after(SPEED, self.next_turn)

    def change_direction(self, new_dir):
        opposites = {"left": "right", "right": "left", "up": "down", "down": "up"}
        if new_dir != opposites.get(self.direction):
            self.direction = new_dir

    def check_collisions(self):
        x, y = self.snake[0]

        # Wall collisions
        if x < 0 or x >= GAME_WIDTH or y < 0 or y >= GAME_HEIGHT:
            return True

        # Self collision
        for body_part in self.snake[1:]:
            if x == body_part[0] and y == body_part[1]:
                return True

        return False

    def game_over(self):
        self.running = False
        self.canvas.create_text(
            GAME_WIDTH / 2,
            GAME_HEIGHT / 2,
            font=("Consolas", 30, "bold"),
            text="GAME OVER",
            fill="red",
            tag="gameover",
        )

        # Save score to game.txt
        self.save_score()

        # Re-enable inputs
        self.name_entry.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.NORMAL)

    def save_score(self):
        # Append player name and score to game.txt
        with open(SCORE_FILE, "a") as f:
            f.write(f"{self.player_name},{self.score}\n")

        # Reload table
        self.load_scores()

    def load_scores(self):
        # Clear existing rows in table
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not os.path.exists(SCORE_FILE):
            return

        scores = []
        with open(SCORE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and "," in line:
                    parts = line.rsplit(",", 1)
                    name = parts[0]
                    try:
                        score = int(parts[1])
                        scores.append((name, score))
                    except ValueError:
                        continue

        # Sort by score (highest first)
        scores.sort(key=lambda item: item[1], reverse=True)

        # Insert sorted records into the table widget
        for name, score in scores:
            self.tree.insert("", tk.END, values=(name, score))


if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()
