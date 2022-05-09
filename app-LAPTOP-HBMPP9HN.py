from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# DATABASE = "C:/Users/18016/OneDrive - Wellington College/Maori Dictionary/dictionary.db"
DATABASE = r"C:/Users/Joshua Butterfield/OneDrive - Wellington College/Maori Dictionary/dictionary.db"
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "banana"


def create_connection(db_file):
    """
    Create a connection with the database
    parameter: name of the database file
    returns: a connection to the file
    """
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


def is_logged_in():
    """
    A function to return whether the user is logged in or not
    """
    if session.get("email") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True


def category_selected():
    """
    A function to return what category the user has chosen
    """
    # session.get("cat_name")
    # print(cat_name)
    print("hello")


@app.route('/')
def render_homepage():
    if request.method == 'POST':
        cat_name = request.form.get('cat_name').strip().lower()
        con = create_connection(DATABASE)
        print("hello")
        query = "INSERT INTO categories(cat_name) VALUES(?)"
        cur = con.cursor()
        cur.execute(query, (cat_name))
        category = cur.fetchall()
        con.commit()
        con.close()
    if request.method == 'GET':
        query = "SELECT cat_name FROM categories"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, ())
        category = cur.fetchall()
        con.commit()
        con.close()

    if is_logged_in():
        fname = session['fname']
    else:
        fname = ""

    return render_template('home.html', categories_list=category, logged_in=is_logged_in(), user_id=fname)


@app.route('/signup', methods=['Get', 'Post'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        first_name = request.form.get('first_name').title().strip()
        surname = request.form.get('surname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Check to see whether the passwords match
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)

        query = "INSERT INTO enduser (first_name, surname, email, password) VALUES(?, ?, ?, ?)"

        cur = con.cursor()
        try:
            cur.execute(query, (first_name, surname, email, hashed_password))
            print(first_name, surname, email, hashed_password)
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()
        return redirect('/login')  # takes user back to the login page

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template('signup.html', error=error, logged_in=is_logged_in())


@app.route('/login', methods=['Get', 'Post'])
def render_login_page():
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, first_name, password FROM enduser WHERE email=? "
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]

        else:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")
        # Set up a session for the login to tell the program I'm logged in
        session['email'] = email
        session['customer_id'] = user_id
        session['fname'] = first_name
        session['cart'] = []
        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?messsage=See=you+next+time')


@app.route('/categories')
def render_categories():
    con = create_connection(DATABASE)
    query = "SELECT cat_name FROM categories"
    cur = con.cursor()
    cur.execute(query)
    # print(cat_name)

    query = "SELECT id, maori, english, description, level, image from dict_data "
    cur = con.cursor()
    cur.execute(query)
    data_list = cur.fetchall()
    con.close()

    return render_template('categories.html', dict_list=data_list, logged_in=is_logged_in())


app.run(host='0.0.0.0', debug=True)