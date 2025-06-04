# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import requests
import uuid
from datetime import datetime, timezone
import re
import argparse

def generate_bom_ref(component_name):
    return f"{component_name}-{uuid.uuid5(uuid.NAMESPACE_OID, component_name)}"

def initialize_bom_structure():
    uuid_v4 = uuid.uuid4()
    urn_uuid = f"urn:uuid:{uuid_v4}"
    # Struttura base del BOM CycloneDX
    cyclonedx_bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": urn_uuid,
        "version": 1,
        "metadata":{}
    }
    
    return cyclonedx_bom

def generate_cyclonedx_component(data):

    #Structure of the single component representing the machine learning model.
    component = {
        "type": "machine-learning-model",
        "bom-ref": generate_bom_ref(data.get('id')),
        "licenses": [],
        "externalReferences": [{
            "url":  f"https://huggingface.co/{data.get('id')}",
            "type": 'documentation'
        }
        ],
        "modelCard": {
            "modelParameters": {}
        }
    }

    #components->name
    if data.get('id'):
        component["name"]=data.get('id')

    #components->modelCard->task
    if data.get('pipeline_tag'):
        component["modelCard"].setdefault("modelParameters", {})["task"] = data['pipeline_tag']


    #components->modelCard->modelParameters->architectureFamily
    if 'model_type' in data.get('config', {}):
        component["modelCard"].setdefault("modelParameters", {})['architectureFamily'] = data['config']['model_type']
        

    #components->modelCard->modelParameters->modelArchitecture
    if 'architectures' in data.get('config', {}):
        component["modelCard"].setdefault("modelParameters", {})['modelArchitecture'] = ", ".join(data['config']['architectures']) 
        

    #components->modelCard->properties "library_name"
    if data.get('library_name'): 
        component["modelCard"].setdefault("properties", []).append(generate_properties('library_name',data['library_name']))

    #components->authors 
    if data.get('author'):
        component['authors'] = [{'name': data['author']}]

    #components->licenses
    if 'license' in data.get('cardData', {}):
        license = data['cardData']['license']
        # Controlla se license è una lista
        if isinstance(license, list):
            for lic in license:
                lic_info = is_license_recognized(lic) 
                if lic_info:
                    #The license is recognized by SPDX
                    #components->licenses->license->id, #components->licenses->license->url
                    component['licenses'].append({"license": {"id": lic_info['licenseId'], "url":lic_info['reference']}}) 
                else:
                    #The license is not recognized by SPDX.
                    if lic == 'other': 
                        if 'license_name' in data.get('cardData', {}):
                            license_name = data['cardData']['license_name'] #components->licenses->license->name
                            license_entry = {"license": {"name": license_name}}
                            if 'license_link' in data.get('cardData', {}):
                                license_link = data['cardData']['license_link']
                                license_entry['license']['url'] = license_link #components->licenses->license->url
                            if 'license_details' in data.get('cardData', {}):
                                license_details = data['cardData']['license_details']
                                license_entry['license']['properties'] = [generate_properties('license_details',license_details)] #components->licenses->license->properties
                            component['licenses'].append(license_entry)
                        else:
                            #If license == other but license_name does not define
                            license_entry = {"license": {"name": lic}} #components->licenses->license->name
                            component['licenses'].append(license_entry)
                    else:
                        #If SPDX does not define the license used and lic != other
                        component['licenses'].append({"license": {"name": lic}}) #components->licenses->license->name
        # license is not a list
        else:
            lic_info = is_license_recognized(license)
            if lic_info:
                #The license is not recognized by SPDX.
                #components->licenses->license->id, #components->licenses->license->url
                component['licenses'].append({"license": {"id": lic_info['licenseId'], "url":lic_info['reference']}}) 
            else:
                #The license is not recognized by SPDX.
                if license == 'other': #https://github.com/huggingface/hub-docs/blob/main/datasetcard.md?plain=1
                    if 'license_name' in data.get('cardData', {}):
                        license_name = data['cardData']['license_name'] #components->licenses->license->name
                        license_entry = {"license": {"name": license_name}}
                        if 'license_link' in data.get('cardData', {}):
                            license_link = data['cardData']['license_link']
                            license_entry['license']['url'] = license_link #components->licenses->license->url
                        if 'license_details' in data.get('cardData', {}):
                            license_details = data['cardData']['license_details']
                            license_entry['license']['properties'] = [generate_properties('license_details',license_details)] #components->licenses->license->properties
                        component['licenses'].append(license_entry)
                    else:
                        #If license == other but license_name does not define
                        license_entry = {"license": {"name": license}} #components->licenses->license->name
                        component['licenses'].append(license_entry)
                else:
                    #If SPDX does not define the license used and lic != other
                    component['licenses'].append({"license": {"name": license}}) #components->licenses->license->name

        
    #components->description #description (text description)
    valid_titles_model_description = ['model description', 'model details', 'about', 'description', 'details', 'intro', 'introduction', 'model', 'model info', 'model information', 'model overview','model summary','model type','overview','system info']
    model_description = get_model_info(data.get('id'), valid_titles_model_description)
    if model_description:
        component['description'] = model_description
    else : #The sections titled 'Model Details' and 'Model Description' are present
        model_description = get_model_info(data.get('id'), ['model description'])
        if model_description:
            component['description'] = model_description
        

    #components->tags
    if data.get('tags', {}):
        component['tags'] = data.get('tags')


    #components->modelCard->quantitativeAnalysis->performanceMetrics    #performanceMetrics
    if 'model-index' in data.get('cardData', {}):
        model_index = data.get('cardData', {}).get('model-index', [])
        
        for entry in model_index:
            results = entry.get('results', None) 

            for result in results: 

                #type, split, config  dataset
                dataset_name_mi = result.get('dataset',{}).get('type',{}) # dataset id
                dataset_split_mi = result.get('dataset',{}).get('split',{}) # Example: test
                dataset_config_mi = result.get('dataset',{}).get('config',{}) #The name of the dataset subset used in `load_dataset()`. Example: fr in `load_dataset("common_voice", "fr")`. See the `datasets` docs for more info: https://huggingface.co/docs/datasets/package_reference/loading_methods#datasets.load_dataset.name

                slice_mi = f"dataset: {dataset_name_mi}"

                # Add 'split' if present.
                if dataset_split_mi:
                    slice_mi += f", split: {dataset_split_mi}"

                # Add 'config' if present.
                if dataset_config_mi:
                    slice_mi += f", config: {dataset_config_mi}"

                
                metrics_mi = result.get('metrics', {})
                for metric in metrics_mi:
                    type_mi = metric.get('type', {}) #components->modelCard->quantitativeAnalysis->performanceMetrics->type #Example: wer. Use metric id from https://hf.co/metrics
                    value_mi = metric.get('value', {}) #components->modelCard->quantitativeAnalysis->performanceMetrics->value
                    
                    if 'performanceMetrics' in component.get('modelCard',{}).get('quantitativeAnalysis',{}):
                        component['modelCard']['quantitativeAnalysis']['performanceMetrics'].append({"slice": slice_mi,
                                                                                                    "type": type_mi,
                                                                                                    "value": value_mi}) 

                    else:
                        component['modelCard']['quantitativeAnalysis'] = {}
                        component['modelCard']['quantitativeAnalysis']['performanceMetrics'] = [{"slice": slice_mi,
                                                                                                "type": type_mi,
                                                                                                "value": value_mi}] 

    #base_model, base_model_relation
    #components->modelCard->properties
    if 'base_model' in data.get('cardData', {}):
        base_model = data['cardData']['base_model']
        if isinstance(base_model, list):
            base_model = ', '.join(base_model)
        if 'properties' in component.get('modelCard', {}): 
            component['modelCard']['properties'].append(generate_properties('base_model',base_model)) #components->modelCard->properties
        else:
            component['modelCard']['properties'] = [generate_properties('base_model',base_model)] #components->modelCard->properties
        
        if 'base_model_relation' in data.get('cardData', {}):
            base_model_relation = data['cardData']['base_model_relation']
            component['modelCard']['properties'].append(generate_properties('base_model_relation',base_model_relation)) #components->modelCard->properties


    #useCases (text description)
    #modelCard->consideration->useCases
    valid_titles_uses = ['responsibility & safety','responsible deployment','use','uses','uses and limitations','direct use','use cases','intended use','intended uses','intended uses & limitations']
    useCases = get_model_info(data.get('id'), valid_titles_uses)
    if useCases:
        if 'modelCard' in component and 'consideration' in component['modelCard']:
            component['modelCard']['consideration']['useCases'] = useCases
        else:
            component['modelCard']['consideration'] = {}
            component['modelCard']['consideration']['useCases'] = useCases



    #co2_eq_emissions
    #modelCard->consideration->environmentalConsiderations->properties
    if 'co2_eq_emissions' in data.get('cardData', {}):
        
        if 'modelCard' in component and 'consideration' in component['modelCard']:
            component['modelCard']['consideration']['environmentalConsiderations']= {}
            component['modelCard']['consideration']['environmentalConsiderations']['properties'] = []
        else:
            component['modelCard']['consideration'] = {}
            component['modelCard']['consideration']['environmentalConsiderations']= {}
            component['modelCard']['consideration']['environmentalConsiderations']['properties'] = []


        co2_eq_emissions = data['cardData']['co2_eq_emissions']
        
        if isinstance(co2_eq_emissions, dict):
            if co2_eq_emissions.get('emissions', {}):
                emissions = co2_eq_emissions['emissions']
                component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('emissions',emissions))
            if co2_eq_emissions.get('source', {}):
                source = co2_eq_emissions['source'] 
                component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('source',source))
            if co2_eq_emissions.get('training_type', {}):
                training_type = co2_eq_emissions['training_type']
                component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('training_type',training_type))
            if co2_eq_emissions.get('geographical_location', {}):
                geographical_location = co2_eq_emissions['geographical_location']    
                component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('geographical_location',geographical_location)) 
            if co2_eq_emissions.get('hardware_used', {}):
                hardware_used = co2_eq_emissions['hardware_used']
                component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('hardware_used',hardware_used)) 
        else:
            component['modelCard']['consideration']['environmentalConsiderations']['properties'].append(generate_properties('emissions',co2_eq_emissions))

    
    return component


def generate_properties(name, value):
    properties = {
        "name": name,
        "value": value
    }
    return properties

def list_to_string(data):
    # Check if 'license' is a list or a string.
    if isinstance(data, list):
        string_data = ", ".join(data) #license is sometimes returned as a list, so we convert it into a string.
        return string_data
    else:
        return data
    
# Function to get the list of SPDX licenses.
def get_spdx_licenses():
    url = "https://spdx.org/licenses/licenses.json"  
    response = requests.get(url)
    if response.status_code == 200:
        licenses_data = response.json()
        return [
            {"licenseId": license["licenseId"], "reference": license["reference"]}
            for license in licenses_data["licenses"]
        ]
    else:
        raise Exception("Impossibile recuperare l'elenco delle licenze SPDX.")

#Function to check if a license is recognized by SPDX, if not recognized, returns None.
def is_license_recognized(license_name):
    spdx_licenses = get_spdx_licenses()
    for spdx_license in spdx_licenses:
        if license_name.lower() == spdx_license['licenseId'].lower():
            return  {
                'licenseId': spdx_license['licenseId'],        
                'reference': spdx_license['reference']  
            }

    return None  

#Function to remove emojis from a string using regular expressions.
def rimuovi_emoji(testo):
    pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticon
        "\U0001F300-\U0001F5FF"  # Various symbols and pictograms.
        "\U0001F680-\U0001F6FF"  # Transport and various symbols.
        "\U0001F700-\U0001F77F"  # Alchemical symbols.
        "\U0001F780-\U0001F7FF"  # Additional geometric symbols.
        "\U0001F800-\U0001F8FF"  # Additional arrow symbols.
        "\U0001F900-\U0001F9FF"  # Hand and person symbols.
        "\U0001FA00-\U0001FA6F"  # Various objects and tools.
        "\U0001FA70-\U0001FAFF"  # Various emojis
        "\U00002700-\U000027BF"  # Dingbats
        "\U0001F1E0-\U0001F1FF"  # Flags.
        "]+", flags=re.UNICODE
    )
    return pattern.sub(r'', testo)

    
def get_hf_readme(model_id): 

    url = f"https://huggingface.co/{model_id}/raw/main/README.md"
    
    try:
        response = requests.get(url, timeout=10)  
        response.raise_for_status()  
        return response.text  
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to retrieve README.md for model {model_id}: {e}")
        return None

#Function to extract the model description from the README.md.
def get_model_info(model_id, valid_titles):
    """
    Extracts the model description from its README.md.

    :param model_id: Model ID (e.g., 'google-bert/bert-base-uncased')
    :return: Model description as a string
    """
    description_text = []
    capture = False
    
    try:
        readme_content = get_hf_readme(model_id)
        # Splits the content into lines and removes the whitespace
        righe = [riga.strip() for riga in readme_content.splitlines()]

        for i, riga in enumerate(righe):
            if riga.startswith('#'):
                titolo_senza_asterischi = riga.lstrip('# ') 
                titolo_minuscolo = titolo_senza_asterischi.lower()  
                titolo_senza_emoji = rimuovi_emoji(titolo_minuscolo)  

            # Starts capturing the text of the description section
            if capture:
                description_text.append(riga)
                # Stop capturing when another section is found or the last line is reached
                if riga.startswith("#") or i == len(righe)-1:
                    capture = False
                    description_text.pop()
                    description_text.pop(0)  
                    #model_description = "\n".join(description_text) 
                    model_description = "".join(description_text)  
                    return model_description

           
            if riga.startswith('#') and titolo_senza_emoji in valid_titles:
                capture = True
                description_text.append(riga)

    except Exception as e:
        print(f"Error: {e}")
        return None  


def generate_dataset_component(dataset_ID):
#components->modelCard->modelParameters->datasets
    API_dataset_URL = "https://huggingface.co/api/datasets/{}"
    Dataset_URL = "https://huggingface.co/datasets/{}"
    url_dataset = ''
    description = ''
    author_name = ''
    author_url = ''

    license = ''
    license_name = ''
    license_link = ''
    license_details = ''

    response = requests.request("GET", API_dataset_URL.format(dataset_ID))
    if response.status_code == 200:
        datasetData = json.loads(response.text)
        url_dataset = Dataset_URL.format(dataset_ID) #components->modelCard->modelParameters->datasets->contents->url
        dataset = {
            "type": "dataset",
            "bom-ref": generate_bom_ref(dataset_ID),
            "name": dataset_ID,
            "contents": {
                "url": url_dataset,
                "properties": []
            }
        }
        #dataset = generate_cyclonedx_datasets(dataset_ID,url_dataset)
        description = datasetData.get('description', '') #components->modelCard->modelParameters->datasets->description
        author_name = datasetData.get('author','') #components->modelCard->modelParameters->datasets->governance->owners->organization->name
        author_url = 'https://huggingface.co/{}'
        author_url = author_url.format(author_name) #components->modelCard->modelParameters->datasets->governance->owners->organization->url 

        #components->modelCard->modelParameters->datasets->contents->properties 
        if datasetData.get('cardData') is None:
            return
        #task_categories dataset
        if 'task_categories' in datasetData.get('cardData', {}):
            task_categories_d = list_to_string(datasetData['cardData']['task_categories'])
            dataset['contents']['properties'].append(generate_properties('task_categories',task_categories_d))
        
        #task_ids 
        if 'task_ids' in datasetData.get('cardData', {}):
            task_ids_d = list_to_string(datasetData['cardData']['task_ids'])
            dataset['contents']['properties'].append(generate_properties('task_ids',task_ids_d))

        #language 
        if 'language' in datasetData.get('cardData', {}):
            language_d = list_to_string(datasetData['cardData']['language'])
            dataset['contents']['properties'].append(generate_properties('language',language_d))

        #language_details
        if 'language_details' in datasetData.get('cardData', {}):
            language_details_d = list_to_string(datasetData['cardData']['language_details'])
            dataset['contents']['properties'].append(generate_properties('language_details',language_details_d))
        
        #size_categories number_of_elements_in_dataset
        if 'size_categories' in datasetData.get('cardData', {}):
            size_categories_d = list_to_string(datasetData['cardData']['size_categories'])
            dataset['contents']['properties'].append(generate_properties('size_categories',size_categories_d))

        #annotations_creators
        if 'annotations_creators' in datasetData.get('cardData', {}):
            annotations_creators_d = list_to_string(datasetData['cardData']['annotations_creators'])
            dataset['contents']['properties'].append(generate_properties('annotations_creators',annotations_creators_d))

        #language_creators
        if 'language_creators' in datasetData.get('cardData', {}):
            language_creators_d = list_to_string(datasetData['cardData']['language_creators'])
            dataset['contents']['properties'].append(generate_properties('language_creators',language_creators_d))

        #pretty_name 
        if 'pretty_name' in datasetData.get('cardData', {}):
            pretty_name_d = list_to_string(datasetData['cardData']['pretty_name'])
            dataset['contents']['properties'].append(generate_properties('pretty_name',pretty_name_d))

        #source_datasets 
        if 'source_datasets' in datasetData.get('cardData', {}):
            source_datasets_d = list_to_string(datasetData['cardData']['source_datasets'])
            dataset['contents']['properties'].append(generate_properties('source_datasets',source_datasets_d))
        
        #paperswithcode_id
        if 'paperswithcode_id' in datasetData.get('cardData', {}):
            paperswithcode_id_d = list_to_string(datasetData['cardData']['paperswithcode_id'])
            dataset['contents']['properties'].append(generate_properties('paperswithcode_id',paperswithcode_id_d))

        #config
        if 'configs' in datasetData.get('cardData', {}):
            configs_d = datasetData['cardData']['configs']
            for config_d in configs_d:
                config_name_d = config_d['config_name']  #Name of the dataset subset, if applicable. Example: default
                data_files_d = config_d['data_files']
                strConfigInfo = "Name of the dataset subset: {} ".format(config_name_d)
                strConfigInfo += ", ".join([json.dumps(d) for d in data_files_d])
                dataset['contents']['properties'].append(generate_properties('configs',strConfigInfo)) #configs  "Name of the dataset subset: {...configs->config_name}, split: {...configs->data_files->split}, path: {...configs->data_files->path}"
        

        
        #license
        if 'license' in datasetData.get('cardData', {}):
            license = list_to_string(datasetData['cardData']['license']) 
            dataset['contents']['properties'].append(generate_properties('license',license))
        if license == 'other': 
            if 'license_name' in datasetData.get('cardData', {}):
                license_name = datasetData['cardData']['license_name']
                dataset['contents']['properties'].append(generate_properties('license_name',license_name))
            if 'license_link' in datasetData.get('cardData', {}):
                license_link = datasetData['cardData']['license_link']
                dataset['contents']['properties'].append(generate_properties('license_link',license_link))
            if 'license_details' in datasetData.get('cardData', {}):
                license_details = datasetData['cardData']['license_details']
                dataset['contents']['properties'].append(generate_properties('license_details',license_details))


        
    else:
        # Error, the dataset is not present on Hugging Face
        print(f"Error in the request. Status code: {response.status_code}, dataset: {dataset_ID}")

        dataset = {
            "type": "dataset",
            "bom-ref": generate_bom_ref(dataset_ID),
            "name": dataset_ID,
            "contents": {
                "url": url_dataset,
                "properties": []
            }
        }
    
    

    governance_info = {
        "owners": [
            {
                "organization": {
                    "name": author_name,
                    "url": author_url
                }
            }
        ]   
    }
    
    
    dataset['description'] = description
    dataset['governance'] = governance_info

    dataset_compoent = {
        "type": "data",
        "bom-ref": generate_bom_ref(dataset_ID),
        "name": dataset_ID,
        "data": []
    }
    dataset_compoent['data'].append(dataset)

    return dataset_compoent




def generateAIBOM(modelID):

    # Generates the basic structure of the BOM
    bom = initialize_bom_structure()

    API_URL_ = f"https://huggingface.co/api/models/{modelID}"

    try:
        response_ = requests.get(API_URL_)
        response_.raise_for_status()  
        data = response_.json() 
        print(f"✅ Successfully retrieved model info for: {modelID}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed. Error: {e}")
        exit()

    # Generate the component
    component = generate_cyclonedx_component(data)


    # Add the datasets to the component
    datasets = []
    if 'datasets' in data.get('cardData', {}):
        datasets = data['cardData']['datasets']
        if isinstance(datasets, str): 
            datasets = [datasets]  # Trasforma la stringa in una lista con l'elemento come unico elemento    
        for name_dataset in datasets:
            component.setdefault('modelCard', {}).setdefault('modelParameters', {}).setdefault('datasets', []) # Ensure that the nested structure exists before appending the dataset reference
            component['modelCard']['modelParameters']['datasets'].append({'ref':generate_bom_ref(name_dataset)})
            dataset_component = generate_dataset_component(name_dataset)
            
            bom.setdefault('components',{})
            bom['components'].append(dataset_component)

    
    



    timestamp_iso = datetime.now(timezone.utc).isoformat()
    bom['metadata']['timestamp'] = timestamp_iso

    bom['metadata']['component'] = component 

    return bom



# Create the parser
parser = argparse.ArgumentParser(description="This script takes the Hugging Face model ID as input and generates an AIBOM (AI Bill of Materials) in CycloneDX format (.json). The AIBOM includes essential information about the model, such as dependencies, datasets, and associated metadata, to facilitate transparency, reproducibility, and proper tracking of machine learning models.")
parser.add_argument("model_id", type=str, help="ID of the Hugging Face machine learning model to create the AIBOM")
parser.add_argument("-o", "--output", type=str, help="Path to save the output file", default=None)
args = parser.parse_args()
modelID = args.model_id

aibom = generateAIBOM(modelID)


if args.output is None:
    path = f"{args.model_id}.json".replace("/", "_")
else:
    path = args.output + f"{args.model_id}.json".replace("/", "_")

# Save the BOM to a JSON file
try:
    with open(path, "w") as f:
        json.dump(aibom, f, indent=4)
        print(f"✅ AIBoM successfully created: {path}")
except Exception as e:
    print(f"❌ Error in AIBoM creation: {e}")
#--------------------------------------------------------------

