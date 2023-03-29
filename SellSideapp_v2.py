import streamlit as st
import pandas as pd
import sys
sys.path.append("Programs")
import Upload_Order_LI
import AutomaticUploadCampaings as AutUpdateSheets

pages = ["Carga de Ordenes y Line Items",
         "Recarga Looker Campaign Sheets",
         ]

def load_df(page):
    titles = []
    dfs = []
    try:
        df = Upload_Order_LI.ordenes_get_config_data()
        #df = df[~df.Status.isin(["OK"])]#,"IGNORE"])]
        dfs.append(df)
    except Exception as e:
        st.warning(f"Error Loading the data: {e}")
        dfs.append(df)
    titles.append("Pagina Ordenes")

    try:
        df = Upload_Order_LI.pauta_regular_get_config_data()
        df = df[~df.Status.isin(["OK"])]#,"IGNORE"])]
        dfs.append(df)
    except Exception as e:
        st.warning(f"Error Loading the data: {e}")
        dfs.append(df)
    titles.append("Pagina Pauta Regular")
    
    try:
        df = Upload_Order_LI.eventos_get_config_data()
        df = df[~df.Status.isin(["OK"])]#,"IGNORE"])]
        dfs.append(df)
    except Exception as e:
        st.warning(f"Error Loading the data: {e}")
        dfs.append(df)
    titles.append("Pagina Eventos")
    
    return titles, dfs
    
def export_df(page):
    try:
        if page==pages[0]:
            Upload_Order_LI.main()
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

if choice == pages[0]:
    st.info(
f"""Esta applicación sirve para crear las Órdenes y LineItems de campañas de video en GAM para **{st.secrets['client']['client']}**.\n
El procedimiento a seguir es el siguiente:\n
- Hacer click en el botón **'Load Data'** para visualizar las Órdenes y LineItems predefinidas en el archivo sheets {st.secrets['client']['url_sheets']}
- Revisar que los datos sean los correctos
- Hacer click en el botón **'Update Data'**. Esta acción creara las Órdenes y LineItems pertinentes y mostrará en pantalla el resto de los Órdenes y LineItems pendientes.
- En caso de ocurrir un error, comunicar a un screenshot a **{st.secrets['client']['encargado']}**
""")

    col1, col2 = st.columns(2)
    with col1:
        LoadButton = st.button("Load Data")

    with col2:
        UploadButton = st.button("Upload Data")

    if LoadButton:
        with st.spinner("Loading data..."):
            titles, dfs = load_df(choice)
            for title, df in zip(titles, dfs):
                st.text(title)
                st.dataframe(df)

    if UploadButton:
        with st.spinner("Exporting data..."):
            titles, exported_dfs = export_df(choice)
            for title, df in zip(titles, exported_dfs):
                st.text(title)
                st.dataframe(df)

# "Recarga Looker Campaign Sheets"
elif choice == pages[1]:
    UpdateButton = st.button("Update Data")
    if UpdateButton:
        with st.spinner("Updating data..."):
            update_data(choice)
        
        st.text("The Automatic-Campaign-Data Google Sheet is updated")

    