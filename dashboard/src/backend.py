import logging
import os
from typing import Optional
import time

import pandas as pd

from src.utils import initialize_logger, load_env_vars
from src.feature_store_api.api import FeatureStore
from src.feature_store_api.types import FeatureGroupConfig, FeatureViewConfig

# initialize_logger()
load_env_vars()

logger = logging.getLogger()

OHLC_FEATURE_GROUP = FeatureGroupConfig(
    name='ohlc_feature_group_v2',
    version=3,
    description='OHLC data for crypto products',
    primary_key=['timestamp', 'product_id'],
    event_time='timestamp',
    online_enabled=True,
)

OHLC_FEATURE_VIEW = FeatureViewConfig(
    name='ohlc_feature_view_v2',
    version=4,
    description='OHLC feature view',
    feature_group_config=OHLC_FEATURE_GROUP,
)

def generate_list_primary_keys(
    from_unix_seconds: int,
    to_unix_seconds: int,
    product_ids: list,
) -> list:

    primary_keys = []

    for product_id in product_ids:
        for unix_seconds in range(from_unix_seconds, to_unix_seconds):
            primary_keys.append({
                'timestamp': unix_seconds * 1000,
                'product_id': product_id,
            })

    return primary_keys

def temp():

    import hsfs
    
    # Establish connection
    connection = hsfs.connection()

    # Get the feature store
    fs = connection.get_feature_store(name='paustemplate_featurestore')

    # Retrieve the feature view
    fv = fs.get_feature_view('ohlc_feature_view', version=4)

    # Read all data from the feature view
    features_raw = fv.read()

    # Convert to DataFrame
    features_df = pd.DataFrame(features_raw)

    # Print the entire DataFrame
    print(features_df)

    # Close the connection
    connection.close()


def get_features(
    last_minutes: int = 5,
    current_unix_seconds: Optional[int] = None,
    product_ids: Optional[list] = ['XBT/EUR'],
) -> pd.DataFrame:

    if current_unix_seconds is None:
        current_unix_seconds = int(time.time())

    logger.info("Connecting to Feature Store")
    feature_store = FeatureStore(
        api_key=os.environ["HOPSWORKS_API_KEY"],
        project_name=os.environ["HOPSWORKS_PROJECT_NAME"],
    )

    logger.info("Getting feature view to read data from")
    feature_view = feature_store.get_or_create_feature_view(OHLC_FEATURE_VIEW)
    logger.info(f"Feature view details: {feature_view}")

    logger.info("Generating primary keys to read data from")
    from_unix_seconds = current_unix_seconds - last_minutes * 60
    primary_keys = generate_list_primary_keys(
        from_unix_seconds, 
        current_unix_seconds,
        product_ids)
    
    logger.info(f"First 10 primary keys: {primary_keys[:10]}")
    logger.info(f"Reading {len(primary_keys)} primary keys from {OHLC_FEATURE_VIEW}.")

    # Read raw data from the feature view
    features_raw = feature_view.read(primary_keys)
    logger.info(f"Raw data retrieved: {features_raw}")

    # Convert raw data to DataFrame
    features = pd.DataFrame(features_raw)
    logger.info(f"DataFrame shape after read: {features.shape}")
    logger.info(f"DataFrame columns: {features.columns}")
    logger.info(f"DataFrame head: {features.head()}")

    # Check if the DataFrame contains any non-None values
    if features.isnull().all().all():
        logger.error("All values in the DataFrame are None. Check the feature store data and configuration.")
    else:
        logger.info("DataFrame contains valid data.")

    # sort ohlc by product_id and timestamp
    features = features.sort_values(by=['product_id', 'timestamp'])

    # After retrieving the features, print the first few rows to check data existence
    if not features.empty:
        print(features.head())
    else:
        print("The DataFrame is empty.")

    return features

if __name__ == '__main__':

    features = get_features(last_minutes=10, product_ids=['XBT/EUR', 'XBT/USD'])
    print(features)