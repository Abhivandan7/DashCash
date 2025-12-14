# 🚀 DashCash: The Pinless ATM Revolution

Tired of fumbling with PINs? Welcome to **DashCash**, a cutting-edge ATM simulator that redefines banking security and speed! This is a full-featured, CPU-optimized application that replaces traditional four-digit codes with instant **Face Recognition** powered by Deep Learning.

Built with Python and Streamlit, DashCash is designed to run efficiently on any standard computer, proving that advanced biometrics don't require expensive hardware.

## ✨ Why DashCash is Awesome

- **⚡ Zero-PIN Login:** Your face _is_ your card! Log in instantly using a live camera feed via advanced **DeepFace** recognition.
- **🧠 CPU-Powered Efficiency:** We use smart techniques, like Streamlit's resource caching, to load the heavy **VGG-Face** Deep Learning model only once. This means blazing fast authentication without needing a dedicated GPU.
- **🔒 Rock-Solid Persistence:** All transactions, balances, and enrollment data are securely saved in a portable **SQLite** database (`atm_data.db`).
- **🏦 Full-Service ATM:** Enjoy seamless Enrollment, Cash Withdrawal, Deposit, and Balance Inquiry features.

## 🛠️ Prerequisites: Get Your System Ready

Before experiencing the speed of DashCash, you need a few essential tools.

### 1. Python (3.8+)

Ensure you have a recent version of Python installed.

- **Check:** Open your terminal/command line and type: `python --version`

### 2. Required Libraries (The DashCash Engine)

The authentication engine requires several powerful Python packages, including `DeepFace` and `tf-keras` (the recommended framework for Keras models).

- **Installation Command:** Run this single command in your terminal. It will install everything you need:
  ```bash
  pip install streamlit pandas numpy deepface opencv-python Pillow tf-keras
  ```
  _Heads up: DeepFace will download large model weights the first time, so this step takes a few minutes._

## 🚀 The Three-Step DashCash Setup

### Step 1: Create the Workspace

1.  Create a main folder for your project (e.g., `DashCash`).
2.  Inside this main folder, create an empty sub-folder named exactly: **`enrolled_faces`** (This is where your secure biometric profile pictures will be stored).

    _Your folder structure must look like this:_

    ```
    DashCash/
    ├── simulator.py (Your code goes here!)
    └── enrolled_faces/
    ```

### Step 2: Save the Code

Copy the final, working Python code into a file named **`simulator.py`** and save it inside your `DashCash` folder.

### Step 3: Ignite the System!

1.  Open your terminal/command line.
2.  Navigate to your `DashCash` folder using the `cd` command.
    ```bash
    cd path/to/DashCash
    ```
3.  Launch the Streamlit application:
    ```bash
    streamlit run simulator.py
    ```

Your web browser will automatically open the DashCash Simulator!

## 🏦 Using the DashCash System

### 1. New User: Enroll Your Face (The "Biometric Signature")

1.  In the sidebar (**Menu**), select **Enroll New User**.
2.  Enter your new **Account Number**, **Full Name**, and **Initial Deposit**.
3.  Use the **camera input** to capture a clear, well-lit picture of your face.
4.  Click **Create Account & Enroll Face**.
    - _Success!_ Your face is now the key to your account.

### 2. Login: Access in a Flash

1.  In the sidebar, switch to the **Login** view.
2.  Use the **camera input** to take a new picture of your face (even if it's slightly different—the AI handles it!).
3.  Click **Authenticate & Access Account**.
    - The DeepFace engine compares your live photo against the stored profiles.
    - If verified, you're logged in instantly!

### 3. Transactions: Seamless Banking

Once logged in, perform any transaction. Every action is immediately written to the `atm_data.db` file, ensuring your balance is always up-to-date.

- Select **Withdrawal**, **Deposit**, or **Balance Check** from the options.
- Enter the amount and click **Complete**.

## 🛑 Troubleshooting Tips

| Issue                                               | Cause                                                                                                | Quick Fix                                                                                            |
| :-------------------------------------------------- | :--------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| **"Authentication Failed. Face not recognized..."** | The live image is too different from the enrolled image, or lighting is poor.                        | Try matching the angle and lighting you used during the initial Enrollment.                          |
| **App is slow on the first run**                    | DeepFace is downloading its core model files (VGG-Face).                                             | **This is normal!** The model is cached after the first use, making all subsequent logins very fast. |
| **"Error: No clear face detected..."**              | Your face was obscured or outside the frame during capture.                                          | Re-take the picture, ensuring your face is clearly visible and centered in good light.               |
| **`StreamlitDuplicateElementId`**                   | You have an older or slightly mixed version of the code where a widget ID was accidentally repeated. | Ensure you've copied the _entire_ final Python code block correctly.                                 |

---

## 📂 Data and Persistence

Remember, the power of DashCash lies in its persistence:

- **`atm_data.db`**: This SQLite file holds your accounts and balances.
- **`enrolled_faces/`**: This directory holds your secure biometric photo profiles.

**DO NOT DELETE** these files and folders if you want your accounts to remain active!
