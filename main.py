import tkinter as tk
from tkinter import messagebox
import requests
import json
import os

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("400x500")
        
        self.fav_file = "favorites.json"
        self.favorites = self.load_favorites()

        # UI элементы
        tk.Label(root, text="Введите логин GitHub:").pack(pady=5)
        self.search_entry = tk.Entry(root, width=30)
        self.search_entry.pack(pady=5)

        tk.Button(root, text="Найти", command=self.search_user).pack(pady=5)

        self.result_frame = tk.Frame(root)
        self.result_frame.pack(pady=20)

        self.user_label = tk.Label(self.result_frame, text="", font=("Arial", 12, "bold"))
        self.user_label.pack()

        self.add_fav_btn = tk.Button(self.result_frame, text="В избранное", 
                                     state=tk.DISABLED, command=self.add_to_favorites)
        self.add_fav_btn.pack(pady=5)

        tk.Label(root, text="Избранные:").pack(pady=5)
        self.fav_listbox = tk.Listbox(root, width=40, height=10)
        self.fav_listbox.pack(pady=5)
        self.update_fav_listbox()

        self.current_user = None

    def search_user(self):
        username = self.search_entry.get().strip()
        if not username:
            messagebox.showwarning("Внимание", "Поле поиска не должно быть пустым!")
            return

        response = requests.get(f"https://api.github.com/users/{username}")
        
        if response.status_code == 200:
            data = response.json()
            self.current_user = data['login']
            self.user_label.config(text=f"Найдено: {data['login']} ({data.get('name', 'Нет имени')})")
            self.add_fav_btn.config(state=tk.NORMAL)
        else:
            self.user_label.config(text="Пользователь не найден")
            self.add_fav_btn.config(state=tk.DISABLED)

    def add_to_favorites(self):
        if self.current_user and self.current_user not in self.favorites:
            self.favorites.append(self.current_user)
            self.save_favorites()
            self.update_fav_listbox()
            messagebox.showinfo("Успех", f"{self.current_user} добавлен в избранное")

    def load_favorites(self):
        if os.path.exists(self.fav_file):
            with open(self.fav_file, "r") as f:
                return json.load(f)
        return []

    def save_favorites(self):
        with open(self.fav_file, "w") as f:
            json.dump(self.favorites, f)

    def update_fav_listbox(self):
        self.fav_listbox.delete(0, tk.END)
        for user in self.favorites:
            self.fav_listbox.insert(tk.END, user)

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()