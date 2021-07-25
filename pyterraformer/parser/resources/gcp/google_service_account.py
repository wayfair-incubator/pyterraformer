from analytics_terraformer_core.meta_classes import Literal
from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleServiceAccount(ResourceObject):
    _type = "google_service_account"
    REQUIRED_ATTRIBUTES = ["account_id", "display_name", "project"]

    def __init__(self, id, rtype, text, attributes=None):

        ResourceObject.__init__(self, rtype, id, text, attributes)

    def render_iam_binding(self, absolute=False, workspace=None) -> str:
        if not absolute:
            return "serviceAccount:{}".format(self.render_attribute("email"))
        else:
            return f"serviceAccount:{self.resolved_account_id}@{self.project.resolve(workspace=self._file.workspace, file=self._file)}.iam.gserviceaccount.com"

    @property
    def resolved_account_id(self):
        return self.account_id.resolve(workspace=self._file.workspace, file=self._file)

    @property
    def resolved_project(self):
        return self.project.resolve(workspace=self._file.workspace, file=self._file)

    @property
    def import_address(self) -> str:
        return f'projects/{self.project}/serviceAccounts/{self.resolved_account_id}@{self.resolved_project}.iam.gserviceaccount.com'

    @property
    def id_lookup(self) -> Literal:
        return Literal(f"google_service_account.{self.id}.id")

    @property
    def email_lookup(self):
        return Literal(f"google_service_account.{self.id}.email")

    @property
    def name_lookup(self):
        return f"google_service_account.{self.id}.name"

    @property
    def iam_likely_email(self):
        return f"serviceAccount:{self.id}@{self.project.resolve(workspace=self._file.workspace, file=self._file)}.iam.gserviceaccount.com"
