import tkinter as tk
from tkinter import messagebox, ttk
import requests
import json
import os
import re
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("600x700")
        
        self.fav_file = "favorites.json"
        self.favorites = self.load_favorites()
        self.current_search_results = []

        # UI элементы
        tk.Label(root, text="Введите логин GitHub:", font=("Arial", 10)).pack(pady=5)
        
        frame_input = tk.Frame(root)
        frame_input.pack(pady=5)
        
        self.search_entry = tk.Entry(frame_input, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda event: self.search_users())
        
        tk.Button(frame_input, text="Найти", command=self.search_users, bg="#4CAF50", fg="white").pack(side=tk.LEFT)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(root, mode='indeterminate', length=400)
        
        # Результаты поиска
        tk.Label(root, text="Результаты поиска:", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Фрейм для списка результатов с прокруткой
        frame_results = tk.Frame(root)
        frame_results.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(frame_results)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox = tk.Listbox(frame_results, yscrollcommand=scrollbar.set, 
                                          height=10, font=("Arial", 10))
        self.results_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_listbox.yview)
        
        # Информация о выбранном пользователе
        self.info_frame = tk.Frame(root, relief=tk.RIDGE, borderwidth=2)
        self.info_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.user_info_label = tk.Label(self.info_frame, text="", justify=tk.LEFT, font=("Arial", 9))
        self.user_info_label.pack(pady=5, padx=5)
        
        # Кнопки действий
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=5)
        
        self.add_fav_btn = tk.Button(frame_buttons, text="В избранное", 
                                     state=tk.DISABLED, command=self.add_to_favorites,
                                     bg="#2196F3", fg="white", width=15)
        self.add_fav_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_buttons, text="Очистить результаты", command=self.clear_results,
                 bg="#FF9800", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        
        # Избранные
        tk.Label(root, text="Избранные пользователи:", font=("Arial", 10, "bold")).pack(pady=5)
        
        frame_fav = tk.Frame(root)
        frame_fav.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        fav_scrollbar = tk.Scrollbar(frame_fav)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.fav_listbox = tk.Listbox(frame_fav, yscrollcommand=fav_scrollbar.set, 
                                      height=6, font=("Arial", 10))
        self.fav_listbox.pack(fill=tk.BOTH, expand=True)
        fav_scrollbar.config(command=self.fav_listbox.yview)
        
        self.update_fav_listbox()
        
        # Привязка событий
        self.results_listbox.bind('<<ListboxSelect>>', self.on_result_select)
        self.fav_listbox.bind('<Double-Button-1>', self.on_favorite_double_click)

        self.current_selected_user = None

    def validate_username(self, username):
        """Валидация имени пользователя GitHub"""
        if not username:
            return False, "Имя пользователя не может быть пустым"
        
        if len(username) > 39:
            return False, "Имя пользователя не может превышать 39 символов"
        
        # Допустимые символы: буквы, цифры, дефис (не в начале и не в конце)
        pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$'
        if not re.match(pattern, username):
            return False, "Имя пользователя может содержать только буквы, цифры и дефис (не в начале и не в конце)"
        
        return True, ""

    def search_users(self):
        """Поиск пользователей через GitHub Search API"""
        username = self.search_entry.get().strip()
        
        # Валидация
        is_valid, error_msg = self.validate_username(username)
        if not is_valid:
            messagebox.showwarning("Внимание", error_msg)
            return

        # Показываем прогресс
        self.progress.pack(pady=5)
        self.progress.start()
        
        try:
            # Используем Search API для поиска пользователей
            url = f"https://api.github.com/search/users?q={username}&per_page=20"
            
            # Добавляем User-Agent (требование GitHub API)
            headers = {
                'User-Agent': 'GitHub-User-Finder-App/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            self.current_search_results = data.get('items', [])
            
            # Очищаем список результатов
            self.results_listbox.delete(0, tk.END)
            
            if not self.current_search_results:
                self.results_listbox.insert(tk.END, "❌ Пользователи не найдены")
                self.user_info_label.config(text="")
                self.add_fav_btn.config(state=tk.DISABLED)
            else:
                total_count = data.get('total_count', 0)
                self.results_listbox.insert(tk.END, f"📊 Найдено: {total_count} пользователей (показано {len(self.current_search_results)})")
                self.results_listbox.insert(tk.END, "-" * 50)
                
                for user in self.current_search_results:
                    self.results_listbox.insert(tk.END, f"👤 {user['login']}")
                    
            self.user_info_label.config(text="")
            self.add_fav_btn.config(state=tk.DISABLED)
            
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка сети", "Нет подключения к интернету. Проверьте ваше соединение.")
            self.user_info_label.config(text="❌ Ошибка сети")
        except requests.exceptions.Timeout:
            messagebox.showerror("Ошибка", "Превышено время ожидания ответа от сервера.")
            self.user_info_label.config(text="❌ Таймаут соединения")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                messagebox.showerror("Ошибка", "Превышен лимит запросов. Попробуйте позже.")
            elif response.status_code == 422:
                messagebox.showerror("Ошибка", "Некорректный запрос.")
            else:
                messagebox.showerror("Ошибка HTTP", f"Ошибка {response.status_code}: {str(e)}")
            self.user_info_label.config(text=f"❌ Ошибка: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при выполнении запроса: {str(e)}")
            self.user_info_label.config(text="❌ Ошибка запроса")
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка", "Не удалось обработать ответ от сервера.")
            self.user_info_label.config(text="❌ Ошибка парсинга данных")
        finally:
            self.progress.stop()
            self.progress.pack_forget()

    def on_result_select(self, event):
        """Обработчик выбора пользователя из результатов поиска"""
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Пропускаем заголовки и разделители
        if index < 2 or not self.current_search_results:
            return
        
        # Корректируем индекс (первые 2 элемента - заголовки)
        result_index = index - 2
        if result_index >= len(self.current_search_results):
            return
        
        selected_user = self.current_search_results[result_index]
        self.current_selected_user = selected_user['login']
        
        # Загружаем дополнительную информацию о пользователе
        self.load_user_details(selected_user['login'])

    def load_user_details(self, username):
        """Загрузка детальной информации о пользователе"""
        try:
            headers = {
                'User-Agent': 'GitHub-User-Finder-App/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(f"https://api.github.com/users/{username}", 
                                   headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Формируем информацию для отображения
            info_text = f"""
📌 Информация о пользователе:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Логин: {data.get('login', 'Н/Д')}
📛 Имя: {data.get('name', 'Не указано')}
🏢 Компания: {data.get('company', 'Не указана')}
📍 Локация: {data.get('location', 'Не указана')}
📚 Репозитории: {data.get('public_repos', 0)}
👥 Подписчики: {data.get('followers', 0)}
👣 Подписки: {data.get('following', 0)}
📅 Аккаунт создан: {data.get('created_at', 'Н/Д')[:10]}
🔄 Последнее обновление: {data.get('updated_at', 'Н/Д')[:10]}
🔗 Профиль: {data.get('html_url', 'Н/Д')}
            """
            
            self.user_info_label.config(text=info_text, fg="black")
            self.add_fav_btn.config(state=tk.NORMAL)
            
        except requests.exceptions.RequestException as e:
            self.user_info_label.config(text=f"❌ Ошибка загрузки деталей: {str(e)}", fg="red")
            self.add_fav_btn.config(state=tk.DISABLED)

    def add_to_favorites(self):
        """Добавление пользователя в избранное"""
        if not self.current_selected_user:
            messagebox.showwarning("Внимание", "Сначала выберите пользователя из результатов поиска.")
            return
        
        if self.current_selected_user in self.favorites:
            messagebox.showinfo("Информация", f"{self.current_selected_user} уже находится в избранном.")
            return
        
        self.favorites.append(self.current_selected_user)
        self.save_favorites()
        self.update_fav_listbox()
        messagebox.showinfo("Успех", f"✓ {self.current_selected_user} добавлен в избранное!")

    def clear_results(self):
        """Очистка результатов поиска"""
        self.results_listbox.delete(0, tk.END)
        self.current_search_results = []
        self.user_info_label.config(text="")
        self.add_fav_btn.config(state=tk.DISABLED)
        self.current_selected_user = None
        self.search_entry.delete(0, tk.END)

    def on_favorite_double_click(self, event):
        """Обработка двойного клика по избранному пользователю"""
        selection = self.fav_listbox.curselection()
        if selection:
            username = self.fav_listbox.get(selection[0])
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, username)
            self.search_users()

    def load_favorites(self):
        """Загрузка избранного из файла"""
        if os.path.exists(self.fav_file):
            try:
                with open(self.fav_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки избранного: {e}")
                return []
        return []

    def save_favorites(self):
        """Сохранение избранного в файл"""
        try:
            with open(self.fav_file, "w", encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
        except IOError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {e}")

    def update_fav_listbox(self):
        """Обновление списка избранного"""
        self.fav_listbox.delete(0, tk.END)
        for user in self.favorites:
            self.fav_listbox.insert(tk.END, f"⭐ {user}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
