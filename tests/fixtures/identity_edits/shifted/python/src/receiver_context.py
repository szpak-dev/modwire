
class ExampleReceiver:
    example_shared = 1

    @classmethod
    def example_type(cls):
        cls.example_direct_type = 2

        def example_captured():
            cls.example_captured_type = 3

    def example_instance(self):
        self.example_shared = 4
        self.example_shared = 5
        self.example_direct_instance = 6

        def example_captured():
            self.example_captured_instance = 7

        def example_shadowed(self):
            self.example_unknown = 8

        def example_rebound():
            self = example_factory()
            self.example_unknown = 9
