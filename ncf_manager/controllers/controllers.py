# -*- coding: utf-8 -*-
# ######################################################################
# © 2015-2018 Marcos Organizador de Negocios SRL. (https://marcos.do/)
#             Eneldo Serrata <eneldo@marcos.do>
# © 2017-2018 iterativo SRL. (https://iterativo.do/)
#             Gustavo Valverde <gustavo@iterativo.do>
# © 2018      INDEXA SRL. (https://indexa.do/)
#             José López <jlopez@indexa.do>

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
# along with NCF Manager.  If not, see <http://www.gnu.org/licenses/>.
# ######################################################################

import json
import re
import logging

from odoo import http

_logger = logging.getLogger(__name__)

try:
    from stdnum.do import rnc, cedula
except(ImportError, IOError) as err:
    _logger.debug(str(err))


class Odoojs(http.Controller):
    @http.route('/dgii_ws', auth='public', cors="*")
    def index(self, **kwargs):
        """
        Look for clients in the web service of the DGII
            :param self:
            :param **kwargs dict :the parameters received
            :param term string : the character of the client or his rnc /
        """
        term = kwargs.get("term", False)
        if term:
            if term.isdigit() and len(term) in [9, 11]:
                result = rnc.check_dgii(term)
            else:
                result = rnc.search_dgii(term, end_at=20, start_at=1)
            if not result is None:
                if not isinstance(result, list):
                    result = [result]

                for d in result:
                    d["name"] = " ".join(re.split("\s+", d["name"], flags=re.UNICODE))  # remove all duplicate white space from the name
                    d["label"] = u"{} - {}".format(d["rnc"], d["name"])
                return json.dumps(result)

    @http.route('/validate_rnc/', auth='public', cors="*")
    def validate_rnc(self, **kwargs):
        """
        Check if the number provided is a valid RNC
            :param self:
            :param **kwargs dict :the parameters received
            :param rnc string : the character of the client or his rnc
        """
        num = kwargs.get("rnc", False)
        if num.isdigit():
            if (len(num) == 9 and rnc.is_valid(num)) or (len(num) == 11 and cedula.is_valid(num)):
                try:
                    info = rnc.check_dgii(num)
                except Exception as err:
                    info = None
                    _logger.error(">>> " + str(err))

                if info is not None:
                    # remove all duplicate white space from the name
                    info["name"] = " ".join(re.split("\s+", info["name"], flags=re.UNICODE))

                return json.dumps({"is_valid": True, "info": info})

        return json.dumps({"is_valid": False})
