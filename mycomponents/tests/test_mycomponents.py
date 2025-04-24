import logging
import pytest
import pulumi
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mock_content = "<h1>Example!</h1>"


@pytest.fixture
def example_static_page():
    """
        inspired by https://github.com/pulumi/pulumi/blob/da70a80fcfd37b8b32fc736a167ca15173bbb00d/sdk/python/lib/test_with_mocks/test_testing_with_mocks.py#L173
    """
    loop = asyncio.get_event_loop()
    loop.set_default_executor(ImmediateExecutor())

    old_settings = pulumi.runtime.settings.SETTINGS
    try:
        pulumi.runtime.mocks.set_mocks(MyMocks())
        from mycomponents.staticpage import StaticPage, StaticPageArgs

        yield StaticPage("test", StaticPageArgs(index_content=mock_content))
    finally:
        logger.debug("cleaning up staticpage fixture")
        pulumi.runtime.settings.configure(old_settings)
        loop.set_default_executor(ThreadPoolExecutor())


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        if args.typ == "mycomponents:index:StaticPage":
            outputs = dict(args.inputs, website_url="http://example.com")
            logger.info(outputs)
            return [args.name + "_id", outputs]
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return ["", {}]


class ImmediateExecutor(ThreadPoolExecutor):
    """This removes multithreading from current tests. Unfortunately in
    presence of multithreading the tests are flaky. The proper fix is
    postponed - see https://github.com/pulumi/pulumi/issues/7663

    * from https://github.com/pulumi/pulumi/blob/da70a80fcfd37b8b32fc736a167ca15173bbb00d/sdk/python/lib/test_with_mocks/test_testing_with_mocks.py#L173
    """

    def __init__(self):
        super()
        self._default_executor = ThreadPoolExecutor()

    def submit(self, fn, *args, **kwargs):
        v = fn(*args, **kwargs)
        return self._default_executor.submit(ImmediateExecutor._identity, v)

    def map(self, func, *iterables, timeout=None, chunksize=1):
        raise Exception("map not implemented")

    def shutdown(self, wait=True, cancel_futures=False):
        raise Exception("shutdown not implemented")

    @staticmethod
    def _identity(x):
        return x


@pulumi.runtime.test
def test_static_page(example_static_page):
    """
    Getting to know unit testing pulumi component resources with python
    """

    def test_bucket(args):
        urn, index_content, website_url = args
        logger.info(f"test_bucket: '{example_static_page._name}' with args={args}")
        assert index_content == mock_content
        assert 1 == 1

    # BUG: for some reason, pytest hangs sporadically when we use named arguments to pulumi.Output.all!? This took some hunting.
    return pulumi.Output.all(
        example_static_page.urn,
        example_static_page.index_content,
        example_static_page.website_url,
    ).apply(test_bucket)
