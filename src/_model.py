import os
import shutil
import json


class MenuPage:
    def __init__(self, content, file_name):
        self.content = str(content)
        self.file_name = file_name
    
    def write_to_file(self, base_directory=".", **_):
        write_to_file = base_directory + "/" + self.file_name
        with open(write_to_file, "w", encoding="utf-8") as f:
            f.write(self.content)
    
    def __len__(self):
        return 1

    def _as_string(self, indent=0):
        spaces = " " * indent
        return f"{spaces}MenuPage({self.file_name}) " + self.content[17:36]


class MenuGroup:
    def __init__(self, tab_name, folder_name):
        self.tab_name = tab_name
        self.folder_name = folder_name
        self.content = []

    def add(self, content):
        assert isinstance(content, MenuGroup) or \
            isinstance(content, MenuPage)
        self.content.append(content)
        return content
    
    def write_to_file(self, base_directory=".", position=0):
        # Reset the existing folder if it exists
        write_to_folder = base_directory + "/" + self.folder_name
        if os.path.isdir(write_to_folder):
            shutil.rmtree(write_to_folder)
        os.makedirs(write_to_folder)
        
        # Create the _category_.json file
        category = {
            "label": self.tab_name,
            "position": position
        }
        with open(write_to_folder + "/_category_.json", "w", encoding="utf-8") as f:
            json.dump(category, f, indent=4)
        
        # Recursively write the rest of the contents
        for i, content in enumerate(self.content):
            if isinstance(content, MenuGroup) or isinstance(content, MenuPage):
                content.write_to_file(base_directory=write_to_folder, position=i)
    
    def __len__(self):
        return sum([len(o) for o in self.content])
    
    def _as_string(self, indent=0):
        spaces = " " * indent
        return f"{spaces}MenuGroup({self.folder_name})\n" + \
            "\n".join(map(lambda m: m._as_string(indent + 2), self.content))

    def __repr__(self):
        return self._as_string(indent=0)
