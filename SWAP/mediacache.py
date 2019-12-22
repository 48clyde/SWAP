#
# Provides a simple cache for media files.
#
# Note: only enforces space/size constraints on startup where the oldest files are deleted
#
#

from appdirs import *
import pathlib
import hashlib
import shutil


class MediaCache:

    def __init__(self, group, max_size=200000000, max_files=200):
        self.group = group
        self.max_size = max_size
        self.max_files = max_files
        self.group_dir = os.path.join(user_cache_dir('SWAP', '48clyde'), group)
        pathlib.Path(self.group_dir).mkdir(parents=True, exist_ok=True)
        self.cached = {}
        self.cached_size = 0
        self.__load_cache()
        self.__check_limits()

    #
    # See what files are on disk
    #
    def __load_cache(self):
        self.cached.clear()
        for root, dirs, files in os.walk(self.group_dir):
            for file in files:
                file_name = os.path.join(root, file)
                stat = os.stat(file_name)
                self.cached[file_name] = (stat.st_ctime, stat.st_size)
                self.cached_size += stat.st_size

    #
    # Store a file in the cache
    #

    def store_file(self, file_name):
        fcn = self.get_file_cache_name(file_name)
        shutil.copy(file_name, fcn)
        stat = os.stat(fcn)
        self.cached[fcn] = (stat.st_ctime, stat.st_size)
        self.cached_size += stat.st_size
        self.__check_limits(fcn)

    #
    # Check the cache limits.
    #

    def __check_limits(self, exclude=None):
        #
        # File count limit reached?
        #
        ordered = sorted(self.cached, key=lambda cf: cf[1])

        cl = len(self.cached)
        if cl > self.max_files:
            to_remove = ordered[0: cl - self.max_files]
            for r in to_remove:
                if r is not exclude:
                    os.remove(r)
                    self.cached_size -= self.cached[r][0]
                    self.cached.pop(r)
        #
        # File size limit?
        #
        if self.cached_size > self.max_size:
            for f in ordered:
                if self.cached_size <= self.max_size:
                    break
                if f is not exclude:
                    os.remove(f)
                    self.cached_size -= self.cached[f][1]
                    self.cached.pop(f)

    #
    # See if the file is cached
    #

    def is_file_in_cache(self, file_name):
        fcn = self.get_file_cache_name(file_name)
        return fcn in self.cached

    #
    # Get the name of file in the cache, doesn't mean that the file is actually there
    #

    def get_file_cache_name(self, file_name):
        cfn = hashlib.md5(file_name.encode('utf-8')).hexdigest()
        return os.path.join(self.group_dir, cfn)


if __name__ == "__main__":
    mc = MediaCache("test", 100000, 3)
    mc.store_file("../screenshot.png")
    mc.store_file("../notes.txt")
    mc.store_file("sample.mp3")

