from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = "btennant"

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(5000))
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.pub_date = datetime.utcnow()
        self.owner = owner

# create the User class with id, username, and password,
# connecting with Blog class on blogs

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    '''
    Require the user to log in before making a new post
    '''
    # if user isn't logged in, still needs to be allowed to see certain pages so they can log in
    # endpoint is the name of the view function, not the url path
    allowed_routes = ['login', 'display_post', 'index', 'signup', 'static'] #need to add CSS route to this list
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    '''
    Allows the user to login, if their data validates. Otherwise returns an error.
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        users = User.query.all()

        if user not in users:
            error = "User does not exist"
            return render_template('login.html', error=error)

        if user and user.password == password:
            session['username'] = username
            return redirect('/newpost')
        else:
            error = "Username or password incorrect"
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    '''
    Allows user to sign up for an account if their data validates. Otherwise returns error messages in form.
    '''
    if request.method == 'POST':
        username_error = ""
        existing_error = ""
        password_error = ""
        match_error = ""

        username = request.form['username']
        password = request.form['password']
        verify_password = request.form['verify_password']

        if username == "":
            username_error = "Username cannot be blank"
        elif (len(username)) < 3:
            username_error = "Username must be more than 3 characters in length"

        if password == "":
            password_error = "Password cannot be blank"
        elif (len(password)) < 3:
            password_error = "Password must be more than 3 characters in length"
        elif password != verify_password:
            match_error = "Passwords do not match"

        #  check to see if username is taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            existing_error = "That username is taken"

        # if there aren't any errors, then proceed to newpost with username stored in session
        # if there are errors, return form with error messages

        if not existing_user and not username_error and not password_error and not match_error:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            # use session (dictionary object stored on the server) to 'remember' that user has logged in
            session['username'] = username
            return redirect('/newpost')
        else:
            return render_template('signup.html',
                                    existing_error=existing_error,
                                    username_error=username_error,
                                    password_error=password_error,
                                    match_error=match_error)

    return render_template('signup.html')

@app.route('/logout')
def logout():
    '''
    Logs user out
    '''
    del session['username']
    return redirect('/')

@app.route('/blog', methods=['GET'])
def display_post():
    '''
    Shows all blog posts by default. If a request is made, shows either an individual entry or an individual
    user's page.
    '''
    # on the blog page, list all the blog posts with author name and link to their individual page
    # if the query params request an entry, show that individual entry
    # if the query params request a user ID, show that user's page

    # depending on what argument is passed in the request, get the id or the userid
    entry_id = request.args.get("id")
    userID = request.args.get("userid")

    if entry_id:
        entry = Blog.query.get(entry_id)
        return render_template("entry.html", entry=entry)

    if userID:
        user_posts = Blog.query.filter_by(owner_id=userID).all()
        return render_template("user.html", user_posts=user_posts)

    posts = Blog.query.order_by(desc(Blog.pub_date))
    return render_template("blog.html", posts=posts)

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    '''
    Creates a new blog post, or returns an error if data doesn't validate.
    '''
    if request.method == 'POST':
        title = request.form['title']
        entry = request.form['entry']
        error_1 = ''
        error_2 = ''

        if not title or not entry:
            if not title:
                error_1 = "Please enter a title"
            if not entry:
                error_2 = "Please enter a post body"
            return render_template('/newpost.html', title=title, entry=entry, error_1=error_1, error_2=error_2)
        else:
            # get the username from the session
            owner = User.query.filter_by(username=session['username']).first()

            post = Blog(title, entry, owner=owner)
            db.session.add(post)
            db.session.commit()

            # now that session is committed to the database,
            # get the ID of the post, then concatenate that ID
            # with the query params and redirect to the entry page

            entry_id = str(post.id)
            return redirect("/blog?id=" + entry_id)

    return render_template('newpost.html')

@app.route('/')
def index():
    '''
    Displays a list of all Blogz users with links to their pages.
    '''

    # get the username of all the objects of the User class/all the rows in the User table
    users = User.query.all()
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run()
