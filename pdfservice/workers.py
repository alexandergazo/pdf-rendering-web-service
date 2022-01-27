import io
import os

import dramatiq
import pdf2image
import redis
from dramatiq.brokers.redis import RedisBroker
from PIL import Image

redis_client = redis.Redis(host='redis', port=6379)

broker = RedisBroker(client=redis_client)
dramatiq.set_broker(broker)
queue_name = os.getenv('DRAMATIQ_QUEUE_NAME')
actor_name = os.getenv('DRAMATIQ_ACTOR_NAME')
DOC_NAMESPACE = os.getenv('DOC_NAMESPACE_STRING')
DOC_IMG_NAMESPACE = os.getenv('DOC_IMG_NAMESPACE_STRING')

DATA_DIR = os.getenv('DATA_DIR')
IMG_FORMAT = os.getenv('IMG_FORMAT').lower()
MAX_WIDTH = int(os.getenv('MAX_IMG_WIDTH'))
MAX_HEIGHT = int(os.getenv('MAX_IMG_WEIGHT'))
DEFAULT_EXPIRATION = int(os.getenv('REDIS_DEFAULT_EXPIRATION'))


@dramatiq.actor(actor_name=actor_name, queue_name=queue_name)
def render_pdf(ID: str, hex_data: str):

    basename = f"/{DATA_DIR}/{ID}"
    os.makedirs(basename, exist_ok=True)

    bytes_data = bytes.fromhex(hex_data)
    images = pdf2image.convert_from_bytes(bytes_data)

    for i, img in enumerate(images):
        ratio = min(MAX_WIDTH / img.width, MAX_HEIGHT / img.height)
        img = img.resize((round(img.width * ratio), round(img.height * ratio)), Image.BILINEAR)

        path = os.path.join(basename, f'{i}.{IMG_FORMAT}')
        img.save(path, IMG_FORMAT)

        img_bytes = io.BytesIO()
        img.save(img_bytes, IMG_FORMAT)

        # cache
        redis_client.setex(
            DOC_IMG_NAMESPACE.format(ID, i), DEFAULT_EXPIRATION, img_bytes.getvalue()
        )

    redis_client.hset(DOC_NAMESPACE.format(ID), mapping={'done': 1, 'n_pages': len(images)})
