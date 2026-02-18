import streamlit as st
import pandas as pd
import os
from PIL import Image

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Quick Catalog", layout="wide")

CSV_FILE = 'inventory.csv'
IMG_DIR = 'product_images'

# Initialize CSV if it doesn't exist
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=['Name', 'Status', 'MRP', 'Image_Path'])
    df.to_csv(CSV_FILE, index=False)

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

# --- DATA FUNCTIONS ---
def get_data():
    return pd.read_csv(CSV_FILE)

def save_data(df):
    """Saves the current DataFrame back to the inventory.csv file."""
    df.to_csv(CSV_FILE, index=False)

def add_item(name, status, mrp, img_file):
    img_path = os.path.join(IMG_DIR, img_file.name)
    with open(img_path, "wb") as f:
        f.write(img_file.getbuffer())
    
    df = get_data()
    new_row = pd.DataFrame([[name, status, mrp, img_path]], columns=df.columns)
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)

def process_image(uploaded_file, product_name):
    """Resizes image and pads it into a square to ensure perfect alignment."""
    img = Image.open(uploaded_file)
    img.convert("RGB") # Ensures consistent color mode
    
    # 1. Define our standard square size
    size = (800, 800)
    
    # 2. Resize the image to fit within that square while keeping aspect ratio
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # 3. Create a new white background square
    new_img = Image.new("RGB", size, (255, 255, 255))
    
    # 4. Center the image on the white square
    upper_left = (
        (size[0] - img.size[0]) // 2,
        (size[1] - img.size[1]) // 2
    )
    new_img.paste(img, upper_left)
    
    # 5. Save with the product name
    ext = "jpg" # Forcing jpg for consistency
    clean_name = product_name.replace(" ", "_")
    filename = f"{clean_name}.{ext}"
    path = os.path.join(IMG_DIR, filename)
    
    new_img.save(path, "JPEG", quality=85, optimize=True)
    return path

# --- UI ---
st.sidebar.title("Mayur Electronics")
menu = st.sidebar.radio("Go to", ["View Catalog", "Manage Inventory"])

if menu == "View Catalog":
    st.title("Live Catalog")
    df = get_data()
    
    if df.empty:
        st.warning("Catalog is empty. Add items in 'Manage Inventory'.")
    else:
        # Search Bar
        search = st.text_input("Search products...", "")
        filtered_df = df[df['Name'].str.contains(search, case=False)]

        cols = st.columns(4, vertical_alignment="center") # 4 items per row
        for i, row in filtered_df.iterrows():
            with cols[i % 4]:
                st.image(row['Image_Path'], use_container_width=True)
                st.subheader(row['Name'])
                st.write(f"₹ {row['MRP']:.2f}")
                # Visual Stock Indicator
                if row['Status'] == "In Stock":
                    st.success("In Stock")
                else:
                    st.error("Out of Stock")
                
                st.markdown("---")

else:
    st.title("Inventory Manager")
    df = get_data()
    
    tab1, tab2 = st.tabs(["Add New", "Edit / Delete"])

    # --- TAB 1: ADD NEW ---
    with tab1:
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("Product Name")
            status = st.selectbox("Status", ["In Stock", "Out of Stock"])
            mrp = st.number_input("MRP", min_value=0.0, step = 0.01, format="%.2f")
            img = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'])
            
            if st.form_submit_button("Add Product"):
                if name and img:
                    if name.lower() in df['Name'].str.lower().values:
                        st.error(f"Error: Product '{name}' already exists!")
                    else:
                        img_path = process_image(img, name)
                        new_row = pd.DataFrame([[name, status, mrp, img_path]], columns=df.columns)
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        st.success(f"Successfully added {name}")
                        st.rerun()
                else:
                    st.error("Missing Name or Image")

    # --- TAB 2: EDIT / DELETE ---
    with tab2:
        if df.empty:
            st.info("No products to edit.")
        else:
            selected_product = st.selectbox("Select Product to Update", df['Name'].tolist())
            product_index = df[df['Name'] == selected_product].index[0]
            current_row = df.iloc[product_index]

            st.write(f"**Current Status:** {current_row['Status']}")
            st.image(current_row['Image_Path'], width=150)

            col1, col2 = st.columns(2)
            with col1:
                new_price = st.number_input("Update Price", value = float(df.at[product_index, 'MRP']), step=0.01)
                new_status = st.selectbox("Update Status", ["In Stock", "Out of Stock"], 
                                          index=0 if current_row['Status'] == "In Stock" else 1)
                new_img = st.file_uploader("Replace Image (Optional)", type=['jpg', 'png', 'jpeg'])
            
            with col2:
                st.write("### Actions")
                if st.button("Save Changes"):
                    df.at[product_index, 'Status'] = new_status
                    if new_img:
                        new_img_path = os.path.join(IMG_DIR, new_img.name)
                        with open(new_img_path, "wb") as f:
                            f.write(new_img.getbuffer())
                        df.at[product_index, 'Image_Path'] = new_img_path
                    
                    save_data(df)
                    st.success("Updated successfully!")
                    st.rerun()

                if st.checkbox(f"Confirm Delete {selected_product}"):
                    if st.button("Delete", type="primary"):
                        # Delete the file from folder
                        if os.path.exists(df.at[product_index, 'Image_Path']):
                            os.remove(df.at[product_index, 'Image_Path'])
                        df = df.drop(product_index)
                        save_data(df)
                        st.rerun()
