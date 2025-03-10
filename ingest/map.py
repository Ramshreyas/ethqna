# crawler/map.py

import json
import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from os import getenv
import yaml

def load_config(config_file='config/config.yaml'):
    """
    Load configuration from a YAML file.
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def map_sources(sources, storage_path, api_key_env_var):
    """
    Map the provided sources and save the maps.
    """
    # Load environment variables
    load_dotenv()

    api_key = getenv(api_key_env_var)
    if not api_key:
        raise EnvironmentError(f"{api_key_env_var} not found in environment variables.")

    app = FirecrawlApp(api_key=api_key)

    map_results = {}
    for source in sources:
        print(f"Mapping source: {source}")
        map_result_dict = app.map_url(source)
        map_results[source] = map_result_dict

        # Create source-specific directory
        source_dir = os.path.join(storage_path, 'maps', source.replace('https://', '').replace('http://', '').replace('/', '_'))
        os.makedirs(source_dir, exist_ok=True)

        # Write the map to a JSON file
        map_file = os.path.join(source_dir, 'map_new.json')
        with open(map_file, 'w') as f:
            json.dump(map_result_dict, f, indent=4)
        print(f"Map saved to {map_file}")

    return map_results
