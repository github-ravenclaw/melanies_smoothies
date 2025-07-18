import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# UI setup
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie")

# Input: name on order
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Get active session and fruit options
cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"), col('SEARCH_ON'))

# Convert Snowpark DataFrame to Pandas DataFrame
pd_df = my_dataframe.to_pandas()

# Ingredient selection (clean list from Pandas df)
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# If user selected ingredients
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Get SEARCH_ON value for selected fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        if pd.isna(search_on) or search_on == 'None':
            st.warning(f"No nutrition information available for {fruit_chosen}.")
        else:
            st.subheader(f"{fruit_chosen} Nutrition Information")

            # API call for nutrition info
            smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")

            if smoothiefroot_response.status_code == 200:
                response_json = smoothiefroot_response.json()
                nutrition_df = pd.DataFrame(response_json)
                st.dataframe(data=nutrition_df, use_container_width=True)
            else:
                st.error(f"Failed to fetch nutrition info for {fruit_chosen}.")

    # Trim trailing space from ingredient string
    ingredients_string = ingredients_string.strip()

    # SQL insert statement
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    # Submit order button
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered! ✅')
