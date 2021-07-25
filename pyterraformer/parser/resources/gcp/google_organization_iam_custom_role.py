import re
from typing import List
from pyterraformer.parser.resources.resource_object import ResourceObject


class GoogleOrganizationIamCustomRole(ResourceObject):
    _type = "google_organization_iam_custom_role"
    REQUIRED_ATTRIBUTES = ["role_id", "org_id", "title", "description", "permissions"]

    def __init__(self, id, rtype, text, attributes=None):
        ResourceObject.__init__(self, rtype, id, text, attributes)
        self.role_id = self.role_id

    def render_role(self):
        return f"organizations/825417849120/roles/{self.role_id}"

    @classmethod
    def create(  # type: ignore
        cls,
        id: str,
        role_id: str,
        org_id: str,
        title: str,
        description: str,
        permissions: List[str],
        **kwargs,
    ):
        # clean and map to lowercase
        id = id.replace("_", "-")
        role_id = role_id.replace("-", "_")
        permissions = [val.replace('"', "").strip() for val in permissions]
        if not re.match("^[a-zA-Z0-9_\.]{3,64}\Z", role_id):
            raise ValueError(
                f"Role ID {role_id} does not match required regex [a-zA-Z0-9_\.]{{3, 64}}"
            )
        kwargs["role_id"] = role_id
        kwargs["org_id"] = org_id
        kwargs["title"] = title
        kwargs["description"] = description
        kwargs["permissions"] = permissions
        return super().create(id, **kwargs)
