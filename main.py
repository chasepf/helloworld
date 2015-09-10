import os
import webapp2
import jinja2
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
lessons_dir = os.path.join(os.path.dirname(__file__), 'lessons')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader([template_dir, lessons_dir]),
                               extensions=['jinja2.ext.autoescape'],
                               autoescape = True)

GUESTBOOK_NAME = "Chasepf's Guestbook"
PAGE_NOT_FOUND = 404
MAX_COMMENTS = 10
EMPTY_INPUT = '?err=1'

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def get(self):
        self.render("home.html")

class Lessons(Handler):
    def get(self):
        page = self.request.get("page")
        lesson_text = "lesson%s.html" % page
        if os.path.isfile(lessons_dir+'/lesson%s.html' % page):
          self.render(lesson_text, page=page)
        else:
          self.abort(PAGE_NOT_FOUND)

def guestbook_key(guestbook_name):
    """Constructs a Datastore key for a Guestbook entity.
    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)

class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Guestbook(Handler):
    def get(self):
        greetings_query = Greeting.query(
            ancestor=guestbook_key(GUESTBOOK_NAME)).order(-Greeting.date)
        greetings = greetings_query.fetch(MAX_COMMENTS)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
        
        error_mesg = ''
        err_type = self.request.get("err")
        if err_type == '1':
            error_mesg = 'Please fill out this field'
        else:
            if not err_type == '':
                self.abort(PAGE_NOT_FOUND)
        
        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(GUESTBOOK_NAME),
            'url': url,
            'url_linktext': url_linktext,
            'error_mesg': error_mesg
        }

        self.render('guestbook.html', **template_values)

    def post(self):
        greeting = Greeting(parent=guestbook_key(GUESTBOOK_NAME))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        
        if greeting.content.strip():
            greeting.put()
            self.redirect('/guestbook')
        else:
            self.redirect('/guestbook' + EMPTY_INPUT)

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/guestbook', Guestbook),
                               ('/lessons', Lessons)
                               ],
                              debug=True)