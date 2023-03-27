import streamlit as st
import pandas as pd
import datetime
import traceback
import os
import numpy as np
import unidecode

import Google_Ad_Manager_wrapper as gam
import Google_Sheets_wrapper as Sheets
gam_version = 'v202208'

RefDataFolder = os.path.join(os.getcwd(),"Programs","RefData","")

ad_units = pd.read_csv(RefDataFolder+"AdUnitIDs.csv", dtype=str)
ad_units = ad_units[ad_units["Ad unit"].str.contains("Izzi Network")]
ad_units["Ad Unit Name"] = ad_units["Ad unit"].apply(lambda x: x.split("»")[-1].split("(")[0].strip().lower().replace(" ",""))
ad_units_dict = ad_units.set_index("Ad Unit Name")["Ad unit ID"].to_dict()

ad_units_dict["cinemax"] = '21935100075'
ad_units_dict["espn2"] = '21935016823'
ad_units_dict["tudn"] = '21935012479'
ad_units_dict["tudnhd"] = '22271035398'
ad_units_dict["nflnetwork"] = '21935043830'
ad_units_dict["vix"] = '22800534414'

def channel_list_to_ids(x):
    global ad_units_dict
    if len(x)==0: 
        return ""
    
    if x.lower().replace(" ","")=="runofnetwork": 
        return ""
    
    id_list = []
    for chn in [y.strip() for y in x.lower().replace(" ","").split(",")]:
        if chn in ad_units_dict.keys():
            id_list.append(ad_units_dict[chn])
        else:
            print(f"Check format from channel: {chn}")
            raise Exception(f"EL CANAL: {chn}  NO ESTA DADO DE ALTA")
            
    return ",".join(id_list)


# # Main functions
def get_Create_LineItem_data(evtdata):
    LI_targeting = gam.Targeting()
    LI_targeting.get_inventoryTargeting(targetedAdUnits=np.unique(evtdata["Ad Unit IDs"].split(",")))
    LI_targeting.get_technologyTargeting(targetedDevice=np.unique(unidecode.unidecode(evtdata["Devices"]).lower().
                                         replace(" ","").split(",")))
    LI_targeting.get_geoTargeting(targetedLocations=np.unique(unidecode.unidecode(evtdata["Geography"]).lower().
                                  replace(" ","").split(",")),
                                  excludedLocations=np.unique(unidecode.unidecode(evtdata["GeographyExclude"]).lower().
                                  replace(" ","").split(",")))
    
    if len(evtdata["Order ID"])>0:
        OrderID = evtdata["Order ID"]
    else:
        OrderID = gam.get_orderNAME_data(gam.yaml_file, evtdata["Order Name"])['id']
    
    LI = gam.LineItem(
                    orderID = OrderID,
                    orderName = evtdata["Order Name"],
                    name = evtdata["LineItemName"], 
                    startDateTime = evtdata["Start DateTime"], 
                    endDateTime = evtdata["End DateTime"], 
                    lineItemType = evtdata["Line item type"].replace(" ",""), 
                    costPerUnit = float(evtdata["CPM"].split("$")[-1]), 
                    costType = "CPM", 
                    Goal = int(evtdata["Goal"].split("%")[0]), 
                    creative_width = int(evtdata["Expected creatives"].split("x")[0]), 
                    creative_height = int(evtdata["Expected creatives"].split("x")[1]),
                    targeting = LI_targeting.__dict__,
                    goalType = 'DAILY'
                 )
    return LI.__dict__


def LineItem_Name_Nomenclatura(evtdata, if_test=False):
    # Functions to calculate Line Item name
    # Device
    DeviceCategory_dict = {"All":"ALL",        "Desktop":"DSK", "App":"APP",
                           "Set Top Box":"SB", "Tablet":"TBT",  "Smartphone":"SMT"}
    # Channels
    Channel_dict = {
        "Izzi ROS":"IROS",             "Afizzionados":"AFI",  "AMC":"AMC",             "AXN":"AXN",
        "Cartoon Network":"CN",        "Cinemax":"CMX",       "Comedy Central":"CC",   "De Pelicula":"DP",
        "Discovery Channel":"DCH",     "Discovery H&H":"DHH", "Distrito Comedia":"DC", "E!":"E!",
        "El Gourmet":"EG",             "ESPN":"ES1",          "ESPN 2":"ES2",          "ESPN 3":"ES3",
        "FOX":"FOX",                   "FOX Life":"FL",       "Fox Sports":"FS1",      "Fox Sports 2":"FS2",
        "Fox Sports 3":"FS3",          "FX":"FX",             "History":"HIS",         "History 2":"HIS2",
        "Hola TV":"HTV",      "Investigation Discovery":"ID", "Izzi Test":"IT",        "Las Estrellas _2":"LE2",
        "Lifetime":"LT",               "Milenio":"MIL",       "MTV":"MTV",             "NatGeo":"NG",
        "NBA TV":"NBA",                "NFL Network":"NFL",   "Nickelodeon":"NIC",     "Paramount":"PAR",
        "Sony":"SON",                  "Space":"SPA",         "Studio Universal":"SU", "TLNovelas":"TLN",
        "TNT":"TNT",                   "TNT Series":"TNTS",   "TUDN":"TUDN",           "Unicable":"UNI",
        "Universal Channel":"UCH",     "Guía SKY ROS":"GSROS","Guía SKY Home":"GSHOM", "Guía SKY Detalle":"GSDET",
        "Guía SKY Estadísticas":"GSEST",  "Blue to go ROS":"BTGROS",   "Blue to go Home":"BTGHOM",
        "Blue to go En Vivo":"BTGEV",     "Blue to go Video":"BTGVID", "SKY + BTG":"SKYROS",
        "ESPN 2 HD":"ES2HD",
    }
    Channel_dict = {unidecode.unidecode(key).lower().replace(" ",""):value for key, value in Channel_dict.items()}
    
    # Dates
    month_abr = {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV", 12:"DEC"}
    date_format = lambda x: month_abr[x.month]+x.strftime("%y")
    
    # Calculating the Line Item Name
    # Line Item Name: 
    # Media-Channel-Advertiser-OrderName-LineItemDetail-Date-Format-Device-SegmentCategory-Segment-KPI-CostType-Event
    
    # Values to determine
    if len(evtdata["Ad Unit"].split(","))>1:
        Channel = "MIX"
    else:
        Channel = Channel_dict[unidecode.unidecode(evtdata["Ad Unit"]).lower().replace(" ","")]
        
    Advertiser = evtdata["Advertiser"]
    OrderName = unidecode.unidecode(("Boletin"+evtdata["Boletin"]+"_")*(len(evtdata["Boletin"])>0)+
                                              (evtdata["Torneo"] +"_")*(len(evtdata["Torneo"]) >0)+
                                              (evtdata["Jornada"])*(len(evtdata["Jornada"])>0)
                                   ).replace(" ","")
    LineItemDetail = unidecode.unidecode((evtdata["Local"])*(len(evtdata["Local"])>0)+
                                         ("_vs_"+evtdata["Visitante"])*(len(evtdata["Visitante"])>0)
                                        ).replace(" ","")
    
    Date = date_format(evtdata["Start DateTime"])
    
    if len(evtdata["Devices"].split(","))>1:
        Device = "ALL"
    else:
        Device = DeviceCategory_dict[evtdata["Devices"]]
    
    # Constant values
    Media = 'IZZI'
    Format = 'VD'
    SegmentCategory = 'NC'
    Segment = 'ROS'
    KPI = "IMP"
    CostType = "CPM"
    
    if if_test:
        Media = "TEST"
        
    LineItemName = "-".join([Media, Channel, Advertiser, OrderName, LineItemDetail, Date, Format, Device, 
                             SegmentCategory, Segment, KPI, CostType, evtdata["Tipo de Evento"]])
    return LineItemName

def get_config_data():
    spreadsheetID = st.secrets["LineItemsUpload"]["spreadsheetID"]
    Sheets_service = Sheets.get_GS_service()
    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "Configuracion")
    print(len(config_data))
    config_data = pd.DataFrame(config_data[2:], columns=config_data[0])
    for col in ["Update Date","Comments","LineItemURL","Boletin","Jornada","Visitante",
                "Dia","Ad Type","LineItemID","LineItemName","Creative IDs","GeographyExclude"]:
        config_data[col].fillna("",inplace=True)

    config_data.dropna(inplace=True)
    
    config_data["Start DateTime"] = pd.to_datetime(config_data["Start Date"]+" "+config_data["Start Time"])
    config_data["End DateTime"]   = pd.to_datetime(config_data["End Date"]+" "+config_data["End Time"])
    config_data["Line item type"] = config_data["Line item type"].apply(lambda x: x.upper())
    config_data["Ad Unit IDs"] = config_data["Ad Unit"].apply(lambda x: channel_list_to_ids(x))
    return config_data

def main():
    spreadsheetID = st.secrets["LineItemsUpload"]["spreadsheetID"]
    Sheets_service = Sheets.get_GS_service()
    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "Configuracion")
    config_data_description = config_data[1]
    config_data = pd.DataFrame(config_data[2:], columns=config_data[0])
    for col in ["Update Date","Comments","LineItemURL","Boletin","Jornada","Visitante",
                "Dia","Ad Type","LineItemID","LineItemName","Creative IDs","GeographyExclude"]:
        config_data[col].fillna("",inplace=True)

    config_data.dropna(inplace=True)
    config_data_columns = config_data.columns
    config_data["Start DateTime"] = pd.to_datetime(config_data["Start Date"]+" "+config_data["Start Time"])
    config_data["End DateTime"]   = pd.to_datetime(config_data["End Date"]+" "+config_data["End Time"])
    config_data["Line item type"] = config_data["Line item type"].apply(lambda x: x.upper())
    config_data["Ad Unit IDs"] = config_data["Ad Unit"].apply(lambda x: channel_list_to_ids(x))


    # In[9]:
    config_data[config_data["Status"].isin(["FAIL","UPDATE"])]
    gam.create_yamlfile()

    # In[10]:

    if_test = False
    IMPLEMENT__X__DAYS_BEFORE = 3
    GAM_url_to_LI = "https://admanager.google.com/"+st.secrets["ad_manager"]["network_code"]+"#delivery/line_item/detail/line_item_id={}&order_id={}"

    for row, evtdata in config_data.iterrows():
        # if the event is already implemented or its canceled then nothing happends
        if evtdata["Status"] in ["OK","CANCELED","IGNORE",""]:
            #print(f"Status of LineItem: {evtdata['LineItemName']} is: {evtdata['Status']}")
            continue

        # Create the Line Item Name from the available data
        if len(evtdata['LineItemName'])==0 or evtdata["Status"] in ["FAIL","UPDATE"]:
            config_data.at[row, "LineItemName"] = LineItem_Name_Nomenclatura(evtdata, if_test=if_test)
            evtdata['LineItemName'] = config_data.at[row, "LineItemName"]
            print(f"Status of LineItem: {evtdata['LineItemName']} is: {evtdata['Status']}")

        # if the event is to occur in less than IMPLEMENT__X__DAYS_BEFORE then create the LineItem
        if (evtdata["Start DateTime"]-datetime.datetime.today()).days > IMPLEMENT__X__DAYS_BEFORE:
            #print(f"LineItem: {evtdata['LineItemName']} is to implement in : {evtdata['Start DateTime']}")
            continue

        print(f"Processsing LineItem: {evtdata['LineItemName']}")
        try:
            # create the LineItem data     
            LI_createdata = get_Create_LineItem_data(evtdata)

            # if line item exist it updates it otherwise it create's it
            LI_data_if_exists = len(evtdata['LineItemID'])>0
            if LI_data_if_exists:
                LI_createdata['id'] = evtdata['LineItemID']
                resp = gam.update_lineitem(gam.yaml_file, LI_createdata)
            else:
                resp = gam.create_lineitem(gam.yaml_file, LI_createdata)
                config_data.at[row, "LineItemID"] = resp[0]['id']
                evtdata['LineItemID'] = config_data.at[row, "LineItemID"]

            # associate creatives 
            if len(evtdata['Creative IDs'])>0:
                for cred_id in evtdata['Creative IDs'].replace(" ","").split(","):
                    association = {"lineItemId":evtdata['LineItemID'], "creativeId":cred_id}
                    gam.createLineItemCreativeAssociations(gam.yaml_file, association)

            config_data.at[row, "Status"] = "OK"
            config_data.at[row, "LineItemURL"] = GAM_url_to_LI.format(evtdata['LineItemID'], LI_createdata['orderId'])
            config_data.at[row, "Comments"] = "Successful"

        except Exception as e:
            print("An error occur", e)
            config_data.at[row, "Status"] = "FAIL"
            config_data.at[row, "Comments"] = traceback.format_exc()

        config_data.at[row, "Update Date"] = datetime.date.today()

    new_config_data = pd.concat([pd.DataFrame([config_data_description], columns=config_data_columns), 
                                 config_data[config_data_columns].astype(str)]).astype(str)
    gam.delete_yamlfile()
    Sheets.update_spreadsheet(Sheets_service,spreadsheetID,"Configuracion",new_config_data)
