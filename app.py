from flask import Flask,render_template,request,redirect,url_for,session,flash,request
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import cv2
import numpy as np
import dlib
from imutils import face_utils
import time
import asyncio
from pygame import mixer
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate



app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
db=SQLAlchemy(app)
app.secret_key = '__primary_key__'
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))  # Assuming gender is a string ('male', 'female', 'others')
    place = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))  # Assuming a basic phone number format

    def __init__(self, name, email, password, age, gender, place, phone_number):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.age = age
        self.gender = gender
        self.place = place
        self.phone_number = phone_number

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Admin(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(20),unique=True,nullable=False) 
    password = db.Column(db.String(60), nullable=False)   
# Decorator for user authentication
def login_required(role='user'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('You need to log in first.', 'danger')
                return redirect(url_for('login'))

            user_id = session['user_id']
            user = User.query.get(user_id)

            if user.role != role:
                flash(f'You do not have permission to access this page as a {role}.', 'danger')
                return redirect(url_for('homepage'))

            return func(*args, **kwargs)

        return wrapper

    return decorator
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.password == password:
            flash('Admin login successful!', 'success')
            session['admin_id'] = admin.id  # Store admin ID in the session
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login unsuccessful. Please check your username and password.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_dashboard')

def admin_dashboard():
    if 'admin_id' not in session:
        flash('You do not have access to the admin dashboard.', 'danger')
        return redirect(url_for('homepage'))

    total_users = User.query.count()
    
    users = User.query.all()
    

    return render_template('admin_dashboard.html', users=users, total_users=total_users)

@login_required(role='admin')
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))    



with app.app_context():
    db.create_all()


  

   


mixer.init()
no_driver_sound = mixer.Sound('nodriver_audio.wav')
sleep_sound = mixer.Sound('sleep_sound.wav')
tired_sound = mixer.Sound('rest_audio.wav')

# Initializing the face detector and landmark detector
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def compute(ptA, ptB):
    dist = np.linalg.norm(ptA - ptB)
    return dist


def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up/(2.0*down)

    # Checking if it is blinked
    if (ratio > 0.22):
        return 'active'
    else:
        return 'sleep'


def mouth_aspect_ratio(mouth):
    # compute the euclidean distances between the two sets of
    # vertical mouth landmarks (x, y)-coordinates
    A = compute(mouth[2], mouth[10])  # 51, 59
    B = compute(mouth[4], mouth[8])  # 53, 57

    # compute the euclidean distance between the horizontal
    # mouth landmark (x, y)-coordinates
    C = compute(mouth[0], mouth[6])  # 49, 55

    # compute the mouth aspect ratio
    mar = (A + B) / (2.0 * C)

    # return the mouth aspect ratio
    return mar


(mStart, mEnd) = (49, 68)


async def tired():
    start = time.time()
    rest_time_start=start
    tired_sound.play()
    a = 0
    while (time.time()-start < 9):
        if(time.time()-rest_time_start>3):
            tired_sound.play()
        # cv2.imshow("USER",tired_img)
    tired_sound.stop()
    return


def detech():
    # status marking for current state
    sleep_sound_flag = 0
    no_driver_sound_flag = 0
    yawning = 0
    no_yawn = 0
    sleep = 0
    active = 0
    status = ""
    color = (0, 0, 0)
    no_driver=0
    frame_color = (0, 255, 0)
    # Initializing the camera and taking the instance
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("DRIVER (Enter q to exit)", cv2.WINDOW_NORMAL)

# Set the position of the window
    cv2.moveWindow("DRIVER (Enter q to exit)", 100,100)
    # Give some time for camera to initialize(not required)
    time.sleep(1)
    start = time.time()
    no_driver_time=time.time()
    no_driver_sound_start = time.time()

    while True:
        _, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_frame = frame.copy()
        faces = detector(gray, 0)

        # detected face in faces array
        if faces:
         no_driver_sound_flag=0   
         no_driver_sound.stop()   
         no_driver=0  
         no_driver_time=time.time() 
        #  sleep_sound.stop()
         for face in faces:
            x1 = face.left()
            y1 = face.top()
            x2 = face.right()
            y2 = face.bottom()

            cv2.rectangle(frame, (x1, y1), (x2, y2), frame_color, 2)
            # cv2.rectangle(face_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            landmarks = predictor(gray, face)
            landmarks = face_utils.shape_to_np(landmarks)

            # The numbers are actually the landmarks which will show eye
            left_blink = blinked(landmarks[36], landmarks[37],
                                 landmarks[38], landmarks[41], landmarks[40], landmarks[39])
            right_blink = blinked(landmarks[42], landmarks[43],
                                  landmarks[44], landmarks[47], landmarks[46], landmarks[45])
            mouth = landmarks[mStart:mEnd]
            mouthMAR = mouth_aspect_ratio(mouth)
            mar = mouthMAR

            # Now judge what to do for the eye blinks

            if (mar > 0.70):
                sleep = 0
                active = 0
                yawning += 1
                status = "Yawning"
                color = (255, 0, 0)
                frame_color = (255, 0, 0)
                sleep_sound_flag = 0
                sleep_sound.stop()

            elif (left_blink == 'sleep' or right_blink == 'sleep'):
                if (yawning > 20):
                    no_yawn += 1
                sleep += 1
                yawning = 0
                active = 0
                if (sleep > 5):
                    status = "Sleeping !"
                    color = (0, 0, 255)
                    frame_color = (0, 0, 255)
                    if sleep_sound_flag == 0:
                        sleep_sound.play()
                    sleep_sound_flag = 1
            else:
                if (yawning > 20):
                    no_yawn += 1
                yawning = 0
                sleep = 0
                active += 1
                status = "Awake"
                color = (0, 255, 0)
                frame_color = (0, 255, 0)
                if active > 5:
                    sleep_sound_flag = 0
                    sleep_sound.stop()

            cv2.putText(frame, status, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

            if (time.time()-start < 60 and no_yawn >= 3):
                no_yawn = 0
                # print("tired")
                # asyncio.run(put_image(frame))
                # time.sleep(2)
                asyncio.run(tired())
            elif time.time()-start > 60:
                start = time.time()

            for n in range(0, 68):
                (x, y) = landmarks[n]
                cv2.circle(face_frame, (x, y), 1, (255, 255, 255), -1)
        else:
            no_driver+=1
            sleep_sound_flag = 0
            sleep_sound.stop()
            if(no_driver>10):
              status="No Driver"
              color=(0,0,0)
            if time.time()-no_driver_time>5:
                if(no_driver_sound_flag==0):
                   no_driver_sound.play()
                   no_driver_sound_start=time.time()
                else:
                    if(time.time()-no_driver_sound_start>3):
                        no_driver_sound.play()
                        no_driver_sound_start=time.time()
                no_driver_sound_flag=1

        cv2.putText(frame, status, (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
        cv2.imshow("DRIVER (Enter q to exit)", frame)
        cv2.imshow("68_POINTS", face_frame)
        if (cv2.waitKey(1) & 0xFF == ord('q')):
            break
    no_driver_sound.stop()
    sleep_sound.stop()
    tired_sound.stop()
    cap.release()
    cv2.destroyAllWindows()   


    

@app.route("/open_camera")

def open():
    detech()
    print("open camera")
    return redirect("/dashboard")



@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['name'] = user.name
            session['email'] = user.email
            flash('Login successful!', 'success')  # Add flash message
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'danger')  # Add flash message
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

import re  

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        place = request.form['place']
        phone_number = request.form['phone_number']

        # Check if all required fields are filled
        if not all([name, email, password, age, gender, place, phone_number]):
            flash('Please fill in all details.', 'danger') 
            return render_template('register.html')

        # Check if age is above 18
        if int(age) < 18:
            flash('You must be above 18 to register.', 'danger')
            return render_template('register.html')

        # Check if password meets criteria (at least 8 characters, including letters and numbers)
        if len(password) < 8 or not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
            flash('Password must contain at least 8 characters, including letters and numbers.', 'danger')
            return render_template('register.html')

        new_user = User(
            name=name,
            email=email,
            password=password,
            age=age,
            gender=gender,
            place=place,
            phone_number=phone_number
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')  
        return redirect('/login')

    return render_template('register.html')


    
@app.route('/dashboard')

def dashboard():
    if 'name' in session:
        user=User.query.filter_by(email=session['email']).first()
        if user:
            return render_template('dashboard.html',user=user)
    
    return redirect('/login')  

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')      



@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")


if __name__=="__main__":
    app.run(debug=True)
    app.debug = True
