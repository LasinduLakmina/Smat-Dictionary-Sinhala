import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import requests
from typing import Dict, List, Optional
from googletrans import Translator

class DictionaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Dictionary - සිංහල")
        self.root.configure(bg="#f8f9fa")
        # Configure font for Sinhala text
        self.sinhala_font = ("Iskoola Pota", 12)
        self.root.geometry("800x600")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f8f9fa")
        self.style.configure("TLabel", background="#f8f9fa", font=("Helvetica", 10))
        self.style.configure("TButton", font=("Helvetica", 10), padding=6)
        self.style.configure("Search.TButton", font=("Helvetica", 10, "bold"), padding=6, background="#007bff")
        self.style.configure("TCombobox", padding=4, selectbackground="#007bff")
        self.style.configure("TEntry", padding=6)
        
        # Create main container with padding
        self.main_frame = ttk.Frame(self.root, padding="20 15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Language selection frame with improved spacing
        self.lang_frame = ttk.Frame(self.main_frame)
        self.lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Language mapping
        self.language_map = {
            'auto': 'Detect Language',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'ja': '日本語',
            'ko': '한국어',
            'zh-cn': '中文',
            'si': 'සිංහල'
        }
        
        # Source language
        self.src_lang_var = tk.StringVar(value='auto')
        # Target language
        self.tgt_lang_var = tk.StringVar(value='en')
        self.src_lang_combo = ttk.Combobox(
            self.lang_frame,
            textvariable=self.src_lang_var,
            values=[f"{name} ({code})" for code, name in self.language_map.items()],
            width=25,
            state='readonly'
        )
        self.src_lang_combo.pack(side=tk.LEFT, padx=8)
        
        # Swap button with improved styling
        self.swap_button = ttk.Button(
            self.lang_frame,
            text="⇄",
            command=self.swap_languages,
            width=3,
            style="TButton"
        )
        self.swap_button.pack(side=tk.LEFT, padx=8)
        
        # Target language with improved styling
        self.tgt_lang_combo = ttk.Combobox(
            self.lang_frame,
            textvariable=self.tgt_lang_var,
            values=[f"{name} ({code})" for code, name in self.language_map.items() if code != 'auto'],
            width=25,
            state='readonly'
        )
        self.tgt_lang_combo.pack(side=tk.LEFT, padx=8)
        
        # Search frame with improved spacing
        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Initialize search variable
        self.search_var = tk.StringVar()
        
        # Search entry with improved styling
        self.search_entry = ttk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            font=self.sinhala_font,
            style="TEntry"
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Search button with improved styling
        self.search_button = ttk.Button(
            self.search_frame,
            text="Search",
            command=self.search_word,
            style="Search.TButton"
        )
        self.search_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # Translate button with improved styling
        self.translate_button = ttk.Button(
            self.search_frame,
            text="Translate",
            command=self.translate_text,
            style="Search.TButton"
        )
        self.translate_button.pack(side=tk.LEFT, padx=(0, 8))
        
        # Save button with improved styling
        self.save_button = ttk.Button(
            self.search_frame,
            text="Save Word",
            command=self.save_word,
            style="TButton"
        )
        self.save_button.pack(side=tk.LEFT)
        
        # Results frame with improved styling
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results text with improved styling
        self.results_text = tk.Text(
            self.results_frame,
            wrap=tk.WORD,
            font=self.sinhala_font,
            padx=15,
            pady=15,
            bg="#ffffff",
            relief="flat",
            borderwidth=1
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for better formatting
        self.results_text.tag_configure("title", font=("Helvetica", 12, "bold"), foreground="#007bff")
        self.results_text.tag_configure("heading", font=("Helvetica", 11, "bold"), foreground="#212529")
        self.results_text.tag_configure("content", font=("Helvetica", 10), foreground="#495057")
        
        # Initialize database
        self.init_database()
        
        # API configuration
        self.api_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"
        
        # Initialize translator
        self.translator = Translator()
        
        # Configure hover effects for buttons
        self.style.map('TButton',
            foreground=[('active', '#007bff')],
            background=[('active', '#e9ecef')]
        )
        self.style.map('Search.TButton',
            foreground=[('active', '#ffffff')],
            background=[('active', '#0056b3')]
        )
        
        # Configure hover effects for comboboxes
        self.style.map('TCombobox',
            fieldbackground=[('readonly', '#ffffff'), ('readonly', 'focus', '#e9ecef')],
            selectbackground=[('readonly', '#007bff')],
            selectforeground=[('readonly', '#ffffff')]
        )
        
        # Add search suggestions list
        self.suggestions_listbox = tk.Listbox(
            self.search_frame,
            font=self.sinhala_font,
            height=5,
            selectmode=tk.SINGLE,
            activestyle='none',
            relief='flat',
            bg='#ffffff',
            selectbackground='#007bff',
            selectforeground='#ffffff'
        )
        
        # Bind events for search suggestions
        self.search_entry.bind('<KeyRelease>', self.update_suggestions)
        self.suggestions_listbox.bind('<<ListboxSelect>>', self.use_suggestion)
        
        # Add scrollbar for suggestions
        self.suggestions_scrollbar = ttk.Scrollbar(
            self.search_frame,
            orient=tk.VERTICAL,
            command=self.suggestions_listbox.yview
        )
        self.suggestions_listbox.configure(yscrollcommand=self.suggestions_scrollbar.set)
    
    def init_database(self):
        """Initialize SQLite database for saved words"""
        self.conn = sqlite3.connect('dictionary.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_words (
                word TEXT PRIMARY KEY,
                definition TEXT,
                synonyms TEXT,
                antonyms TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def search_word(self):
        """Search for a word in both API and local database"""
        word = self.search_var.get().strip().lower()
        if not word:
            messagebox.showwarning("Warning", "Please enter a word to search")
            return
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Check local database first
        self.cursor.execute("SELECT * FROM saved_words WHERE word=?", (word,))
        local_result = self.cursor.fetchone()
        
        if local_result:
            self.display_local_result(local_result)
        
        # Search online API
        try:
            response = requests.get(f"{self.api_url}{word}")
            if response.status_code == 200:
                self.display_api_result(response.json())
            else:
                if not local_result:
                    self.results_text.insert(tk.END, f"No definition found for '{word}'")
        except requests.RequestException as e:
            if not local_result:
                self.results_text.insert(tk.END, f"Error searching for '{word}': {str(e)}")
    
    def display_local_result(self, result):
        """Display result from local database"""
        word, definition, synonyms, antonyms, _ = result
        self.results_text.insert(tk.END, "📚 From Your Dictionary:\n", "title")
        self.results_text.insert(tk.END, f"Word: {word}\n")
        self.results_text.insert(tk.END, f"Definition: {definition}\n")
        if synonyms:
            self.results_text.insert(tk.END, f"Synonyms: {synonyms}\n")
        if antonyms:
            self.results_text.insert(tk.END, f"Antonyms: {antonyms}\n")
        self.results_text.insert(tk.END, "\n")
    
    def display_api_result(self, data):
        """Display result from API"""
        self.results_text.insert(tk.END, "🌐 Online Dictionary:\n", "title")
        for entry in data:
            for meaning in entry.get('meanings', []):
                self.results_text.insert(tk.END, f"\nPart of Speech: {meaning.get('partOfSpeech', '')}\n")
                for definition in meaning.get('definitions', []):
                    self.results_text.insert(tk.END, f"\nDefinition: {definition.get('definition', '')}\n")
                    if 'example' in definition:
                        self.results_text.insert(tk.END, f"Example: {definition['example']}\n")
                
                if meaning.get('synonyms'):
                    self.results_text.insert(tk.END, f"Synonyms: {', '.join(meaning['synonyms'][:5])}\n")
                if meaning.get('antonyms'):
                    self.results_text.insert(tk.END, f"Antonyms: {', '.join(meaning['antonyms'][:5])}\n")
    
    def swap_languages(self):
        """Swap source and target languages"""
        if self.src_lang_var.get() != 'Detect Language (auto)':
            src = self.src_lang_var.get()
            tgt = self.tgt_lang_var.get()
            self.src_lang_var.set(tgt)
            self.tgt_lang_var.set(src)

    def get_language_code(self, display_value):
        """Extract language code from display value"""
        code = display_value.split('(')[-1].rstrip(')')
        return code

    def translate_text(self):
        """Translate the input text"""
        text = self.search_var.get().strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to translate")
            return
        
        try:
            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            
            # Get language codes from display values
            src_code = self.get_language_code(self.src_lang_var.get())
            tgt_code = self.get_language_code(self.tgt_lang_var.get())
            
            # Perform translation
            translation = self.translator.translate(
                text,
                src=src_code,
                dest=tgt_code
            )
            
            # Display results
            self.results_text.insert(tk.END, "🌐 Translation:\n", "title")
            self.results_text.insert(tk.END, f"From: {self.language_map[translation.src]}\n")
            self.results_text.insert(tk.END, f"To: {self.language_map[translation.dest]}\n\n")
            self.results_text.insert(tk.END, f"Original: {text}\n")
            self.results_text.insert(tk.END, f"Translated: {translation.text}\n")
            
            if translation.pronunciation:
                self.results_text.insert(tk.END, f"Pronunciation: {translation.pronunciation}\n")
                
        except Exception as e:
            messagebox.showerror("Error", f"Translation error: {str(e)}")
    
    def save_word(self):
        """Save word to local database"""
        word = self.search_var.get().strip().lower()
        if not word:
            messagebox.showwarning("Warning", "Please enter a word to save")
            return
        
        try:
            response = requests.get(f"{self.api_url}{word}")
            if response.status_code == 200:
                data = response.json()
                definition = data[0]['meanings'][0]['definitions'][0]['definition']
                synonyms = ', '.join(data[0]['meanings'][0].get('synonyms', [])[:5])
                antonyms = ', '.join(data[0]['meanings'][0].get('antonyms', [])[:5])
                
                self.cursor.execute(
                    "INSERT OR REPLACE INTO saved_words (word, definition, synonyms, antonyms) VALUES (?, ?, ?, ?)",
                    (word, definition, synonyms, antonyms)
                )
                self.conn.commit()
                messagebox.showinfo("Success", f"Word '{word}' has been saved to your dictionary")
            else:
                messagebox.showerror("Error", f"Could not find the word '{word}'")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error saving word: {str(e)}")

    def update_suggestions(self, event=None):
        """Update search suggestions based on current input"""
        current_text = self.search_entry.get().strip().lower()
        if len(current_text) < 2:
            self.suggestions_listbox.place_forget()
            self.suggestions_scrollbar.place_forget()
            return
        
        # Get suggestions from saved words
        self.cursor.execute(
            "SELECT word FROM saved_words WHERE word LIKE ? LIMIT 5",
            (f"{current_text}%",)
        )
        suggestions = [row[0] for row in self.cursor.fetchall()]
        
        if suggestions:
            self.suggestions_listbox.delete(0, tk.END)
            for suggestion in suggestions:
                self.suggestions_listbox.insert(tk.END, suggestion)
            
            # Position suggestions below search entry
            entry_x = self.search_entry.winfo_x()
            entry_y = self.search_entry.winfo_y()
            entry_height = self.search_entry.winfo_height()
            
            self.suggestions_listbox.place(
                x=entry_x,
                y=entry_y + entry_height,
                width=self.search_entry.winfo_width()
            )
            self.suggestions_scrollbar.place(
                x=entry_x + self.search_entry.winfo_width(),
                y=entry_y + entry_height,
                height=self.suggestions_listbox.winfo_height()
            )
        else:
            self.suggestions_listbox.place_forget()
            self.suggestions_scrollbar.place_forget()
    
    def use_suggestion(self, event=None):
        """Use the selected suggestion"""
        selection = self.suggestions_listbox.curselection()
        if selection:
            suggested_word = self.suggestions_listbox.get(selection[0])
            self.search_var.set(suggested_word)
            self.suggestions_listbox.place_forget()
            self.suggestions_scrollbar.place_forget()
            self.search_word()

if __name__ == "__main__":
    root = tk.Tk()
    app = DictionaryApp(root)
    root.mainloop()