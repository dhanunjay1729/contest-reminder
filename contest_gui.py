import tkinter as tk
from tkinter import ttk, font, messagebox
import requests
from datetime import datetime, timedelta
import pytz
from dateutil import parser
import threading
import webbrowser

# API endpoints
CODEFORCES_API = "https://codeforces.com/api/contest.list"

class ContestReminderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Contest Reminder")
        # Position on right side
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        x_position = screen_width - 1100  # window width + margin
        self.root.geometry(f"700x500+{x_position}+150")
        
        # Set theme colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.today_color = "#ff4444"
        self.this_week_color = "#87CEEB"
        self.next_week_color = "#44ff44"
        self.button_color = "#3a3a3a"
        self.highlight_color = "#ffd700"  # Gold for next contest
        
        # Configure root
        self.root.configure(bg=self.bg_color)
        
        # Contest data
        self.contests = []
        
        # Create GUI elements
        self.setup_gui()
        
        # Start auto-refresh
        self.refresh_contests()
        self.auto_refresh()
    
    def setup_gui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = tk.Label(
            title_frame,
            text="📅 Contest Reminder",
            font=("Arial", 18, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title_label.pack(side="left")
        
        # Refresh button
        self.refresh_btn = tk.Button(
            title_frame,
            text="🔄",
            command=self.refresh_contests,
            bg=self.button_color,
            fg=self.fg_color,
            font=("Arial", 10),
            relief="flat",
            padx=5,
            cursor="hand2"
        )
        self.refresh_btn.pack(side="right")
        
        # Next Contest Frame (Smaller)
        self.next_contest_frame = tk.Frame(self.root, bg="#2a2a2a", relief="ridge", bd=1)
        self.next_contest_frame.pack(fill="x", padx=10, pady=3)
        
        self.next_contest_label = tk.Label(
            self.next_contest_frame,
            text="⭐ Loading...",
            font=("Arial", 11, "bold"),
            bg="#2a2a2a",
            fg=self.highlight_color,
            pady=5
        )
        self.next_contest_label.pack()
        
        # Legend Frame
        legend_frame = tk.Frame(self.root, bg=self.bg_color)
        legend_frame.pack(fill="x", padx=10, pady=3)
        
        tk.Label(legend_frame, text="Legend: ", font=("Arial", 9), 
                bg=self.bg_color, fg=self.fg_color).pack(side="left")
        tk.Label(legend_frame, text="● Today", font=("Arial", 9), 
                bg=self.bg_color, fg=self.today_color).pack(side="left", padx=5)
        tk.Label(legend_frame, text="● This Week", font=("Arial", 9), 
                bg=self.bg_color, fg=self.this_week_color).pack(side="left", padx=5)
        tk.Label(legend_frame, text="● Next Week", font=("Arial", 9), 
                bg=self.bg_color, fg=self.next_week_color).pack(side="left", padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Loading...",
            font=("Arial", 8),
            bg=self.bg_color,
            fg="#aaaaaa"
        )
        self.status_label.pack(anchor="e", padx=10)
        
        # Main content area with scrollbar
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Fix scrolling for Linux/trackpad
        # Bind multiple events for better compatibility
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        
        # For touchpad gestures
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        
        # Linux specific bindings
        self.root.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        self.root.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))
    
    def _on_mousewheel(self, event):
        # For Windows/Mac
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_shift_mousewheel(self, event):
        # For horizontal scroll if needed
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def fetch_contests(self):
        """Fetch all contests from different platforms"""
        all_contests = []
        
        # Fetch Codeforces
        try:
            response = requests.get(CODEFORCES_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                for contest in data['result']:
                    if contest['phase'] == 'BEFORE':
                        all_contests.append({
                            'name': contest['name'],
                            'platform': 'CodeForces',
                            'start_time': datetime.fromtimestamp(contest['startTimeSeconds'], tz=pytz.UTC),
                            'duration_seconds': contest['durationSeconds'],
                            'url': f"https://codeforces.com/contests/{contest['id']}"
                        })
        except Exception as e:
            print(f"Error fetching Codeforces: {e}")
        
        # Generate CodeChef contests (Every Wednesday at 8:00 PM IST)
        local_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(local_tz)
        
        days_until_wednesday = (2 - current_time.weekday()) % 7
        if days_until_wednesday == 0 and current_time.hour >= 20:
            days_until_wednesday = 7
        
        for week in range(3):
            next_wednesday = current_time + timedelta(days=days_until_wednesday + (week * 7))
            next_wednesday = next_wednesday.replace(hour=20, minute=0, second=0, microsecond=0)
            
            if (next_wednesday - current_time).days <= 14:
                all_contests.append({
                    'name': f'CodeChef Starters {140 + week}',
                    'platform': 'CodeChef',
                    'start_time': next_wednesday.astimezone(pytz.UTC),
                    'duration_seconds': 10800,
                    'url': 'https://www.codechef.com/contests'
                })
        
        # Generate LeetCode contests
        # Weekly - Every Sunday at 8:00 AM IST
        days_until_sunday = (6 - current_time.weekday()) % 7
        if days_until_sunday == 0 and current_time.hour >= 8:
            days_until_sunday = 7
        
        for week in range(3):
            next_weekly = current_time + timedelta(days=days_until_sunday + (week * 7))
            next_weekly = next_weekly.replace(hour=8, minute=0, second=0, microsecond=0)
            
            if (next_weekly - current_time).days <= 14:
                all_contests.append({
                    'name': f'LeetCode Weekly {450 + week}',
                    'platform': 'LeetCode',
                    'start_time': next_weekly.astimezone(pytz.UTC),
                    'duration_seconds': 5400,
                    'url': 'https://leetcode.com/contest/'
                })
        
        # Biweekly - Starting June 7th
        next_biweekly = local_tz.localize(datetime(2025, 6, 7, 20, 0, 0))
        
        for i in range(2):
            contest_date = next_biweekly + timedelta(days=14 * i)
            if contest_date > current_time and (contest_date - current_time).days <= 14:
                all_contests.append({
                    'name': f'LeetCode Biweekly {131 + i}',
                    'platform': 'LeetCode',
                    'start_time': contest_date.astimezone(pytz.UTC),
                    'duration_seconds': 5400,
                    'url': 'https://leetcode.com/contest/'
                })
        
        return all_contests
    
    def get_contest_color(self, contest_date, current_date):
        """Get color based on contest date"""
        days_diff = (contest_date.date() - current_date.date()).days
        
        if days_diff == 0:
            return self.today_color
        elif days_diff <= 7:
            return self.this_week_color
        elif days_diff <= 14:
            return self.next_week_color
        else:
            return self.fg_color
    
    def create_contest_widget(self, parent, contest, color):
        """Create a widget for a single contest"""
        frame = tk.Frame(parent, bg="#2a2a2a", relief="ridge", bd=1)
        frame.pack(fill="x", pady=2)
        
        # Main content
        main_frame = tk.Frame(frame, bg="#2a2a2a")
        main_frame.pack(fill="x", padx=8, pady=4)
        
        # Contest name with platform
        name_text = f"{contest['name']} [{contest['platform']}]"
        name_label = tk.Label(
            main_frame,
            text=name_text,
            font=("Arial", 10, "bold"),
            bg="#2a2a2a",
            fg=color,
            anchor="w"
        )
        name_label.pack(fill="x")
        
        # Time info
        local_tz = pytz.timezone('Asia/Kolkata')
        start_local = contest['start_time'].astimezone(local_tz)
        current_time = datetime.now(local_tz)
        time_diff = start_local - current_time
        
        time_text = start_local.strftime('%a, %d %b at %H:%M')
        if time_diff.days == 0:
            time_text += f" (In {time_diff.seconds//3600}h {(time_diff.seconds%3600)//60}m)"
        else:
            time_text += f" (In {time_diff.days} days)"
        
        # Duration
        duration_seconds = contest['duration_seconds']
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        duration_text = f"{hours}h {minutes}m"
        
        info_label = tk.Label(
            main_frame,
            text=f"🕐 {time_text} | ⏱️ {duration_text}",
            font=("Arial", 9),
            bg="#2a2a2a",
            fg="#aaaaaa",
            anchor="w"
        )
        info_label.pack(fill="x")
        
        # Make frame clickable
        def open_url(event):
            webbrowser.open(contest['url'])
        
        frame.bind("<Button-1>", open_url)
        for child in frame.winfo_children():
            child.bind("<Button-1>", open_url)
            for subchild in child.winfo_children():
                subchild.bind("<Button-1>", open_url)
        
        # Change cursor on hover
        frame.bind("<Enter>", lambda e: frame.configure(bg="#3a3a3a"))
        frame.bind("<Leave>", lambda e: frame.configure(bg="#2a2a2a"))
    
    def update_next_contest_display(self):
        """Update the next contest display at the top"""
        if not self.contests:
            self.next_contest_label.config(text="⭐ No upcoming contests")
            return
        
        local_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(local_tz)
        
        # Find the next contest
        valid_contests = []
        for contest in self.contests:
            start_local = contest['start_time'].astimezone(local_tz)
            if start_local > current_time and (start_local - current_time).days <= 14:
                valid_contests.append(contest)
        
        if not valid_contests:
            self.next_contest_label.config(text="⭐ No upcoming contests")
            return
        
        # Sort by time only
        valid_contests.sort(key=lambda x: x['start_time'])
        next_contest = valid_contests[0]
        
        start_local = next_contest['start_time'].astimezone(local_tz)
        time_diff = start_local - current_time
        
        if time_diff.days == 0:
            time_text = f"{time_diff.seconds//3600}h {(time_diff.seconds%3600)//60}m"
        else:
            time_text = f"{time_diff.days}d {time_diff.seconds//3600}h"
        
        self.next_contest_label.config(
            text=f"⭐ Next: {next_contest['name']} [{next_contest['platform']}] in {time_text}"
        )
    
    def display_contests(self):
        """Display all contests sorted by time"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.contests:
            tk.Label(
                self.scrollable_frame,
                text="No contests found",
                font=("Arial", 10),
                bg=self.bg_color,
                fg=self.fg_color
            ).pack(pady=20)
            return
        
        # Sort contests by time only
        self.contests.sort(key=lambda x: x['start_time'])
        
        local_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(local_tz)
        
        for contest in self.contests:
            start_local = contest['start_time'].astimezone(local_tz)
            
            # Only show contests within 2 weeks
            if (start_local - current_time).days > 14:
                continue
            
            # Create contest widget
            color = self.get_contest_color(start_local, current_time)
            self.create_contest_widget(self.scrollable_frame, contest, color)
    
    def refresh_contests(self):
        """Refresh contest data in a separate thread"""
        self.status_label.config(text="Refreshing...")
        self.refresh_btn.config(state="disabled")
        
        def fetch_and_update():
            try:
                self.contests = self.fetch_contests()
                self.root.after(0, self.update_display)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch contests: {e}"))
        
        thread = threading.Thread(target=fetch_and_update)
        thread.daemon = True
        thread.start()
    
    def update_display(self):
        """Update the display after fetching contests"""
        self.update_next_contest_display()
        self.display_contests()
        self.status_label.config(text=f"Updated: {datetime.now().strftime('%H:%M')}")
        self.refresh_btn.config(state="normal")
    
    def auto_refresh(self):
        """Auto-refresh every 30 minutes"""
        self.refresh_contests()
        self.root.after(1800000, self.auto_refresh)  # 30 minutes

def main():
    root = tk.Tk()
    app = ContestReminderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
