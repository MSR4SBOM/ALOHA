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
python ALOHA.py facebook/bart-large
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
    "serialNumber": "urn:uuid:c11ff07a-64b8-4944-8317-c2b7d41632b6",
    "version": 1,
    "metadata": {
        "timestamp": "2025-03-19T20:48:08.493691+00:00",
        "component": {
            "type": "machine-learning-model",
            "bom-ref": "facebook/bart-large-2c308c2e-6643-55f4-8588-42fb9fc394cd",
            "licenses": [
                {
                    "license": {
                        "id": "Apache-2.0",
                        "url": "https://spdx.org/licenses/Apache-2.0.html"
                    }
                }
            ],
            "externalReferences": [
                {
                    "url": "https://huggingface.co/facebook/bart-large",
                    "type": "documentation"
                }
            ],
            "modelCard": {
                "modelParameters": {
                    "datasets": [],
                    "task": "feature-extraction",
                    "architectureFamily": "bart",
                    "modelArchitecture": "BartModel"
                },
                "properties": [
                    {
                        "name": "library_name",
                        "value": "transformers"
                    }
                ],
                "consideration": {
                    "useCases": "## Intended uses & limitations\n\nYou can use the raw model for text infilling. However, the model is mostly meant to be fine-tuned on a supervised dataset. See the [model hub](https://huggingface.co/models?search=bart) to look for fine-tuned versions on a task that interests you.\n"
                }
            },
            "name": "facebook/bart-large",
            "authors": [
                {
                    "name": "facebook"
                }
            ],
            "description": "## Model description\n\nBART is a transformer encoder-decoder (seq2seq) model with a bidirectional (BERT-like) encoder and an autoregressive (GPT-like) decoder. BART is pre-trained by (1) corrupting text with an arbitrary noising function, and (2) learning a model to reconstruct the original text.\n\nBART is particularly effective when fine-tuned for text generation (e.g. summarization, translation) but also works well for comprehension tasks (e.g. text classification, question answering).\n",
            "tags": [
                "transformers",
                "pytorch",
                "tf",
                "jax",
                "rust",
                "bart",
                "feature-extraction",
                "en",
                "arxiv:1910.13461",
                "license:apache-2.0",
                "endpoints_compatible",
                "region:us"
            ]
        }
    },
    "components": []
}
```

## License
This project is licensed under **Mozilla Public License 2.0 License**.
