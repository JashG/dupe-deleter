import os
from hashlib import blake2b
from collections import defaultdict

# Number of bytes to scan when generating small hash
SMALL_CHUNK = 1024  # bytes
# Delete criteria
DELETE_CRITERIA = {
    'name': 'name',
    'last_modified': 'last_modified',
}

# Files that were unable to be processed; will be printed in console output
# TODO: When adding class structure, this won't be a global variable
error_files = []


def check_duplicates(directory=None, recursive=False):
    # Stores all files that have the same size
    files_by_size = __find_files_by_size(directory, recursive)
    # Stores all duplicate files (same size and same contents)
    duplicate_files = __scan_duplicate_files(files_by_size)

    return duplicate_files


def delete_duplicates(directory=None,
                      recursive=False,
                      delete_criteria='name',
                      max_size=1):
    # Stores all files that have the same size
    files_by_size = __find_files_by_size(directory, recursive)
    # Delete all duplicate files (same size and same contents)
    duplicate_files = __scan_duplicate_files(files_by_size,
                                             delete=True,
                                             delete_criteria=delete_criteria,
                                             max_size=max_size)

    return duplicate_files


def __read_bytes(file, num_bytes=SMALL_CHUNK, offset=0):
    if offset > 0:
        file.seek(offset)

    while True:
        chunk = file.read(num_bytes)
        if not chunk:
            return
        yield chunk


def __generate_hash(file_name, small_hash=True):
    hash_obj = blake2b()
    fp = open(file_name, 'rb')

    if small_hash:
        hash_obj.update(fp.read(SMALL_CHUNK))
    else:
        for chunk in __read_bytes(fp):
            hash_obj.update(chunk)

    file_hash = hash_obj.digest()
    fp.close()

    return file_hash


def __find_files_by_size(directory, recursive=False):
    files_by_size = defaultdict(list)

    for (dir_path, dir_names, file_names) in os.walk(directory):
        for file_name in file_names:
            path = os.path.join(dir_path, file_name)
            try:
                size = os.path.getsize(path)
                file_obj = File(path, size)
            except OSError as e:
                file_obj = File(path, size, e)
                error_files.append(file_obj)
                continue

            files_by_size[size].append(file_obj)

        if not recursive:
            break

    return files_by_size


def __scan_duplicate_files(files_by_size,
                           delete=False,
                           delete_criteria='',
                           min_size=0,
                           max_size=0):
    """
    Iterates through dictionary, files_by_size, where each value is a list of files with the same
    file size.

    :param files_by_size: Dict of files to scan, where key is size (bytes) and value is list of
    File objects of that size
    :param delete: Whether or not to delete the duplicate files found
    :param delete_criteria: Criteria that determines which file to keep when a duplicate(s) is found;
    see DELETE_CRITERIA list
    :param min_size: The minimum size file to scan (in MB); files below this threshold will be skipped
    :param max_size: The maximum size file to scan (in MB); files above this threshold will be skipped
    :return:
    """
    # Key is tuple (file size, large hash), value is DuplicateFileHandler that stores original and
    # duplicate files
    duplicate_files = dict()
    # Key is tuple (file size, small hash), value is first file path we encounter with those values
    small_hash_files = defaultdict(str)
    # Key is (file size, large hash), value is file we consider to be the 'original' file based on
    # the delete_criteria. We use this because it stores every file with a unique large hash; however,
    # if that file doesn't have a duplicate, we don't want to store it in duplicate_files.
    large_hash_files = defaultdict(str)

    i = 1

    for files in files_by_size.values():
        # Continue in cases where there are no duplicates
        if len(files) < 2:
            continue

        for file in files:
            file_path = file.path
            file_size = file.size

            # Returns hash of full file, or small hash if it already covers the entire file
            def get_large_hash():
                return __generate_hash(file_path, small_hash=False) if (file_size > SMALL_CHUNK) else small_hash

            # When a duplicate file is discovered, compare the original file with the duplicate
            # and determine if they need to be swapped based on delete_criteria
            def should_swap_files(original_file, duplicate_file):
                if not delete_criteria:
                    return False

                if delete_criteria == DELETE_CRITERIA['name']:
                    # If original file comes later alphabetically, we should swap
                    return original_file > duplicate_file
                elif delete_criteria == DELETE_CRITERIA['last_modified']:
                    original_mod_time = os.path.getmtime(original_file)
                    duplicate_mod_time = os.path.getmtime(duplicate_file)

                    # If original file was modified before duplicate, we should swap
                    return original_mod_time < duplicate_mod_time

            # For each file with the same size, compute the small and large hashes
            try:
                small_hash = __generate_hash(file_path, small_hash=True)
                large_hash = get_large_hash()
            except OSError as e:
                error_files.append(File(file.path, file.size, e))
                continue

            # Determine if there exists a file of the same size and small hash
            existing_small_hash_file = small_hash_files[(file_size, small_hash)]

            # If such file doesn't exist, store this one's small and large hash
            if not existing_small_hash_file:
                small_hash_files[(file_size, small_hash)] = file_path
                large_hash_files[(file_size, large_hash)] = file_path
            # If such a file does exist, there's no need to store this one.
            # Instead, just see if there exists a file of the same size and large hash
            else:
                existing_large_hash_file = large_hash_files[(file_size, large_hash)]

                # If this is the first file we've come across with this large hash, store it
                if not existing_large_hash_file:
                    large_hash_files[(file_size, large_hash)] = file_path
                else:
                    # If this is our first duplicate, create a duplicate handler for this file
                    # TODO Find a more elegant way to do this
                    try:
                        duplicate_handler = duplicate_files[(file_size, large_hash)]
                    except KeyError:
                        i = i + 1
                        duplicate_handler = DuplicateFileHandler()
                        duplicate_files[(file_size, large_hash)] = duplicate_handler

                    # Figure out if the duplicate we found should be treated as the original file
                    # based on the delete_criteria
                    if should_swap_files(existing_large_hash_file, file_path):
                        large_hash_files[(file_size, large_hash)] = file_path
                        duplicate_handler.set_original(file_path)
                        duplicate_handler.append_duplicate(existing_large_hash_file)
                    else:
                        # If this is the first duplicate we've encountered, we need to also set
                        # the original file
                        if not duplicate_handler.get_original():
                            duplicate_handler.set_original(existing_large_hash_file)
                        duplicate_handler.append_duplicate(file_path)

    return duplicate_files


class File:

    def __init__(self, path, size, error=None):
        self.path = path
        self.size = size
        self.error = error


class DuplicateFileHandler:

    def __init__(self, original='', duplicates=None):
        self.original = original
        if duplicates is None:
            self.duplicates = []
        else:
            self.duplicates = duplicates

    def set_original(self, file):
        self.original = file

    def get_original(self):
        return self.original

    def append_duplicate(self, file):
        self.duplicates.append(file)
