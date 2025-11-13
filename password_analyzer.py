import tkinter as tk
from tkinter import messagebox, filedialog
from zxcvbn import zxcvbn
import itertools
import re
import argparse
import sys

# --- Leetspeak mapping for substitutions ---
LEET_MAP = {
    'e': '3',
    'a': '4',
    'i': '1',
    'o': '0',
    's': '5',
    't': '7'
}

# --- Years and Numbers to Append ---
YEARS = ['2024', '2025']
NUMBERS = ['123', '321', '007', '86']

# --- Helper Functions ---

def leetspeak_variants(word):
    """
    Generate leetspeak variants for a given word.
    Example: 'name' -> ['name', 'nam3', 'n4me', 'n4m3']
    """
    variants = set([word])
    chars = list(word.lower())
    indexes = [i for i, c in enumerate(chars) if c in LEET_MAP]
    # Generate all combinations of substitutions
    for l in range(1, len(indexes)+1):
        for positions in itertools.combinations(indexes, l):
            w = chars[:]
            for idx in positions:
                w[idx] = LEET_MAP[w[idx]]
            variants.add(''.join(w))
    return list(variants)

def generate_wordlist(inputs):
    """
    Generate wordlist from user inputs and leetspeak & append rules.
    """
    raw_words = [str(v).strip() for k, v in inputs.items() if v]
    # Remove duplicates and empty values
    raw_words = list({w for w in raw_words if w})

    wordlist = set()
    for word in raw_words:
        variants = leetspeak_variants(word)
        for v in variants:
            wordlist.add(v)
            # Add numbers and years
            for num in NUMBERS + YEARS:
                wordlist.add(v + num)
                wordlist.add(num + v)

    # Also combine words (e.g., name + birth_year)
    for w1, w2 in itertools.combinations(raw_words, 2):
        combined = [w1 + w2, w2 + w1]
        for base in combined:
            wordlist.add(base)
            for v in leetspeak_variants(base):
                wordlist.add(v)
            for num in NUMBERS + YEARS:
                wordlist.add(base + num)
                wordlist.add(num + base)

    return sorted(wordlist)

def analyze_password_strength(password):
    """
    Evaluate password strength using zxcvbn.
    """
    results = zxcvbn(password)
    score = results['score']
    crack_time = results['crack_times_display']['offline_fast_hashing_1e10_per_second']
    feedback = results['feedback']
    suggestions = feedback.get('suggestions', [])
    warning = feedback.get('warning', '')
    return score, crack_time, warning, suggestions

def save_wordlist(filename, wordlist):
    """
    Save generated wordlist to a file.
    """
    with open(filename, 'w') as f:
        for word in wordlist:
            f.write(word + '\n')

# --- Tkinter GUI ---

class PasswordAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Strength Analyzer & Wordlist Generator")

        # --- Input fields ---
        self.entries = {}

        details = [
            ("Full Name", "name"),
            ("Birth Year", "birth_year"),
            ("Pet Name", "pet_name"),
            ("Favorite Word", "favorite_word"),
            ("Other Detail", "other_detail"),
            ("Password", "password")
        ]
        row = 0
        for label, key in details:
            tk.Label(root, text=label).grid(row=row, column=0, sticky="e", pady=2)
            entry = tk.Entry(root, show="*" if key=="password" else "")
            entry.grid(row=row, column=1, pady=2, padx=5, sticky="ew")
            self.entries[key] = entry
            row += 1

        # --- Buttons ---
        tk.Button(root, text="Check Strength", command=self.check_strength).grid(row=row, column=0, pady=6)
        tk.Button(root, text="Generate Wordlist", command=self.generate_wordlist).grid(row=row, column=1, pady=6)
        row += 1

        # --- Feedback area ---
        self.feedback_text = tk.Text(root, height=8, width=60, state="disabled")
        self.feedback_text.grid(row=row, column=0, columnspan=2, padx=5, pady=5)

        # --- Configure column ---
        root.columnconfigure(1, weight=1)

    def check_strength(self):
        """
        Event handler for password strength check.
        """
        password = self.entries['password'].get()
        if not password:
            messagebox.showerror("Input Error", "Please enter a password.")
            return

        score, crack_time, warning, suggestions = analyze_password_strength(password)
        feedback_str = f"Password Score (0-4): {score}\n"
        feedback_str += f"Estimated Time to Crack: {crack_time}\n"
        if warning:
            feedback_str += f"Warning: {warning}\n"
        if suggestions:
            feedback_str += "Suggestions:\n" + "\n".join("  - " + s for s in suggestions)

        self.feedback_text.configure(state="normal")
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(tk.END, feedback_str)
        self.feedback_text.configure(state="disabled")

    def generate_wordlist(self):
        """
        Event handler for wordlist generation.
        """
        details = {k: v.get() for k, v in self.entries.items() if k != 'password'}
        if not any(details.values()):
            messagebox.showerror("Input Error", "Please provide at least one detail for wordlist generation.")
            return

        wordlist = generate_wordlist(details)
        save_wordlist('custom_wordlist.txt', wordlist)
        messagebox.showinfo("Success", f"Wordlist generated and saved as 'custom_wordlist.txt' ({len(wordlist)} words)!")

# --- CLI Mode ---
def run_cli_mode(args):
    """
    Run as command-line interface using argparse.
    """
    # Get user details
    print("=== Password Strength Analyzer & Wordlist Generator ===")
    name = input("Enter your Full Name: ")
    birth_year = input("Enter your Birth Year: ")
    pet_name = input("Enter your Pet Name: ")
    favorite_word = input("Enter your Favorite Word: ")
    other_detail = input("Enter other detail (or leave blank): ")
    password = input("Enter your Password for strength analysis: ")

    # Analyze password strength
    score, crack_time, warning, suggestions = analyze_password_strength(password)
    print(f"\nPassword Score (0-4): {score}")
    print(f"Estimated Time to Crack: {crack_time}")
    if warning:
        print(f"Warning: {warning}")
    if suggestions:
        print("Suggestions:")
        for s in suggestions:
            print(f"  - {s}")

    # Generate wordlist
    details = {
        'name': name,
        'birth_year': birth_year,
        'pet_name': pet_name,
        'favorite_word': favorite_word,
        'other_detail': other_detail
    }
    wordlist = generate_wordlist(details)
    save_wordlist('custom_wordlist.txt', wordlist)
    print(f"\nWordlist generated and saved as 'custom_wordlist.txt' ({len(wordlist)} words)!")

# --- Main entry point ---

def main():
    # Parse CLI arguments to select mode
    parser = argparse.ArgumentParser(description="Password Strength Analyzer with Custom Wordlist Generator")
    parser.add_argument('--cli', action='store_true', help='Run the app in CLI mode (terminal)')
    args = parser.parse_args()

    if args.cli:
        run_cli_mode(args)
    else:
        # Start Tkinter GUI
        root = tk.Tk()
        app = PasswordAnalyzerGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
