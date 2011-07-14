import os
from webob.dec import wsgify
from webob import exc
from webob import Response
from tempita import HTMLTemplate
import urllib

here = os.path.dirname(os.path.abspath(__file__))


class Application(object):

    def __init__(self, dir):
        self.dir = dir

    @wsgify
    def __call__(self, req):
        req.charset = None
        if req.path_info == '/':
            return self.homepage(req)
        elif req.path_info == '/code.js':
            return self.bookmarklet(req)
        elif req.path_info == '/favicon.ico':
            return exc.HTTPNotFound()
        else:
            return self.store(req)

    def homepage(self, req):
        tmpl = HTMLTemplate.from_filename(os.path.join(here, 'homepage.html'))
        resp = tmpl.substitute(app=self, req=req)
        return Response(body=resp)

    def bookmarklet(self, req):
        with open(os.path.join(here, 'code.js')) as fp:
            return Response(
                body=fp.read(),
                content_type='application/javascript')

    def store(self, req):
        fn = self.filename(req)
        if req.method == 'GET':
            if not os.path.exists(fn):
                return exc.HTTPNotFound()
            with open(fn, 'rb') as fp:
                content_type = fp.readline().strip()
                body = fp.read()
                return Response(
                    cache_expires=True,
                    content_type=content_type,
                    body=body)
        elif req.method == 'POST':
            content_type = req.str_POST.get('content-type', 'text/html')
            if '_charset_' in req.str_POST:
                content_type += '; charset=' + req.str_POST['_charset_']
            body = req.str_POST['body']
            if req.POST.get('add-script'):
                body += ('\n<script>runComments = {app: %r, page: %r};</script><script src="%s/code.js"></script>\n'
                         % (req.application_url, req.url, req.application_url))
            with open(fn, 'wb') as fp:
                fp.write(content_type.strip() + '\n')
                fp.write(body)
            return Response(
                cache_expires=True,
                status=303,
                location=req.url)
        elif req.method == 'PUT':
            # FIXME: should figure out content-type
            content_type = 'application/json'
            body = req.body
            with open(fn, 'wb') as fp:
                fp.write(content_type.strip() + '\n')
                fp.write(body)
            return Response(
                cache_expires=True,
                status=201,
                location=req.url)
        else:
            return exc.HTTPMethodNotAllowed(
                allow='GET,POST')

    def filename(self, req):
        path = req.path_info.lstrip('/')
        path = urllib.quote(path, '')
        return os.path.join(self.dir, path)

if __name__ == '__main__':
    from wsgiref import simple_server
    data = os.path.join(here, 'annotation-data')
    if not os.path.exists(data):
        os.makedirs(data)
    app = Application(data)
    server = simple_server.make_server('127.0.0.1', 8080, app)
    print 'server on http://localhost:8080'
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
