from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

#DATABASE = "C:/Users/18016/OneDrive - Wellington College/Maori Dictionary/dictionary.db"
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


@app.route('/', methods=['Get', 'Post'])
def render_homepage():
    # Section to add categories
    if request.method == 'POST':
        cat_name = request.form.get('cat_name').strip()
        con = create_connection(DATABASE)
        query = "INSERT INTO categories(cat_name) VALUES(?)"
        cur = con.cursor()
        cur.execute(query, (cat_name,))
        con.commit()
        con.close()
        return redirect('/')

    category = get_categories()
        
    if is_logged_in():
        fname = session['fname']
    else:
        fname = ""
        
    return render_template('home.html', categories_list=category, logged_in=is_logged_in(), user_id=fname)


@app.route('/signup', methods=['Get', 'Post'])
def render_signup():
    category = get_categories()
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
    return render_template('signup.html', error=error, logged_in=is_logged_in(), categories_list=category)


@app.route('/login', methods=['Get', 'Post'])
def render_login_page():
    category = get_categories()
    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, first_name, password FROM enduser WHERE email=? "
        cur = con.cursor()
        cur.execute(query, (email, ))
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

        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in(), categories_list=category)


@app.route('/logout')
def render_logout_page():
    category = get_categories()
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?messsage=See=you+next+time')


@app.route('/categories', methods=['Get', 'Post'])
def categories():
    #category = get_categories()
    if request.method == 'POST':
        con = create_connection(DATABASE)
        added_maori = request.form.get('maori').strip().title()
        added_english = request.form.get('english').strip().title()
        added_description = request.form.get('description')
        added_level = request.form.get('level').strip().title()
        added_image = "noimage.png"
        category_selected = request.args.get('type')
        added_date_entry = datetime.now()

        #if added level... <10

        query = "INSERT INTO dict_data (maori, english, description, level, image, category, timestamp) VALUES(?, ?, ?, ?, ?, ?, ?)"
        cur = con.cursor()
        cur.execute(query, (added_maori, added_english, added_description, added_level, added_image, category_selected, added_date_entry))
        con.commit()
        con.close()

    # Section to prevent NULL error
    query = "SELECT cat_name FROM categories"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, ())
    category = cur.fetchall()
    con.commit()
    con.close()

    con = create_connection(DATABASE)
    category_selected = request.args.get('type')
    query = "SELECT id, maori, english, description, level, image, timestamp FROM dict_data WHERE category = '"+category_selected+"'"
    cur = con.cursor()
    cur.execute(query)
    data_list = cur.fetchall()
    con.commit()
    con.close()

    return render_template('categories.html', dict_list=data_list, logged_in=is_logged_in(), category_selected=category_selected, categories_list=category)


@app.route('/word')
def render_word():
    #category = get_categories()
    word_selected = request.args.get('type')
    con = create_connection(DATABASE)

    query = "SELECT id, english, description, level, image, timestamp FROM dict_data WHERE maori = '" + word_selected + "'"
    cur = con.cursor()
    cur.execute(query)
    word_info = cur.fetchall()
    con.commit()
    con.close()
    
    return render_template('word.html', word_selected=word_selected, word_info=word_info, logged_in=is_logged_in())


app.run(host='0.0.0.0', debug=True)