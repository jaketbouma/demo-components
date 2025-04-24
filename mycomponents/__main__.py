from pulumi.provider.experimental import component_provider_host

from mycomponents.staticpage import StaticPage

if __name__ == "__main__":
    component_provider_host(name="mycomponents", components=[StaticPage])
