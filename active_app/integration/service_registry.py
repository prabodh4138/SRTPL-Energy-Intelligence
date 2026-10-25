class ServiceRegistry:
    def __init__(self):
        self._services = {}

    def register(self, name, service):
        self._services[name] = service

    def get(self, name):
        if name not in self._services:
            raise KeyError(f"Service not registered: {name}")
        return self._services[name]

    def names(self):
        return sorted(self._services)
