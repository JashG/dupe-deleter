import unittest
import os
import shutil
import processing as pro
from processing import DuplicateFileHandler


# File paths/directories created in tests
BASE_PATH = '../test/files'

# We will create duplicate file handlers that store appropriate duplicates that we create
# in the tests in order to make testing smoother
DUPLICATE_FILE_HANDLERS = []


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Populate BASE_PATH directory with files, some of which are duplicates.
        """
        cls.__setup_directory(cls, recursive_layer=False)

    @classmethod
    def tearDownClass(cls):
        """
        Remove all files created in BASE_PATH directory.
        """
        cls.__teardown_directory()

    def test_check_duplicates(self):
        """
        Tests our main check_duplicates function.
        This is our 'dry run' function; does not actually delete files.
        """
        global DUPLICATE_FILE_HANDLERS

        # # # # # # # # #
        # Non-recursive #
        # # # # # # # # #

        test_duplicate_handlers = pro.check_duplicates(BASE_PATH, recursive=False)
        # For testing purposes, we will sort our DuplicateFileHandlers by original
        # file name so they are in a predictable order each time
        test_duplicate_handlers = sorted(test_duplicate_handlers.values(), key=lambda dupes: dupes.original)
        expected_duplicate_handlers = sorted(DUPLICATE_FILE_HANDLERS, key=lambda dupes: dupes.original)

        # First, ensure that the number of duplicates is correct
        self.assertEqual(len(expected_duplicate_handlers), len(test_duplicate_handlers))

        # Then, ensure they are the correct duplicates
        for expected_handler, test_handler in zip(expected_duplicate_handlers, test_duplicate_handlers):
            self.assertEqual(expected_handler.original, test_handler.original)
            self.assertEqual(len(expected_handler.duplicates), len(test_handler.duplicates))

            # Sort actual duplicate files by name and ensure they are the same
            expected_duplicates = sorted(expected_handler.duplicates)
            test_duplicates = sorted(test_handler.duplicates)

            for e_file, t_file in zip(expected_duplicates, test_duplicates):
                self.assertEqual(e_file, t_file)

        # # # # # # #
        # Recursive #
        # # # # # # #

        # duplicate_files = pro.check_duplicates(BASE_PATH, recursive=True)
        #
        # for key in duplicate_files:
        #     file_handler = duplicate_files[key]
        #     original = file_handler.original
        #     duplicates = file_handler.duplicates
        #
        #     if len(original) > 0 and len(duplicates) == 0:
        #         self.fail("Original file with no duplicates was found. Path: ", original)
        #
        #     base_name = self.__get_file_base_name(original)
        #     print("Original file: ", original)
        #
        #     for file in duplicates:
        #         print("Duplicate file: ", file)
        #         self.assertEqual(base_name, self.__get_file_base_name(file))
        #
        #     print("\n")

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

    # # # # # # # # # # #
    # Helper functions  #
    # # # # # # # # # # #
    @staticmethod
    def __get_file_base_name(path):
        parts = path.split('_')
        if len(parts) == 2:
            return parts[1].split('.')[0]
        if len(parts) == 3:
            return parts[1]

    @staticmethod
    def __setup_directory(cls, recursive_layer=False):
        if not recursive_layer:
            cls.__create_test_directory()
        else:
            cls.__create_test_directory('../test/files/folder1', extra=3, double_extra=5)

    @staticmethod
    def __create_test_directory(path=BASE_PATH, extra=2, double_extra=10):
        # Here, we will store our duplicate file information
        global DUPLICATE_FILE_HANDLERS

        # Create test directory and populate with files (some duplicates)
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            print("Setup failed with path: %s" % path)

        # Create 50 files; create 1 duplicate for every <extra> file; create additional duplicate
        # for every <double_extra> file
        for i in range(1, 51):
            file_name = path + '/random_' + str(i) + '.txt'
            contents = str(i) + ' contents'
            with open(file_name, 'w') as fp:
                fp.write(contents)

            if i % extra == 0:
                handler = DuplicateFileHandler(original=file_name)
                file_name = path + '/random_' + str(i) + '_2.txt'
                with open(file_name, 'w') as fp:
                    fp.write(contents)
                    handler.append_duplicate(file_name)

                if i % double_extra == 0:
                    file_name = path + '/random_' + str(i) + '_3.txt'
                    with open(file_name, 'w') as fp:
                        fp.write(contents)
                        handler.append_duplicate(file_name)

                DUPLICATE_FILE_HANDLERS.append(handler)

    @staticmethod
    def __teardown_directory():
        shutil.rmtree(BASE_PATH)


if __name__ == '__main__':
    unittest.main()
