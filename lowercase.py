import os

def rename_files_to_lowercase(directory):
    try:
        for filename in os.listdir(directory):
            old_path = os.path.join(directory, filename)
            new_filename = filename.lower()
            new_path = os.path.join(directory, new_filename)
            
            if old_path != new_path:  # Avoid unnecessary renaming
                os.rename(old_path, new_path)
                print(f'Renamed: {filename} -> {new_filename}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    dir_path = input("Enter the directory path: ")
    if os.path.isdir(dir_path):
        rename_files_to_lowercase(dir_path)
    else:
        print("Invalid directory path.")
