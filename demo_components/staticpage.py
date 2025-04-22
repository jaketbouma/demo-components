# Copyright 2016-2021, Pulumi Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import Optional

from pulumi import Inputs, ResourceOptions
from pulumi_aws import s3
import pulumi


class StaticPageArgs:

    index_content: pulumi.Input[str]
    """The HTML content for index.html."""

    @staticmethod
    def from_inputs(inputs: Inputs) -> 'StaticPageArgs':
        return StaticPageArgs(index_content=inputs['indexContent'])

    def __init__(self, index_content: pulumi.Input[str]) -> None:
        self.index_content = index_content


class StaticPage(pulumi.ComponentResource):
    bucket: s3.BucketV2
    index_object: s3.BucketObject
    website_url: pulumi.Output[str]

    def __init__(self,
                 name: str,
                 args: StaticPageArgs,
                 props: Optional[dict] = None,
                 opts: Optional[ResourceOptions] = None) -> None:

        super().__init__('shopkeeper:index:StaticPage', name, props, opts)

        # Create a bucket and expose a website index document.
        self.bucket = s3.BucketV2(
            f'{name}-bucket',
            bucket_prefix=f'{name}',
            force_destroy=True,
            opts=ResourceOptions(parent=self)
        )

        bucket_website_configuration = s3.BucketWebsiteConfigurationV2(
            f'{name}-BucketWebsiteConfigurationV2',
            bucket=self.bucket,
            index_document='index.html',
            opts=ResourceOptions(parent=self.bucket)
        )

        # Create a bucket policy
        bucket_ownership_controls = s3.BucketOwnershipControls(
            f"{name}-BucketOwnershipControls",
            bucket=self.bucket.bucket,
            rule={
                "object_ownership": "BucketOwnerPreferred",
            },
            opts=ResourceOptions(parent=self.bucket)
        )
        bucket_public_access_block = s3.BucketPublicAccessBlock(
            f"{name}-BucketPublicAccessBlock",
            bucket=self.bucket.bucket,
            block_public_acls=False,
            block_public_policy=False,
            ignore_public_acls=False,
            restrict_public_buckets=False,
            opts=ResourceOptions(parent=self.bucket)
        )
        bucket_acl_v2 = s3.BucketAclV2(
            f"{name}-BucketAclV2",
            bucket=self.bucket.bucket,
            acl="public-read",
            opts = ResourceOptions(
                depends_on=[
                    bucket_ownership_controls,
                    bucket_public_access_block,
                ],
                parent=self.bucket
            )
        )

        # Create a bucket object for the index document.
        self.index_object = s3.BucketObject(
            f'{name}-index-object',
            bucket=self.bucket.bucket,
            key='index.html',
            content=args.index_content,
            content_type='text/html',
            opts=ResourceOptions(parent=self.bucket))

        # Set the access policy for the bucket so all objects are readable.
        s3.BucketPolicy(
            f'{name}-bucket-policy',
            bucket=self.bucket.bucket,
            policy=self.bucket.bucket.apply(_allow_getobject_policy),
            opts=ResourceOptions(parent=self.bucket)
        )

        self.website_url = bucket_website_configuration.website_endpoint

        self.register_outputs({
            'bucket': self.bucket,
            'website_url': self.bucket.website_endpoint,
            'index_object': self.index_object
        })


def _allow_getobject_policy(bucket_name: str) -> str:
    return json.dumps({
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': [
                    f'arn:aws:s3:::{bucket_name}/*',  # policy refers to bucket name explicitly
                ],
            },
        ],
    })
