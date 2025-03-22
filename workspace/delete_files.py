import os
import shutil

def delete_files_in_directory(directory_path):
 try:
 files = os.listdir(directory_path)
 for file in files:
 file_path = os.path.join(directory_path, file)
 if os.path.isfile(file_path):
 os.remove(file_path)
 print(f"Deleted file: {file_path}")
 elif os.path.isdir(file_path):
 shutil.rmtree(file_path)
 print(f"Deleted directory: {file_path}")
 print(f"Successfully deleted all files and subdirectories in {directory_path}")
 except FileNotFoundError:
 print(f"Error: Directory not found: {directory_path}")
 except PermissionError:
 print(f"Error: Permission denied to delete files in {directory_path}")
 except Exception as e:
 print(f"An unexpected error occurred: {e}")


directory_path = "E:\\Program\\Auto-Central-Control\\Auto-Central-Control\\workspace"
delete_files_in_directory(directory_path)
