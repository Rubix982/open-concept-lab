# Set your API key
from nnsight import CONFIG

CONFIG.set_default_api_key("91ec1040-feab-4b6f-b1cf-77dc3812ca24")

from nnsight.modeling.language import LanguageModel

model = LanguageModel("meta-llama/Llama-3.1-8B")

import logging
logging.basicConfig(level=logging.DEBUG)

with model.trace("The Eiffel Tower is in the city of", remote=True):
    output = model.output.save()
