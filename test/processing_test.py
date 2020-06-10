import unittest
import os
import shutil
from api import processing as pro
from api.processing import DuplicateFileHandler


# File paths/directories created in tests
BASE_PATH = '../test/files/'
BASE_PATH_NESTED = BASE_PATH + 'folder1/'

# Stores duplicate files we create for testing purposes
# non_recursive stores the duplicate files only in the top-level directory (BASE_PATH) we create
# recursive stores the duplicate files that are also found when scanning the nested directory
# (BASE_PATH_NESTED). For each dict, key is the base file name and value is the DuplicateFileHandler object
# Key: base name, Value: FileHandler object
DUPLICATE_FILE_HANDLERS = dict(
    nonrecursive=dict(),
    recursive=dict()
)


class ProcessingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Populate BASE_PATH directory with files, some of which are duplicates.
        """
        cls.__setup_directory()

    @classmethod
    def tearDownClass(cls):
        """
        Remove all files created in BASE_PATH directory.
        """
        cls.__teardown_directory()

    def test_check_duplicates(self):
        """
        Tests our main check_duplicates function; our 'dry run' function
        """
        global DUPLICATE_FILE_HANDLERS

        # # # # # # # # #
        # Non-recursive #
        # # # # # # # # #

        # For testing purposes, we will sort our DuplicateFileHandlers by original
        # file name so they are in a predictable order each time
        test_handlers_non_recursive = pro.check_duplicates(BASE_PATH, recursive=False)
        test_handlers_non_recursive = sorted(test_handlers_non_recursive.values(), key=lambda dupes: dupes.original)
        expected_handlers_non_recursive = sorted(DUPLICATE_FILE_HANDLERS['nonrecursive'].values(),
                                                 key=lambda dupes: dupes.original)

        self.__compare_handlers(test_handlers_non_recursive, expected_handlers_non_recursive)

        # # # # # # #
        # Recursive #
        # # # # # # #

        test_handlers_recursive = pro.check_duplicates(BASE_PATH, recursive=True)
        test_handlers_recursive = sorted(test_handlers_recursive.values(), key=lambda dupes: dupes.original)
        expected_handlers_recursive = sorted(DUPLICATE_FILE_HANDLERS['recursive'].values(),
                                             key=lambda dupes: dupes.original)

        self.__compare_handlers(test_handlers_recursive, expected_handlers_recursive)

        # # # # # # # # # # # # # # # # # # # # # #
        # Non-recursive, actually deleting files  #
        # # # # # # # # # # # # # $ # # # # # # # #

        # dupes = pro.check_duplicates(BASE_PATH, recursive=True)

        # for key in dupes:
        #     files = dupes[key]
        #
        #     if len(files) == 0:
        #         continue
        #     if len(files) == 1:
        #         self.fail("Only one file was reported for key: ", key)
        #
        #     base_name = self.__get_file_base_name(files[0])
        #
        #     for file in dupes[key]:
        #         self.assertEqual(base_name, self.__get_file_base_name(file))

    def __compare_handlers(self,
                           test_handlers,
                           expected_handlers,
                           delete_criteria=None):
        """
        Given two lists of handlers, sorted by original file name, asserts that each handler's
        original file and list of duplicate files are equal.

        If there is no delete_criteria specified, then we don't care which file is considered
        the original and which are duplicates; we'll consider them all the same.

        :param test_handlers: handlers created from our tests
        :param expected_handlers: expected handlers
        """
        # First, ensure that the number of duplicates is correct
        self.assertEqual(len(expected_handlers), len(test_handlers))

        # Then, ensure they are the correct duplicates
        for expected_handler, test_handler in zip(expected_handlers, test_handlers):
            if delete_criteria is not None:
                self.assertEqual(expected_handler.original, test_handler.original)

            expected_duplicates = expected_handler.duplicates
            test_duplicates = test_handler.duplicates
            if delete_criteria is None:
                expected_duplicates.append(expected_handler.original)
                test_duplicates.append(test_handler.original)

            # Sort actual duplicate files by name before checking if they are the same
            expected_duplicates = sorted(expected_duplicates)
            test_duplicates = sorted(test_duplicates)

            # Ensure there are the expected number of duplicates
            self.assertEqual(len(expected_handler.duplicates), len(test_handler.duplicates))

            for e_file, t_file in zip(expected_duplicates, test_duplicates):
                self.assertEqual(e_file, t_file)

    # # # # # # # # # # #
    # Helper functions  #
    # # # # # # # # # # #
    @staticmethod
    def __get_file_base_name(path):
        """
        Returns the file's base name (everything before the extension)

        :param path: path to the file
        :return: base name of file
        """
        parts = path.split('_')
        if len(parts) == 2:
            return parts[1].split('.')[0]
        if len(parts) == 3:
            return parts[1]

    @staticmethod
    def __setup_directory(base_dir=BASE_PATH,
                          nested_dir=BASE_PATH_NESTED,
                          duplicate_freq=2,
                          extra_duplicate_freq=10):
        """
        Set up our test files. Creates a directory (base_dir) and a nested directory (nested_dir)
        that each contain 50 of the same files. In addition, each there exists a duplicate for every
        <duplicate_freq> file and an extra duplicate for every file that is a multiple of
        <duplicate_freq> and <extra_duplicate_freq>.

        Populates our global dict with all of the duplicate files that we expect to find when searching
        <base_dir> non-recursively and recursively.
        """
        # Here, we will store our duplicate file information
        global DUPLICATE_FILE_HANDLERS

        # Create test directories to populate with files (some duplicates)
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError:
            print("Setup failed with path: %s" % base_dir)

        try:
            os.makedirs(nested_dir, exist_ok=True)
        except OSError:
            print("Setup failed with path: %s" % nested_dir)

        def create_file(name, idx):
            contents = str(idx) + ' contents'
            with open(name, 'w') as fp:
                fp.write(contents)

        for i in range(1, 51):
            base_path = 'random_' + str(i)
            file_path = base_dir + base_path + '.txt'
            create_file(file_path, i)
            nested_file_path = nested_dir + base_path + '.txt'
            create_file(nested_file_path, i)

            # Create our DuplicateFileHandlers
            # Only stores the duplicate files in the top-level of the directory
            file_handler_non_recursive = DuplicateFileHandler(original=file_path)
            # Stores all of the duplicate files, both at the top-level and nested
            file_handler_recursive = DuplicateFileHandler(original=file_path)
            file_handler_recursive.append_duplicate(nested_file_path)

            # Create duplicates
            if i % duplicate_freq == 0:
                # Duplicate in top-level directory
                dupe_file_path = base_dir + base_path + '_2.txt'
                create_file(dupe_file_path, i)
                # Duplicate in nested directory
                nested_dupe_file_path = nested_dir + base_path + '_2.txt'
                create_file(nested_dupe_file_path, i)

                file_handler_non_recursive.append_duplicate(dupe_file_path)
                file_handler_recursive.append_duplicate(dupe_file_path)
                file_handler_recursive.append_duplicate(nested_dupe_file_path)

                if i % extra_duplicate_freq == 0:
                    # Duplicate in top-level directory
                    dupe_file_path = base_dir + base_path + '_3.txt'
                    create_file(dupe_file_path, i)
                    # Duplicate in nested directory
                    nested_dupe_file_path = nested_dir + base_path + '_3.txt'
                    create_file(nested_dupe_file_path, i)

                    file_handler_non_recursive.append_duplicate(dupe_file_path)
                    file_handler_recursive.append_duplicate(dupe_file_path)
                    file_handler_recursive.append_duplicate(nested_dupe_file_path)

                # Only store the non-recursive DuplicateFileHandler if there was a duplicate
                DUPLICATE_FILE_HANDLERS['nonrecursive'][base_path] = file_handler_non_recursive

            # In our recursive layer, every file is a duplicate, so store the DuplicateFileHandler
            DUPLICATE_FILE_HANDLERS['recursive'][base_path] = file_handler_recursive

    @staticmethod
    def __teardown_directory():
        shutil.rmtree(BASE_PATH)


if __name__ == '__main__':
    unittest.main()
