import os
import stat

def live_directory_stats(directory):
    """This function uses os.stat() to generate a dictionary of files and their
    modification times as the value. This can be passed into
    live_compare_difference if two calls of this function were performed at
    different times.
    """
    file_list = []
    for path, _, files in os.walk(directory):
        file_list += [path + "/" + file for file in files]
    
    file_stats = {}
    for file in file_list:
        stats = os.stat(file)
        modification_time = stats[stat.ST_MTIME]
        # Remove the directory prefix when creating the key
        # file_stats[file[len(directory) + 1:]] = modification_time
        file_stats[file] = modification_time
    return file_stats


def live_compare_difference(old, _new):
    """Given two dictionaries of files, this function will compare between the
    two whether files were added/removed/modified. The return value is a tuple
    of three lists.
    """
    removed_files = []
    modified_files = []
    new_files = []

    for file in old.keys():
        if file not in _new:
            removed_files.append(file)
            continue
        old_modification_time = old[file]
        new_modification_time = _new[file]
        if old_modification_time != new_modification_time:
            modified_files.append(file)
    for file in _new.keys():
        if file not in old:
            new_files.append(file)
    return removed_files, modified_files, new_files


class DirectorySync:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

    def sync(self):
        source_stats = live_directory_stats(self.source)
        dest_stats = live_directory_stats(self.destination)
        removed_pages, modified_pages, added_pages = \
            live_compare_difference(dest_stats, source_stats)
        
        # If pages were removed, delete them from the build directory
        for file in removed_pages:
            print("Removing '{}'".format(file))
            os.remove(self.destination + "/" + file)
        
        # If pages were added or modified, then write the new file to the build
        # directory, overwriting anything there previously.
        for file in modified_pages + added_pages:
            print("Updating '{}'".format(file))
            with open(self.source + "/" + file) as f:
                to_write = f.read()
                with open(self.destination + "/" + file, "w") as w:
                    w.write(to_write)
        
        return len(removed_pages) + len(modified_pages) + len(added_pages)
        
