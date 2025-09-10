import PyInstaller.__main__
import os
import sys

def create_exe():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main script
    main_script = os.path.join(script_dir, 'instagram_dl', 'cli.py')
    
    # PyInstaller options
    options = [
        main_script,
        '--onefile',
        '--name=instagram-dl',
        '--icon=NONE',
        '--add-data=README.md;.',
        '--hidden-import=tkinter',
        '--noconsole',  # Remove this if you want to show console
        f'--workpath={os.path.join(script_dir, "build")}',
        f'--distpath={os.path.join(script_dir, "dist")}',
        '--clean'
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(options)

if __name__ == '__main__':
    create_exe()
