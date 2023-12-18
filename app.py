from ast import Return
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
# import redis
import os
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
from chatbot import ask, create_agent
from ChromaOperations import list_collections, list_docs_in_collection, create_collection
from ChromaOperations import delete_collection as delete_chroma_collection
from Upload import upload_docs
from flask import flash
from werkzeug.utils import secure_filename
import shutil
import Config
#from dotenv import load_dotenv
#load_dotenv()
app = Flask(__name__)

# Define the absolute path for storing uploaded files
UPLOAD_FOLDER = '/var/www/sara/webserver/tempdocs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the UPLOAD_FOLDER exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DBCONN_STR
# app.config['REDIS_HOST'] = os.getenv('REDIS_HOST')
# app.config['REDIS_PORT'] = os.getenv('REDIS_PORT')
# app.config['MONGO_CONN_STR'] = os.getenv('MONGO_CONN_STR')

db = SQLAlchemy(app)

# cacheserver = redis.Redis(host=app.config['REDIS_HOST'], port=int(app.config['REDIS_PORT']), db=0)

# User class, which maps via ORM to User table in database
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(255))

# collection class, which maps via ORM to User table in database
class Collections(db.Model):
    name = db.Column(db.String(100), nullable=True)
    uuid = db.Column(db.String(100), nullable=True)
    collection_name = db.Column(db.String(100), nullable=True, primary_key=True)

class UploadedFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.Text, nullable=True)
    # file_content = db.Column(db.LargeBinary, nullable=True)
    uuid = db.Column(db.Text, nullable=True)
    collection_name = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=True, server_default=db.func.current_timestamp())

# Decorator for verifying the JWT and handling user authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token', None)

        if not token:
            # Redirect to the login page if no token is present
            return redirect(url_for('login'))

        try:
            data = jwt.decode(token, app.secret_key, algorithms="HS256")
            current_user = User.query.filter_by(public_id=data.get('public_id')).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            # Token has expired, redirect to login
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            # Invalid token, redirect to login
            return redirect(url_for('login'))

        # Pass the current user to the route function
        return f(current_user, *args, **kwargs) if current_user else f(*args, **kwargs)

    return decorated


# this route returns a home page as HTML
@app.route('/')
@token_required
def home(current_user=None):
   return render_template('homepage.html', username=current_user.name)	


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # We will try json body first, then HTML form
    email = None
    password = None

    if request.content_type == 'application/json':
        json_data = request.get_json()
        if not json_data.get('email') or not json_data.get('password'):
            # return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        email = json_data['email']
        password = json_data['password']
    else:
        auth = request.form
        if not auth or not auth.get('email') or not auth.get('password'):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
            # return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})
        email = auth['email']
        password = auth['password']

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('Invalid username or password', 'error')
        return render_template('login.html', successful_login=False)
        # returns 401 if user does not exist
        #return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})

    if check_password_hash(user.password, password):
        # generates the JWT Token
        token = jwt.encode({
            'public_id': user.public_id,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        session['token'] = token
        flash('Login sucessful', 'success')
        return render_template('login.html', successful_login=True)
        #return redirect(url_for('home'))

        #return make_response(jsonify({'token': token}), 201)

    # returns 401 if password is wrong
    # return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required"'})
    flash('Invalid username or password', 'error')
    return render_template('login.html', successful_login=False)
    #return redirect(url_for('login.html'))




@app.route('/collections')
@token_required
def collections(current_user=None):
    return render_template('collections_page.html')


@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('register.html')

    uname = None
    email = None
    password = None

    if request.content_type == 'application/json':
        json = request.get_json()
        if not json.get('uname') or not json.get('email') or not json.get('password'):
            return jsonify({'message': 'You must provide user name, email, and password to sign up'}), 400
        uname = json['uname']
        email = json['email']
        password = json['password']
    else:
        data = request.form
        if not data or not data.get('uname') or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'You must provide user name, email, and password to sign up'}), 400
        uname = data['uname']
        email = data['email']
        password = data['password']

    # checking for existing user
    user = User.query.filter_by(email=email).first()
    if not user:
        # OK to add. Create new user.
        hashed_password = generate_password_hash(password)
        new_user = User(
            public_id=str(uuid.uuid4()),
            name=uname,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            # Redirect to login page after successful registration
            #return redirect(url_for('login'))
            return render_template('register.html')
        except Exception as e:
            # Handle database commit errors
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return jsonify({'error': str(e)}), 500
    else:
        # returns 202 if user already exists
        flash('User already exists. Please Log in.', 'info')
        return redirect(url_for('signup'))


@app.route('/chat', methods=["GET", "POST"])
@token_required
def chat(current_user=None):
	if request.method == "POST":
		# Get user input from the form
		user_input = request.form.get('msg')
        

		agent = create_agent()
		# Call the chatbot function to get the response
		bot_response = ask(agent=agent, question=user_input,collection_name= request.form.get('collection'))
		# Return the response as JSON (you can modify this based on your needs)
		return jsonify({'msg': bot_response})
	
	return render_template('chat.html')	

@app.route('/create_collection', methods=['GET','POST'])
@token_required
def create_collection_api(current_user=None):

    if request.method == "POST":
        data = request.json
        collection_name = data.get('collectionname')
        username = data.get('username')
        
        if not collection_name:
            return jsonify({'error': 'Collection name is required'}), 400
        
        create_collection(collection_name)
        new_collection = Collections(
            uuid=current_user.public_id,
            name= current_user.name,
            collection_name=collection_name
        )
        db.session.add(new_collection)
        db.session.commit()

        return jsonify({'message': f'Collection {collection_name} created successfully'}), 201

    return render_template('create_collections.html')


@app.route('/list_collections', methods=['GET','POST'])
@token_required
def list_collections_api(current_user=None):

    if request.method == "POST":
        try:
        
            data = request.json
            name = data.get('username')

            collections_list = Collections.query.filter_by(uuid=current_user.public_id).all()
            if len(collections_list) == 0:
                return jsonify({'collections': []}), 200 
            else:
                collections_data = [Collections.collection_name for Collections in collections_list]
                return jsonify({'collections': collections_data}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    return render_template('list_collections.html')    
    

@app.route('/upload', methods=['GET', 'POST'])
@token_required
def upload(current_user=None):
    if request.method == 'POST':
        # Handle file upload logic here
        # Make sure to validate file type (.pptx and .pdf)
        collection_name = request.form['collection']
        print("Collection is : ",collection_name)
        uploaded_files = request.files.getlist('files[]')

        # Create a subdirectory for the collection within the UPLOAD_FOLDER
        folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.public_id)
        os.makedirs(folder, exist_ok=True)

        for file in uploaded_files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(folder, filename)
            file.save(file_path)  # Save the file to the specified subdirectory

        # return "Files uploaded successfully!"

        upload_docs(directory_path=folder, collection_name=collection_name)
        shutil.rmtree(folder)

        # Add data to the UploadedFiles database model
        for file in uploaded_files:
            filename = secure_filename(file.filename)
            new_uuid = str(uuid.uuid4())
            timestamp = datetime.utcnow()

            new_uploaded_file = UploadedFiles(
                file_name=filename,
                uuid=new_uuid,
                collection_name=collection_name,
                timestamp=timestamp
            )

            db.session.add(new_uploaded_file)
            db.session.commit()

        return redirect(url_for('upload_success'))
    
    user_collections = Collections.query.filter_by(uuid=current_user.public_id).all()
    collections = [collection.collection_name for collection in user_collections]

    return render_template('upload.html', collections=collections)

@app.route('/upload-success')
@token_required
def upload_success(current_user=None):
    # Render the upload-success.html template
    return render_template('upload-success.html')
	


# Route for user logout
@app.route('/logout', methods=['GET'])
def logout():
    # Clear the session data
    session.clear()
    flash('Logout successful', 'success')
    return redirect(url_for('login'))



@app.route('/user_info')
@token_required
def user_info(current_user):
    return jsonify({
        'id': current_user.id,
        'public_id': current_user.public_id,
        'name': current_user.name,
        'email': current_user.email
        # Add any other user attributes you want to include
    })


@app.route('/chat_collections', methods=['POST'])
@token_required
def get_collections(current_user=None):
    try:
        # Get collections for the current user
        collections_list = Collections.query.filter_by(uuid=current_user.public_id).all()

        # Extract collection names from the query result
        collection_names = [collection.collection_name for collection in collections_list]

        # Return the collection names as a JSON response
        return jsonify({'collections': collection_names}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@app.route('/list_documents', methods=['GET', 'POST'])
@token_required
def list_documents(current_user=None):
    if request.method == "GET":
        # Render the list-documents.html template for GET requests
        user_collections = Collections.query.filter_by(uuid=current_user.public_id).all()
        collections = [collection.collection_name for collection in user_collections]
        return render_template('list-documents.html', collections=collections)

    elif request.method == "POST":
        try:
            data = request.json
            selected_collection = data.get('selected_collection')

            if not selected_collection:
                return jsonify({'error': 'Selected collection is required'}), 400

            # Retrieve documents for the selected collection
            documents_list = UploadedFiles.query.filter_by(collection_name=selected_collection).all()

            # Extract file names from the query result
            file_names = [document.file_name for document in documents_list]

            # Return the file names as a JSON response
            return jsonify({'documents': file_names}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('list-documents.html')


# Route for rendering the delete_collection.html page
@app.route('/delete_collection', methods=['GET'])
@token_required
def delete_collection(current_user=None):
    # Get collections for the current user
    user_collections = Collections.query.filter_by(uuid=current_user.public_id).all()
    collections = [collection.collection_name for collection in user_collections]

    # Render the delete_collection.html template with the list of collections
    return render_template('delete-collection.html', collections=collections)

@app.route('/delete_collection', methods=['POST'])
@token_required
def delete_collection_api(current_user=None):
    try:
        # Get the selected collection from the request data
        data = request.json
        selected_collection = data.get('selected_collection')

        # Delete the collection from the database
        delete_chroma_collection(selected_collection)
        collection_to_delete = Collections.query.filter_by(collection_name=selected_collection, uuid=current_user.public_id).first()
        if collection_to_delete:
            # Delete all rows in the uploaded_files table belonging to the selected collection
            UploadedFiles.query.filter_by(collection_name=selected_collection).delete()

            db.session.delete(collection_to_delete)
            db.session.commit()
            return jsonify({'message': f'Collection {selected_collection} deleted successfully, along with its documents'}), 200
        else:
            return jsonify({'error': f'Collection {selected_collection} not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


