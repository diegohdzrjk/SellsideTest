import streamlit as st
import pandas as pd
import datetime
import numpy as np
import Google_Ad_Manager_wrapper as gam
import Google_Sheets_wrapper as Sheets
gam_version = 'v202208'

# # 2- GLOBAL PARAMETERS

# In[2]:


GAM_LineItem_dimensions = ['ORDER_NAME','LINE_ITEM_NAME','ADVERTISER_NAME']
GAM_LineItem_dimensionAttributes = ['ORDER_START_DATE_TIME', 'ORDER_END_DATE_TIME', 
                                    'LINE_ITEM_START_DATE_TIME', 'LINE_ITEM_END_DATE_TIME', 
                                    'LINE_ITEM_GOAL_QUANTITY', 'LINE_ITEM_COST_TYPE', 
                                    'LINE_ITEM_COST_PER_UNIT', 'LINE_ITEM_SPONSORSHIP_GOAL_PERCENTAGE']

GAM_LineItem_columns = ['TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS']

GAM_LineItem_unmutable_columns = ['ORDER_ID', 'LINE_ITEM_ID', 'SHORT_CAMPAIGN_NAME', 'SHORT_SEGMENT_NAME']
GAM_LineItem_updatable_columns = ['LINE_ITEM_ID',
                                 'ORDER_NAME', 'LINE_ITEM_NAME', 'ADVERTISER_NAME', 'ADVERTISER_ID', 'ORDER_START_DATE_TIME', 
                                 'ORDER_END_DATE_TIME', 'LINE_ITEM_START_DATE_TIME','LINE_ITEM_END_DATE_TIME', 
                                 'LINE_ITEM_GOAL_QUANTITY', 'LINE_ITEM_COST_TYPE', 'LINE_ITEM_COST_PER_UNIT',
                                 'LINE_ITEM_SPONSORSHIP_GOAL_PERCENTAGE'
                                ]

GAM_Creative_dimensions = ['ORDER_NAME','LINE_ITEM_NAME','CREATIVE_NAME']
GAM_Creative_dimensionAttributes = ['ORDER_START_DATE_TIME', 'ORDER_END_DATE_TIME', 
                                    'LINE_ITEM_START_DATE_TIME', 'LINE_ITEM_END_DATE_TIME']

GAM_Creative_columns = ['TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS']

GAM_Creative_unmutable_columns = ['ORDER_ID', 'LINE_ITEM_ID', 'CREATIVE_ID', 'SHORT_CAMPAIGN_NAME', 
                                  'SHORT_SEGMENT_NAME', 'SHORT_CREATIVE_NAME']
GAM_Creative_updatable_columns = ['LINE_ITEM_ID', 'CREATIVE_ID',
                                 'ORDER_NAME', 'LINE_ITEM_NAME', 'CREATIVE_NAME', 'ORDER_START_DATE_TIME', 
                                 'ORDER_END_DATE_TIME', 'LINE_ITEM_START_DATE_TIME','LINE_ITEM_END_DATE_TIME'
                                ]


GAM_Order_dimensions = ['ORDER_NAME','LINE_ITEM_NAME','ADVERTISER_NAME']
GAM_Order_dimensionAttributes = ['ORDER_START_DATE_TIME', 'ORDER_END_DATE_TIME', 
                                 'LINE_ITEM_START_DATE_TIME', 'LINE_ITEM_END_DATE_TIME', 
                                 'LINE_ITEM_GOAL_QUANTITY']

GAM_Order_columns = ['TOTAL_LINE_ITEM_LEVEL_IMPRESSIONS']

GAM_Order_unmutable_columns = ['ORDER_ID','LINE_ITEM_GOAL_QUANTITY']
GAM_Order_updatable_columns = ['ORDER_NAME','ORDER_ID', 'ORDER_START_DATE_TIME', 'ORDER_END_DATE_TIME']


# # 3- GAM Cleaning functions

# In[12]:

def clean_order_gam_df(df):
    df.rename(columns={col:col.split(".")[1] for col in df.columns}, inplace=True)
    df.LINE_ITEM_START_DATE_TIME = df.LINE_ITEM_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.LINE_ITEM_END_DATE_TIME = df.LINE_ITEM_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    
    df.ORDER_START_DATE_TIME = df.ORDER_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.ORDER_END_DATE_TIME = df.ORDER_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    
    df.LINE_ITEM_GOAL_QUANTITY.fillna("0", inplace=True)
    df = df[df.ORDER_ID!=2699100650][df.columns[:-1]]
    df = df[df.ORDER_NAME.apply(lambda x: "test" not in x.lower())].reset_index(drop=True)
    df.LINE_ITEM_GOAL_QUANTITY = pd.to_numeric(df.LINE_ITEM_GOAL_QUANTITY.apply(lambda x: -1 if x=="Unlimited" else x))
    cols = ["ORDER_NAME", "ORDER_ID", "ORDER_START_DATE_TIME", "ORDER_END_DATE_TIME", "LINE_ITEM_GOAL_QUANTITY"]
    df = df[cols].groupby(cols[:-1]).sum().reset_index()
    return df

def clean_gam_df(df):
    df.rename(columns={col:col.split(".")[1] for col in df.columns}, inplace=True)
    df.LINE_ITEM_START_DATE_TIME = df.LINE_ITEM_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.LINE_ITEM_END_DATE_TIME = df.LINE_ITEM_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    
    df.ORDER_START_DATE_TIME = df.ORDER_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.ORDER_END_DATE_TIME = df.ORDER_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    
    df.LINE_ITEM_GOAL_QUANTITY.fillna("0", inplace=True)
    df.LINE_ITEM_SPONSORSHIP_GOAL_PERCENTAGE = df.LINE_ITEM_SPONSORSHIP_GOAL_PERCENTAGE.apply(lambda x: "0" 
                                                                                              if x=="-" else x)
    df.LINE_ITEM_COST_PER_UNIT /= 1e6
    df = df[df.ORDER_ID!=2699100650][df.columns[:-1]]
    df = df[df.ORDER_NAME.apply(lambda x: "test" not in x.lower())].reset_index(drop=True)
    return df

def clean_creative_gam_df(df):
    df.rename(columns={col:col.split(".")[1] for col in df.columns}, inplace=True)
    df.LINE_ITEM_START_DATE_TIME = df.LINE_ITEM_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.LINE_ITEM_END_DATE_TIME = df.LINE_ITEM_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    
    df.ORDER_START_DATE_TIME = df.ORDER_START_DATE_TIME.apply(lambda x: x.split("T")[0])
    df.ORDER_END_DATE_TIME = df.ORDER_END_DATE_TIME.apply(lambda x: x.split("T")[0] if x!="Unlimited" 
                                                                  else "Unlimited")
    df = df[df.ORDER_ID!=2699100650][df.columns[:-1]]
    df = df[df.ORDER_NAME.apply(lambda x: "test" not in x.lower())].reset_index(drop=True)
    return df


def generate_short_names(df):
    ABR_DATES = []
    for n in range(15,30):
        ABR_DATES += [f"ENE{n}",f"FEB{n}",f"MAR{n}",f"ABR{n}",f"MAY{n}",f"JUN{n}",
                      f"JUL{n}",f"AGO{n}",f"SEP{n}",f"OCT{n}",f"NOV{n}",f"DIC{n}"]
    
    ABR_TO_REMOVE = st.secrets["ad_managerAbbrebiations"]["ABR_TO_REMOVE"]
    ABR_TO_REMOVE_ORDER = st.secrets["ad_managerAbbrebiations"]["ABR_TO_REMOVE_ORDER"] + ABR_DATES 
    ABR_TO_REMOVE_LI =  st.secrets["ad_managerAbbrebiations"]["ABR_TO_REMOVE_LI"] + ABR_DATES #Date
    ABR_TO_REMOVE_CREATIVE = st.secrets["ad_managerAbbrebiations"]["ABR_TO_REMOVE_CREATIVE"] + ABR_DATES #Date

    ABR_TO_REMOVE_space = ["(COPIA)"]+[f"(COPIA{n})" for n in range(0,11)]
    ABR_TO_REMOVE_space += ["(COPY)"]+[f"(COPY{n})" for n in range(0,11)]

    def unique_list(string1):
        words = string1.split()
        return (" ".join(sorted(set(words), key=words.index)))

    def get_name_by_dash_nomenclature(name, nametype):
        if nametype=="order":
            return name.split("-")[6]
        elif nametype=="lineitem":
            return name.split("-")[5]
        elif nametype=="creative":
            return name.split("-")[5]
        else:
            return name
    
    def get_name(s, nametype, ABR_list, words_to_remove=[]):
        if (nametype=="order" and s.count("-")==10)|(nametype=="lineitem" and s.count("-")==8)|(nametype=="creative" and s.count("-")==7):
            return get_name_by_dash_nomenclature(s, nametype)
        
        new_s = s.upper().replace(" ","")
        for abr in ABR_list:
            new_s = new_s.replace("-"+abr.upper()+"-","-")
            
        for abr in ABR_TO_REMOVE_space:
            new_s = new_s.replace(abr.upper(),"")
        
        new_s_r = new_s
        for words in words_to_remove:
            if new_s_r == words.upper().replace(" ",""):
                continue
            for w in words.upper().split(" "):
                new_s_r= new_s_r.replace(w,"")
        
        swords = lambda s_: s_.replace("_"," ").replace("-"," ").split(" ")[1:-1]
        returntext = unique_list(" ".join([si.capitalize() for si in swords(new_s_r)]).strip())
        
        if len(returntext)<2:
            return unique_list(" ".join([si.capitalize() for si in swords(new_s)]).strip())
        else: 
            return returntext
    
    df["SHORT_CAMPAIGN_NAME"] = df.apply(lambda x: get_name(x.ORDER_NAME, "order", ABR_TO_REMOVE_ORDER), axis=1)
    
    if "CREATIVE_NAME" in df.columns:
        df["SHORT_SEGMENT_NAME"]  = df.apply(lambda x: get_name(x.LINE_ITEM_NAME, "lineitem", ABR_TO_REMOVE_LI,
                                                                [x.SHORT_CAMPAIGN_NAME]), axis=1)
        df["SHORT_CREATIVE_NAME"] = df.CREATIVE_NAME.apply(lambda x: get_name(x, "creative", ABR_TO_REMOVE_CREATIVE))
    else:
        df["SHORT_SEGMENT_NAME"]  = df.apply(lambda x: get_name(x.LINE_ITEM_NAME, "lineitem", ABR_TO_REMOVE_LI, 
                                                                [x.ADVERTISER_NAME, x.SHORT_CAMPAIGN_NAME]), axis=1)
    return df

def get_GAM_updated_category(df, column, GAM_dimensions, GAM_columns, GAM_dimensionAttributes, cleanfuncs,
                             update_all=False, mindate=datetime.date(2022,1,1)):

    if column not in df.columns:
        print(f"{column} not in Data columns")
        return None, None
    
    if "ORDER_END_DATE_TIME" not in df.columns:
        print("ORDER_END_DATE_TIME not in Data columns")
        return None, None
    
    updated_gam_df = pd.DataFrame()
    stored_data_df = pd.DataFrame()

    if len(df)>0:
        loaded_items = df[column].unique()
        items_isUnlimited = []
        update_items = []
        stored_items = []

        # If update all the we don't need to check one by one
        if update_all:
            update_items = loaded_items
        else:
            # Check which Items are still running to continiously update them
            for i, item in enumerate(loaded_items):
                item_end_date = df[df[column]==item].iloc[0].ORDER_END_DATE_TIME
                # If Item is long lived then check for any updates in names / creative or else
                
                if item_end_date == "Unlimited":
                    items_isUnlimited.append(item)
                    continue

                # Check if date is less than the item end date
                if datetime.date.today() < datetime.datetime.strptime(item_end_date, "%Y-%m-%d").date():
                    update_items.append(item)
                    continue

                # If not necesary to update them we saved them appart
                stored_items.append(item)

        # Check not Unlimited items for starting date --> min value is the start date for the GAM consulting
        data_check = df[df[column].isin(update_items)]
        end_date = datetime.date.today()
        start_date = np.max([mindate, 
                             np.min(np.array([datetime.datetime.strptime(startdate, "%Y-%m-%d").date()
                                              for startdate in data_check.ORDER_START_DATE_TIME.unique()]))
                           ])
        
        print(start_date, end_date)
        # Get the order ID's of all the updatable items
        if items_isUnlimited == []:
            data_check = df[df[column].isin(update_items)]
        else:
            data_check = df[df[column].isin(items_isUnlimited+update_items)]
            
        update_orderIDs = data_check.ORDER_ID.unique()

        # Call to GAM API to get updated data
        if update_all:
            filters = None
        else:
            filters = "ORDER_ID IN ("+", ".join(update_orderIDs)+")"
        
        gam.create_yamlfile()
        
        gam_report = gam.report(gam.yaml_file, GAM_dimensions, GAM_columns, start_date, end_date, filters=filters,
                                dimension_attributes=GAM_dimensionAttributes, version=gam_version, 
                                adUnitView="HIERARCHICAL")

        gam.delete_yamlfile()

        gam_df = pd.read_csv(gam_report, compression = 'gzip')
        for func in cleanfuncs:
            gam_df = gam_df.pipe(func)
        updated_gam_df = gam_df.copy()
        
        if len(stored_items)>0:
            stored_data_df = df[df[column].isin(stored_items)]

    print(updated_gam_df.shape, stored_data_df.shape)
    
    return updated_gam_df.astype(str), stored_data_df.astype(str)



def main():
    
    spreadsheetID = st.secrets["ad_managerAbbrebiations"]["spreadsheetID"]
    service = Sheets.get_GS_service()
    order_data = Sheets.get_spreadsheet_data(service, spreadsheetID, "OrderData")

    if order_data:
        order_data = pd.DataFrame(order_data[1:], columns=order_data[0])
    else:
        order_data = pd.DataFrame(columns=order_data[0])

    print("order_data", order_data.shape)
    
    updated_gam_df, stored_data_df = get_GAM_updated_category(order_data, 'ORDER_NAME', GAM_Order_dimensions, 
                                                          GAM_Order_columns, GAM_Order_dimensionAttributes,
                                                          cleanfuncs=[clean_order_gam_df],
                                                          update_all=True
                                                         )
    
    # Get the last week active orders to add them
    end_date = datetime.date.today()
    start_date = datetime.date.today()-datetime.timedelta(8)

    gam.create_yamlfile()
    gam_report = gam.report(gam.yaml_file, GAM_Order_dimensions, GAM_Order_columns, start_date, end_date, 
                            dimension_attributes=GAM_Order_dimensionAttributes, 
                            version=gam_version, adUnitView="HIERARCHICAL")

    gam.delete_yamlfile()

    gam_df = pd.read_csv(gam_report, compression = 'gzip')
    active_gam_df = gam_df.pipe(clean_order_gam_df).copy().astype(str)
    print("active_gam_df", active_gam_df.shape)
    
    # Merge the previous loaded updated data and the newly gotten gotten data
    dup_col_ids = ["ORDER_ID"]
    join_df_unmutable = pd.concat([active_gam_df, updated_gam_df, stored_data_df, order_data])[GAM_Order_unmutable_columns]
    join_df_unmutable.drop_duplicates(subset=dup_col_ids, keep='last', inplace=True)
    join_df_unmutable.set_index("ORDER_ID", inplace=True)

    join_df_updatable = pd.concat([active_gam_df, updated_gam_df, stored_data_df, order_data])[GAM_Order_updatable_columns]
    join_df_updatable.drop_duplicates(subset=dup_col_ids, keep='first', inplace=True)
    join_df_updatable.set_index("ORDER_ID", inplace=True)

    join_df = pd.concat([join_df_unmutable, join_df_updatable], axis=1, join='inner').reset_index()[active_gam_df.columns]
    join_df.sort_values(["ORDER_START_DATE_TIME", 'ORDER_NAME'], ascending=False, inplace=True)
    print("join_df_unmutable", join_df_unmutable.shape)
    print("join_df_updatable", join_df_updatable.shape)
    print("join_df", join_df.shape)

    service = Sheets.get_GS_service()
    Sheets.update_spreadsheet(service, spreadsheetID, "OrderData", df=join_df)


    lineitem_data = Sheets.get_spreadsheet_data(service, spreadsheetID, "LineItems")

    if lineitem_data:
        lineitem_data = pd.DataFrame(lineitem_data[1:], columns=lineitem_data[0])
    else:
        lineitem_data = pd.DataFrame()
    print("lineitem_data", lineitem_data.shape)

    updated_gam_df, stored_data_df = get_GAM_updated_category(lineitem_data, 'LINE_ITEM_NAME', GAM_LineItem_dimensions, 
                                                              GAM_LineItem_columns, GAM_LineItem_dimensionAttributes,
                                                              cleanfuncs=[clean_gam_df, generate_short_names],
                                                              update_all=True
                                                             )
    # ## 4.2- Get active orders

    # In[7]:


    # Get the last week active orders to add them
    end_date = datetime.date.today()
    start_date = datetime.date.today()-datetime.timedelta(8)

    gam.create_yamlfile()
    gam_report = gam.report(gam.yaml_file, GAM_LineItem_dimensions, GAM_LineItem_columns, start_date, end_date, 
                            dimension_attributes=GAM_LineItem_dimensionAttributes, 
                            version=gam_version, adUnitView="HIERARCHICAL")
    gam.delete_yamlfile()

    gam_df = pd.read_csv(gam_report, compression = 'gzip')
    active_gam_df = gam_df.pipe(clean_gam_df).pipe(generate_short_names).copy().astype(str)
    print("active_gam_df", active_gam_df.shape)

    # ## 4.3- Joining the data

    # In[8]:


    # Merge the previous loaded updated data and the newly gotten gotten data
    dup_col_ids = ["LINE_ITEM_ID"]
    join_df_unmutable = pd.concat([active_gam_df, updated_gam_df, stored_data_df, lineitem_data])[GAM_LineItem_unmutable_columns]
    join_df_unmutable.drop_duplicates(subset=dup_col_ids, keep='last', inplace=True)
    join_df_unmutable.set_index("LINE_ITEM_ID", inplace=True)

    join_df_updatable = pd.concat([active_gam_df, updated_gam_df, stored_data_df, lineitem_data])[GAM_LineItem_updatable_columns]
    join_df_updatable.drop_duplicates(subset=dup_col_ids, keep='first', inplace=True)
    join_df_updatable.set_index("LINE_ITEM_ID", inplace=True)

    join_df = pd.concat([join_df_unmutable, join_df_updatable], axis=1, join='inner').reset_index()[active_gam_df.columns]
    join_df.sort_values(["LINE_ITEM_START_DATE_TIME", 'ORDER_NAME','LINE_ITEM_NAME'], ascending=False, inplace=True)
    print("join_df_unmutable", join_df_unmutable.shape)
    print("join_df_updatable", join_df_updatable.shape)
    print("join_df", join_df.shape)

    # ## 4.4- Upload data to Sheets

    # In[9]:

    service = Sheets.get_GS_service()
    Sheets.update_spreadsheet(service, spreadsheetID, "LineItems", df=join_df)

    # # 5- Creative Catalog

    # ## 5.1- Update already loaded data

    # In[26]:

    creatives_data = Sheets.get_spreadsheet_data(service, spreadsheetID, "CreativeTab")

    if creatives_data:
        creatives_data = pd.DataFrame(creatives_data[1:], columns=creatives_data[0])
    else:
        creatives_data = pd.DataFrame()
    print("creatives_data",creatives_data.shape)


    # In[27]:


    creatives_updated_gam_df, creatives_stored_data_df = get_GAM_updated_category(creatives_data, 'CREATIVE_NAME',
                                                                                  GAM_Creative_dimensions, 
                                                                                  GAM_Creative_columns, 
                                                                                  GAM_Creative_dimensionAttributes, 
                                                                                  cleanfuncs=[clean_creative_gam_df, 
                                                                                              generate_short_names],
                                                                                  update_all=True
                                                                                 )

    # ## 5.2- Get active orders

    # In[28]:


    end_date = datetime.date.today()
    start_date = datetime.date.today()-datetime.timedelta(8)
    
    gam.create_yamlfile()
    gam_report = gam.report(gam.yaml_file, GAM_Creative_dimensions, GAM_Creative_columns, start_date, end_date, 
                            dimension_attributes=GAM_Creative_dimensionAttributes, version=gam_version, 
                            adUnitView="HIERARCHICAL")
    gam.delete_yamlfile()

    gam_df = pd.read_csv(gam_report, compression = 'gzip')
    creatives_active_gam_df = gam_df.pipe(clean_creative_gam_df).pipe(generate_short_names).copy().astype(str)

    # ## 5.3- Joining the data

    # In[29]:


    dup_col_ids = ['LINE_ITEM_ID',"CREATIVE_ID"]
    join_df_unmutable = pd.concat([creatives_active_gam_df, creatives_updated_gam_df, 
                                   creatives_stored_data_df, creatives_data])[GAM_Creative_unmutable_columns]
    join_df_unmutable.drop_duplicates(subset=dup_col_ids, keep='last', inplace=True)
    join_df_unmutable.set_index(dup_col_ids, inplace=True)

    join_df_updatable = pd.concat([creatives_active_gam_df, creatives_updated_gam_df, 
                                   creatives_stored_data_df, creatives_data])[GAM_Creative_updatable_columns]
    join_df_updatable.drop_duplicates(subset=dup_col_ids, keep='first', inplace=True)
    join_df_updatable.set_index(dup_col_ids, inplace=True)

    creatives_join_df = pd.concat([join_df_unmutable, join_df_updatable], axis=1, 
                                  join='inner').reset_index()[creatives_active_gam_df.columns]
    creatives_join_df.sort_values(["LINE_ITEM_START_DATE_TIME", 'ORDER_NAME','LINE_ITEM_NAME'], ascending=False, inplace=True)
    print("creatives_join_df_unmutable", join_df_unmutable.shape)
    print("creatives_join_df_updatable", join_df_updatable.shape)
    print("creatives_join_df", creatives_join_df.shape)

    # # 5.4- Upload data to Sheets

    # In[30]:

    service = Sheets.get_GS_service()
    Sheets.update_spreadsheet(service, spreadsheetID, "CreativeTab", df=creatives_join_df)