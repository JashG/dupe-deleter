import unittest
import os
import shutil
import processing as pro

# File paths/directories created in tests
BASE_PATH = '../test/files'


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Populate BASE_PATH directory with files, some of which are duplicates.
        """
        cls.__setup_directory(cls, recursive=True)

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
        # # # # # # # # #
        # Non-recursive #
        # # # # # # # # #
        duplicate_files = pro.check_duplicates(BASE_PATH, recursive=False)

        for key in duplicate_files:
            file_handler = duplicate_files[key]
            original = file_handler.original
            duplicates = file_handler.duplicates

            if len(original) > 0 and len(duplicates) == 0:
                self.fail(("Original file with no duplicates was found. Path: ", original))

            base_name = self.__get_file_base_name(original)
            print("Original file: ", original)

            for file in duplicates:
                print("Duplicate file: ", file)
                self.assertEqual(base_name, self.__get_file_base_name(file))

            print("\n")

        # # # # # # #
        # Recursive #
        # # # # # # #
        duplicate_files = pro.check_duplicates(BASE_PATH, recursive=True)

        for key in duplicate_files:
            file_handler = duplicate_files[key]
            original = file_handler.original
            duplicates = file_handler.duplicates

            if len(original) > 0 and len(duplicates) == 0:
                self.fail("Original file with no duplicates was found. Path: ", original)

            base_name = self.__get_file_base_name(original)
            print("Original file: ", original)

            for file in duplicates:
                print("Duplicate file: ", file)
                self.assertEqual(base_name, self.__get_file_base_name(file))

            print("\n")

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
    def __setup_directory(cls, recursive=True):
        cls.__create_test_directory()
        if recursive:
            cls.__create_test_directory('../test/files/folder1', extra=3, double_extra=5)

    @staticmethod
    def __create_test_directory(path=BASE_PATH, extra=2, double_extra=10):
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
                file_name = path + '/random_' + str(i) + '_2.txt'
                with open(file_name, 'w') as fp:
                    fp.write(contents)

                if i % double_extra == 0:
                    file_name = path + '/random_' + str(i) + '_3.txt'
                    with open(file_name, 'w') as fp:
                        fp.write(contents)

    @staticmethod
    def __teardown_directory():
        shutil.rmtree(BASE_PATH)


if __name__ == '__main__':
    unittest.main()
