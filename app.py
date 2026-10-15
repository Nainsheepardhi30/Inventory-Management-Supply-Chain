import streamlit as st
import pandas as pd
from function import get_basic_info, connect_to_database, get_additional_table, add_new_manual_id, get_categories, get_suppliers ,get_all_products,get_product_history, place_reorder, get_pending_reorders, mark_reorder_as_received


st.set_page_config(
    page_title="Inventory Management Dashboard",
    layout="wide"
)


# sidebar
st.sidebar.title("Inventory Management Dashboard")
Option = st.sidebar.radio("Select Option" , ["Basic information" , "Operationl Tasks"])

# main page
st.title("Inventory And Supply chain Dashboard")
db = connect_to_database()
cursor = db.cursor(dictionary=True)



# ---------------- Basic information page -----------------

if Option == "Basic information":
    st.header("Basic Information")

    # get basic information from DB
    basic_info = get_basic_info()

    col = st.columns(3)
    keys = list(basic_info.keys())
    for i in range(3):
        col[i].metric(label=keys[i], value=basic_info[keys[i]])

    col = st.columns(3)
    for i in range(3,6):
        col[i-3].metric(label=keys[i], value=basic_info[keys[i]])


    st.divider()


    table = get_additional_table()
    for label, data in table.items():
        st.header(label)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()

# ----------------- OPERATIONAL TASKS PAGE -----------------
elif Option == "Operationl Tasks" :
    st.header("Operationl Tasks")
    selected_task = st.selectbox("Choose an Tasks" , ["Add New Product","Product History","Place Reorder","Receive Reorder"])
#------------------- ADD NEW PRODUCT ----------------------
    if selected_task == "Add New Product":
        st.header("Add New Product")
        categories = get_categories(cursor)
        suppliers = get_suppliers(cursor)


        with st.form("add_product_form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("Category", categories)
            product_price = st.number_input("Price", min_value=0.0)
            product_stock = st.number_input("Stock Quantity", min_value=0, step=1)
            product_reorder_level = st.number_input("Reorder Level", min_value=0, step=1)


            supplier_ids = [s["supplier_id"] for s in suppliers]
            supplier_names = [s["supplier_name"] for s in suppliers]

            product_supplier = st.selectbox("Supplier", 
                                    options = supplier_ids,
                                    format_func = lambda x: supplier_names[supplier_ids.index(x)]
                                    )
            
            

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("please enter a product name.")
                else:
                    try:
                        add_new_manual_id(cursor, db, product_name, product_category, product_price, product_stock, product_reorder_level, product_supplier)
                        st.success(f"Product {product_name} added successfully!")
                    except Exception as e:
                        st.error(f"An error occurred while adding the product: {e}")

# ------------------- PRODUCT HISTORY ----------------------

    if selected_task == "Product History":
        st.header("Product Inventory History")
        products = get_all_products(cursor)
        product_ids = [p["product_id"] for p in products]
        product_names = [p["product_name"] for p in products]

        selected_product_name = st.selectbox(
            "Select a Product",
            options=product_names,
        )

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_id)

            if selected_product_id:
                df = pd.DataFrame(history_data)
                st.dataframe(df)

            else:
                st.info("No history found for the selected product.")



    if selected_task == "Place Reorder":
        st.header("place an Reorder")

        products = get_all_products(cursor)
        product_ids = [p["product_id"] for p in products]
        product_names = [p["product_name"] for p in products]

        selected_product_name = st.selectbox(
            "Select a Product",
            options=product_names,
        )
        reorder_quantity = st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("place Reorder"):
            if not selected_product_name:
                st.error("Please select a product.")
            elif reorder_quantity <= 0:
                st.error("Reorder quantity must be greater than 0.")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_id, reorder_quantity)
                    st.success(f"Reorder placed for {selected_product_name} with quantity {reorder_quantity}.")
                except Exception as e:
                    st.error(f"An error occurred while placing the reorder: {e}")


# ------------------- RECEIVE REORDER ----------------------
    if selected_task == "Receive Reorder":
        st.header("Mark Reorder as Received")

# fetch order in ordered stage
        pending_reorders = get_pending_reorders(cursor)

        if not pending_reorders:
            st.info("No pending Order to receive.")
        else:   
            reorder_ids = [r["reorder_id"] for r in pending_reorders]
            reorder_labels = [f"ID: {r['reorder_id']} - Product: {r['product_name']}" for r in pending_reorders]

            selected_label = st.selectbox("Select Reorder to Mark as Received", options=reorder_labels)

            if selected_label:
                selected_reorder_id = reorder_ids[reorder_labels.index(selected_label)]
                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor, db, selected_reorder_id)
                        st.success(f"Reorder ID {selected_reorder_id} marked as received.")
                    except Exception as e:
                        st.error(f"An error occurred while marking the reorder as received: {e}")