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

from six.moves.urllib import parse as url_parse

from openstack import exceptions
from openstack import resource


class MonitoringResource(resource.Resource):
    """MaaS pagination is dumb. The marker is the first item in the next
    list instead of the last item in the previous list. This is a dumb
    workaround. I'm sorry."""

    @classmethod
    def list(cls, session, limit=None, marker=None, path_args=None,
             paginated=False, **params):
        """Get a response that is a list of objects.

        This method starts at ``limit`` and ``marker`` (both defaulting to
        None), advances the marker to the last item received in each response,
        and continues making requests for more resources until no results
        are returned.

        :param session: The session to use for making this request.
        :type session: :class:`~openstack.session.Session`
        :param limit: The maximum amount of results to retrieve.
                      The default is ``None``, which means no limit will be
                      set, and the underlying API will return its default
                      amount of responses.
        :param marker: The position in the list to begin requests from.
                       The type of value to use for ``marker`` depends on
                       the API being called.
        :param dict path_args: A dictionary of arguments to construct
                               a compound URL.
                               See `How path_args are used`_ for details.
        :param bool paginated: ``True`` if a GET to this resource returns
                               a paginated series of responses, or ``False``
                               if a GET returns only one page of data.
                               **When paginated is False only one
                               page of data will be returned regardless
                               of the API's support of pagination.**
        :param dict params: Parameters to be passed into the underlying
                            :meth:`~openstack.session.Session.get` method.

        :return: A generator of :class:`Resource` objects.
        :raises: :exc:`~openstack.exceptions.MethodNotSupported` if
                 :data:`Resource.allow_list` is not set to ``True``.
        """
        if not cls.allow_list:
            raise exceptions.MethodNotSupported('list')

        more_data = True

        while more_data:
            resp, marker = cls.page(session, limit, marker, path_args,
                                    **params)

            # TODO(briancurtin): Although there are a few different ways
            # across services, we can know from a response if it's the end
            # without doing an extra request to get an empty response.
            # Resources should probably carry something like a `_should_page`
            # method to handle their service's pagination style.
            if not resp or marker is None:
                more_data = False

            # Keep track of how many items we've yielded. If we yielded
            # less than our limit, we don't need to do an extra request
            # to get back an empty data set, which acts as a sentinel.
            yielded = 0
            for data in resp:
                value = cls.existing(**data)
                yielded += 1
                yield value

            if not paginated or limit and yielded < limit:
                more_data = False

    @classmethod
    def page(cls, session, limit=None, marker=None, path_args=None, **params):
        """Get a one page response.

        This method gets starting at ``marker`` with a maximum of ``limit``
        records.

        :param session: The session to use for making this request.
        :type session: :class:`~openstack.session.Session`
        :param limit: The maximum amount of results to retrieve. The default
                      is to retrieve as many results as the service allows.
        :param marker: The position in the list to begin requests from.
                       The type of value to use for ``marker`` depends on
                       the API being called.
        :param dict path_args: A dictionary of arguments to construct
                               a compound URL.
                               See `How path_args are used`_ for details.
        :param dict params: Parameters to be passed into the underlying
                            :meth:`~openstack.session.Session.get` method.

        :return: A list of dictionaries returned in the response body.
        """

        filters = {}

        if limit:
            filters['limit'] = limit
        if marker:
            filters['marker'] = marker

        if path_args:
            url = cls.base_path % path_args
        else:
            url = cls.base_path
        if filters:
            url = '%s?%s' % (url, url_parse.urlencode(filters))

        resp = session.get(url, service=cls.service, params=params).body
        next_marker = None
        if resp['metadata']['next_marker'] != 'null':
            next_marker = resp['metadata']['next_marker']
        if cls.resources_key:
            resp = resp[cls.resources_key]
        return resp, next_marker

    @classmethod
    def find(cls, session, name_or_id, path_args=None):
        """Find a resource by its name or id.

        :param session: The session to use for making this request.
        :type session: :class:`~openstack.session.Session`
        :param resource_id: This resource's identifier, if needed by
                            the request. The default is ``None``.
        :param dict path_args: A dictionary of arguments to construct
                               a compound URL.
                               See `How path_args are used`_ for details.

        :return: The :class:`Resource` object matching the given name or id
                 or None if nothing matches.
        """
        try:
            args = {
                cls.id_attribute: name_or_id
            }
            info, next_marker = cls.page(session, limit=2, **args)
            if len(info) == 1:
                return cls.existing(**info[0])
        except exceptions.HttpException:
            pass

        if cls.name_attribute:
            params = {cls.name_attribute: name_or_id,
                      'fields': cls.id_attribute}
            info, next_marker = cls.page(session, limit=2, path_args=path_args,
                                         **params)
            if len(info) == 1:
                return cls.existing(**info[0])
            if len(info) > 1:
                msg = "More than one %s exists with the name '%s'."
                msg = (msg % (cls.get_resource_name(), name_or_id))
                raise exceptions.DuplicateResource(msg)

        return None
