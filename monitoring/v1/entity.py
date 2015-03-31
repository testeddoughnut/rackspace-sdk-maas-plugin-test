# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import

from .. import monitoring_service
from .. import monitoring_resource
from openstack import resource


class Entity(monitoring_resource.MonitoringResource):
    resources_key = 'values'
    base_path = '/entities'
    service = monitoring_service.MonitoringService()
    name_attribute = 'label'

    # capabilities
    allow_create = True
    allow_retrieve = True
    allow_update = True
    allow_delete = True
    allow_list = True

    put_update = True

    # Properties
    #: A dictionary of addresses this server can be accessed through.
    #: The dictionary contains keys such as ``private`` and ``public``,
    #: each containing a list of dictionaries for addresses of that type.
    #: The addresses are contained in a dictionary with keys ``addr``
    #: and ``version``, which is either 4 or 6 depending on the protocol
    #: of the IP address. *Type: dict*
    ip_addresses = resource.prop('ip_addresses', type=dict)
    #: Metadata stored for this server. *Type: dict*
    metadata = resource.prop('metadata', type=dict)
    #: The name of this server.
    label = resource.prop('label')
