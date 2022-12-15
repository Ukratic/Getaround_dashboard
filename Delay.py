import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

pd.options.mode.chained_assignment = None  # default='warn'

# Page config, titles & introduction
st.set_page_config(page_title="getaround dashboard", page_icon=":blue_car:", layout="wide")

st.title('Getaround project 🌎:blue_car:')

st.markdown("""This is a dashboard for the Getaround project.

The purpose of this dashboard is to provide a quick overview of the data and to allow the business team to explore the data in more detail.
Data is split into 2 datasets : one contains the data from the cars and the other one contains the data from the rentals.

You will find graphs representing completed or canceled rentals per checkin type, the distribution of checkout delays and several recommendations to improve the business.\n
The current page covers the delay dataset. You can navigate to the other page using the sidebar on the left.

You can also check out the Getaround pricing API [here](https://getaround-api-p5.herokuapp.com/docs) to extract data and use the predict endpoint.""")

st.sidebar.write("Dashboard made by [@Ukratic](https://github.com/Ukratic)")

st.sidebar.success("Navigate to a page above")

st.header("Getaround data : Delay")
st.markdown("""A few new columns have been added to make it easier to explore the data.
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

connect_share = (data['checkin_type'].value_counts()/data['checkin_type'].count()*100)[1]
mobile_share = (data['checkin_type'].value_counts()/data['checkin_type'].count()*100)[0]
connect_canceled = (data[data['state']=='canceled']['checkin_type'].value_counts()/data[data['state']=='canceled']['checkin_type'].count()*100)[1]

st.markdown(f"""Mobile use is prevalent with a {round(mobile_share,2)}% share while Connect has a {round(connect_share,2)}% . 
However, {round(connect_canceled)}% of cancellations are with Connect, suggesting a slightly bigger impact from cancellations on this type of rental flow. """)

late_df = data[data['delays_checkout_min_cleaned']>0]

drivers_late = len(late_df)
drivers_total = len(data)
percentage_drivers_late = drivers_late/drivers_total*100
time_late = late_df['delays_checkout_min_cleaned'].sum()/len(late_df)

st.markdown(f"On average, {round(percentage_drivers_late,2)} % of drivers are late and are {round(time_late,2)} minutes late.")

st.markdown(f"Cancelled rentals represent {round(data[data['state']=='canceled']['state'].count()/data['state'].count()*100,2)}% of the total rentals.")


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

st.markdown("""There are still a lot of outliers even after removing the most extreme. 
It would be interesting to have data on rental duration, since it is just stated that rentals are for "a few hours to a few days".""")

st.subheader("What is the impact of delays ?")
st.markdown("""We can look at the impact of delays on the business from 2 perspectives :
- User experience
- Business perspective
""")

# User experience
st.subheader("User experience perspective")

st.markdown("If we put in place a threshold between checkout and new checkin, how many drivers would be affected?")

impacted_df = data.dropna(subset=['time_delta_with_previous_rental_in_minutes'])
impacted_df['difference'] = impacted_df['time_delta_with_previous_rental_in_minutes'] - impacted_df['delays_checkout_min_cleaned']
issues = len(impacted_df[impacted_df['difference'] < 0])
issues_percentage = issues/len(data)*100

st.markdown(f"""{issues} of drivers ({round(issues_percentage,2)}%) have an issue with the time delta between rentals and
{len(impacted_df[impacted_df['difference'] < -30])} drivers causing an issue are more than 30 minutes late.

Implementing a 30 minutes delay would impact {len(impacted_df[impacted_df['time_delta_with_previous_rental_in_minutes'] < 30])} drivers.
""")

threshold_range = np.arange(0, 60*12, step=15) # 15min intervals for 12 hours
impacted_list_mobile = []
impacted_list_connect = []
impacted_list_total = []
solved_list_mobile = []
solved_list_connect = []
solved_list_total = []

solved_list = []
for t in threshold_range:
    impacted = impacted_df.dropna(subset=['time_delta_with_previous_rental_in_minutes'])
    connect_impact = impacted[impacted['checkin_type'] == 'connect']
    mobile_impact = impacted[impacted['checkin_type'] == 'mobile']
    connect_impact = connect_impact[connect_impact['time_delta_with_previous_rental_in_minutes'] < t]
    mobile_impact = mobile_impact[mobile_impact['time_delta_with_previous_rental_in_minutes'] < t]
    impacted = impacted[impacted['time_delta_with_previous_rental_in_minutes'] < t]
    impacted_list_connect.append(len(connect_impact))
    impacted_list_mobile.append(len(mobile_impact))
    impacted_list_total.append(len(impacted))

    solved = impacted_df[impacted_df['difference'] < 0]
    connect_solved = solved[solved['checkin_type'] == 'connect']
    mobile_solved = solved[solved['checkin_type'] == 'mobile']
    connect_solved = connect_solved[connect_solved['delay_at_checkout_in_minutes'] < t]
    mobile_solved = mobile_solved[mobile_solved['delay_at_checkout_in_minutes'] < t]
    solved = solved[solved['delay_at_checkout_in_minutes'] < t]
    solved_list_connect.append(len(connect_solved))
    solved_list_mobile.append(len(mobile_solved))
    solved_list_total.append(len(solved))


ax = fig.add_subplot(1, 1, 1)
fig, ax = plt.subplots(1, 2, sharex=True, figsize=(20,7))
ax[0].plot(threshold_range, solved_list_connect)
ax[0].plot(threshold_range, solved_list_mobile)
ax[0].plot(threshold_range, solved_list_total)
ax[1].plot(threshold_range, impacted_list_connect)
ax[1].plot(threshold_range, impacted_list_mobile)
ax[1].plot(threshold_range, impacted_list_total)
ax[0].set_xlabel('Threshold (min)')
ax[0].set_ylabel('Number of impacted cases & cases solved')
ax[0].legend(['Connect solved','Mobile solved','Total solved' ])
ax[1].legend(['Connect impacted','Mobile impacted','Total impacted' ])
st.pyplot(fig)

st.markdown("""We can see a similar behavior for both Connect and Mobile cases, though a plateau is hit a little faster for Connect rentals.
There is unfortunately a significant number of other rentals impacted (that could not occur as they would have) in implementing the threshold, which has to be evaluated against the positive effects in user experience.

We can see that the curve of cases solved start to slow significantly after 120 minutes and even more around 180 (which is actually a plateau for Connect cases).

Therefore our recommendation would be to **implement the threshold at 120 minutes** and in any case no more than 180.

Overall the effect seems best if implemented on both Connect and Mobile rentals, but a sound approach would be to start with Connect, the smaller sample size (also the specificity of this checkin type with less human interaction makes it ideal).
 """)


# Money money money
st.subheader("~~Loan Shark~~ Business perspective")

st.markdown("""
We can also look at this from a purely money-making standpoint. Ideally, we would want to fix user experience. However, our data doesn't contain feedback from users, so I'll look at one thing that is still sure to matter to most : money.

I stress that this is a projection of maximum impact on a completely strained situation of permanent demand for rentals. 

In this theoretical situation, let's look at:
- How much could be lost from delays
- Quantify the ratio of risks & benefits
- Looking again at what threshold should be set to improve this ratio
""")

# selecting canceled rides
canceled = (data['state'] == 'canceled').sum()
median_rental = 119
canceled_loss = canceled*median_rental 

number_delays = (data['delays_checkout_min_cleaned'] > 0).sum()
sum_delays = data[data['delays_checkout_min_cleaned'] > 0]['delays_checkout_min_cleaned'].sum() # sum of delays superior to 0, in minutes
minute_rate = median_rental/1440 #1440 minutes in a day
late_revenue = sum_delays*minute_rate

st.markdown(f"""At the median rate and assuming that an average rental is for 24 hours, the {canceled} cancellations totaled a {canceled_loss} \$ `max loss`.""")

st.markdown("""

What is this `max loss` ? Not an absolute. It's more like money not made, really.

It relies on a few assumptions :
- First, that the user renting his car seeks to absolutely optimize revenue.
- Second, that all cancellations are due to delays.
- Third, that no money is made from the additional time fater the planned checkout time.
- Fourth, that users renting a car don't wait ; in case of a delay, they cancel outright.


This results in using **revenue and loss of profit** together with **zero tolerance for tardiness** in lieu of evaluating user discomfort, which is not necessarily reliable.

""") 

st.markdown(f"""Supposing a rate by the minute for a late checkout, the {number_delays} late arrivals brought in {round(late_revenue,2)} $ (not counting outliers).
If late checkouts have to pay for the additional time at a rate by the minute, some of the "max loss" is mitigated.""")

late_loss = canceled_loss - late_revenue
st.markdown(f"""If canceled rentals were for less than {round(late_revenue/canceled_loss*24,2)} hours, additional revenue from late checkouts and loss from canceled rentals break even after 24 hours.
If cancelled rentals were supposed to last a full day, it potentially generates a {round(late_loss,2)} $ loss, again assuming all cancelled rentals were because of a late checkout.""")

threshold_range = np.arange(0, 60*24, step=15) # 15min intervals in a day
total_late_revenue = []
for i in threshold_range:
    late_revenue_growing = data[data['delays_checkout_min_cleaned'] > i]['delays_checkout_min_cleaned'].sum()*minute_rate
    total_late_revenue.append(late_revenue_growing)
total_late_revenue.reverse()

fig, ax = plt.subplots(1, 2, sharex=True, figsize=(15,6))
ax[0].plot(threshold_range/60, total_late_revenue)
ax[0].hlines(y=canceled_loss/24*5.86, xmin=0, xmax=24, linewidth=2, color='r')
ax[0].set_title('Assuming average canceled rentals were for 5.86 hours')
ax[0].set_xlabel('Time (hours)')
ax[1].set_xlabel('Time (hours)')
ax[0].set_ylabel('Revenue $')
ax[1].plot(threshold_range/60, total_late_revenue)
ax[1].hlines(y=canceled_loss, xmin=0, xmax=24, linewidth=2, color='r')
ax[0].legend(['Additional revenue','Max loss'], loc='center left')
ax[1].set_title('Assuming average canceled rentals were for 24 hours')
st.pyplot(fig)


st.markdown("""The `max loss` supposes a 24 hour average rental. If cancelled rentals were actually for smaller durations, there is much less impact.

At this point we would really need more time data (duration of each ride, how much time a car spends unused, are there other cars available...) to accurately estimate losses.""")

at_risk = number_delays*minute_rate*1440
ended = (data['state'] == 'ended').sum()
revenue = ended*median_rental + late_revenue
risk_over_revenue = round(at_risk/(revenue),2)

st.markdown(f"""We can calculate the `maximum risk` of late arrivals.
This is even more theoretical since it assumes:
- Every minute late results in a cancellation
- All rentals have a next one planned 
- All cancelled rentals would have been a 24 hour rental

Late arrivals trigger a `max risk` of {at_risk} \$, so about {risk_over_revenue} times the total estimated revenue from rentals of {round(revenue,2)} $.""")


st.markdown("""We can see that ignoring this would have devastating consequences in this situation. It is not "real" of course, but it is interesting to see how much there is left to optimize !

We don't actually know that all cancellations are linked to a late checkout however, nor that it is not compensated by re-allocating cars to other rentals.
It would be useful to have more data on this issue, such as maybe asking users why they cancelled ? This would help us isolate the cost of late arrivals and incidentally could also unveil other issues that users might have with the rental service.

Next we'll try to set an acceptable threshold, but it would also be worthwhile to set a penalty for late arrivals and increase the rental rate after the due hour.""")

# Risk over revenue with penalty
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

st.markdown("""For standard rentals of **1 day** and a **penalty of 3 times the normal minute rate** after the rental is due, with our current data we would need to set a **threshold of 180 minutes** to mitigate losses from late checkouts.

It is of course possible to ~~squeeze some more~~ increase the profit margin by increasing the penalty, but this would also increase the risk of losing customers.""")


st.markdown("""**Additional remarks**:
A significant caveat is that all this, on top of some assumptions (duration of rental, maximum loss...), does not take into account actual demand in rentals. This has limited production applications and this should be used as an exploratory guide into the data, but neither a comprehensive projection of revenue nor a reliable way to alleviate user discomfort (see assumptions for `max loss` and `max risk` above).

A reduced profit margin is not a perfectly accurate way to account for user discomfort and a new metric should be made, perhaps using the results of a poll to estimate the impact of delays on the user experience.

It should also be noted that in order to fully measure the potential negative or positive impact of implementing this new delay, we would need start and end times of all rentals.""")
