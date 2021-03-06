from flask import Flask, render_template, request, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor, CKEditorField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from datetime import date
import bleach

# ----- Flask and Bootstrap ----- #
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SUPERSECRETKEY'
ckeditor = CKEditor(app)
Bootstrap(app)

# ----- Connect to DB ----- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ----- DB Table ----- #
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# ----- WTF form ----- #
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# ----- Strip URL of invalid tags ----- #
def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike', 'strong',
                    'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul']
    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }
    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)
    return cleaned


# -------- Website Routes -------- #
@app.route("/")
def home_page():
    blog_posts = BlogPost.query.all()
    return render_template("index.html", blog_posts=blog_posts)


@app.route("/about")
def about_page():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    if request.method == 'GET':
        return render_template("contact.html", contact_received=False)
    elif request.method == 'POST':
        contact_name = request.form['name']
        contact_email = request.form['email']
        contact_phone = request.form['phone']
        contact_message = request.form['message']
        return render_template("contact.html", contact_received=True)
    else:
        return '<h1>Invalid request to contact_page (must be GET or POST)</h1>'


@app.route("/posts/<int:post_id>")
def get_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    return render_template("post.html", post=requested_post)


@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            # Posts inside "post.html" are marked as "|safe".
            # To prevent malicious injections, 'body' is stripped of illegal tags before being saved.
            body=strip_invalid_html(form.body.data),
            img_url=form.img_url.data,
            author=form.author.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home_page'))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        # Posts inside "post.html" are marked as "|safe".
        # To prevent malicious injections, 'body' is stripped of illegal tags before being saved.
        post.body = strip_invalid_html(edit_form.body.data)
        db.session.commit()
        return redirect(url_for("get_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home_page'))


# ------- Start application ------- #
if __name__ == "__main__":
    app.run(debug=True)
