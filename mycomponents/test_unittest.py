import logging
import unittest

import pulumi

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
sp = StaticPage("test", StaticPageArgs(index_content=mock_content))


class TestingWithMocks(unittest.TestCase):

    @pulumi.runtime.test
    def test_static_page_bucket(self):
        """
        Getting to know unit testing pulumi component resources with python
        """

        def test_bucket(args):
            index_content = args[0]
            logger.info(f"test_bucket: '{sp._name}' with args={args}")
            assert index_content == mock_content
            assert 1 == 1
            return 1

        # BUG: for some reason, pytest hangs sporadically when we use named arguments to pulumi.Output.all!? This took some hunting.
        return pulumi.Output.all(sp.index_content).apply(test_bucket)
