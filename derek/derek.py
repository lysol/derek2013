import os
from flask import Flask, render_template, abort
import markdown
import default_settings
import json
import datetime
from dateutil.parser import parse as dateparse

instance_path = os.path.expanduser('~/derek_instance/')

app = Flask(__name__, instance_path=instance_path)
app.config.from_object('derek.default_settings')
external_cfg = os.path.join(app.instance_path, 'application.cfg')
app.config.from_pyfile(external_cfg, silent=True)
app.TRAP_BAD_REQUEST_ERRORS = True


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
    def index(cls):
        filtered = filter(lambda x: x[-9:] == '.markdown' or x[-3:] == '.md',
                          os.listdir(cls.posts_path()))
        indexed = [cls.load(file, True) for file in filtered]
        return indexed

    @classmethod
    def parse(cls, contents):
        in_comment = False
        comment_start = -1
        comment = None
        json_body = None
        for i in range(0, len(contents)):
            if contents[i:i+2] == '/*':
                in_comment = True
                comment_start = i
            elif in_comment and contents[i:i+2] == '*/':
                in_comment = False
                comment = contents[comment_start+2:i]
                json_body = json.loads(comment.replace('\n', ''))
                break
        if comment is None:
            raise Exception("No post metadata detected.")
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
            stuff = cls.parse(contents)
            print stuff.keys()
            if 'post_date' in stuff:
                print 'post_date'
                mtime = float(dateparse(stuff['post_date']).strftime('%s'))
            else:
                print 'fack'
                mtime = os.path.getmtime(ofile)
            return Post(slug.split('.')[0], stuff['title'], stuff['contents'],
                        datetime.datetime.fromtimestamp(mtime), icon=stuff['icon'])
        else:
            print "Not found: " + ofile
            return None


@app.route('/<path:path>')
@app.route('/', defaults={'path': ''})
def all(path):
    if path == '':
        posts = Post.index()
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
