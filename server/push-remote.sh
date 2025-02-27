#!/bin/bash

AWS_PROFILE_LOCAL="mcserver-dev" # or 'default' profile

source build/.env
export S3_BUCKET_NAME=$S3_BUCKET_NAME
export SERVER_BACKUP=$SERVER_BACKUP

INSTALL_PKG="install.tar.gz"
./scripts/save-mcserver.sh --profile $AWS_PROFILE_LOCAL

tar -cpvzf $INSTALL_PKG build scripts service
aws s3 cp $INSTALL_PKG s3://ec2-mc-server/$INSTALL_PKG --profile $AWS_PROFILE_LOCAL

rm $INSTALL_PKG $SERVER_BACKUP