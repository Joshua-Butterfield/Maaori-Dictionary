from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# Databases for at school and home
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


def is_teacher():
    """
    A function to return whether the user is a teacher or not
    """
    if session.get("teacher") == 1:
        print("User is not a teacher")
        return False
    if session.get("teacher") == 0:
        print("User is a teacher")
        return True


def get_categories():
    """
    A function to display the categories
    """
    if request.method == 'GET':
        query = "SELECT cat_name FROM categories"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, ())
        category = cur.fetchall()
        print(category)
        con.commit()
        con.close()
        return category


# Homepage of website
@app.route('/', methods=['Get', 'Post'])
def render_homepage():
    category = get_categories()  # displaying categories
    if is_logged_in():  # to display first name of user on homepage
        first_name = session['first_name']
    else:
        first_name = ""

    return render_template('home.html', categories_list=category, logged_in=is_logged_in(),
                           teacher=is_teacher(), user_id=first_name)


# Section to add categories
@app.route('/add_category', methods=["GET", "POST"])
def render_add_category():
    if not is_logged_in() and not is_teacher():
        return redirect('/')
    category = get_categories()  # displaying categories
    if request.method == 'POST':
        cat_name = request.form.get('cat_name').strip().title()
        cat_desc = request.form.get('cat_desc')
        con = create_connection(DATABASE)
        query = "INSERT INTO categories(cat_name, cat_desc) VALUES(?, ?)"
        cur = con.cursor()
        try:
            cur.execute(query, (cat_name, cat_desc))
        except sqlite3.IntegrityError:
            return redirect('/?category+already+exists')
        con.commit()
        con.close()
        return redirect('/')

    return render_template('add_category.html', logged_in=is_logged_in(), categories_list=category,
                           teacher=is_teacher())


# Section for user signup
@app.route('/signup', methods=['Get', 'Post'])
def render_signup():
    category = get_categories()  # displaying categories
    if request.method == 'POST':  # Post to insert data
        # Grabs information from the website
        first_name = request.form.get('first_name').title().strip()
        surname = request.form.get('surname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('teacher')

        # Check to see whether the passwords match
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        # Sets a boundary for the password to increase security
        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+at+least+8+characters')

        hashed_password = bcrypt.generate_password_hash(password)  # hashes password (encrypts to prevent hacking)

        con = create_connection(DATABASE)  # creates connection with my database file
        # Inserts information from the form into the database
        query = "INSERT INTO enduser (first_name, surname, email, password, teacher) VALUES(?, ?, ?, ?, ?)"
        cur = con.cursor()
        try:
            cur.execute(query, (first_name, surname, email, hashed_password, teacher))  # runs the query
        except sqlite3.IntegrityError:  # if email is a duplicate
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()
        return redirect('/login')  # takes user back to the login page

    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('signup.html', error=error, logged_in=is_logged_in(), categories_list=category,
                           teacher=is_teacher())


# Section for user login
@app.route('/login', methods=['Get', 'Post'])
def render_login_page():
    category = get_categories()  # displaying categories
    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, first_name, password, teacher FROM enduser WHERE email=? "
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
            teacher = user_data[0][3]
        else:
            return redirect("/login?error=Email+or+password+is+incorrect")
        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Email+or+password+is+incorrect")
        # Set up a session for the login to tell the program if the user is logged in and a teacher
        session['email'] = email
        session['enduser_id'] = user_id
        session['first_name'] = first_name
        session['teacher'] = teacher
        return redirect('/')  # take user back to homepage

    return render_template('login.html', logged_in=is_logged_in(), categories_list=category, teacher=is_teacher())


# Section for user logout
@app.route('/logout')
def render_logout_page():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See=you+next+time')


# Section for displaying information within each category
@app.route('/categories', methods=['Get', 'Post'])
def categories():
    if request.method == 'POST':
        con = create_connection(DATABASE)
        # Data from adding a word
        added_maori = request.form.get('maori').strip().title()
        added_english = request.form.get('english').strip().title()
        added_description = request.form.get('description')
        added_level = request.form.get('level').strip().title()
        added_image = "noimage.png"
        category_selected = request.args.get('type')
        added_date_entry = datetime.now()
        first_name = session['first_name']
        added_user = first_name
        
        # Section for checking the level entered is valid
        level = request.form.get('level')
        try:
            if type(level) is type(None):
                return redirect('/?error=Level+must+be+between+0+and+10')
            else:
                level = int(level)
                if level < 1 or level > 10:
                    return redirect('/?error=Level+must+be+between+0+and+10')
        except ValueError:
            return redirect('/?error=Please+enter+a+valid+number')

        query = "INSERT INTO dict_data (maori, english, description, level, image, cat_name, timestamp, user) " \
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query, (
            added_maori, added_english, added_description, added_level, added_image, category_selected,
            added_date_entry, added_user))
        con.commit()
        con.close()

    # Section to display categories but prevent NULL error
    query = "SELECT cat_name FROM categories"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, ())
    category = cur.fetchall()
    con.commit()
    con.close()

    # Section to display information
    con = create_connection(DATABASE)
    category_selected = request.args.get('type')
    query = "SELECT id, maori, english, description, level, image, timestamp FROM dict_data WHERE cat_name = " \
            "'" + category_selected + "'"
    cur = con.cursor()
    cur.execute(query)
    data_list = cur.fetchall()
    con.commit()
    con.close()

    query = "SELECT cat_desc from categories where cat_name ='" + category_selected + "'"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query)
    cat_descs = cur.fetchall()
    con.commit()
    con.close()

    return render_template('categories.html', dict_list=data_list, logged_in=is_logged_in(), cat_descs=cat_descs,
                           category_selected=category_selected, categories_list=category, teacher=is_teacher())


# Section for each individual word
@app.route('/word')
def render_word():
    category = get_categories()  # displaying categories
    word_selected = request.args.get('type')  # grabs the word clicked
    con = create_connection(DATABASE)
    query = "SELECT id, english, description, level, image, timestamp, user FROM dict_data WHERE maori = " \
            "'" + word_selected + "'"
    cur = con.cursor()
    cur.execute(query)
    word_info = cur.fetchall()
    con.commit()
    con.close()

    return render_template('word.html', word_selected=word_selected, word_info=word_info, logged_in=is_logged_in(),
                           categories_list=category, teacher=is_teacher())


# Section to delete word
@app.route('/delete_word', methods=["GET", "POST"])
def render_delete_word():
    if not is_logged_in() and not is_teacher():
        return redirect('/')
    if request.method == 'GET':
        word_selected = request.args.get('type')  # grabs the word clicked
        if type:
            if word_selected is None:
                print("NULL")
            else:
                query = "DELETE FROM dict_data WHERE maori = '" + word_selected + "'"
                con = create_connection(DATABASE)
                cur = con.cursor()
                cur.execute(query)
                con.commit()
                con.close()
    return redirect('/')


# Section to delete categories
@app.route('/delete_category', methods=["GET", "POST"])
def render_delete_category():
    if request.method == 'GET':
        category_selected = request.args.get('type')  # grabs the category clicked
        if type:
            if category_selected is None:  # prevent NULL error
                print("NULL")
            else:
                query = "DELETE FROM categories WHERE cat_name = '" + category_selected + "'"
                con = create_connection(DATABASE)
                cur = con.cursor()
                cur.execute(query)
                con.commit()
                con.close()
    return redirect('/')


app.run(host='0.0.0.0', debug=True)
