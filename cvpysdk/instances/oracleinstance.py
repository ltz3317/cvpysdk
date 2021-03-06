#FIXME:https://engweb.commvault.com/engtools/defect/215340
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
File for operating on a Oracle Instance.

OracleInstance is the only class defined in this file.

OracleInstance: Derived class from Instance Base class, representing an
                            oracle instance, and to perform operations on that instance

OracleInstance:

    __init__()                          -- Constructor for the class

    configure_data_masking_policy()     --  Method to configure data masking policy

    get_masking_policy_id()             --  Method to get policy id of given data masking policy

    standalone_data_masking()           --  Method to launch standalone data masking job on instance

    delete_data_masking_policy()        --  Method to delete given data masking policy

    _get_browse_options                 -- Method to get browse options for oracle instance

    _process_browse_response            -- Method to process browse response

    oracle_home()                       -- Getter for $ORACLE_HOME of this instance

    version()                           -- Getter for oracle database version

    is_catalog_enabled()                -- Getter to check if catalog is enabled for backups

    catalog_user()                      -- Getter for getting catalog user

    catalog_db()                        -- Getter for catalog database name

    archive_log_dest()                  -- Getter for archivelog destination

    os_user()                           -- Getter for OS user owning oracle software

    cmd_sp()                            -- Getter for command line storage policy

    log_sp()                            -- Getter for log storage policy

    is_autobackup_on()                  -- Getter to check if autobackup is enabled

    db_user()                           -- Getter for SYS database user name

    tns_name()                          -- Getter for TNS connect string

    dbid()                              -- Getter for getting DBID of database

    restore()                           -- Method to restore the instance

"""
from __future__ import unicode_literals

import json

from ..instance import Instance
from ..exception import SDKException


class OracleInstance(Instance):
    """
    Class to represent a standalone Oracle Instance
    """

    def __init__(self, agent_object, instance_name, instance_id=None):
        """
        Constructor for the class

        Args:
            agent_object    -- instance of the Agent class
            instance_name   -- name of the instance
            instance_id     --  id of the instance

        """
        super(OracleInstance, self).__init__(
            agent_object, instance_name, instance_id)
        self._instanceprop = {}  # instance variable to hold instance properties

    def configure_data_masking_policy(self, policy_name, table_list_of_dict):
        """Method to configure data masking policy with given parameters
        Args:
            policy_name         (str)   --  string representing policy name
            table_list_of_dict  list(dict)  -- list containing one dict item representing
                                                rules for single table
            Sample  list
            Tables:
                    [
                    {
                    "name":"schema_name.table_name",
                    "columns": [ {"name":"column_name", "type":"algorithm_type"},
                                "arguments":[list of strings]…]
                    }
                    ]
                    Sample :
                    [
                    {
                    "name":"HR.NUMNEW",
                    "columns":[{"name":"N1","type":0},{"name":"N2","type":2,
                    "arguments":["1000","2000"]}]
                    },
                    {
                    "name":"HR.CHANGE",
                    "columns":[{"name":"C1","type":1},{"name":"C2","type":1}]
                    }
                    ]
            schema_name , table_name, column_name: str
            Column type key in main dict takes list of dict as value :
            This list of dict represents each column name and type of algorithm
            and arguments if any for that algorithm
            arguments : list of strings

            Choose appropriate algorithm type and pass necessary arguments based
            on column type

            Algorithm       Arguments mandatory       Arguments Format        Algorithm type number

            Shuffling           NA                              NA                      0
            Numeric Range       [min, max]                  ["1000","2000"]             2
            Numeric Variance    [variance percentage]           ["50"]                  3
            FPE                 NA                              NA                      1
            Fixed String        string_to_replace           ["string_to_replace"]       4


            Supported Algorithms :

            Column Type     Algorithms Supported

            Numeric         Shuffling, FPE, Numeric Range, Numeric Variance
            Char            Shuffling , FPE , Fixed String
            Varchar         Shuffling , FPE , Fixed String

        """
        request_json = {
            "opType": 2,
            "policy": {
                "association": {"instanceId": int(self.instance_id)},
                "config": {"tables": table_list_of_dict},
                "policy": {"policyName": policy_name}
            }
        }

        flag, response = self._cvpysdk_object.make_request(
            'POST', self._services['MASKING_POLICY'], request_json
        )
        if flag:
            if response.json():
                error_code = response.json()['errorCode']

                if error_code != 0:
                    error_string = response.json()['errorMessage']
                    raise SDKException(
                        'Instance',
                        '102',
                        'Error while creating Data masking policy\nError: "{0}"'.format(
                            error_string)
                    )
                else:
                    return True

            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException('Response', '101',
                               self._update_response_(response.text))

    def get_masking_policy_id(self, policy_name):
        """Method to get policy id of given data masking policy
        Args:
            policy_name          (str)       -- data masking policy name

        Returns:
            policy_id            (int)       -- data masking policy ID

        """
        instance_id = int(self.instance_id)
        flag, response = self._cvpysdk_object.make_request(
            'GET', self._services['MASKING_POLICY'])
        response_json = response.json()
        policy_list = response_json["policies"]
        policy_id = None
        for i in policy_list:
            pname = i["policy"]["policyName"]
            associated_instance_id = i["association"]["instanceId"]
            if (pname == policy_name) and (associated_instance_id == instance_id):
                policy_id = int(i["policy"]["policyId"])
                break
            else:
                continue
        return policy_id

    def delete_data_masking_policy(self, policy_name):
        """Method to delete given data masking policy
        Args:
            policy_name         (str)       --  data masking policy name to be deleted

        Returns:
            bool                            -- returns true when deletion succeeds

        Raises:
            Exception

                When deletion of policy fails

                When Invalid policy name under given instance is provided
        """
        source_instance_id = int(self.instance_id)
        policy_id = self.get_masking_policy_id(policy_name)
        if policy_id is None:
            raise SDKException(
                'Instance',
                '106')

        request_json = {
            "opType": 3,
            "policy": {
                "association": {"instanceId": source_instance_id},
                "policy": {"policyId": policy_id, "policyName": policy_name}
            }
        }

        flag, response = self._cvpysdk_object.make_request(
            'POST', self._services['MASKING_POLICY'], request_json
        )
        if flag:
            if response.json():
                error_code = response.json()['errorCode']

                if error_code != 0:
                    raise SDKException(
                        'Instance',
                        '102',
                        'Error while deleting Data masking policy\nError')
                else:
                    return True

            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException('Response', '101',
                               self._update_response_(response.text))

    def standalone_data_masking(
            self,
            policy_name,
            destination_client=None,
            destination_instance=None):
        """Method to launch standalone data masking job on given instance

        Args:

            policy_name          (str)       -- data masking policy name

            destination_client   (str)       -- destination client in which destination
            instance exists

            destination_instance (str)       -- destination instance to which masking
            to be applied

        Returns:
            object -- Job containing data masking job details


        Raises:
            SDKException
                if policy ID retrieved is None

        """
        if destination_client is None:
            destination_client = self._properties['instance']['clientName']
        if destination_instance is None:
            destination_instance = self.instance_name
        destination_client_object = self._commcell_object.clients.get(
            destination_client)
        destination_agent_object = destination_client_object.agents.get(
            'oracle')
        destination_instance_object = destination_agent_object.instances.get(
            destination_instance)
        destination_instance_id = int(destination_instance_object.instance_id)
        source_instance_id = int(self.instance_id)
        policy_id = self.get_masking_policy_id(policy_name)
        if policy_id is None:
            raise SDKException(
                'Instance',
                '106')
        request_json = self._restore_json(paths=r'/')
        data_masking_options = {
            "restoreOptions": {
                "destination": {
                    "destClient": {
                        "clientName": destination_client},
                    "destinationInstance": {
                        "clientName": destination_client,
                        "instanceName": destination_instance,
                        "instanceId": destination_instance_id}},
                "dbDataMaskingOptions": {
                    "isStandalone": True,
                    "enabled": True,
                    "dbDMPolicy": {
                        "association": {
                            "instanceId": source_instance_id},
                        "policy": {
                            "policyId": policy_id,
                            "policyName": policy_name}}}}}
        request_json["taskInfo"]["subTasks"][0]["options"] = data_masking_options
        return self._process_restore_response(request_json)

    def _get_oracle_restore_json(self, destination_client,
                                 instance_name, tablespaces,
                                 files, browse_option,
                                 common_options, oracle_options):
        """
        Gets the basic restore JSON from base class and modifies it for oracle

        Args:
            destination_client  (str)   --  Destination client name

            instance_name   (str)   --  instance name to restore

            tablespaces (list)  --  tablespace name list

            files   (dict)  --  fileOptions

            browse_option   (dict)  --  dict containing browse options

            common_options  (dict)  --  dict containing common options

            oracle_options  (dict)  --  dict containing other oracle options

        Returns:
            (dict) -- JSON formatted options to restore the oracle database

        Raises:
            TypeError:
                if tablespace is passed as a list
                if files is not passed as a dictionary

        """
        if not isinstance(tablespaces, list):
            raise TypeError('Expecting a list for tablespaces')
        if files is not None:
            if not isinstance(files, dict):
                raise TypeError('Expecting a dict for files')

        destination_id = int(self._commcell_object.clients.get(
            destination_client).client_id)
        tslist = ["SID: {0} Tablespace: {1}".format(
            instance_name, ts) for ts in tablespaces]
        restore_json = self._restore_json(paths=r'/')
        if common_options is not None:
            restore_json["taskInfo"]["subTasks"][0]["options"]["restoreOptions"][
                "commonOptions"] = common_options
        restore_json["taskInfo"]["subTasks"][0]["options"]["restoreOptions"][
            "oracleOpt"] = oracle_options
        if files is None:
            restore_json["taskInfo"]["subTasks"][0]["options"]["restoreOptions"]["fileOption"] = {
                "sourceItem": tslist
            }
        else:
            restore_json["taskInfo"]["subTasks"][0]["options"][
                "restoreOptions"]["fileOption"] = files

        if browse_option is not None:
            restore_json["taskInfo"]["subTasks"][0]["options"]["restoreOptions"][
                "browseOption"] = browse_option
        return restore_json

    def _get_browse_options(self):
        """Method to return the database instance properties for browse and restore"""
        return {
            "path": "/",
            "entity": {
                "appName": self._properties['instance']['appName'],
                "instanceId": int(self.instance_id),
                "applicationId": int(self._properties['instance']['applicationId']),
                "clientId": int(self._properties['instance']['clientId']),
                "instanceName": self._properties['instance']['instanceName'],
                "clientName": self._properties['instance']['clientName']
            }
        }

    def _process_browse_response(self, request_json):
        """Runs the DBBrowse API with the request JSON provided for Browse,
            and returns the contents after parsing the response.

            Args:
                request_json    (dict)  --  JSON request to run for the API

            Returns:
                list - list containing tablespaces for the instance

            Raises:
                SDKException:
                    if browse job failed

                    if browse is empty

                    if browse is not success
        """
        if 'tablespaces' in self._instanceprop:
            return self._instanceprop['tablespaces']

        browse_service = self._commcell_object._services['ORACLE_INSTANCE_BROWSE'] % (
            self.instance_id
        )

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', browse_service, request_json
        )

        if flag:
            response_data = json.loads(response.text)
            if response_data:
                if "oracleContent" in response_data:
                    self._instanceprop['tablespaces'] = response_data["oracleContent"]
                    return self._instanceprop['tablespaces']
                elif "errorCode" in response_data:
                    error_message = response_data['errorMessage']
                    o_str = 'Browse job failed\nError: "{0}"'.format(
                        error_message)
                    raise SDKException('Instance', '102', o_str)
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(
                response.text)
            raise SDKException('Response', '101', response_string)

    @property
    def oracle_home(self):
        """
        getter for oracle home

        Returns:
            string - string of oracle_home

        """
        return self._properties['oracleInstance']['oracleHome']

    @property
    def is_catalog_enabled(self):
        """
        Getter to check if catalog has been enabled

        Returns:
            Bool - True if catalog is enabled. Else False.

        """
        return self._properties['oracleInstance']['useCatalogConnect']

    @property
    def catalog_user(self):
        """
        Getter for catalog user

        Returns:
            string  - String containing catalog user

        Raises:
            SDKException:
                if not set

                if catalog is not enabled

        """
        if not self.is_catalog_enabled:
            raise SDKException('Instance', r'102', 'Catalog is not enabled.')
        try:
            return self._properties['oracleInstance']['catalogConnect']['userName']
        except KeyError as error_str:
            raise SDKException('Instance', r'102',
                               'Catalog user not set - {}'.format(error_str))

    @property
    def catalog_db(self):
        """
        Getter for catalog database

        Returns:
            string  - String containing catalog database

        Raises:
            SDKException:
                if not set

                if catalog is not enabled

        """
        if not self.is_catalog_enabled:
            raise SDKException('Instance', r'102', 'Catalog is not enabled.')
        try:
            return self._properties['oracleInstance']['catalogConnect']['domainName']
        except KeyError as error_str:
            raise SDKException('Instance', r'102',
                               'Catalog database not set - {}'.format(error_str))

    @property
    def os_user(self):
        """
        Getter for oracle software owner

        Returns:
            string - string of oracle software owner

        """
        return self._properties['oracleInstance']['oracleUser']['userName']

    @property
    def version(self):
        """
        Getter for oracle version

        Returns:
            string - string of oracle instance version

        """
        return self._properties['version']

    @property
    def archive_log_dest(self):
        """
        Getter for the instance's archive log dest

        Returns:
            string - string for archivelog location

        """
        return self._properties['oracleInstance']['archiveLogDest']

    @property
    def cmd_sp(self):
        """
        Getter for Command Line storage policy

        Returns:
            string - string for command line storage policy

        """
        return self._properties['oracleInstance']['oracleStorageDevice'][
            'commandLineStoragePolicy']['storagePolicyName']

    @property
    def log_sp(self):
        """
        Oracle Instance's Log Storage Poplicy

        Returns:
            string  -- string containing log storage policy

        """
        return self._properties['oracleInstance']['oracleStorageDevice'][
            'logBackupStoragePolicy']['storagePolicyName']

    @property
    def is_autobackup_on(self):
        """
        Getter to check whether autobackup is set to ON

        Returns:
            Bool - True if autobackup is set to ON. Else False.

        """
        return True if self._properties['oracleInstance']['ctrlFileAutoBackup'] == 1 else False

    @property
    def db_user(self):
        """
        Getter to get the database user used to log into the database

        Returns: Oracle database user for the instance

        """
        return self._properties['oracleInstance']['sqlConnect']['userName']

    @property
    def tns_name(self):
        """
        Getter to get the TNS Names of the database

        Returns:
            string  -- TNS name of the instance configured

        Raises:
            SDKException:
                if not set

        """
        try:
            return self._properties['oracleInstance']['sqlConnect']['domainName']
        except KeyError as error_str:
            raise SDKException('Instance', r'102',
                               'Instance TNS Entry not set - {}'.format(error_str))

    @property
    def dbid(self):
        """
        Getter to get the DBID of the database instance

        Returns: DBID of the oracle database

        """
        return self._properties['oracleInstance']['DBID']

    @property
    def tablespaces(self):
        """
        Getter for listing out all tablespaces for the instance

        Returns:
            list -- list containing tablespace names for the database

        """
        return [ts['tableSpace'] for ts in self.browse()]

    def browse(self, *args, **kwargs):
        """Overridden method to browse oracle database tablespaces"""
        if args and isinstance(args[0], dict):
            options = args[0]
        elif kwargs:
            options = kwargs
        else:
            options = self._get_browse_options()
        return self._process_browse_response(options)

    def backup(self, subclient_name=r"default"):
        """Uses the default subclient to backup the database

        Args:
            subclient_name (str) -- name of subclient to use
                default: default
        """
        return self.subclients.get(subclient_name).backup(r'full')

    def restore(
            self,
            files=None,
            destination_client=None,
            common_options=None,
            browse_option=None,
            oracle_options=None):
        """
        Method to restore full/partial database using latest backup or backup copy

        Args:
            files   (dict)    --  fileOption for restore
            destination_client  (str)    --  destination client name

            common_options  dict)    --  dictionary containing common options
                default:    None

            browse_option   (dict)  --  dictionary containing browse options

            oracle_options (dict) --    dictionary containing other oracle options
                default:    By default it restores the controlfile and datafiles from latest backup

            Example: {
            "resetLogs": 1,
            "switchDatabaseMode": True,
            "noCatalog": True,
            "restoreControlFile": True,
            "recover": True,
            "recoverFrom": 3,
            "restoreData": True,
            "restoreFrom": 3
            }

        Returns:
            object  --  Job containing restore details

        Raises:
            TypeError   --  If the oracle options is not a dict
            SDKException    --  If destination_client can't be set

        """
        if oracle_options is None:
            oracle_options = {
                "resetLogs": 1,
                "switchDatabaseMode": True,
                "noCatalog": True,
                "restoreControlFile": True,
                "recover": True,
                "recoverFrom": 3,
                "restoreData": True,
                "restoreFrom": 3
            }

        if not isinstance(oracle_options, dict):
            raise TypeError('Expecting a dict for oracle_options')

        try:
            if destination_client is None:
                destination_client = self._properties['instance']['clientName']
        except SDKException:
            raise
        else:
            # subclient = self.subclients.get(subclient_name)
            options = self._get_oracle_restore_json(destination_client=destination_client,
                                                    instance_name=self.instance_name,
                                                    tablespaces=self.tablespaces,
                                                    files=files,
                                                    browse_option=browse_option,
                                                    common_options=common_options,
                                                    oracle_options=oracle_options)
            return self._process_restore_response(options)
