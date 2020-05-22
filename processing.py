import os
from hashlib import blake2b
from collections import defaultdict

SMALL_CHUNK = 1024  # bytes

# Files that were unable to be processed; will be printed in console output
error_files = []


def read_bytes(file, num_bytes=SMALL_CHUNK, offset=0):
    if offset > 0:
        file.seek(offset)

    while True:
        chunk = file.read(num_bytes)
        if not chunk:
            return
        yield chunk


def generate_hash(file_name, small_hash=True):
    hash_obj = blake2b()
    fp = open(file_name, 'rb')

    if small_hash:
        hash_obj.update(fp.read(SMALL_CHUNK))
    else:
        for chunk in read_bytes(fp):
            hash_obj.update(chunk)

    file_hash = hash_obj.digest()
    fp.close()

    return file_hash


def check_duplicates(directory=None, recursive=False):
    # Stores all files that have the same size
    files_by_size = __find_files_by_size__(directory, recursive)
    # Stores all duplicate files (same size and same contents)
    duplicate_files = __find_duplicate_files__(files_by_size)

    return duplicate_files


def __find_files_by_size__(directory, recursive=False):
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


def __find_duplicate_files__(files_by_size):
    # Key is tuple (file size, large hash), value is list of duplicate files
    duplicate_files = defaultdict(list)
    # Key is tuple (file size, small hash), value is file path
    small_hash_files = defaultdict(str)
    # Key is (file size, large hash), value is first file we find with the corresponding large hash
    large_hash_files = defaultdict(str)

    for files in files_by_size.values():
        # Continue in cases where there are no duplicates
        if len(files) < 2:
            continue

        for file in files:
            file_path = file.path
            file_size = file.size

            # Returns hash of full file, or small hash if it already covers the entire file
            def get_large_hash():
                return generate_hash(file_path, small_hash=False) if (file_size > SMALL_CHUNK) else small_hash

            # For each file with the same size, compute the small and large hashes
            try:
                small_hash = generate_hash(file_path, small_hash=True)
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
                # If we've already come across a file with the same large hash, let's store
                # this file in our duplicates
                else:
                    duplicates = duplicate_files[(file_size, large_hash)]
                    # If this is the first duplicate we've come across, make sure the first file
                    # we found with the same large hash is also saved
                    if len(duplicates) == 0:
                        duplicates.append(existing_large_hash_file)

                    duplicates.append(file_path)

        return duplicate_files


class File:

    def __init__(self, path, size, error=None):
        self.path = path
        self.size = size
        self.error = error
