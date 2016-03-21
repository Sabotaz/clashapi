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

from urllib.parse import urlparse, urlencode
import requests

import copy
import warnings
import time

#from xml.parsers import expat
from time import strptime
from calendar import timegm

__version__ = "0.9"
_default_useragent = "clashapi.py/{}".format(__version__)
_useragent = None  # use set_user_agent() to set this.

proxy = None
proxySSL = False

#-----------------------------------------------------------------------------

def set_cast_func(func):
	"""Sets an alternative value casting function for the XML parser.
	The function must have 2 arguments; key and value. It should return a
	value or object of the type appropriate for the given attribute name/key.
	func may be None and will cause the default _autocast function to be used.
	"""
	global _castfunc
	_castfunc = _autocast if func is None else func

def set_user_agent(user_agent_string):
	"""Sets a User-Agent for any requests sent by the library."""
	global _useragent
	_useragent = user_agent_string

class Error(Exception):
	def __init__(self, code, message):
		self.code = code
		self.message = message
	def __str__(self):
		return '%s [code=%s]' % (self.message, self.code)

class RequestError(Error):
	pass

class AuthenticationError(Error):
	pass

class ServerError(Error):
	pass

def EVEAPIConnection(url="api.clashofclans.com/v1", cacheHandler=None, proxy=None, proxySSL=False):
	if not url.startswith("http"):
		url = "https://" + url
	p = urlparse(url, "https")
	if p.path and p.path[-1] == "/":
		p.path = p.path[:-1]
	ctx = _RootContext(None, p.path, {}, {})
	ctx._handler = cacheHandler
	ctx._scheme = p.scheme
	ctx._host = p.netloc
	ctx._proxy = proxy or globals()["proxy"]
	ctx._proxySSL = proxySSL or globals()["proxySSL"]
	return ctx

def _HandleResult(response, fromContext, storeFunc):
	# nothing to do : response is already a json object
	if fromContext and storeFunc:
		# call the cache handler to store this object
		storeFunc(response)

	return response

#-----------------------------------------------------------------------------
# API Classes
#-----------------------------------------------------------------------------

_listtypes = (list, tuple, dict)
_unspecified = []

class _CacheControl(object):
	def __init__(self, cachedUntil=None, cachedFor=None):
		self.currentTime = time.time()
		if cachedUntil is not None:
			self.cachedUntil = cachedUntil
		elif cachedFor is not None:
			self.cachedUntil = self.currentTime + cachedFor
		else:
			self.cachedUntil = self.currentTime

class _Context(object):

	def __init__(self, root, path, parentDict, newKeywords=None):
		self._root = root or self
		self._path = path
		if newKeywords:
			if parentDict:
				self.parameters = parentDict.copy()
			else:
				self.parameters = {}
			self.parameters.update(newKeywords)
		else:
			self.parameters = parentDict or {}

	def context(self, *args, **kw):
		if kw or args:
			path = self._path
			if args:
				path += "/" + "/".join(args)
			return self.__class__(self._root, path, self.parameters, kw)
		else:
			return self

	def __getattr__(self, this):
		# perform arcane attribute majick trick
		return _Context(self._root, self._path + "/" + this, self.parameters)

	def __call__(self, **kw):
		if kw:
			# specified keywords override contextual ones
			for k, v in self.parameters.items():
				if k not in kw:
					kw[k] = v
		else:
			# no keywords provided, just update with contextual ones.
			kw.update(self.parameters)

		# now let the root context handle it further
		return self._root(self._path, **kw)

class _AuthContext(_Context):

	def clan(self, clanTag):
		# returns a copy of this connection object but for every call made
		# through it, it will add the folder "/clans" to the url, and the
		# clanTag to the parameters passed.
		return _Context(self._root, self._path + "/clans"+"/"+clanTag, self.parameters)

	def location(self, locationId):
		# same as character except for the folder "/locations"
		return _Context(self._root, self._path + "/locations"+"/"+locationId, self.parameters)

class _RootContext(_Context):

	def auth(self, **kw):
		if len(kw) == 1 and ("token" in kw):
			return _AuthContext(self._root, self._path, self.parameters, kw)
		raise ValueError("Must specify token")

	def setcachehandler(self, handler):
		self._root._handler = handler

	def __bool__(self):
		return True

	def __call__(self, path, **kw):
		# convert list type arguments to something the API likes
		token = kw["token"]
		del kw["token"]
		for k, v in kw.items():
			if isinstance(v, _listtypes):
				kw[k] = ','.join(map(str, list(v)))

		cache = self._root._handler

		# now send the request
		#path += ".xml.aspx"

		if cache:
			response = cache.retrieve(self._host, path, kw)
		else:
			response = None

		if response is None:
			if not _useragent:
				warnings.warn("No User-Agent set! Please use the set_user_agent() module-level function before accessing the CLASH API.", stacklevel=3)

			proxies = None
			if self._proxy is not None:
				if self._proxySSL:
					proxies = {'https':self._proxy}
				else:
					proxies = {'http':self._proxy}

			req = self._scheme+'://'+self._host+path
			headers = {"Accept": "application/json", "User-Agent": _useragent or _default_useragent, "authorization": "Bearer " + token}

			r = requests.get(req, headers = headers, params = kw)

			if r.status_code != requests.codes.ok:
				r.raise_for_status()
			if cache:
				store = True
			else:
				store = False
			response = r.json()

			secs = r.headers['Cache-Control'].split()[1].split('=')[1]
			cacheControl = _CacheControl(cachedFor=int(secs))
		else:
			store = False

		retrieve_fallback = cache and getattr(cache, "retrieve_fallback", False)
		if retrieve_fallback:
			# implementor is handling fallbacks...
			try:
				return _HandleResult(response, True, store and (lambda _: cache.store(self._host, path, kw, response, cacheControl)))
			except Error as e:
				response = retrieve_fallback(self._host, path, kw, reason=e)
				if response is not None:
					return response
				raise
		else:
			# implementor is not handling fallbacks...
			return _HandleResult(response, True, store and (lambda _: cache.store(self._host, path, kw, response, cacheControl)))



