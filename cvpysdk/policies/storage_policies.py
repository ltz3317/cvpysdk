# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing storage policy related operations on the commcell.

This file has all the classes related to Storage Policy operations.

StoragePolicies:  Class for representing all the Storage Policies associated to the commcell.

StoragePolicy:    Class for representing a single Storage Policy associated to the commcell.


StoragePolicies:
    __init__(commcell_object)    --  initialize the StoragePolicies instance for the commcell

    __str__()                    --  returns all the storage policies associated with the commcell

    __repr__()                   --  returns a string for the instance of the StoragePolicies class

    _get_policies()              --  gets all the storage policies of the commcell

    all_storage_policies()       --  returns the dict of all the storage policies on commcell

    has_policy(policy_name)      --  checks if a storage policy exists with the given name

    add()                        --  adds a new storage policy to the commcell

    add_tape_sp()                --  add new storage policy with tape library as data path

    delete(storage_policy_name)  --  removes the specified storage policy from the commcell

    refresh()                    --  refresh the storage policies associated with the commcell


StoragePolicy:
    __init__(commcell_object,
             storage_policy_name,
             storage_policy_id)             --  initialize the instance of StoragePolicy class for
    a specific storage policy of the commcell


    __repr__()                              --  returns a string representation of the
    StoragePolicy instance

    _get_storage_policy_id()                --  gets the id of the StoragePolicy instance

    _get_storage_policy_properties()        --  returns the properties of this storage policy

    _initialize_storage_policy_properties() --  initializes storage policy properties

    has_copy()                              --  checks if copy with given name exists

    create_secondary_copy()                 --  creates a storage policy copy

    create_dedupe_secondary_copy()          --  create secondary copy with dedupe enabled

    delete_secondary_copy()                 --  deletes storage policy copy

    copies()                                --  returns the storage policy copies associated with
    this storage policy

    run_backup_copy()                       --  Runs the backup copy job from Commcell

    run_snapshot_cataloging()               --  Runs the deferred catalog job from Commcell

    run_aux_copy()                          --  starts a aux copy job for this storage policy and
    returns the job object

    refresh()                               --  refresh the properties of the storage policy

    update_transactional_ddb()              --  enable/disable transactional DDB option on a DDB

    seal_ddb()                              --  seal a DDB store

    delete_job()                            -- delete a job from storage policy node

    add_ddb_partition()                     -- Adds a new DDB partition

    move_dedupe_store()                     -- Moves a deduplication store

    run_ddb_verification()                  -- Runs DDB verification job


"""

from __future__ import absolute_import
from __future__ import unicode_literals

from base64 import b64encode

from past.builtins import basestring
from future.standard_library import install_aliases

from ..exception import SDKException
from ..job import Job

from ..storage import DiskLibrary
from ..storage import MediaAgent

install_aliases()


class StoragePolicies(object):
    """Class for getting all the storage policies associated with the commcell."""

    def __init__(self, commcell_object):
        """Initialize object of the StoragePolicies class.

            Args:
                commcell_object (object)  --  instance of the Commcell class

            Returns:
                object - instance of the StoragePolicies class
        """
        self._commcell_object = commcell_object
        self._POLICY = self._commcell_object._services['STORAGE_POLICY']

        self._policies = None
        self.refresh()

    def __str__(self):
        """Representation string consisting of all storage policies of the commcell.

            Returns:
                str - string of all the storage policies associated with the commcell
        """
        representation_string = '{:^5}\t{:^20}\n\n'.format('S. No.', 'Storage Policy')

        for index, policy in enumerate(self._policies):
            sub_str = '{:^5}\t{:20}\n'.format(index + 1, policy)
            representation_string += sub_str

        return representation_string.strip()

    def __repr__(self):
        """Representation string for the instance of the Clients class."""
        return "StoragePolicies class instance for Commcell: '{0}'".format(
            self._commcell_object.commserv_name
        )

    def _get_policies(self):
        """Gets all the storage policies associated to the commcell specified by commcell object.

            Returns:
                dict - consists of all storage policies of the commcell
                    {
                         "storage_policy1_name": storage_policy1_id,
                         "storage_policy2_name": storage_policy2_id
                    }

            Raises:
                SDKException:
                    if response is empty

                    if response is not success
        """
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'GET', self._POLICY + "?getAll=TRUE")

        if flag:
            if response.json() and 'policies' in response.json():
                policies = response.json()['policies']

                if policies == []:
                    return {}

                policies_dict = {}

                for policy in policies:
                    temp_name = policy['storagePolicyName'].lower()
                    temp_id = str(policy['storagePolicyId']).lower()
                    policies_dict[temp_name] = temp_id

                return policies_dict
            else:
                return {}
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    @property
    def all_storage_policies(self):
        """Returns dict of all the storage policies on this commcell

            dict - consists of all storage policies of the commcell
                    {
                         "storage_policy1_name": storage_policy1_id,
                         "storage_policy2_name": storage_policy2_id
                    }
        """
        return self._policies

    def has_policy(self, policy_name):
        """Checks if a storage policy exists in the commcell with the input storage policy name.

            Args:
                policy_name (str)  --  name of the storage policy

            Returns:
                bool - boolean output whether the storage policy exists in the commcell or not

            Raises:
                SDKException:
                    if type of the storage policy name argument is not string
        """
        if not isinstance(policy_name, basestring):
            raise SDKException('Storage', '101')

        return self._policies and policy_name.lower() in self._policies

    def get(self, storage_policy_name):
        """Returns a StoragePolicy object of the specified storage policy name.

            Args:
                storage_policy_name     (str)   --  name of the storage policy

            Returns:
                object - instance of the StoragePolicy class for the given policy name

            Raises:
                SDKException:
                    if type of the storage policy name argument is not string

                    if no storage policy exists with the given name
        """
        if not isinstance(storage_policy_name, basestring):
            raise SDKException('Storage', '101')

        storage_policy_name = storage_policy_name.lower()

        if self.has_policy(storage_policy_name):
            return StoragePolicy(
                self._commcell_object, storage_policy_name, self._policies[storage_policy_name]
            )
        else:
            raise SDKException(
                'Storage', '102', 'No policy exists with name: {0}'.format(storage_policy_name)
            )

    def add(self,
            storage_policy_name,
            library,
            media_agent,
            dedup_path=None,
            incremental_sp=None,
            retention_period=5,
            number_of_streams=None):
        """Adds a new Storage Policy to the Commcell.

            Args:
                storage_policy_name (str)         --  name of the new storage policy to add

                library             (str/object)  --  name or instance of the library
                to add the policy to

                media_agent         (str/object)  --  name or instance of media agent
                to add the policy to

                dedup_path          (str)         --  the path of the deduplication database
                default: None

                incremental_sp      (str)         --  the name of the incremental storage policy
                associated with the storage policy
                default: None

                retention_period    (int)         --  time period in days to retain
                the data backup for
                default: 5

                number_of_streams   (int)         --  the number of streams for the storage policy
                default: None

            Raises:
                SDKException:
                    if type of the storage policy name argument is not string

                    if type of the retention period argument is not int

                    if type of the library argument is not either string or DiskLibrary instance

                    if type of the media agent argument is not either string or MediaAgent instance

                    if failed to create storage policy

                    if response is empty

                    if response is not success
        """
        from urllib.parse import urlencode

        if ((dedup_path is not None and not isinstance(dedup_path, basestring)) or
                (not (isinstance(storage_policy_name, basestring) and
                      isinstance(retention_period, int))) or
                (incremental_sp is not None and not isinstance(incremental_sp, basestring))):
            raise SDKException('Storage', '101')

        if isinstance(library, DiskLibrary):
            disk_library = library
        elif isinstance(library, basestring):
            disk_library = DiskLibrary(self._commcell_object, library)
        else:
            raise SDKException('Storage', '104')

        if isinstance(media_agent, MediaAgent):
            media_agent = media_agent
        elif isinstance(media_agent, basestring):
            media_agent = MediaAgent(self._commcell_object, media_agent)
        else:
            raise SDKException('Storage', '103')

        if dedup_path or incremental_sp:
            encode_dict = {
                "storagepolicy": storage_policy_name,
                "mediaagent": media_agent.media_agent_name,
                "library": disk_library.library_name
            }
            if dedup_path:
                encode_dict["deduppath"] = dedup_path
            if incremental_sp:
                encode_dict["incstoragepolicy"] = incremental_sp

            web_service = self._POLICY + '?' + urlencode(encode_dict)

            flag, response = self._commcell_object._cvpysdk_object.make_request('PUT', web_service)

            if flag:
                try:
                    if response.json():
                        if 'errorCode' in response.json() and 'errorMessage' in response.json():
                            error_message = response.json()['errorMessage'].split('\n')[0]
                            o_str = 'Failed to add storage policy\nError: "{0}"'

                            raise SDKException('Storage', '102', o_str.format(error_message))

                except ValueError:
                    if response.text:
                        # initialize the policies again
                        # so the policies object has all the policies
                        self.refresh()
                        return response.text.strip()
                    else:
                        raise SDKException('Response', '102')
            else:
                response_string = self._commcell_object._update_response_(response.text)
                raise SDKException('Response', '101', response_string)
        else:
            request_json = {
                "storagePolicyCopyInfo": {
                    "library": {
                        "libraryId": int(disk_library.library_id)
                    },
                    "mediaAgent": {
                        "mediaAgentId": int(media_agent.media_agent_id)
                    },
                    "retentionRules": {
                        "retainBackupDataForDays": retention_period
                    }
                },
                "storagePolicyName": storage_policy_name
            }

            if number_of_streams is not None:
                number_of_streams_dict = {
                    "numberOfStreams": number_of_streams
                }
                request_json.update(number_of_streams_dict)

            flag, response = self._commcell_object._cvpysdk_object.make_request(
                'POST', self._POLICY, request_json
            )

            if flag:
                if response.json():
                    if 'archiveGroupCopy' in response.json():
                        # initialize the policies again
                        # so the policies object has all the policies
                        self.refresh()

                    elif 'error' in response.json():
                        error_message = response.json()['error']['errorMessage']
                        o_str = 'Failed to create storage policy\nError: "{0}"'

                        raise SDKException('Storage', '102', o_str.format(error_message))
                else:
                    raise SDKException('Response', '102')
            else:
                response_string = self._commcell_object._update_response_(response.text)
                raise SDKException('Response', '101', response_string)

            return self.get(storage_policy_name)

    def add_tape_sp(self, storage_policy_name, library, media_agent, drive_pool, scratch_pool):
        """
        Adds storage policy with tape data path
        Args:
                storage_policy_name (str)         --  name of the new storage policy to add

                library             (str)          --  name or instance of the library
                to add the policy to

                media_agent         (str/object)  --  name or instance of media agent
                to add the policy to

                drive_pool          (str)         --  Drive pool name of the tape library

                scratch_pool      (str)          --  Scratch pool name of the tape library

            Raises:
                SDKException:
                    if type of the storage policy name argument is not string

                    if type of the retention period argument is not int

                    if type of the library argument is not either string or DiskLibrary instance

                    if type of the media agent argument is not either string or MediaAgent instance

                    if failed to create storage policy

                    if response is empty

                    if response is not success
        """

        from urllib.parse import urlencode
        if not (isinstance(drive_pool, basestring) and
                isinstance(scratch_pool, basestring) and
                isinstance(library, basestring) and
                isinstance(media_agent, basestring) and
                isinstance(storage_policy_name, basestring)):
            raise SDKException('Storage', '101')

        tape_library = library
        encode_dict = {"storagepolicy": storage_policy_name, "mediaagent": media_agent,
                       "library": tape_library, "drivepool": drive_pool,
                       "scratchpool": scratch_pool}
        web_service = self._POLICY + '?' + urlencode(encode_dict)

        flag, response = self._commcell_object._cvpysdk_object.make_request('PUT', web_service)

        if flag:
            try:
                if response.json():
                    if 'errorCode' in response.json():
                        error_code = response.json()['errorCode']
                        if error_code != 0:
                            o_str = 'Failed to add storage policy\nError: "{0}"'
                            raise SDKException('Storage', '102', o_str.format(error_code))

            except ValueError:
                if response.text:
                    # initialize the policies again
                    # so the policies object has all the policies
                    self.refresh()
                    return response.text.strip()
                else:
                    raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

        return self.get(storage_policy_name)

    def delete(self, storage_policy_name):
        """Deletes a storage policy from the commcell.

            Args:
                storage_policy_name (str)  --  name of the storage policy to delete

            Raises:
                SDKException:
                    if type of the storage policy name argument is not string

                    if failed to delete storage policy

                    if response is empty

                    if response is not success
        """
        if not isinstance(storage_policy_name, basestring):
            raise SDKException('Storage', '101')

        if self.has_policy(storage_policy_name):
            policy_delete_service = self._POLICY + '/{0}'.format(storage_policy_name)

            flag, response = self._commcell_object._cvpysdk_object.make_request(
                'DELETE', policy_delete_service
            )

            if flag:
                try:
                    if response.json():
                        if 'errorCode' in response.json() and 'errorMessage' in response.json():
                            error_message = response.json()['errorMessage']
                            o_str = 'Failed to delete storage policy\nError: "{0}"'

                            raise SDKException('Storage', '102', o_str.format(error_message))
                except ValueError:
                    if response.text:
                        self.refresh()
                        return response.text.strip()
                    else:
                        raise SDKException('Response', '102')
            else:
                response_string = self._commcell_object._update_response_(response.text)
                raise SDKException('Response', '101', response_string)
        else:
            raise SDKException(
                'Storage', '102', 'No policy exists with name: {0}'.format(storage_policy_name)
            )

    def refresh(self):
        """Refresh the storage policies associated with the Commcell."""
        self._policies = self._get_policies()


class StoragePolicy(object):
    """Class for performing storage policy operations for a specific storage policy"""

    def __init__(self, commcell_object, storage_policy_name, storage_policy_id=None):
        """Initialise the Storage Policy class instance."""
        self._storage_policy_name = storage_policy_name.lower()
        self._commcell_object = commcell_object

        if storage_policy_id:
            self._storage_policy_id = str(storage_policy_id)
        else:
            self._storage_policy_id = self._get_storage_policy_id()

        self._STORAGE_POLICY = self._commcell_object._services['GET_STORAGE_POLICY'] % (
            self.storage_policy_id
        )
        self._storage_policy_properties = None
        self._copies = {}
        self.refresh()

    def __repr__(self):
        """String representation of the instance of this class."""
        representation_string = 'Storage Policy class instance for Storage Policy: "{0}"'
        return representation_string.format(self.storage_policy_name)

    def _get_storage_policy_id(self):
        """Gets the storage policy id asscoiated with the storage policy"""

        storage_policies = StoragePolicies(self._commcell_object)
        return storage_policies.get(self.storage_policy_name).storage_policy_id

    def _get_storage_policy_properties(self):
        """Gets the storage policy properties of this storage policy.

            Returns:
                dict - dictionary consisting of the properties of this storage policy

            Raises:
                SDKException:
                    if response is empty

                    if response is not success
        """
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'GET', self._STORAGE_POLICY
        )

        if flag:
            if response.json():
                return response.json()
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def _initialize_storage_policy_properties(self):
        """Initializes the common properties for the storage policy."""
        self._storage_policy_properties = self._get_storage_policy_properties()
        self._copies = {}

        if 'copy' in self._storage_policy_properties:
            for copy in self._storage_policy_properties['copy']:
                copy_type = copy['copyType']
                active = copy['active']
                copy_id = copy['StoragePolicyCopy']['copyId']
                copy_name = copy['StoragePolicyCopy']['copyName'].lower()
                library_name = copy['library']['libraryName']
                copy_precedence = copy['copyPrecedence']
                temp = {
                    "copyType": copy_type,
                    "active": active,
                    "copyId": copy_id,
                    "libraryName": library_name,
                    "copyPrecedence": copy_precedence
                }
                self._copies[copy_name] = temp

    def has_copy(self, copy_name):
        """Checks if a storage policy copy exists for this storage
            policy with the input storage policy name.

            Args:
                copy_name (str)  --  name of the storage policy copy

            Returns:
                bool - boolean output whether the storage policy copy exists or not

            Raises:
                SDKException:
                    if type of the storage policy copy name argument is not string
        """
        if not isinstance(copy_name, basestring):
            raise SDKException('Storage', '101')

        return self._copies and copy_name.lower() in self._copies

    def create_secondary_copy(self,
                              copy_name,
                              library_name,
                              media_agent_name,
                              drive_pool=None,
                              spare_pool=None,
                              tape_library_id=None,
                              drive_pool_id=None,
                              spare_pool_id=None,
                              snap_copy=False):
        """Creates Synchronous copy for this storage policy

            Args:
                copy_name           (str)   --  copy name to create

                library_name        (str)   --  library name to be assigned

                media_agent_name    (str)   --  media_agent to be assigned

                snap_copy           (bool)  --  boolean on whether copy should be a snap copy
                default: False

            Raises:
                SDKException:
                    if type of inputs in not string

                    if copy with given name already exists

                    if failed to create copy

                    if response received is empty

                    if response is not success
        """
        if not (isinstance(copy_name, basestring) and
                isinstance(library_name, basestring) and
                isinstance(media_agent_name, basestring)):
            raise SDKException('Storage', '101')

        if self.has_copy(copy_name):
            err_msg = 'Storage Policy copy "{0}" already exists.'.format(copy_name)
            raise SDKException('Storage', '102', err_msg)

        media_agent_id = self._commcell_object.media_agents._media_agents[media_agent_name.lower()]['id']

        snap_copy = int(snap_copy == True)

        if drive_pool is not None:
            request_xml = """
                        <App_CreateStoragePolicyCopyReq copyName="{0}">
                            <storagePolicyCopyInfo copyType="0" isDefault="0" isMirrorCopy="0" isSnapCopy="{11}" numberOfStreamsToCombine="1">
                                <StoragePolicyCopy _type_="18" storagePolicyId="{1}" storagePolicyName="{2}" />
                                <library _type_="9" libraryId="{3}" libraryName="{4}" />
                                <mediaAgent _type_="11" mediaAgentId="{5}" mediaAgentName="{6}" />
                                <drivePool drivePoolId = "{7}" drivePoolName = "{8}"  libraryName = "{4}" />
                                <spareMediaGroup spareMediaGroupId = "{9}" spareMediaGroupName = "{10}" libraryName = "{4}" />
                                <retentionRules retainArchiverDataForDays="-1" retainBackupDataForCycles="1" retainBackupDataForDays="30" />
                            </storagePolicyCopyInfo>
                        </App_CreateStoragePolicyCopyReq>
                        """.format(copy_name, self.storage_policy_id, self.storage_policy_name,
                                   tape_library_id, library_name, media_agent_id, media_agent_name,
                                   drive_pool_id, drive_pool, spare_pool_id, spare_pool, snap_copy)

        else:
            library_id = self._commcell_object.disk_libraries._libraries[library_name.lower()]
            request_xml = """
            <App_CreateStoragePolicyCopyReq copyName="{0}">
                <storagePolicyCopyInfo copyType="0" isDefault="0" isMirrorCopy="0" isSnapCopy="{7}" numberOfStreamsToCombine="1">
                    <StoragePolicyCopy _type_="18" storagePolicyId="{1}" storagePolicyName="{2}" />
                    <library _type_="9" libraryId="{3}" libraryName="{4}" />
                    <mediaAgent _type_="11" mediaAgentId="{5}" mediaAgentName="{6}" />
                    <retentionRules retainArchiverDataForDays="-1" retainBackupDataForCycles="1" retainBackupDataForDays="30" />
                </storagePolicyCopyInfo>
            </App_CreateStoragePolicyCopyReq>
            """.format(copy_name, self.storage_policy_id, self.storage_policy_name,
                       library_id, library_name, media_agent_id, media_agent_name, snap_copy)

        create_copy_service = self._commcell_object._services['CREATE_STORAGE_POLICY_COPY']

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', create_copy_service, request_xml
        )

        self.refresh()

        if flag:
            if response.json():
                if 'error' in response.json():
                    error_code = int(response.json()['error']['errorCode'])
                    if error_code != 0:
                        if 'errorMessage' in response.json()['error']:
                            error_message = "Failed to create {0} Storage Policy copy with error \
                            {1}".format(copy_name, str(response.json()['error']['errorMessage']))
                        else:
                            error_message = "Failed to create {0} Storage Policy copy".format(
                                copy_name
                            )
                        raise SDKException('Storage', '102', error_message)

                else:
                    raise SDKException('Response', '102')
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def delete_secondary_copy(self, copy_name):
        """Deletes the copy associated with this storage policy

            Args:
                copy_name   (str)   --  copy name to be deleted

            Raises:
                SDKException:
                    if type of input parameters is not string

                    if storage policy copy doesn't exist with given name

                    if failed to delete storage policy copy

                    if response received is empty

                    if response is not success
        """
        if not isinstance(copy_name, basestring):
            raise SDKException('Storage', '101')
        else:
            copy_name = copy_name.lower()

        if not self.has_copy(copy_name):
            err_msg = 'Storage Policy copy "{0}" doesn\'t exists.'.format(copy_name)
            raise SDKException('Storage', '102', err_msg)

        delete_copy_service = self._commcell_object._services['DELETE_STORAGE_POLICY_COPY']

        request_xml = """
        <App_DeleteStoragePolicyCopyReq>
            <archiveGroupCopy _type_="18" copyId="{0}" copyName="{1}" storagePolicyId="{2}" storagePolicyName="{3}" />
        </App_DeleteStoragePolicyCopyReq>
        """.format(self._copies[copy_name]['copyId'], copy_name, self.storage_policy_id,
                   self.storage_policy_name)

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', delete_copy_service, request_xml
        )

        self.refresh()

        if flag:
            if response.json():
                if 'error' in response.json():
                    error_code = int(response.json()['error']['errorCode'])
                    if error_code != 0:
                        error_message = "Failed to delete {0} Storage Policy copy".format(
                            copy_name
                        )
                        raise SDKException('Storage', '102', error_message)
                else:
                    raise SDKException('Response', '102')
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    @property
    def copies(self):
        """Treats the storage policy copies as a read-only attribute"""
        return self._copies

    @property
    def storage_policy_id(self):
        """Treats the storage policy id as a read-only attribute."""
        return self._storage_policy_id

    @property
    def storage_policy_name(self):
        """Treats the storage policy name as a read-only attribute."""
        return self._storage_policy_name

    def run_backup_copy(self):
        """
        Runs the backup copy from Commcell for the given storage policy

        Args:
                None

        Returns:
                object - instance of the Job class for this backup copy job
        Raises:
            SDKException:

                    if backup copy job failed

                    if response is empty

                    if response is not success
        """
        request_json = {
            "taskInfo": {
                "associations": [
                    {
                        "storagePolicyName": self.storage_policy_name
                    }
                ],
                "task": {
                    "initiatedFrom": 2,
                    "taskType": 1,
                    "policyType": 3,
                    "taskFlags": {
                        "disabled": False
                    }
                },
                "subTasks": [
                    {
                        "subTaskOperation": 1,
                        "subTask": {
                            "subTaskType": 1,
                            "operationType": 4028
                        },
                        "options": {
                            "adminOpts": {
                                "snapToTapeOption": {
                                    "allowMaximum": True,
                                    "noofJobsToRun": 1
                                }
                            }
                        }
                    }
                ]
            }
        }

        backup_copy = self._commcell_object._services['CREATE_TASK']
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', backup_copy, request_json)

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self._commcell_object, response.json()['jobIds'][0])
                elif "errorCode" in response.json():
                    error_message = response.json()['errorMessage']

                    o_str = 'Backup copy job failed\nError: "{0}"'.format(error_message)
                    raise SDKException('Storage', '106', o_str)
                else:
                    raise SDKException('Storage', '106', 'Failed to run the backup copy job')
            else:
                raise SDKException('Response', '106')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def run_snapshot_cataloging(self):
        """
        Runs the deferred catalog job from Commcell for the given storage policy

        Args:
                None

        Returns:
                object - instance of the Job class for this snapshot cataloging job

        Raises:
            SDKException:

                    if snapshot cataloging job failed

                    if response is empty

                    if response is not success
        """

        request_json = {
            "taskInfo": {
                "associations": [
                    {
                        "storagePolicyName": self.storage_policy_name
                    }
                ],
                "task": {
                    "taskType": 1,
                    "initiatedFrom": 2,
                    "policyType": 0,
                    "taskFlags": {
                        "isEdgeDrive": False,
                        "disabled": False
                    }
                },
                "subTasks": [
                    {
                        "subTaskOperation": 1,
                        "subTask": {
                            "subTaskType": 1,
                            "operationType": 4043
                        },
                        "options": {
                            "backupOpts": {
                                "backupLevel": 2,
                                "dataOpt": {
                                    "useCatalogServer": True,
                                    "enforceTransactionLogUsage": False
                                }
                            }
                        }
                    }
                ]
            }
        }

        snapshot_catalog = self._commcell_object._services['CREATE_TASK']
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', snapshot_catalog, request_json)

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self._commcell_object, response.json()['jobIds'][0])
                elif "errorCode" in response.json():
                    error_message = response.json()['errorMessage']

                    o_str = 'Deferred catalog job failed\nError: "{0}"'.format(
                        error_message)
                    raise SDKException('Storage', '107', o_str)
                else:
                    raise SDKException('Storage', '107', 'Failed to run the deferred catalog job')
            else:
                raise SDKException('Response', '107')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    @property
    def storage_policy_properties(self):
        """Returns the storage policy properties

            dict - consists of storage policy properties
        """
        return self._storage_policy_properties

    @property
    def library_name(self):
        """Treats the library name as a read-only attribute."""
        primary_copy = self._storage_policy_properties.get('copy')
        if 'library' in primary_copy[0]:
            library = primary_copy[0].get('library', {})
            return library.get('libraryName')

    @property
    def library_id(self):
        """Treats the library id as a read-only attribute."""
        primary_copy = self._storage_policy_properties.get('copy')
        if 'library' in primary_copy[0]:
            library = primary_copy[0].get('library', {})
            return library.get('libraryId')

    def run_aux_copy(self, storage_policy_copy_name=None, media_agent=None, use_scale=False, streams=0,
                     all_copies=True, total_jobs_to_process=0):
        """Runs the aux copy job from the commcell.
            Args:

                storage_policy_copy_name (str)  --  name of the storage policy copy

                media_agent              (str)  --  name of the media agent

                use_scale                (bool) --  use Scalable Resource Management (True/False)

                streams                  (int)  --  number of streams to use

                all_copies               (bool) -- run auxcopy job on all copies or select copy (True/False)

                total_jobs_to_process    (int)  -- Total number jobs to process for the auxcopy job

            Returns:
                object - instance of the Job class for this aux copy job

            Raises:
                SDKException:
                    if type of the  argument is not string

                    if aux copy job failed

                    if response is empty

                    if response is not success
        """
        if not (isinstance(total_jobs_to_process, int) and
                isinstance(streams, int)):
            raise SDKException('Storage', '101')

        use_max_streams = True
        if streams != 0:
            use_max_streams = False

        if storage_policy_copy_name is not None:
            all_copies = False
            if not (isinstance(storage_policy_copy_name, basestring) and
                    isinstance(media_agent, basestring)):
                raise SDKException('Storage', '101')
        else:
            if all_copies is False:
                raise SDKException('Storage', '110')
            storage_policy_copy_name = ""
            media_agent = ""

        request_json = {
            "taskInfo": {
                "associations": [
                    {
                        "copyName": storage_policy_copy_name,
                        "storagePolicyName": self.storage_policy_name
                    }
                ],
                "task": {
                    "initiatedFrom": 2,
                    "taskType": 1,
                    "policyType": 0,
                    "taskFlags": {
                        "disabled": False
                    }
                },
                "subTasks": [
                    {
                        "subTaskOperation": 1,
                        "subTask": {
                            "subTaskType": 1,
                            "operationType": 4003
                        },
                        "options": {
                            "backupOpts": {
                                "mediaOpt": {
                                    "auxcopyJobOption": {
                                        "maxNumberOfStreams": streams,
                                        "useMaximumStreams": use_max_streams,
                                        "useScallableResourceManagement": use_scale,
                                        "totalJobsToProcess": total_jobs_to_process,
                                        "allCopies": all_copies,
                                        "mediaAgent": {
                                            "mediaAgentName": media_agent
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }

        aux_copy = self._commcell_object._services['CREATE_TASK']

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', aux_copy, request_json
        )

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self._commcell_object, response.json()['jobIds'][0])
                elif "errorCode" in response.json():
                    error_message = response.json()['errorMessage']

                    o_str = 'Restore job failed\nError: "{0}"'.format(error_message)
                    raise SDKException('Storage', '102', o_str)
                else:
                    raise SDKException('Storage', '102', 'Failed to run the aux copy job')
            else:
                raise SDKException('Response', '102')

        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def refresh(self):
        """Refresh the properties of the StoragePolicy."""
        self._initialize_storage_policy_properties()

    def delete_job(self, job_id, copy_name):
        """
        Deletes a job on Storage Policy
            Args:
                job_id      (str)   --  ID for the job to be deleted

                copy_name   (str)   --  name of the copy

        Raises:
            SDKException:
                if type of input parameters is not string
        """
        if not (isinstance(copy_name, basestring) and isinstance(job_id, basestring)):
            raise SDKException('Storage', '101')

        request_xml = """
        <App_JobOperationCopyReq operationType="2">
        <jobList appType="" commCellId="2" jobId="{0}"><copyInfo copyName="{1}" storagePolicyName="{2}"/></jobList>
        <commCellInfo commCellId="2"/></App_JobOperationCopyReq>
        """.format(job_id, copy_name, self.storage_policy_name)

        self._commcell_object._qoperation_execute(request_xml)

    def seal_ddb(self, copy_name):
        """
        Seals the deduplication database

            Args:
                copy_name   (str)   --  name of the storage policy copy

            Raises:
                SDKException:
                    if type of input parameters is not string
        """
        if not isinstance(copy_name, basestring):
            raise SDKException('Storage', '101')

        request_xml = """
        <App_SealSIDBStoreReq>
            <archiveGroupCopy>
                <copyName>{0}</copyName>
                <storagePolicyName>{1}</storagePolicyName>
            </archiveGroupCopy>
        </App_SealSIDBStoreReq>

        """.format(copy_name, self.storage_policy_name)
        self._commcell_object._qoperation_execute(request_xml)

    def update_transactional_ddb(self, update_value, copy_name, media_agent_name):
        """
        Updates TransactionalDDB option on the deduplication database

            Args:
                update_value    (bool)   --   enable(True)/disable(False)

                copy_name       (str)   --   name of the associated copy

                media_agent_name(str)   --   name of the media agent

            Raises:
                SDKException:
                    if type of input parameters is not string
        """
        if not (isinstance(copy_name, basestring) and isinstance(media_agent_name, basestring)):
            raise SDKException('Storage', '101')

        request_xml = """
        <App_UpdateStoragePolicyCopyReq >
            <storagePolicyCopyInfo >
                <StoragePolicyCopy>
                    <copyName>{0}</copyName>
                    <storagePolicyName>{1}</storagePolicyName>
                </StoragePolicyCopy>
                <DDBPartitionInfo>
                    <maInfoList>
                        <mediaAgent>
                            <mediaAgentName>{2}</mediaAgentName>
                        </mediaAgent>
                            </maInfoList>
                            <sidbStoreInfo>
                                <sidbStoreFlags>
                            <enableTransactionalDDB>{3}</enableTransactionalDDB>
                        </sidbStoreFlags>
                            </sidbStoreInfo>
                    </DDBPartitionInfo>
           </storagePolicyCopyInfo>
        </App_UpdateStoragePolicyCopyReq>
        """.format(copy_name, self.storage_policy_name, media_agent_name, int(update_value))

        self._commcell_object._qoperation_execute(request_xml)

    def create_dedupe_secondary_copy(self, copy_name, library_name,
                                     media_agent_name, path, ddb_media_agent,
                                     dash_full=None,
                                     source_side_disk_cache=None,
                                     software_compression=None):
        """Creates Synchronous copy for this storage policy

            Args:
                copy_name               (str)   --  copy name to create

                library_name            (str)   --  library name to be assigned

                media_agent_name        (str)   --  media_agent to be assigned

                path                    (str)   --  path where deduplication store is to be hosted

                ddb_media_agent         (str)   --  media agent name on which deduplication store is to be hosted

                dash_full               (bool)  --  enable DASH full on deduplication store (True/False)
                Default None

                source_side_disk_cache  (bool)  -- enable source side disk cache (True/False)
                Default None

                software_compression    (bool)  -- enable software compression (True/False)
                Default None

            Raises:
                SDKException:
                    if type of inputs in not string

                    if copy with given name already exists

                    if failed to create copy

                    if response received is empty

                    if response is not success
        """
        if not (isinstance(copy_name, basestring) and
                isinstance(library_name, basestring) and
                isinstance(path, basestring) and
                isinstance(ddb_media_agent, basestring) and
                isinstance(media_agent_name, basestring)):
            raise SDKException('Storage', '101')

        if dash_full is None:
            dash_full = "2"
        if source_side_disk_cache is None:
            source_side_disk_cache = "2"
        if software_compression is None:
            software_compression = "2"

        if self.has_copy(copy_name):
            err_msg = 'Storage Policy copy "{0}" already exists.'.format(copy_name)
            raise SDKException('Storage', '102', err_msg)

        library_id = self._commcell_object.disk_libraries.get(library_name).library_id
        media_agent_id = self._commcell_object.media_agents._media_agents[media_agent_name]['id']

        request_xml = """
        <App_CreateStoragePolicyCopyReq copyName="{0}">
            <storagePolicyCopyInfo copyType="0" isDefault="0">
                <StoragePolicyCopy _type_="18" storagePolicyId="{1}" storagePolicyName="{2}" />
                <library _type_="9" libraryId="{3}" libraryName="{4}" />
                <mediaAgent _type_="11" mediaAgentId="{5}" mediaAgentName="{6}" />
                <copyFlags auxCopyReencryptData="0" />
                <dedupeFlags enableDeduplication="1" enableDASHFull="{9}" enableSourceSideDiskCache="{10}"/>
                <retentionRules retainArchiverDataForDays="-1" retainBackupDataForCycles="1" retainBackupDataForDays="30" />
                <DDBPartitionInfo>
                    <maInfoList>
                        <mediaAgent mediaAgentName="{8}"/>
                        <subStoreList>
                            <diskFreeThresholdMB>5120</diskFreeThresholdMB>
                            <diskFreeWarningThreshholdMB>10240</diskFreeWarningThreshholdMB>
                            <accessPath path="{7}"/>
                        </subStoreList>
                    </maInfoList>
                    <sidbStoreInfo>
                        <operation>1</operation>
                        <copyName>{0}</copyName>
                        <sidbStoreFlags enableSoftwareCompression="{11}"/>
                    </sidbStoreInfo>
                </DDBPartitionInfo>

            </storagePolicyCopyInfo>
        </App_CreateStoragePolicyCopyReq>
        """.format(copy_name, self._storage_policy_id, self.storage_policy_name,
                   library_id, library_name, media_agent_id, media_agent_name,
                   path, ddb_media_agent, int(dash_full),
                   int(source_side_disk_cache), int(software_compression))

        create_copy_service = self._commcell_object._services['CREATE_STORAGE_POLICY_COPY']

        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', create_copy_service, request_xml
        )

        self.refresh()

        if flag:
            if response.json():
                if 'error' in response.json():
                    error_code = int(response.json()['error']['errorCode'])
                    if error_code != 0:
                        if 'errorMessage' in response.json()['error']:
                            error_message = "Failed to create {0} Storage Policy copy with error \
                            {1}".format(copy_name, str(response.json()['error']['errorMessage']))
                        else:
                            error_message = "Failed to create {0} Storage Policy copy".format(
                                copy_name
                            )

                        raise SDKException('Storage', '102', error_message)

                else:
                    raise SDKException('Response', '102')
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def run_ddb_verification(self,
                             copy_name,
                             ver_type,
                             ddb_ver_level):
        """
        Runs DDB verification job

            Args:
                copy_name       (str)   --  name of the copy which is associated with the DDB store

                ver_type        (str)   --  backup level (Full/Incremental)

                ddb_ver_level   (str)   --  DDB verification type
                                            (DDB_VERIFICATION/ DDB_AND_DATA_VERIFICATION /
                                            QUICK_DDB_VERIFICATION/ DDB_DEFRAGMENTATION)

            Returns:
                object - instance of the Job class for this DDB verification job

            Raises:
                SDKException:
                    if type of input parameters is not string

                    if job failed

                    if response is empty

                    if response is not success
        """
        if not (isinstance(copy_name, basestring) and
                isinstance(ver_type, basestring) and
                isinstance(ddb_ver_level, basestring)):
            raise SDKException('Storage', '101')

        request = {
                "taskInfo": {
                    "associations": [
                        {
                            "copyName": "Primary", "storagePolicyName": "sp-dedupe"
                        }
                    ], "task": {
                        "taskType": 1,
                        "initiatedFrom": 1,
                        "policyType": 0,
                        "taskId": 0,
                        "taskFlags": {
                            "disabled": False
                        }
                    }, "subTasks": [
                        {
                            "subTaskOperation": 1, "subTask": {
                                "subTaskType": 1, "operationType": 4007
                            },
                            "options": {
                                "backupOpts": {
                                    "mediaOpt": {
                                        "auxcopyJobOption": {
                                            "maxNumberOfStreams": 0,
                                            "allCopies": True,
                                            "useMaximumStreams": True,
                                            "useScallableResourceManagement": False,
                                            "mediaAgent": {
                                                "mediaAgentName": ""
                                            }
                                        }
                                    }
                                }, "adminOpts": {
                                    "archiveCheckOption": {
                                        "ddbVerificationLevel": ddb_ver_level,
                                        "jobsToVerify": 0,
                                        "allCopies": True,
                                        "backupLevel": ver_type
                                    }
                                }
                            }
                        }
                    ]
                }
                }
        data_verf = self._commcell_object._services['CREATE_TASK']
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', data_verf, request
        )

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self._commcell_object, response.json()['jobIds'][0])
                elif "errorCode" in response.json():
                    error_message = response.json()['errorMessage']

                    o_str = 'DDB verification job failed\nError: "{0}"'.format(error_message)
                    raise SDKException('Storage', '102', o_str)
                else:
                    raise SDKException('Storage', '109')
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def move_dedupe_store(self,
                          copy_name,
                          dest_path,
                          src_path,
                          dest_media_agent,
                          src_media_agent,
                          config_only=False):
        """
        Moves a deduplication store

            Args:
                copy_name               (str)   -- name of the storage policy copy

                dest_path:              (str)   -- path where new partition is to be hosted

                src_path:               (str)   -- path where existing partition is hosted

                dest_media_agent:       (str)   -- media agent name where new partition is to be hosted

                src_media_agent:        (str)   -- media agent name where existing partition is hosted

                config_only             (bool)  -- to only chnage in DB (files need to be moved manually) (True/False)
                Default : False

            Returns:
                object - object - instance of the Job class for this DDB move job

            Raises:
                SDKException:
                    if type of input parameters is not string

                    if job failed

                    if response is empty

                    if response is not success
        """
        if not (isinstance(copy_name, basestring) and
                isinstance(dest_path, basestring) and
                isinstance(src_path, basestring) and
                isinstance(dest_media_agent, basestring) and
                isinstance(src_media_agent, basestring)):
            raise SDKException('Storage', '101')

        request = {
                    "taskInfo": {
                        "associations": [
                            {
                             "copyName": copy_name, "storagePolicyName": self.storage_policy_name
                            }
                        ], "task": {
                                "taskType": 1,
                                "initiatedFrom": 1,
                                "policyType": 0,
                                "taskId": 0,
                                "taskFlags": {
                                    "disabled": False
                                }
                        }, "subTasks": [
                            {
                                "subTaskOperation": 1,"subTask": {
                                    "subTaskType": 1, "operationType": 5013
                                }, "options": {
                                    "adminOpts": {
                                        "libraryOption": {
                                            "operation": 20, "ddbMoveOption": {
                                                "flags": 2, "subStoreList": [
                                                    {
                                                        "srcPath": src_path,
                                                        "changeOnlyDB": config_only,
                                                        "destPath": dest_path,
                                                        "destMediaAgent": {
                                                            "name": dest_media_agent
                                                        }, "srcMediaAgent": {
                                                            "name": src_media_agent
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
        ddb_move = self._commcell_object._services['CREATE_TASK']
        flag, response = self._commcell_object._cvpysdk_object.make_request(
            'POST', ddb_move, request
        )

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self._commcell_object, response.json()['jobIds'][0])
                elif "errorCode" in response.json():
                    error_message = response.json()['errorMessage']

                    o_str = 'DDB move job failed\nError: "{0}"'.format(error_message)
                    raise SDKException('Storage', '102', o_str)
                else:
                    raise SDKException('Storage', '108')
            else:
                raise SDKException('Response', '102')
        else:
            response_string = self._commcell_object._update_response_(response.text)
            raise SDKException('Response', '101', response_string)

    def add_ddb_partition(self,
                          copy_id,
                          sidb_store_id,
                          sidb_new_path,
                          media_agent):
        """
        Adds a new DDB partition
            Args:
                copy_id         (str)   -- storage policy copy id

                sidb_store_id   (str)   -- deduplication store id

                sidb_new_path   (str)   -- path where new partition is to be hosted

                media_agent     (str)   -- media agent on which new partition is to be hosted

            Raises:
                SDKException:
                    if type of input parameters is not string
        """
        if not (isinstance(copy_id, basestring) and
                isinstance(sidb_store_id, basestring) and
                isinstance(sidb_new_path, basestring) and
                isinstance(media_agent, basestring)):
            raise SDKException('Storage', '101')

        if isinstance(media_agent, MediaAgent):
            media_agent = media_agent
        elif isinstance(media_agent, basestring):
            media_agent = MediaAgent(self._commcell_object, media_agent)

        request_xml = """
        <EVGui_ParallelDedupConfigReq commCellId="2" copyId="{0}" operation="15"> 
        <SIDBStore SIDBStoreId="{1}"/>
        <dedupconfigItem commCellId="0"> 
        <maInfoList><clientInfo id="{2}" name="{3}"/> 
        <subStoreList><accessPath path="{4}"/> 
        </subStoreList></maInfoList></dedupconfigItem> 
        </EVGui_ParallelDedupConfigReq>

        """.format(copy_id, sidb_store_id, media_agent.media_agent_id,
                   media_agent.media_agent_name, sidb_new_path)
        self._commcell_object._qoperation_execute(request_xml)
