import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import io
import shutil
from deepface import DeepFace
from PIL import Image

# --- CONFIGURATION ---
DB_FILE = 'atm_data.db'
ENROLLMENT_DIR = 'enrolled_faces'
RECOGNITION_MODEL = "VGG-Face" 
# Use OpenCV for face detection as it is generally the fastest CPU option
DETECTOR_BACKEND = 'opencv' 

# --- 1. DATABASE & FILE SYSTEM MANAGEMENT ---

def init_db():
    """Initializes the SQLite database and the enrolled faces directory."""
    os.makedirs(ENROLLMENT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create the Users table
    # Storing the image path rather than the embedding itself is more standard for DeepFace/find
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            account_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            balance REAL NOT NULL,
            enrolled_face_path TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

# --- 2. CACHING AND MODEL LOADING (CPU Optimization) ---

@st.cache_resource
def load_face_recognizer(model_name: str):
    """Initializes and caches the DeepFace model for single-time loading."""
    st.info(f"Loading the {model_name} Deep Learning model... (CPU Optimization)")
    try:
        # DeepFace.build_model() ensures the model is loaded and ready.
        DeepFace.build_model(model_name=model_name)
        st.success(f"Model ({model_name}) loaded successfully and cached.")
        return model_name
    except Exception as e:
        st.error(f"Error loading DeepFace model: {e}")
        st.stop()

# --- 3. CORE LOGIC (Enrollment and Transaction Handlers) ---

def enroll_user(account_no, name, initial_deposit, image_bytes):
    """
    Handles user enrollment: saves the image, checks for face, and records data in DB.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if Account No already exists
    c.execute('SELECT account_no FROM users WHERE account_no=?', (account_no,))
    if c.fetchone():
        conn.close()
        return False, "Error: Account number already exists."

    # 1. Save Image
    user_file_name = f"{account_no}.jpg"
    file_path = os.path.join(ENROLLMENT_DIR, user_file_name)
    
    # Convert bytes to PIL Image and save
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.save(file_path)
    except Exception as e:
        conn.close()
        return False, f"Error saving image file: {e}"

    # 2. Verify Face Detection (Crucial for reliable authentication later)
    try:
        # Check if a face is detected in the new image
        DeepFace.extract_faces(img_path=file_path, detector_backend=DETECTOR_BACKEND, enforce_detection=True)
    except ValueError as e:
        # If no face is detected, clean up the file
        os.remove(file_path)
        conn.close()
        return False, "Error: No clear face detected in the image. Enrollment failed."
    except Exception as e:
        # Other DeepFace errors
        os.remove(file_path)
        conn.close()
        return False, f"DeepFace processing error: {e}"

    # 3. Record Data in DB
    try:
        c.execute('INSERT INTO users VALUES (?, ?, ?, ?)', 
                  (account_no, name, initial_deposit, file_path))
        conn.commit()
        conn.close()
        return True, "User successfully enrolled and account created!"
    except Exception as e:
        # If DB insertion fails, clean up the saved image file
        os.remove(file_path)
        conn.close()
        return False, f"Database insertion error: {e}"

def update_balance(account_no, amount, transaction_type):
    """Handles deposit or withdrawal and updates the balance in the database."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get current balance
    c.execute('SELECT balance FROM users WHERE account_no=?', (account_no,))
    current_balance = c.fetchone()[0]

    if transaction_type == 'Withdrawal':
        if current_balance < amount:
            conn.close()
            return False, "Insufficient funds."
        new_balance = current_balance - amount
    elif transaction_type == 'Deposit':
        new_balance = current_balance + amount
    else:
        conn.close()
        return False, "Invalid transaction type."

    # Update database
    c.execute('UPDATE users SET balance=? WHERE account_no=?', (new_balance, account_no))
    conn.commit()
    conn.close()
    
    # Update session state for immediate UI refresh
    st.session_state.user_account['balance'] = new_balance
    return True, f"{transaction_type} successful. New balance: ${new_balance:,.2f}"

# --- 4. STREAMLIT INTERFACE ---

def main():
    # Initialize the database and load the cached model
    init_db()
    MODEL_NAME = load_face_recognizer(RECOGNITION_MODEL)

    st.title("💳 Full-Featured Pinless ATM Simulator")
    st.caption(f"Biometric Model: **{MODEL_NAME}** | Persistence: **SQLite**")

    # Initialize Session State
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_account = None

    menu = ["Login", "Enroll New User"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        if st.session_state.logged_in:
            show_transaction_view()
        else:
            show_login_view(MODEL_NAME)
            
    elif choice == "Enroll New User":
        show_enrollment_view()

def show_login_view(model_name):
    """Displays the biometric login interface using a live camera feed."""
    st.subheader("Biometric Login")
    
    captured_image = st.camera_input("Take a picture of your face to log in")
    auth_button_pressed = st.button("Authenticate & Access Account", key="login_auth_button")
    
    if auth_button_pressed:
        if captured_image is not None:
            
            # Define paths for the probe image and the clean database
            PROBE_FILE = os.path.join(ENROLLMENT_DIR, 'temp_auth_file.jpg')
            TEMP_DB_DIR = 'temp_clean_db' 
            
            # 1. Save the captured image to the defined probe file path
            image = Image.open(captured_image)
            image.save(PROBE_FILE)
            
            # 2. Create a clean database directory for DeepFace to search
            # This is the key step to prevent matching the probe file itself.
            os.makedirs(TEMP_DB_DIR, exist_ok=True)
            
            # Copy only the permanent enrolled user files to the temporary DB directory
            enrolled_files = [f for f in os.listdir(ENROLLMENT_DIR) if f != os.path.basename(PROBE_FILE)]
            for file_name in enrolled_files:
                shutil.copy(os.path.join(ENROLLMENT_DIR, file_name), TEMP_DB_DIR)

            # Reset the debug message state
            st.session_state['debug_match_path'] = None
            
            with st.spinner('Running Biometric Verification...'):
                try:
                    # DeepFace search: Use PROBE_FILE as input, and TEMP_DB_DIR as the search directory
                    results = DeepFace.find(
                        img_path=PROBE_FILE, 
                        db_path=TEMP_DB_DIR, # Search the clean directory!
                        model_name=model_name, 
                        detector_backend=DETECTOR_BACKEND,
                        enforce_detection=True 
                    )
                    
                    user_data = None
                    
                    # 1. PROCESS RESULTS
                    if results and isinstance(results, list) and len(results) > 0 and not results[0].empty:
                        
                        # Get the closest matching enrolled image path (e.g., 'temp_clean_db/1001.jpg')
                        best_match_path_raw = results[0]['identity'].iloc[0]
                        
                        # The path returned by DeepFace is relative to TEMP_DB_DIR. 
                        # We must convert it back to the original ENROLLMENT_DIR path for the DB query.
                        
                        # Extract just the filename (e.g., '1001.jpg')
                        match_filename = os.path.basename(best_match_path_raw)
                        
                        # Construct the original path stored in the database
                        best_match_path = os.path.join(ENROLLMENT_DIR, match_filename)
                        best_match_path = os.path.normpath(best_match_path) # Final normalization
                        st.session_state['debug_match_path'] = best_match_path

                        # 2. Retrieve User Data from DB
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute('SELECT * FROM users WHERE enrolled_face_path=?', (best_match_path,))
                        user_data = c.fetchone()
                        conn.close()
                        
                    # 3. FINAL CHECK AND REDIRECT
                    if user_data:
                        # Success: Load the account into session state
                        st.session_state.logged_in = True
                        st.session_state.user_account = {
                            'account_no': user_data[0],
                            'name': user_data[1],
                            'balance': user_data[2],
                            'path': user_data[3]
                        }
                        st.balloons()
                        st.success(f"✅ Authentication Successful! Welcome, {st.session_state.user_account['name']}!")
                        st.rerun() 
                    else:
                        st.error("❌ Authentication Failed. Face not recognized or user data not linked correctly.")
                        if st.session_state.get('debug_match_path'):
                             st.error(f"DEBUG: Failed to find user in DB using path: {st.session_state['debug_match_path']}")

                except Exception as e:
                    st.error(f"Error during verification. Please ensure your face is clearly visible. DeepFace Error: {e}")
                
                finally:
                    # CLEANUP: Remove the probe file AND the temporary clean database directory
                    if os.path.exists(PROBE_FILE):
                        os.remove(PROBE_FILE)
                    if os.path.exists(TEMP_DB_DIR):
                        shutil.rmtree(TEMP_DB_DIR) # Recursively delete the temporary directory
        
        else:
            st.warning("Please capture your face image using the camera input before authenticating.")

def show_enrollment_view():
    """Displays the interface for enrolling a new user."""
    st.subheader("Enroll New Pinless Account")

    with st.form("enrollment_form"):
        new_account_no = st.text_input("New Account Number (Unique ID)", max_chars=10)
        new_name = st.text_input("Full Name")
        initial_deposit = st.number_input("Initial Deposit Amount", min_value=10.00, step=100.00)
        face_capture = st.camera_input("Take a clear picture of your face for enrollment", key="enroll_camera")

        submitted = st.form_submit_button("Create Account & Enroll Face")

        if submitted and face_capture is not None:
            if not new_account_no or not new_name:
                st.error("Please fill in Account Number and Name.")
                return

            # Call the enrollment handler
            success, message = enroll_user(
                account_no=new_account_no, 
                name=new_name, 
                initial_deposit=initial_deposit, 
                image_bytes=face_capture.getbuffer()
            )

            if success:
                st.success(message)
                st.info(f"You can now login using your face.")
            else:
                st.error(message)

        elif submitted and face_capture is None:
             st.error("Please take a picture of your face to enroll.")


def show_transaction_view():
    """Displays the main ATM transaction interface."""
    st.subheader(f"Welcome, {st.session_state.user_account['name']}!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Account No", st.session_state.user_account['account_no'])
    with col2:
        st.metric("Current Balance", f"${st.session_state.user_account['balance']:,.2f}")
    
    st.write("---")
    
    transaction_type = st.radio("Select Operation", ["Withdrawal", "Deposit", "Balance Check", "Log Out"])
    
    if transaction_type in ["Withdrawal", "Deposit"]:
        amount = st.number_input(f"Enter {transaction_type} Amount", min_value=1.00, step=10.00, key=f"txn_{transaction_type}")
        if st.button(f"Complete {transaction_type}"):
            success, message = update_balance(
                account_no=st.session_state.user_account['account_no'],
                amount=amount,
                transaction_type=transaction_type
            )
            if success:
                st.success(message)
            else:
                st.error(message)

    elif transaction_type == "Balance Check":
        st.info(f"Your current balance is **${st.session_state.user_account['balance']:,.2f}**.")
        
    elif transaction_type == "Log Out":
        if st.button("Confirm Log Out"):
            st.session_state.logged_in = False
            st.session_state.user_account = None
            st.success("You have been securely logged out. Please log in again.")
            st.rerun()

if __name__ == "__main__":
    main()