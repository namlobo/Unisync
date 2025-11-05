# app.py - UniSync Student Resource Hub (FIXED: Critical Issues Patched)

import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
import hashlib 
import os
from pathlib import Path

# --- Configuration & Constants ---
BASE_DIR = Path(__file__).resolve().parent 
UPLOAD_DIR = BASE_DIR / "static" / "images"
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
if 'logged_in_srn' not in st.session_state: st.session_state.logged_in_srn = None
if 'page' not in st.session_state: st.session_state.page = 'landing' 
if 'history' not in st.session_state: st.session_state.history = ['landing']
# We will initialize other flags (like 'barter_proposed') inside their respective pages

# --- File System Utility (Remains the same) ---
def save_uploaded_file(uploaded_file):
    if uploaded_file is None: return None
    file_extension = Path(uploaded_file.name).suffix
    unique_filename = f"{Path(uploaded_file.name).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(Path("static") / "images" / unique_filename)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- FIX 1: Add a function to reset submission flags ---
def reset_submission_flags():
    """Resets all form submission flags when navigating."""
    if 'barter_proposed' in st.session_state:
        st.session_state.barter_proposed = False
    # Add other flags here if you create more, e.g.:
    # st.session_state.review_submitted = False

# --- FIX 2: Update Navigation to reset flags ---
def navigate_to(page_name):
    reset_submission_flags() # Reset flags on any navigation
    if not st.session_state.history or st.session_state.history[-1] != page_name:
        st.session_state.history.append(page_name)
    st.session_state.page = page_name
    st.rerun()

# --- FIX 3: Update Go Back to reset flags ---
def go_back():
    """Navigates to the previous page in history."""
    reset_submission_flags() # Reset flags on any navigation
    if len(st.session_state.history) > 1:
        st.session_state.history.pop()
        previous_page = st.session_state.history.pop()
        navigate_to(previous_page)
    else:
        navigate_to('home' if st.session_state.logged_in_srn else 'landing')

def render_back_button():
    """Renders a back button on sub-pages."""
    if st.session_state.page not in ['landing', 'home']:
        st.markdown('<div style="margin-bottom: 20px;">', unsafe_allow_html=True)
        if st.button("⬅️ Go Back", key="back_btn"):
            go_back()
        st.markdown('</div>', unsafe_allow_html=True)
            
# --- DB Connection & Utility Functions ---

def get_db_connection():
    if DB_HOST is None: return None
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Database Connection Error: {err}")
        return None

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password): return stored_hash == hash_password(provided_password)

def fetch_all_categories(conn):
    """
    Fetches only the MainType names for the dropdown (CORRECTED FIX).
    """
    if not conn: return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            MIN(Cat_ID) AS Cat_ID, 
            MainType AS FullType 
        FROM Category
        GROUP BY MainType
        ORDER BY 
            CASE WHEN MainType = 'Miscellaneous' THEN 1 ELSE 0 END, -- <-- FIX: Changed 'Misc' to 'Miscellaneous'
            MainType
    """)
    categories = cursor.fetchall()
    cursor.close()
    return categories

# --- 0. Landing Page ---
def page_landing():
    st.title("Welcome to UniSync - Student Resource Hub 📚🤝")
    st.subheader("Connect with peers to Buy, Sell, Lend, Borrow, and Barter!")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Log In", key="landing_login_btn", use_container_width=True): navigate_to('login')
    with col2:
        if st.button("Sign Up", key="landing_signup_btn", use_container_width=True): navigate_to('signup')

# --- 1. Login Page ---
def page_login():
    if st.button("⬅️ Back to Landing", key="login_to_landing"): navigate_to('landing')
    st.title("UniSync Login")
    
    with st.form("login_form"):
        st.markdown("### Enter your credentials")
        login_srn = st.text_input("SRN or Email", key="login_srn_input")
        login_password = st.text_input("Password", type="password", key="login_pass_input")
        login_submitted = st.form_submit_button("Log In")

        if login_submitted:
            if not login_srn or not login_password: st.warning("Please enter both credentials."); return
            
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT SRN, Password FROM Student WHERE SRN = %s OR Email = %s"
                cursor.execute(query, (login_srn, login_srn))
                user = cursor.fetchone()
                
                if user and verify_password(user['Password'], login_password):
                    st.session_state.logged_in_srn = user['SRN']
                    navigate_to('home')
                else:
                    st.error("Invalid SRN/Email or Password.")
                conn.close()
    
    st.markdown('**Don\'t have an account?**')
    if st.button("Go to Sign Up", key='login_to_signup'): navigate_to('signup')

# --- 2. Signup Page ---
def page_signup():
    render_back_button()
    st.title("UniSync Sign Up")
    
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
            if not all([signup_srn, signup_fname, signup_email, signup_phone, signup_dept, signup_password]): st.warning("All mandatory fields are required."); return
            
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
                    st.session_state.logged_in_srn = signup_srn
                    st.success(f"Account created successfully for {signup_srn}! Redirecting to home.")
                    navigate_to('home') 
                except mysql.connector.Error as err:
                    st.error(f"Signup Failed: SRN or Email/Phone might already exist. Error: {err}")
                finally:
                    conn.close()

    st.markdown('**Already have an account?**')
    if st.button("Go to Log In", key='login_to_signup'): navigate_to('login')

# --- 3. Home Page (Browsing & Filtering) ---
def page_home_browse():
    st.sidebar.title(f"Welcome, {st.session_state.logged_in_srn}")
    
    # --- Sidebar Navigation (Main Buttons) ---
    st.sidebar.subheader("Quick Actions")
    if st.sidebar.button("🏠 Browse/Home", use_container_width=True): navigate_to('home')
    if st.sidebar.button("💸 **SELL** an Item", use_container_width=True): navigate_to('upload_sell')
    if st.sidebar.button("📚 **LEND** an Item", use_container_width=True): navigate_to('upload_lend')
    if st.sidebar.button("🔄 **BARTER** an Item", use_container_width=True): navigate_to('upload_barter')
    st.sidebar.markdown("---")
    if st.sidebar.button("⚙️ My Activity/Transactions", use_container_width=True): navigate_to('my_activity')
    if st.sidebar.button("🚪 Logout", use_container_width=True): 
        # --- FIX: Also reset flags on logout ---
        reset_submission_flags()
        st.session_state.logged_in_srn = None
        st.session_state.page = 'landing'
        st.rerun()

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
    
    # --- *** CRITICAL FIX 3: SQL Injection Patch and Dynamic Query ---
    
    # Base query now selects the ListingType
    base_query = """
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, r.ImagePath, r.ListingType,
            CONCAT(c.MainType, ' - ', c.SubType) AS CategoryName, c.Cat_ID
        FROM Resource r
        JOIN Category c ON r.CategoryID = c.Cat_ID
    """
    
    # Use parameterized queries to prevent SQL Injection
    where_clauses = ["r.Status = 'Available'"]
    params = []
    
    if search_query:
        where_clauses.append("(r.Title LIKE %s OR r.Description LIKE %s)")
        params.extend([f"%%{search_query}%%", f"%%{search_query}%%"])
    
    # Category Filtering Logic (Handles MainType selection)
    if selected_category_name != 'All Categories':
        # This part is safe as it's not direct user input
        where_clauses.append("c.MainType = %s")
        params.append(selected_category_name)

    # Apply Transaction Type filter
    if selected_option != 'All Options':
        type_map = {'Buy/Sell': 'Sell', 'Lend/Borrow': 'Lend', 'Barter': 'Barter'}
        where_clauses.append("r.ListingType = %s")
        params.append(type_map[selected_option])
    
    # Finalize query
    final_query = base_query + " WHERE " + " AND ".join(where_clauses)
    
    # Pass parameters safely to pandas
    df_resources = pd.read_sql(final_query, conn, params=params)
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
        
        # --- *** CRITICAL FIX 4: Use ListingType, not ResourceID % 3 ***
        # This correctly identifies the item type based on data from the DB
        listing_type = row['ListingType']
        if listing_type == 'Sell': 
            option_tag, tag_color, action_page = "BUY/SELL", "#007bff", 'buysell'
        elif listing_type == 'Lend': 
            option_tag, tag_color, action_page = "LEND/BORROW", "#28a745", 'lendborrow'
        else: # Barter
            option_tag, tag_color, action_page = "BARTER", "#ffc107", 'barter'
            
        # Note: The filter logic is now handled by the SQL query, 
        # so the old Python `if selected_option ... continue` block is no longer needed.
        
        with col:
            with st.container(border=True): 
                st.markdown(f"#### {row['Title']} <span style='background-color: {tag_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 14px;'>{option_tag}</span>", unsafe_allow_html=True)
                
                image_full_path = BASE_DIR / row['ImagePath'] if row['ImagePath'] else None
                
                if row['ImagePath'] and os.path.exists(image_full_path):
                    # --- FIX: Hide Warning ---
                    st.image(str(image_full_path), caption=row['Title'], use_container_width=True)
                else:
                    st.markdown(f'<div style="width: 100%; height: 150px; background-color: #f0f0f0; text-align: center; line-height: 150px; color: #777; border-radius: 5px; font-size: 12px;">{IMAGE_PLACEHOLDER}</div>', unsafe_allow_html=True)

                st.caption(f"**Category:** {row['CategoryName']} | **Condition:** {row['itemCondition']}")
                st.markdown(f"*{row['Description'][:70]}...*")

                if st.button(f"View/Act on {row['ResourceID']}", key=f"act_{row['ResourceID']}", use_container_width=True):
                    # Store target_resource_id only if needed by target page (e.g., buysell)
                    # st.session_state.target_resource_id = row['ResourceID'] 
                    navigate_to(action_page) 


# --- 4. Upload Pages ---
def page_upload_item(action_type):
    render_back_button()
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
            # --- FIX: Hide Warning ---
            if uploaded_file: st.image(uploaded_file, caption="Uploaded Image Preview", use_container_width=True)
        
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
                selected_main_type = category_name 
                cursor = conn.cursor()
                cursor.execute("SELECT MIN(Cat_ID) FROM Category WHERE MainType = %s GROUP BY MainType", (selected_main_type,))
                cat_row = cursor.fetchone()
                category_id = cat_row[0] if cat_row else None

                if not title: st.error("Title is required."); return
                if category_id is None: st.error("Category ID could not be determined. Please ensure the selected category exists in the database."); return

                # --- *** CRITICAL FIX 5: Insert the ListingType into Resource ***
                # This ensures the item is correctly tagged from the moment it's created.
                query_resource = """
                INSERT INTO Resource (Title, Description, itemCondition, Status, OwnerID, CategoryID, ImagePath, ListingType)
                VALUES (%s, %s, %s, 'Available', %s, %s, %s, %s)
                """
                cursor.execute(query_resource, (title, description, item_condition, st.session_state.logged_in_srn, category_id, image_path_to_db, action_type))
                resource_id = cursor.lastrowid
                
                # This part of your logic was already correct:
                # Only 'sell' creates a corresponding record immediately.
                # 'lend' and 'barter' items are just listed as resources, 
                # which is correct for this app design.
                if action_type == 'sell':
                    query_bs = """
                    INSERT INTO BuySell (ItemID, SellerID, Price, Status, TransactionDate)
                    VALUES (%s, %s, %s, 'Listed', CURDATE())
                    """
                    # Note: Removed BuyerID from insert, as it's NULL on listing
                    cursor.execute(query_bs, (resource_id, st.session_state.logged_in_srn, action_specific_data))
                
                conn.commit()
                st.success(f"Item '{title}' successfully listed for {action_type}! Resource ID: {resource_id}")
                navigate_to('home') 

            except mysql.connector.Error as err:
                st.error(f"Database operation failed: {err}")
            finally:
                cursor.close()
                conn.close()

# --- 5. Transaction Management Pages (Integrated Logic) ---

def page_buysell():
    render_back_button()
    st.header("🤝 Buy / Sell Management")
    user_srn = st.session_state.logged_in_srn
    
    tab1, tab2 = st.tabs(["Browse Items to Buy", "Confirm Sales"])

    # Tab 1: Browse Items to Buy (R-operation & C-operation for purchase initiation)
    with tab1:
        st.subheader("Available Items for Sale")
        conn = get_db_connection()
        if not conn: return
        
        # This query is now correct because the homepage 
        # only sends users here for items that are ACTUALLY for sale.
        query = """
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, 
            bs.Price, CONCAT(s.FirstName, ' ', s.LastName) AS SellerName
        FROM Resource r
        JOIN Student s ON r.OwnerID = s.SRN
        JOIN BuySell bs ON r.ResourceID = bs.ItemID 
        WHERE r.Status = 'Available' 
          AND r.ListingType = 'Sell' -- Ensures it's a 'Sell' item
          AND r.OwnerID != %s 
          AND bs.Status = 'Listed' -- Only show items that are 'Listed'
        """
        df = pd.read_sql(query, conn, params=(user_srn,))

        if df.empty:
            st.info("No items currently listed for sale by others.")
        else:
            st.dataframe(df)
            st.markdown("---")
            st.markdown("#### Initiate Purchase")
            
            # Check if there are any items left to select
            if df['ResourceID'].empty:
                st.info("No items available to purchase.")
                conn.close()
                return

            buy_resource_id = st.selectbox("Select Resource ID to Purchase", df['ResourceID'].unique())
            
            if st.button("Request Purchase"):
                try:
                    cursor = conn.cursor()
                    
                    # Your payment logic is correct
                    cursor.execute("SELECT SellerID, Price FROM BuySell WHERE ItemID = %s AND Status = 'Listed' LIMIT 1", (buy_resource_id,))
                    res_info = cursor.fetchone()
                    
                    if not res_info:
                        st.error("This item is no longer available or already pending.")
                        return
                    
                    seller_srn = res_info[0]
                    price = res_info[1]

                    query_update_bs = """
                    UPDATE BuySell
                    SET BuyerID = %s, Status = 'PendingPayment', TransactionDate = CURDATE()
                    WHERE ItemID = %s AND SellerID = %s AND Status = 'Listed'
                    """
                    cursor.execute(query_update_bs, (user_srn, buy_resource_id, seller_srn))
                    
                    conn.commit()
                    st.success(f"Purchase request initiated for Resource ID: {buy_resource_id} (Price: ₹{price:.2f}). Please provide transaction ID in the **Confirm Sales** tab.")
                    st.rerun() # Rerun to update the dataframe
                except mysql.connector.Error as err:
                    st.error(f"Failed to initiate purchase: {err}")
                finally:
                    cursor.close()
        conn.close()

    # Tab 2: Confirm Sales (This section is correct and implements your payment flow)
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
        else:
            st.info("You have no pending payments to confirm.")

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
    render_back_button()
    st.header("📚 Lend / Borrow Management")
    user_srn = st.session_state.logged_in_srn
    
    tab1, tab2 = st.tabs(["Browse Items to Borrow", "Manage Active Loans"])

    # Tab 1: Browse Items to Borrow (R-operation & C-operation for loan)
    with tab1:
        st.subheader("Available Items to Borrow")
        conn = get_db_connection()
        if not conn: return
        
        # This query is now correct because the homepage 
        # only sends users here for items that are ACTUALLY for lend.
        query = """
        SELECT 
            r.ResourceID, r.Title, r.Description, r.itemCondition, 
            CONCAT(s.FirstName, ' ', s.LastName) AS LenderName
        FROM Resource r
        JOIN Student s ON r.OwnerID = s.SRN
        WHERE r.Status = 'Available' 
          AND r.ListingType = 'Lend' -- This is the fix
          AND r.OwnerID != %s
        """
        df = pd.read_sql(query, conn, params=(user_srn,))
        
        if df.empty:
            st.info("No items currently available to borrow.")
            conn.close()
            return

        st.dataframe(df)

        st.markdown("---")
        st.markdown("#### Request to Borrow")
        
        if df['ResourceID'].empty:
            conn.close()
            return
            
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
                lender_srn_tuple = cursor.fetchone()
                
                if not lender_srn_tuple:
                    st.error("Resource not found.")
                    cursor.close()
                    conn.close()
                    return
                
                lender_srn = lender_srn_tuple[0]
                
                try:
                    # Your logic for calling the stored procedure is correct.
                    cursor.callproc('initiate_lend', (borrow_resource_id, lender_srn, user_srn, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), 0)) 
                    conn.commit()
                    st.success(f"Borrowing initiated for Resource ID: {borrow_resource_id}. Resource status updated to 'Unavailable'.")
                    st.rerun()
                except mysql.connector.Error as err:
                    st.error(f"Failed to initiate loan: {err}")
                finally:
                    if cursor: cursor.close()
        conn.close()

    # Tab 2: Manage Active Loans (This logic was already correct)
    with tab2:
        st.subheader("Manage Items to Return")
        conn = get_db_connection()
        if not conn: return
        
        query = """
        SELECT 
            lb.LendBorrowID, r.Title, lb.StartDate, lb.EndDate, lb.Status, 
            DATEDIFF(CURDATE(), lb.EndDate) AS DaysLate, 
            r.ResourceID
        FROM LendBorrow lb
        JOIN Resource r ON lb.itemID = r.ResourceID
        WHERE lb.BorrowerID = %s
        ORDER BY lb.StartDate DESC
        """
        df_loans = pd.read_sql(query, conn, params=(user_srn,))

        if df_loans.empty:
            st.info("No active or historical items borrowed.")
        else:
            st.dataframe(df_loans)
            
            st.markdown("---")
            st.markdown("#### Item Actions")

            # Actions for ONGOING loans
            df_ongoing = df_loans[df_loans['Status'] == 'Ongoing']
            if not df_ongoing.empty:
                return_id = st.selectbox("Select Loan ID to Return", df_ongoing['LendBorrowID'].unique(), key="return_id_select")
                
                if st.button("Confirm Return Early / On Time", key="confirm_return_btn"):
                    try:
                        cursor = conn.cursor()
                        cursor.callproc('complete_lend_with_penalty', (return_id,))
                        conn.commit()
                        
                        cursor.execute("SELECT PenaltyAmount FROM LendBorrow WHERE LendBorrowID = %s", (return_id,))
                        penalty_tuple = cursor.fetchone()
                        penalty = penalty_tuple[0] if penalty_tuple else 0
                        
                        if penalty > 0:
                            st.warning(f"Item returned. **LATE RETURN** - A penalty of **₹{penalty:.2f}** has been applied.")
                        else:
                            st.success("Item successfully returned and loan completed!")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to process return: {err}")
                    finally:
                        if cursor: cursor.close()

            # --- REVIEW BUTTON HINT: Display review options for COMPLETED loans ---
            df_completed_unreviewed = df_loans[
                (df_loans['Status'] == 'Completed') & 
                (~df_loans['ResourceID'].isin(pd.read_sql("SELECT ItemID FROM Review WHERE STD_ID = %s", conn, params=(user_srn,))['ItemID']))
            ]
            
            if not df_completed_unreviewed.empty:
                st.info("You have completed loans pending review. Please use the 'My Reviews' tab in 'My Activity'.")
                
        conn.close()

def page_barter():
    render_back_button()
    st.header("🔄 Barter Management (Propose & Review)")
    user_srn = st.session_state.logged_in_srn

    # --- FIX: Initialize the session state flag for this page ---
    if 'barter_proposed' not in st.session_state:
        st.session_state.barter_proposed = False

    tab1, tab2, tab3 = st.tabs(["Propose Barter", "Review Proposals", "My Barters"])
    
    conn = get_db_connection()
    if not conn: return
    # Users can only offer their own 'Barter' items
    user_resources = pd.read_sql("SELECT ResourceID, Title FROM Resource WHERE OwnerID = %s AND Status = 'Available' AND ListingType = 'Barter'", conn, params=(user_srn,))
    resource_map = {f"{r['Title']} (ID: {r['ResourceID']})": r['ResourceID'] for r in user_resources.to_dict('records')}
    resource_names = list(resource_map.keys())
    conn.close()

    # Tab 1: Propose Barter (C-operation)
    with tab1:
        st.subheader("Propose a New Barter")

        # --- FIX: Logic to show message OR form ---
        if st.session_state.get('barter_proposed', False):
            st.success("✅ Barter proposal submitted! Awaiting acceptance.")
            st.info("The other user will see this in their 'Review Proposals' tab.")
            # This hides the form by not running the 'else' block
        
        else:
            # This 'else' block contains all your original form logic
            if not resource_names:
                st.info("You must have 'Barter' items listed as 'Available' to propose a trade.")
                return

            conn = get_db_connection()
            if not conn: return
            
            # Users can only trade for other 'Barter' items
            query_others = """
            SELECT ResourceID, Title, CONCAT(s.FirstName, ' ', s.LastName) AS OwnerName
            FROM Resource r JOIN Student s ON r.OwnerID = s.SRN
            WHERE r.Status = 'Available' 
              AND r.ListingType = 'Barter' -- This is the fix
              AND r.OwnerID != %s
            """
            df_others = pd.read_sql(query_others, conn, params=(user_srn,))
            conn.close()

            if df_others.empty:
                st.info("No available 'Barter' items from other students to trade with.")
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
                            cursor.execute("SELECT OwnerID FROM Resource WHERE ResourceID = %s", (item2_id,))
                            accepter_id_tuple = cursor.fetchone()
                            if not accepter_id_tuple:
                                st.error("Target item not found.")
                                return
                            accepter_id = accepter_id_tuple[0]
                            
                            cursor.execute("INSERT INTO Transactions (Type) VALUES ('Barter')")
                            trans_id = cursor.lastrowid
                            
                            query = """
                            INSERT INTO Barter (Item1ID, Item2ID, ProposerID, AccepterID, Status, BarterDate, TransactionID)
                            VALUES (%s, %s, %s, %s, 'Pending', CURDATE(), %s)
                            """
                            cursor.execute(query, (item1_id, item2_id, user_srn, accepter_id, trans_id))
                            conn.commit()
                            
                            # --- FIX: Set the flag and rerun ---
                            st.session_state.barter_proposed = True
                            st.rerun()

                        except mysql.connector.Error as err:
                            st.error(f"Failed to submit barter: {err}")
                        finally:
                            cursor.close()
                            conn.close()

    # Tab 2: Review Proposals (U-operation - Acceptance)
    with tab2:
        st.subheader("Proposals to Review")
        
        # --- FIX: Added info box for debugging ---
        st.info(f"📋 Checking for proposals where you ({user_srn}) are the 'Accepter'.")

        conn = get_db_connection()
        if not conn: return
        
        # This query is correct.
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
            # --- FIX: This query is now from the user's perspective and ONLY shows 'Accepted' ---
            query_history = """
            (
                -- I was the Proposer (I GAVE Item1, I RECEIVED Item2)
                SELECT 
                    b.BarterID, 
                    r1.Title AS 'Item You Gave',
                    r2.Title AS 'Item You Received',
                    CONCAT(s_acc.FirstName, ' ', s_acc.LastName) AS 'Traded With',
                    b.Status, 
                    b.BarterDate
                FROM Barter b
                JOIN Resource r1 ON b.Item1ID = r1.ResourceID
                JOIN Resource r2 ON b.Item2ID = r2.ResourceID
                JOIN Student s_acc ON b.AccepterID = s_acc.SRN
                WHERE b.ProposerID = %s AND b.Status = 'Accepted'
            )
            UNION
            (
                -- I was the Accepter (I GAVE Item2, I RECEIVED Item1)
                SELECT 
                    b.BarterID, 
                    r2.Title AS 'Item You Gave',
                    r1.Title AS 'Item You Received',
                    CONCAT(s_prop.FirstName, ' ', s_prop.LastName) AS 'Traded With',
                    b.Status, 
                    b.BarterDate
                FROM Barter b
                JOIN Resource r1 ON b.Item1ID = r1.ResourceID
                JOIN Resource r2 ON b.Item2ID = r2.ResourceID
                JOIN Student s_prop ON b.ProposerID = s_prop.SRN
                WHERE b.AccepterID = %s AND b.Status = 'Accepted'
            )
            ORDER BY BarterDate DESC
            """
            df_history = pd.read_sql(query_history, conn, params=(user_srn, user_srn))
            if df_history.empty:
                st.info("No accepted barter history found.")
            else:
                st.dataframe(df_history, hide_index=True)
            conn.close()

def page_my_activity():
    render_back_button()
    st.header("⚙️ My Resources and Activity")
    user_srn = st.session_state.logged_in_srn
    conn = get_db_connection()
    if not conn: return

    tab1, tab2, tab3, tab4 = st.tabs(["My Resources (Owner)", "My Purchases", "My Loans", "My Reviews/Reminders"])

    # Tab 1: My Resources (Owner/Delete)
    with tab1:
        st.subheader("Items I Own")
        query_resources = """
        SELECT r.ResourceID, r.Title, r.itemCondition, r.Status, c.MainType, r.ListingType
        FROM Resource r
        JOIN Category c ON r.CategoryID = c.Cat_ID
        WHERE r.OwnerID = %s
        """
        df_resources = pd.read_sql(query_resources, conn, params=(user_srn,))
        
        if not df_resources.empty:
            st.dataframe(df_resources)
            
            st.markdown("---")
            st.subheader("Delete a Resource")
            deletable_resources = df_resources[df_resources['Status'] == 'Available']
            
            if deletable_resources.empty:
                st.info("You can only delete resources currently marked as 'Available'.")
            else:
                delete_id = st.selectbox("Select Resource ID to Delete (Permanently)", deletable_resources['ResourceID'].unique())
                
                if st.button(f"Confirm DELETE Resource {delete_id}", type="primary"):
                    try:
                        cursor = conn.cursor()
                        # D-operation: DELETE the resource
                        # This works because the DB script ensures the resource owner matches the logged-in user.
                        # Requires ON DELETE CASCADE on: BuySell, LendBorrow, Barter, Review
                        cursor.execute("DELETE FROM Resource WHERE ResourceID = %s AND OwnerID = %s", (delete_id, user_srn))
                        conn.commit()
                        st.success(f"Resource ID {delete_id} deleted successfully (and all related records).")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Deletion failed. Error: {err}. Please ensure ON DELETE CASCADE is configured for this table.")
                    finally:
                        cursor.close()
        else:
             st.info("No resources currently owned by you.")

    # Tab 2: My Purchases (Bought/Bartered)
    with tab2:
        st.subheader("Purchased Items (Buy/Sell)")
        # This correctly shows the 'Completed' status
        query_purchases = """
        SELECT bs.BuySellID, r.Title, bs.Price, bs.Status AS SaleStatus, bs.TransactionDate
        FROM BuySell bs
        JOIN Resource r ON bs.ItemID = r.ResourceID
        WHERE bs.BuyerID = %s AND bs.Status IN ('Completed', 'PendingPayment', 'PendingConfirmation');
        """
        df_purchases = pd.read_sql(query_purchases, conn, params=(user_srn,))
        st.dataframe(df_purchases, hide_index=True)
        
        st.subheader("Bartered Items (Acquired)")
        # --- FIX: This query is now correct. It checks both roles (Proposer/Accepter) ---
        query_barter_acquired = """
        (
            -- Find items I acquired as the PROPOSER (I get Item2)
            SELECT b.BarterID, r2.Title AS AcquiredItemTitle, b.BarterDate, b.Status
            FROM Barter b
            JOIN Resource r2 ON b.Item2ID = r2.ResourceID -- Item I received
            WHERE b.ProposerID = %s AND b.Status = 'Accepted'
        )
        UNION
        (
            -- Find items I acquired as the ACCEPTER (I get Item1)
            SELECT b.BarterID, r1.Title AS AcquiredItemTitle, b.BarterDate, b.Status
            FROM Barter b
            JOIN Resource r1 ON b.Item1ID = r1.ResourceID -- Item I received
            WHERE b.AccepterID = %s AND b.Status = 'Accepted'
        )
        ORDER BY BarterDate DESC
        """
        df_barter_acquired = pd.read_sql(query_barter_acquired, conn, params=(user_srn, user_srn))
        st.dataframe(df_barter_acquired, hide_index=True)

    # Tab 3: My Loans (Borrowed/Lent)
    with tab3:
        st.subheader("Borrowed Items (My Responsibility)")
        query_borrowed = """
        SELECT lb.LendBorrowID, r.Title, lb.StartDate, lb.EndDate, lb.Status, 
               lb.PenaltyAmount, r.ResourceID
        FROM LendBorrow lb
        JOIN Resource r ON lb.itemID = r.ResourceID
        WHERE lb.BorrowerID = %s
        ORDER BY lb.StartDate DESC;
        """
        df_borrowed = pd.read_sql(query_borrowed, conn, params=(user_srn,))
        st.dataframe(df_borrowed, hide_index=True)

        # --- Display Return/Review Buttons for Borrowed Items ---
        st.markdown("---")
        st.subheader("Actions on Loans")
        
        df_ongoing = df_borrowed[df_borrowed['Status'] == 'Ongoing']
        
        if not df_ongoing.empty:
            st.warning("You have ongoing loans. Select the ID below to return:")
            with st.form("return_form"):
                return_id = st.selectbox("Loan ID to Return", df_ongoing['LendBorrowID'].unique(), key="loan_return_id")
                
                # Button to trigger loan completion procedure (handles early return logic implicitly)
                if st.form_submit_button("Confirm Return"):
                    try:
                        cursor = conn.cursor()
                        # NOTE: The bug was likely in the stored procedure query structure (fixed outside this file).
                        cursor.callproc('complete_lend_with_penalty', (return_id,))
                        conn.commit()
                        
                        # Fetch calculated penalty for display
                        cursor.execute("SELECT PenaltyAmount FROM LendBorrow WHERE LendBorrowID = %s", (return_id,))
                        penalty_tuple = cursor.fetchone()
                        penalty = penalty_tuple[0] if penalty_tuple else 0
                        
                        if penalty > 0:
                            st.error(f"Item returned. **LATE RETURN** - A penalty of **₹{penalty:.2f}** has been applied.")
                        else:
                            st.success("Item successfully returned and loan completed!")
                        st.rerun()
                    except mysql.connector.Error as err:
                        st.error(f"Failed to process return: {err}")
                    finally:
                        if cursor: cursor.close()
        
        st.subheader("Items I Have Lent Out")
        query_lent = """
        SELECT lb.LendBorrowID, r.Title, lb.StartDate, lb.EndDate, lb.Status, 
               CONCAT(s.FirstName, ' ', s.LastName) AS Borrower
        FROM LendBorrow lb
        JOIN Resource r ON lb.itemID = r.ResourceID
        JOIN Student s ON lb.BorrowerID = s.SRN
        WHERE lb.LenderID = %s;
        """
        df_lent = pd.read_sql(query_lent, conn, params=(user_srn,))
        st.dataframe(df_lent, hide_index=True)


    # Tab 4: My Reviews (Reminders/Reviews)
    with tab4:
        st.subheader("My Reminders")
        query_reminders = "SELECT ReminderID, Msg, RDate, Status FROM Reminder WHERE STD_ID = %s ORDER BY RDate DESC"
        df_reminders = pd.read_sql(query_reminders, conn, params=(user_srn,))
        st.dataframe(df_reminders, hide_index=True)
        
        st.subheader("My Reviews")
        query_reviews = """
        SELECT rv.Rating, rv.Comments, r.Title, r.ResourceID
        FROM Review rv JOIN Resource r ON rv.ItemID = r.ResourceID WHERE rv.STD_ID = %s
        """
        df_reviews = pd.read_sql(query_reviews, conn, params=(user_srn,))
        st.dataframe(df_reviews)

        st.markdown("---")
        st.subheader("Submit a New Review")
        
        # Determine items eligible for review (Completed transactions without a review)
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
                        conn.commit(); st.success(f"Review submitted for {review_item_name}!"); st.rerun()
                    except mysql.connector.Error as err: st.error(f"Failed to submit review: {err}")
                    finally: cursor.close()
        else:
            st.info("No items are eligible for a new review.")

    conn.close()

# --- Main Router ---
if st.session_state.logged_in_srn is None:
    if st.session_state.page == 'login': page_login()
    elif st.session_state.page == 'signup': page_signup()
    else: page_landing() 
else:
    if st.session_state.page == 'home': page_home_browse()
    elif st.session_state.page == 'upload_sell': page_upload_item('sell')
    elif st.session_state.page == 'upload_lend': page_upload_item('lend')
    elif st.session_state.page == 'upload_barter': page_upload_item('barter')
    elif st.session_state.page == 'buysell': page_buysell()
    elif st.session_state.page == 'lendborrow': page_lendborrow()
    elif st.session_state.page == 'barter': page_barter()
    elif st.session_state.page == 'my_activity': page_my_activity()
    else: page_home_browse()