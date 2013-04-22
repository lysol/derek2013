import os
from flask import Flask, render_template, abort, url_for, Response
import markdown
import default_settings
import json
import datetime
from dateutil.parser import parse as dateparse
import feedgenerator

instance_path = os.path.expanduser('~/derek_instance/')

app = Flask(__name__, instance_path=instance_path)
app.config.from_object('derek.default_settings')
external_cfg = os.path.join(app.instance_path, 'application.cfg')
app.config.from_pyfile(external_cfg, silent=True)
app.TRAP_BAD_REQUEST_ERRORS = True


class DerekException:

    def __init__(self, text):
        self.text = text


class Post:

    @classmethod
    def posts_path(cls):
        return os.path.join(os.path.dirname(__file__), 'static/posts/')

    def created_formatted(self):
        return self.create_date.strftime("%B %d, %Y")

    def __init__(self, slug, title, contents, create_date, icon='antenna'):
        self.title = title
        self.contents = contents
        self.slug = slug
        self.create_date = create_date
        self.icon = icon

    @classmethod
    def feed(cls):
        return (post.feed_dict for post in cls.index())

    @classmethod
    def index(cls, include_future=False):
        filtered = filter(lambda x: x[-9:] == '.markdown' or x[-3:] == '.md',
                          os.listdir(cls.posts_path()))
        indexed = filter(lambda x: x is not None,
                         [cls.load(file, True) for file in filtered])

        def datesort(x, y):
            if x.create_date > y.create_date:
                return 1
            elif x.create_date < y.create_date:
                return -1
            else:
                return 0

        def nofuture(x):
            return x.create_date <= datetime.datetime.now()

        indexed.sort(datesort)
        indexed.reverse()
        if not include_future:
            indexed = filter(nofuture, indexed)
        return indexed

    @classmethod
    def parse(cls, contents):
        in_comment = False
        comment_start = -1
        comment = None
        json_body = None
        for i in range(0, len(contents)):
            if contents[i:i+4] == '<!--':
                in_comment = True
                comment_start = i
            elif in_comment and contents[i:i+3] == '-->':
                in_comment = False
                comment = contents[comment_start+4:i]
                json_body = json.loads(comment.replace('\n', ''))
                break
        if comment is None:
            raise DerekException("No post metadata detected.")
        return {'title': json_body['title'],
                'post_date': json_body['post_date'] if
                'post_date' in json_body else None,
                'contents': markdown.markdown(contents[i+2:]),
                'icon': json_body['icon'] if 'icon' in json_body else None}

    @classmethod
    def load(cls, slug, ext=False):
        ofile = cls.posts_path() + slug + ('.markdown' if not ext else '')
        if os.path.exists(ofile):
            handle = open(ofile)
            contents = handle.read()
            handle.close()
            try:
                stuff = cls.parse(contents)
                if 'post_date' in stuff:
                    mtime = float(dateparse(stuff['post_date']).strftime('%s'))
                else:
                    mtime = os.path.getmtime(ofile)
                return Post(slug.split('.')[0], stuff['title'], stuff['contents'],
                            datetime.datetime.fromtimestamp(mtime), icon=stuff['icon'])
            except DerekException:
                return None
        else:
            return None

    def get_icon(self):
        return self.icon if self.icon is not None else 'disk'

    def icon_url(self):
        return url_for('static', filename='img/icons/' + self.get_icon() + '.png')

    @property
    def feed_dict(self):
        return {
            "title": self.title,
            "link": url_for('all', path=self.slug),
            "description": self.summary
        }

    @property
    def summary(self):
        return self.contents if len(self.contents) < 255 else \
            self.contents[:255] + '...'


@app.route('/feed')
def feed():
    feed = feedgenerator.Rss201rev2Feed(
        title="Derek R. Arnold",
        link="http://derekarnold.net",
        description="Derek R. Arnold's Famous Internet Content",
        language="en"
    )
    map(lambda post: feed.add_item(**post), Post.feed())

    return Response(feed.writeString('utf-8'), mimetype="text/xml")


@app.route('/<path:path>')
@app.route('/', defaults={'path': ''})
def all(path):
    if path == '':
        posts = Post.index()
        return render_template('home.html', posts=posts)
    elif path == 'future':
        posts = Post.index(True)
        return render_template('home.html', posts=posts)
    slug = path.split('/')[0]
    post = Post.load(slug)
    if post is not None:
        return render_template('post.html', post=post)
    abort(404)

app.secret_key = app.config['SECRET']
app.debug = True

if __name__ == '__main__':
    app.run()
