## Execution

To run the service, use docker-compose:
```
mkdir data
docker-compose build
docker-compose up
```

## Example conversion:

Upload document:

`curl -F "data=@test/in.pdf" -X POST 127.0.0.1/documents`

Check document status:

`curl 127.0.0.1/documents/<ID>`

Get converted document page:

`curl 127.0.0.1/documents/<ID>/pages/<PAGE> -o <PAGE>.png`


## Implementation Details

### Redis

Due to the simplicity of use and good performance, I have opted for Redis as the messaging queue and cache. Redis could have also been used as the database, but assuming limited RAM, I have decided to use it only as an LFU cache. However, the database approach would, simplify the code, improve the performance, and prevent the use of host volumes. A solution to the RAM problem could be "Redis on Flash", which is, unfortunately, an enterprise solution.

Redis restricts the size of its inputs to 512MB. This is why I have also restricted the size of uploads to approximately 200MB (adequate for regular use), as dramatiq forces the use of JSON in messaging, and therefore the byte-content of PDF files has to be stored as a hexdump with double memory footprint. An alternative would be to reimplement the dramatiq messaging schema.

### File Indexing

I decided to index the received documents using MD5 hash of its contents. This way, the system does not have to recompute identical documents. Attackers might be able to check whether a specific document has already been uploaded, however in my opinion, this is a negligible problem, and therefore the benefits of not having to recompute the image again outweigh any risks.

During testing, one might prefer to use UUID for indexing as it generates a unique ID without the need for generating unique pdf documents. In that case, run:

`docker-compose --env-file .locust.env up`

### Page Count While Processing

I have decided against displaying the number of pages of the input document while the document is being processed. This would require an additional read from disk since the main utility (`poppler`) works only over files. On the other hand, if we wanted to show the count nonetheless, a simple call to `pdf2image.pdfinfo_from_bytes` would suffice.


## Future Work

- [ ] Tests (simple load tests are included, coverage is missing)
- [ ] Logging
