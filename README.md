# Web Scraping real estate analytics

This repository containts 3 main files: 
- scaper.py
- transform.py
- implementation.ipynb

`scraper.py` and `transform.py` contain helper functions for the ETL process, which are imported in `implementation.ipynb` jupyter notebook. Selenium and BeautifulSoup libraries are used for html parsing (`scraper.py`) and all the necessary preprocessing (imputation, removal of redundant features, data schema) is done through `transform.py` functions, ending up with a clean dataframe containing one property per row. The program supports certain property locations which are accessible through google place ids (geo_id), but in an updated version google place api could be used instead. Also, the program offers the possibility of scraping either residential or professional properties, land, parking places, availabe to rent or to buy. 

An example is demonstrated in `implementation.ipynb`, where 305 properties for the location Gyzi are downloaded. An Exploratory Data Analysis (EDA) together with a naive regression analysis take place afterwards. A wide range of techniques could be further used, namely unsupervised machine learning (clustering) to identify clusters of properties and supervised machine learning to predict user visits or property pricing (data-driven real estate investment analysis).  







