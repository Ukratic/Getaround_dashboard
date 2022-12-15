import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

# Page config, titles & introduction
st.set_page_config(page_title="getaround dashboard", page_icon=":blue_car:", layout="wide")

st.title('Getaround project 🌎:blue_car:')

st.markdown("""This is a dashboard for the Getaround project.

The purpose of this dashboard is to provide a quick overview of the data and to allow the user to explore the data in more detail.
Data is split into 2 datasets : one contains the data from the cars and the other one contains the data from the rentals.

You will find graphs representing completed or canceled rentals per checkin type, the distribution of checkout delays and several recommendations to improve the business.
""")

st.sidebar.write("Dashboard made by [@Ukratic](https://github.com/Ukratic)")
st.sidebar.success("Navigate to a page above")

st.subheader("Getaround data : Delay")
st.markdown("""A few new columns have been added to the data to make it easier to explore the data.
- `checkout` : string value representing the delay (see values in graph below).
- `next_rental` : Whether there is a rental after the current one or not.
- `next_checkout_min_delay` : `delay_at_checkout_in_minutes` without outliers.
""")

# Load data
@st.cache(allow_output_mutation=True)
def load_data(nrows):
    data = pd.read_csv('https://storage.googleapis.com/get_around_data/delay_df.csv')
    return data

data_load_state = st.text('Loading data, please wait...')
data = load_data(None)
data_load_state.text("")

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data)

# Data exploration
st.subheader("Data exploration")

st.markdown("""I calculated two metrics to evaluate risk and revenue : `max loss` and `max risk`.
- `max loss` : the maximum loss if all rentals are canceled because of a late checkout.
- `max risk` : the maximum risk if all rentals are canceled because of a late checkout AND zero revenue from late rentals.

These metrics are meant to be used as a guide to evaluate the impact, in replacement for a study from which we could evaluate user experience.

**It relies on the following assumptions**:
- A standard rental of 24 hours and median rental rate of 119 $
- A rate by the minute with no penalty for a late checkout after the agreed-upon time.
- After a canceled rental, the car is not rented for 24 hours.
- Users can't find other cars in the neighborhood as replacement.
- The user renting his car seeks to absolutely optimize revenue.

This results in using **revenue and loss of profit** to evaluate user experience, which is not necessarily reliable.

""")
col1, col2= st.columns(2)

with col1 :
#plot 1    
    checkout_clean = data.dropna(subset=['delay_at_checkout_in_minutes'])
    checktype_checkout = checkout_clean.groupby(['checkin_type','checkout']).size().reset_index(name='count')
    checktype_checkout['percentage'] = [i / checktype_checkout['count'].sum() * 100 for i in checktype_checkout['count']]

    fig = plt.figure(figsize=(10,6))
    sns.barplot(y=checktype_checkout['percentage'],x=checktype_checkout['checkin_type'], hue=checktype_checkout['checkout'],orient='vertical')
    plt.title('Mobile and Connect rentals per checkout delay')
    st.pyplot(fig)

with col2 : 
    has_next = data.groupby(['checkin_type','next_rental']).size().reset_index(name='count')
    has_next['percentage'] = [i / has_next['count'].sum() * 100 for i in has_next['count']]

    fig = plt.figure(figsize=(10,6))
    sns.barplot(y=has_next['percentage'],x=has_next['checkin_type'], hue=has_next['next_rental'],orient='vertical')
    plt.title('Next rental or not depending on checkin type')
    st.pyplot(fig)

med_delay = data['delays_checkout_min_cleaned'].median()
mean_delay = data['delays_checkout_min_cleaned'].mean()

st.markdown("""Most late checkouts are still within the next 2 hours, so we can reasonably hope to significantly reduce risk by setting a threshold.
Mobile check in type is more frequent, but otherwise the distribution is fairly close despite a little more NA's.""")

st.markdown(f"""On average, drivers are {round(mean_delay,2)} minutes late, with a median value of {med_delay} minutes.
""")

col1, col2= st.columns(2)
with col1 :
#plot 1    
    fig = plt.figure(figsize=(10,6))
    sns.histplot(data=data,x='time_delta_with_previous_rental_in_minutes')
    plt.title('Distribution of time delta with previous rentals')
    st.pyplot(fig)

with col2 : 
    fig = plt.figure(figsize=(10,6))
    sns.histplot(data=data,x='delays_checkout_min_cleaned')
    plt.title('Distribution of delays at checkout')
    st.pyplot(fig)

st.markdown("""The range in delays even after removing the most extreme outliers makes one suspicious of the data's quality, since it is stated that rentals are for a few hours to a few days.
The time delta would be interesting, if not for the fact that it is not available for all rentals.""")



# selecting canceled rides
canceled = (data['state'] == 'canceled').sum()
median_rental = 119
canceled_loss = canceled*median_rental 

number_delays = (data['delays_checkout_min_cleaned'] > 0).sum()
sum_delays = data[data['delays_checkout_min_cleaned'] > 0]['delays_checkout_min_cleaned'].sum() # sum of delays superior to 0, in minutes
minute_rate = median_rental/1440 #1440 minutes in a day
late_revenue = sum_delays*minute_rate

st.markdown(f"""At the median rate and assuming that an average rental is for 24 hours, the {canceled} cancellations totaled a {canceled_loss} \$ `max loss`.
Supposing a rate by the minute with no penalty for a late checkout, the {number_delays} late arrivals brought in {round(late_revenue,2)} $ (not counting outliers)""")


late_loss = canceled_loss - late_revenue
st.markdown(f"""If the actual operational delay is less than {round(late_revenue/canceled_loss*24,2)} hours, additional revenue from late checkouts and loss from canceled rentals break even.
For a full day, it generates a {round(late_loss,2)} $ loss for a full day, assuming all cancelled rentals were because of a late checkout.""")

at_risk = number_delays*minute_rate*1440
ended = (data['state'] == 'ended').sum()
revenue = ended*median_rental + late_revenue
risk_over_revenue = round(at_risk/(revenue),2)

st.markdown(f"Late arrivals trigger a `max risk` of {at_risk} \$, so about {risk_over_revenue} times the total estimated revenue from rentals of {round(revenue,2)} $.")


st.markdown("""We can compute `max risk`, but we don't actually know that all cancellations are linked to a late checkout nor that it is not compensated by re-allocating cars to other rentals.
It would be useful to have more data on this issue, such as maybe asking users why they cancelled ? This would help us isolate the cost of late arrivals and incidentally could also unveil other issues that clients might have with the rental service.
We would also need more time data (duration of each ride, how much time a car spends unused...) to accurately estimate losses.""")
threshold_range = np.arange(0, 60*24, 15) # looking at thresholds for each 15min intervals
penalty = 3  # penalty for late arrival is set at 3 times the normal minute rate
risk_over_revenue_penalty= []

for t in threshold_range:
    count = (data['delays_checkout_min_cleaned'] > t).sum()
    late_revenue_penalty = data[data['delays_checkout_min_cleaned'] > t]['delays_checkout_min_cleaned'].sum() * minute_rate * 3
    late_risk = count * median_rental
    risk_over_revenue_penalty.append(late_risk/late_revenue_penalty)

fig = plt.figure(figsize=(12,7))
sns.lineplot(x=threshold_range,y=risk_over_revenue_penalty)
plt.ylabel('Risk of 1 = max loss is equal to revenue from late arrivals')
plt.title('Threshold time (in minutes) and risk over late revenue')
st.pyplot(fig)

st.markdown("""For standard rentals of **1 day** and a **penalty of 3 times the normal minute rate** after the rental is due, with our current data we would need to set a **threshold below 180 minutes** to negate all losses from late checkouts.
A significant caveat is that all this, on top of some assumptions, does not take into account actual demand in rentals. This has limited production applications and while it alleviates customer discomfort, this should not be relied upon as a comprehensive projection of revenue.
It is assumed that the customer doesn't wait and cancels outright, which is not necessarily the case.""")

connect_share = (data['checkin_type'].value_counts()/data['checkin_type'].count()*100)[1]
mobile_share = (data['checkin_type'].value_counts()/data['checkin_type'].count()*100)[0]
connect_canceled = (data[data['state']=='canceled']['checkin_type'].value_counts()/data[data['state']=='canceled']['checkin_type'].count()*100)[1]

st.markdown(f"As shown on the first graph above, Mobile use is prevalent with a {round(mobile_share,2)}% share and Connect has a {round(connect_share,2)}% share. However, {round(connect_canceled)}% of cancellations are with Connect, \
suggesting a bigger impact from cancellations on this type of rental flow. Sample size and results would suggest that our action would have most impact on customers using Connect.")

st.subheader("Conclusion")
st.markdown("""Therefore, **our recommandation would be to implement a delay of 3 hours for Connect rentals, with a penalty of 3 times the normal rate for late checkouts**.
A discussion with the product team would be needed to determine whether or not there should be a margin without penalty (and if a penalty can be implemented at all !), to account for delays due to traffic or other unforeseen circumstances and avoid frustrating customers.
This would mitigate the impact of late arrivals ando help customers who are inconvenienced by late arrivals.
It would also be interesting to look at the impact of this delay on the number of cancellations and the number of late arrivals, once we implement a penalty for delays.
We would also need to look at the impact on the number of rentals and the revenue generated by Connect rentals, to see if the delay is worth it.

All in all, reduced profit is not a perfectly accurate way to account for user discomfort. 
We would ideally need a new metric, perhaps using the results of a poll to estimate the impact of delays on the user experience.""")
