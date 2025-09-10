import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import threading
import instaloader
import re
from typing import Optional, List
from datetime import datetime
import requests
import sys
import io
from PIL import Image, ImageTk
import queue
import time
from random import uniform
from profile_downloader_v2 import InstagramProfileDownloader  # Import our new profile downloader

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.update_me()

    def write(self, string):
        self.queue.put(string)

    def flush(self):
        pass

    def update_me(self):
        while True:
            try:
                while True:
                    string = self.queue.get_nowait()
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert('end', string)
                    self.text_widget.see('end')
                    self.text_widget.configure(state='disabled')
            except queue.Empty:
                break
        self.text_widget.after(100, self.update_me)

class InstagramDownloader:
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = Path(download_dir)
        self.quality = "high"
        self.loader = None
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.is_logged_in = False
        self.last_password = None  # Store password for session refresh
        self._username = None  # Store username for profile downloader
        
    def login(self, username: str, password: str) -> bool:
        """Login to Instagram account"""
        if not self.loader:
            self.initialize_loader()
            
        try:
            print("Attempting to log in to Instagram...")
            self.loader.login(username, password)
            self.is_logged_in = True
            self.last_password = password  # Store password for session refresh
            self._username = username  # Store username for profile downloader
            print("Successfully logged in to Instagram")
            return True
        except Exception as e:
            print(f"Failed to login: {str(e)}")
            self.is_logged_in = False
            self.last_password = None
            self._username = None
            return False
    def initialize_loader(self):
        """Initialize the Instaloader instance with optimized settings"""
        self.loader = instaloader.Instaloader(
            dirname_pattern="{target}",
            filename_pattern="{date_utc}_UTC_{shortcode}",
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
            request_timeout=60.0,
            quiet=False
        )
        # Configure session to handle rate limits
        self.loader.context._session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        self.loader.context.max_connection_attempts = 3
        self.loader.context.request_timeout = 60.0
        self.loader.context.query_delay = lambda: uniform(5.0, 15.0)  # Random delay between requests

    def wait_with_backoff(self, attempt: int):
        """Implement exponential backoff waiting"""
        wait_time = min(300, 30 * (2 ** attempt))  # Max 5 minutes
        jitter = uniform(-5, 5)
        actual_wait = wait_time + jitter
        print(f"\nRate limit hit. Waiting {actual_wait:.1f} seconds before retrying...")
        time.sleep(actual_wait)

    def download_post(self, url: str) -> List[Path]:
        """Download a single post."""
        try:
            shortcode = self._extract_shortcode_from_url(url)
            if not shortcode:
                raise ValueError("Invalid Instagram URL")

            print(f"\nFetching post with shortcode: {shortcode}")
            attempt = 0
            max_attempts = 3
            
            while attempt < max_attempts:
                try:
                    post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                    break
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(f"Error fetching post: {e}")
                    self.wait_with_backoff(attempt)
            
            return self._download_post(post)
            
        except Exception as e:
            print(f"Error downloading post: {str(e)}")
            raise

    def _get_profile_post_urls(self, profile_url: str) -> List[str]:
        """Get all post URLs from a profile using a web request."""
        username = self._extract_username_from_url(profile_url)
        if not username:
            raise ValueError("Invalid profile URL")
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
        }

        if self.is_logged_in:
            headers['Cookie'] = self.loader.context._session.cookies.get_dict()

        urls = []
        try:
            response = requests.get(f'https://www.instagram.com/{username}/', headers=headers)
            response.raise_for_status()
            
            # Extract post shortcodes from the response
            matches = re.findall(r'"shortcode":"([^"]+)"', response.text)
            if matches:
                urls = [f'https://www.instagram.com/p/{shortcode}/' for shortcode in set(matches)]
                
        except Exception as e:
            print(f"Error fetching profile page: {e}")
            raise

        return urls

    def download_profile(self, profile_url: str) -> List[Path]:
        """Download all posts from a profile."""
        try:
            username = self._extract_username_from_url(profile_url)
            if not username:
                raise ValueError("Invalid profile URL")

            print(f"\nFetching profile: {username}")
            
            # Create profile downloader instance only when needed
            profile_downloader = InstagramProfileDownloader(str(self.download_dir))
            
            # Login using stored credentials
            if not profile_downloader.login(self._username, self.last_password):
                raise Exception("Failed to authenticate profile downloader")
            
            print("Using improved profile downloader...")
            profile_downloader.download_profile(username)
            
            # Return the path to the downloads directory for this user
            return [self.download_dir / username]
            
        except Exception as e:
            print(f"Error downloading profile: {e}")
            return []

            if profile.mediacount == 0:
                print("\nThis profile has no posts to download.")
                return []

            # Get posts with careful rate limiting
            downloaded_files = []
            total_posts = profile.mediacount
            posts_downloaded = 0
            print(f"\nStarting download of {total_posts} posts...")
            
            def get_post_iterator():
                """Get a fresh post iterator with a new session"""
                self.loader.context._session = requests.Session()
                if self.is_logged_in:
                    username = self.loader.context.username
                    if username:
                        self.loader.login(username, self.last_password)
                        time.sleep(5)  # Wait after login
                return profile.get_posts()
            
            try:
                retry_count = 0
                max_total_retries = 3
                post_iterator = get_post_iterator()
                
                while retry_count < max_total_retries:
                    try:
                        for post in post_iterator:
                            posts_downloaded += 1
                            print(f"\nDownloading post {posts_downloaded}/{total_posts} ({posts_downloaded/total_posts*100:.1f}%)...")
                            
                            # Try to download the post
                            max_retries = 3
                            for retry in range(max_retries):
                                try:
                                    files = self._download_post(post)
                                    downloaded_files.extend(files)
                                    
                                    # Success! Add a longer delay
                                    delay = uniform(10, 20)  # Increased delay
                                    print(f"Successfully downloaded. Waiting {delay:.1f} seconds...")
                                    time.sleep(delay)
                                    break
                                    
                                except Exception as e:
                                    if retry < max_retries - 1:
                                        wait_time = 30 * (2 ** retry)
                                        print(f"Download failed. Waiting {wait_time} seconds... (Attempt {retry + 1}/{max_retries})")
                                        time.sleep(wait_time)
                                    else:
                                        print(f"Failed to download post after {max_retries} attempts: {e}")
                                        raise
                                        
                        # If we get here, we've downloaded all posts successfully
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_total_retries:
                            if posts_downloaded == 0:
                                raise  # Re-raise if we haven't downloaded anything
                            else:
                                print(f"\nWarning: Could only download {posts_downloaded} posts due to: {str(e)}")
                                break
                                
                        print(f"\nError occurred. Retrying with new session... (Attempt {retry_count}/{max_total_retries})")
                        time.sleep(60)  # Wait a minute before retry
                        try:
                            post_iterator = get_post_iterator()
                        except Exception as e:
                            print(f"Failed to get new session: {e}")
                            raise
                    
                    # Add delay between posts
                    if posts_downloaded < total_posts:
                        delay = uniform(8, 15)  # Conservative delay
                        print(f"Waiting {delay:.1f} seconds before next post...")
                        time.sleep(delay)
                    
            except instaloader.exceptions.QueryReturnedNotFoundException:
                print(f"\nProfile not found or has no accessible posts")
                return downloaded_files
            except instaloader.exceptions.LoginRequiredException:
                print(f"\nThis profile requires login to access")
                raise
            except instaloader.exceptions.InstaloaderException as e:
                if "429" in str(e):
                    print(f"\nRate limit hit. Please wait 15-30 minutes before trying again.")
                    raise
                elif posts_downloaded == 0:
                    print(f"\nFailed to fetch any posts: {str(e)}")
                    raise
                else:
                    print(f"\nWarning: Could only fetch {posts_downloaded} out of {total_posts} posts due to: {str(e)}")
                    return downloaded_files
            
            print(f"\nSuccessfully downloaded {posts_downloaded} posts")
                        

            
        except Exception as e:
            print(f"Error downloading profile: {str(e)}")
            raise

    def _download_post(self, post) -> List[Path]:
        """Download a single post."""
        temp_dir = self.download_dir / "temp"
        if temp_dir.exists():
            for f in temp_dir.glob('*'):
                f.unlink()
            temp_dir.rmdir()
        temp_dir.mkdir(exist_ok=True)

        try:
            if post.is_video:
                if self.quality == "high" and hasattr(post, 'video_url'):
                    url = post.video_url
                    ext = '.mp4'
                else:
                    self.loader.download_post(post, target=str(temp_dir))
                    return self._process_downloaded_files(temp_dir, post.shortcode)
            else:
                url = post.url if self.quality == "high" else getattr(post, 'thumbnail_url', post.url)
                ext = '.jpg'

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_file = temp_dir / f"instagram_{post.shortcode}_{timestamp}{ext}"
            
            attempt = 0
            max_attempts = 3
            while attempt < max_attempts:
                try:
                    print(f"Downloading {ext[1:]} file...")
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        with open(target_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    break
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(f"Download attempt {attempt} failed: {e}")
                    self.wait_with_backoff(attempt)

            final_path = self.download_dir / target_file.name
            if final_path.exists():
                final_path.unlink()
            target_file.rename(final_path)
            
            temp_dir.rmdir()
            return [final_path]

        except Exception as e:
            print(f"Direct download failed: {str(e)}")
            try:
                print("Trying fallback download method...")
                self.loader.download_post(post, target=str(temp_dir))
                return self._process_downloaded_files(temp_dir, post.shortcode)
            except Exception as e2:
                print(f"Fallback download failed: {str(e2)}")
                raise

    def _extract_shortcode_from_url(self, url: str) -> Optional[str]:
        """Extract shortcode from post URL."""
        patterns = [
            r'instagram.com/p/([^/?]+)',
            r'instagram.com/reel/([^/?]+)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        return None

    def _extract_username_from_url(self, url: str) -> Optional[str]:
        """Extract username from profile URL."""
        pattern = r'instagram.com/([^/?]+)'
        if match := re.search(pattern, url):
            username = match.group(1)
            return None if username in ['p', 'reel'] else username
        return None

    def _process_downloaded_files(self, temp_dir: Path, shortcode: str) -> List[Path]:
        """Process downloaded files and move them to final location."""
        downloaded_files = []
        for file in temp_dir.glob('*'):
            if file.suffix.lower() in ('.jpg', '.mp4'):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_name = f"instagram_{shortcode}_{timestamp}{file.suffix}"
                final_path = self.download_dir / new_name
                
                if final_path.exists():
                    final_path.unlink()
                file.rename(final_path)
                downloaded_files.append(final_path)
                print(f"Saved: {final_path.name}")
        
        return downloaded_files

class InstagramDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Content Downloader")
        self.downloader = InstagramDownloader()
        self.downloader.initialize_loader()
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Login Frame
        self.login_frame = ttk.LabelFrame(self.main_frame, text="Login", padding="5")
        self.login_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Username
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Login Button
        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=0, column=4, padx=5)
        
        # Login Status
        self.login_status_var = tk.StringVar(value="Not logged in")
        ttk.Label(self.login_frame, textvariable=self.login_status_var).grid(row=0, column=5, padx=5)
        
        # URL Entry and Quality Selection (same line)
        ttk.Label(self.main_frame, text="Instagram URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        
        # Quality Frame
        quality_frame = ttk.Frame(self.main_frame)
        quality_frame.grid(row=1, column=2, sticky=tk.W, pady=5)
        
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT, padx=(10, 5))
        self.quality_var = tk.StringVar(value="high")
        ttk.Radiobutton(quality_frame, text="High", variable=self.quality_var, 
                       value="high").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(quality_frame, text="Low", variable=self.quality_var,
                       value="low").pack(side=tk.LEFT, padx=5)
        
        # Download Type Selection
        ttk.Label(self.main_frame, text="Download:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.download_type = tk.StringVar(value="post")
        ttk.Radiobutton(self.main_frame, text="Single Post", variable=self.download_type,
                       value="post").grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(self.main_frame, text="Profile", variable=self.download_type,
                       value="profile").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # Download Button
        self.download_button = ttk.Button(self.main_frame, text="Download", command=self.start_download)
        self.download_button.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.main_frame, mode='indeterminate')
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Log Text
        self.log_text = scrolledtext.ScrolledText(self.main_frame, height=15, width=60)
        self.log_text.grid(row=5, column=0, columnspan=3, pady=5)
        self.log_text.configure(state='disabled')
        
        # Redirect stdout to the log text
        sys.stdout = RedirectText(self.log_text)
        
    def login(self):
        """Handle login button click"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        self.login_button.state(['disabled'])
        self.login_status_var.set("Logging in...")
        self.root.update()
        
        def do_login():
            success = self.downloader.login(username, password)
            self.root.after(0, self.login_complete, success)
        
        thread = threading.Thread(target=do_login)
        thread.daemon = True
        thread.start()
    
    def login_complete(self, success: bool):
        """Handle login completion"""
        self.login_button.state(['!disabled'])
        if success:
            self.login_status_var.set("Logged in")
            self.password_entry.delete(0, tk.END)  # Clear password for security
        else:
            self.login_status_var.set("Login failed")
    
    def start_download(self):
        """Start the download process in a separate thread."""
        if not self.downloader.is_logged_in:
            messagebox.showerror("Error", "Please log in first")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter an Instagram URL")
            return
            
        self.downloader.quality = self.quality_var.get()
        self.download_button.state(['disabled'])
        self.progress_bar.start(10)
        
        thread = threading.Thread(target=self.download_content, args=(url,))
        thread.daemon = True
        thread.start()
        
    def download_content(self, url: str):
        """Download content based on selected type."""
        try:
            if self.download_type.get() == "post":
                self.downloader.download_post(url)
            else:
                self.downloader.download_profile(url)
            
            self.root.after(0, self.download_complete, True)
            
        except Exception as e:
            self.root.after(0, self.download_complete, False, str(e))
    
    def download_complete(self, success: bool, error_message: str = None):
        """Handle download completion."""
        self.download_button.state(['!disabled'])
        self.progress_bar.stop()
        
        if success:
            messagebox.showinfo("Success", "Download completed successfully!")
        else:
            messagebox.showerror("Error", f"Download failed: {error_message}")

def main():
    root = tk.Tk()
    app = InstagramDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
