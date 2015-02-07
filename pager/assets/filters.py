import re
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile

from webassets.filter import Filter, register_filter, FilterError

class Requirify(Filter):
    name = 'requirify'
    max_debug_level = None

    def input(self, _in, out, **kw):
        module_path = re.sub(r'^(js)/', '', kw['source'])
        source = _in.read()
        out.write(
            "requirify('%s', function(require, exports, module) {\n%s\n});" % (
                module_path, source
            )
        )
register_filter(Requirify)

class Iced(Filter):
    name = 'iced'
    max_debug_level = None
    options = {
        'binary': 'ICED_BIN'
    }

    def input(self, _in, out, **kw):
        args = "-sp"
        proc = Popen([self.binary, args], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate(_in.read())
        if proc.returncode != 0:
            raise FilterError(('iced: subprocess had error: source=%s, '+
                               'stderr=%s, stdout=%s, returncode=%s') % (
                kw['source'], stderr, stdout, proc.returncode))
        elif stderr:
            print "iced filter has warnings:", stderr
        out.write(stdout)
register_filter(Iced)

class StaticUglifyJS(Filter):
    """
    Minify Javascript using `UglifyJS <https://github.com/mishoo/UglifyJS/>`_.

    UglifyJS is an external tool written for NodeJS; this filter assumes that
    the ``uglifyjs`` executable is in the path. Otherwise, you may define
    a ``UGLIFYJS_BIN`` setting.

    Additional options may be passed to ``uglifyjs`` using the setting
    ``UGLIFYJS_EXTRA_ARGS``, which expects a list of strings.
    """

    name = 'static-uglifyjs'
    options = {
        'binary': 'UGLIFYJS_BIN',
        'extra_args': 'UGLIFYJS_EXTRA_ARGS',
    }

    def output(self, _in, out, **kw):
        args = [self.binary or 'uglifyjs']
        if self.extra_args:
            args.extend(self.extra_args)
        with NamedTemporaryFile(
            suffix='.js', prefix='webssets_uglifyjs_', delete=True
        ) as source:
            source.write(_in.read())
            source.flush()
            args += (source.name,)
            uglifyjs = Popen(args, stdin=None, stdout=PIPE, stderr=PIPE)
            stdout, stderr = uglifyjs.communicate()
            if uglifyjs.returncode != 0:
                raise FilterError(
                    'uglifyjs: return error: stderr=%s, stdout=%s, $?=%s' % (
                        stderr, stdout, uglifyjs.returncode
                    )
                )
            elif stderr.replace('\n', ''):
                print >> sys.stderr, "uglifyjs: return some warnings:", stderr, "\n"
            out.write(stdout)
register_filter(StaticUglifyJS)