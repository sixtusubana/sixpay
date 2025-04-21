from flask import Blueprint, render_template, flash, redirect, url_for, jsonify, request, current_app, session
from flask_login import login_required, current_user, login_user, logout_user
from CLIENT.settings import App_name, SERVER_URL
# from CLIENT import socketio, emit
from CLIENT import login_manager
from CLIENT.model import AdminUser
from werkzeug.utils import secure_filename

import json
from datetime import date, datetime, timezone
import os

import requests

agent_bp = Blueprint("agent_bp", __name__, template_folder='templates', static_folder='static')

upload_path = os.path.join(current_app.config[ 'UPLOAD_FOLDER' ])

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}

# Function to check allowed file types
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@agent_bp.route("/sign-up", methods=["POST", "GET"])
def sign_up():
    if request.method == 'POST':
        try:
            # Extract form data
            form_data = {
                "firstname": request.form.get("firstname"),
                "surname": request.form.get("surname"),
                "email": request.form.get("email"),
                "phone": request.form.get("phone"),
                "password": request.form.get("password"),
                "confirm_password": request.form.get("confirm_password"),
                "refferal_id": request.form.get("refferal_id"),
                "terms_accepted": request.form.get("terms"),
            }

            # Ensure passwords match
            if form_data["password"] != form_data["confirm_password"]:
                flash("Passwords do not match!", 'danger')
                return redirect(url_for("agent_bp.sign_up"))

            # Remove confirm_password before sending data
            del form_data["confirm_password"]

            # Send form data to external API
            response = requests.post(f"{SERVER_URL}/agent/signup", json=form_data)

            if response.status_code != 201:
                flash(f"Failed to register: {response.json()}", 'danger')
                return redirect(url_for("agent_bp.sign_up"))

            flash("Registration successful! Please log in.", 'success')
            return redirect(url_for("agent_bp.login"))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('agent_bp.sign_up'))

    refferal_id = request.args.get("referral_id")
    if refferal_id:
        return render_template("client/sign-up.html", refferal_id=refferal_id, title=App_name)
    return render_template("client/sign-up.html", title=App_name)


@agent_bp.route("/", methods=["POST", "GET"])
@agent_bp.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get("email")
        password = data.get("password")
        remember_me = data.get("rememberMe")

        # Simulated authentication check
        resp = requests.post(f"{SERVER_URL}/agent/login", data=data)
        if resp.status_code == 200:
            # Extract user_id from API server response
            session[ 'access_token' ] = resp.json().get('access_token')
            user_id = resp.json().get('user_id')
            # Log the user in using Flask-Login
            user = AdminUser(user_id)
            login_user(user)
            return redirect(url_for('agent_bp.dashboard'))
        else:
            flash(f"{resp.json()['message']}", 'danger')
            return redirect(url_for('agent_bp.login'))
    return render_template("client/sign-in.html", title=App_name)

@current_app.template_filter('to_datetime')
def to_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")  # Adjust format if needed

# Register the filter
current_app.jinja_env.filters['to_datetime'] = to_datetime

@agent_bp.route("/dashboard", methods=["POST", "GET"])
@login_required
def dashboard():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    resp = requests.get(f"{SERVER_URL}/agent/dashboard", headers=headers)
    # return resp.json()
    if resp.status_code == 200:
        return render_template('client/dashboard.html', referral_link=f'{url_for("agent_bp.sign_up", referral_id=resp.json()["user"]["public_id"], _external=True)}', title=App_name, details=resp.json(), user=resp.json()['user'])
    else:
        flash(f"{resp.json()}", "danger")
        return redirect(url_for('agent_bp.login'))

@agent_bp.route("/mystery-vault", methods=["POST", "GET"])
@login_required
def mystery_vault():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    id = request.args.get("user")
    resp = requests.get(f"{SERVER_URL}/agent/mystery_vault?id={id}", headers=headers)
    # return resp.json()
    if resp.status_code == 200 or resp.status_code == 201:
        flash(f"{resp.json()['message']}", "success")
        return redirect(url_for('agent_bp.dashboard'))
    else:
        flash(f"{resp.json()}", "danger")
        return redirect(url_for('agent_bp.login'))

@agent_bp.route('/forget-password', methods=["POST", "GET"])
def forget_password():
    if request.method == 'POST':
        data = request.form
        resp = requests.post(f"{SERVER_URL}/agent/password-reset", data=data)
        if resp.status_code == 200:
            flash(f"{resp.json()['message']}", 'success')
            return redirect(url_for('agent_bp.forget_password'))
        flash(f"{resp.json()[ 'message' ]}", 'danger')
        return redirect(url_for('agent_bp.forget_password'))
    else:
        return render_template('client/forget-password.html', title=App_name)

@agent_bp.route('/submit-bank-details', methods=['POST'])
def submit_bank_details():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    try:
        # Get form data from the request
        form_data = {
            "agency_id": request.form.get("agency_id"),
            "bank_name": request.form.get("bank_name"),
            "swift_code": request.form.get("swift_code"),
            "account_name": request.form.get("account_name"),
            "account_number": request.form.get("account_number")
        }
        # form_data = request.form
        # Forward the data to the external API
        response = requests.post(f"{SERVER_URL}/agent/receive_bank_details", json=json.dumps(form_data), headers=headers)

        # Check response status
        if response.status_code == 200 or response.status_code == 201:
            flash("Bank details submitted successfully!", "success")
            return redirect(url_for('agent_bp.dashboard'))
        else:
            flash("Failed to submit bank details", "danger")
            return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", "danger")
        return redirect(url_for('agent_bp.dashboard'))

@agent_bp.route('/edit-bank-details', methods=['POST'])
def edit_bank_details():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    try:
        # Get form data from the request
        form_data = {
            "bank_id": request.form.get("bank_id"),
            "bank_name": request.form.get("bank_name"),
            "swift_code": request.form.get("swift_code"),
            "account_name": request.form.get("account_name"),
            "account_number": request.form.get("account_number")
        }
        # form_data = request.form
        # Forward the data to the external API
        response = requests.put(f"{SERVER_URL}/agent/edit_bank_details", json=json.dumps(form_data), headers=headers)

        # Check response status
        if response.status_code == 200 or response.status_code == 201:
            flash("Bank details updated successfully!", "success")
            return redirect(url_for('agent_bp.dashboard'))
        else:
            flash("Failed to update bank details", "danger")
            return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", "danger")
        return redirect(url_for('agent_bp.dashboard'))

@agent_bp.route('/delete-bank-details', methods=['GET'])
def delete_bank_details():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        id = request.args.get("bank")
        # form_data = request.form
        # Forward the data to the external API
        response = requests.delete(f"{SERVER_URL}/agent/delete_bank_details?id={id}", headers=headers)

        # Check response status
        if response.status_code == 200 or response.status_code == 201:
            flash("Bank details deleted successfully!", "success")
            return redirect(url_for('agent_bp.dashboard'))
        else:
            flash("Failed to delete bank details", "danger")
            return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", "danger")
        return redirect(url_for('agent_bp.dashboard'))


@agent_bp.route('/referrals', methods=['GET', "POST"])
def referrals():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        resp = requests.get(f"{SERVER_URL}/agent/team_members", headers=headers)
        if resp.status_code == 200 or resp.status_code == 201:
            return render_template("client/team_members.html", team=resp.json()['team'], user=resp.json()['user'], title=App_name)
        flash("Something went wrong", 'danger')
        return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", 'danger')
        return redirect(url_for('agent_bp.dashboard'))

@agent_bp.route('/wallet-transactions', methods=['GET', "POST"])
def wallet_transactions():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        resp = requests.get(f"{SERVER_URL}/agent/wallet_transactions", headers=headers)
        if resp.status_code == 200 or resp.status_code == 201:
            return render_template("client/wallet_transaction.html", transactions=resp.json()['transactions'], user=resp.json()['user'], title=App_name)
        flash("Something went wrong", 'danger')
        return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", 'danger')
        return redirect(url_for('agent_bp.dashboard'))


@agent_bp.route('/unlock-vault', methods=['GET'])
@login_required
def unlock_vault():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    if not token:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

    try:

        user_id = request.args.get('user_id')  # Read from URL parameters
        vault_id = request.args.get('vault_id')

        if not user_id or not vault_id:
            return jsonify({'success': False, 'message': 'Missing user_id or vault_id'}), 400



        # Forward the data to the external API
        response = requests.get(f"{SERVER_URL}/agent/unlock_vault?vault_id={vault_id}", headers=headers)
        return jsonify(response.json())

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@agent_bp.route('/team-settings', methods=['GET', "POST"])
def team_settings():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        id = request.args.get('id')
        status = request.args.get('status')
        resp = requests.get(f"{SERVER_URL}/agent/team_settings?id={id}&status={status}", headers=headers)
        if resp.status_code == 200 or resp.status_code == 201:
            flash("Status updated successfully", 'success')
            return redirect(url_for('agent_bp.team_members'))
        flash("Something went wrong", 'danger')
        return redirect(url_for('agent_bp.team_members'))
    except Exception as e:
        flash(f"{e}", 'danger')
        return redirect(url_for('agent_bp.team_members'))


@agent_bp.route('/bonus-wallet', methods=['GET', "POST"])
def bonus_wallet():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    if request.method == "POST":
        # Get form data from the request
        form_data = {
            "agency_id": request.form.get("agency_id"),
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "email": request.form.get("email"),
            "phone_number": request.form.get("phone_number"),
            "country_code": request.form.get("country_code"),
            "gender": request.form.get("gender"),
            "date_of_birth": request.form.get("date_of_birth"),
            "mothers_tongue": request.form.get("mothers_tongue"),
            "nationality": request.form.get("nationality"),
            "country": request.form.get("country"),
            "city_of_residence": request.form.get("city_of_residence"),
            "passport_status": request.form.get("passport_status"),
        }

        # form_data = request.form
        # Forward the data to the external API
        response = requests.post(f"{SERVER_URL}/agent/students", json=json.dumps(form_data),
                                 headers=headers)

        # Check response status
        if response.status_code == 200 or response.status_code == 201:
            flash("Member added successfully!", "success")
            return redirect(url_for('agent_bp.students'))
        else:
            flash(f"{response.json()['message']}", "danger")
            return redirect(url_for('agent_bp.students'))

    if request.args:
        try:
            id = request.args.get("id")
            resp = requests.get(f"{SERVER_URL}/agent/bonus_wallet?id={id}", headers=headers)
            if resp.status_code == 200 or resp.status_code == 201:
                # return resp.json()
                return render_template("client/bonus_wallet.html", wallet=resp.json()[ 'wallet' ],
                                       user=resp.json()[ 'user' ], title=App_name)
            flash("Something went wrong", 'danger')
            return redirect(url_for('agent_bp.dashboard'))
        except Exception as e:
            flash(f"{e}", 'danger')
            return redirect(url_for('agent_bp.dashboard'))
    # try:
    resp = requests.get(f"{SERVER_URL}/agent/bonus_wallet", headers=headers)
    if resp.status_code == 200 or resp.status_code == 201:
        return render_template("client/bonus_wallet.html", wallet=resp.json()['wallet'], user=resp.json()['user'], title=App_name)
    flash(f"{resp.json()}", 'danger')
    return redirect(url_for('agent_bp.dashboard'))
    # except Exception as e:
    #     flash(f"{e}", 'danger')
    #     return redirect(url_for('agent_bp.dashboard'))

@agent_bp.route('/students_profile', methods=['GET', "POST"])
def students_profile():
    token = session[ 'access_token' ]
    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        id = request.args.get('profile')
        resp = requests.get(f"{SERVER_URL}/agent/students_profile?id={id}", headers=headers)
        if resp.status_code == 200 or resp.status_code == 201:
            return resp.json()
            # return render_template("client/bonus_wallet.html", students=resp.json()['students'], user=resp.json()['user'], title=App_name)
        flash("Something went wrong", 'danger')
        return redirect(url_for('agent_bp.dashboard'))
    except Exception as e:
        flash(f"{e}", 'danger')
        return redirect(url_for('agent_bp.dashboard'))

@agent_bp.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('token_expiration', None)
    logout_user()
    return redirect(url_for('agent_bp.login'))

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    flash('you must be logged in to view that page', 'danger')
    return redirect(url_for('auth_bp.admin_login'))