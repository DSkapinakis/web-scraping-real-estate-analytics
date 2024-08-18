
#import libraries

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from copy import deepcopy
import re


'''
Features to preprocess
'''

num_cols_with_string_parts = ['Price', 'Square Meters', 'Plot area']

feature_to_delete = ['Semi-outdoor space',                                      
'Pets allowed',                                      
'Suitable for investment',                                
'Insect screens',                                            
'Front facing, Corner property',                            
'Suitable for holiday home',                         
'Inner building part',                                      
'Front facing',                                             
'Double fronted',                                            
'Double fronted, Corner property',
'Double fronted, Inner building part',                           
'Front facing, Double fronted',                               
'Ideal for students',                                        
'Corner property',                                            
'Front facing, Double fronted, Corner property',              
'Available from',
'Availability',
'Agents accepted',
'Corner property, Inner building part', 
'Rent includes',
'Playroom', 
'Front facing, Double fronted, Inner building part', 
'Private rooftop']     

binary_features_to_impute =  ['Suitable for professional use',                              
'Fireplace',                                                  
'Tents',                                                     
'Air conditioning',                                            
'Solar water heater',                                         
'No maintenance fees',                                        
'Aluminium frames',                                            
'Parking',                                                    
'Short term rental',                                         
'Security door',                                              
'Pool',                                                      
'Garden',                                                     
'Storage room',                                               
'Night electricity tariff',                                   
'Furnished',                                                   
'No elevator']

features_to_impute_nan =[
'Zone',                                                        
'Year Built',                                                 
'Renovation year',                                            
'Floor type',                                                  
'Bathrooms',                                                   
'View',                                                       
'Bedrooms',                                                     
'Style',                                                      
'Condition',                                                   
'Plot area',
'Heating Method'                                                  
]

heating_system_features = ['Autonomous heating centrally installed',	
                           'Fully autonomous', 'Central heating',	
                           'Autonomous heating centrally installed, Central heating']



'''
Encoder class and preprocessing functions of the program - helpers for main Transform() function
'''

class CustomEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        for col in self.columns:
            X[col] = X[col].replace(to_replace={X[col][X[col].notna()].iloc[0]: 1}).fillna(0)
        return X
    
def fix_num_cols_with_string_parts(df, col):
    
    df[col] = df[col].apply(lambda x: re.sub(r'[^\d]+', '', x) if x is not np.nan else np.nan)    

    return df[col]

def assign_heating(row):
    if pd.isna(row['No heating']):
        return 1
    else:
        return 0
    
def assign_heating_system(row):
    relevant_columns = [col for col in heating_system_features if col in row.index]
    if not relevant_columns or row[relevant_columns].isna().all():
        return 'Not specified'
    elif 'Fully autonomous' in row and row['Fully autonomous'] == 'Fully autonomous':
        return 'Fully autonomous'
    elif 'Central heating' in row and row['Central heating'] == 'Central heating':
        return 'Central heating'
    elif 'Autonomous heating centrally installed, Central heating' in row and row['Autonomous heating centrally installed, Central heating'] == 'Autonomous heating centrally installed, Central heating':
        return 'Autonomous heating centrally installed, Central heating'
    elif 'Autonomous heating centrally installed' in row and row['Autonomous heating centrally installed'] == 'Autonomous heating centrally installed':
        return 'Autonomous heating centrally installed'


'''
Transform Function: takes as input a raw dataframe and returns a preprocessed one without missing values and
redundant features. Also it defines a data schema got certain variables. 
'''


def Transform(df):

    if 'Availability' in df.columns: 
        df = df.drop(df[df['Availability'] == 'Occupied'].index)

    if 'WC' in df.columns: 
        df['WC'] = df['WC'].fillna(0)

    for col in [i for i in num_cols_with_string_parts if i in df.columns]:
    # Fix numerical columns that have a string part - initial preprocessing
        df[col] = fix_num_cols_with_string_parts(df, col)


    ## define schema 
    schema = {'WC': int, 'visits': int, 'Square Meters': float, 
    'saves': int,'Price': float, 'Bathrooms': int,'Bedrooms': int, 'visits': float,
    'Year Built': int, 'Renovation year': int}


    df[[i for i in list(schema.keys()) if i in df.columns]] = df[[i for i in list(schema.keys()) if i in df.columns]].fillna(-999)

    # Apply the conversions using astype()
    df[[i for i in list(schema.keys()) if i in df.columns]] = df[[i for i in list(schema.keys()) if i in df.columns]].astype(schema)    

    df.replace(-999, np.nan, inplace=True)

    # datetime object
    if 'publication_Date' in df.columns:
        df['publication_Date'] = pd.to_datetime(df['publication_Date'], dayfirst=True)

    df_transformed = deepcopy(df)

    # delete features
    if any(i in df_transformed.columns for i in feature_to_delete):
        df_transformed = df_transformed.drop(columns = [i for i in feature_to_delete if i in df_transformed.columns])

    # binary imputation 1 - 0 (nan)
    if any(i in df_transformed.columns for i in binary_features_to_impute):
        enc = CustomEncoder(columns = [i for i in binary_features_to_impute if i in df_transformed.columns])
        df_transformed = enc.fit_transform(df_transformed)
    
    # imputation not specified
    if any(i in df_transformed.columns for i in features_to_impute_nan):
        for feature in [i for i in features_to_impute_nan if i in df_transformed.columns]:
            df_transformed[feature] = df_transformed[feature].apply(lambda x: 'Not specified' if  pd.isna(x) else x)

    # heating 1 - 0
    if 'No heating' in df_transformed.columns:
        df_transformed['Heating'] = df_transformed.apply(assign_heating, axis=1)
        df_transformed = df_transformed.drop(columns='No heating')

    if any(i in df_transformed.columns for i in heating_system_features):

        df_transformed['Heating System'] = df_transformed.apply(assign_heating_system, axis=1)
        df_transformed = df_transformed.drop(columns=[i for i in heating_system_features if i in df_transformed.columns])

    return df_transformed