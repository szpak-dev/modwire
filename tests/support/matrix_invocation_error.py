class MatrixInvocationError(Exception):
    def __init__(self, argument_count: int) -> None:
        super().__init__(f"Extraction matrix requires ROOT OUTPUT; received {argument_count} arguments.")
