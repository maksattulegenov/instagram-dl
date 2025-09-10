import sys
from .downloader import InstagramDownloader
from .gui import InstagramDownloaderGUI
from .profile import InstagramProfileDownloader

__version__ = '1.0.0'

def main():
    """Entry point for the command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download content from Instagram.')
    parser.add_argument('url', help='Instagram URL (post or profile)')
    parser.add_argument('-u', '--username', help='Instagram username')
    parser.add_argument('-p', '--password', help='Instagram password')
    parser.add_argument('-o', '--output', default='downloads', help='Output directory')
    parser.add_argument('-g', '--gui', action='store_true', help='Launch GUI mode')
    parser.add_argument('--profile', action='store_true', help='Download entire profile')
    parser.add_argument('--version', action='version', version=f'instagram-dl {__version__}')
    
    args = parser.parse_args()
    
    if args.gui:
        import tkinter as tk
        root = tk.Tk()
        app = InstagramDownloaderGUI(root)
        root.mainloop()
        return
    
    if not args.username or not args.password:
        print("Error: Username and password are required for downloading.")
        parser.print_help()
        sys.exit(1)
    
    try:
        downloader = InstagramDownloader(args.output)
        if not downloader.login(args.username, args.password):
            print("Failed to login. Please check your credentials.")
            sys.exit(1)
        
        if args.profile:
            downloader.download_profile(args.url)
        else:
            downloader.download_post(args.url)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
