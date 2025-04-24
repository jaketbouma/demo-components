import logging

import pulumi

# import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Setting mocks")


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


pulumi.runtime.set_mocks(
    MyMocks(),
    preview=False,  # Sets the flag `dry_run`, which is true at runtime during a preview.
)

logger.info("Mocks set")


from mycomponents.staticpage import StaticPage, StaticPageArgs

mock_content = "<h1>Ollo</h1>"
sp = StaticPage("test", StaticPageArgs(index_content=mock_content))

# @pytest.fixture
# def example_static_page():
#    logger.info("Creating fixture test")
#    sp = StaticPage("test", StaticPageArgs(index_content=mock_content))
#    logger.info("Done")
#    return sp


@pulumi.runtime.test
def test_static_page_bucket():
    """
    Getting to know unit testing pulumi component resources with python
    """

    def test_bucket(args):
        urn, index_content = args
        logger.info(f"test_bucket: '{sp._name}' with args={args}")
        assert index_content == mock_content

    # BUG: for some reason, pytest hangs sporadically when we use named arguments to pulumi.Output.all!? This took some hunting.
    return pulumi.Output.all(sp.urn, sp.index_content).apply(test_bucket)


# @pulumi.runtime.test
# def test_static_page_content_object(example_static_page):
#    def test_content_object(args):
#        logger.info(f"test_content: '{example_static_page._name}' with args={args}")
#        assert args["content"] == mock_content
#
#    return pulumi.Output.all(
#        content = example_static_page.index_object.content
#    ).apply(test_content_object)
