from googleads import ad_manager, common, errors
import tempfile
import os
import json
import streamlit as st

yaml_file = 'yaml_file.yaml'
gam_version = 'v202208'
RefDataFolder = os.path.join(os.getcwd(),"Programs","RefData","")


def report(ad_network_file, dimensions, columns, start_date, end_date, dimension_attributes=[], time_zone_type=None, filters=None, dateRangeType='CUSTOM_DATE', version=gam_version, adUnitView="Normal", reportCurrency="USD", printall=False):
    
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    #client.cache = common.ZeepServiceProxy.NO_CACHE
    network_service = client.GetService('NetworkService', version=version)
    current_network = network_service.getCurrentNetwork()
    if printall: print('Found network %s (%s)!' % (current_network['displayName'], current_network['networkCode']))
        
    if filters is None:
        statement = (ad_manager.StatementBuilder(version=version)
                    .Limit(None)
                    .Offset(None))
    else:
        statement = (ad_manager.StatementBuilder(version=version)
                    .Where(filters)
                    .Limit(None)
                    .Offset(None))
        
    if dateRangeType=='CUSTOM_DATE':
        dict_query=  {
                          'dimensions': dimensions,
                          'dimensionAttributes': dimension_attributes,
                          'statement': statement.ToStatement(),
                          'columns': columns,
                          'dateRangeType': 'CUSTOM_DATE',
                          'startDate': start_date,
                          'endDate': end_date
                      }
    else:
        dict_query=  {
                          'dimensions': dimensions,
                          'dimensionAttributes': dimension_attributes,
                          'statement': statement.ToStatement(),
                          'columns': columns,
                          'dateRangeType': dateRangeType
                      }
        
    if(adUnitView=="HIERARCHICAL"):
        dict_query.update( {'adUnitView':'HIERARCHICAL' } )
    
    if reportCurrency:
        dict_query.update( {'reportCurrency':reportCurrency} )
        
    report_job = {'reportQuery':dict_query }
    if time_zone_type is not None:
        report_job['reportQuery']['timeZoneType'] = time_zone_type
    report_downloader = client.GetDataDownloader(version=version)
    try:
        if printall: print("Hola 1")
        report_job_id = report_downloader.WaitForReport(report_job)
        if printall: print("Hola 2")
    except errors.AdManagerReportError as e:
        print('Failed to generate report. Error was: %s' % e)
    export_format = 'CSV_DUMP'
    report_file = tempfile.NamedTemporaryFile(suffix='.csv.gz', delete=False)
    if printall: print("Hola 4")
    report_downloader.DownloadReportToFile(report_job_id, export_format, report_file)
    if printall: print("Hola 5")
    report_file.close()
    return report_file.name

def get_lineitem_data(ad_network_file, LineItemId, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    lineitem_service = client.GetService('LineItemService', version=version)
    return lineitem_service.getLineItemsByStatement({'query': f'WHERE Id = {LineItemId}', 'values': None}).results[0]

def get_forecast_lineitem_data(ad_network_file, lineitem_data, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    forecast_service = client.GetService('ForecastService', version=version)
    return forecast_service.getDeliveryForecast({'lineItem': lineitem_data}, {})

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

def get_preset_Targeting(ad_network_file, preset_name, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('TargetingPresetService', version=version)
    query = {'query': f"WHERE Name = '{preset_name.strip()}'", 'values': None}
    return service.getTargetingPresetsByStatement(query)

def createLineItemCreativeAssociations(ad_network_file, association, version=gam_version):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    service = client.GetService('LineItemCreativeAssociationService', version=version)
    return service.createLineItemCreativeAssociations(association)


class LineItem():
    #https://developers.google.com/ad-manager/api/reference/v202208/LineItemService
    def __init__(self, name, startDateTime, endDateTime, lineItemType, costPerUnit, costType, Goal, targeting,
                 priority=None, contractedUnitsBought=0, orderID='2679337185', orderName=None, LineItemID=None,
                 startDateTimeType='USE_START_DATE_TIME', creativeRotationType="OPTIMIZED", deliveryRateType=None,#"EVENLY",
                 discountType='PERCENTAGE', discount=0.0, environmentType='VIDEO_PLAYER', currencyCode='MXN',
                 goalType = 'DAILY', creative_width=640, creative_height=480
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
        if deliveryRateType: self.deliveryRateType=deliveryRateType
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
                                'goalType': goalType,
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
        if targetedAdUnits!=[""]:
            self.inventoryTargeting["targetedAdUnits"] = [{'adUnitId': adunitid,'includeDescendants': True} 
                                                      for adunitid in targetedAdUnits]
        if excludedAdUnits!=[""]:
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
