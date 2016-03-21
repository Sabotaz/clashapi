#!/usr/bin/python3
#-----------------------------------------------------------------------------
# clashapi - Clash of Clan API access
#
# Copyright (c)2016 Julien "Sablier" Christophe <sablier@zendikar.fr>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE
#
#-----------------------------------------------------------------------------

# Based on eveapi - EVE Online API access (https://github.com/ntt/eveapi)
# Copyright (c)2007-2014 Jamie "Entity" van den Berge <jamie@hlekkir.com>

# for ssl error : http://stackoverflow.com/questions/31649390/python-requests-ssl-handshake-failure

import tempfile
import pickle
import zlib
import time
import os
from os.path import join, exists

class CacheHandler(object):
	# Note: this is an example handler to demonstrate how to use them.
	# a -real- handler should probably be thread-safe and handle errors
	# properly (and perhaps use a better hashing scheme).

	def __init__(self, debug=False):
		self.debug = debug
		self.count = 0
		self.cache = {}
		self.tempdir = join(tempfile.gettempdir(), "eveapi")
		if not exists(self.tempdir):
			os.makedirs(self.tempdir)

	def log(self, what):
		if self.debug:
			print("[%d] %s" % (self.count, what))

	def retrieve(self, host, path, params):
		# eveapi asks if we have this request cached
		key = hash((host, path, frozenset(list(params.items()))))

		self.count += 1  # for logging

		# see if we have the requested page cached...
		cached = self.cache.get(key, None)
		if cached:
			cacheFile = None
			#print "'%s': retrieving from memory" % path
		else:
			# it wasn't cached in memory, but it might be on disk.
			cacheFile = join(self.tempdir, str(key) + ".cache")
			if exists(cacheFile):
				self.log("%s: retrieving from disk" % path)
				f = open(cacheFile, "rb")
				cached = self.cache[key] = pickle.loads(zlib.decompress(f.read()))
				f.close()

		if cached:
			# check if the cached doc is fresh enough
			if time.time() < cached[0]:
				self.log("%s: returning cached document" % path)
				return cached[1]  # return the cached XML doc
			# it's stale. purge it.
			self.log("%s: cache expired, purging!" % path)
			del self.cache[key]
			if cacheFile:
				os.remove(cacheFile)

		self.log("%s: not cached, fetching from server..." % path)
		# we didn't get a cache hit so return None to indicate that the data
		# should be requested from the server.
		return None

	def store(self, host, path, params, doc, obj):
		# eveapi is asking us to cache an item
		key = hash((host, path, frozenset(list(params.items()))))

		cachedFor = obj.cachedUntil - obj.currentTime
		if cachedFor:
			self.log("%s: cached (%d seconds)" % (path, cachedFor))

			cachedUntil = time.time() + cachedFor

			# store in memory
			cached = self.cache[key] = (cachedUntil, doc)

			# store in cache folder
			cacheFile = join(self.tempdir, str(key) + ".cache")
			f = open(cacheFile, "wb")
			f.write(zlib.compress(pickle.dumps(cached, -1)))
			f.close()
