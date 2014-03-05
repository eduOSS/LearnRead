import os
import random
import shutil


def fill_suffix(base_str, width, fill_character):
    fill_width = max(0, width - len(base_str))
    return base_str + fill_width * fill_character


class FileUtils(object):

    @classmethod
    def random_path(cls):
        return os.path.join('/tmp/', str(random.randint(0, 10000)) + '.txt')

    @classmethod
    def copy(cls, src_path, dst_path):
        shutil.copy(src_path, dst_path)

    @classmethod
    def read(cls, path):
        with open(path, 'r') as content_file:
            return content_file.read()
