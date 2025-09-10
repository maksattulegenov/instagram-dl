import requests
import json
from pathlib import Path
from typing import List, Dict, Optional, Generator
from datetime import datetime
import time
from random import uniform
import concurrent.futures
from dataclasses import dataclass
import re
import urllib.parse

@dataclass
class MediaItem:
    shortcode: str
    url: str
    is_video: bool
    date: datetime
    caption: Optional[str]

class InstagramProfileDownloader:
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        self.session.headers.update(self.headers)

    def login(self, username: str, password: str) -> bool:
        """Login to Instagram"""
        try:
            # First get the initial cookies and CSRF token
            login_url = 'https://www.instagram.com/accounts/login/'
            response = self.session.get(login_url)
            
            # Try different patterns for CSRF token
            csrf_token = None
            patterns = [
                r'"csrf_token":"(.*?)"',
                r'csrf_token=(.*?);',
                r'csrftoken=(.*?);'
            ]
            
            for pattern in patterns:
                if match := re.search(pattern, str(response.headers.get('Set-Cookie', '')) + response.text):
                    csrf_token = match.group(1)
                    break
                    
            if not csrf_token:
                # If no CSRF token found, try to get it from cookies
                csrf_token = self.session.cookies.get('csrftoken')
                
            if not csrf_token:
                print("Could not find CSRF token, using fallback authentication...")
                # Try to continue anyway with basic auth
                csrf_token = 'missing'
                
            # Update headers with CSRF token and other required headers
            self.session.headers.update({
                'X-CSRFToken': csrf_token,
                'X-Instagram-AJAX': '1',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'https://www.instagram.com/accounts/login/',
                'Origin': 'https://www.instagram.com'
            })

            # Add small delay to mimic human behavior
            time.sleep(uniform(1, 2))

            # Perform login
            login_data = {
                'username': username,
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'stopDeletionNonce': '',
                'trustedDeviceRecords': '{}'
            }
            
            login_response = self.session.post(
                'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                data=login_data
            )

            # Check multiple possible success indicators
            response_data = login_response.json() if login_response.text else {}
            is_authenticated = any([
                response_data.get('authenticated') is True,
                response_data.get('status') == 'ok',
                'userId' in response_data,
                'sessionid' in self.session.cookies
            ])

            if is_authenticated:
                print("Successfully logged in to Instagram")
                return True
            else:
                print("Failed to login: Authentication failed")
                return False

        except Exception as e:
            print(f"Failed to login: {str(e)}")
            return False

    def get_user_id(self, username: str) -> Optional[str]:
        """Get user ID from username"""
        try:
            # First get the API response
            api_url = f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}'
            
            # Update headers specifically for this request
            headers = self.session.headers.copy()
            headers.update({
                'X-IG-App-ID': '936619743392459',  # Instagram's web app ID
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*'
            })
            
            response = self.session.get(api_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data and 'data' in data and 'user' in data['data']:
                return data['data']['user']['id']
            
            print(f"Could not find user ID in API response for {username}")
            return None

        except Exception as e:
            print(f"Error getting user ID: {str(e)}")
            # Print response content for debugging if available
            if 'response' in locals():
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.text[:200]}...")  # Print first 200 chars
            return None

    def get_profile_media(self, username: str, limit: Optional[int] = None) -> Generator[MediaItem, None, None]:
        """Get all media from a profile using Instagram's API"""
        try:
            # Set up headers for all requests
            headers = self.session.headers.copy()
            headers.update({
                'X-IG-App-ID': '936619743392459',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
                'X-ASBD-ID': '198387',
                'X-IG-WWW-Claim': '0',
                'X-CSRFToken': self.session.cookies.get('csrftoken', ''),
                'Referer': f'https://www.instagram.com/{username}/',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            })

            # First, get the user ID using Instagram's user info endpoint
            user_info_url = f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}'
            
            print(f"Fetching profile info for {username}...")
            response = self.session.get(user_info_url, headers=headers)
            if response.status_code == 404:
                print(f"Profile {username} not found")
                return
            response.raise_for_status()
            
            try:
                user_data = response.json()
                if not user_data.get('data', {}).get('user'):
                    print(f"No data found for user {username}")
                    print(f"Response: {user_data}")
                    return
                user_id = user_data['data']['user']['id']
                print(f"Found user ID: {user_id}")
            except Exception as e:
                print(f"Error parsing user data: {e}")
                print(f"Response text: {response.text[:200]}...")
                return

            # Get user's media
            count = 0
            has_next_page = True
            max_id = None
            
            while has_next_page and (limit is None or count < limit):
                time.sleep(uniform(1.0, 2.0))  # Add delay between requests
                
                try:
                    # Get user's posts using the feed API
                    url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/'
                    params = {
                        'count': 12  # Number of posts per request
                    }
                    if max_id:
                        params['max_id'] = max_id
                    
                    print(f"Fetching posts... (current count: {count})")
                    response = self.session.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'items' not in data:
                        print(f"No items found in response: {data}")
                        return
                        
                    items = data['items']
                    if not items:
                        print("No more items available")
                        break
                        
                    for item in items:
                        if limit and count >= limit:
                            return
                            
                        # Handle carousel posts (multiple images/videos)
                        if item.get('carousel_media'):
                            for carousel_item in item['carousel_media']:
                                media_url = None
                                is_video = bool(carousel_item.get('video_versions'))
                                
                                if is_video:
                                    media_url = carousel_item['video_versions'][0]['url']
                                else:
                                    candidates = carousel_item.get('image_versions2', {}).get('candidates', [])
                                    if candidates:
                                        media_url = candidates[0]['url']
                                
                                if media_url:
                                    yield MediaItem(
                                        shortcode=item['code'],
                                        url=media_url,
                                        is_video=is_video,
                                        date=datetime.fromtimestamp(item['taken_at']),
                                        caption=item.get('caption', {}).get('text') if item.get('caption') else None
                                    )
                                    count += 1
                        else:
                            # Single image/video post
                            media_url = None
                            is_video = bool(item.get('video_versions'))
                            
                            if is_video:
                                media_url = item['video_versions'][0]['url']
                            else:
                                candidates = item.get('image_versions2', {}).get('candidates', [])
                                if candidates:
                                    media_url = candidates[0]['url']
                            
                            if media_url:
                                yield MediaItem(
                                    shortcode=item['code'],
                                    url=media_url,
                                    is_video=is_video,
                                    date=datetime.fromtimestamp(item['taken_at']),
                                    caption=item.get('caption', {}).get('text') if item.get('caption') else None
                                )
                                count += 1
                    
                    # Update pagination info
                    has_next_page = data.get('more_available', False)
                    if has_next_page:
                        max_id = data.get('next_max_id')
                        if not max_id:
                            print("No next_max_id found for pagination")
                            break
                    
                except Exception as e:
                    print(f"Error fetching posts: {str(e)}")
                    if 'response' in locals():
                        print(f"Response status: {response.status_code}")
                        print(f"Response text: {response.text[:200]}...")
                    return

                if 'items' not in data:
                    print("Invalid response format from Instagram API")
                    print(f"Response: {data}")
                    break

                items = data['items']
                if not items:
                    print("No items found in response")
                    break

                for item in items:
                    if limit and count >= limit:
                        return

                    try:
                        # Handle carousel posts (multiple images/videos)
                        if item.get('carousel_media'):
                            for carousel_item in item['carousel_media']:
                                # Get video URL
                                video_url = None
                                if carousel_item.get('video_versions'):
                                    video_url = carousel_item['video_versions'][0]['url']
                                
                                # Get image URL
                                image_url = None
                                if carousel_item.get('image_versions2'):
                                    candidates = carousel_item['image_versions2'].get('candidates', [])
                                    if candidates:
                                        image_url = candidates[0]['url']
                                
                                media_url = video_url or image_url
                                if media_url:
                                    yield MediaItem(
                                        shortcode=item.get('code', ''),
                                        url=media_url,
                                        is_video=bool(video_url),
                                        date=datetime.fromtimestamp(item.get('taken_at', 0)),
                                        caption=item.get('caption', {}).get('text') if item.get('caption') else None
                                    )
                                    count += 1
                        else:
                            # Single image/video post
                            # Get video URL
                            video_url = None
                            if item.get('video_versions'):
                                video_url = item['video_versions'][0]['url']
                            
                            # Get image URL
                            image_url = None
                            if item.get('image_versions2'):
                                candidates = item['image_versions2'].get('candidates', [])
                                if candidates:
                                    image_url = candidates[0]['url']
                            
                            media_url = video_url or image_url
                            if media_url:
                                yield MediaItem(
                                    shortcode=item.get('code', ''),
                                    url=media_url,
                                    is_video=bool(video_url),
                                    date=datetime.fromtimestamp(item.get('taken_at', 0)),
                                    caption=item.get('caption', {}).get('text') if item.get('caption') else None
                                )
                                count += 1
                    except Exception as e:
                        print(f"Error processing item: {str(e)}")
                        print(f"Item data: {item}")
                        continue  # Continue with next item
                    
                    # Handle carousel posts (multiple images/videos)
                    if node.get('__typename') == 'GraphSidecar':
                        sidecar_children = node.get('edge_sidecar_to_children', {}).get('edges', [])
                        for child in sidecar_children:
                            child_node = child['node']
                            yield MediaItem(
                                shortcode=node['shortcode'],
                                url=child_node['video_url'] if child_node.get('is_video') else child_node['display_url'],
                                is_video=child_node.get('is_video', False),
                                date=datetime.fromtimestamp(node['taken_at_timestamp']),
                                caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                            )
                            count += 1
                    else:
                        # Single image/video post
                        yield MediaItem(
                            shortcode=node['shortcode'],
                            url=node['video_url'] if node.get('is_video') else node['display_url'],
                            is_video=node.get('is_video', False),
                            date=datetime.fromtimestamp(node['taken_at_timestamp']),
                            caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                        )
                        count += 1

                # Check if there are more pages
                has_next_page = bool(data.get('more_available'))
                if has_next_page:
                    end_cursor = data.get('next_max_id')
                    if not end_cursor:
                        print("No more pages available")
                        break
                else:
                    print("No more items available")
                    break
            page_info = edge_owner_to_timeline_media.get('page_info', {})
                
            # Process all media items
            while True:
                for edge in edges:
                    if limit and count >= limit:
                        return

                    node = edge['node']
                    
                    # Handle carousel posts (multiple images/videos)
                    if node.get('__typename') == 'GraphSidecar':
                        sidecar_children = node.get('edge_sidecar_to_children', {}).get('edges', [])
                        for child in sidecar_children:
                            child_node = child['node']
                            yield MediaItem(
                                shortcode=node['shortcode'],
                                url=child_node['video_url'] if child_node['is_video'] else child_node['display_url'],
                                is_video=child_node['is_video'],
                                date=datetime.fromtimestamp(node['taken_at_timestamp']),
                                caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                            )
                            count += 1
                    else:
                        # Single image/video post
                        yield MediaItem(
                            shortcode=node['shortcode'],
                            url=node['video_url'] if node['is_video'] else node['display_url'],
                            is_video=node['is_video'],
                            date=datetime.fromtimestamp(node['taken_at_timestamp']),
                            caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                        )
                        count += 1

                # Check if we have more pages
                has_next_page = page_info.get('has_next_page')
                if not has_next_page or (limit and count >= limit):
                    break

                end_cursor = page_info.get('end_cursor')
                if not end_cursor:
                    break

                # Get next page using GraphQL API
                variables = {
                    "id": user_id,
                    "first": 50,
                    "after": end_cursor
                }

                params = {
                    'query_hash': '69cba40317214236af40e7efa697781d',
                    'variables': json.dumps(variables)
                }

                response = self.session.get(
                    'https://www.instagram.com/graphql/query/',
                    params=params
                )

                if response.status_code != 200:
                    print(f"Error fetching next page: HTTP {response.status_code}")
                    break

                data = response.json()
                user_media = data.get('data', {}).get('user', {}).get('edge_owner_to_timeline_media', {})
                edges = user_media.get('edges', [])
                page_info = user_media.get('page_info', {})
                
                for edge in edges:
                    if limit and count >= limit:
                        break
                        
                    node = edge['node']
                    
                    # Handle carousel posts (multiple images/videos)
                    if node.get('__typename') == 'GraphSidecar':
                        carousel_edges = node.get('edge_sidecar_to_children', {}).get('edges', [])
                        for carousel_edge in carousel_edges:
                            carousel_node = carousel_edge['node']
                            yield MediaItem(
                                shortcode=node['shortcode'],
                                url=carousel_node['video_url'] if carousel_node['is_video'] else carousel_node['display_url'],
                                is_video=carousel_node['is_video'],
                                date=datetime.fromtimestamp(node['taken_at_timestamp']),
                                caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                            )
                            count += 1
                    else:
                        # Single image/video post
                        yield MediaItem(
                            shortcode=node['shortcode'],
                            url=node['video_url'] if node['is_video'] else node['display_url'],
                            is_video=node['is_video'],
                            date=datetime.fromtimestamp(node['taken_at_timestamp']),
                            caption=node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text')
                        )
                        count += 1
                
                has_next_page = page_info['has_next_page']
                end_cursor = page_info['end_cursor']
                
                # Add delay between requests
                time.sleep(uniform(1.0, 2.0))

        except Exception as e:
            print(f"Error fetching profile media: {str(e)}")
            return

    def download_media_item(self, media_item: MediaItem, username: str) -> bool:
        """Download a single media item"""
        try:
            # Create user directory
            user_dir = self.download_dir / username
            user_dir.mkdir(exist_ok=True)
            
            # Generate filename
            date_str = media_item.date.strftime("%Y%m%d_%H%M%S")
            ext = "mp4" if media_item.is_video else "jpg"
            filename = f"instagram_{media_item.shortcode}_{date_str}.{ext}"
            filepath = user_dir / filename
            
            # Don't redownload if file exists
            if filepath.exists():
                print(f"File already exists: {filename}")
                return True
                
            # Download the file
            print(f"Downloading {filename}...")
            response = self.session.get(media_item.url, stream=True)
            
            if response.ok:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"Successfully downloaded: {filename}")
                return True
            else:
                print(f"Failed to download {filename}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error downloading {media_item.shortcode}: {str(e)}")
            return False

    def download_profile(self, username: str, limit: Optional[int] = None, max_workers: int = 3):
        """Download all media from a profile"""
        # Create user directory if it doesn't exist
        user_dir = self.download_dir / username
        user_dir.mkdir(exist_ok=True)
        
        # Collect all media items first
        media_items = []
        try:
            for item in self.get_profile_media(username, limit):
                media_items.append(item)
                print(f"Found media: {item.shortcode} ({'video' if item.is_video else 'image'})")
        except Exception as e:
            print(f"Error fetching profile media: {str(e)}")
            return
        
        if not media_items:
            print(f"No media items found for user: {username}")
            return
            
        print(f"\nFound {len(media_items)} media items. Starting download...")
        
        # Download media items with a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_media_item, item, username): item 
                for item in media_items
            }
            
            completed = 0
            total = len(futures)
            
            for future in concurrent.futures.as_completed(futures):
                item = futures[future]
                try:
                    success = future.result()
                    completed += 1
                    if success:
                        print(f"Progress: {completed}/{total} - Successfully downloaded {item.shortcode}")
                    else:
                        print(f"Progress: {completed}/{total} - Failed to download {item.shortcode}")
                except Exception as e:
                    completed += 1
                    print(f"Progress: {completed}/{total} - Error downloading {item.shortcode}: {str(e)}")
                
                # Add a small delay between downloads
                time.sleep(uniform(0.5, 1.0))

if __name__ == "__main__":
    # Example usage
    downloader = InstagramProfileDownloader()
    downloader.login("your_username", "your_password")
    downloader.download_profile("target_username", limit=10)  # Download first 10 posts
