

folder_path = "C:/Users/PMLS/Desktop/Softtech Internship/Art_DRM_backend"  
import os

def list_important_files(start_path):
    exclude_dirs = {"__pycache__", ".git", "venv"}
    allowed_extensions = (".py", ".txt", ".md")
    
    for root, dirs, files in os.walk(start_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith(allowed_extensions) and not file.startswith('.'):
                print(f"📄 {os.path.join(root, file)}")

list_important_files(folder_path)