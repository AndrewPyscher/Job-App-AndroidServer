from flask import Blueprint, request,session
import os
from dotenv import load_dotenv
import psycopg2
import bcrypt

load_dotenv()

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
    
    check = 'SELECT * FROM users WHERE username = %s '
    cursor.execute(check, (username,))
    
    
    result = cursor.fetchone()
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return str(result[0])
        
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
        return str(result[0])
    
    return "Username or Password is incorrect!"

@views.route('/changePassword', methods=['POST'])
def changePassword():
    if not verifyLogin():
        return "Access Denied"
    
    conn = openConnect()
    cursor = conn.cursor()
    username = request.json.get('username')
    password = request.json.get('password')
    salt = bcrypt.gensalt()
    hpassword = bcrypt.hashpw(str(password).encode('utf-8'), salt)
    password = hpassword.decode('utf-8')
    update = '''
    UPDATE users 
    SET password = %s
    WHERE username = %s '''
    cursor.execute(update, (password,username))
    
    cursor.close()
    conn.commit()
    conn.close()
    
    return 'Password changed'
   
@views.route('/verifyLogin', methods=["GET"])
def home():
    if verifyLogin():
        return f"{session.get('username')} is logged in"
    return "Access Denied"


@views.route('/myAccount', methods=["GET"])
def myAccount():
    #or session.get('role') != 'applicant'
    if not verifyLogin():
        return "Access Denied"
    username = session.get('username')
    if(request.args.get('username')):
        username = request.args.get('username')
    
    conn = openConnect()
    cursor = conn.cursor()
    select = 'SELECT user_id, name, address, phone, email, about_me, workhistory, education from user_info join users  ON user_info.user_id = users.id WHERE username = %s'
    cursor.execute(select, (username,))
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
    
    select = f'''SELECT job_posting.id, employer_id, job_title, description, salary, type,location
            FROM job_posting JOIN users
            ON job_posting.employer_id = users.id
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
    select = '''SELECT job_posting.id,job_title, description, salary, type, location
            FROM job_posting JOIN users
            ON job_posting.employer_id = users.id
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
    name = request.json.get('name')
    phone = request.json.get('phone')
    email = request.json.get('email')
    workHistory = request.json.get('workHistory')
    education = request.json.get('education')
    print(id)
    print(address)
    print(about_me)
    print(name)
    print(phone)
    print(email)
    print(workHistory)
    print(education)
    
    update = '''
    UPDATE user_info 
    SET address = %s, 
    about_me = %s,
    name = %s,
    phone = %s,
    email = %s,
    workHistory = %s,
    education = %s
    WHERE user_id = %s'''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(update, (address, about_me, name, phone, email, workHistory, education, id))
    cursor.close()
    conn.commit()
    conn.close()
    return f"id:{id}, address:{address}, about_me:{about_me}, name:{name}, phone:{phone}, email{email}, workhistory:{workHistory}, education{education}"
    
@views.route('/updateEmployer', methods=["POST"])
def updateEmployer():
    if not verifyLogin():
        return "Access Denied"
    
    employer_user_id = request.json.get('employer_user_id')
    location = request.json.get('location')
    company_name = request.json.get('company_name')
    conn = openConnect()
    cursor = conn.cursor()
    
    update = '''
    UPDATE employer_info 
    SET company_name = %s, 
    location = %s
    WHERE employer_user_id = %s'''
    
    cursor.execute(update, (company_name, location, employer_user_id))
    cursor.close()
    conn.commit()
    conn.close()
    return "Employer Updated"


@views.route('/insertRating', methods=["GET"])
def insertRating():
    if not verifyLogin():
        return "Access Denied"
    
    employer_id = request.args.get('employer_id')
    reviewer_id = request.args.get('reviewer_id')
    rating = request.args.get('rating')
    
    
    conn = openConnect()
    cursor = conn.cursor()
    
    delete = 'DELETE FROM ratings WHERE employer_id = %s and reviewer_id = %s'
    
    insert = '''
    INSERT INTO ratings
    (employer_id, reviewer_id, rating)
    VALUES (%s,%s,%s)'''
    cursor.execute(delete, (employer_id, reviewer_id))
    cursor.execute(insert, (employer_id, reviewer_id, rating))
    
    cursor.close()
    conn.commit()
    conn.close()
    
    return "Success"



@views.route('/insertEmployerInfo', methods=["POST"])
def insertEmployerInfo():
    if not verifyLogin():
        return "Access Denied"
    
    employer_user_id = request.json.get('employer_user_id')
    location = request.json.get('location')
    company_name = request.json.get('company_name')
    conn = openConnect()
    cursor = conn.cursor()
    
    insert = '''
    INSERT INTO employer_info 
    (employer_user_id, company_name, location)
    VALUES 
    (%s,%s,%s)
    '''
    
    cursor.execute(insert, (employer_user_id, company_name, location))
    cursor.close()
    conn.commit()
    conn.close()
    return "Employer Updated"

@views.route('/insertUserInfo', methods=["POST"])
def insertUserInfo():
    if not verifyLogin():
        return "Access Denied"
    
    id = request.json.get('id')
    address = request.json.get('address')
    about_me = request.json.get('about_me')
    name = request.json.get('name')
    phone = request.json.get('phone')
    email = request.json.get('email')
    workHistory = request.json.get('workHistory')
    education = request.json.get('education')
    
    insert = ''' 
    INSERT INTO user_info 
    (user_id, address, about_me, name, phone,email, workhistory,education)
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    
    conn = openConnect()
    cursor = conn.cursor()
    cursor.execute(insert, (id, address, about_me, name, phone, email, workHistory, education))
    cursor.close()
    conn.commit()
    conn.close()
    return "Created"




@views.route('/insertApp', methods=["POST"])
def insertApp():
    if not verifyLogin():
        return "Access Denied"
    
    jp_id = request.json.get('jp_id')
    applicant_id = request.json.get('applicant_id')
    message = request.json.get('message')
    conn = openConnect()
    cursor = conn.cursor()
    insert = '''
    INSERT INTO applications 
    (jp_id, applicant_id, message)
    VALUES 
    (%s,%s,%s)'''
    cursor.execute(insert, (jp_id, applicant_id, message))
    cursor.close()
    conn.commit()
    conn.close()
    return "Valid"

@views.route('/companyReviews', methods=["GET"])
def companyReviews():
    if not verifyLogin():
        return "Access Denied"
    
    employer_id = request.args.get('employer_id')
    conn = openConnect()
    cursor = conn.cursor()

    select = 'SELECT rating FROM ratings WHERE employer_id = %s'
    cursor.execute(select, (employer_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response


@views.route('/updateApplication', methods=['POST'])
def updateApp():
    if not verifyLogin():
        return "Access Denied"
    
    conn = openConnect()
    cursor = conn.cursor()
    
    message = request.json.get('message')
    status = request.json.get('status')
    jp_id = request.json.get('jp_id')
    applicant_id = request.json.get('applicant_id')
    
    update = '''
    UPDATE applications 
    SET message = %s, 
    status = %s
    WHERE jp_id = %s and applicant_id = %s'''
    
    cursor.execute(update, (message, status, jp_id, applicant_id))
    conn.commit()
    cursor.close()
    conn.close()
    return "Success"

@views.route('/getUserApp', methods=['GET'])
def getUserApp():
    if not verifyLogin():
        return "Access Denied"
    conn = openConnect()
    cursor = conn.cursor()
    id = request.args.get('id')
    select = 'SELECT status, message FROM applications WHERE applicant_id = %s'
    cursor.execute(select, (id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response
    
@views.route('/getEmployerApp', methods=['GET'])
def getEmployerApp():
    if not verifyLogin():
        return "Access Denied"
    conn = openConnect()
    cursor = conn.cursor()
    id = request.args.get('id')
    select = 'SELECT status, message FROM applications WHERE jp_id = %s'
    cursor.execute(select, (id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response

@views.route('/jobCategory', methods=['GET'])
def jobCategory():
    if not verifyLogin():
        return "Access Denied"
    
    type = request.args.get('type').replace('%20'," ")
    conn = openConnect()
    cursor = conn.cursor()
    select = '''
    SELECT job_posting.id,job_title, description, salary, type, location FROM job_posting
    JOIN users
    ON job_posting.employer_id = users.id
    JOIN employer_info
    ON employer_user_id = users.id
    WHERE type = %s'''
    cursor.execute(select, (type,))

    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response

@views.route('/jobByEmployer', methods=['GET'])
def jobByEmployer():
    if not verifyLogin():
        return "Access Denied"
    
    employer_id = request.args.get('employer_id')
    conn = openConnect()
    cursor = conn.cursor()
    select = '''
    SELECT job_posting.id,job_title, description, salary, type, location FROM job_posting
    JOIN users
    ON job_posting.employer_id = users.id
    JOIN employer_info
    ON employer_user_id = users.id
    WHERE employer_id = %s'''
    cursor.execute(select, (employer_id,))

    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    response = ""
    if result:
        for row in result:
            response += delimiter.join(map(str, row)) + delimiter2
    return response
    
def verifyLogin():
    print(session)
    return 'username' in session 

@views.route('/logout', methods=["GET"])
def logout():
    if verifyLogin():
        session.pop('username', None)
        session.pop('role', None)
        return "You've been signed out"
    
    else:
        return "No one signed in"
    
@views.route('/createJob', methods=['POST'])
def createJob():
    if not verifyLogin():
        return "Access Denied"
    
    conn = openConnect()
    cursor = conn.cursor()

    employer_id = request.json.get('employer_id')
    job_title = request.json.get('job_title')
    description = request.json.get('description')
    salary = request.json.get('salary')
    type = request.json.get('type')
    
    update = '''
    INSERT INTO job_posting
    (employer_id, job_title, description, salary,type) 
    VALUES
    (%s, %s, %s, %s, %s)
    '''
    
    cursor.execute(update, (employer_id, job_title, description, salary, type))
    conn.commit()
    cursor.close()
    conn.close()
    return "Success"
    

@views.route("/")
def landing():
    return "Hello World"


def openConnect():
    print(os.getenv('DBUSER'))
    conn = psycopg2.connect(
    dbname=os.getenv('DBNAME'),
    user=os.getenv('DBUSER'),
    password=os.getenv('PASSWORD'),
    host=os.getenv('HOST'),
    port=os.getenv('PORT')
    )
    return conn  