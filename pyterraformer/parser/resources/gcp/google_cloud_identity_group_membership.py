from pyterraformer.parser.resources.resource_object import ResourceObject
from typing import Optional
"""'resource "google_cloud_identity_group_membership" "wf-gcp-ae-svc_ML-Dataproc-Accounts_members" {
  for_each = toset(var.wf-gcp-ae-svc_ML-Dataproc-Accounts_members)
  group = var.wf-gcp-ae-svc_ML-Dataproc-Accounts_group_id

  preferred_member_key {
    id = each.key
  }

  roles {
    name = "MEMBER"
  }
}
"""


class GoogleCloudIdentityGroupMembership(ResourceObject):
    _type = "google_cloud_identity_group_membership"
    REQUIRED_ATTRIBUTES = ["group", "preferred_member_key", "roles"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
        # self.group_id = group_id
        # self.membership_id = membership_id

    @property
    def import_address(self) ->str:
        raise NotImplementedError
        return f'groups/{self.group_id}/membership_id/{self.membership_id}'

    @classmethod
    def create(cls, id, **kwargs):
        return super().create(id, **kwargs)
