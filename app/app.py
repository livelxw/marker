import base64
import os
from dataclasses import dataclass
from typing import Optional

import uvicorn
from fastapi import FastAPI

from marker.convert import convert_single_pdf
from marker.models import load_all_models

app = FastAPI()

model_lst = load_all_models()
TEMP_PATH = 'tmp'


def pdf_to_md(
        content: bytes,
        langs: Optional[list[str]] = None,
        start_page: int = 0,
        max_pages: int = 10,
        batch_multiplier: int = 2
):
    if not os.path.exists(TEMP_PATH):
        os.mkdir(TEMP_PATH)
    tmp_file_path = os.path.join(TEMP_PATH, os.urandom(24).hex())
    with open(tmp_file_path, 'wb') as tmp:
        tmp.write(content)
        full_text, images, out_meta = convert_single_pdf(
            tmp.name,
            model_lst,
            max_pages=max_pages,
            langs=langs,
            batch_multiplier=batch_multiplier,
            start_page=start_page
        )
    if os.path.exists(tmp_file_path):
        try:
            os.remove(tmp_file_path)
        except:
            pass
    return {'full_text': full_text, 'images': images, 'out_meta': out_meta}


@dataclass
class Instance:
    content: str


@dataclass
class Prediction:
    text: str


@dataclass
class PredictRequest:
    instances: list[Instance]


@dataclass
class PredictResponse:
    predictions: list[Prediction]


@app.post('/predict')
async def predict(request: PredictRequest):
    predictions = []
    for instance in request.instances:
        base64_bytes = base64.b64decode(instance.content)
        text = pdf_to_md(content=base64_bytes).get('full_text', '')
        predictions.append(Prediction(text=text))
    return PredictResponse(predictions=predictions)


@app.get('/health')
async def health():
    return {}


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', access_log=False)
