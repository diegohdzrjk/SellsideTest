from googleads import ad_manager, common, errors
import tempfile

gam_version_default = 'v202208'
def report(ad_network_file, dimensions, columns, start_date, end_date, dimension_attributes=[], time_zone_type=None, filters=None, dateRangeType='CUSTOM_DATE', version=gam_version_default, adUnitView="Normal", reportCurrency="USD", printall=False):
    
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

def get_lineitem_data(ad_network_file, LineItemId, version=gam_version_default):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    lineitem_service = client.GetService('LineItemService', version=version)
    return lineitem_service.getLineItemsByStatement({'query': f'WHERE Id = {LineItemId}', 'values': None}).results[0]

def get_forecast_lineitem_data(ad_network_file, lineitem_data, version=gam_version_default):
    client = ad_manager.AdManagerClient.LoadFromStorage(ad_network_file)
    client.cache = common.ZeepServiceProxy.NO_CACHE
    forecast_service = client.GetService('ForecastService', version=version)
    return forecast_service.getDeliveryForecast({'lineItem': lineitem_data}, {})
