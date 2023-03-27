import streamlit as st
import pandas as pd
import time
import sys
sys.path.append("Programs")
import Upload_LI_Events as EventUploadLI
import Upload_LI_PautaR as PautaRegularUploadLI
import AutomaticUploadCampaings as AutUpdateSheets

pages = ["Carga Line Items Eventos", 
         "Carga Line Items Pauta Regular", 
         "Recarga Looker Campaign Sheets",
         ]

def load_df(page):
    try:
        if page=="Carga Line Items Eventos":
            df = EventUploadLI.get_config_data()
            df = df[~df.Status.isin(["OK"])]#,"IGNORE"])]
            return df
        
        if page=="Carga Line Items Pauta Regular":
            df = PautaRegularUploadLI.get_config_data()
            df = df[~df.Status.isin(["OK"])]#,"IGNORE"])]
            return df

        return pd.DataFrame([])
    except Exception as e:
        st.warning(f"Error Loading the data: {e}")
        return pd.DataFrame([])
    
def export_df(page):
    try:
        if page=="Carga Line Items Eventos":
            EventUploadLI.main()     
        if page=="Carga Line Items Pauta Regular":
            print("Not doing anything")
            PautaRegularUploadLI.main()
        return load_df(page)

    except Exception as e:
        st.warning(f"Error Exporting the data: {e}")
        return pd.DataFrame([])

def update_data(page):
    AutUpdateSheets.main()

##################
######  App ######
##################

st.sidebar.title("Sell Side App")
st.sidebar.header('Aplicaciones')
choice = st.sidebar.radio("Process", pages)
st.sidebar.info("""Esta applicación está diseñada para facilitar la elaboración 
            de procesos, sin necessidad de consultar a los Data Analyst""")

st.title("Sell Side App: "+choice)

if choice in pages[:2]:
    col1, col2 = st.columns(2)
    with col1:
        LoadButton = st.button("Load Data")

    with col2:
        UploadButton = st.button("Upload Line items")

    if LoadButton:
        with st.spinner("Loading data..."):
            df = load_df(choice)
            #st.session_state.df = df
            st.dataframe(df)

    if UploadButton:
        with st.spinner("Exporting data..."):
            exported_df = export_df(choice)
            st.dataframe(exported_df)

# "Recarga Looker Campaign Sheets"
elif choice == pages[2]:
    UpdateButton = st.button("Update Data")
    if UpdateButton:
        with st.spinner("Updating data..."):
            update_data(choice)
        
        st.text("The Automatic-Campaign-Data Google Sheet is updated")

    