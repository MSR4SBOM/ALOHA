# ALOHA: A(IBoM) tooL generatOr from Hugging fAce

ALOHA (AI Bill of Materials) is a Python tool designed to generate an **AI Bill of Materials (AIBOM)** for machine learning models hosted on the **Hugging Face** platform. It extracts relevant model information and outputs a JSON file compliant with the **[CycloneDX ](https://cyclonedx.org/)v1.6** standard.


## Features
- Retrieves model information from Hugging Face model cards.
- Generates an AIBOM in **JSON format**, following the **CycloneDX standard**.
- Helps improve transparency and traceability in the AI supply chain.

## Installation
To install the required dependencies, make sure Python >= 3.10.2 is installed, then run:

```sh
pip install -r requirements.txt
```


## Usage
To generate an AIBOM for a Hugging Face model, run:
```sh
python ALOHA.py <model_ID> -o <output_dir_path>
```
- **<model_ID>**: The model ID from Hugging Face in the format author/model. This is a required parameter and must correspond to a valid model identifier.
- **<output_dir_path>**: Specifies the destination directory where the output files will be saved. This is an optional parameter; if not provided, the tool will use a default directory.

### Example
```sh
python ALOHA.py bigcode/starpii
```
This will produce a JSON file containing the AIBOM for the specified model.

## Output Format
The generated AIBOM follows the **CycloneDX** standard (**[CycloneDX 1.6 JSON Schema](https://cyclonedx.org/docs/1.6/json/)**) and includes:
- **`bomFormat` & `specVersion`**: Defines the BOM format and CycloneDX specification version.
- **`serialNumber` & `version`**: Unique identifiers for the AIBOM instance.
- **`metadata`**: Includes the timestamp of generation and model-related details.
- **`components`**: Contains information about the dataset(s) used to train/test the machine learning model, if specified by the model's author.
- **`externalReferences`**: Provides links to the model's official documentation on Hugging Face.
- **`properties`**: Stores additional metadata not natively supported by CycloneDX.

Further details about these main fields and subfields can be found here **[documentation](https://github.com/MSR4SBOM/ALOHA/blob/main/documentation.json)**.

## Example JSON output:
```json
{
    "bomFormat": "CycloneDX",
    "specVersion": "1.6",
    "serialNumber": "urn:uuid:421fccc0-305e-4541-bc3d-cdc05a46c313",
    "version": 1,
    "metadata": {
        "timestamp": "2025-06-04T17:20:24.648647+00:00",
        "component": {
            "type": "machine-learning-model",
            "bom-ref": "bigcode/starpii-4e7675e7-7b30-5eb5-862d-d1fbf9b4ba8f",
            "name": "bigcode/starpii",
            "externalReferences": [
                {
                    "url": "https://huggingface.co/bigcode/starpii",
                    "type": "documentation"
                }
            ],
            "modelCard": {
                "modelParameters": {
                    "task": "token-classification",
                    "architectureFamily": "bert",
                    "modelArchitecture": "BertForTokenClassification",
                    "datasets": [
                        {
                            "ref": "bigcode/pii-annotated-toloka-donwsample-emails-cdd64174-148d-5284-a37c-504412b8f3b4"
                        },
                        {
                            "ref": "bigcode/pseudo-labeled-python-data-pii-detection-filtered-75f77736-2796-536b-b7c3-7a350d034fe4"
                        }
                    ]
                },
                "properties": [
                    {
                        "name": "library_name",
                        "value": "transformers"
                    }
                ]
            },
            "authors": [
                {
                    "name": "bigcode"
                }
            ],
            "tags": [
                "transformers",
                "pytorch",
                "bert",
                "token-classification",
                "code",
                "dataset:bigcode/pii-annotated-toloka-donwsample-emails",
                "dataset:bigcode/pseudo-labeled-python-data-pii-detection-filtered",
                "arxiv:2301.03988",
                "autotrain_compatible",
                "endpoints_compatible",
                "region:us"
            ]
        }
    },
    "components": [
        {
            "type": "data",
            "bom-ref": "bigcode/pii-annotated-toloka-donwsample-emails-cdd64174-148d-5284-a37c-504412b8f3b4",
            "name": "bigcode/pii-annotated-toloka-donwsample-emails",
            "data": [
                {
                    "type": "dataset",
                    "bom-ref": "bigcode/pii-annotated-toloka-donwsample-emails-cdd64174-148d-5284-a37c-504412b8f3b4",
                    "name": "bigcode/pii-annotated-toloka-donwsample-emails",
                    "contents": {
                        "url": "https://huggingface.co/datasets/bigcode/pii-annotated-toloka-donwsample-emails",
                        "properties": [
                            {
                                "name": "task_categories",
                                "value": "token-classification"
                            },
                            {
                                "name": "language",
                                "value": "code"
                            }
                        ]
                    },
                    "governance": {
                        "owners": [
                            {
                                "organization": {
                                    "name": "bigcode",
                                    "url": "https://huggingface.co/bigcode"
                                }
                            }
                        ]
                    },
                    "description": "\n\t\n\t\t\n\t\tPII dataset\n\t\n\n\n\t\n\t\t\n\t\tDataset description\n\t\n\nThis is an annotated dataset for Personal Identifiable Information (PII) in code. The target entities are: Names, Usernames, Emails, IP addresses, Keys, Passwords, and IDs. \nThe annotation process involved 1,399 crowd-workers from 35 countries with Toloka. \nIt consists of 12,099 samples of\n~50 lines of code in 31 programming languages. You can also find a PII detection model that we trained on this dataset at bigcode-pii-model.\u2026 See the full description on the dataset page: https://huggingface.co/datasets/bigcode/bigcode-pii-dataset."
                }
            ]
        },
        {
            "type": "data",
            "bom-ref": "bigcode/pseudo-labeled-python-data-pii-detection-filtered-75f77736-2796-536b-b7c3-7a350d034fe4",
            "name": "bigcode/pseudo-labeled-python-data-pii-detection-filtered",
            "data": [
                {
                    "type": "dataset",
                    "bom-ref": "bigcode/pseudo-labeled-python-data-pii-detection-filtered-75f77736-2796-536b-b7c3-7a350d034fe4",
                    "name": "bigcode/pseudo-labeled-python-data-pii-detection-filtered",
                    "contents": {
                        "url": "https://huggingface.co/datasets/bigcode/pseudo-labeled-python-data-pii-detection-filtered"
                    },
                    "governance": {
                        "owners": [
                            {
                                "organization": {
                                    "name": "bigcode",
                                    "url": "https://huggingface.co/bigcode"
                                }
                            }
                        ]
                    },
                    "description": "\n\t\n\t\t\n\t\tPseudo-labeled-python-data-pii-detection-filtered\n\t\n\nThis dataset was used for the training of a PII detection NER model. We annotated it using pseudo-labelelling to enhance model performance on some rare PII entities like keys.\nIt consists of 18,000 files annotates using an ensemble of two encoder models Deberta-v3-large and stanford-deidentifier-base which were fine-tuned on a labeled PII dataset for code with 400 files from this work. To select good-quality pseudo-labels, \nwe\u2026 See the full description on the dataset page: https://huggingface.co/datasets/bigcode/pseudo-labeled-python-data-pii-detection-filtered."
                }
            ]
        }
    ]
}
```

## License
This project is licensed under **Mozilla Public License 2.0 License**.
