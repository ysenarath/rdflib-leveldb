# -*- coding: utf-8 -*-
"""
"""
__all__ = [
    "__title__",
    "__summary__",
    "__uri__",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    "lfu_cache",
    "lru_cache",
]


__title__ = "rdflib-leveldb"

__summary__ = (
    "An adaptation of RDFLib BerkeleyDB Store’s key-value approach,"
    "using LevelDB as a back-end. Implemented by Gunnar Grimnes, "
    "based on an original contribution by Drew Perttula. "
    "Migrated to Python 3 by Graham Higgins."
)

__uri__ = "https://github.com/RDFLib/rdflib-leveldb"

__version__ = "0.2"

__author__ = "Graham Higgins"
__email__ = "gjhiggins@gmail.com"

__license__ = "BSD"
__copyright__ = "Copyright 2021 {}".format(__author__)

import collections
import functools

from heapq import nsmallest
from operator import itemgetter


# this is added to python in 3.2, presumably more efficient than this
# from
# http://code.activestate.com/recipes/498245-lru-and-lfu-cache-decorators/


def lru_cache(maxsize=100):
    """Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """

    def decorating_function(user_function):
        cache = collections.OrderedDict()  # order: least recent to most recent

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args
            if kwds:
                key += tuple(sorted(kwds.items()))
            try:
                result = cache.pop(key)
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                wrapper.misses += 1
                if len(cache) >= maxsize:
                    cache.popitem(0)  # purge least recently used cache entry
            cache[key] = result  # record recent use of this key
            return result

        wrapper.hits = wrapper.misses = 0
        return wrapper

    return decorating_function


def lfu_cache(maxsize=100):
    """Least-frequenty-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    """

    def decorating_function(user_function):
        cache = {}  # mapping of args to results
        use_count = collections.defaultdict(int)
        # times each key has been accessed
        kwd_mark = object()  # separate positional and keyword args

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args
            if kwds:
                key += (kwd_mark,) + tuple(sorted(kwds.items()))
            use_count[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least frequently used cache entry
                if len(cache) > maxsize:
                    for key, _ in nsmallest(
                        maxsize // 10, use_count.items(), key=itemgetter(1)
                    ):
                        del cache[key], use_count[key]

            return result

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper

    return decorating_function
