from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from .document_controller import DocumentOperationController

api_v1 = NinjaExtraAPI(
    version="1.0.0",
    openapi_extra={
        "components": {
            "securitySchemes": {
                "Bearer": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        },
        "security": [{"Bearer": []}],
    },
)

api_v1.register_controllers(
    NinjaJWTDefaultController,
    DocumentOperationController,
)