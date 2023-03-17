# This file is part of NCF Manager.

# NCF Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# NCF Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with NCF Manager.  If not, see <https://www.gnu.org/licenses/>.

import json
import re
import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc
except (ImportError, IOError) as err:
    _logger.debug(str(err))


class Odoojs(http.Controller):

    @http.route('/dgii_ws', auth='public', cors="*")
    def index(self, **kwargs):
        term = kwargs.get("term", False)

        query_dgii_wsmovil = request.env['ir.config_parameter'].sudo(
         ).get_param('dgii.wsmovil_module')
        
        if term and query_dgii_wsmovil == 'True':
            if not term:
                return json.dumps([])

            try:
                if term.isdigit() and len(term) in [9, 11]:
                    result = rnc.check_dgii(term)
                else:
                    result = rnc.search_dgii(term, end_at=20, start_at=1)

                if result is not None:
                    if not isinstance(result, list):
                        result = [result]

                    for d in result:
                        d["name"] = " ".join(
                            re.split(r"\s+", d["name"], flags=re.UNICODE)
                        )  # remove all duplicate white space from the name
                        d["label"] = u"{} - {}".format(d["rnc"], d["name"])
                    return json.dumps(result)
            except requests.exceptions.ConnectionError:
                _logger.error("RncSearchError by %s", str(term), exc_info=True)

            return json.dumps([])
