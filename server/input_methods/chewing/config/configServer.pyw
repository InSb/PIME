#! python3
# Copyright (C) 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import tornado.ioloop
import tornado.web
import sys
import os
from ctypes import windll  # for calling Windows api

configDir = os.path.expanduser("~\\PIME\\chewing")
dataDir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SERVER_TIMEOUT = 120
timeout_handler = None


class LoadHandler(tornado.web.RequestHandler):
    def get(self, file):
        if file == "config":
            self.load_config()
        elif file == "symbols":
            self.load_data("symbols.dat")
        elif file == "swkb":
            self.load_data("swkb.dat")
        else:
            self.write("")

    def load_config(self):
        try:
            with open(os.path.join(configDir, "config.json"), "r", encoding="UTF-8") as f:
                self.write(f.read())
        except Exception:
            self.write("{}")

    def load_data(self, name):
        try:
            userFile = os.path.join(configDir, name)
            with open(userFile, "r", encoding="UTF-8") as f:
                self.write(f.read())
        except FileNotFoundError:
            with open(os.path.join(dataDir, name), "r", encoding="UTF-8") as f:
                self.write(f.read())
        except Exception:
            self.write("")


class SaveHandler(tornado.web.RequestHandler):
    def post(self, file):
        data = self.get_argument("data", '')
        if file == "config":
            filename = "config.json"
        elif file == "symbols":
            filename = "symbols.dat"
        elif file == "swkb":
            filename = "swkb.dat"
        else:
            return
        os.makedirs(configDir, exist_ok=True)
        filename = os.path.join(configDir, filename)
        try:
            print(filename)
            # print(filename, data)
            with open(filename, "w", encoding="UTF-8") as f:
                f.write(data)
            self.write("ok")
        except Exception:
            self.write("failed")


def on_timeout():
    # terminate the server process
    tornado.ioloop.IOLoop.current().close()
    sys.exit(0)


class KeepAliveHandler(tornado.web.RequestHandler):
    def get(self):
        global timeout_handler
        loop = tornado.ioloop.IOLoop.current()
        if timeout_handler:
            loop.remove_timeout(timeout_handler)
            timeout_handler = loop.call_later(SERVER_TIMEOUT, on_timeout)
        self.write("ok")


def launch_browser(port):
    dirname = os.path.dirname(__file__)
    hta_file = os.path.join(dirname, "config.hta")
    # os.startfile(hta_file)
    # launch the hta file with ShellExecute since we need to pass port number as parameter
    windll.shell32.ShellExecuteW(None, "open", hta_file, "{0}".format(port), dirname, 1)  # SW_SHOWNORMAL = 1


def main():
    app = tornado.web.Application([
        (r"/keep_alive", KeepAliveHandler),  # keep the api server alive
        (r"/load/(.+)", LoadHandler),
        (r"/save/(.+)", SaveHandler)
    ])

    # find a port number that's available
    for port in range(5566, 32767):
        try:
            app.listen(port, "127.0.0.1")
            break
        except OSError:  # it's possible that the port we want to use is already in use
            continue

    # setup the main event loop
    launch_browser(port)
    loop = tornado.ioloop.IOLoop.current()
    global timeout_handler
    timeout_handler = loop.call_later(SERVER_TIMEOUT, on_timeout)
    loop.start()


if __name__ == "__main__":
    main()
