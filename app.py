from pymongo import MongoClient,errors
from bson import ObjectId
from flask import Flask,render_template,jsonify,request,redirect,session,url_for,send_file,abort
from flask_cors import CORS
import random,string,json,os,bcrypt,shutil,fpdf,pytz,requests,uuid,threading,asyncio,concurrent.futures,secrets,io
from functools import wraps 
from datetime import datetime
from telegram import Bot
from telegram.error import NetworkError,TelegramError
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class TelegramBot():
    def __init__(self):
        self.machine = Bot(token='7859503017:AAFULHzznwYDvL72FH5z2ks6lsQ_hKiynoE')
        #self.CHAT_ID = '1874749450'

    async def send_info(self,message):
        chat_id = '1874749450'
        await self.machine.send_message(
            chat_id= chat_id,
            text= message
        )

chelsea = TelegramBot()

timezone = pytz.timezone('Africa/Nairobi')

app = Flask(__name__)
CORS(app) #allows the frontend to access backend

app.secret_key = 'strongkey'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdOCworAAAAAFX42UjmQFFkYMK5j0lwRGGCmb29'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdOCworAAAAALs-ma14ePDiI8ojLZARiLSEDxKX'

client = MongoClient('localhost',27017)

@app.route('/<lang>/')
def index(lang):
    if lang not in ['en', 'sw']:
        lang = 'en'  # Default language
    return render_template(f'index_{lang}.html')

def load_json():
    with open('static/assets/transaction_ids.json','r') as f:
        return json.load(f) 

def save_json(data):
    with open('static/assets/transaction_ids.json','w') as f:
        json.dump(data,f,indent=4)        

def create_id():
    code = "".join([random.choice(string.digits) for _ in range(6)])
    codes = load_json()
    if code not in codes:
        codes.append(code)
        save_json(codes)
        return code
    else:
        create_id()

def send_email(rec_email,message,code,username):
    GMAIL_USER = 'fmspoint@gmail.com'
    password = 'zcdq aahw thfj usfm'
    

    server = SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(GMAIL_USER,password)

    msg = MIMEMultipart()
    if message == 1:
        msg['Subject'] = 'FMSPOINT Verification'

    elif message == 2:
        msg['Subject'] = 'Welcome to FMSPoint' 

    elif message == 3:
        msg['Subject'] = 'New Login Detected in your FMS Account'  

    elif message == 4:
        msg['Subject'] = 'Reset Codes'        

    msg['From'] = 'FMSPoint <services@fmspoint.site>'
    msg['To'] = rec_email

    if message == 1:
        with open('static/messages/register.html','r',encoding='utf-8') as f:
            body = f.read().format(code=code,username=username)
            

    elif message == 2:
        with open('static/messages/welcome.html','r',encoding='utf-8') as f:
            body = f.read().format(dashboard_url=code,username=username) 

    elif message == 3:
        login_time = code[0]
        device = code[1]
        with open('static/messages/login_detected.html','r',encoding='utf-8') as f:
            body = f.read().format(login_time=login_time,device_info=device,username=username,user_email=rec_email)        

    elif message == 4:      
        with open('static/messages/resetpass.html','r',encoding='utf-8') as f:
            body = f.read().format(username=username,code=code) 

    msg.attach(MIMEText(body,'html'))

    server.send_message(msg)
    server.quit()


def code_gen():
    return "".join([random.choice(string.digits) for _ in range(6)])

def login_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if 'verified' not in session:
            return redirect(url_for('login'))
        else:
            return f(*args,**kwargs) 
    return wrapper 

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def admin_required(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if 'verified' not in session or 'is_admin' not in session:
            return redirect(url_for('login'))
        else:
            return f(*args,**kwargs) 
    return wrapper

@app.route('/')
def home():
    try:
        session.pop('verified')
        session.pop('ip_adress')
    except KeyError:
        pass    
    return render_template('index.html')

@app.route('/login')
def login():
    try:
        session.pop('verified')
        session.pop('ip_adress')
    except KeyError:
        pass    
    return render_template('login.html')

@app.route('/logout',methods=['GET'])
def logout():
    session.pop('verified')
    session.pop('ip_adress')
    return redirect(url_for('home'))


@app.route('/verify_credentials', methods=['POST'])
def verify_credentials():
    data = request.get_json()
    
    captcha_response = data.get('recaptchaResponse')
    
    secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
    try:
        captcha_verification = requests.post("https://www.google.com/recaptcha/api/siteverify", data={
            'secret': secret_key,
            'response': captcha_response
        })
  
        captcha_result = captcha_verification.json()

        if not captcha_result.get('success'):
            return jsonify({'error': 'CAPTCHA verification failed', 'permitted': False})
    except Exception as e:
        return str(e)       
        
    username = data.get('username').strip()
    password = data.get('password').encode('utf-8')

    credentials = client.credentials.logins 
    details = credentials.find_one({'username': username})
    if not details:
        return jsonify({'error': 'Account set not found', 'permitted': False})
    
    hashedpassword = details.get('password').encode('utf-8')
    is_blocked = details.get('is_blocked')
    is_admin = details.get('is_admin')
    if not bcrypt.checkpw(password, hashedpassword):
        return jsonify({'error': 'Wrong Username or Password', 'permitted': False})
    
    if is_blocked:
        return jsonify({'error':'Your account is blocked please contact support','permitted':False})
    
    session['db_name'] = username
    session['ip_adress'] = request.headers.get('X-Forwarded-For', request.remote_addr)
    session['verified'] = username
    if is_admin:
        session['is_admin'] = username

    send_login_alert(username)
    
    return jsonify({"error": None,'permitted': True,'is_admin':is_admin})    

def send_login_alert(username):
    email = client.credentials.logins.find_one({'username':username}).get('email')
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = request.user_agent.platform or "Unknown Device"

    info = [login_time,device]

    message=3
    #rec_email,message,code,username
    email_thread = threading.Thread(target=send_email , args=(email,message,info,username))
    email_thread.start()


def check_ip(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        if request.headers.get('X-Forwarded-For', request.remote_addr) != session.get('ip_adress'):
            return redirect(url_for('logout'))
        else:
            return f(*args,**kwargs)
        
    return wrapper

@app.route('/get_sitekey',methods=['GET'])
def get_sitekey():
    key = app.config['RECAPTCHA_PUBLIC_KEY']
    return jsonify({'key':key})

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('main.html')

@app.route('/add_member_temp',methods=['GET'])
@login_required
@check_ip
def add_member_temp():
    return render_template('add.html')

@app.route('/record_temp',methods=['GET'])
@login_required
@check_ip
def record_temp():
    return render_template('record.html')

@app.route('/access_temp',methods=['GET'])
@login_required
@check_ip
def access_temp():
    return render_template('access.html')

@app.route('/message_templates',methods=['GET'])
@login_required
@check_ip
def message_templates():
    return render_template('message_templates.html')

@app.route('/register',methods=['GET'])
def register():
    return render_template('create_account.html')

@app.route('/sms_system',methods=['GET'])
@login_required
@check_ip
def sms_system():
    return render_template('sms_system.html')

@app.route('/reset_password',methods=['GET'])
def reset_password():
    return render_template('reset_password.html')

@app.route('/send_reset_codes',methods=['POST'])
def send_codes():
    data = request.get_json()
    email = data.get('email')
    codes = code_gen()

    if '@' not in email:
        return jsonify({'error': 'Wrong Email Format'})

    checker = client.credentials.logins.find_one({'email':email})
    if not checker:
        return jsonify({'error': 'User not found'})
    
    code = client.credentials.codes
    username = checker.get('username')
    obj = {
        "email": email,
        "username":  username,
        "codes": codes
    }

    session['email_for_reset'] = email
    code.find_one_and_delete({'email': email})
    code.insert_one(obj)
    
    username = checker.get('username')
    message = 4
    email_thread = threading.Thread(target=send_email, args=(email,message,codes,username))
    email_thread.start()

    return jsonify({'message': 'Email sent successfully'})

@app.route('/verify_reset_codes',methods=['POST'])
def verify_reset_codes():
    data = request.get_json()
    user_code = str(data.get('enteredCode'))

    if 'email_for_reset' not in session:
        return jsonify({'error': 'Code Expired please request another code again'})
    
    email = session.get('email_for_reset')
    gen_code =  client.credentials.codes.find_one({'email':email}).get('codes')
    if str(gen_code) == user_code:
        session['email_resetted'] = email
        return jsonify({'message':'Valid verification code'})   
    else:
        return jsonify({'error':'Invalid verification code'})

@app.route('/update_password',methods=['POST'])
def update_password():
    if 'email_resetted' not in session:
        return jsonify({'error': 'False Attempt'})
    
    try:
        data = request.get_json()
        
        password = data.get('password').encode('utf-8')
        #print(password)
        email = session['email_resetted']

        salt = bcrypt.gensalt()
        hashp = bcrypt.hashpw(password,salt).decode('utf-8')

        client.credentials.logins.update_one({'email':email},{'$set':{'password':hashp}})
        return jsonify({'message': 'Password Changed Successfully'})

    except Exception as e:
        return  jsonify({'error': str(e)})  


@app.route('/register_user',methods=['POST'])
def register_user():
    data = request.get_json()
    fullName = data.get('FullName')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password2')
    license = data.get('license')
    captcha_response = data.get('recaptchaResponse')
    
    secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
    try:
        captcha_verification = requests.post("https://www.google.com/recaptcha/api/siteverify", data={
            'secret': secret_key,
            'response': captcha_response
        })
  
        captcha_result = captcha_verification.json()

        if not captcha_result.get('success'):
            return jsonify({'error': 'CAPTCHA verification failed, Verify or Reload', 'permitted': False})
    except Exception as e:
        return str(e)       

    db = client.credentials.licenses
    checker = db.find_one({'license_key':license})

    if not checker:
        return jsonify({'error': 'Invalid License Key'})
    
    temp_db = client["temporary"]["temp_acc"]

    if temp_db.find_one({'email':email}):
        temp_db.delete_one({'email':email})

    password = password.encode('utf-8')  

    salt = bcrypt.gensalt()
    hashp = bcrypt.hashpw(password,salt).decode('utf-8')  

    temp_person = {
        "fullname": fullName,
        "username": username,
        "email": email,
        "password": hashp,
        "license": license,
        "is_blocked": False,
        "is_admin": False
    }

    temp_db.insert_one(temp_person)
    
    key = checker.get('license_key')
    used = checker.get('status')

    if used == 'used' or used== 'revoked':
        return jsonify({'error': 'License Key has already been used'})
    
    if client.credentials.logins.find_one({'email':email}):
        return jsonify({'error':'This email has already been used by another user please try again by using another email'})
    
    if client.credentials.logins.find_one({'username':username}):
        return jsonify({'error':'This username has already been used by another user please try again by using another username'})
    
    message = 1
    codes = code_gen()
    email_thread = threading.Thread(target=send_email , args=(email,message,codes,username))
    email_thread.start()

    code = client.credentials.codes
    
    obj = {
        "email": email,
        "username":  username,
        "codes": codes
    }

    session['email'] = email
    code.find_one_and_delete({'email': email})
    code.insert_one(obj)

    return jsonify({'permit': True })

@app.route('/resendcodes',methods=['GET'])
def resendcodes():
    if 'email' not in session:
        return jsonify({'error':'Session expired, sign up newly again'})
    email = session['email']
    verifier = client.credentials.codes
    saved = verifier.find_one({"email":email})
    if saved:
        message = 1
        codes = saved.get('codes')
        temp_db = client["temporary"]['temp_acc']
        new_acc = temp_db.find_one({'email':email})
        
        if new_acc:
            username = new_acc.get('username')
            email_thread = threading.Thread(target=send_email , args=(email,message,codes,username))
            email_thread.start()
            return jsonify({"message": "CODES have been resent successfully"})
        else:
            return jsonify({"error": "Session expired please create the account newly"})     
    else:
        return jsonify({"error": "Session expired please create the account newly"})

@app.route('/verifier', methods=['GET'])
def verifier():
    return render_template('verify.html')   

@app.route('/verifycodes',methods=['POST'])
def verifycodes():
    data = request.get_json()
    code = data.get('code')
    os.system('cls')
    if 'email' not in session:
        return jsonify({'error':'session expired'})
    
    verifier = client.credentials.codes
    email = session['email']

    saved = verifier.find_one({"email":email})
    if saved:
        codes = saved.get('codes')
        if codes == code:
            temp_db = client["temporary"]['temp_acc']
            new_acc = temp_db.find_one({'email':email})
            if new_acc:
                client.credentials.logins.insert_one(new_acc)
                username = new_acc.get('username')
                license =  new_acc.get('license')
                templates = client[username]['message_templates']

                smsystem = client[username]['sms_system']

                lic_info = {
                    'license_key': license,
                    'status': 'used',
                    'usedBy': username
                }

                client.credentials.licenses.delete_one({'license_key': license})
                client.credentials.licenses.insert_one(lic_info)

                temp_sms = {
                    "bado_anadaiwa": "Shalom {name}, tumepokea {payment_type} ya {amount:,} kama mchango wako kwa {person}. Umeshalipa jumla ya {amount_paid:,}, deni lako bado ni {amount_debt:,}. Tunathamini mchango wako mkubwa Mungu akubariki.",
                    "amelipa_yote": "Shalom {name}, tumepokea {payment_type} ya {amount:,} kama mchango wako kwa shughuli ya {person}. Umeshalipa jumla kiasi cha {amount_paid:,} Tunakushukuru umemaliza deni lako, Mungu akubariki.",
                    "fedha_taslimu": "Shalom {name}, tunakushukuru tumepokea fedha taslimu kiasi cha shillingi {cash:,} ,ikiwa ni mchango wako kwaajili ya shughuli ya {person}, Mungu akubariki sana.",
                    "ahadi_tu": "Shalom {name}, tunakushukuru tumepokea ahadi yako ya shillingi {ahadi:,} itakayotusaidia kufanikisha shughuli ya {person}, Mungu akubariki sana.",
                    "fedha_na_ahadi": "Shalom ndugu {name} tunakushukuru kwa mchango wako tumepokea fedha taslimu kiasi cha shillingi {cash:,} na ahadi ya shillingi {ahadi:,} inayoleta jumla ya shilingi {total:,} kwa ajili ya kufanikisha shughuli ya {person}, Mungu akubariki sana.",
                    "kumbusha_deni": "Habari {name}, tafadhali kumbuka kukamilisha ahadi yako ya {debt_amount:,} kwa ajili ya mchango."
                }

                sms_info = {
                    'balance': 0,
                    'templates': len(temp_sms),
                    'sent_sms_count': 0,
                    'delivered_sms_count': 0
                }

                smsystem.insert_one(sms_info)

                templates.insert_one(temp_sms)
                templates.insert_one({"SENDER_IDS":['MICHANGO','SENDOFF','KIKAO','HARUSI']})

                temp_db.delete_one({'email':email})
                verifier.delete_one({"codes":codes})

                message = 2
                dashboard_url = 'https://fmspoint.site/dashboard'
                email_thread = threading.Thread(target=send_email, args=(email,message,dashboard_url,username))
                email_thread.start()

                return jsonify({"message":"Account has been created successfully"})
            else:
                return jsonify({"error": "Session expired please create the account newly"})
        else:
            return jsonify({"error": "The entered code does not match"})
    else:
        return jsonify({"error": "Kindly request the codes newly again"})
  

def get_db(code):
    if 'db_name' not in session:
        raise AttributeError("Session has expired or is missing 'db_name'.")
    
    db = client[session['db_name']]
    if code == 1:
        return db["wanakamati"],db["transaction"]
    elif code == 2:
        return db


@app.route('/add_member',methods = ['POST'])
@login_required
@check_ip
def add_member():
    data = request.json    
    transaction_id = create_id()
    wanakamati,transaction= get_db(1)
     
    try:
        wanakamati.create_index('name',unique=True,name='name_1')
        wanakamati.create_index('phone',name='phone_1')

        new_member = {
            "id" : ("".join(data['name'].split(' '))).lower(),
            "name" : data['name'],
            "phone" : data['phoneNumber'],
            "promise_amount" : int(data['promise_amount']),
            "cash_amount": int(data['cash_amount']),
            "paid_amount": int(data['cash_amount']),
            "debt_amount": int(data['promise_amount']),
            "addition_amount": 0,
            "date": data['date']
        }

        phone = data['phoneNumber']
        if list(wanakamati.find({'phone':phone})) != [] and phone != None:
            return jsonify({'error': "Namba hizi zimeshatumika na mchangiaji mwingine tafadhali badilisha"})
        
        wanakamati.insert_one(new_member)       

        if int(data['cash_amount']) > 0:
            trans = {
                "id": transaction_id,
                "name": data['name'],
                "date": data['date'],
                "paymentType": 'cash',
                "amount": int(data['cash_amount'])
            }
            transaction.insert_one(trans)

        if int(data['promise_amount']) > 0:
            trans = {
                "id": transaction_id,
                "name": data['name'],
                "date": data['date'],
                "paymentType": 'ahadi',
                "amount": int(data['promise_amount'])   
            }           
            transaction.insert_one(trans) 

        try:
            tg_message = f"Mchangiaji mpya mwenye \nJina: {data['name']}, \nNamba za simu: {data['phoneNumber']}, \nAhadi: {data['promise_amount']}\nCash: {data['cash_amount']}\nTarehe: {data['date']}\nAmeongezwa kutoka IP ADDRESS: {request.headers.get('X-Forwarder-For',request.remote_addr)}"  
            asyncio.run(chelsea.send_info(tg_message))
        except NetworkError:
            pass
        except TelegramError:
            pass    

        return jsonify({"message": "Mchangiaji ameongezwa kwa mafanikio"})
    except errors.OperationFailure:
        return jsonify({f"error": "Mchangiaji mwenye hizi namba au Jina tayari yumo tafadhali tumia jina au namba  zingine"})  
    except AttributeError:
        return redirect(url_for('logout'))  
    except:
        return redirect(url_for('logout'))
    

@app.route('/get_summary',methods=['POST'])  
@login_required
@check_ip  
def get_summary():
    try:    
        wanakamati,transaction= get_db(1)
        total_paid = 0
        total_promise = 0
        total_debt = 0
        total_addition = 0
        data = list(wanakamati.find({},{"_id":False})) 
        for datum in data:
            total_paid += datum['paid_amount']
            total_promise += datum['promise_amount']
            total_debt += datum['debt_amount']
            total_addition += datum['addition_amount']
        total_money = total_debt + total_paid    
        return jsonify({
            "totalPaid": total_paid,
            'totalDebt' : total_debt,
            'totalAdditional': total_addition,
            'totalCollection' : total_money 
            })    
    except KeyError as e:
        return jsonify({'error': str(e)})
    except ValueError as e:
        return jsonify({'error': str(e)})
    except IndexError as e:
        return jsonify({'error': str(e)})
    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/get_members',methods=['POST'])
@login_required
@check_ip
def get_members():
    body = request.json
    
    try:
        wanakamati,transaction= get_db(1)
        if body.get('sortby') == 'default':
            query = list(wanakamati.find({},{"_id":False}))  
            return jsonify(query)
        elif body.get('sortby') == 'AK':
            query = list(wanakamati.find({},{"_id":False}).sort({'promise_amount':-1}))  
            return jsonify(query)
        elif body.get('sortby') == 'CK':
            query = list(wanakamati.find({},{"_id":False}).sort({'paid_amount':-1}))  
            return jsonify(query)
        elif body.get('sortby') == 'DK':
            query = list(wanakamati.find({},{"_id":False}).sort({'debt_amount':-1}))  
            return jsonify(query)
        elif body.get('sortby') == 'AN':
            query = list(wanakamati.find({},{"_id":False}).sort({'promise_amount':1}))  
            return jsonify(query)
        elif body.get('sortby') == 'CN':
            query = list(wanakamati.find({},{"_id":False}).sort({'paid_amount':1}))  
            return jsonify(query)
        elif body.get('sortby') == 'DN':
            query = list(wanakamati.find({},{"_id":False}).sort({'debt_amount':1}))  
            return jsonify(query)
        elif body.get('sortby') == 'AA':
            query = list(wanakamati.find({},{"_id":False}).sort({'name':1}))  
            return jsonify(query)
        elif body.get('sortby') == 'AZ':
            query = list(wanakamati.find({},{"_id":False}).sort({'name':-1}))  
            return jsonify(query)
    except AttributeError:
        return redirect(url_for('logout'))   

@app.route('/record_transaction',methods=['POST'])
@login_required
@check_ip
def record_transaction():
    code = create_id()
    data = request.json
    idd = ("".join(data.get('memberName').split(' '))).lower()
    paymentType = data['paymentType']
    date = data['date']
    amount = int(data['amount'])
    checker1 = False
    checker2 = False

    try:
        wanakamati,transaction= get_db(1)
        if idd.isdigit():
            checker1 = wanakamati.find_one({"phone": idd})
            
        else:
            checker2 = wanakamati.find_one({"id": idd})

        if checker2:
            name = checker2['name']
            promise_amount = checker2['promise_amount']
            paid_amount = checker2['paid_amount']
            debt_amount = checker2['debt_amount']

            if paymentType == 'cash':
                debt_amount = debt_amount - amount
                paid_amount  = paid_amount  + amount
                wanakamati.update_one({"id": idd},{"$set":{"debt_amount": debt_amount,"paid_amount":paid_amount}}) 

                checker2 = wanakamati.find_one({"id": idd})   
                debt_amount = checker2['debt_amount']
                addition_amount = checker2['addition_amount']

                if debt_amount < 0:
                    addition_amount = addition_amount + (debt_amount * -1)
                    wanakamati.update_one({"id": idd},{"$set":{"debt_amount": 0,"addition_amount":addition_amount}})

            elif paymentType == 'ahadi':
                promise_amount = promise_amount + amount
                debt_amount = debt_amount + amount  
                wanakamati.update_one({"id": idd},{"$set":{"debt_amount": debt_amount ,"promise_amount": promise_amount }}) 

                checker2 = wanakamati.find_one({"id": idd})
                debt_amount = checker2['debt_amount']
                addition_amount = checker2['addition_amount']
                if addition_amount > 0:
                    if debt_amount >  addition_amount:
                        debt_amount = debt_amount - addition_amount
                        wanakamati.update_one({"id": idd},{"$set":{"debt_amount": debt_amount,"addition_amount":0}})
                    else:
                        addition_amount = addition_amount - debt_amount
                        wanakamati.update_one({"id": idd},{"$set":{"debt_amount": 0,"addition_amount":addition_amount}}) 
                    


            transaction.insert_one({ "id": code ,"name": name, "date": date, "paymentType":paymentType, "amount": amount})             

            try:
                tg_message = f"Muamala mpya umerecordiwa\nJina: {name}\nPayment Type: {paymentType}\nCash: {paid_amount}\nAhadi: {promise_amount}\nDeni: {debt_amount} \ntarehe:{data['date']}\nAmeongezwa kutoka IP ADDRESS: {request.headers.get('X-Forwarder-For',request.remote_addr)}"   
                asyncio.run(chelsea.send_info(tg_message))
            except NetworkError:
                pass
            except TelegramError:
                pass     

            return jsonify({'message': "Muamala umefanyika kikamilifu"})      

        elif checker1:   
            name = checker1['name']
            promise_amount = checker1['promise_amount']
            paid_amount = checker1['paid_amount']
            debt_amount = checker1['debt_amount']  

            if paymentType == 'cash':
                debt_amount = debt_amount - amount
                paid_amount  = paid_amount  + amount 
                wanakamati.update_one({"phone": idd},{"$set":{"debt_amount": debt_amount,"paid_amount":paid_amount}}) 

                checker1 = wanakamati.find_one({"phone": idd})  
                paid_amount = checker1['paid_amount']
                debt_amount = checker1['debt_amount']
                addition_amount = checker1['addition_amount']

                if debt_amount < 0:
                    addition_amount = (debt_amount * -1)
                    wanakamati.update_one({"phone": idd},{"$set":{"debt_amount": 0,"addition_amount":addition_amount}}) 

            elif paymentType == 'ahadi':
                promise_amount = promise_amount + amount
                debt_amount = debt_amount + amount  
                wanakamati.update_one({"phone": idd},{"$set":{"debt_amount": debt_amount,"promise_amount": promise_amount }})  

                checker1 = wanakamati.find_one({"phone": idd})
                debt_amount = checker1['debt_amount']
                addition_amount = checker1['addition_amount']
                if addition_amount > 0:
                    if debt_amount >  addition_amount:
                        debt_amount = debt_amount - addition_amount
                        wanakamati.update_one({"phone": idd},{"$set":{"debt_amount": debt_amount,"addition_amount":0}})
                    else:
                        addition_amount = addition_amount - debt_amount
                        wanakamati.update_one({"phone": idd},{"$set":{"debt_amount": 0,"addition_amount":addition_amount}})      

            transaction.insert_one({ "id": code ,"name": name, "date": date, "paymentType":paymentType, "amount": amount}) 

            try:
                tg_message = f"Muamala mpya umerecordiwa\nJina: {name}\nPayment Type: {paymentType}\nCash: {paid_amount}\nAhadi: {promise_amount}\nDeni: {debt_amount} \ntarehe:{data['date']}\nAmeongezwa kutoka IP ADDRESS: {request.headers.get('X-Forwarder-For',request.remote_addr)}"   
                asyncio.run(chelsea.send_info(tg_message))
            except NetworkError:
                pass
            except TelegramError:
                pass     

            return jsonify({'message': "Muamala umefanyika kikamilifu"})    

        else:
            return jsonify({"error": "Mchangiaji hayupo tafadhali ingiza taarifa kwa usahihi"}),400  

    except AttributeError:
        return redirect(url_for('logout'))      

@app.route('/get_transactions',methods=['POST'])
@login_required
@check_ip
def get_transactions():
    body = request.json
    try:
        wanakamati,transaction= get_db(1)
        if body.get('sortby') == 'default':
            data = list(transaction.find({},{"_id": False}))
            return jsonify(data)
        elif body.get('sortby') == 'AK':
            data = list(transaction.find({},{"_id": False}).sort({'paymentType':1}))
            return jsonify(data)  
        elif body.get('sortby') == 'CK':
            data = list(transaction.find({},{"_id": False}).sort({'paymentType':-1}))
            return jsonify(data) 
        elif body.get('sortby') == 'KN':
            data = list(transaction.find({},{"_id": False}).sort({'amount': 1}))
            return jsonify(data) 
        elif body.get('sortby') == 'KK':
            data = list(transaction.find({},{"_id": False}).sort({'amount': -1}))
            return jsonify(data) 
        elif body.get('sortby') == 'AA':
            data = list(transaction.find({},{"_id": False}).sort({'name': 1}))
            return jsonify(data) 
        elif body.get('sortby') == 'AZ':
            data = list(transaction.find({},{"_id": False}).sort({'name': -1}))
            return jsonify(data) 
    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/editTransaction',methods=['POST'])
@login_required
@check_ip
def editTransaction():
    data = request.json
    code = data['trans_id']
    newName = data['memberName']
    name = data['formerName']
    newAmount = int(data['amount'])
    newpaymentType = data['paymentType']
    newDate = data['date']
    formerAmount = int(data['formerAmount'])
    formerpaymentType = data['formerpaymentType']

    try:
        wanakamati,transaction= get_db(1)
        if transaction.find_one({"id": code}):
            former_wanakamati = wanakamati.find_one({'name': name})
            new_mwanakamati = wanakamati.find_one({'name': newName})
            if former_wanakamati and new_mwanakamati:
                if formerpaymentType == 'ahadi':
                    former_wanakamati['promise_amount'] = former_wanakamati['promise_amount'] - formerAmount
                    former_wanakamati['debt_amount'] = former_wanakamati['debt_amount'] - formerAmount
                    wanakamati.update_one({'name': name},{"$set":{ "promise_amount": former_wanakamati['promise_amount'] , "debt_amount": former_wanakamati['debt_amount']}})

                    former_wanakamati = wanakamati.find_one({'name': name})
                    if former_wanakamati['addition_amount'] > 0:
                        if former_wanakamati['debt_amount'] > former_wanakamati['addition_amount']:
                            former_wanakamati['debt_amount'] = former_wanakamati['debt_amount'] - former_wanakamati['addition_amount']
                            wanakamati.update_one({'name': name},{"$set":{ "promise_amount": former_wanakamati['promise_amount'] , "debt_amount": former_wanakamati['debt_amount'], "addition_amount": 0}})
                        else:
                            former_wanakamati['addition_amount'] = former_wanakamati['addition_amount'] -  former_wanakamati['debt_amount']
                            wanakamati.update_one({'name': name},{"$set":{ "promise_amount": former_wanakamati['promise_amount'] , "debt_amount": 0, "addition_amount": former_wanakamati['addition_amount']}})

                    
                    
                    new_mwanakamati = wanakamati.find_one({'name': newName})
                    if formerpaymentType == newpaymentType:
                    
                        new_mwanakamati['promise_amount'] = new_mwanakamati['promise_amount'] + newAmount
                        new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] + newAmount
                        wanakamati.update_one({'name': newName},{ "$set": {"promise_amount": new_mwanakamati['promise_amount'], "debt_amount": new_mwanakamati['debt_amount'] } })

                        new_mwanakamati = wanakamati.find_one({'name': newName})
                        if new_mwanakamati['addition_amount'] > 0:
                            if new_mwanakamati['debt_amount'] > new_mwanakamati['addition_amount']:
                                new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] - new_mwanakamati['addition_amount']
                                wanakamati.update_one({'name': newName},{ "$set": {"addition_amount": 0, "debt_amount": new_mwanakamati['debt_amount'] } })
                            else:
                                new_mwanakamati['addition_amount'] = new_mwanakamati['addition_amount'] - new_mwanakamati['debt_amount']
                                wanakamati.update_one({'name': newName},{ "$set": {"addition_amount": new_mwanakamati['addition_amount'], "debt_amount": 0} })


                    else:
                        new_mwanakamati['paid_amount'] = new_mwanakamati['paid_amount'] + newAmount
                        new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] - newAmount
                        wanakamati.update_one({'name': newName},{'$set': { 'paid_amount': new_mwanakamati['paid_amount'] , 'debt_amount':new_mwanakamati['debt_amount'] }})

                        new_mwanakamati = wanakamati.find_one({'name': newName})
                        if new_mwanakamati['debt_amount'] < 0:
                            new_mwanakamati['addition_amount'] = new_mwanakamati['addition_amount'] + (new_mwanakamati['debt_amount'] * -1)
                            wanakamati.update_one({'name': newName},{'$set': { 'addition_amount': new_mwanakamati['addition_amount'] , 'debt_amount':0 }})
                                        

                elif formerpaymentType == "cash":
                    former_wanakamati['paid_amount'] = former_wanakamati['paid_amount'] - formerAmount
                    former_wanakamati['debt_amount'] = former_wanakamati['debt_amount'] + formerAmount

                    wanakamati.update_one({'name': name},{"$set":{ "paid_amount": former_wanakamati['paid_amount'] , "debt_amount": former_wanakamati['debt_amount']}})

                    former_wanakamati = wanakamati.find_one({'name': name})

                    if former_wanakamati['debt_amount'] < 0:
                        former_wanakamati['addition_amount'] = former_wanakamati['addition_amount'] + (former_wanakamati['debt_amount'] * -1)
                        wanakamati.update_one({'name': name},{"$set":{ "addition_amount": former_wanakamati['addition_amount'] , "debt_amount": 0}})

                    new_mwanakamati = wanakamati.find_one({'name': newName})

                    if formerpaymentType == newpaymentType:
                        new_mwanakamati['paid_amount'] = new_mwanakamati['paid_amount'] + newAmount
                        new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] - newAmount

                        wanakamati.update_one({'name': newName},{ "$set": {"paid_amount": new_mwanakamati['paid_amount'], "debt_amount": new_mwanakamati['debt_amount'] } })   

                        new_mwanakamati = wanakamati.find_one({'name': newName})

                        if new_mwanakamati['debt_amount'] < 0:
                            new_mwanakamati['addition_amount'] = new_mwanakamati['addition_amount'] + (new_mwanakamati['debt_amount'] * -1)
                            wanakamati.update_one({'name': newName},{"$set":{ "addition_amount": new_mwanakamati['addition_amount'] , "debt_amount": 0}})

                    else:
                        new_mwanakamati['promise_amount'] = new_mwanakamati['promise_amount'] + newAmount
                        new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] + newAmount
                        wanakamati.update_one({'name': newName},{ "$set": {"promise_amount": new_mwanakamati['promise_amount'], "debt_amount": new_mwanakamati['debt_amount'] } })      

                        new_mwanakamati = wanakamati.find_one({'name': newName})
                        if new_mwanakamati['addition_amount'] > 0:
                            if new_mwanakamati['debt_amount'] > new_mwanakamati['addition_amount']:
                                new_mwanakamati['debt_amount'] = new_mwanakamati['debt_amount'] - new_mwanakamati['addition_amount']
                                wanakamati.update_one({'name': newName},{ "$set": {"addition_amount": 0, "debt_amount": new_mwanakamati['debt_amount'] } })
                            else:
                                new_mwanakamati['addition_amount'] = new_mwanakamati['addition_amount'] - new_mwanakamati['debt_amount']
                                wanakamati.update_one({'name': newName},{ "$set": {"addition_amount": new_mwanakamati['addition_amount'], "debt_amount": 0} })


                transaction.update_one({"id": code},{"$set":{
                    "name": newName,
                    "paymentType": newpaymentType,
                    "date" : newDate,
                    "amount" : newAmount
                }})    

                return jsonify({"message": "Mabadiliko yamefanyika kwa ukamilifu"})
            else:
                return jsonify({"error": "Mabadiliko hayajafanikiwa tafadhali hakikisha Mchangiaji mpya yupo kwenye list"})        
        else:
            return jsonify({"error": "Kumbukumbu namba sio sahihi"})     

    except AttributeError:
        return redirect(url_for('logout'))         

@app.route('/edit_member_info', methods=['POST'])
@login_required
@check_ip
def edit_member_info():
    try:
        data = request.json
    except Exception as e:
        return jsonify({'error': str(e)})    
    name = data.get('name')
    phone = data.get('phone')
    formerName = (data.get('formerName')).strip()
    formerPhone = (data.get('formerPhone'))
    idd = ("".join(formerName.split(' '))).lower()
    newidd = ("".join(name.split(' '))).lower()

    if formerName == name and formerPhone == phone:
        return jsonify({"error": "Taarifa ulizoingiza zinafanana na taarifa za zamani tafadhali badilisha"})

    try:
        wanakamati,transaction= get_db(1)
        #miamala = list(transaction.find({"name": formerName}))
        if wanakamati.find_one({'id':idd}):
            wanakamati.create_index('name',unique=True,name='name_1')
            wanakamati.create_index('phone',name='phone_1')

            if formerPhone == phone:
                try:
                    wanakamati.update_one({'id':idd},{"$set":{"id": newidd , "name": name}})
                    transaction.update_many({'name': formerName},{"$set": {"name": name}})
                    return jsonify({'message': 'Mabadiliko yamefanyika kwa ukamilifu'})
                
                except errors.OperationFailure:
                    return jsonify({"error": "Jina hili limeshatumika na mchangiaji mwingine tafadhali tumia jina lingine"}) 
            else:  
                if wanakamati.find_one({'phone': phone}) is None:
                    if formerName == name:
                        try:
                            wanakamati.update_one({'id':idd},{"$set":{
                                "phone": phone
                            }})
                            return jsonify({'message': 'Mabadiliko yamefanyika kwa ukamilifu'})           
                        except errors.OperationFailure:
                            return jsonify({"error": "Namba hizi zimeshatumika na mchangiaji mwingine tafadhali tumia jina lingine"})
                        
                    else:
                        try:
                            wanakamati.update_one({'id':idd},{"$set":{
                                "id": newidd , "name": name,"phone": phone
                            }})
                            transaction.update_many({'name': formerName},{"$set": {"name": name}})
                            return jsonify({'message': 'Mabadiliko yamefanyika kwa ukamilifu'})
                        except errors.OperationFailure:
                            return jsonify({"error": "Jina hili au namba hizi imeshatumika mchangiaji mwingine tafadhali tumia badilisha"})
                else:
                    return jsonify({"error": "Namba hizi zimeshatumika na mchangiaji mwingine tafadhali tumia namba zingine"})
        else:
            return jsonify({'error':'Taarifa za mwanzo hazipo'})             

    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/delete_user',methods=['POST'])
@login_required
@check_ip
def delete_user():
    data = request.json
    name = data.get('formerName').strip()
    idd = ("".join(name.split(' '))).lower()
    try:
        wanakamati,transaction= get_db(1)
        finder = wanakamati.find_one({"id":idd})
        if finder:
            transaction_name = finder.get('name')
            if wanakamati.delete_one({"id":idd}) and transaction.delete_many({'name':transaction_name}):
                return jsonify({'message': "Mchangiaji amefutwa kwenye mfumo kikamilifu"})
            else:
                return jsonify({'error': "Mchangiaji hajafutwa kwenye mfumo"})
        else:
            return jsonify({'error': "Mchangiaji hayupo kwenye mfumo"})   
    except AttributeError:
        return redirect(url_for('logout'))      
        

@app.route('/delete_transaction',methods=['POST'])
@login_required
@check_ip
def delete_transaction():
    data = request.json
    transaction_id = data.get('trans_id').strip()
    payment_type = data.get('formerpaymentType').strip().lower()
    try:
        wanakamati,transaction= get_db(1)
        details = list(transaction.find({"id": transaction_id}))

        if len(details) > 1:
            
            for detail in details:
                name = detail.get('name').strip()
                paymentType = detail.get('paymentType').strip().lower()
                amount = detail.get('amount')

                if paymentType == payment_type:
                    new_id = transaction_id + 'todelete'
                    transaction.update_one(
                        {"_id": detail["_id"]},  
                        {"$set": {"id": new_id}}  
                    )
                    if paymentType == 'cash':
                        mtu = wanakamati.find_one({'name': name})
                        alicholipa = mtu.get('paid_amount')
                        
                        mtu['paid_amount'] = alicholipa - amount
                        wanakamati.update_one({'name': name},{'$set': {'paid_amount': mtu['paid_amount']}})


                    elif paymentType == 'ahadi':
                        mtu = wanakamati.find_one({'name': name})
                        anachodaiwa = mtu.get('debt_amount')
                        mtu['debt_amount'] = anachodaiwa - amount
                        wanakamati.update_one({'name': name},{'$set': {'paid_amount': mtu['debt_amount']}})

                    transaction.delete_one({'id': new_id})  

            return jsonify({'message': "Muamala umefutwa kikamilifu"})

        else:
            detail = details[0]
            objid = detail.get('_id') 
            jina = detail.get('name')
            payment_method = detail.get('paymentType')
            kiasi = detail.get('amount')

            call = list(transaction.find({'name': jina}) ) 
            if len(call) > 1:
                if payment_method == 'cash':
                    mhusika = wanakamati.find_one({'name': jina})
                    deni = mhusika.get('debt_amount')
                    malipo = mhusika.get('paid_amount')

                    deni = deni + kiasi
                    malipo = malipo - kiasi

                    wanakamati.update_one({'name': jina},{
                        '$set': {"debt_amount": deni , "paid_amount": malipo}
                    })
                    transaction.delete_one({'_id':objid})
                    return jsonify({'message': "Muamala umefutwa kikamilifu"})

                elif payment_method == 'ahadi':
                    mhusika = wanakamati.find_one({'name': jina})
                    deni = mhusika.get('debt_amount')
                    ahadi = mhusika.get('promise_amount')

                    deni = deni - kiasi
                    ahadi = ahadi - kiasi

                    wanakamati.update_one({'name': jina},{
                        '$set': {"debt_amount": deni , "promise_amount": ahadi}
                    })
                    transaction.delete_one({'_id':objid})
                    return jsonify({'message': "Muamala umefutwa kikamilifu"})

            else:
                name = detail.get('name')
                wanakamati.delete_one({'name': name})
                transaction.delete_many({'id': transaction_id}) 
                return jsonify({'message': "Muamala umefutwa kikamilifu"}) 
    except AttributeError:
        return redirect(url_for('logout'))   
    except Exception as e:
        return jsonify({'error': str(e)})    

@app.route('/download_backup',methods=['GET'])
@login_required
@check_ip
def download_backup():
    try:
        db = get_db(2)
        timestamp = datetime.now().strftime('%d-%m-%Y')
        collections = ['wanakamati','transaction']
        for collection in collections:
            if 'db_name' not in session:
                return jsonify({'error': 'Authenication failed'})
            
            data = list(db[collection].find({},{"_id":False}))
            for doc in data:
                doc['_id'] = str(doc['_id'])

            FILE_NAME = f'{timestamp}-{collection}.json'
            os.makedirs(timestamp,exist_ok=True)
            FILE_PATH = os.path.join(timestamp,FILE_NAME) 

            with open(FILE_PATH,'w',encoding=('utf-8')) as f:
                json.dump(data,f,indent=4)

        if os.path.isfile(f'{timestamp}-backup.zip'):
            os.remove(f'{timestamp}-backup.zip')        

        shutil.make_archive(f'{timestamp}-backup','zip',timestamp)
        shutil.rmtree(timestamp)
        return send_file(f'{timestamp}-backup.zip',as_attachment=True) 
    except AttributeError:
        return redirect(url_for('logout'))  

def totals():
    total_paid = 0
    total_promise = 0
    total_debt = 0
    total_addition = 0
    try:
        wanakamati,transaction= get_db(1)
        data = list(wanakamati.find({},{"_id":False})) 
        for datum in data:
            total_paid += datum['paid_amount']
            total_promise += datum['promise_amount']
            total_debt += datum['debt_amount']
            total_addition += datum['addition_amount']
        total_money = total_debt + total_paid   

        return [total_money,total_paid,total_debt]
    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/get_report',methods=['GET'])
@login_required
@check_ip
def get_report():
    try:    
        wanakamati,transaction= get_db(1)
        data = list(wanakamati.find({},{"_id":False}))
        info = []
        num = 1
        for doc in data:
            name = doc.get('name')
            phone = str(doc.get('phone'))
            alicholipa = doc.get('paid_amount')
            anachodaiwa = doc.get('debt_amount')
            info.append([num,name,phone,f"{alicholipa:,}",f"{anachodaiwa:,}"])
            num += 1

        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font('Arial',size=15,style='B')

        pdf.cell(0,20,txt='FUNDRAISING MANAGEMENT SYSTEM REPORT',ln=True,align='C')

        total = totals()
        total_money = total[0]
        total_paid = total[1]
        total_debt = total[2]

        pdf.set_font('Arial',size=12)
        pdf.multi_cell(
            0,7,
            txt = f'Report ya Hadi Leo Tarehe: {datetime.now().strftime("%d/%m/%Y")}\nJumla Kuu Ya Ahadi (Ambayo haijalipwa): {total_debt:,} TZS\nJumla Kuu Ya Fedha Taslimu (Cash iliyochangishwa): {total_paid:,}TZS\nJumla Kuu ya Fedha Zote (Ahadi+Cash): {total_money:,} TZS',
            align='L'
            )
        pdf.ln(20)

        col_width = [10,55,55,30,30] 

        header = ['S/N','Jina','Namba','Cash(TZS)','Deni(TZS)']
        for i in range(len(header)):
            pdf.cell(
                col_width[i],10,header[i],border=1,align='C'
            )
        pdf.ln(10)

        for row in info:
            if pdf.get_y() > 279:
                pdf.add_page()
                for i in range(len(row)):
                    pdf.cell(col_width[i],10,str(row[i]),border=1,align='C')
                pdf.ln(10)    
            else:
                for i in range(len(row)):
                    pdf.cell(col_width[i],10,str(row[i]),border=1,align='C')
                pdf.ln(10)   

        timestamp = datetime.now().strftime('%d-%m-%Y')
        output = f'Report Ya Tarehe {timestamp}.pdf'
        if os.path.isfile(output):
            os.remove(output)
        pdf.output(output)
        return send_file(output,as_attachment=True)
    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/notify_record',methods=['POST'])
@login_required
@check_ip
def notify_record():
    next_sms = True
    data = request.get_json()
    firstime = data.get('isFirstTime')
    sender_id = data.get('sender_id')

    if 'db_name' not in session:
        return jsonify({'error': "Authorization failed"})
    
    SENDER = session['db_name']
    thender = client['credentials']['logins']
    sacha = thender.find_one({"username": SENDER})
    person = sacha.get("fullname")
    
    
    message_template = client[SENDER]['message_templates'] 
    sms = list(message_template.find({},{'_id':False}))

    template = sms[0]
    bado_anadaiwa = template.get('bado_anadaiwa')
    amelipa_yote = template.get('amelipa_yote')
    fedha_taslimu_tu = template.get('fedha_taslimu')
    ahadi_tu = template.get('ahadi_tu')
    taslimu_na_ahadi = template.get('fedha_na_ahadi')

    try:
        wanakamati,transaction= get_db(1)
        if not firstime:
            name = str(data.get('memberName').strip())
            amount = int(data.get('amount'))
            payment_type = data.get('paymentType')
            date = data.get('date')

            ac = [name,amount,payment_type,date]
            for a in ac:
                if a == None:
                    return
                
            if name.isdigit():
                info = wanakamati.find_one({'phone': name})    
            else:
                info = wanakamati.find_one({'name': name})

            majina = info.get('name')
            namba = info.get('phone')
            ahadi_ya_mwanzo = info.get('promise_amount')
            alicholipa = info.get('paid_amount')
            anachodaiwa = info.get('debt_amount')    
            cash_ya_mwanzo = info.get('cash_amount')

            formater = {
                "name": majina,
                "payment_type": payment_type,
                "amount": amount,
                "person": person,
                "amount_paid": alicholipa,
                "amount_debt": anachodaiwa
            }

            #(majina,namba,alicholipa,anachodaiwa,cash_ya_mwanzo)
            if namba == None:
                return jsonify({'error': 'Muamala umefanyika kikamilifu ila ⚠️ Mchangiaji hasajaliwa kwa namba za simu ❌'})

            if anachodaiwa > 0:
                message = bado_anadaiwa.format(**formater)
            elif anachodaiwa <= 0:
                message = amelipa_yote.format(**formater)

            if next_sms:
                res = use_next_sms(namba,message,sender_id)
                if res == 200:
                    return jsonify({'message': 'amepata ujumbe kwa ukamilifu ✅'})
                elif res == 403:
                    return jsonify({'error': 'ila Mchangiaji hajapata ujumbe salio la sms ni pungufu ❌❌❌❌'})
                else:
                    return jsonify({'error': '⚠️ Mchangiaji hajapata ujumbe ❌'})
            else:
                api_key = '3c9a79Ua4b26f65tcB9O29ebgXdu14Pf9p4a4cfcf499e9ehT9=='
                man = store_message(api_key,namba,message,SENDER,majina)
                if man == 200:
                    #('message stored successfully')
                    return jsonify({'message': '✅ Mchangiaji amepata ujumbe kwa ukamilifu'})
                else:
                    return jsonify({'message': ' Mchangiaji hajapata ujumbe kwa ukamilifu'})
            
        else:
            name = str(data.get('name').strip())
            namba = str(data.get('phoneNumber').strip()) 
            ahadi = int(str(data.get('promise_amount').strip()))
            cash = int(str(data.get('cash_amount').strip())) 
            date = str(data.get('date')) 

            total = ahadi + cash

            formater = {
                "name": name,
                "cash": cash,
                "person": person,
                "ahadi": ahadi,
                "total": total
            }

            if namba == None:
                return jsonify({'error': 'Muamala umefanyika kikamilifu ila ⚠️ Mchangiaji hasajaliwa kwa namba za simu ❌'})

            if cash > 0 and ahadi == 0:
                message = fedha_taslimu_tu.format(**formater)
                
            elif ahadi > 0 and cash == 0:
                message = ahadi_tu.format(**formater)
            else:
                message = taslimu_na_ahadi.format(**formater)
                
            if next_sms:
                res = use_next_sms(namba,message,sender_id,SENDER,name)
                if res == 200:
                    return jsonify({'message': 'amepata ujumbe kwa ukamilifu ✅'})
                elif res == 403:
                    return jsonify({'error': 'Tafadhali ongeza salio la sms salio lako ni pungufu'})
                else:
                    return jsonify({'error': '⚠️ Mchangiaji hajapata ujumbe ❌'})

            else:
                api_key = '3c9a79Ua4b26f65tcB9O29ebgXdu14Pf9p4a4cfcf499e9ehT9=='
                man = store_message(api_key,namba,message)
                if man == 200:
                    #('message stored successfully')
                    return jsonify({'message': '✅ Mchangiaji amepata ujumbe kwa ukamilifu'})
                else:
                    return jsonify({'message': ' Mchangiaji hajapata ujumbe kwa ukamilifu'})
    except AttributeError:
        return redirect(url_for('logout'))              

def use_next_sms(namba,message,sender_id,SENDER,name):
    reference = str(uuid.uuid4())

    db_sys = client[SENDER]['sms_system']
    sms_info = list(db_sys.find({},{"_id":False}))[0]
    balance = int(sms_info.get('balance'))

    count = len(str(message))

    if balance - count < 0:
        return 403

    formatedNumber = "255"+ namba[1:]
    headers = {
        'Authorization': 'Basic VmVudm9ranI6R2FtZWwwZnQ=',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    data = {
        'from': sender_id,
        'to' : formatedNumber,
        'text': message,
        'reference': reference
    }

    API_URL = 'https://messaging-service.co.tz/api/sms/v1/text/single'
    try:
        response = requests.post(API_URL,headers=headers,json=data)

        if response.status_code == 200:
            save_thread = threading.Thread(target=manage_sent_message, args=(namba,sender_id,SENDER,name,response.json()))
            save_thread.start()
            return 200
        else:
            return 404
    except Exception as e:
        return str(e)       

def manage_sent_message(namba,sender_id,SENDER,name,response):
    db = client[SENDER]['stored_messages']
    db_sys = client[SENDER]['sms_system']

    sms_info = list(db_sys.find({},{"_id":False}))[0]
    balance = sms_info.get('balance')
    temps = sms_info.get('templates')
    former_sms_count = int(sms_info.get('sent_sms_count'))
    delivered_counts = int(sms_info.get('delivered_sms_count'))

    messageId = response.get('messages')[0].get('messageId')
    sms_count = response.get('messages')[0].get('smsCount')
    ujumbe = response.get('messages')[0].get('message')

    date = datetime.now(timezone).strftime('%d-%m-%Y')
    muda = datetime.now(timezone).strftime('%H:%M')

    sms_obj = {
        'sender_id': sender_id,
        'receiver_name': name,
        'receiver_phone': namba,
        'message': ujumbe,
        'sms_count': int(sms_count),
        'messageId': messageId,
        'date': date,
        'time': muda
    }

    balance -= int(sms_count)
    former_sms_count += sms_count
    delivered_counts += 1


    db_sys.drop()

    new_sms_info = {
        'balance': balance,
        'templates': temps,
        'sent_sms_count': former_sms_count,
        'delivered_sms_count': delivered_counts
    }

    new_db_sys = db_sys = client[SENDER]['sms_system']
    new_db_sys.insert_one(new_sms_info)

    db.insert_one(sms_obj)


def store_message(API,namba,message):
    db = get_db(2)
    messages = db['messages']
    messages.create_index('API_KEY')
    messages.insert_one({
        'API_KEY': API,
        'namba': namba,
        'message' : message
    })
    return 200

@app.route('/get_messages',methods=['GET'])
def get_message():
    API_KEY = request.headers.get('Authorization')
    #(API_KEY)
    authorized = open('static/assets/AUTHORIZED_API.json','r')
    authorized = json.load(authorized)
    if API_KEY not in authorized:
        #('Unauthorized')
        return jsonify({'error': 'You are unauthorized'}), 401
    try:
        db = get_db(2)
        messages = db['messages']
        checker =  list(messages.find({'API_KEY':API_KEY}))
        update = checker[:]
        if update == []:
            #('no new message')
            return jsonify(
                [{
                'new': False
                }]), 200
        
        #('new message')
        all_texts = []
        for sms in update:
            namba = sms.get('namba')
            message = sms.get('message')
            single_feedback = {
                'namba': namba,
                'message': message
            }
            all_texts.append(single_feedback)
        to_sent = all_texts[:]
        messages.delete_many({'API_KEY':API_KEY})
        return jsonify([{'new': True},to_sent]),200
    except AttributeError:
        return redirect(url_for('logout'))  

@app.route('/get_default_template',methods=['GET'])
@login_required
@check_ip
def get_default_template():
    if 'db_name' not in session:
        return jsonify({"error":"Session expired please login"})
    
    username = session['db_name']
    db = client[username]['message_templates']
    templates = list(db.find({},{'_id':False}))
    return jsonify(templates[0])

@app.route('/modify_template_message',methods=['POST'])
@login_required
@check_ip
def modify_template_message():
    
    data = request.get_json()
    bado_anadaiwa = data.get('badoAnadaiwa').strip()
    amelipa_yote = data.get('amelipaYote').strip()
    fedha_taslimu = data.get('fedhaTaslimu').strip()
    ahadi_tu = data.get('ahadiTu').strip()
    fedha_na_ahadi = data.get('fedhaNaAhadi').strip()
    kumbusha_deni = data.get('KumbushaDeni').strip()

    if "db_name" not in session:
        return jsonify({"error":"Session expired please log in"})
    
    username = session['db_name']
    collection = client[username]['message_templates']
    collection.drop()

    temp_sms = {
        "bado_anadaiwa": bado_anadaiwa,
        "amelipa_yote": amelipa_yote,
        "fedha_taslimu": fedha_taslimu,
        "ahadi_tu": ahadi_tu,
        "fedha_na_ahadi": fedha_na_ahadi,
        "kumbusha_deni": kumbusha_deni
    }

    collection.insert_one(temp_sms)
    return jsonify({"message": "✅Mabadiliko yamefanyika kikamilifu"})

@app.route('/sms_sender', methods=['GET'])
@login_required
@check_ip
def sms_sender():
    return render_template('sms_sender.html')

@app.route('/get_debts',methods=['GET'])
@login_required
@check_ip
def get_debts():
    os.system('cls')
    if 'db_name' not in session:
        return jsonify({'error':"Session Expired please log in again"})
    
    username = session['db_name']
    collection = client[username]['wanakamati']
    members = list(collection.find({},{'_id':False}).sort({"debt_amount":-1}))

    wadaiwa = []
    wadaiwa = [member for member in members if member.get('debt_amount') > 0]
    tobesent = wadaiwa[:]
    wadaiwa = []
    return jsonify(tobesent)

@app.route('/remind_debts',methods=['POST'])
@login_required
@check_ip
def remind_debts():
    data = request.get_json()
    if 'db_name' not in session:
        return jsonify({"error":"Session expired log in and try again"})
    
    username =  session['db_name']
    db = client[username]['message_templates']
    st = list(db.find({},{"_id":False}))

    ujumbe = st[0].get('kumbusha_deni')

    results = []

    def send_sms(member):
        name = member.get('name')
        debt = int(member.get('debt'))
        phoneNO = member.get('phone')
        if len(str(member.get('phone'))) == 10:  
            placeholder = {
                "name": name,
                "debt_amount": debt
            }
            message = ujumbe.format(**placeholder)
            
            return use_multinext_sms(phoneNO,message,data[1],username,name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(send_sms,member): member for member in data[0]}

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result == 403:
                return ({'insufficient':'Salio lako la sms halitoshi tafadhali ongeza'})
            results.append(result)

    return jsonify({"results": results})

def use_multinext_sms(namba,message,sender_id,username,name):
    reference = str(uuid.uuid4())

    db_sys = client[username]['sms_system']
    sms_info = list(db_sys.find({},{"_id":False}))[0]
    balance = int(sms_info.get('balance'))

    count = len(str(message))

    if balance - count < 0:
        return 403

    formatedNumber = "255"+ namba[1:]
    headers = {
        'Authorization': 'Basic VmVudm9ranI6R2FtZWwwZnQ=',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    data = {
        'from': sender_id,
        'to' : formatedNumber,
        'text': message,
        'reference': reference
    }

    API_URL = 'https://messaging-service.co.tz/api/sms/v1/text/single'
    try:
        response = requests.post(API_URL,headers=headers,json=data)

        if response.status_code == 200:
            save_thread = threading.Thread(target=manage_sent_message, args=(namba,sender_id,username,name,response.json()))
            save_thread.start()
            return 200
        else:
            return 404
    except Exception as e:
        return str(e)       

@app.route('/get_sender_ids',methods=['GET'])
@login_required
@check_ip
def get_sender_ids():
    if 'db_name' not in session:
        return jsonify({'error':'Session Expired Login Again'})

    username = session['db_name']
    db = client[username]['message_templates']
    ids = list(db.find({},{"_id":False}))[1].get('SENDER_IDS')

    return  jsonify(ids)

@app.route('/sms_history',methods=['GET'])
@login_required
@check_ip
def sms_history():
    return render_template('sms_history.html')
    

@app.route('/get_sms_history',methods=['GET'])
@login_required
@check_ip
def get_sms_history():
    if 'db_name' not in session:
        return jsonify({'error':'Session Expired Login Again'})
    
    username = session['db_name']
    db = client[username]['stored_messages']
    all_messages = list(db.find({},{"_id":False}))

    return jsonify(all_messages)

@app.route('/get_sms_balance',methods=['GET'])
@login_required
@check_ip
def get_sms_balance():
    if 'db_name' not in session:
        return(jsonify({'error':'Session Expired Login Again'}))
    
    username = session['db_name']
    db = client[username]['sms_system']
    infos = list(db.find({},{"_id":False}))[0]

    return jsonify(infos)

# Admin routes
@app.route('/admin/login', methods=['GET'])
@admin_required
def admin_login():
    return render_template('login.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin.html')

cred_db = client["credentials"]

@admin_required
def admin_get_users():
    col = cred_db['logins']
    users = list(col.find({},{'_id':False}))
    os.system('cls')
    
    non_adms = []
    for user in users:
        if user.get('is_admin'):
            continue
        else:
            non_adms.append(user)

    return non_adms        

@app.route('/admin/get_users',methods=['GET'])
@admin_required
def get_users():    
    non_adms = admin_get_users()

    used_balance = 0
    copy_non_adms = non_adms[:]
    report = []
    for user in copy_non_adms:
        fullname = user.get('fullname')
        username = user.get('username')
        status = user.get('is_blocked')
        db = client[username]['sms_system']
        try:
            sms_balance = list(db.find({}))[0].get('balance')
            used_balance += int(sms_balance)
            obj = {
                'sms_balance': sms_balance,
                'username': username,
                'fullname': fullname,
                'status': status
            }
            report.append(obj)
        except IndexError:
            continue    
    API_URL = 'https://messaging-service.co.tz/api/sms/v1/balance'

    headers = {
            'Authorization': 'Basic VmVudm9ranI6R2FtZWwwZnQ=',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    try:
        res = requests.get(API_URL,headers=headers)

        rem_balance = res.json().get('sms_balance')
        unsed_balance = int(rem_balance) - used_balance

        balance= {
            'bought_sms': used_balance,
            'total_rem': int(rem_balance),
            'unbought_balance': unsed_balance
        }

        report_sent = report[:]
        non_adms = []
        report= []

        take = [balance,report_sent]
        return jsonify(take)
    except Exception as e:
        return str(e)   

@app.route('/admin/edit_user_balance',methods=['POST'])
@admin_required
def edit_user_balance():
    data = request.get_json()
    
    username = data.get('username')
    balance = int(data.get('newBalance'))
    try:
        db = client[username]['sms_system']

        info = list(db.find({},{'_id':False}))[0]
        new_info = info
        
        new_info['balance'] = balance
        db.drop()
        new_db = client[username]['sms_system']
        new_db.insert_one(new_info)

        return jsonify({'message': 'Balance updated successfully'})
    
    except IndexError as e:
        #print('here is the ror')
        return jsonify({'error': str(e)})
    except Exception as e:
        #print('error here')
        return jsonify({'error': str(e)})

@app.route('/admin/sender_ids',methods=['GET'])    
@admin_required
def sender_id_page():
    return render_template('sender_ids.html')

@app.route('/admin/get_senderids',methods=['GET'])
@admin_required
def get_senderids_forUsers():    
    non_adms = admin_get_users()

    report = []
    for user in non_adms:
        username = user.get('username')
        try:
            sender_ids = list(client[username]['message_templates'].find({},{'_id':False}))[1].get('SENDER_IDS')
            obj={
                "username": username,
                "sender_ids": sender_ids
            }
            report.append(obj)
        except IndexError:
            continue
        except Exception:
            #print('i knew')
            continue
       
    cp_report = report[:]
    report = []
    return jsonify(cp_report)        

@app.route('/admin/global_sender_id_add',methods=['POST'])
@admin_required
def global_sender_id_add():
    data = request.get_json()
    users = data.get('all_usernames')
    sender_id = data.get('senderId').upper()

    errors = []
    success = []
    for user in users:
        message_templates = client[user]['message_templates'].find_one({})
        
        if message_templates and len(message_templates) >= 2:
            # Append "NEW_ID" to SENDER_IDS
            client[user]['message_templates'].update_one(
                {"SENDER_IDS": {"$exists": True}},  # Targets the second doc
                {"$push": {"SENDER_IDS": sender_id}}  
            )
            success.append(user)
        else:
            errors.append(user)

    return jsonify({'errors':errors,'success':success})   

@app.route('/admin/single_sender_id_add',methods=['POST']) 
@admin_required   
def single_sender_id_add():
    data = request.get_json()
    username = data.get('username')
    sender_id = data.get('senderId').upper()
    action = data.get('action')

    if action == 'add':
        db = client[username]['message_templates']
        db.update_one({'SENDER_IDS': {'$exists':True}},{'$push':{'SENDER_IDS': sender_id}})
        return jsonify({'message':'Sender ID added successfully'})
    elif action == 'remove':
        db = client[username]['message_templates']
        db.update_one({'SENDER_IDS': {'$exists':True}},{'$pull':{'SENDER_IDS': sender_id}})
        return jsonify({'message':'Sender ID removed successfully'})

@app.route('/admin/block_user',methods=['POST'])
@admin_required
def block_user():
    data = request.get_json()
    username = data.get('username')
    active = data.get('isBlocked')   
    #print(f"is {active}")
    client['credentials']['logins'].update_one({'username':username},{'$set':{'is_blocked': active}})

    res = client['credentials']['logins'].find_one({"username":username}).get('is_blocked')
    #print(res)
    if active == res:
        return jsonify({'message':'work'})
    else:
        return jsonify({'error':'no work'})

@app.route('/admin/gen_license',methods=['POST'])
@admin_required
def gen_license():
    data = request.get_json()
    quantity = int(data.get('quantity'))

    licenses = []
    while True:
        if quantity > 0:
            licenses.append("".join(random.sample([random.choice(string.ascii_letters) for _ in range(6)] + [random.choice(string.digits) for _ in range(6)],12)))
            quantity -= 1
        else:
            break    

    for license in licenses:
        lic_obj = {
            "license_key": 'FMS-'+license,
            'status': "unused",
            'usedBy': None
        }
        client['credentials']['licenses'].insert_one(lic_obj)

    return jsonify({'message':'Collected please refresh the browser'})  

@app.route('/admin/get_licenses',methods=['GET'])
@admin_required
def get_licenses():

    licenses = list(client['credentials']['licenses'].find({},{'_id':False}))

    if licenses:
        return jsonify(licenses)
    else:
        return jsonify({'message':'No available licenses'})

@app.route('/admin/revoke_license',methods=['POST'])
@admin_required
def revoke_license():
    data= request.get_json()
    license_key = data.get('code')
    man = client['credentials']['licenses']
    if man.update_one({'license_key':license_key},{'$set':{'status':{'revoked'}}}):
        return jsonify({'message': 'revoked successfully'})
    else:
        return jsonify({'error': 'revoke unsuccessfully'})

@app.route('/admin/export_db', methods=['POST'])
@admin_required
def export_db():
    try:
        data = request.get_json()
        username = data.get('user')
        collection = data.get('collection')

        if not username or not collection:
            return jsonify({'error': 'Missing user or collection'}), 400

        # Get data and convert ObjectId to string
        data = list(client[username][collection].find({}))
        for doc in data:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])

        # Create in-memory file
        output = io.BytesIO()
        output.write(json.dumps(data, indent=4).encode('utf-8'))
        output.seek(0)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"{username}-{collection}-{timestamp}.json"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/import_db', methods=['POST'])
@admin_required
def import_db():
    try:
        data = request.get_json()
        user = data.get('user')
        collection = data.get('collection')
        documents = data.get('data')
        
        if not all([user, collection, documents]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if not isinstance(documents, list):
            client[user][collection].insert_many(documents)
        
        # Convert _id strings to ObjectId
        processed_docs = []
        for doc in documents:
            new_doc = {}
            for key, value in doc.items():
                if key == '_id' and value:
                    try:
                        # Handle both string and $oid formats
                        if isinstance(value, dict) and '$oid' in value:
                            new_doc[key] = ObjectId(value['$oid'])
                        else:
                            new_doc[key] = ObjectId(value)
                    except:
                        # If invalid ObjectId, keep original
                        new_doc[key] = value
                else:
                    new_doc[key] = value
            processed_docs.append(new_doc)

        
        for processed_doc in processed_docs:
            client[user][collection].insert_one(processed_doc)
            #print(processed_doc.get('name'))

        return jsonify({
                'success': True
            })
            
    except Exception as e:
        #print(str(e))
        return jsonify({'error': str(e)}), 500  

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)