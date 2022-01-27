import hashlib
import io
import os
import uuid

import dramatiq
import flask
import redis
from dramatiq.brokers.redis import RedisBroker
from dramatiq.message import Message

app = flask.Flask(__name__)
app.config['DATA_DIR'] = os.getenv('DATA_DIR')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH'))
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

redis_client = redis.Redis(host='redis', port=6379)
dramatiq_broker = RedisBroker(client=redis_client)
dramatiq.set_broker(dramatiq_broker)
queue_name = os.getenv('DRAMATIQ_QUEUE_NAME')
actor_name = os.getenv('DRAMATIQ_ACTOR_NAME')

DOC_NAMESPACE = os.getenv('DOC_NAMESPACE_STRING')
DOC_IMG_NAMESPACE = os.getenv('DOC_IMG_NAMESPACE_STRING')

DEFAULT_EXPIRATION = int(os.getenv('REDIS_DEFAULT_EXPIRATION'))
IMG_FORMAT = os.getenv('IMG_FORMAT').lower()

ID_METHOD = os.getenv('ID_METHOD')
assert ID_METHOD in ['MD5', 'UUID'], f"ID_METHOD must be (MD5|UUID). Was {ID_METHOD}"


@app.route('/documents', methods=['POST'])
def post_upload_document():

    if len(flask.request.files) != 1:
        flask.abort(400)

    file = next(flask.request.files.values())

    extension = file.filename.split('.')[-1]

    if extension not in app.config['ALLOWED_EXTENSIONS']:
        flask.abort(415)

    data = file.read()
    file.close()

    ID = hashlib.md5(data).hexdigest() if ID_METHOD == 'MD5' else str(uuid.uuid4())

    if not redis_client.exists(ID):

        redis_client.hset(DOC_NAMESPACE.format(ID), mapping={'done': 0})

        message = Message(
            args=[ID, data.hex()],
            actor_name=actor_name,
            queue_name=queue_name,
            kwargs={},
            options={},
        )
        dramatiq_broker.enqueue(message)

    return {"id": ID}


@app.route('/documents/<string:ID>', methods=['GET'])
def get_document(ID):

    status = redis_client.hget(DOC_NAMESPACE.format(ID), 'done')

    if status is not None:

        done = int(status.decode())

        result_dict = {"status": 'done' if done else 'processing'}

        n_pages = redis_client.hget(DOC_NAMESPACE.format(ID), 'n_pages')
        if n_pages is not None:
            result_dict |= {"n_pages": n_pages.decode()}

        return result_dict

    flask.abort(404)


@app.route('/documents/<string:ID>/pages/<int:PAGE_NUMBER>', methods=['GET'])
def get_document_page(ID, PAGE_NUMBER):

    if redis_client.hget(DOC_NAMESPACE.format(ID), 'done') == b'1':

        n_pages = int(redis_client.hget(DOC_NAMESPACE.format(ID), 'n_pages').decode())
        if (PAGE_NUMBER - 1) not in range(n_pages):
            flask.abort(404)

        result = redis_client.get(DOC_IMG_NAMESPACE.format(ID, PAGE_NUMBER - 1))

        if result is not None:
            return flask.send_file(
                io.BytesIO(result),
                attachment_filename=f'{PAGE_NUMBER - 1}.{IMG_FORMAT}',
                mimetype=f'image/{IMG_FORMAT}',
            )

        path = os.path.join(app.config['DATA_DIR'], ID, f'{PAGE_NUMBER - 1}.{IMG_FORMAT}')

        if not os.path.exists(path):
            flask.abort(500)  # data corrupted

        with open(path, 'rb') as f:
            bytes_data = f.read()

        redis_client.setex(
            DOC_IMG_NAMESPACE.format(ID, PAGE_NUMBER - 1), DEFAULT_EXPIRATION, bytes_data
        )
        return flask.send_file(path)

    flask.abort(404)


if __name__ == "__main__":
    # run flask test server
    app.run(host='127.0.0.1', port=8000, debug=True)
