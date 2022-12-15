import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

# Page config, titles & introduction
st.set_page_config(page_title="delay dashboard", page_icon=":red_car:", layout="wide")


st.sidebar.write("Dashboard made by [@Ukratic](https://github.com/Ukratic)")
st.sidebar.success("Navigate to a page above")

st.subheader("Getaround data : Pricing")
st.markdown("""Egregious outliers have been removed but otherwise the data is unchanged.
""")

# Load data
@st.cache(allow_output_mutation=True)
def load_data(nrows):
    data = pd.read_csv('https://storage.googleapis.com/get_around_data/pricing_df.csv')
    return data

data_load_state = st.text('Loading data, please wait...')
data = load_data(None)
data_load_state.text("")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

# Data exploration
st.subheader("Data exploration")

st.markdown("""Data on car brands and models""")
col1, col2= st.columns(2)

with col1 :
#plot 1    
    models_df = data.groupby('model_key').mean().sort_values(by='rental_price_per_day',ascending=False)

    fig = plt.figure(figsize=(10,6))
    sns.barplot(x=models_df.index,y=models_df['rental_price_per_day'],palette='Set2')
    plt.xticks(rotation=60)
    plt.title('Average rental price per day per brand')
    st.pyplot(fig)

with col2 : 
    models2_df = data.groupby('model_key').sum().sort_values('rental_price_per_day',ascending=False)

    fig = plt.figure(figsize=(10,6))
    sns.barplot(x=models2_df.index,y=models2_df['rental_price_per_day'],palette='husl')
    plt.xticks(rotation=60)
    plt.title('Total rental revenue per day per brand')
    st.pyplot(fig)

st.markdown("The 5 top brands (Renault, Citroën, BMW, Audi and Peugeot) are on the cheaper side but much more important to the business, with more than 75% of income from rentals.")


fig = plt.figure(figsize=(12,7))
corr_mx = data.corr()
matrix = np.triu(corr_mx) # take upper correlation matrix

sns.heatmap(corr_mx, mask=matrix,annot=True, cmap = 'YlGnBu', linewidths=0.1, square=True)
st.pyplot(fig)

st.markdown("Bigger engine power, comfort options and less mileage contribute to a higher rental price per day. This makes sense !")

col1, col2= st.columns(2)
with col1 :
#plot 1    
    fig = plt.figure(figsize=(10,6))
    sns.histplot(data['rental_price_per_day'])
    plt.title('Distribution of rental price per day')
    st.pyplot(fig)

with col2 : 
    fig = plt.figure(figsize=(10,6))
    sns.histplot(data['mileage'])
    plt.title('Distribution of mileage')
    st.pyplot(fig)

st.markdown("Most rentals cost between 100 and 150 per day.")