import musicazoo.wsgi
import musicazoo.settings
import werkzeug.serving

werkzeug.serving.run_simple('',musicazoo.settings.ports["wsgi"],musicazoo.wsgi.application,extra_files='settings.py')
