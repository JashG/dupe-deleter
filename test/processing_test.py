import unittest
import os
import processing as pro

# File paths/directories created in tests
BASE_PATH = '../test/files'


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Populate BASE_PATH directory with files, some of which are duplicates.
        """
        # Create test directory and populate with files (some duplicates)
        try:
            os.makedirs(BASE_PATH, exist_ok=True)
        except OSError:
            print("Setup failed with path: %s" % BASE_PATH)

        # Create 50 files; create 1 duplicate for every other file; create additional duplicate
        # for every tenth file
        for i in range(1, 51):
            file_name = BASE_PATH + '/random_' + str(i) + '.txt'
            contents = str(i) + ' contents'
            with open(file_name, 'w') as fp:
                fp.write(contents)
            # Create duplicate for every other file
            if i % 2 == 0:
                file_name = BASE_PATH + '/random_' + str(i) + '_2.txt'
                with open(file_name, 'w') as fp:
                    fp.write(contents)
                # Create additional duplicate for every third file
                if i % 10 == 0:
                    file_name = BASE_PATH + '/random_' + str(i) + '_3.txt'
                    with open(file_name, 'w') as fp:
                        fp.write(contents)

    def test_check_duplicates(self):
        """
        Tests our main check_duplicates function
        """
        dupes = pro.check_duplicates(BASE_PATH)

        # For testing purposes, we know files are duplicates based on the way they were named
        for key in dupes:
            files = dupes[key]

            if len(files) == 0:
                continue
            if len(files) == 1:
                self.fail("Only one duplicate was reported for key: ", key)

            base_name = self.__get_file_base_name(files[0])

            for file in dupes[key]:
                self.assertEqual(base_name, self.__get_file_base_name(file))

    @staticmethod
    def __get_file_base_name(path):
        parts = path.split('_')
        if len(parts) == 2:
            return parts[1].split('.')[0]
        if len(parts) == 3:
            return parts[1]


if __name__ == '__main__':
    unittest.main()
