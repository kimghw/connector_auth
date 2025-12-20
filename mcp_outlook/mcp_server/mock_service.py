"""Mock service for testing"""

class Service:
    """Mock service class for testing"""
    def __init__(self):
        print(f"Mock Service initialized")

    async def initialize(self, user_email=None):
        print(f"Mock Service.initialize() called with {user_email}")

    async def keyword_search(self, **kwargs):
        return {"result": "mock keyword_search"}

    async def mail_list(self, **kwargs):
        return {"result": "mock mail_list"}