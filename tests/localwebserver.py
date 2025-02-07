#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
# SPDX-FileCopyrightText: Copyright (C) 2024 Stefan Lengfeld

import _thread
import os
import socket
import socketserver
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from os.path import join
from urllib.parse import urlparse

# TODO import tests from my other project


class TCPServerReuseAddress(socketserver.TCPServer):
    allow_reuse_address = True
    address_family = socket.AF_INET6
    # TODO make the socket dualstack
    # -> it's not so easiy, because its a attribute for the socket!


class DefaultRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(404)  # Not Found
        self.end_headers()


# This implements a file resolver to a local diretory
# See a good example:
#    https://github.com/python/cpython/blob/3.12/Lib/http/server.py
class FileRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, self_of_TCPServer):
        self._serve_directory = self_of_TCPServer._serve_directory
        super(SimpleHTTPRequestHandler, self).__init__(request, client_address, self_of_TCPServer)

    # Make the server quiet. Do not print anything to stdout.
    # See https://stackoverflow.com/a/56230070
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        # Parse the "path", because it contains parameters ('?')
        path_parsed = urlparse(self.path)

        # Remove the leading slash. Otherwise join() will not work!
        assert path_parsed.path[0] == "/"
        abs_path = join(self._serve_directory, path_parsed.path[1:])

        try:
            with open(abs_path, "rb") as f:
                content = f.read()
                self.send_response(200)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError as e:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        except Exception as e:
            print("LocalWebserver Generic Error: %s" % (e,))
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, e)
            return None


# See also https://github.com/python/cpython/blob/main/Lib/test/test_httpservers.py#L47
class LocalWebserver:
    def __init__(self, port, request_handler=None):
        self._port = port
        self._serve_directory = os.getcwd()
        if request_handler is None:
            self._request_handler = DefaultRequestHandler
        else:
            self._request_handler = request_handler

    def __enter__(self):
        self._httpd = TCPServerReuseAddress(("::1", self._port), self._request_handler)
        self._httpd._serve_directory = self._serve_directory

        def f():
            # The following call uses polling internall to check for the exit
            # flag, that is set by 'shutdown()'
            self._httpd.serve_forever()
            self._httpd.server_close()

        self._t = threading.Thread(target=f)
        self._t.start()

        return None

    def __exit__(self, *args):
        self._httpd.shutdown()
        self._t.join()
