from typing import Callable
from _model import MenuGroup, MenuPage


class DirFile:
    def __init__(self, file_name: str, data: dict):
        self.file_name = file_name
        self.data = data


class DirFolder:
    def __init__(self, folder_name: str, sidebar_label: str):
        self.folder_name = folder_name
        self.sidebar_label = sidebar_label
        self.contents = []
    
    def add_file(self, file):
        self.contents.append(file)
        return file
    
    def __iter__(self):
        return self.contents.__iter__()


class DirectoryGenerator:
    """
    This Generator follows a specific structure to work. The idea is that you pass
    it a dictionary dictating how you want the file structure to work. And then
    you want to generate the files, pass this instance a function pointer to the
    generation function. We will automatically resupply you with the information
    you stored in the dictionary.
    
    The file structure is as follows:

    folder {
        sidebar: Folder Label
        files [
            file.txt: {
                // Any information extra stored here   
            }

            // This could contain another folder recursively
        ]
    }
    """
    def __init__(self, structure: dict, tab_name: str, to_folder="."):
        self.root = DirFolder(to_folder, tab_name)
        self._recursively_generate(structure, self.root)
    
    def _recursively_generate(self, p_structure: dict, p_folder: DirFolder):
        for f_name, structure in p_structure.items():
            # Structure is a Directory
            if "files" in structure:
                sidebar_label = structure["sidebar"]
                folder = p_folder.add_file(DirFolder(f_name, sidebar_label))
                for entry in structure["files"]:
                    self._recursively_generate(entry, folder)
            # Structure is a File
            else:
                p_folder.add_file(DirFile(f_name, structure))

    def _recursively_create_model(self, p_folder: DirFolder, p_menu: MenuGroup, gen: Callable, **kwargs):
        for i, file in enumerate(p_folder):
            # Directory
            if isinstance(file, DirFolder):
                menu = p_menu.add(MenuGroup(file.sidebar_label, file.folder_name))
                self._recursively_create_model(file, menu, gen, **kwargs)
            # File
            elif isinstance(file, DirFile):
                page_content = gen(file.file_name, i, file.data, **kwargs)
                if page_content is not None:
                    p_menu.add(MenuPage(page_content, file.file_name))

    def convert_to_model(self, generation_function: Callable, **kwargs) -> MenuGroup:
        """
        The generation function is in this format:

        def generate_file(file_name: str, position: int, file_data: dict, **kwargs) -> str:
            pass
        
        The generation function will be called for each file being created and
        we will pass the relevant information to each file so you can create it.
        The string returned is the contents of the file.
        """
        root_menu = MenuGroup(self.root.sidebar_label, self.root.folder_name)
        self._recursively_create_model(self.root, root_menu, generation_function, **kwargs)
        return root_menu
