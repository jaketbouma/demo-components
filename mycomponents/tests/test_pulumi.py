import pulumi
import logging
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


pulumi.runtime.set_mocks(
    MyMocks(),
    preview=False,  # Sets the flag `dry_run`, which is true at runtime during a preview.
)


from mycomponents.staticpage import StaticPage, StaticPageArgs

mock_content = "<h1>Ollo</h1>"

@pytest.fixture
def example_static_page():
    return StaticPage("test", StaticPageArgs(index_content=mock_content))


@pulumi.runtime.test
def test_static_page_bucket(example_static_page):
    """
    Getting to know unit testing pulumi component resources with python
    """
    def test_bucket(args):
        logger.info(f"test_bucket: '{example_static_page._name}' with args={args}")
        assert args["bucket_prefix"] == "test"
        assert args["bucket_id"].startswith("test-")
        assert args["force_destroy"] == True

    return pulumi.Output.all(
        bucket_prefix=example_static_page.bucket.bucket_prefix,
        bucket_id = example_static_page.bucket.id,
        force_destroy = example_static_page.bucket.force_destroy
    ).apply(test_bucket)


@pulumi.runtime.test
def test_static_page_content_object(example_static_page):   
    def test_content_object(args):
        logger.info(f"test_content: '{example_static_page._name}' with args={args}")
        assert args["content"] == mock_content
    
    return pulumi.Output.all(
        content = example_static_page.index_object.content
    ).apply(test_content_object)