import os
import shutil
import folder_paths

class DeleteFolderAny:
    def __init__(self):
        self.success = False
        self.message = ""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "path": ("STRING", {"default": "", "multiline": False}),
                "target_directory": (["output", "input", "temp"], {"default": "output"}),
                "action": (["delete_path", "clear_directory"], {"default": "delete_path"}),
            },
            "optional": {
                "any_input": ("*", {}),
            }
        }
    
    @classmethod
    def VALIDATE_INPUTS(s, **kwargs):
        return True  # Bypass all input validation

    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("success", "message")
    FUNCTION = "delete_path"
    OUTPUT_NODE = True
    CATEGORY = "utils"

    def delete_path(self, path, target_directory, action, any_input=None):
        self.success = False
        self.message = ""
        
        # Map directory choice to actual path
        directory_map = {
            "input": folder_paths.get_input_directory(),
            "output": folder_paths.get_output_directory(),
            "temp": folder_paths.get_temp_directory()
        }
        
        if target_directory not in directory_map:
            self.message = f"Invalid target directory: {target_directory}"
            print(f"DeleteFolder: {self.message}")
            return (self.success, self.message)
        
        base_path = directory_map[target_directory]
        
        # Determine target path based on action
        if action == "clear_directory":
            # Clear all content in the base directory
            target_path = base_path
            if path:
                print(f"Warning: Path '{path}' ignored when clearing entire directory")
        else:
            # Delete specific path
            if not path:
                self.message = "No path provided for delete_path action"
                print(f"DeleteFolder: {self.message}")
                return (self.success, self.message)
            target_path = os.path.join(base_path, path)
        
        full_path = os.path.abspath(target_path)
        
        # Security check: ensure path is within the selected directory
        try:
            if os.path.commonpath([full_path, base_path]) != base_path:
                self.message = f"Access denied - path is outside {target_directory} directory"
                print(f"DeleteFolder: {self.message}")
                return (self.success, self.message)
        except ValueError:
            self.message = "Access denied - invalid path"
            print(f"DeleteFolder: {self.message}")
            return (self.success, self.message)

        try:
            if action == "clear_directory":
                # Delete all content in directory (files and folders)
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    deleted_files = 0
                    deleted_folders = 0
                    for item in os.listdir(full_path):
                        item_path = os.path.join(full_path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            deleted_files += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            deleted_folders += 1
                    self.success = True
                    self.message = f"Cleared {deleted_files} files and {deleted_folders} folders from {full_path}"
                    print(f"DeleteFolder: {self.message}")
                else:
                    self.message = f"Directory does not exist: {full_path}"
                    print(f"DeleteFolder: {self.message}")
                    # Success is False here
            else:
                # Delete specific folder/file
                if os.path.exists(full_path):
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                        self.success = True
                        self.message = f"Deleted directory: {full_path}"
                        print(f"DeleteFolder: {self.message}")
                    else:
                        os.remove(full_path)
                        self.success = True
                        self.message = f"Deleted file: {full_path}"
                        print(f"DeleteFolder: {self.message}")
                else:
                    self.message = f"Path does not exist: {full_path}"
                    print(f"DeleteFolder: {self.message}")
                    # Success is False here
        except Exception as e:
            self.message = f"Error deleting {full_path}: {str(e)}"
            print(f"DeleteFolder: {self.message}")
            # Success is False here (exception case)

        return (self.success, self.message)

# Register the node
NODE_CLASS_MAPPINGS = {
    "DeleteFolderAny": DeleteFolderAny
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeleteFolderAny": "Delete Folder (Any Input)"
}
