import streamlit as st
import pandas as pd


APP_NAME = 'Booking Summary Report'

st.set_page_config(page_title=APP_NAME, page_icon='', layout='centered')

st.image(st.secrets['images']["rr_logo"], width=100)

st.title(APP_NAME)
st.info('Interpret the booking summary report from Escapia.')


upload_file = st.file_uploader('**Booking Summary Report** | Bookings Entered Between', type=['xlsx'], )


if upload_file is not None:
    df                  = pd.read_excel(upload_file, sheet_name='Sheet 1')
    df['Creation_Date'] = pd.to_datetime(df['Creation_Date'])
    df['First_Night']   = pd.to_datetime(df['First_Night'])

    dates = st.date_input('Date Range', value=(pd.to_datetime('today')-pd.Timedelta(days=7), pd.to_datetime('today')-pd.Timedelta(days=1)), key='date_range')

    if len(dates) != 2:
        st.info('Choose a second date to proceed.')
        st.stop()

    date_range = pd.date_range(start=dates[0], end=dates[1])
    past_range = pd.date_range(start=dates[0] - pd.Timedelta(days=7), end=dates[1] - pd.Timedelta(days=7))


    cf = df[df['Creation_Date'].isin(date_range)].copy()
    pf = df[df['Creation_Date'].isin(past_range)].copy()


    cf['Reason'] = cf['Reservation_Notes'].str.extract(r'\|(.*?)\|')
    pf['Reason'] = pf['Reservation_Notes'].str.extract(r'\|(.*?)\|')


    tabs = st.tabs(['📖 Bookings', '💰 Revenue','🧑‍🧑‍🧒 Reservation Types','💫 Reservation Nights','💬 Reasons for Booking'])


    with tabs[0]:
        st.header('📖 Bookings')
        l, lm, rm, r = st.columns(4)
    
        l.metric('Total', len(cf), len(cf) - len(pf))
        lm.metric('Reservations', cf[cf['Booking_Number'].str.contains('BKG')].shape[0], cf[cf['Booking_Number'].str.contains('BKG')].shape[0] - pf[pf['Booking_Number'].str.contains('BKG')].shape[0])
        rm.metric('Holds', cf[cf['Booking_Number'].str.contains('HLD')].shape[0], cf[cf['Booking_Number'].str.contains('HLD')].shape[0] - pf[pf['Booking_Number'].str.contains('HLD')].shape[0], delta_color='inverse')


    with tabs[1]:
        st.header('💰 Revenue')
        st.metric('Total Booking', f"${cf['BookingTotal'].sum():,.2f}", f"${cf['BookingTotal'].sum() - pf['BookingTotal'].sum():,.2f}")


    with tabs[2]:
        st.header('🧑‍🧑‍🧒 Reservation Types')
        l, lm, rm, r = st.columns(4)
        l.metric('Renters', cf[cf['ReservationTypeDescription'] == 'Renter'].shape[0], cf[cf['ReservationTypeDescription'] == 'Renter'].shape[0] - pf[pf['ReservationTypeDescription'] == 'Renter'].shape[0])
        lm.metric('Owners', cf[cf['ReservationTypeDescription'] == 'Owner'].shape[0], cf[cf['ReservationTypeDescription'] == 'Owner'].shape[0] - pf[pf['ReservationTypeDescription'] == 'Owner'].shape[0], delta_color='inverse')
        rm.metric('Guest of Owners', cf[cf['ReservationTypeDescription'] == 'Guest of Owner'].shape[0], cf[cf['ReservationTypeDescription'] == 'Guest of Owner'].shape[0] - pf[pf['ReservationTypeDescription'] == 'Guest of Owner'].shape[0], delta_color='inverse')
        r.metric('Maintenance', cf[cf['BookingTypeDescription'] == 'Maintenance'].shape[0], cf[cf['BookingTypeDescription'] == 'Maintenance'].shape[0] - pf[pf['BookingTypeDescription'] == 'Maintenance'].shape[0], delta_color='inverse')


    with tabs[3]:
        st.header('💫 Reservation Nights')
        l, lm, rm, r = st.columns(4)
        l.metric('Total', cf[cf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].sum(), int(cf[cf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].sum() - pf[pf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].sum()))
        lm.metric('Average', round(cf[cf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].mean(),1), round(float(cf[cf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].mean() - pf[pf['ReservationTypeDescription'].isin(['Owner', 'Guest of Owner', 'Renter'])]['Nights'].mean()),1))


    with tabs[4]:
        st.header('💬 Reasons for Booking')
        creasons = cf['Reason'].value_counts().reset_index()
        creasons.columns = ['Reason', 'Current Week Count']


        preasons = pf['Reason'].value_counts().reset_index()
        preasons.columns = ['Reason', 'Previous Week Count']

        reasons = pd.merge(creasons, preasons, on='Reason', how='outer').fillna(0)

        l, lm, rm, r = st.columns(4)
        column = 0

        for reason in reasons['Reason'].unique():

            value = reasons[reasons['Reason'] == reason]['Current Week Count'].values[0]
            delta = int(value - reasons[reasons['Reason'] == reason]['Previous Week Count'].values[0])

            match column:
                case 0:
                    l.metric(reason, value, delta)
                case 1:
                    lm.metric(reason, value, delta)
                case 2:
                    rm.metric(reason, value, delta)
                case 3:
                    r.metric(reason, value, delta)

            column += 1

            if column > 3: column = 0

        st.divider()
        
        unit_reasons = cf.groupby('Reason')['Unit_Code'].apply(list)
        unit_reasons = unit_reasons.reset_index()
        unit_reasons.columns = ['Reason', 'Units']
        st.dataframe(unit_reasons, use_container_width=True, hide_index=True)

        st.divider()


        unit_selection = st.selectbox('Select a unit to see its booking detail:', options=['Select a unit'] + cf['Unit_Code'].sort_values().unique().tolist())

        if unit_selection != 'Select a unit':
            cf_unit = cf[cf['Unit_Code'] == unit_selection].copy()
            cf_unit = cf_unit[cf_unit['Reason'].notna()]
            st.dataframe(cf_unit, use_container_width=True, hide_index=True)