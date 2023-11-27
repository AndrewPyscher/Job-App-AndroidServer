from flask import Blueprint, request, session
import psycopg2
import bcrypt
views = Blueprint(__name__, "views")
delimiter = "!@#"
delimiter2 = "$%^"

@views.route("/createUser", methods=["POST"])
def createUser():
    conn = openConnect()
    cursor = conn.cursor()
    data = request.json
    role = data.get('role')
    username = data.get('username')
    password = data.get('password')

    salt = bcrypt.gensalt()
    # get rid of
    hpassword = bcrypt.hashpw(str(password).encode('utf-8'), salt)
    password = hpassword.decode('utf-8')
    
    check = 'SELECT * FROM users WHERE username = %s'
    cursor.execute(check,(username,))
    result = cursor.fetchone()
    
    if result is not None:
        return "Username Already Exists!"
    
    insert = 'INSERT INTO users (role, username, password) VALUES (%s, %s, %s)'
    cursor.execute(insert, (role,username,password))
    conn.commit()
    cursor.close()
    conn.close()
    
    return "Account Created"
        
@views.route('/login', methods=["POST"])
def login():
    conn = openConnect()
    cursor = conn.cursor()
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    check = 'SELECT * FROM users WHERE username = %s '
    cursor.execute(check, (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()    
    # username doesn't exist
    if result is None:
        return "Username or Password is incorrect!"
    
    
    hashed_password = result[3]
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        session['username'] = username
        session['role'] = result[1]
        return "login"
    
    return "Username or Password is incorrect!"
   
@views.route('/verifyLogin', methods=["GET"])
def home():
    if verifyLogin():
        return f"{session.get('username')} is logged in"
    return "Access Denied"


@views.route('/myAccount', methods=["GET"])
def myAccount():
    if not verifyLogin() or session.get('role') != 'applicant':
        return "Access Denied"
    
    conn = openConnect()
    cursor = conn.cursor()
    select = 'SELECT name, address, phone, email, about_me from user_info join users  ON user_info.user_id = users.id WHERE username = %s'
    cursor.execute(select, (session.get('username'),))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    response = ""
    # name address phone email aboutme
    if result:
        for row in result:
            response += str(row) + delimiter
    
    return response


@views.route('/allJobs', methods=["GET"])
def allJobs():
    if not verifyLogin():
        return "Access Denied"
    
    
    active = request.args.get('active')
    if active == 'all':
        active = 'true or active = false'
    
    select = f'''SELECT job_posting.id, job_title, description, salary, type,location
            FROM job_posting JOIN users
            ON job_posting.emloyee_id = users.id
            JOIN employer_info
            ON employer_user_id = users.id
            WHERE active ={active if active != None else True}'''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(select)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response

@views.route('/oneJob', methods=["GET"])
def oneJob():
    if not verifyLogin():
        return "Access Denied"
    #/oneJob?id=<id>
    id = request.args.get('id')

    select = '''SELECT job_posting.id,job_title, description, salary, type,location
            FROM job_posting JOIN users
            ON job_posting.emloyee_id = users.id
            JOIN employer_info
            ON employer_user_id = users.id
            WHERE job_posting.id = %s'''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(select,(id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    response = ""
    print(result)
    if result:
        for row in result:
            response += str(row) + delimiter
    else:
        return "Job doesn't exist"

    return response


@views.route('/activeJob', methods=["GET"])
def activeJob():
    if not verifyLogin():
        return "Access Denied"

    id = request.args.get('id')
    active = request.args.get('active')

    update = 'UPDATE job_posting SET active = %s WHERE id = %s'
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(update, (active,id))
    cursor.close()
    conn.commit()
    conn.close()
    return 'Job updated'



@views.route('/updatePosting', methods=["POST"])
def updatePosting():
    if not verifyLogin():
        return "Access Denied"

    
    id = request.json.get('id')
    active = request.json.get('active')
    salary = request.json.get('salary')
    job_title = request.json.get('job_title')
    description = request.json.get('description')
    type = request.json.get('type')

    update = '''
    UPDATE job_posting 
    SET active = %s, 
    salary = %s,
    job_title = %s,
    description = %s,
    type = %s
    WHERE id = %s'''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(update, (active,salary,job_title,description,type,id))
    cursor.close()
    conn.commit()
    conn.close()
    return 'Job updated'


@views.route('/updateProfile', methods=['POST'])
def updateProfile():
    if not verifyLogin():
        return "Access Denied"
    
   
    id = request.json.get('id')
    address = request.json.get('address')
    about_me = request.json.get('about_me')
    print(address)
    name = request.json.get('name')
    phone = request.json.get('phone')
    email = request.json.get('email')
    
    update = '''
    UPDATE user_info 
    SET address = %s, 
    about_me = %s,
    name = %s,
    phone = %s,
    email = %s
    WHERE id = %s'''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(update, (address, about_me, name, phone, email, id))
    cursor.close()
    conn.commit()
    conn.close()
    return 'Account updated'
    
    
def verifyLogin():
    return 'username' in session 

@views.route('/logout', methods=["GET"])
def logout():
    if verifyLogin():
        session.pop('username', None)
        session.pop('role', None)
        return "You've been signed out"
    
    else:
        return "No one signed in"
    

@views.route("/")
def landing():
    return "Hello World"


def openConnect():
    conn = psycopg2.connect(
    dbname="jobsearch",
    user="postgres",
    password="1",
    host="localhost",
    port="5432"
    )
    return conn  