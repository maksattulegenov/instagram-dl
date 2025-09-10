"""
Command-line interface for Instagram Downloader
"""

import argparse
import sys
from typing import List
from instagram_dl.downloader import InstagramDownloader
from instagram_dl.profile import InstagramProfileDownloader
from instagram_dl.gui import InstagramDownloaderGUI

def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments
    
    Args:
        args: List of command line arguments
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Download media content from Instagram posts and profiles"
    )
    
    parser.add_argument(
        "-u", "--username",
        help="Instagram username for login"
    )
    
    parser.add_argument(
        "-p", "--password",
        help="Instagram password for login"
    )
    
    parser.add_argument(
        "-d", "--directory",
        default="downloads",
        help="Directory to save downloaded files (default: downloads)"
    )
    
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Download entire profile instead of single post"
    )
    
    parser.add_argument(
        "--max-posts",
        type=int,
        help="Maximum number of posts to download from profile"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical user interface"
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="URL of Instagram post or profile to download"
    )
    
    return parser.parse_args(args)

def main():
    """Main entry point for the command-line interface"""
    args = parse_args(sys.argv[1:])
    
    # Launch GUI if requested
    if args.gui:
        gui = InstagramDownloaderGUI()
        gui.run()
        return
        
    # Validate arguments for CLI mode
    if not args.url:
        print("Error: URL is required for CLI mode")
        return
        
    if not args.username or not args.password:
        print("Error: Username and password are required for CLI mode")
        return
        
    try:
        if args.profile:
            # Download profile
            downloader = InstagramProfileDownloader(args.username, args.password, args.directory)
            files = downloader.download_profile(args.url, args.max_posts)
            downloader.close()
        else:
            # Download single post
            downloader = InstagramDownloader(args.directory)
            if not downloader.login(args.username, args.password):
                print("Error: Login failed")
                return
                
            files = downloader.download_post(args.url)
            downloader.close()
            
        print(f"Successfully downloaded {len(files)} files")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main()
