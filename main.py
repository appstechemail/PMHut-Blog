import flask_login
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, session, abort
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
# from gravatar import Gravatar
import hashlib
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, BooleanField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date, timedelta, datetime
import create_db
import blog_posts_list
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import sqlite3
import random
import string
import requests
import secrets

EMAIL = os.environ.get('EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
SMTP_ADDRESS = os.environ.get('SMTP_ADDRESS')
# API_KEY = os.environ["API_KEY"]

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
login_manager = LoginManager()
login_manager.init_app(app)
Bootstrap5(app)
ckeditor = CKEditor(app)

# CREATE DATABASE
create_db = create_db.CreateDB()
db = create_db.db
cursor = db.cursor()
# login_u = LoginUser()
blog_posts = blog_posts_list.BlogList()
now = date.today().strftime("%B %d, %Y")
next_day = datetime.today() + timedelta(days=1)


def gravatar_url(email, size=80, default='https://gravatar.com/appstechemail'):
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}%ss={size}&d={default}"


# def gravatar_url(email, size=80, default='https://gravatar.com/appstechemail'):
#     email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
#     gravatar_api_url = f"https://www.gravatar.com/{email_hash}.json"
#
#     try:
#         response = requests.get(gravatar_api_url)
#         if response.status_code == 200:
#             gravatar_data = response.json()
#             if gravatar_data.get('entry'):
#                 return f"https://www.gravatar.com/avatar/{email_hash}%ss={size}"
#     except requests.RequestException as e:
#         print(f"Error checking Gravatar: {e}")
#
#     return default


# For adding profile images to the comment section
# gravatar = Gravatar(app,
#                     size=100,
#                     rating='g',
#                     default='retro',
#                     force_default=False,
#                     force_lower=False,
#                     use_ssl=False,
#                     base_url=None)


# Create Blog Post Form Fields
class BlogPostForm(FlaskForm):
    title = StringField('Blog Post Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    author = StringField('Your Name', validators=[DataRequired()])
    img_url = StringField('Blog Image URL', validators=[DataRequired()])
    body = CKEditorField('Blog Content', validators=[DataRequired()])
    submit = SubmitField(label='Submit Post')


class CommentForm(FlaskForm):
    comment = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField(label='Submit Comment')


class AboutForm(FlaskForm):
    project_about = CKEditorField('About Project', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


# Create Login form fields
class UserRegd(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Example@email.com"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "*******"})
    name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Name"})
    submit = SubmitField('SIGN ME UP')


# #################################### START Search Form + Update Admin Role ######################
class UserSearch(FlaskForm):
    email = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    admin_role = StringField('', render_kw={"placeholder": "Role"}, default='')
    update_role = BooleanField('Update Role', default=False)
    search = SubmitField('Search/Update', render_kw={"hidden": False})


# #################################### END Search Form + Update Admin Role ######################
class UserLogin(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Example@email.com"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "*******"})
    submit = SubmitField('LET ME IN!')


class UserReset(FlaskForm):
    # app.config['BOOTSTRAP_BTN_SIZE'] = 'block'
    email = StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Example@email.com"})
    submit = SubmitField('Get New Password')


class ChangePassword(FlaskForm):
    # app.config['BOOTSTRAP_BTN_SIZE'] = 'block'
    email = StringField('Email', validators=[DataRequired()], render_kw={"placeholder": "Example@email.com"})
    new_password = PasswordField('New Password', validators=[DataRequired()], render_kw={"placeholder": "*******"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()],
                                     render_kw={"placeholder": "Re-Type New Password"})
    verify = IntegerField('Verify', validators=[DataRequired()])
    submit = SubmitField('Change Password')


# ############################ LOGIN ##########################################
# @login_manager.unauthorized_handler
# def unauthorized():
#     return redirect(url_for('login'))


class UserM(UserMixin):
    def __init__(self, uid, email, password, name, admin_role, author_id):
        self.id = uid
        self.email = email
        self.password = password
        self.name = name
        self.admin_role = admin_role
        self.author_id = author_id


@login_manager.user_loader
def load_user(user_id):
    sql_user_loader = (
        "SELECT u.id, u.email, u.password, u.name, u.admin_role, COALESCE(SUM(bp.author_id), 0) "
        "FROM user_tab u "
        "LEFT JOIN blog_post bp ON u.id = bp.author_id "
        "WHERE u.id = %s "
        "GROUP BY u.id, u.email, u.password, u.name"
    )
    cursor.execute(sql_user_loader, [user_id])
    user_row = cursor.fetchone()

    if user_row:
        return UserM(user_row[0], user_row[1], user_row[2], user_row[3], user_row[4], user_row[5])
    else:
        return None


# ######################Restric User Decorators######################################################
def restrict_to_super_user(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # print(f"Inside restrict_to_super_user - Admin_role is : {current_user.admin_role}")
        if current_user.is_authenticated and current_user.admin_role == 1:
            return func(*args, **kwargs)
        else:
            abort(403)  # Forbidden

    return decorated_function


def restrict_to_admin(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # sql_admin_query = "SELECT admin_role from user_tab WHERE id = %s "
        # admin_role = cursor.execute(sql_admin_query, [current_user.id]).fetchone()[0]
        # print(f"Inside restrict_to_admin - Admin_role is : {admin_role}")
        # print(f"Inside restrict_to_admin - Admin_role is : {current_user.admin_role}")
        if ((current_user.is_authenticated and current_user.admin_role == 2) or
                (current_user.is_authenticated and current_user.admin_role == 1)):
            return func(*args, **kwargs)
        else:
            abort(403)  # Forbidden

    return decorated_function


def restrict_to_blog_owner(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # print(f"Inside restrict_to_admin - Admin_role is : {current_user.admin_role}")
        if ((current_user.is_authenticated and current_user.admin_role == 2 and
             current_user.id == current_user.author_id) or
                (current_user.is_authenticated and current_user.admin_role == 1)):
            return func(*args, **kwargs)
        else:
            abort(403)  # Forbidden

    return decorated_function


# ##############Valid Token Function#######################

# def valid_token(token):
#     # Query the database to check if the token exists and is not expired
#     sql_query = "SELECT token, expiration_datetime FROM token WHERE token = %s"
#     cursor.execute(sql_query, (token,))
#     token_data = cursor.fetchone()
#
#     if token_data:
#         # Check if the token is not expired
#         expiration_datetime = datetime.strptime(token_data[1], '%Y-%m-%d %H:%M:%s')
#         if expiration_datetime < datetime.now():
#             return "expire"
#         else:
#             return True
#     else:
#         # Token does not exist in the database
#         return False


def valid_token(token):
    # Query the database to check if the token exists and is not expired
    sql_query = "SELECT token, expiration_datetime FROM token WHERE token = %s"
    cursor.execute(sql_query, (token,))
    token_data = cursor.fetchone()

    if token_data:
        # Check if the token is not expired
        expiration_datetime_str = str(token_data[1]).split('.')[0]  # Remove fractional seconds
        try:
            expiration_datetime = datetime.strptime(expiration_datetime_str, '%Y-%m-%d %H:%M:%S')
            if expiration_datetime < datetime.now():
                return "expire"
            else:
                return True
        except ValueError:
            # If parsing fails, return an error
            return "error"
    else:
        # Token does not exist in the database
        return False


# Generate a random token of specified length
def generate_token(length=32):
    token = secrets.token_urlsafe(length)
    return token


# #############################################

# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegd()
    # print(f"user existsCheck: start")
    if request.method == 'POST':
        # print(f"user existsCheck: Entered Post Query")
        # print(f"Email: {form.email.data}")
        sql_query = "SELECT count(*) FROM user_tab WHERE email = %s;"
        cursor.execute(sql_query, [form.email.data,])
        user_exists = cursor.fetchone()
        # print(f"Cursor at row 292: {cursor.execute(sql_query, [form.email.data])}")
        # user_data = [rec for rec in user_exists]
        # print(f"user exists: {user_exists}")
        # print(f"user exists: {user_data}")
        if user_exists[0] == 0:
            # print(f"Enter New user creation")
            # Hashing and salting the password entered by the user
            hash_and_salted_password = generate_password_hash(password=form.password.data,
                                                              method='pbkdf2:sha256', salt_length=8)
            # param = (request.form.get("email"), hash_and_salted_password, request.form.get("name"))

            # param = (form.email.data, hash_and_salted_password, form.name.data)
            # sql_insert = "INSERT into user_tab(email, password, name) VALUES (%s, %s ,%s);"
            # cursor.execute(sql_insert, param)
            # db.commit()
            sql_query = "SELECT max(id)+1 FROM user_tab;"
            cursor.execute(sql_query)
            user_exists = cursor.fetchone()
            max_id = user_exists[0]
            sql_user_insert = "INSERT INTO user_tab (id, email, password, name, admin_role) VALUES (%s, %s, %s, %s, %s)"
            user_insert_param = (max_id, form.email.data, hash_and_salted_password, form.name.data, 0)
            cursor.execute(sql_user_insert, user_insert_param)
            db.commit()

            # sql_register = ("SELECT id, email, password, name, admin_role, (SELECT COALESCE(SUM(author_id), 0) "
            #                 "FROM blog_post Where user.id = blog_post.author_id LIMIT 1) author_id "
            #                 "FROM USER_tab WHERE email = %s")

            sql_register = ("SELECT u.id, u.email, u.password, u.name, u.admin_role, "
                            "COALESCE(SUM(bp.author_id), 0) AS author_id "
                            "FROM user_tab AS u "
                            "LEFT JOIN blog_post AS bp ON u.id = bp.author_id "
                            "WHERE u.email = %s GROUP BY u.id, u.email, u.password, u.name, u.admin_role;")
            cursor.execute(sql_register, [form.email.data])
            user_reg_row = cursor.fetchone()
            # print(f"user_reg_row row 317: {user_reg_row}")
            user = UserM(user_reg_row[0], user_reg_row[1], user_reg_row[2], user_reg_row[3],
                         user_reg_row[4], user_reg_row[5])
            login_user(user, True)
            return redirect(url_for("get_all_posts"))
        else:
            # We may use category= 'error' and the color will change to red as .error entry as red in stylesheet
            flash("You've already signed up with that email, log in instead!", 'message')
            return redirect(url_for('login'))
    else:
        return render_template("register.html", form=form)


@app.route('/search_users', methods=['GET', 'POST'])
@restrict_to_super_user
def search_users():
    form = UserSearch()
    update_flag = False
    submit_label = 'Search'
    # print(f"Start")
    # print(f"Email: {form.email.data}")
    # form.update_role.data = ''

    # # TODO: update_admin_role() to provide access to create blog and update
    sql_check_diff_count = "SELECT count(*) FROM user_tab WHERE email = %s"
    cursor.execute(sql_check_diff_count, [form.email.data])
    user_count = cursor.fetchone()
    # print(f"User_Count: {user_count}")
    if user_count[0] > 0:
        sql_retrieve_admin_code = "SELECT email, admin_role FROM user_tab WHERE email = %s"
        cursor.execute(sql_retrieve_admin_code, [form.email.data])
        current_admin_rec = cursor.fetchone()
        email, admin_role = current_admin_rec
        # print(f"Admin Role, Form.ADMIN_ROLE.DATA: {type(admin_role)}--{admin_role} ---{type(form.admin_role.data)}--"
        #       f"{form.admin_role.data}")
        # print(f"form.update_role.data: {form.update_role.data}")
        if form.admin_role.data != '' and form.update_role.data:
            if admin_role != int(form.admin_role.data):
                # print("Enter POST of Search Update")
                sql_update_role_query = "UPDATE user_tab SET admin_role = %s WHERE email = %s"
                update_role_param = (form.admin_role.data, email)
                cursor.execute(sql_update_role_query, update_role_param)
                db.commit()
                update_flag = True  # record updated
                # form.email.data = ''
                form.admin_role.data = ''
                form.update_role.data = ''
                flash("Updated role Successfully!", 'message')

    if form.validate_on_submit() and (form.admin_role.data == '' or not form.update_role.data):
        # Retrieve the form data
        email = form.email.data
        # print(f"Email1: {email}")
        user_data = []

        if email.upper() == 'ALL':
            sql_user_data = "SELECT id, email, name, admin_role FROM user_tab"
            cursor.execute(sql_user_data)
            user_rec = cursor.fetchall()
            user_data = [{'id': rec[0], 'email': rec[1], 'name': rec[2], 'admin_role': rec[3]} for rec in user_rec]
            # print(f"User Data1: {user_data}")
            submit_label = 'Search'
        else:
            sql_count_query = "SELECT count(*) FROM user_tab WHERE email = %s"
            cursor.execute(sql_count_query, [form.email.data])
            user_count = cursor.fetchone()
            if user_count[0] > 0:
                sql_user_data = "SELECT id, email, name, admin_role FROM user_tab WHERE email = %s"
                cursor.execute(sql_user_data, [form.email.data])
                user_rec = cursor.fetchall()
                user_data = [{'id': rec[0], 'email': rec[1], 'name': rec[2], 'admin_role': rec[3]} for rec in user_rec]
                form.admin_role.data = user_data[0]['admin_role']
                # print(f"User Data21: {user_data}")
                submit_label = 'Update Admin Role'
            else:
                flash("Invalid Email!", 'message')
        return render_template('user-details.html', submit_label=submit_label, user_data=user_data, form=form)
    elif not update_flag and form.email.data != '':
        flash("For Query, ensure admin role field is blank!", 'message')

    return render_template('user-details.html', form=form)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLogin()
    # print(f"Inside Login email is: {form.email.data}")
    if request.method == "POST" and form.validate_on_submit():
        username = form.email.data
        password = form.password.data
        # Find user by email entered.
        sql_count = "SELECT count(*) from user_tab WHERE email = %s"
        cursor.execute(sql_count, [username])
        user_count = cursor.fetchone()
        if user_count[0] != 0:
            # sql_login_user = ("SELECT id, email, password, name, admin_role, (SELECT COALESCE(SUM(author_id), 0) "
            #                   "FROM blog_post Where user.id = blog_post.author_id LIMIT 1) author_id "
            #                   "FROM USER_tab WHERE email = %s")

            sql_login_user = (
                "SELECT u.id, u.email, u.password, u.name, u.admin_role, COALESCE(SUM(bp.author_id), 0) "
                "FROM user_tab u "
                "LEFT JOIN blog_post bp ON u.id = bp.author_id "
                "WHERE u.email = %s "
                "GROUP BY u.id, u.email, u.password, u.name"
            )
            cursor.execute(sql_login_user, [username])
            user_row = cursor.fetchone()
            # user_rec = dict(user_row)
            # print(user_rec)
            if user_row:
                user = UserM(user_row[0], user_row[1], user_row[2], user_row[3],
                             user_row[4], user_row[5])
                # print(f"user: {user}")
                if check_password_hash(user.password, password):
                    login_user(user)
                    # next_page = request.args.get('next')
                    # print(f"Sessions: {session}")
                    return redirect(url_for("get_all_posts"))
                else:
                    flash('Password incorrect, please try again.', 'error')
                    return redirect(url_for('login'))
        else:
            flash("That email does not exists. Please try again!", 'error')
            return redirect(url_for('login'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/reset', methods=['GET', 'POST'])
def request_reset_password():
    form = UserReset()

    if request.method == "POST":
        # Generate a random four-digit code

        sql_query = "SELECT id, email, password, name FROM user_tab WHERE email = %s"
        cursor.execute(sql_query, [form.email.data])
        user_rec = cursor.fetchone()
        if user_rec:
            # print(f"User Rec in Reset: {user_rec}")
            user_id, user_email, user_password, user_name = user_rec
            # print(f"User rec: {user_email}, {user_password}, {user_name}")

            verification_code = ''.join(random.choices(string.digits, k=4))
            # verification_code_time = f"{verification_code}-{now}"

            sql_verification_query = "UPDATE user_tab SET verification_code = %s Where email = %s"
            param = (verification_code, user_email)
            cursor.execute(sql_verification_query, param)

            random_token = generate_token()
            # print("Random Token:", random_token)
            sql_check_token_userid = "SELECT count(*) FROM token WHERE user_id = %s "
            cursor.execute(sql_check_token_userid, [user_id])
            sql_token_userid_count = cursor.fetchone()
            if sql_token_userid_count[0] > 0:
                sql_update_token_id = ("UPDATE token SET token = %s, expiration_datetime = %s, token_used = %s "
                                       "WHERE user_id = %s")
                update_token_param = (random_token, next_day, 0, user_id)
                cursor.execute(sql_update_token_id, update_token_param)
                db.commit()
            else:
                sql_insert_token = "INSERT INTO token(token, user_id, expiration_datetime) VALUES(%s, %s, %s);"
                token_param = (random_token, user_id, next_day)
                cursor.execute(sql_insert_token, token_param)
                db.commit()

            # Send an email containing the reset password link with the token
            reset_password_link = url_for('reset_password', token=random_token, _external=True)

            # Render the template with the user's name and the verification code
            html_content = render_template('password-change.html', user_name=user_name,
                                           verification_code=verification_code, reset_link=reset_password_link)

            # print(f"HTML CONTENT: {html_content}")

            # Create a multipart message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Blog Reset Password'
            msg['From'] = EMAIL
            msg['To'] = user_email
            # print(f"msg: {msg}")

            # Attach the HTML content to the email
            html_message = MIMEText(html_content, 'html')
            # print(f"html_message: {html_message}")
            msg.attach(html_message)

            # Image Embedded
            # This example assumes the image is in the current directory
            # fp = open('C:/MyFolder/Python/pythonProject/PMHut-Blog/static/assets/img/pmlogo.png', 'rb')
            fp = open('./static/assets/img/pmlogo.png', 'rb')
            msg_image = MIMEImage(fp.read())
            fp.close()

            # Define the image's ID as referenced in password-change.html
            msg_image.add_header('Content-ID', '<image1>')
            msg_image.add_header('Content-Disposition', 'inline', filename='pmlhutlogo.png')
            msg.attach(msg_image)

            with smtplib.SMTP(SMTP_ADDRESS, port=587) as connection:
                connection.starttls()
                connection.login(EMAIL, EMAIL_PASSWORD)
                connection.sendmail(from_addr=msg['From'], to_addrs=msg['To'], msg=msg.as_string())

            form.email.data = ''

            # return render_template("password-change.html")
            return render_template("reset.html", text="Email sent successfully", form=form)
            # return redirect(url_for('get_all_posts'))
    else:
        return render_template("reset.html", text="Reset Password", form=form)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ChangePassword()
    if request.method == "POST":
        check_token = valid_token(token)
        sql_check_token_used_query = "SELECT token_id, user_id, token_used from token where token = %s"
        cursor.execute(sql_check_token_used_query, [token])
        get_token_data = cursor.fetchone()
        token_id, user_id, token_used = get_token_data
        if check_token and not token_used:
            sql_check_email = "SELECT count(*) FROM user_tab WHERE email = %s"
            cursor.execute(sql_check_email, [form.email.data])
            email_count = cursor.fetchone()
            if email_count[0] > 0:
                if form.new_password.data == form.confirm_password.data:
                    hash_and_salted_password = generate_password_hash(password=form.new_password.data,
                                                                      method='pbkdf2:sha256', salt_length=8)
                    sql_verification_query = "SELECT count(*) FROM user_tab WHERE verification_code = %s"
                    cursor.execute(sql_verification_query, [form.verify.data])
                    verification_count = cursor.fetchone()
                    # print(f"Verification Count: {verification_count}")
                    if verification_count[0] > 0:
                        sql_update_query = "UPDATE user_tab SET password = %s WHERE email = %s;"
                        update_password_param = (hash_and_salted_password, form.email.data)
                        cursor.execute(sql_update_query, update_password_param)

                        sql_update_token_used_query = ("UPDATE token SET token_used = %s "
                                                       "WHERE user_id = (SELECT id FROM USER_tab WHERE email = %s)")
                        update_token_used_param = (1, form.email.data)
                        cursor.execute(sql_update_token_used_query, update_token_used_param)

                        db.commit()
                        flash("Password reset successfully.", 'message')
                        return redirect(url_for('request_reset_password'))

                    else:
                        flash("Verification code is invalid!", 'error')
                else:
                    flash("Passwords do not match - Please re-enter", 'error')
            else:
                flash('Invalid Email: Please enter valid email', 'error')
        elif check_token == 'expire':
            flash('Password reset link has expired.', 'message')
        else:
            flash('Invalid password reset link.', 'error')

    return render_template("change-password.html", text="Change Password", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# ##################################################################################

@app.route('/')
def get_all_posts():
    # TODO: Query the database for all the posts. Convert the data to a python list.
    posts = blog_posts.blog_posts()

    # print(f"Inside Get All Posts - Current UserName: {current_user}")
    # print(f"Inside Posts Get All Posts - Current User Is Authenticated: {current_user.is_authenticated}")
    return render_template("index.html", all_posts=posts, current_user=current_user)


# TODO: Add a route so that you can click on individual posts.
@app.route('/post/<post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = blog_posts.show_blog_post(post_id)[0]
    # print(f"Enter Show_Post: {current_user.id} --- {current_user.author_id}")
    # Only allow logged-in users to comment on posts

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment_param = (current_user.id, current_user.name, form.comment.data, now, post_id)
        sql_insert = ("INSERT INTO comment(user_id, user_name, text, date, post_id) "
                      "values(%s, %s, %s, %s, %s);")
        cursor.execute(sql_insert, new_comment_param)
        db.commit()
        form.comment.data = ''
    # if current_user.is_authenticated:
    sql_comment_count = "SELECT count(*) FROM comment WHERE post_id = %s"
    cursor.execute(sql_comment_count, [post_id])
    comment_count = cursor.fetchone()
    # print(f"Comment Count: {comment_count}")
    if comment_count[0] > 0:

        sql_comment_query = ("SELECT c.id, c.user_id, c.user_name, c.text, c.date, c.post_id, "
                             "( SELECT u.email FROM user_tab AS u WHERE u.id = c.user_id LIMIT 1) AS email "
                             "FROM comment AS c WHERE c.post_id = %s order by c.date desc;")

        cursor.execute(sql_comment_query, [post_id])
        comment_rec = cursor.fetchall()
        # print(f"Comment Rec - {comment_rec}")
        # comment_data = [dict(rec) for rec in comment_rec]  # It will not work as comment table has all columns
        comment_data = [{"id": rec[0], "author_id": rec[1], "author": rec[2], "text": rec[3], "date": rec[4],
                         "post_id": rec[5], "email": rec[6]} for rec in comment_rec]

        return render_template("post.html", post=requested_post, comments=comment_data,
                               form=form, current_user=current_user)

    return render_template("post.html", post=requested_post, form=form, current_user=current_user)


# TODO: add_new_post() to create a new blog post
@restrict_to_admin
@app.route("/new-post", methods=['GET', 'POST'])
def new_blog_post():
    form = BlogPostForm()
    # posts = blog_posts.blog_posts()
    # max_id = {k: max(d[k] for d in posts) for k in posts[0].keys()}["id"]
    if form.validate_on_submit() and request.method == 'POST':

        param = (current_user.id, form.title.data, form.subtitle.data, now, form.body.data, form.author.data,
                 form.img_url.data)
        # print(f"Param in Main New_Blog: {param}")
        blog_posts.new_blog_post(param)
        return redirect(url_for('get_all_posts'))
    else:
        return render_template('make-post.html', form=form)


# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<post_id>', methods=['GET', 'POST'])
@restrict_to_blog_owner
def edit_post(post_id):
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = blog_posts.show_blog_post(post_id)[0]
    # print(requested_post)
    form = BlogPostForm(
        title=requested_post['title'],
        subtitle=requested_post['subtitle'],
        img_url=requested_post['img_url'],
        author=requested_post['author'],
        body=requested_post['body']
    )
    if form.validate_on_submit() and request.method == 'POST':
        param = (form.title.data, form.subtitle.data, form.body.data, form.author.data, form.img_url.data, post_id)
        blog_posts.update_blog_post(param)
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("make-post.html", form=form, is_edit=True)


# TODO: delete_post() to remove a blog post from the database
@app.route("/del-post/<post_id>", methods=['GET', 'DELETE'])
@restrict_to_super_user
def del_post(post_id):
    blog_posts.delete_blog_post(post_id)
    return redirect(url_for('get_all_posts'))


# TODO: delete_comment() to remove a blog post from the database
@app.route("/del-comment/<comment_id>", methods=['GET', 'DELETE'])
@restrict_to_super_user
def del_comment(comment_id):
    sql_comment_query = "SELECT post_id, id FROM comment WHERE id = %s"
    cursor.execute(sql_comment_query, [comment_id])
    post_comment_rec = cursor.fetchone()
    # print(f"Post_comment_rec: {post_comment_rec}")
    post_id, comment_id = post_comment_rec
    # print(f"post_id - comment_id ---- {post_id}--{comment_id}")
    blog_posts.delete_comment(comment_id, post_id)
    # flash(f"page: {request.args.get('page')}, comment_id: {comment_id}")
    return redirect(url_for('show_post', post_id=post_id))


# Below is the code from previous lessons. No changes needed.
@app.route("/about")
def about():
    sql_project_count_rec = "SELECT count(*) FROM project WHERE project_id = %s"
    cursor.execute(sql_project_count_rec, ['PMHUT001'])
    check_project_count = cursor.fetchone()
    if check_project_count[0] > 0:
        sql_about_query = "SELECT project_id, about FROM project WHERE project_id = %s"
        cursor.execute(sql_about_query, ['PMHUT001'])
        project_data = cursor.fetchone()
        project_id, updated_about = project_data
        return render_template('about.html', text=updated_about)
    else:
        return render_template('about.html', text='To be Updated')


# TODO: edit_about() to edit about
@app.route("/edit-about", methods=['GET', 'POST'])
@restrict_to_super_user
def edit_about():
    sql_project_query = ("SELECT id, project_id, project_name, about, last_updated_on FROM project "
                         "WHERE project_id = %s ")
    cursor.execute(sql_project_query, ['PMHUT001'])
    project_rec = cursor.fetchone()
    # print(f"Project Rec: {project_rec}")
    pid, project_id, project_name, project_about, last_update_on = project_rec
    form = AboutForm(project_about=project_about)
    if form.validate_on_submit() and request.method == 'POST':
        sql_project_update_query = "UPDATE project SET about = %s WHERE project_id = %s"
        project_update_param = (form.project_about.data, project_id)
        cursor.execute(sql_project_update_query, project_update_param)
        db.commit()
        return redirect(url_for('about'))

    return render_template('about_update.html', form=form)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        # ##############Render the template with the user's name and the verification code
        html_content = render_template('contact-mail.html', msg_body=message, phone=phone, name=name,
                                       email=email)

        # Create a multipart message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Blog Message'
        msg['From'] = email
        msg['To'] = EMAIL
        # print(f"msg: {msg}")

        # Attach the HTML content to the email
        html_message = MIMEText(html_content, 'html')
        # print(f"html_message: {html_message}")
        msg.attach(html_message)

        # Image Embedded
        # This example assumes the image is in the current directory
        # fp = open('C:/MyFolder/Python/pythonProject/PMHut-Blog/static/assets/img/pmlogo.png', 'rb')
        fp = open('./static/assets/img/pmlogo.png', 'rb')
        msg_image = MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced in password-change.html
        msg_image.add_header('Content-ID', '<image1>')
        msg_image.add_header('Content-Disposition', 'inline', filename='pmlhutlogo.png')
        msg.attach(msg_image)

        with smtplib.SMTP(SMTP_ADDRESS, port=587) as connection:
            connection.starttls()
            connection.login(EMAIL, EMAIL_PASSWORD)
            connection.sendmail(from_addr=msg['From'], to_addrs=msg['To'], msg=msg.as_string())

        return render_template("contact.html", text="Successfully sent your message")
    else:
        return render_template("contact.html", text="Contact Me")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
