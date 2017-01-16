#!/usr/bin/env python

import os
import BaseHTTPServer
import SimpleHTTPServer
import urllib
import cgi
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class ReqHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    server_version = "SimpleServer/0.1"
    extra_status = None

    def do_POST(self):
        """Handle a POST request."""
        content_type = self.headers['content-type']
        boundary_key = "boundary="
        if boundary_key not in content_type:
            self.extra_status = "ERROR: not a multipart upload"
            return self.do_GET()
        boundary = content_type[content_type.index(boundary_key)+len(boundary_key):]
        bytes_left = int(self.headers['content-length'])
        line = self.rfile.readline() # first file boundary
        bytes_left -= len(line)
        n_files = 0
        while bytes_left > 0:
            result, message, bytes_left = self.save_file(boundary, bytes_left)
            print("Result: {}, Message: {}".format(result, message))
            n_files += 1
        self.extra_status = "Successfully uploaded {} file(s)".format(n_files)
        return self.do_GET()

    def save_file(self, boundary, bytes_left):
        content_disposition = self.rfile.readline() # content disposition and filename
        bytes_left -= len(content_disposition)
        filename = re.findall('filename="(.*)"', content_disposition)[0]
        filepath = os.path.join(self.translate_path(self.path), filename)
        line = self.rfile.readline() # content type
        bytes_left -= len(line)
        line = self.rfile.readline() # newline
        bytes_left -= len(line)
        try:
            boundary_found = False
            buffered_line = None
            with open(filepath, 'wb') as output:
                while bytes_left > 0 and not boundary_found:
                    line = self.rfile.readline()
                    bytes_left -= len(line)
                    if boundary in line:
                        buffered_line = buffered_line[:-2] # trim CRLF
                        boundary_found = True
                    if buffered_line is not None:
                        output.write(buffered_line)
                    buffered_line = line
                return (True, "{} uploaded".format(filename), bytes_left)
        except:
            return (False, "Error writing to disk", 0)

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
        (COPIED VERBATIM FROM SimpleHTTPServer BUT MODIFIED TO SUPPORT UPLOADS)

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n")
        if self.extra_status is not None:
            f.write("<strong>%s</strong>\n" % self.extra_status)
        f.write("<h2>Upload</h2>")
        f.write("<form ENCTYPE=\"multipart/form-data\" method=\"post\">")
        f.write("<input name=\"file\" type=\"file\" multiple=\"multiple\"/>")
        f.write("<input type=\"submit\" value=\"Upload\"/></form>\n")
        f.write("<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.extra_status = None
        return f

def run(handler_class = ReqHandler, server_class = BaseHTTPServer.HTTPServer):
    httpd = server_class(('', 8000), handler_class)
    print('Serving on port 8000 ...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
