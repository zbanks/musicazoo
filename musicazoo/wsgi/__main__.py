import musicazoo.wsgi
import werkzeug.serving

werkzeug.serving.run_simple('localhost',8080,musicazoo.wsgi.application,extra_files='settings.py')
