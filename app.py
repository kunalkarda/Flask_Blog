from flask import Flask,render_template,flash,session,logging,redirect,url_for,request
from flask_login import LoginManager,login_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField,TextAreaField,Form,validators
from wtforms.validators import DataRequired,Email,EqualTo,ValidationError,Length
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from functools import wraps


app = Flask(__name__)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = 'dd'

login = LoginManager(app)
login.login_view = 'login'
mysql = MySQL(app)
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/articles')
def all_article():
	cur = mysql.connection.cursor()
	result = cur.execute("select * from articles")
	articles = cur.fetchall()
	if result > 0:
	
		return render_template("articles.html",articles=articles)
	else :
		msg= 'No Articles Found'
		return render_template("articles.html")		
	cur.close()
 



@app.route('/articles/<string:id>')
def article(id):
	cur = mysql.connection.cursor()
	result = cur.execute("select * from articles where id= %s",[id])
	article= cur.fetchone()
	return render_template("article.html",article=article)


class LoginForm(Form):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])


@app.route('/login', methods=['GET','POST'])
def login():
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate() :
		username = form.username.data
		password_c = form.password.data
		cur = mysql.connection.cursor()

		result = cur.execute("SELECT * from users where username = %s",[username])

		if result > 0:
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(password_c,password):
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in','success')
				return redirect(url_for('dashboard'))
			else :
				error = 'USERname not found'
				return render_template('login.html',error=error)

 	return render_template("login.html",form=form)



class RegistrationForm(Form):
    name = StringField('name', [validators.Length(min=4, max=25)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/register',methods=['GET','POST'])
def register():
	form = RegistrationForm(request.form) 
	if request.method == 'POST' and form.validate():
		name = form.name.data
		username = form.username.data
        	email = form.email.data
        	password = sha256_crypt.encrypt(str(form.password.data))

            	cur = mysql.connection.cursor()
            	cur.execute("INSERT INTO users(name, email ,username,password) VALUES( %s,%s,%s,%s)",(name,email,username,password))
            	mysql.connection.commit()
            	cur.close()

            	flash('Thanks for registering','success')
            	return redirect(url_for('login')) 
        return render_template("register.html", form=form)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first","danger")
            return redirect(url_for('login'))

    return wrap



@app.route("/dashboard")
@login_required
def dashboard():
	cur = mysql.connection.cursor()
	result = cur.execute("select * from articles")
	articles = cur.fetchall()
	if result > 0:
	
		return render_template("dashboard.html",articles=articles)
	else :
		msg= 'No Articles Found'
		return render_template("dashboard.html")		
	cur.close()
 
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=4, max=25)])
    body = TextAreaField('Body', [validators.Length(min=4, max=300)])

@app.route("/add-article",methods=['GET','POST'])
@login_required
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		cur = mysql.connection.cursor()
            	cur.execute("INSERT INTO articles(title, body ,author) VALUES( %s,%s,%s)",(title,body,session['username']))
            	mysql.connection.commit()
            	cur.close()
		
		flash('Article Created', 'success')
		return redirect(url_for('dashboard'))
	return render_template("add_article.html",form=form)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):

	cur = mysql.connection.cursor()
	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

	article = cur.fetchone()
	cur.close()

	form = ArticleForm(request.form)


	form.title.data = article['title']
	form.body.data = article['body']

	if request.method == 'POST' and form.validate():
	        title = request.form['title']
	        body = request.form['body']


	        cur = mysql.connection.cursor()
	        app.logger.info(title)

	        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

	        mysql.connection.commit()

	
	        cur.close()

	        flash('Article Updated', 'success')

	        return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@login_required
def del_article(id):

	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM articles WHERE id = %s", [id])
	mysql.connection.commit()
	cur.close()

	flash('Article Deleted', 'success')

	return redirect(url_for('dashboard'))

@app.route("/logout")
@login_required
def logout():

    session.clear()
    flash('you are now logout','success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)




