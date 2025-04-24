import json
from typing import Optional, TypedDict

import pulumi
from pulumi import Inputs, ResourceOptions
from pulumi_aws import s3


class StaticPageArgs(TypedDict):
    index_content: pulumi.Input[str]
    """The HTML content for index.html."""


class StaticPage(pulumi.ComponentResource):
    website_url: pulumi.Output[str]

    def __init__(
        self, name: str, args: StaticPageArgs, opts: Optional[ResourceOptions] = None
    ) -> None:

        super().__init__("mycomponents:index:StaticPage", name, args, opts)

        # Create a bucket and expose a website index document.
        bucket = s3.BucketV2(
            f"{name}bucket",
            bucket_prefix=f"{name}",
            force_destroy=True,
            opts=ResourceOptions(parent=self),
        )

        bucket_website_configuration = s3.BucketWebsiteConfigurationV2(
            f"{name}-BucketWebsiteConfigurationV2",
            bucket=bucket,
            index_document={
                "suffix": "index.html",
            },
            opts=ResourceOptions(parent=bucket),
        )

        # Create a bucket policy
        bucket_ownership_controls = s3.BucketOwnershipControls(
            f"{name}-BucketOwnershipControls",
            bucket=bucket.bucket,
            rule={
                "object_ownership": "BucketOwnerPreferred",
            },
            opts=ResourceOptions(parent=bucket),
        )
        bucket_public_access_block = s3.BucketPublicAccessBlock(
            f"{name}-BucketPublicAccessBlock",
            bucket=bucket.bucket,
            block_public_acls=False,
            block_public_policy=False,
            ignore_public_acls=False,
            restrict_public_buckets=False,
            opts=ResourceOptions(parent=bucket),
        )
        bucket_acl_v2 = s3.BucketAclV2(
            f"{name}-BucketAclV2",
            bucket=bucket.bucket,
            acl="public-read",
            opts=ResourceOptions(
                depends_on=[
                    bucket_ownership_controls,
                    bucket_public_access_block,
                ],
                parent=bucket,
            ),
        )

        # Create a bucket object for the index document.
        index_object = s3.BucketObject(
            f"{name}-index-object",
            bucket=bucket.bucket,
            key="index.html",
            content=args.get("index_content"),
            content_type="text/html",
            opts=ResourceOptions(parent=bucket),
        )

        # Set the access policy for the bucket so all objects are readable.
        s3.BucketPolicy(
            f"{name}-bucket-policy",
            bucket=bucket.bucket,
            policy=bucket.bucket.apply(_allow_getobject_policy),
            opts=ResourceOptions(parent=bucket),
        )

        self.website_url = bucket_website_configuration.website_endpoint

        self.register_outputs({"website_url": self.website_url, "bucket": bucket})


def _allow_getobject_policy(bucket_name: str) -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}/*",  # policy refers to bucket name explicitly
                    ],
                },
            ],
        }
    )
