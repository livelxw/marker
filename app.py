import os
import tempfile
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI

from marker.convert import convert_single_pdf
from marker.models import load_all_models

app = FastAPI()


def pdf_to_md(langs: list[str], content: bytes, start_page: int = 0, max_pages: int = 10, batch_multiplier: int = 2):
    with tempfile.NamedTemporaryFile() as tmp:
        try:
            tmp.write(content)
            model_lst = load_all_models()
            full_text, images, out_meta = convert_single_pdf(
                tmp.name,
                model_lst,
                max_pages=max_pages,
                langs=langs,
                batch_multiplier=batch_multiplier,
                start_page=start_page
            )
            return {'full_text': full_text, 'images': images, 'out_meta': out_meta}

        finally:
            tmp.close()
            os.unlink(tmp.name)


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
        text = pdf_to_md(instance.content).get('full_text', '')
        predictions = predictions.append(Prediction(text=text))
    return PredictResponse(predictions=predictions)


@app.get('/health')
async def health():
    return {}


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', access_log=False)
