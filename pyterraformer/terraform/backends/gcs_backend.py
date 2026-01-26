from dataclasses import dataclass
from typing import ClassVar, Dict, List, Optional

from pyterraformer.terraform.backends.base_backend import BaseBackend


@dataclass
class GCSBackend(BaseBackend):
    """Stores the state as an object in a configurable prefix in a pre-existing bucket on Google Cloud Storage (GCS). The bucket must exist prior to configuring the backend."""

    credentials: str | None = None
    impersonate_service_account: str | None = None
    impersonate_service_account_delegations: list[str] | None = None
    access_token: str | None = None
    prefix: str | None = None
    encryption_key: str | None = None

    SECRET_FIELDS: ClassVar = ["encryption_key", "access_token"]

    def generate_environment(self) -> dict:
        output = {}
        if self.credentials:
            output["GOOGLE_BACKEND_CREDENTIALS"] = self.credentials
            output["GOOGLE_CREDENTIALS"] = self.credentials
        if self.impersonate_service_account:
            output["GOOGLE_IMPERSONATE_SERVICE_ACCOUNT"] = self.impersonate_service_account
        if self.encryption_key:
            output["GOOGLE_ENCRYPTION_KEY"] = self.encryption_key
        return output
