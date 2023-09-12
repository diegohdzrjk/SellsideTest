#!/usr/bin/env python
# coding: utf-8

# In[1]:

import streamlit as st
import pandas as pd
import datetime
import traceback
import os
import json
import unidecode
from googleads import ad_manager, common, errors
import sys
sys.path.append("Programs")
sys.path.append("Programs/RefData")

import Google_Ad_Manager_wrapper as gam
import Google_Sheets_wrapper as Sheets

RefDataFolder = os.path.join(os.getcwd(),"Programs","RefData","")

yaml_file = 'Izzi_test.yaml'#os.path.join(os.path.abspath(os.path.curdir),'Izzi_test.yaml')
gam_version = 'v202308'



# # List of Ad Units

# In[2]:


ad_units = pd.read_csv(RefDataFolder+"AdUnitIDs.csv", dtype=str)
ad_units = ad_units[ad_units["Ad unit"].str.contains("Izzi Network")]
ad_units["Ad Unit Name"] = ad_units["Ad unit"].apply(lambda x: x.split("»")[-1].split("(")[0].strip().lower().replace(" ",""))
ad_units_dict = ad_units.set_index("Ad Unit Name")["Ad unit ID"].to_dict()


# # Update Ad Units

# In[3]:


ad_units_dict["cinemax"] = '21935100075'
ad_units_dict["espn2"] = '21935016823'
ad_units_dict["tudn"] = '21935012479'
ad_units_dict["tudnhd"] = '22271035398'
ad_units_dict["nflnetwork"] = '21935043830'



# In[4]:


ad_units_dict


# In[5]:

def delete_yamlfile():
    global yaml_file
    if os.path.exists(yaml_file):
        os.remove(yaml_file)

def create_yamlfile():
    global yaml_file
    delete_yamlfile()
    if not os.path.exists(yaml_file):
        with open(yaml_file,'w') as f:
            f.write("ad_manager:\n")
            f.write("  application_name: Izzi\n")
            f.write("  network_code: "+str(st.secrets["ad_manager"]["network_code"])+"\n")
            f.write("  client_id: "+str(st.secrets['ad_manager']['client_id'])+"\n")
            f.write("  client_secret: "+str(st.secrets['ad_manager']['client_secret'])+"\n")
            f.write("  refresh_token: "+str(st.secrets['ad_manager']['refresh_token'])+"\n")
            f.close()
    print("YAML File created")


def get_orderNAME_data(ad_network_file, OrderName, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('OrderService', version=version)
    query = {'query': f"WHERE Name = '{OrderName.strip()}'", 'values': None}
    return service.getOrdersByStatement(query).results[0]

def get_lineitem_data(ad_network_file, LineItemId, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('LineItemService', version=version)
    query = {'query': f'WHERE Id = {LineItemId}', 'values': None}
    return service.getLineItemsByStatement(query).results[0]

def get_lineitemNAME_data(ad_network_file, LineItemName, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('LineItemService', version=version)
    query = {'query': f"WHERE Name = '{LineItemName.strip()}'", 'values': None}
    return service.getLineItemsByStatement(query).results

def create_lineitem(ad_network_file, LineItem, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('LineItemService', version=version)
    return service.createLineItems(LineItem)

def update_lineitem(ad_network_file, LineItem, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('LineItemService', version=version)
    return service.updateLineItems(LineItem)

def channel_list_to_ids(x):
    id_list = []
    for chn in [y.strip() for y in x.lower().replace(" ","").split(",")]:
        if chn in ad_units_dict.keys():
            id_list.append(ad_units_dict[chn])
        else:
            print(f"Check format from channel: {chn}")
    return ",".join(id_list)


# In[6]:


class LineItem():
    #https://developers.google.com/ad-manager/api/reference/v202208/LineItemService
    def __init__(self, name, startDateTime, endDateTime, lineItemType, costPerUnit, costType, Goal, targeting,
                 priority=None, contractedUnitsBought=0, orderID='2679337185', orderName=None, LineItemID=None,
                 startDateTimeType='USE_START_DATE_TIME', creativeRotationType="OPTIMIZED", deliveryRateType="EVENLY",
                 discountType='PERCENTAGE', discount=0.0, environmentType='VIDEO_PLAYER', currencyCode='MXN',
                 creative_width=640, creative_height=480
                ):
        """
            name: Lineitem name
            startDateTime: Start Date Time
            endDateTime: End Date Time
            costPerUnit: 230mxn cpm --> {'currencyCode': 'MXN', 'microAmount': 230000000}
            Goal: number
            
            costType: CPA, CPC, CPD, CPM, VCPM, CPM_IN_TARGET, UNKNOWN
            orderID: Order ID
            orderName: Order name
            LineItemID: LineItem ID
            lineItemType: SPONSORSHIP, STANDARD, NETWORK, BULK, PRICE_PRIORITY, HOUSE, LEGACY_DFP, CLICK_TRACKING, 
                          ADSENSE, AD_EXCHANGE, BUMPER, ADMOB, PREFERRED_DEAL, UNKNOWN
            startDateTimeType: USE_START_DATE_TIME, IMMEDIATELY, ONE_HOUR_FROM_NOW, UNKNOWN
            creativeRotationType: EVEN, OPTIMIZED, MANUAL, SEQUENTIAL
            deliveryRateType: EVENLY, FRONTLOADED, AS_FAST_AS_POSSIBLE
            discountType: ABSOLUTE_VALUE, PERCENTAGE
            discount: number
            contractedUnitsBought: number of contracted Units Bought
            environmentType: VIDEO_PLAYER, BROWSER
            targeting: targeting
            currencyCode: MXN, USD
            creative_width: in pixel
            creative_height: in pixel
        """
        
        self.orderId = orderID
        self.name = name
        if LineItemID: self.id = LineItemID
        if orderName: self.orderName = orderName  
        self.startDateTime = {
                                'date': {
                                    'year': startDateTime.year,
                                    'month': startDateTime.month,
                                    'day': startDateTime.day
                                },
                                'hour': startDateTime.hour,
                                'minute': startDateTime.minute,
                                'second': startDateTime.second,
                                'timeZoneId': 'America/Mexico_City'
                            }
        self.endDateTime = {
                                'date': {
                                    'year': endDateTime.year,
                                    'month': endDateTime.month,
                                    'day': endDateTime.day
                                },
                                'hour': endDateTime.hour,
                                'minute': endDateTime.minute,
                                'second': endDateTime.second,
                                'timeZoneId': 'America/Mexico_City'
                            }
        self.startDateTimeType = startDateTimeType
        self.creativeRotationType = creativeRotationType
        self.lineItemType = lineItemType
        if priority: self.priority = priority
        self.costType = costType
        self.discountType = discountType
        self.discount = discount
        self.contractedUnitsBought = contractedUnitsBought
        self.costType = costType
        self.costPerUnit = {'currencyCode': currencyCode, 'microAmount': int(1e6*costPerUnit)}
        self.targeting = targeting
        self.environmentType = environmentType
        self.videoMaxDuration = 30000
        self.primaryGoal = {
                                'goalType': 'DAILY',
                                'unitType': 'IMPRESSIONS' ,
                                'units': Goal
                            }
        self.deliveryForecastSource = 'HISTORICAL'
        self.allowOverbook = True
        self.creativePlaceholders = [
                                        {
                                            'size': {
                                                'width': creative_width,
                                                'height': creative_height,
                                                'isAspectRatio': False
                                            },
                                            'creativeTemplateId': None,
                                            'companions': [],
                                            'appliedLabels': [],
                                            'effectiveAppliedLabels': [],
                                            'expectedCreativeCount': 1,
                                            'creativeSizeType': 'PIXEL',
                                            'targetingName': None,
                                            'isAmpOnly': False
                                        }
                                    ]
        
class Targeting():
    #https://developers.google.com/ad-manager/api/reference/v202208/LineItemService.Targeting
    def __init__(self):
        self.inventoryTargeting = {}
        self.geoTargeting = {}
        self.technologyTargeting = {}
        self.requestPlatformTargeting = {'targetedRequestPlatforms': ['VIDEO_PLAYER']}
        
    def get_geoTargeting(self, targetedLocations=[], excludedLocations=[]):
        #https://developers.google.com/ad-manager/api/reference/v202208/LineItemService.GeoTargeting
        with open(RefDataFolder+"Location_dict.json", "r") as outfile:
            Location_dict = json.load(outfile) 

        with open(RefDataFolder+"Location_dict_city.json", "r") as outfile:
            Location_dict_city = json.load(outfile)
            
        self.geoTargeting = {
            "targetedLocations": [Location_dict[loc] if loc in Location_dict.keys() else Location_dict_city[loc]
                                  for loc in targetedLocations if len(loc)>0],
            
            "excludedLocations": [Location_dict[loc] if loc in Location_dict.keys() else Location_dict_city[loc]
                                  for loc in excludedLocations if len(loc)>0],
        }
    
    def get_inventoryTargeting(self, targetedAdUnits=[], excludedAdUnits=[]):
        #https://developers.google.com/ad-manager/api/reference/v202208/LineItemService.InventoryTargeting
        self.inventoryTargeting["targetedAdUnits"] = [{'adUnitId': adunitid,'includeDescendants': True} 
                                                      for adunitid in targetedAdUnits]
        self.inventoryTargeting["excludedAdUnits"] = [{'adUnitId': adunitid,'includeDescendants': True} 
                                                      for adunitid in excludedAdUnits]
        
    def get_technologyTargeting(self, targetedDevice=[], excludedDevice=[]):
        Device_dict = {'desktop':     {'id': 30000,'name': 'Desktop'},
                       'smartphone':  {'id': 30001,'name': 'Smartphone'},
                       'tablet':      {'id': 30002,'name': 'Tablet'},
                       'connectedtv': {'id': 30004,'name': 'Connected TV'},
                       'settopbox':   {'id': 30006,'name': 'Set Top Box'}
                      }
        self.technologyTargeting["deviceCategoryTargeting"] = {
            "targetedDeviceCategories": [Device_dict[dev] for dev in targetedDevice],
            "excludedDeviceCategories": [Device_dict[dev] for dev in excludedDevice],
        }


# # Main functions

# In[7]:


def get_Create_LineItem_data(evtdata):
    LI_targeting = Targeting()
    LI_targeting.get_inventoryTargeting(targetedAdUnits=evtdata["Ad Unit IDs"].split(","))
    LI_targeting.get_technologyTargeting(targetedDevice=unidecode.unidecode(evtdata["Devices"]).lower().
                                         replace(" ","").split(","))
    LI_targeting.get_geoTargeting(targetedLocations=unidecode.unidecode(evtdata["Geography"]).lower().
                                  replace(" ","").split(","),
                                  excludedLocations=unidecode.unidecode(evtdata["GeographyExclude"]).lower().
                                  replace(" ","").split(","))

    

    LI = LineItem(
                    orderID = get_orderNAME_data(yaml_file, evtdata["Order Name"])['id'] ,
                    orderName = evtdata["Order Name"],
                    name = evtdata["LineItemName"], 
                    startDateTime = evtdata["Start DateTime"], 
                    endDateTime = evtdata["End DateTime"], 
                    lineItemType = evtdata["Line item type"], 
                    costPerUnit = float(evtdata["CPM"].split("$")[-1]), 
                    costType = "CPM", 
                    Goal = int(evtdata["Goal"].split("%")[0]), 
                    creative_width = int(evtdata["Expected creatives"].split("x")[0]), 
                    creative_height = int(evtdata["Expected creatives"].split("x")[1]),
                    targeting = LI_targeting.__dict__,
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


# # Read Configuration Sheet

# # Main function

# In[8]:

def get_config_data():
    spreadsheetID = "1Lm6_eAXt8soY_QsmUxa8O5LI62VQwfbT8ZAadH9Myjw"
    Sheets_service = Sheets.get_GS_service()
    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "Configuracion")
    print(len(config_data))
    config_data = pd.DataFrame(config_data[2:], columns=config_data[0])
    for col in ["Update Date","Comments","LineItemURL","Boletin","Jornada","Visitante",
                "Dia","Ad Type","LineItemID","LineItemName","GeographyExclude"]:
        config_data[col].fillna("",inplace=True)

    config_data.dropna(inplace=True)
    
    config_data["Start DateTime"] = pd.to_datetime(config_data["Start Date"]+" "+config_data["Start Time"])
    config_data["End DateTime"]   = pd.to_datetime(config_data["End Date"]+" "+config_data["End Time"])
    config_data["Line item type"] = config_data["Line item type"].apply(lambda x: x.upper())
    config_data["Ad Unit IDs"] = config_data["Ad Unit"].apply(lambda x: channel_list_to_ids(x))
    return config_data

def main():
    spreadsheetID = "1Lm6_eAXt8soY_QsmUxa8O5LI62VQwfbT8ZAadH9Myjw"
    Sheets_service = Sheets.get_GS_service()

    config_data = Sheets.get_spreadsheet_data(Sheets_service, spreadsheetID, "Configuracion")
    config_data_description = config_data[1]
    config_data = pd.DataFrame(config_data[2:], columns=config_data[0])
    for col in ["Update Date","Comments","LineItemURL","Boletin","Jornada","Visitante",
                "Dia","Ad Type","LineItemID","LineItemName","GeographyExclude"]:
        config_data[col].fillna("",inplace=True)

    config_data.dropna(inplace=True)
    config_data_columns = config_data.columns
    config_data["Start DateTime"] = pd.to_datetime(config_data["Start Date"]+" "+config_data["Start Time"])
    config_data["End DateTime"]   = pd.to_datetime(config_data["End Date"]+" "+config_data["End Time"])
    config_data["Line item type"] = config_data["Line item type"].apply(lambda x: x.upper())
    config_data["Ad Unit IDs"] = config_data["Ad Unit"].apply(lambda x: channel_list_to_ids(x))


    # In[9]:

    config_data[config_data["Status"].isin(["FAIL","UPDATE"])]

    create_yamlfile()
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
                resp = update_lineitem(yaml_file, LI_createdata)
            else:
                resp = create_lineitem(yaml_file, LI_createdata)
                config_data.at[row, "LineItemID"] = resp[0]['id']
                evtdata['LineItemID'] = config_data.at[row, "LineItemID"]

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
    delete_yamlfile()
    Sheets.update_spreadsheet(Sheets_service,spreadsheetID,"Configuracion",new_config_data)
