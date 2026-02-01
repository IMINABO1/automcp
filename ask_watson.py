from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai import Credentials

from config import IBM_API_KEY, IBM_PROJECT_ID, IBM_WATSONX_URL, IBM_MODEL_ID

_credentials = Credentials(
    url=IBM_WATSONX_URL,
    api_key=IBM_API_KEY
)

_params = {
    GenParams.MAX_NEW_TOKENS: 500
}

_model = ModelInference(
    model_id=IBM_MODEL_ID,
    credentials=_credentials,
    project_id=IBM_PROJECT_ID,
    params=_params
)

def ask_watson(prompt):
    return _model.generate_text(prompt=prompt)

if __name__ == "__main__":
    print(
        ask_watson("Tell me a fun fact about IBM")
    )
