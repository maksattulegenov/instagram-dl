"""
Core Instagram downloader functionality
"""

import os
import re
import time
import json
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from tqdm import tqdm

class InstagramDownloader:
    """Main class for downloading content from Instagram"""
    
    def __init__(self, download_path: str = "downloads"):
        """
        Initialize the downloader with configuration
        
        Args:
            download_path (str): Directory where downloads will be saved
        """
        self.download_path = download_path
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self._logged_in = False

    def login(self, username: str, password: str) -> bool:
        """
        Log in to Instagram
        
        Args:
            username (str): Instagram username
            password (str): Instagram password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # First get the CSRF token
            login_page = self.session.get("https://www.instagram.com/accounts/login/")
            csrf = re.search('csrf_token":"(.*?)"', login_page.text).group(1)
            
            # Prepare login data
            login_data = {
                "username": username,
                "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
                "queryParams": {},
                "optIntoOneTap": "false"
            }
            
            # Add headers for login request
            self.session.headers.update({
                "X-CSRFToken": csrf,
                "Referer": "https://www.instagram.com/accounts/login/"
            })
            
            # Attempt login
            response = self.session.post(
                "https://www.instagram.com/accounts/login/ajax/",
                data=login_data
            )
            
            if response.json().get("authenticated"):
                self._logged_in = True
                return True
                
        except Exception as e:
            print(f"Login failed: {str(e)}")
        
        return False

    def _get_media_info(self, url: str) -> Dict:
        """
        Get media information from a post URL
        
        Args:
            url (str): URL of the Instagram post
            
        Returns:
            dict: Media information including URLs
        """
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the script containing media data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if "@type" in data and data["@type"] == "SocialMediaPosting":
                        return data
                except:
                    continue
                    
            # Alternative method using shared data
            shared_data = soup.find('script', text=re.compile('window._sharedData'))
            if shared_data:
                json_data = json.loads(re.search(r'window._sharedData = (.+);</script>', shared_data.string).group(1))
                media = json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
                return media
                
        except Exception as e:
            print(f"Error getting media info: {str(e)}")
            
        return {}

    def download_post(self, url: str, filename: Optional[str] = None) -> List[str]:
        """
        Download media from a single post
        
        Args:
            url (str): URL of the Instagram post
            filename (str, optional): Custom filename for the downloaded media
            
        Returns:
            list: List of paths to downloaded files
        """
        if not self._logged_in:
            raise Exception("Not logged in. Please call login() first.")
            
        media_info = self._get_media_info(url)
        downloaded_files = []
        
        try:
            if media_info.get("video"):
                # Handle video
                video_url = media_info["video"]["contentUrl"]
                output_path = self._download_file(video_url, filename, "mp4")
                downloaded_files.append(output_path)
            elif media_info.get("image"):
                # Handle image
                image_url = media_info["image"]["contentUrl"]
                output_path = self._download_file(image_url, filename, "jpg")
                downloaded_files.append(output_path)
            
            # Handle carousel/multiple images
            if "carousel" in media_info:
                for i, item in enumerate(media_info["carousel"]):
                    if item.get("video"):
                        output_path = self._download_file(
                            item["video"]["contentUrl"],
                            f"{filename}_{i}" if filename else None,
                            "mp4"
                        )
                    else:
                        output_path = self._download_file(
                            item["image"]["contentUrl"],
                            f"{filename}_{i}" if filename else None,
                            "jpg"
                        )
                    downloaded_files.append(output_path)
                    
        except Exception as e:
            print(f"Error downloading post: {str(e)}")
            
        return downloaded_files

    def _download_file(self, url: str, filename: Optional[str] = None, ext: str = "jpg") -> str:
        """
        Download a file from URL
        
        Args:
            url (str): URL of the file to download
            filename (str, optional): Custom filename
            ext (str): File extension
            
        Returns:
            str: Path to the downloaded file
        """
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            
        if not filename:
            filename = f"instagram_{int(time.time())}_{os.urandom(4).hex()}"
            
        output_path = os.path.join(self.download_path, f"{filename}.{ext}")
        
        response = self.session.get(url, stream=True)
        file_size = int(response.headers.get("Content-Length", 0))
        
        with tqdm(total=file_size, unit='B', unit_scale=True, desc=filename) as progress:
            with open(output_path, "wb") as f:
                for data in response.iter_content(chunk_size=1024):
                    if data:
                        f.write(data)
                        progress.update(len(data))
                        
        return output_path

    def close(self):
        """Close the session"""
        self.session.close()
