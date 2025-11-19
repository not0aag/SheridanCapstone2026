{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::safedrive-videos-dev-neil",
        "arn:aws:s3:::safedrive-videos-dev-neil/*"
      ]
    }
  ]
}
````

### 3. Never Commit Credentials

Add to `.gitignore`:
````
.env
*.pem
*.key
aws_credentials.csv
````

---

## Current Development Setup (Local Storage)

**Location:** `./videos/` folder in backend directory

**Structure:**
````
backend/
├── videos/              ← Local storage (gitignored)
│   ├── incidents/
│   │   ├── incident_1.mp4
│   ├── raw/
````

**Switching to S3:**
- Change `USE_S3 = True` in config
- Code automatically uses S3 instead of local storage
- No other changes needed!

---

## Cost Estimates (AWS Free Tier)

**Free Tier (First 12 months):**
- 5 GB S3 Standard storage
- 20,000 GET requests
- 2,000 PUT requests

**After Free Tier:**
- $0.023 per GB/month (Standard)
- $0.0004 per 1,000 PUT requests
- $0.0004 per 1,000 GET requests

**Example Cost:**
- 100 GB storage = ~$2.30/month
- 10,000 videos uploaded = ~$0.40
- **Total:** ~$3/month for moderate usage

---

## Next Steps

1. ✅ Code is ready and tested with local storage
2. ⏳ Wait for AWS account verification
3. ⏳ Create S3 bucket when ready
4. ⏳ Create IAM user and get credentials
5. ⏳ Update .env file
6. ✅ Switch USE_S3 to True
7. ✅ Deploy!

---

## Troubleshooting

### Error: "AccessDenied"
- Check IAM user has S3 permissions
- Verify bucket name is correct
- Check AWS credentials in .env

### Error: "NoSuchBucket"
- Bucket name might be wrong
- Bucket might be in different region
- Check `AWS_REGION` in config

### Error: "CredentialsNotFound"
- `.env` file not loaded
- Check environment variables
- Restart server after updating .env

---

## References

- AWS S3 Documentation: https://docs.aws.amazon.com/s3/
- Boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- S3 Pricing: https://aws.amazon.com/s3/pricing/
````
