from flask import Blueprint, json, jsonify, url_for, current_app, flash, request, redirect, send_from_directory, send_file, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from API.model import *
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from sqlalchemy.sql import func
from API.settings import *
from API import mail, Message
from API.email_sender import *
import json
import random

from werkzeug.utils import secure_filename
from datetime import datetime as dt, date
import uuid

from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

today_raw = date.today()
today = date.isoformat(today_raw)
month = f"{today_raw.month}-{today_raw.year}"
import os
import secrets
import string

VAULT = {
    "bronze": [
        {"package": "Airtime Recharge Bonus", "reward": 15},
        {"package": "Data Recharge Bonus", "reward": 10},
    ],
    "silver": [
        {"package": "Electricity Bill Bonus", "reward": 25},
        {"package": "Netflix Subscription Discount", "reward": 30},
        {"package": "Shopping Voucher", "reward": 20},
    ],
    "gold": [
        {"package": "Luxury Dinner Voucher", "reward": 50},
        {"package": "Flirt Ticket (Exclusive Event)", "reward": 60},
        {"package": "VIP Concert Ticket", "reward": 75},
        {"package": "Premium Gym Membership", "reward": 80},
    ],
}



# Function to generate a random password
def generate_password(length=8):
    characters = string.ascii_letters + string.digits  # Letters and numbers
    return ''.join(secrets.choice(characters) for _ in range(length))

from math import ceil

UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# upload_path = os.path.join(current_app.config[ 'UPLOAD_FOLDER' ])

app = current_app

agent_bp = Blueprint("agent_bp", __name__, template_folder='templates', static_folder='static')


# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}



# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# @agent_bp.route("/")
# def index():
#     return "hello Sixpay"

@agent_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        # Check if email already exists
        existing_client = Client.query.filter_by(email=data['email']).first()
        if existing_client:
            return jsonify({
                "error": f"A customer with this email ({data['email']}) has already registered."
            }), 400

        # Generate unique account number (Ensuring uniqueness)
        while True:
            account_number = random.randint(1000000000, 9999999999)  # 10-digit number
            if not Client.query.filter_by(account_number=account_number).first():
                break  # Ensure uniqueness before proceeding

        # Generate a unique verification code
        verification_code = str(random.randint(100000, 999999))  # 6-digit code

        # Hash password
        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256')

        refered_by = Client.query.filter_by(public_id=data["refferal_id"]).first()


        # Create new client record
        new_client = Client(
            public_id=str(uuid.uuid4()),
            firstname=data["firstname"],
            surname=data["surname"],
            account_number=account_number,
            email=data["email"],
            phone=data["phone"],
            code=verification_code,
            password_hash=hashed_password,
            balance=0.0,
            bonus_balance=0.0,
            status="ACTIVE",
            game_on=False,
            date_registered=dt.now()
        )

        if refered_by:
            new_client.refferal_id = refered_by.id
            point = Gamify.query.filter_by(client_id=refered_by.id).first()
            point.keys_earned += 2
            db.session.add(point)

        # Save to database
        db.session.add(new_client)
        db.session.commit()

        # Send welcome email (Optional)
        # send_welcome_email(new_client.email, new_client.firstname, verification_code)

        return jsonify({
            "message": "Client registered successfully!",
            "client_id": new_client.id,
            "account_number": new_client.account_number
        }), 201

    except Exception as e:
        db.session.rollback()  # Ensure rollback on error
        return jsonify({
            "error": "Failed to process request",
            "details": str(e)
        }), 500


@agent_bp.route("/upload_agency_doc", methods=["POST"])
def upload_agency_doc():
    try:
        uploaded_files = {}

        # Allowed file types
        file_fields = ["company_registration", "liability_insurance", "certifications"]

        for field in file_fields:
            if field in request.files:
                file = request.files[field]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    uploaded_files[field] = file_path

        return jsonify({"message": "Files uploaded successfully", "files": uploaded_files}), 201

    except Exception as e:
        return jsonify({"error": "File upload failed", "details": str(e)}), 500
        


@agent_bp.route('/login', methods=['POST'])
def login():
    data = request.form

    # Check if all required fields are present
    if not all(key in data for key in ('email', 'password')):
        return jsonify({'message': 'Missing fields'}), 400
    try:
        email = data['email']
        password = data['password']

        # if username != 'petstellon':
        #     return jsonify({'message': 'App in maintenance mode.'}), 400

        # Find admin by username
        agent = Client.query.filter_by(email=email).first()

        # Check if agent exists and verify password
        if agent and agent.check_password(password):
            try:
                user_agent = request.headers.get('User-Agent')
                ip_address = request.remote_addr
                info = {'ip': ip_address, 'agent': user_agent, 'location': ip_address}
                #send_login_email(admin.email, admin.username, info)
            except Exception as error:
                return jsonify({'error': str(error)})
            else:
                # Create access token
                access_token = create_access_token(identity=str(agent.id))
                return jsonify({'access_token': access_token, 'user_id': agent.id}), 200
        else:
            return jsonify({'message': 'Invalid username or password'}), 401
    except Exception as error:
        return jsonify({ 'error': str(error) })

@agent_bp.route('/dashboard', methods=['POST', "GET"])
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    try:
        client = Client.query.filter_by(id=current_user).first()
    except Exception as e:
        return jsonify({'message': f"{e}"}), 500
    else:
        return jsonify({ 'user': client.to_dict(), 'agency': client.to_dict() }), 200

@agent_bp.route('/mystery_vault', methods=['POST', "GET"])
@jwt_required()
def mystery_vault():
    current_user = get_jwt_identity()
    try:
        client = Client.query.filter_by(id=current_user).first()
        client.game_on = True
        db.session.add(client)

        key = Gamify.query.filter_by(client_id=client.id).first()
        if key:
            key.keys_earned += 1
            db.session.add(key)
        else:
            new = Gamify(client_id=current_user, keys_earned=1, status='ACTIVE')
            db.session.add(new)

        db.session.commit()
    except Exception as e:
        return jsonify({'message': f"{e}"}), 500
    else:
        return jsonify({ 'user': client.to_dict(), 'message': f"Waooo! Mystery Vault Activated. You just earn 1key for activation. share your link to family and friends to earn more keys and unlock your mystery vault." }), 200

@agent_bp.route("/password-reset", methods=["POST"])
def password_reset():
    data = request.form
    email = data.get("email")

    agent = Client.query.filter_by(email=email).first()
    if not agent:
        return jsonify({"message": "Email not found"}), 404
    try:
        # Generate a unique token
        token = serializer.dumps(email, salt="password-reset-salt")

        # Send the email with reset link
        reset_url = url_for("agent_bp.reset_password", token=token, _external=True)
        info = {
            'name': agent.firstname,
            'reset_link': reset_url
        }
        send_paasreset_email(agent.email, info)
    except Exception as e:
        return jsonify({ "message": f"{e}" }), 404
    else:
        return jsonify({"message": f"Password reset link sent to {email}"}), 200


@agent_bp.route("/reset-password/<token>", methods=[ "GET" ])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)  # Token expires in 1 hour
    except:
        return "Invalid or expired token", 400

    return render_template("agent_reset_password.html", email=email, token=token, title=App_name)

@agent_bp.route("/process_reset_password", methods=["POST"])
def process_reset_password():
    data = request.form
    new_password = data.get("password")
    if not new_password:
        return jsonify({"message": "Password is required"}), 400
    try:
        email = serializer.loads(data.get('token'), salt="password-reset-salt", max_age=3600)  # Expires in 1 hour
    except:
        return jsonify({"message": "Invalid or expired token"}), 400
    else:
        agent = Client.query.filter_by(email=email).first()
        if agent:
            agent.set_password(new_password)
            db.session.add(agent)
            db.session.commit()
            flash("Password reset successful", 'success')
            return redirect(f"{Agent_Link}/login")
        flash("Unable to reset password" , 'danger')
        return redirect(f"{Agent_Link}/login")

@agent_bp.route('/receive_bank_details', methods=['POST'])
@jwt_required()
def receive_bank_details():
    current_user = get_jwt_identity()
    try:
        data = json.loads(request.get_json())  # Expect JSON input

        # Extract JSON data
        agency_id = data.get("agency_id")
        bank_name = data.get("bank_name")
        swift_code = data.get("swift_code")
        account_name = data.get("account_name")
        account_number = data.get("account_number")
        status = data.get("status", "pending")

        # Validate required fields
        if not agency_id or not bank_name or not account_name or not account_number:
            return jsonify({"message": "Missing required fields", "status": "error"}), 400

        # Create new BankDetail entry
        new_bank_detail = BankDetails(
            agency_id=int(agency_id),
            bank_name=bank_name,
            swift_code=swift_code,
            account_name=account_name,
            account_number=account_number,
            status=status
        )

        # Save to Database
        db.session.add(new_bank_detail)
        db.session.commit()

        return jsonify({"message": "Bank details received and stored successfully!", "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/edit_bank_details', methods=['PUT'])
@jwt_required()
def edit_bank_details():
    current_user = get_jwt_identity()
    try:
        data = json.loads(request.get_json())  # Expect JSON input

        # Extract JSON data
        bank_id = data.get("bank_id")
        bank_name = data.get("bank_name")
        swift_code = data.get("swift_code")
        account_name = data.get("account_name")
        account_number = data.get("account_number")

        # Validate required fields
        if not bank_id or not bank_name or not account_name or not account_number:
            return jsonify({"message": "Missing required fields", "status": "error"}), 400

        # Create new BankDetail entry
        new_bank_detail = BankDetails.query.filter_by(id=bank_id).first()
        new_bank_detail.bank_name = bank_name
        new_bank_detail.swift_code = swift_code
        new_bank_detail.account_name = account_name
        new_bank_detail.account_number = account_number

        # Save to Database
        db.session.add(new_bank_detail)
        db.session.commit()

        return jsonify({"message": "Bank details updated successfully!", "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/delete_bank_details', methods=['DELETE'])
@jwt_required()
def delete_bank_details():
    current_user = get_jwt_identity()
    try:
        data = request.args.get('id')  # Expect JSON input


        # Create new BankDetail entry
        new_bank_detail = BankDetails.query.filter_by(id=data).first()

        # Save to Database
        db.session.delete(new_bank_detail)
        db.session.commit()

        return jsonify({"message": "Bank details deleted successfully!", "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/team_members', methods=['GET', "POST"])
@jwt_required()
def team_members():
    current_user = get_jwt_identity()
    try:
        teams = Client.query.filter_by(refferal_id=current_user).all()
        user = Client.query.filter_by(id=current_user).first()
        memebers = [tt.to_dict() for tt in teams]
        return jsonify({"team": memebers, "user": user.to_dict(), "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/wallet_transactions', methods=['GET', "POST"])
@jwt_required()
def wallet_transactions():
    current_user = get_jwt_identity()
    try:
        transactions = WalletTransaction.query.filter_by(client_id=current_user).all()
        user = Client.query.filter_by(id=current_user).first()
        transact = [tt.obj_to_dict() for tt in transactions]
        return jsonify({"transactions": transact, "user": user.to_dict(), "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/unlock_vault', methods=['GET', "POST"])
@jwt_required()
def unlock_vault():
    current_user = get_jwt_identity()
    try:
        vault_id = request.args.get('vault_id')

        user = Client.query.filter_by(id=current_user).first()
        game = Gamify.query.filter_by(client_id=user.id).first()

        if vault_id == 'bronze':
            if game.keys_earned >= 3:
                game.keys_earned -= 3
                game.level = vault_id
                db.session.add(game)

                reward = random.choice(VAULT[vault_id])
                check_wallet = BonusWallet.query.filter((BonusWallet.client_id == current_user)&(BonusWallet.product == reward['package'])).first()

                if check_wallet:
                    old_bal = check_wallet.balance
                    check_wallet.balance += reward[ 'reward' ]
                    db.session.add(check_wallet)

                    tr_rec = WalletTransaction(wallet_id=check_wallet.id, client_id=current_user,
                                               desc=f"Bronze Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=old_bal,
                                               bal_af=reward[ 'reward' ] + old_bal, ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                else:
                    new_wallet = BonusWallet(client_id=user.id, product=reward['package'], balance=reward['reward'])
                    db.session.add(new_wallet)
                    db.session.commit()

                    tr_rec = WalletTransaction(wallet_id=new_wallet.id, client_id=current_user,
                                               desc=f"Bronze Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=0,
                                               bal_af=reward[ 'reward' ], ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                user.bonus_balance += reward['reward']
                db.session.commit()
                return jsonify({ 'success': True, 'message': f'{reward["package"]} bonus activated with £{reward["reward"]} credited to bonus wallet.', 'reward': f'{reward["package"]} bonus activated with £{reward["reward"]} credited to bonus wallet.' })
            return jsonify({'error': "You don't have enough keys to unlock this vault"}), 500
        elif vault_id == 'silver':
            if not game.level:
                return jsonify({ 'error': "You need to unlock bronze Vault first before Silver." }), 500
            if game.keys_earned >= 5:
                game.keys_earned -= 5
                game.level = vault_id
                db.session.add(game)

                reward = random.choice(VAULT[ vault_id ])
                check_wallet = BonusWallet.query.filter((BonusWallet.client_id == current_user) & (
                            BonusWallet.product == reward[ 'package' ])).first()

                if check_wallet:
                    old_bal = check_wallet.balance
                    check_wallet.balance += reward[ 'reward' ]
                    db.session.add(check_wallet)

                    tr_rec = WalletTransaction(wallet_id=check_wallet.id, client_id=current_user,
                                               desc=f"Silver Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=old_bal,
                                               bal_af=reward[ 'reward' ] + old_bal, ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                else:
                    new_wallet = BonusWallet(client_id=user.id, product=reward[ 'package' ], balance=reward['reward'])
                    db.session.add(new_wallet)
                    db.session.commit()

                    tr_rec = WalletTransaction(wallet_id=new_wallet.id, client_id=current_user,
                                               desc=f"Silver Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=0,
                                               bal_af=reward[ 'reward' ], ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                user.bonus_balance += reward[ 'reward' ]
                db.session.commit()
                return jsonify({ 'success': True,
                                 'message': f'{reward[ "package" ]} bonus activated with £{reward[ "reward" ]} credited to bonus wallet.',
                                 'reward': f'{reward[ "package" ]} bonus activated with £{reward[ "reward" ]} credited to bonus wallet.' })
            return jsonify({ 'error': "You don't have enough keys to unlock this vault" }), 500
        else:
            # if not game.level or game.level != 'silver' or game.level == 'bronze':
            #     return jsonify({ 'error': "You need to unlock bronze and silver Vault first before Gold." }), 500
            if game.keys_earned >= 10:
                game.keys_earned -= 10
                game.level = vault_id
                db.session.add(game)

                reward = random.choice(VAULT[ vault_id ])
                check_wallet = BonusWallet.query.filter((BonusWallet.client_id == current_user) & (
                            BonusWallet.product == reward[ 'package' ])).first()

                if check_wallet:
                    old_bal = check_wallet.balance
                    check_wallet.balance += reward[ 'reward' ]
                    db.session.add(check_wallet)

                    tr_rec = WalletTransaction(wallet_id=check_wallet.id, client_id=current_user,
                                               desc=f"Gold Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=old_bal,
                                               bal_af=reward[ 'reward' ] + old_bal, ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                else:
                    new_wallet = BonusWallet(client_id=user.id, product=reward[ 'package' ], balance = reward[ 'reward' ])
                    db.session.add(new_wallet)
                    db.session.commit()

                    tr_rec = WalletTransaction(wallet_id=new_wallet.id, client_id=current_user,
                                               desc=f"Gold Vault Unlocked: {reward}", t_type="CR",
                                               amount=reward[ 'reward' ], bal_bf=0,
                                               bal_af=reward[ 'reward' ], ref=str(uuid.uuid4()))
                    db.session.add(tr_rec)
                user.bonus_balance += reward[ 'reward' ]
                db.session.commit()
                return jsonify({ 'success': True,
                                 'message': f'{reward[ "package" ]} bonus activated with £{reward[ "reward" ]} credited to bonus wallet.',
                                 'reward': f'{reward[ "package" ]} bonus activated with £{reward[ "reward" ]} credited to bonus wallet.' })
            return jsonify({ 'error': "You don't have enough keys to unlock this vault" }), 500

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@agent_bp.route('/team_settings', methods=['GET', "POST"])
@jwt_required()
def team_settings():
    current_user = get_jwt_identity()
    try:
        id = request.args.get("id")
        statuss = request.args.get("status")
        user = TeamMember.query.filter_by(id=id).first()
        if statuss != 'delete':
            user.status = statuss
            db.session.add(user)
        else:
            db.session.delete(user)
        db.session.commit()
        return jsonify({"user": user.to_dict(), "status": "success"}), 201

    except Exception as e:
        return jsonify({"message": str(e), "status": "error"}), 500

@agent_bp.route('/bonus_wallet', methods=['GET', "POST"])
@jwt_required()
def bonus_wallet():
    current_user = get_jwt_identity()
    if request.method == 'POST':
        try:
            data = json.loads(request.get_json())  # Expect JSON input

            # Extract JSON data
            agency_id = data.get("agency_id")
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            email = data.get("email")
            country_code = data.get("country_code")
            phone_number = data.get("phone_number")
            gender = data.get("gender")
            date_of_birth = data.get("date_of_birth")
            mothers_tongue = data.get("mothers_tongue")
            nationality = data.get("nationality")
            country = data.get("country")
            city_of_residence = data.get("city_of_residence")
            passport_status = data.get("passport_status")
            status = data.get("status", "active")

            check = Student.query.filter_by(email=email).first()
            if check:
                return jsonify({ "message": "A student has been registered with this email before.", "status": "error" }), 500

            # Create a new Student instance
            new_student = Student(first_name, last_name, email, phone_number, country_code, nationality, nationality, nationality, nationality)
            new_student.agency_id=agency_id
            new_student.gender=gender
            new_student.date_of_birth=date_of_birth
            new_student.mothers_tongue=mothers_tongue
            new_student.nationality=nationality
            new_student.country=country
            new_student.city_of_residence=city_of_residence
            new_student.passport_status=passport_status
            new_student.assigned_to_team_id=current_user

            new_student.set_password(first_name)


            user = Agent.query.filter_by(id=current_user).first()
            new_student.assigned_to_team = user.agent_name
            db.session.add(new_student)
            db.session.commit()

            new_agency = Agency.query.filter_by(id=agency_id).first()

            # Query all advisors with the role "ADVISOR"
            advisors = Advisor.query.filter_by(role="ADVISOR").all()

            # Count the total number of assigned students per advisor from both Student and Student tables
            advisor_student_counts = {
                advisor.id: (
                        Student.query.filter_by(advisor_id=advisor.id).count() +
                        Student.query.filter_by(assigned_to=advisor.id).count()
                )
                for advisor in advisors
            }

            # Select the advisor with the least assigned students
            if advisor_student_counts:
                least_assigned_advisor_id = min(advisor_student_counts, key=advisor_student_counts.get)
                new_student.advisor_id = least_assigned_advisor_id  # Assign the advisor
                new_student.assigned_to = least_assigned_advisor_id  # Assign the advisor
                db.session.add(new_student)
                db.session.commit()

            # Send welcome email
            adv_info = Advisor.query.filter_by(id=new_student.assigned_to).first()
            send_set_advisor(adv_info.name, new_student.to_dict(), adv_info.email)
            send_agency_advisor(new_agency.agency_name, adv_info.basic_to_dict(), user.email, new_student.to_dict())

            return jsonify({ "message": "Student account created successfully!", "status": "success" }), 201

        except Exception as e:
            return jsonify({ "message": str(e), "status": "error" }), 500

    if request.args:
        try:
            id = request.args.get('id')
            user = Client.query.filter_by(id=current_user).first()
            wallet = BonusWallet.query.filter_by(id=id).first()
            return jsonify({"wallet": wallet.to_dict(), "user": user.to_dict(), "status": "success"}), 201

        except Exception as e:
            return jsonify({"message": str(e), "status": "error"}), 500

    # try:
    user = Client.query.filter_by(id=current_user).first()
    wallet = BonusWallet.query.filter_by(client_id=current_user).all()
    return jsonify({ "wallet": [ww.to_dict() for ww in wallet], "user": user.to_dict(), "status": "success" }), 201

    # except Exception as e:
    #     return jsonify({ "message": str(e), "status": "error" }), 500

@agent_bp.route('/students_profile', methods=['GET', "POST"])
@jwt_required()
def students_profile():
    current_user = get_jwt_identity()
    if request.method == 'POST':
        pass
    try:
        id = request.args.get('id')
        student = Student.query.filter_by(id=id).first()
        return jsonify(student.obj_to_dict())
    except Exception as e:
        return jsonify({ "message": str(e), "status": "error" }), 500

def send_app_status_email(email, info):
    # Render the login email template with user data
    html_content = render_template('email/app_status.html', info=info, title=App_name)
    # Send the login email
    msg = Message(f'{App_name}: APPLICATION STATUS CHANGED', recipients=[ email ])
    msg.html = html_content
    mail.send(msg)

def send_paasreset_email(email, info):
    # Render the login email template with user data
    html_content = render_template('send_password_reset_link.html', info=info, title=App_name)
    # Send the login email
    msg = Message(f'{App_name}: RESET PASSWORD', recipients=[ email ])
    msg.html = html_content
    mail.send(msg)

def send_welcome_email(email, agency_name, password):
    # Prepare user info dictionary for rendering the email template
    info = {
        "agency_name": agency_name,
        "email": email,
        "password": password
    }

    # Render the welcome email template with user data
    html_content = render_template('email/welcome_agent.html', info=info, title=App_name)

    # Create and send the email
    msg = Message(f'{App_name}: Welcome to {App_name}!', recipients=[email])
    msg.html = html_content
    mail.send(msg)

def send_team_welcome_email(email, agency_name, password, first_name):
    # Prepare user info dictionary for rendering the email template
    info = {
        "first_name": first_name,
        "agency_name": agency_name,
        "email": email,
        "password": password,
        "login_url": f"{Agent_Team_Link}/login"
    }

    # Render the welcome email template with user data
    html_content = render_template('email/welcome_team_member.html', info=info, title=App_name)

    # Create and send the email
    msg = Message(f'{App_name}: Welcome to {App_name}!', recipients=[email])
    msg.html = html_content
    mail.send(msg)


def send_set_advisor(name, std_info, email):
    # Render the welcome email template with user data
    html_content = render_template('email/set_advisor.html', std_info=std_info, name=name, title=App_name)
    # Send the welcome email
    msg = Message(f'YOU HAVE A NEW STUDENT', recipients=[ email ])
    msg.html = html_content
    mail.send(msg)


def send_agency_advisor(name, advisor_info, email, student_info):
    # Render the welcome email template with user data
    html_content = render_template('email/agency_advisor.html', advisor_info=advisor_info, agency_name=name, student_info=student_info,  title=App_name)
    # Send the welcome email
    msg = Message(f'STUDENT REGISTRATION RECEIVED', recipients=[ email ])
    msg.html = html_content
    mail.send(msg)