import PyInstaller.__main__
import os
import sys

def create_exe():
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a temporary main script
    main_script_content = '''
import sys
import os

if __name__ == '__main__':
    # Add the package directory to sys.path
    package_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(package_dir))
    
    from instagram_dl.cli import main
    main()
'''
    
    # Write the temporary main script
    temp_main = os.path.join(script_dir, 'main_launcher.py')
    with open(temp_main, 'w') as f:
        f.write(main_script_content)
    
    # PyInstaller options
    options = [
        temp_main,
        '--onefile',
        '--name=instagram-dl',
        '--icon=NONE',
        '--add-data=README.md;.',
        '--add-data=instagram_dl/*.py;instagram_dl',
        '--hidden-import=instagram_dl.downloader',
        '--hidden-import=instagram_dl.profile',
        '--hidden-import=instagram_dl.gui',
        '--hidden-import=tkinter',
        '--console',  # Show console for command-line interface
        f'--workpath={os.path.join(script_dir, "build")}',
        f'--distpath={os.path.join(script_dir, "dist")}',
        '--clean'
    ]
    
    try:
        # Run PyInstaller
        PyInstaller.__main__.run(options)
    finally:
        # Clean up temporary file
        if os.path.exists(temp_main):
            os.remove(temp_main)

if __name__ == '__main__':
    create_exe()
    print("\nBuild complete! The executable can be found in the 'dist' directory.")
    print("You can run it using: instagram-dl --help")
