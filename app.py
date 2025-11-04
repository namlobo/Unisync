# app.py - UniSync Student Resource Hub (Final Version)

import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
import hashlib 

# --- Configuration (using st.secrets) ---
try:
    # Access the database credentials from the .streamlit/secrets.toml file
    # Ensure your secrets.toml file has a [mysql] section with host, user, password, and database.
    DB_HOST = st.secrets["mysql"]["host"]
    DB_USER = st.secrets["mysql"]["user"]
    DB_PASSWORD = st.secrets["mysql"]["password"]
    DB_NAME = st.secrets["mysql"]["database"]
except (KeyError, AttributeError):
    st.error("🚨 Configuration Error: Could not find database credentials in secrets.toml.")
    DB_HOST = DB_USER = DB_PASSWORD = DB_NAME = None 
    
# --- Constants ---
DEPARTMENTS = ['Computer Science', 'Electronics and Commn', 'Mechanical', 'Electrical', 'Civil']
IMAGE_PLACEHOLDER = "" 

# --- Session State Initialization ---
if 'logged_in_srn' not in st.session_state:
    st.session_state.logged_in_srn = None
if 'page' not in st.session_state:
    st.session_state.page = 'landing' # Start on the landing page

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
    .redirect-link { cursor: pointer; color: #28a745; text-decoration: underline; } 
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #e9ecef; }
    
    /* Item Card Container */
    .item-card {
        background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;
        box-shadow: 0 2px 4px 0 rgba(0,0,0,0.1);
        display: flex; flex-direction: row;
    }
    .item-image { width: 150px; height: 150px; background-color: #f0f0f0; border-radius: 5px; margin-right: 15px; line-height: 150px; text-align: center; color: #777; font-size: 12px; }
    .item-details { flex-grow: 1; }
    .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;}
    .item-header h4 { margin: 0; }
    .item-tag { 
        background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; 
        font-weight: bold; margin-left: 10px;
    }
    
    /* Dark Mode Styling */
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #1a1a1a; color: #f7f9fc; }
        h1, h2, h3 { color: #00bfa5; }
        .stButton>button { background-color: #00bfa5; color: black; border-color: #00bfa5; }
        .stButton>button:hover { background-color: #009688; border-color: #009688; }
        .redirect-link { color: #00bfa5; }
        [data-testid="stSidebar"] { background-color: #212529; }
        .item-card { background-color: #2c3034; box-shadow: 0 4px 8px 0 rgba(255,255,255,0.1); }
        .item-image { background-color: #444; color: #aaa; }
    }
</style>
""", unsafe_allow_html=True)

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

def fetch_user_resources(conn, srn):
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ResourceID, Title FROM Resource WHERE OwnerID = %s AND Status = 'Available'", (srn,))
    resources = cursor.fetchall()
    cursor.close()
    return resources

# --- UI Redirects (FIXED: Using st.rerun()) ---
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

# --- Page Definitions ---

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
                        st.success(f"Account created successfully for {signup_srn}! Redirecting to login.")
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
    if st.sidebar.button("🏠 Browse/Home", use_container_width=True):
        st.session_state.page = 'home'
        st.rerun()
    if st.sidebar.button("💸 **SELL** an Item", use_container_width=True):
        st.session_state.page = 'upload_sell'
        st.rerun()
    if st.sidebar.button("📚 **LEND** an Item", use_container_width=True):
        st.session_state.page = 'upload_lend'
        st.rerun()
    if st.sidebar.button("🔄 **BARTER** an Item", use_container_width=True):
        st.session_state.page = 'upload_barter'
        st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("⚙️ My Activity/Transactions", use_container_width=True):
        st.session_state.page = 'my_activity'
        st.rerun()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in_srn = None
        st.session_state.page = 'landing'
        st.rerun()

    st.title("Explore UniSync Resources")
    
    conn = get_db_connection()
    if not conn: return
    
    # --- Search Bar and Filters ---
    search_query = st.text_input("🔍 Search by Title or Description", "")
    
    col_filter1, col_filter2 = st.columns(2)
    
    # Category Filter
    categories = fetch_all_categories(conn)
    category_options = ['All Categories'] + [c['FullType'] for c in categories]
    selected_category_name = col_filter1.selectbox("Filter by Category", category_options)
    
    # Transaction Type Filter (Option-wise filter)
    # This filter logic would require complex joins on the backend (BuySell, LendBorrow, Barter)
    option_filters = ['All Options', 'Buy/Sell', 'Lend/Borrow', 'Barter']
    selected_option = col_filter2.selectbox("Filter by Transaction Type", option_filters)
    
    # --- Dynamic Query Construction ---
    
    # Base Query: Select all available resources (simplified view for browsing)
    base_query = f"""
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, 
            CONCAT(c.MainType, ' - ', c.SubType) AS CategoryName, c.Cat_ID
        FROM Resource r
        JOIN Category c ON r.CategoryID = c.Cat_ID
        WHERE r.Status = 'Available'
    """
    
    # Add Search Filter
    if search_query:
        base_query += f"""
        AND (r.Title LIKE '%{search_query}%' OR r.Description LIKE '%{search_query}%')
        """
        
    # Add Category Filter
    if selected_category_name != 'All Categories':
        selected_cat_id = next((c['Cat_ID'] for c in categories if c['FullType'] == selected_category_name), None)
        if selected_cat_id:
            base_query += f" AND r.CategoryID = {selected_cat_id}"
            
    # Execute base query
    df_resources = pd.read_sql(base_query, conn)
    conn.close()

    # --- Display Results ---
    st.markdown("---")
    st.subheader(f"Available Items ({len(df_resources)})")
    
    if df_resources.empty:
        st.info("No items found matching your search and filters.")
        return

    # Dynamic columns display (3 per row)
    cols = st.columns(3)
    
    for index, row in df_resources.iterrows():
        col = cols[index % 3]
        
        # Determine the primary option for display (Simulated for UI demonstration)
        if row['ResourceID'] % 3 == 0:
            option_tag = "BUY/SELL"
            tag_color = "#007bff"
        elif row['ResourceID'] % 3 == 1:
            option_tag = "LEND/BORROW"
            tag_color = "#28a745"
        else:
            option_tag = "BARTER"
            tag_color = "#ffc107"
            
        # Apply option filter (frontend filtering for demonstration)
        if selected_option != 'All Options':
            if selected_option == 'Buy/Sell' and option_tag != 'BUY/SELL': continue
            if selected_option == 'Lend/Borrow' and option_tag != 'LEND/BORROW': continue
            if selected_option == 'Barter' and option_tag != 'BARTER': continue

        # Item Card HTML structure
        card_html = f"""
        <div class="item-card">
            <div class="item-image">
                {IMAGE_PLACEHOLDER} 
            </div>
            <div class="item-details">
                <div class="item-header">
                    <h4>{row['Title']}</h4>
                    <span class="item-tag" style="background-color: {tag_color};">{option_tag}</span>
                </div>
                <p><strong>Category:</strong> {row['CategoryName']}</p>
                <p><strong>Condition:</strong> {row['itemCondition']}</p>
                <p>{row['Description'][:100]}...</p>
            </div>
        </div>
        """
        
        with col:
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(f"View/Act on {row['ResourceID']}", key=f"act_{row['ResourceID']}", use_container_width=True):
                 st.session_state.target_resource_id = row['ResourceID']
                 st.info(f"Redirecting to action for Resource ID: {row['ResourceID']}")
                 # Logic to redirect based on the transaction type would go here

# --- 4. Upload Pages (Sell/Lend/Barter) ---
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
        
        with col_img:
            st.subheader("Image Upload")
            uploaded_file = st.file_uploader("Upload Item Photo (Optional)", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                 st.image(uploaded_file, caption="Uploaded Image Preview")
            else:
                 st.markdown(f'<div class="item-image" style="width: 100%; height: 200px;">{IMAGE_PLACEHOLDER}</div>', unsafe_allow_html=True)
        
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
            try:
                category_id = category_map[category_name]
                cursor = conn.cursor()
                
                if not title:
                    st.error("Title is required.")
                    return

                # 1. Insert into Resource (Status starts as 'Available')
                query_resource = """
                INSERT INTO Resource (Title, Description, itemCondition, Status, OwnerID, CategoryID)
                VALUES (%s, %s, %s, 'Available', %s, %s)
                """
                cursor.execute(query_resource, (title, description, item_condition, st.session_state.logged_in_srn, category_id))
                resource_id = cursor.lastrowid
                
                # 2. Insert into Specific Transaction Table (Only for Sell, others are demand-driven)
                if action_type == 'sell':
                    query_bs = """
                    INSERT INTO BuySell (ItemID, SellerID, BuyerID, Price, Status, TransactionDate)
                    VALUES (%s, %s, %s, %s, 'Listed', CURDATE())
                    """
                    # Placeholder BuyerID is the SellerID for 'Listed' status
                    cursor.execute(query_bs, (resource_id, st.session_state.logged_in_srn, st.session_state.logged_in_srn, action_specific_data))
                
                conn.commit()
                st.success(f"Item '{title}' successfully listed for {action_type}! Resource ID: {resource_id}")
                st.info("Redirecting to Home page to browse...")
                goto_home()

            except mysql.connector.Error as err:
                st.error(f"Database operation failed: {err}")
            finally:
                cursor.close()
                conn.close()

# --- Placeholder Functions for the other pages (You must populate these with your CRUD logic) ---
def page_buysell():
    # Placeholder for the complex BuySell/Confirmation logic from the earlier solution
    page_home_browse()
    st.header("🤝 Buy / Sell Management (WIP)")
    st.info("Here you would put the full Buy/Sell/Confirm Sales tabs from the earlier solution.")

def page_lendborrow():
    page_home_browse()
    st.header("📚 Lend / Borrow Management (WIP)")
    st.info("Here you would put the full Lend/Borrow/Manage Loans tabs from the earlier solution.")

def page_barter():
    page_home_browse()
    st.header("🔄 Barter Management (WIP)")
    st.info("Here you would put the full Barter Proposal/Review tabs from the earlier solution.")

def page_my_activity():
    page_home_browse()
    st.header("⚙️ My Resources and Activity (WIP)")
    st.info("Here you would put the full My Resources/Reminders/Reviews tabs from the earlier solution.")

# --- Main Router ---
if st.session_state.logged_in_srn is None:
    # Public Pages
    if st.session_state.page == 'login':
        page_login()
    elif st.session_state.page == 'signup':
        page_signup()
    else:
        page_landing() # Default to landing page

else:
    # Authenticated Pages Router
    if st.session_state.page == 'home':
        page_home_browse()
    # Transaction Upload Pages
    elif st.session_state.page == 'upload_sell':
        page_upload_item('sell')
    elif st.session_state.page == 'upload_lend':
        page_upload_item('lend')
    elif st.session_state.page == 'upload_barter':
        page_upload_item('barter')
    # Transaction Management Pages (Need to be fully implemented with your CRUD logic)
    elif st.session_state.page == 'buysell':
        page_buysell()
    elif st.session_state.page == 'lendborrow':
        page_lendborrow()
    elif st.session_state.page == 'barter':
        page_barter()
    elif st.session_state.page == 'my_activity':
        page_my_activity()
    else:
        page_home_browse() # Fallback to home/browse