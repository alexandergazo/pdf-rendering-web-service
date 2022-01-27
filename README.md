### Execution

To run the service use docker-compose:
```
mkdir data
docker-compose build
dokcer-compose up
```

### Example conversion:

Upload document:

`curl -F "data=@test/in.pdf" -X POST 127.0.0.1/documents`

Check document status:

`curl 127.0.0.1/documents/<ID>`

Get converted document page:

`curl 127.0.0.1/documents/<ID>/pages/<PAGE> -o <PAGE>.png`


### Implementation Details

#### Redis

Due to the simplicity of use and good performance I have opted for Redis as the messaging queue and cache. Redis could have also been used as the database, but assuming we have only limited RAM I have decided to use it only as a LFU cache. The database approach would, however, simplify the code, improve the performance, and avoid the use of host volumes. As a solution to the RAM problem would be Redis on Flash, which is unfortunately an enterprise solution.

Redis restricts the size of its inputs to 512MB. This is the reason why I have also restricted the size of uploads to approximately 200MB (adequate for normal use), as dramatiq forces the use of JSON in messaging and therefore the byte-content of PDF files has to be stored as hash with double memory footprint. Alternative would be to reimplement the dramatiq messaging schema.

#### File Indexing

I decided to index the file using MD5 hash of its contents. This might lead to attackers being able to check whether specific document was already uploaded, but in my opinion this is a negligible problem, and therefore the benefits of not having to recompute the image again outweight any risks.

During testing one might use UUID for indexing as it generates unique index without the need for generating unique pdf documents. In that case run:

`docker-compose --env-file .locust.env up`

#### Page Count While Processing

I have decided against displaying the number of pages of the input document while the document is being processed, because this would require an additional read from disk, since the main utility (`poppler`) works only over files. On the other hand, if we wanted to show the count anyway, simple call to `pdf2image.pdfinfo_from_bytes` would suffice.


### Future Work

- [  ] Tests (simple load tests are included, coverage is missing)
- [  ] Logging
