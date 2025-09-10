"""
Graphical user interface for Instagram Downloader
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from .downloader import InstagramDownloader
from .profile import ProfileDownloader

class InstagramDownloaderGUI:
    """GUI class for Instagram Downloader"""
    
    def __init__(self):
        """Initialize the GUI window and components"""
        self.window = tk.Tk()
        self.window.title("Instagram Downloader")
        self.window.geometry("600x400")
        
        # Variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.download_path_var = tk.StringVar(value="downloads")
        
        self.downloader: Optional[InstagramDownloader] = None
        self.profile_downloader: Optional[ProfileDownloader] = None
        
        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        """Create GUI widgets"""
        # Login frame
        self.login_frame = ttk.LabelFrame(self.window, text="Login")
        
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.password_var, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.login_button = ttk.Button(self.login_frame, text="Login", command=self._login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Download frame
        self.download_frame = ttk.LabelFrame(self.window, text="Download")
        
        ttk.Label(self.download_frame, text="URL:").grid(row=0, column=0, padx=5, pady=5)
        self.url_entry = ttk.Entry(self.download_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5)
        
        ttk.Label(self.download_frame, text="Save to:").grid(row=1, column=0, padx=5, pady=5)
        self.path_entry = ttk.Entry(self.download_frame, textvariable=self.download_path_var, width=40)
        self.path_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.browse_button = ttk.Button(self.download_frame, text="Browse", command=self._browse_path)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        self.download_post_button = ttk.Button(
            self.download_frame,
            text="Download Post",
            command=self._download_post
        )
        self.download_post_button.grid(row=2, column=0, pady=10)
        
        self.download_profile_button = ttk.Button(
            self.download_frame,
            text="Download Profile",
            command=self._download_profile
        )
        self.download_profile_button.grid(row=2, column=1, pady=10)
        
        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.window, text="Progress")
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            length=200,
            mode="determinate"
        )
        self.progress_bar.pack(pady=5)

    def _create_layout(self):
        """Arrange widgets in the window"""
        self.login_frame.pack(fill="x", padx=10, pady=5)
        self.download_frame.pack(fill="x", padx=10, pady=5)
        self.progress_frame.pack(fill="x", padx=10, pady=5)

    def _browse_path(self):
        """Open directory browser dialog"""
        path = filedialog.askdirectory()
        if path:
            self.download_path_var.set(path)

    def _login(self):
        """Handle login button click"""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        try:
            self.downloader = InstagramDownloader(self.download_path_var.get())
            if self.downloader.login(username, password):
                self.profile_downloader = ProfileDownloader(username, password, self.download_path_var.get())
                messagebox.showinfo("Success", "Login successful!")
            else:
                messagebox.showerror("Error", "Login failed. Please check your credentials.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")

    def _download_post(self):
        """Handle download post button click"""
        if not self.downloader:
            messagebox.showerror("Error", "Please login first")
            return
            
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        try:
            self.progress_var.set("Downloading post...")
            self.progress_bar["value"] = 0
            self.window.update()
            
            files = self.downloader.download_post(url)
            
            self.progress_bar["value"] = 100
            self.progress_var.set(f"Downloaded {len(files)} files")
            messagebox.showinfo("Success", f"Downloaded {len(files)} files")
            
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")
            
        finally:
            self.progress_bar["value"] = 0
            self.progress_var.set("Ready")

    def _download_profile(self):
        """Handle download profile button click"""
        if not self.profile_downloader:
            messagebox.showerror("Error", "Please login first")
            return
            
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a profile URL")
            return
            
        try:
            self.progress_var.set("Downloading profile...")
            self.progress_bar["value"] = 0
            self.window.update()
            
            files = self.profile_downloader.download_profile(url)
            
            self.progress_bar["value"] = 100
            self.progress_var.set(f"Downloaded {len(files)} files")
            messagebox.showinfo("Success", f"Downloaded {len(files)} files from profile")
            
        except Exception as e:
            messagebox.showerror("Error", f"Profile download failed: {str(e)}")
            
        finally:
            self.progress_bar["value"] = 0
            self.progress_var.set("Ready")

    def run(self):
        """Start the GUI application"""
        self.window.mainloop()

    def close(self):
        """Close the application and clean up"""
        if self.downloader:
            self.downloader.close()
        if self.profile_downloader:
            self.profile_downloader.close()
        self.window.destroy()
