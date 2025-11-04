# app.py - UniSync Student Resource Hub (Final, Complete Version)

import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
import hashlib 
import os
from pathlib import Path

# --- Configuration & Constants ---
# Define base and upload directories
BASE_DIR = Path(__file__).resolve().parent 
UPLOAD_DIR = BASE_DIR / "static" / "images"

# Create the upload directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True) 

try:
    DB_HOST = st.secrets["mysql"]["host"]
    DB_USER = st.secrets["mysql"]["user"]
    DB_PASSWORD = st.secrets["mysql"]["password"]
    DB_NAME = st.secrets["mysql"]["database"]
except (KeyError, AttributeError):
    st.error("🚨 Configuration Error: Could not find database credentials in secrets.toml.")
    DB_HOST = DB_USER = DB_PASSWORD = DB_NAME = None 
    
DEPARTMENTS = ['Computer Science', 'Electronics and Commn', 'Mechanical', 'Electrical', 'Civil']
IMAGE_PLACEHOLDER = "Click to Upload Image" 

# --- Session State Initialization ---
if 'logged_in_srn' not in st.session_state:
    st.session_state.logged_in_srn = None
if 'page' not in st.session_state:
    st.session_state.page = 'landing' 

# --- UI Setup ---
st.set_page_config(
    page_title="UniSync - Student Resource Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimalist, chic UI
st.markdown("""
<style>
    /* General styles */
    .stApp { background-color: #f7f9fc; color: #1a1a1a; }
    h1, h2, h3 { color: #007bff; } 
    
    /* Buttons */
    .stButton>button {
        background-color: #007bff; color: white; border-radius: 5px; border: 1px solid #007bff;
        padding: 0.5rem 1rem; transition: all 0.2s ease;
    }
    .stButton>button:hover { background-color: #0056b3; border-color: #0056b3; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #e9ecef; }
    
    /* Dark Mode Styling */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #1a1a1a; color: #f7f9fc; }
        h1, h2, h3 { color: #00bfa5; }
        .stButton>button { background-color: #00bfa5; color: black; border-color: #00bfa5; }
        .stButton>button:hover { background-color: #009688; border-color: #009688; }
        [data-testid="stSidebar"] { background-color: #212529; }
    }
</style>
""", unsafe_allow_html=True)

# --- File System Utility ---
def save_uploaded_file(uploaded_file):
    """Saves the uploaded file to the local static/images folder."""
    if uploaded_file is None:
        return None
    
    # Use a unique name
    file_extension = Path(uploaded_file.name).suffix
    unique_filename = f"{Path(uploaded_file.name).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Return the path relative to the app directory (for the DB and st.image to find)
        return str(Path("static") / "images" / unique_filename)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- DB Connection & Utility Functions ---

def get_db_connection():
    if DB_HOST is None: return None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def fetch_all_categories(conn):
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Cat_ID, CONCAT(MainType, ' - ', SubType) AS FullType FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    return categories

# --- UI Redirects (Using st.rerun()) ---
def goto_landing():
    st.session_state.page = 'landing'
    st.rerun()

def goto_login():
    st.session_state.page = 'login'
    st.rerun()

def goto_signup():
    st.session_state.page = 'signup'
    st.rerun()

def goto_home():
    st.session_state.page = 'home'
    st.rerun()

# --- 0. Landing Page ---
def page_landing():
    st.title("Welcome to UniSync - Student Resource Hub 📚🤝")
    st.subheader("Connect with peers to Buy, Sell, Lend, Borrow, and Barter!")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.header("Access Your Account")
        if st.button("Log In", key="landing_login_btn", use_container_width=True):
            goto_login()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.header("New Here?")
        if st.button("Sign Up", key="landing_signup_btn", use_container_width=True):
            goto_signup()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 1. Login Page ---
def page_login():
    st.title("UniSync Login")
    
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown("### Enter your credentials")
        login_srn = st.text_input("SRN or Email", key="login_srn_input")
        login_password = st.text_input("Password", type="password", key="login_pass_input")
        login_submitted = st.form_submit_button("Log In")

        if login_submitted:
            if not login_srn or not login_password:
                st.warning("Please enter both credentials.")
            else:
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    query = "SELECT SRN, Password FROM Student WHERE SRN = %s OR Email = %s"
                    cursor.execute(query, (login_srn, login_srn))
                    user = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if user and verify_password(user['Password'], login_password):
                        st.session_state.logged_in_srn = user['SRN']
                        goto_home()
                    else:
                        st.error("Invalid SRN/Email or Password.")
    
    st.markdown('**Don\'t have an account? Click here to Sign Up**')
    if st.button("Go to Sign Up", key='login_to_signup'):
        goto_signup()

    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. Signup Page ---
def page_signup():
    st.title("UniSync Sign Up")
    
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    with st.form("signup_form"):
        st.markdown("### Create Your Account")
        
        col1, col2 = st.columns(2)
        signup_fname = col1.text_input("First Name")
        signup_lname = col2.text_input("Last Name (Optional)")
        
        signup_srn = st.text_input("SRN (e.g., PES2UG23CS999)", max_chars=13)
        signup_email = st.text_input("Email")
        signup_phone = st.text_input("Phone Number", max_chars=15)
        signup_dept = st.selectbox("Department", DEPARTMENTS)
        signup_password = st.text_input("Password", type="password")
        
        signup_submitted = st.form_submit_button("Create Account")

        if signup_submitted:
            if not all([signup_srn, signup_fname, signup_email, signup_phone, signup_dept, signup_password]):
                st.warning("All mandatory fields are required.")
            else:
                conn = get_db_connection()
                if conn:
                    try:
                        hashed_password = hash_password(signup_password)
                        cursor = conn.cursor()
                        query = """
                        INSERT INTO Student (SRN, FirstName, LastName, Email, Phone, Department, JoinDate, Password)
                        VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s)
                        """
                        cursor.execute(query, (signup_srn, signup_fname, signup_lname, signup_email, signup_phone, signup_dept, hashed_password))
                        conn.commit()
                        cursor.close()
                        st.success(f"Account created successfully for {signup_srn}! Redirecting to home.")
                        st.session_state.logged_in_srn = signup_srn
                        goto_home() 
                    except mysql.connector.Error as err:
                        st.error(f"Signup Failed: SRN or Email/Phone might already exist. Error: {err}")
                    finally:
                        if conn and conn.is_connected():
                            conn.close()

    st.markdown('**Already have an account? Click here to Log In**')
    if st.button("Go to Log In", key='signup_to_login'):
         goto_login()
         
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. Home Page (Browsing & Filtering) ---
def page_home_browse():
    st.sidebar.title(f"Welcome, {st.session_state.logged_in_srn}")
    
    # --- Sidebar Navigation (Main Buttons) ---
    st.sidebar.subheader("Quick Actions")
    if st.sidebar.button("🏠 Browse/Home", use_container_width=True): st.session_state.page = 'home'; st.rerun()
    if st.sidebar.button("💸 **SELL** an Item", use_container_width=True): st.session_state.page = 'upload_sell'; st.rerun()
    if st.sidebar.button("📚 **LEND** an Item", use_container_width=True): st.session_state.page = 'upload_lend'; st.rerun()
    if st.sidebar.button("🔄 **BARTER** an Item", use_container_width=True): st.session_state.page = 'upload_barter'; st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("⚙️ My Activity/Transactions", use_container_width=True): st.session_state.page = 'my_activity'; st.rerun()
    if st.sidebar.button("🚪 Logout", use_container_width=True): st.session_state.logged_in_srn = None; st.session_state.page = 'landing'; st.rerun()

    st.title("Explore UniSync Resources")
    
    conn = get_db_connection()
    if not conn: return
    
    # --- Search Bar and Filters ---
    search_query = st.text_input("🔍 Search by Title or Description", "")
    col_filter1, col_filter2 = st.columns(2)
    categories = fetch_all_categories(conn)
    category_options = ['All Categories'] + [c['FullType'] for c in categories]
    selected_category_name = col_filter1.selectbox("Filter by Category", category_options)
    option_filters = ['All Options', 'Buy/Sell', 'Lend/Borrow', 'Barter']
    selected_option = col_filter2.selectbox("Filter by Transaction Type", option_filters)
    
    # --- Dynamic Query Construction (Includes ImagePath) ---
    base_query = f"""
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, r.ImagePath,
            CONCAT(c.MainType, ' - ', c.SubType) AS CategoryName, c.Cat_ID
        FROM Resource r
        JOIN Category c ON r.CategoryID = c.Cat_ID
        WHERE r.Status = 'Available'
    """
    
    if search_query: base_query += f" AND (r.Title LIKE '%%{search_query}%%' OR r.Description LIKE '%%{search_query}%%')"
    if selected_category_name != 'All Categories':
        selected_cat_id = next((c['Cat_ID'] for c in categories if c['FullType'] == selected_category_name), None)
        if selected_cat_id: base_query += f" AND r.CategoryID = {selected_cat_id}"
            
    df_resources = pd.read_sql(base_query, conn)
    conn.close()

    # --- Display Results ---
    st.markdown("---")
    st.subheader(f"Available Items ({len(df_resources)})")
    
    if df_resources.empty:
        st.info("No items found matching your search and filters.")
        return

    cols = st.columns(3)
    
    for index, row in df_resources.iterrows():
        col = cols[index % 3]
        
        # Determine the primary option for display (Simulated for UI demonstration)
        # We also set the action_page variable here
        if row['ResourceID'] % 3 == 0: option_tag, tag_color, action_page = "BUY/SELL", "#007bff", 'buysell'
        elif row['ResourceID'] % 3 == 1: option_tag, tag_color, action_page = "LEND/BORROW", "#28a745", 'lendborrow'
        else: option_tag, tag_color, action_page = "BARTER", "#ffc107", 'barter'
            
        # Apply option filter
        if selected_option != 'All Options':
            if selected_option == 'Buy/Sell' and action_page != 'buysell': continue
            if selected_option == 'Lend/Borrow' and action_page != 'lendborrow': continue
            if selected_option == 'Barter' and action_page != 'barter': continue

        
        with col:
            # --- FIXED UI RENDERING using st.container ---
            with st.container(border=True): 
                # Header with Tag
                st.markdown(f"#### {row['Title']} <span style='background-color: {tag_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 14px;'>{option_tag}</span>", unsafe_allow_html=True)
                
                # Image Display Logic 
                image_full_path = BASE_DIR / row['ImagePath'] if row['ImagePath'] else None
                
                if image_full_path and os.path.exists(image_full_path):
                    st.image(str(image_full_path), caption=row['Title'], use_column_width='always')
                else:
                    st.markdown(f'<div style="width: 100%; height: 150px; background-color: #f0f0f0; text-align: center; line-height: 150px; color: #777; border-radius: 5px; font-size: 12px;">{IMAGE_PLACEHOLDER}</div>', unsafe_allow_html=True)

                # Details
                st.caption(f"**Category:** {row['CategoryName']} | **Condition:** {row['itemCondition']}")
                st.markdown(f"*{row['Description'][:70]}...*")

                # The functional button - REDIRECTION FIX IMPLEMENTED HERE
                if st.button(f"View/Act on {row['ResourceID']}", key=f"act_{row['ResourceID']}", use_container_width=True):
                     st.session_state.target_resource_id = row['ResourceID']
                     st.session_state.page = action_page # Set page based on item type
                     st.rerun() # Force page reload
            # --- END FIXED UI RENDERING ---


# --- 4. Upload Pages (Sell/Lend/Barter - Image Saving Fix) ---
def page_upload_item(action_type):
    st.sidebar.title(f"Welcome, {st.session_state.logged_in_srn}")
    
    st.header(f"💸 List Item for {action_type.capitalize()}")
    st.markdown("---")

    conn = get_db_connection()
    if not conn: return

    categories = fetch_all_categories(conn)
    category_map = {c['FullType']: c['Cat_ID'] for c in categories}
    category_names = list(category_map.keys())
    
    with st.form(f"upload_{action_type}_form"):
        st.subheader("Item Details")
        
        col_img, col_details = st.columns([1, 2])
        uploaded_file = None
        
        with col_img:
            st.subheader("Image Upload")
            uploaded_file = st.file_uploader("Upload Item Photo (Optional)", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                 st.image(uploaded_file, caption="Uploaded Image Preview")
        
        with col_details:
            title = st.text_input("Item Title (e.g., 'DBMS Book', 'Study Chair')")
            description = st.text_area("Detailed Description", height=100)
            item_condition = st.selectbox("Condition", ['Excellent', 'Good', 'Fair', 'Poor'])
            category_name = st.selectbox("Category", category_names)

            action_specific_data = None
            if action_type == 'sell':
                price = st.number_input("Selling Price (₹)", min_value=1.00, format="%f")
                action_specific_data = price
                button_label = "List Item for Sale"
            elif action_type == 'lend':
                lend_terms = st.text_area("Lending Terms (e.g., Duration, Late Fee info)")
                action_specific_data = lend_terms
                button_label = "List Item for Lending"
            elif action_type == 'barter':
                barter_preference = st.text_area("Barter Preferences (What are you looking for?)")
                action_specific_data = barter_preference
                button_label = "List Item for Barter"
                
        submitted = st.form_submit_button(button_label)

        if submitted:
            image_path_to_db = save_uploaded_file(uploaded_file)
            
            try:
                category_id = category_map[category_name]
                cursor = conn.cursor()
                
                if not title:
                    st.error("Title is required.")
                    return

                # 1. Insert into Resource (NOW including ImagePath)
                query_resource = """
                INSERT INTO Resource (Title, Description, itemCondition, Status, OwnerID, CategoryID, ImagePath)
                VALUES (%s, %s, %s, 'Available', %s, %s, %s)
                """
                cursor.execute(query_resource, (title, description, item_condition, st.session_state.logged_in_srn, category_id, image_path_to_db))
                resource_id = cursor.lastrowid
                
                # 2. Insert into Specific Transaction Table (Only for Sell)
                if action_type == 'sell':
                    query_bs = """
                    INSERT INTO BuySell (ItemID, SellerID, BuyerID, Price, Status, TransactionDate)
                    VALUES (%s, %s, %s, %s, 'Listed', CURDATE())
                    """
                    cursor.execute(query_bs, (resource_id, st.session_state.logged_in_srn, st.session_state.logged_in_srn, action_specific_data))
                
                conn.commit()
                st.success(f"Item '{title}' successfully listed for {action_type}! Resource ID: {resource_id}")
                goto_home()

            except mysql.connector.Error as err:
                st.error(f"Database operation failed: {err}")
            finally:
                cursor.close()
                conn.close()

# --- 5. Transaction Management Pages (Integrated Logic) ---

def page_buysell():
    page_home_browse() # Load sidebar/header
    st.header("🤝 Buy / Sell Management")
    user_srn = st.session_state.logged_in_srn
    
    tab1, tab2 = st.tabs(["Browse Items to Buy", "Confirm Sales"])

    # Tab 1: Browse Items to Buy (R-operation & C-operation for purchase initiation)
    with tab1:
        st.subheader("Available Items for Sale")
        conn = get_db_connection()
        if not conn: return
        
        # Query items listed as Available for sale
        query = """
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, 
            bs.Price, CONCAT(s.FirstName, ' ', s.LastName) AS SellerName
        FROM Resource r
        JOIN Student s ON r.OwnerID = s.SRN
        JOIN BuySell bs ON r.ResourceID = bs.ItemID 
        WHERE r.Status = 'Available' AND r.OwnerID != %s AND bs.Status NOT IN ('Completed', 'PendingConfirmation', 'PendingPayment')
        """
        df = pd.read_sql(query, conn, params=(user_srn,))

        if df.empty:
            st.info("No items currently listed for sale by others.")
        else:
            st.dataframe(df)
            st.markdown("---")
            st.markdown("#### Initiate Purchase")
            buy_resource_id = st.selectbox("Select Resource ID to Purchase", df['ResourceID'].unique())
            
            if st.button("Request Purchase"):
                try:
                    cursor = conn.cursor()
                    
                    # 1. Fetch details to start BuySell transaction properly
                    cursor.execute("SELECT OwnerID, Price FROM BuySell WHERE ItemID = %s LIMIT 1", (buy_resource_id,))
                    res_info = cursor.fetchone()
                    seller_srn = res_info[0]
                    price = res_info[1]

                    # 2. Update the BuySell entry that was created during listing
                    query_update_bs = """
                    UPDATE BuySell
                    SET BuyerID = %s, Status = 'PendingPayment', TransactionDate = CURDATE()
                    WHERE ItemID = %s AND SellerID = %s AND Status = 'Listed'
                    """
                    cursor.execute(query_update_bs, (user_srn, buy_resource_id, seller_srn))
                    
                    conn.commit()
                    st.success(f"Purchase request initiated for Resource ID: {buy_resource_id} (Price: ₹{price:.2f}). Please provide transaction ID in the **Confirm Sales** tab.")
                except mysql.connector.Error as err:
                    st.error(f"Failed to initiate purchase: {err}")
                finally:
                    cursor.close()
        conn.close()

    # Tab 2: Confirm Sales (U-operation - Custom Payment Validation)
    with tab2:
        st.subheader("Payment Validation")
        conn = get_db_connection()
        if not conn: return
        
        # Buyer Action (Providing Transaction ID)
        st.markdown("##### 1. Confirm Your Purchase (Buyer Action)")
        query_buyer = """
        SELECT bs.BuySellID, r.Title, bs.Price, bs.BuyerTransID 
        FROM BuySell bs
        JOIN Resource r ON bs.ItemID = r.ResourceID
        WHERE bs.BuyerID = %s AND bs.BuyerTransID IS NULL AND bs.Status = 'PendingPayment'
        """
        df_buyer = pd.read_sql(query_buyer, conn, params=(user_srn,))
        
        if not df_buyer.empty:
            st.dataframe(df_buyer)
            with st.form("buyer_confirm_form"):
                confirm_buysell_id = st.selectbox("Select BuySellID to Confirm Payment", df_buyer['BuySellID'].unique(), key="buy_trans_id_select")
                provided_trans_id = st.text_input("Enter External Transaction ID (e.g., UPI Ref No.)", key="buy_trans_id_input")
                if st.form_submit_button("Submit Transaction ID"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE BuySell SET BuyerTransID = %s, Status = 'PendingConfirmation' WHERE BuySellID = %s", 
                                       (provided_trans_id, confirm_buysell_id))
                        conn.commit()
                        st.success("Transaction ID submitted! Waiting for the seller's confirmation.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to submit Transaction ID: {err}")
                    finally:
                        cursor.close()

        st.markdown("---")
        # Seller Action (Confirming Transaction ID)
        st.markdown("##### 2. Confirm Buyer's Transaction ID (Seller Action)")
        query_seller = """
        SELECT bs.BuySellID, r.Title, bs.Price, bs.BuyerTransID, s.FirstName AS BuyerName
        FROM BuySell bs
        JOIN Resource r ON bs.ItemID = r.ResourceID
        JOIN Student s ON bs.BuyerID = s.SRN
        WHERE bs.SellerID = %s AND bs.BuyerTransID IS NOT NULL AND bs.SellerConfirm = FALSE AND bs.Status = 'PendingConfirmation'
        """
        df_seller = pd.read_sql(query_seller, conn, params=(user_srn,))

        if not df_seller.empty:
            st.dataframe(df_seller)
            with st.form("seller_confirm_form"):
                confirm_sale_id = st.selectbox("Select BuySellID to CONFIRM Payment Received", df_seller['BuySellID'].unique(), key="sell_trans_id_select")
                if st.form_submit_button("Confirm Payment & Complete Sale"):
                    try:
                        cursor = conn.cursor()
                        # Final confirmation, setting SellerConfirm=TRUE and Status='Completed' (Trigger updates Resource)
                        cursor.execute("UPDATE BuySell SET SellerConfirm = TRUE, Status = 'Completed' WHERE BuySellID = %s", (confirm_sale_id,))
                        conn.commit()
                        st.success(f"Sale for BuySellID {confirm_sale_id} confirmed and completed! The resource status has been updated to 'Sold'.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to confirm sale: {err}")
                    finally:
                        cursor.close()
        else:
             st.info("No sales awaiting your confirmation.")
        conn.close()

def page_lendborrow():
    page_home_browse() 
    st.header("📚 Lend / Borrow Management")
    user_srn = st.session_state.logged_in_srn
    
    tab1, tab2 = st.tabs(["Browse Items to Borrow", "Manage Active Loans"])

    # Tab 1: Browse Items to Borrow (R-operation & C-operation for loan)
    with tab1:
        st.subheader("Available Items to Borrow")
        conn = get_db_connection()
        if not conn: return
        
        query = """
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, 
            CONCAT(s.FirstName, ' ', s.LastName) AS LenderName
        FROM Resource r
        JOIN Student s ON r.OwnerID = s.SRN
        WHERE r.Status = 'Available' AND r.OwnerID != %s
        """
        df = pd.read_sql(query, conn, params=(user_srn,))
        
        if df.empty:
            st.info("No items currently available to borrow.")
            conn.close()
            return

        st.dataframe(df)

        st.markdown("---")
        st.markdown("#### Request to Borrow")
        borrow_resource_id = st.selectbox("Select Resource ID to Borrow", df['ResourceID'].unique())
        start_date = st.date_input("Start Date", datetime.today())
        default_end_date = datetime.today() + pd.Timedelta(days=7) 
        end_date = st.date_input("Planned Return Date (Late fee of ₹10/day applies)", default_end_date)
        
        if st.button("Initiate Borrow"):
            if end_date <= start_date:
                st.error("Return Date must be after Start Date.")
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT OwnerID FROM Resource WHERE ResourceID = %s", (borrow_resource_id,))
                lender_srn = cursor.fetchone()[0]
                
                try:
                    # Call Stored Procedure 'initiate_lend'
                    cursor.callproc('initiate_lend', (borrow_resource_id, lender_srn, user_srn, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 0)) 
                    conn.commit()
                    st.success(f"Borrowing initiated for Resource ID: {borrow_resource_id}. Resource status updated to 'Unavailable'.")
                    st.rerun()
                except mysql.connector.Error as err:
                    st.error(f"Failed to initiate loan: {err}")
                finally:
                    if cursor: cursor.close()
        conn.close()

    # Tab 2: Manage Active Loans (U-operation with Penalty)
    with tab2:
        st.subheader("Manage Items to Return")
        conn = get_db_connection()
        if not conn: return
        
        query = """
        SELECT 
            lb.LendBorrowID, r.Title, lb.StartDate, lb.EndDate, lb.Status, 
            DATEDIFF(CURDATE(), lb.EndDate) AS DaysLate, 
            CONCAT(s.FirstName, ' ', s.LastName) AS LenderName
        FROM LendBorrow lb
        JOIN Resource r ON lb.itemID = r.ResourceID
        JOIN Student s ON lb.LenderID = s.SRN
        WHERE lb.BorrowerID = %s AND lb.Status = 'Ongoing'
        """
        df_active = pd.read_sql(query, conn, params=(user_srn,))

        if df_active.empty:
            st.info("No active items borrowed.")
        else:
            st.dataframe(df_active)

            st.markdown("---")
            st.markdown("#### Confirm Return")
            return_lb_id = st.selectbox("Select LendBorrowID to Mark as Returned", df_active['LendBorrowID'].unique())

            if st.button("Confirm Return"):
                try:
                    cursor = conn.cursor()
                    # Call Stored Procedure 'complete_lend_with_penalty'
                    cursor.callproc('complete_lend_with_penalty', (return_lb_id,))
                    conn.commit()
                    
                    # Fetch calculated penalty for display
                    cursor.execute("SELECT PenaltyAmount FROM LendBorrow WHERE LendBorrowID = %s", (return_lb_id,))
                    penalty = cursor.fetchone()[0]
                    
                    if penalty > 0:
                        st.warning(f"Item returned. **LATE RETURN** - A penalty of **₹{penalty:.2f}** has been applied. Please pay the lender.")
                    else:
                        st.success("Item successfully returned and loan completed! Resource status updated to 'Available'.")
                    st.rerun()
                except mysql.connector.Error as err:
                    st.error(f"Failed to complete loan: {err}")
                finally:
                    if cursor: cursor.close()
        conn.close()

def page_barter():
    page_home_browse() 
    st.header("🔄 Barter Management (Propose & Review)")
    user_srn = st.session_state.logged_in_srn

    tab1, tab2, tab3 = st.tabs(["Propose Barter", "Review Proposals", "My Barters"])
    
    conn = get_db_connection()
    if not conn: return
    user_resources = pd.read_sql("SELECT ResourceID, Title FROM Resource WHERE OwnerID = %s AND Status = 'Available'", conn, params=(user_srn,))
    resource_map = {f"{r['Title']} (ID: {r['ResourceID']})": r['ResourceID'] for r in user_resources.to_dict('records')}
    resource_names = list(resource_map.keys())
    conn.close()

    # Tab 1: Propose Barter (C-operation)
    with tab1:
        st.subheader("Propose a New Barter")
        if not resource_names:
            st.info("You must have available items to propose a barter.")
            return

        conn = get_db_connection()
        if not conn: return
        query_others = """
        SELECT ResourceID, Title, CONCAT(s.FirstName, ' ', s.LastName) AS OwnerName
        FROM Resource r JOIN Student s ON r.OwnerID = s.SRN
        WHERE r.Status = 'Available' AND r.OwnerID != %s
        """
        df_others = pd.read_sql(query_others, conn, params=(user_srn,))
        conn.close()

        if df_others.empty:
            st.info("No available items from other students to barter with.")
            return

        other_map = {f"{r['Title']} (Owner: {r['OwnerName']}) (ID: {r['ResourceID']})": r['ResourceID'] for r in df_others.to_dict('records')}
        other_names = list(other_map.keys())

        with st.form("propose_barter_form"):
            item1_name = st.selectbox("Your Item (Item 1)", resource_names)
            item2_name = st.selectbox("Item You Want (Item 2)", other_names)
            
            if st.form_submit_button("Submit Barter Proposal"):
                item1_id = resource_map[item1_name]
                item2_id = other_map[item2_name]
                
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        # Fetch Accepter ID first
                        cursor.execute("SELECT OwnerID FROM Resource WHERE ResourceID = %s", (item2_id,))
                        accepter_id = cursor.fetchone()[0]
                        
                        # 1. Create a Transaction entry
                        cursor.execute("INSERT INTO Transactions (Type) VALUES ('Barter')")
                        trans_id = cursor.lastrowid
                        
                        # 2. Insert into Barter
                        query = """
                        INSERT INTO Barter (Item1ID, Item2ID, ProposerID, AccepterID, Status, BarterDate, TransactionID)
                        VALUES (%s, %s, %s, %s, 'Pending', CURDATE(), %s)
                        """
                        cursor.execute(query, (item1_id, item2_id, user_srn, accepter_id, trans_id))
                        conn.commit()
                        st.success(f"Barter proposal submitted! Item {item1_id} for Item {item2_id}. Awaiting acceptance.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to submit barter: {err}")
                    finally:
                        cursor.close()
                        conn.close()

    # Tab 2: Review Proposals (U-operation - Acceptance)
    with tab2:
        st.subheader("Proposals to Review")
        conn = get_db_connection()
        if not conn: return
        
        query = """
        SELECT b.BarterID, r1.Title AS ProposerItem, r2.Title AS YourItem, 
               CONCAT(s.FirstName, ' ', s.LastName) AS ProposerName
        FROM Barter b
        JOIN Resource r1 ON b.Item1ID = r1.ResourceID
        JOIN Resource r2 ON b.Item2ID = r2.ResourceID
        JOIN Student s ON b.ProposerID = s.SRN
        WHERE b.AccepterID = %s AND b.Status = 'Pending'
        """
        df_proposals = pd.read_sql(query, conn, params=(user_srn,))
        
        if not df_proposals.empty:
            st.dataframe(df_proposals)
            with st.form("review_barter_form"):
                barter_to_review = st.selectbox("Select Barter ID to Accept/Reject", df_proposals['BarterID'].unique())
                
                col_accept, col_reject = st.columns(2)
                
                if col_accept.form_submit_button("Accept Barter"):
                    try:
                        cursor = conn.cursor()
                        # Trigger tg_barter_update_accepted will handle setting item status to 'Unavailable'
                        cursor.execute("UPDATE Barter SET Status = 'Accepted' WHERE BarterID = %s", (barter_to_review,))
                        conn.commit()
                        st.success(f"Barter ID {barter_to_review} accepted! Item statuses updated. Coordinate the exchange.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to accept barter: {err}")
                    finally:
                        cursor.close()
                
                if col_reject.form_submit_button("Reject Barter"):
                    try:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Barter SET Status = 'Rejected' WHERE BarterID = %s", (barter_to_review,))
                        conn.commit()
                        st.warning(f"Barter ID {barter_to_review} rejected.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to reject barter: {err}")
                    finally:
                        cursor.close()
        else:
            st.info("No pending barter proposals for you to review.")
        conn.close()

    # Tab 3: My Barters (R-operation - Status Check)
    with tab3:
        st.subheader("My Barter History")
        conn = get_db_connection()
        if conn:
            query_history = """
            SELECT b.BarterID, r1.Title AS ItemYouOffered, r2.Title AS ItemYouWanted, b.Status, b.BarterDate
            FROM Barter b
            JOIN Resource r1 ON b.Item1ID = r1.ResourceID
            JOIN Resource r2 ON b.Item2ID = r2.ResourceID
            WHERE b.ProposerID = %s OR b.AccepterID = %s
            """
            df_history = pd.read_sql(query_history, conn, params=(user_srn, user_srn))
            if df_history.empty:
                st.info("No barter history found.")
            else:
                st.dataframe(df_history)
            conn.close()

def page_my_activity():
    page_home_browse() 
    st.header("⚙️ My Resources and Activity")
    user_srn = st.session_state.logged_in_srn
    conn = get_db_connection()
    if not conn: return

    tab1, tab2, tab3 = st.tabs(["My Resources", "My Reminders", "My Reviews"])

    # Tab 1: My Resources (R-operation)
    with tab1:
        st.subheader("Items I Own")
        query_resources = """
        SELECT r.ResourceID, r.Title, r.itemCondition, r.Status, c.MainType
        FROM Resource r
        JOIN Category c ON r.CategoryID = c.Cat_ID
        WHERE r.OwnerID = %s
        """
        df_resources = pd.read_sql(query_resources, conn, params=(user_srn,))
        st.dataframe(df_resources)

    # Tab 2: My Reminders (R-operation, U-operation)
    with tab2:
        st.subheader("Actionable Reminders")
        query_reminders = """
        SELECT ReminderID, Msg, RDate, Status
        FROM Reminder
        WHERE STD_ID = %s AND Status = 'Unread'
        ORDER BY RDate
        """
        df_reminders = pd.read_sql(query_reminders, conn, params=(user_srn,))
        
        if df_reminders.empty:
            st.info("You have no unread reminders.")
        else:
            st.dataframe(df_reminders)
            
            with st.form("mark_read_form"):
                reminders_to_mark = st.multiselect("Select Reminder IDs to mark as Read", df_reminders['ReminderID'].unique())
                if st.form_submit_button("Mark as Read"):
                    try:
                        cursor = conn.cursor()
                        for rem_id in reminders_to_mark:
                            cursor.execute("UPDATE Reminder SET Status = 'Read' WHERE ReminderID = %s", (rem_id,))
                        conn.commit()
                        st.success(f"Marked {len(reminders_to_mark)} reminder(s) as Read.")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to update reminder: {err}")
                    finally:
                        cursor.close()

    # Tab 3: My Reviews (C/R-operation)
    with tab3:
        st.subheader("Items I've Reviewed")
        query_reviews = """
        SELECT rv.Rating, rv.Comments, r.Title, r.ResourceID
        FROM Review rv JOIN Resource r ON rv.ItemID = r.ResourceID WHERE rv.STD_ID = %s
        """
        df_reviews = pd.read_sql(query_reviews, conn, params=(user_srn,))
        st.dataframe(df_reviews)

        st.markdown("---")
        st.subheader("Submit a New Review")
        query_eligible = """
        SELECT DISTINCT r.ResourceID, r.Title
        FROM Resource r
        JOIN LendBorrow lb ON r.ResourceID = lb.ItemID AND lb.BorrowerID = %s AND lb.Status = 'Completed'
        LEFT JOIN Review rv ON r.ResourceID = rv.ItemID AND rv.STD_ID = %s
        WHERE rv.ReviewID IS NULL
        UNION
        SELECT DISTINCT r.ResourceID, r.Title
        FROM Resource r
        JOIN BuySell bs ON r.ResourceID = bs.ItemID AND bs.BuyerID = %s AND bs.Status = 'Completed'
        LEFT JOIN Review rv ON r.ResourceID = rv.ItemID AND rv.STD_ID = %s
        WHERE rv.ReviewID IS NULL
        """
        df_eligible = pd.read_sql(query_eligible, conn, params=(user_srn, user_srn, user_srn, user_srn))
        
        if not df_eligible.empty:
            eligible_map = {f"{r['Title']} (ID: {r['ResourceID']})": r['ResourceID'] for r in df_eligible.to_dict('records')}
            eligible_names = list(eligible_map.keys())

            with st.form("new_review_form"):
                review_item_name = st.selectbox("Select Item to Review", eligible_names)
                rating = st.slider("Rating (1-5)", 1, 5, 5)
                comment = st.text_area("Comments (Optional)")
                
                if st.form_submit_button("Submit Review"):
                    review_item_id = eligible_map[review_item_name]
                    try:
                        cursor = conn.cursor()
                        query_insert = "INSERT INTO Review (Rating, Comments, STD_ID, ItemID) VALUES (%s, %s, %s, %s)"
                        cursor.execute(query_insert, (rating, comment, user_srn, review_item_id))
                        conn.commit()
                        st.success(f"Review submitted for {review_item_name}!")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to submit review: {err}")
                    finally:
                        cursor.close()
        else:
            st.info("No items are eligible for a new review.")

    conn.close()

# --- Main Router ---
if st.session_state.logged_in_srn is None:
    if st.session_state.page == 'login':
        page_login()
    elif st.session_state.page == 'signup':
        page_signup()
    else:
        page_landing() 

else:
    if st.session_state.page == 'home':
        page_home_browse()
    elif st.session_state.page == 'upload_sell':
        page_upload_item('sell')
    elif st.session_state.page == 'upload_lend':
        page_upload_item('lend')
    elif st.session_state.page == 'upload_barter':
        page_upload_item('barter')
    elif st.session_state.page == 'buysell':
        page_buysell()
    elif st.session_state.page == 'lendborrow':
        page_lendborrow()
    elif st.session_state.page == 'barter':
        page_barter()
    elif st.session_state.page == 'my_activity':
        page_my_activity()
    else:
        page_home_browse()
