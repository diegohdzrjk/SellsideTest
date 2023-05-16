import streamlit as st
import pandas as pd
import datetime
import traceback
import os
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
ad_units_dict["runofnetwork"] = '21827487336'


def channel_list_to_ids(x):
    global ad_units_dict
    if len(x)==0: 
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
def pauta_regular_get_Create_LineItem_data(evtdata, name_use_preset_targeting=""):
    targeting = None
    if len(name_use_preset_targeting)>0:
        targetingresult = gam.get_preset_Targeting(gam.yaml_file, name_use_preset_targeting)
        if len(targetingresult["results"])>0:
            targeting = dict(targetingresult["results"][0]['targeting'].__dict__['__values__'])
            targeting['requestPlatformTargeting'] = {'targetedRequestPlatforms': ['VIDEO_PLAYER']}
            
    if len(name_use_preset_targeting)==0:
        LI_targeting = gam.Targeting()
        LI_targeting.get_inventoryTargeting(targetedAdUnits=evtdata["Ad Unit IDs"].split(","), 
                                            excludedAdUnits=evtdata["Ad Unit Exclude IDs"].split(","))
        LI_targeting.get_technologyTargeting(targetedDevice=unidecode.unidecode(evtdata["Devices"]).lower().replace(" ","").split(","))
        LI_targeting.get_geoTargeting(targetedLocations=unidecode.unidecode(evtdata["Geography"]).lower().replace(" ","").split(","),
                                      excludedLocations=unidecode.unidecode(evtdata["GeographyExclude"]).lower().replace(" ","").split(","))
        targeting = LI_targeting.__dict__

    LI = gam.LineItem(
                    orderID = gam.get_orderNAME_data(gam.yaml_file, evtdata["Order Name"])['id'] ,
                    orderName = evtdata["Order Name"],
                    name = evtdata["LineItemName"], 
                    startDateTime = evtdata["Start DateTime"], 
                    endDateTime = evtdata["End DateTime"], 
                    lineItemType = evtdata["Line item type"].replace(" ",""), 
                    costPerUnit = float(evtdata["CPM"].replace("$","")), 
                    costType = "CPM", 
                    Goal = int(evtdata["Goal"].replace("%","")), 
                    deliveryRateType = evtdata["Delivery Rate Type"].replace(" ",""),
                    creative_width = int(evtdata["Expected creatives"].lower().split("x")[0]), 
                    creative_height = int(evtdata["Expected creatives"].lower().split("x")[1]),
                    targeting = targeting,
                    goalType = 'LIFETIME'
                 )
    return LI.__dict__

def get_config_data():
    spreadsheetID = st.secrets["LineItemsUpload"]["spreadsheetID"]
    Sheets_service = Sheets.get_GS_service()
    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "ConfiguracionPautaRegular")
    config_data = pd.DataFrame(config_data[2:], columns=config_data[0])
    for col in ["Update Date","Comments","LineItemURL","Segmento","Ad Type","LineItemID",
                "Custom targeting / Preset", "Creative IDs", "Ad Unit Exclude", "GeographyExclude"]:
        config_data[col].fillna("",inplace=True)
    config_data.dropna(inplace=True)
    
    config_data["Start DateTime"] = pd.to_datetime(config_data["Start Date"]+" "+config_data["Start Time"], format='mixed')
    config_data["End DateTime"]   = pd.to_datetime(config_data["End Date"]+" "+config_data["End Time"], format='mixed')
    config_data["Line item type"] = config_data["Line item type"].apply(lambda x: x.upper())
    config_data["Ad Unit IDs"] = config_data["Ad Unit"].apply(lambda x: channel_list_to_ids(x))
    config_data["Ad Unit Exclude IDs"] = config_data["Ad Unit Exclude"].apply(lambda x: channel_list_to_ids(x))
    return config_data

def main():
    spreadsheetID = st.secrets["LineItemsUpload"]["spreadsheetID"]
    Sheets_service = Sheets.get_GS_service()
    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "ConfiguracionPautaRegular")

    config_data_description = config_data[1]
    config_data_columns = config_data[0]
    config_data = get_config_data()

    gam.create_yamlfile()
    
    if_test = False
    IMPLEMENT__X__DAYS_BEFORE = 365
    #"+st.secrets["ad_manager"]["network_code"]+"
    GAM_url_to_LI = "https://admanager.google.com/21828487186#delivery/line_item/detail/line_item_id={}&order_id={}"

    for row, evtdata in config_data.iterrows():
        # if the event is already implemented or its canceled then nothing happends
        if evtdata["Status"] in ["OK","CANCELED","IGNORE",""]:
            #print(f"Status of LineItem: {evtdata['LineItemName']} is: {evtdata['Status']}")
            continue

        # if the event is to occur in less than IMPLEMENT__X__DAYS_BEFORE then create the LineItem
        if (evtdata["Start DateTime"]-datetime.datetime.today()).days > IMPLEMENT__X__DAYS_BEFORE:
            #print(f"LineItem: {evtdata['LineItemName']} is to implement in : {evtdata['Start DateTime']}")
            continue

        print(f"Processsing LineItem: {evtdata['LineItemName']}")

        try:
            # create the LineItem data     
            LI_createdata = pauta_regular_get_Create_LineItem_data(evtdata, 
                                                     name_use_preset_targeting=evtdata["Custom targeting / Preset"])

            print(LI_createdata)

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
        Sheets.update_spreadsheet(Sheets_service,spreadsheetID,"ConfiguracionPautaRegular",new_config_data)
        
    gam.delete_yamlfile()
