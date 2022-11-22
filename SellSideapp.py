import streamlit as st
import pandas as pd
import Upload_Lineitems_2022_10_18 as uploadLI
import time
import logging

logging.getLogger('googleapicliet.locked_file').setLevel(logging.ERROR)

st.sidebar.header('Input')
#st.image("")
st.sidebar.title("Sell Side App")
choice = st.sidebar.radio("Process", ["Upload Line Items API"])

st.sidebar.info("""Esta applicación está diseñada para facilitar la elaboración 
            de procesos, sin necessidad de consultar a los Data Analyst""")


##################
#### Programs ####
##################

#### Upload Line Items API ####
    
def Upload_Line_Items_API_page():
    display_columns = ["Status", "Update Date", "Order Name", "",
                        "Start Date", "Start Time", "End Date", "End Time",
                        "Goal", "CPM", "Ad Unit", "Geography", 
                        "GeographyExclude", "Devices"]
    def load_data():
        configdata = uploadLI.get_config_data()
        return configdata

    def loadtable():
        data_load_state = st.text('Loading data...')
        try:
            data = load_data()
            data_loaded = True
            data_load_state.text("Data loaded")
        except Exception as e:
            print(e)
            data = pd.DataFrame([])
            data_loaded = False
            data_load_state.text("Error loading the data")
        return data_loaded, data

    def displaytable(data):
        new_data =  data[~data.Status.isin(["OK"])]
        new_data = new_data[display_columns]
    
        st.header("New Line Items left to update or upload")
        table = st.dataframe(new_data)

        return table

    # Page Body
    st.title("Upload Line Items using GAM API")    

    col1, col2 = st.columns(2)
    with col1:
        LoadButton = st.button("Load Google Sheets data")
    with col2:
        UploadButton = st.button("Upload Line items")

    if LoadButton:
        data_loaded, data = loadtable()
    else:
        data_loaded = False
    
    if data_loaded:
        displaytable(data)
    
    if UploadButton:
        st.text("Uploading LineItems")
        uploadLI.create_yamlfile()
        uploadLI.main()
        uploadLI.delete_yamlfile()
        data_loaded, data = loadtable()

        if data_loaded:
            displaytable(data)


##############
#### Main ####
##############

if __name__ == "__main__":
    if choice=="Upload Line Items API":
        Upload_Line_Items_API_page()