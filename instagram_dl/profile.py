"""
Profile downloader functionality for batch downloading all media from an Instagram profile
"""

import os
import json
import time
import re
from typing import List, Optional
from .downloader import InstagramDownloader

class InstagramProfileDownloader:
    """Class for downloading all media from an Instagram profile"""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 download_path: str = "downloads"):
        """
        Initialize profile downloader
        
        Args:
            username (str, optional): Instagram username
            password (str, optional): Instagram password
            download_path (str): Directory where downloads will be saved
        """
        self.downloader = InstagramDownloader(download_path)
        if username and password:
            self.login(username, password)

    def login(self, username: str, password: str) -> bool:
        """
        Log in to Instagram
        
        Args:
            username (str): Instagram username
            password (str): Instagram password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        return self.downloader.login(username, password)

    def download_profile(self, profile_url: str, max_posts: Optional[int] = None) -> List[str]:
        """
        Download all media from a profile
        
        Args:
            profile_url (str): URL of the Instagram profile
            max_posts (int, optional): Maximum number of posts to download
            
        Returns:
            list: List of paths to downloaded files
        """
        username = self._extract_username(profile_url)
        if not username:
            raise ValueError("Invalid profile URL")
            
        # Create profile directory
        profile_path = os.path.join(self.downloader.download_path, username)
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
            
        # Get profile posts
        posts = self._get_profile_posts(username, max_posts)
        downloaded_files = []
        
        # Download each post
        for post in posts:
            try:
                post_url = f"https://www.instagram.com/p/{post['shortcode']}/"
                timestamp = int(post.get('taken_at_timestamp', time.time()))
                filename = f"{username}_{post['shortcode']}_{timestamp}"
                
                files = self.downloader.download_post(post_url, filename)
                downloaded_files.extend(files)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error downloading post {post_url}: {str(e)}")
                continue
                
        return downloaded_files

    def _extract_username(self, profile_url: str) -> Optional[str]:
        """
        Extract username from profile URL
        
        Args:
            profile_url (str): Instagram profile URL
            
        Returns:
            str: Username or None if not found
        """
        patterns = [
            r"instagram\.com/([^/?]+)/?$",
            r"instagram\.com/([^/?]+)/"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, profile_url)
            if match:
                return match.group(1)
        return None

    def _get_profile_posts(self, username: str, max_posts: Optional[int] = None) -> List[dict]:
        """
        Get list of posts from a profile
        
        Args:
            username (str): Instagram username
            max_posts (int, optional): Maximum number of posts to fetch
            
        Returns:
            list: List of post data dictionaries
        """
        posts = []
        has_next_page = True
        end_cursor = None
        
        while has_next_page and (max_posts is None or len(posts) < max_posts):
            try:
                # Get profile page
                variables = {
                    "username": username,
                    "first": 50,
                    "after": end_cursor
                }
                
                params = {
                    "query_hash": "e769aa130647d2354c40ea6a439bfc08",
                    "variables": json.dumps(variables)
                }
                
                response = self.downloader.session.get(
                    "https://www.instagram.com/graphql/query/",
                    params=params
                )
                
                data = response.json()
                if not data.get("data"):
                    break
                    
                user = data["data"]["user"]
                if not user:
                    break
                    
                edge = user["edge_owner_to_timeline_media"]
                page_info = edge["page_info"]
                
                # Add posts from current page
                posts.extend(edge["edges"])
                
                # Check if we need to continue
                has_next_page = page_info["has_next_page"]
                end_cursor = page_info["end_cursor"] if has_next_page else None
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching profile posts: {str(e)}")
                break
                
        # Process and limit posts
        processed_posts = []
        for post in posts[:max_posts]:
            if "node" in post:
                processed_posts.append(post["node"])
                
        return processed_posts

    def close(self):
        """Close the downloader session"""
        self.downloader.close()
