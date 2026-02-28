#!/bin/sh

tar -cpvzf $SERVER_BACKUP minecraft
aws s3 cp $SERVER_BACKUP s3://$S3_BUCKET_NAME $@