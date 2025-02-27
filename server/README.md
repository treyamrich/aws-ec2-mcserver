# TO DO Items

### AWS Launch Template
- Assign proper IAM role to the instance. Required permissions: r/w to s3 bucket, and terminate spot instance
- Add the resource tag "Name" = "mcserver" for the key/value pair
- Select desired instance criteria for launch
- Set shutdown behavior to terminate (unless you are using EBS)
- Recommended: Set a max spot instance price. Do not make it too low, otherwise the server will be interrupted more frequently.
- Make sure correct aws launch template name is set for discord bot's config.ini