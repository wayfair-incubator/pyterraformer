from dataclasses import dataclass
from typing import Optional, List, Dict, ClassVar

from pyterraformer.terraform.backends.base_backend import BaseBackend


@dataclass
class GCSBackend(BaseBackend):
    """Stores the state as an object in a configurable prefix in a pre-existing bucket on Google Cloud Storage (GCS). The bucket must exist prior to configuring the backend."""

    credentials: Optional[str] = None
    impersonate_service_account: Optional[str] = None
    impersonate_service_account_delegations: Optional[List[str]] = None
    access_token: Optional[str] = None
    prefix: Optional[str] = None
    encryption_key: Optional[str] = None

    SECRET_FIELDS: ClassVar = ["encryption_key", "access_token"]

    def generate_environment(self) -> Dict:
        output = {}
        if self.credentials:
            output["GOOGLE_BACKEND_CREDENTIALS"] = self.credentials
            output["GOOGLE_CREDENTIALS"] = self.credentials
        if self.impersonate_service_account:
            output[
                "GOOGLE_IMPERSONATE_SERVICE_ACCOUNT"
            ] = self.impersonate_service_account
        if self.encryption_key:
            output["GOOGLE_ENCRYPTION_KEY"] = self.encryption_key
        return output
