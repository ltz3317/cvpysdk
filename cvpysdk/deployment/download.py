# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""" Main file for performing the download operation

Download
========

    __init__(commcell_object)             --  initialize commcell_object of Download class
    associated with the commcell

    download_software()                   --  downloads software packages in the commcell

"""

from ..job import Job
from ..exception import SDKException
from .deploymentconstants import DownloadOptions


class Download(object):
    """"class for downloading software packages"""

    def __init__(self, commcell_object):
        """Initialize commcell_object of the Download class.

            Args:
                commcell_object (object)  --  instance of the Commcell class

            Returns:
                object - instance of the Download class

        """

        self.commcell_object = commcell_object
        self._services = commcell_object._services
        self._cvpysdkcommcell_object = commcell_object._cvpysdk_object
        self.update_option = {}

    def download_software(
            self,
            options=None,
            os_list=None,
            service_pack=None):
        """Downloads the os packages on the commcell

            Args:

                options      (enum)            --  Download option to download software

                os_list      (list of enum)    --  list of windows/unix packages to be downloaded

                service_pack (int)             --  service pack to be downloaded

            Returns:
                object - instance of the Job class for this download job

            Raises:
                SDKException:
                    if Download job failed

                    if response is empty

                    if response is not success

                    if another download job is running

            Usage:

            -   if download_software is not given any parameters it takes default value of latest
                service pack for options and downloads WINDOWS_64 package

                >>> commcell_obj.download_software()

            -   DownloadOptions and DownloadPackages enum is used for providing input to the
                download software method, it can be imported by

                >>> from cvpysdk.deployment.deploymentconstants import DownloadOptions
                    from cvpysdk.deployment.deploymentconstants import DownloadPackages

            -   sample method calls for different options, for latest service pack

                >>> commcell_obj.download_software(
                        options=DownloadOptions.lATEST_SERVICEPACK.value,
                        os_list=[DownloadPackages.WINDOWS_64.value]
                        )

            -   For Latest hotfixes for the installed service pack

                >>> commcell_obj.download_software(
                        options='DownloadOptions.lATEST_HOTFIXES.value',
                        os_list=[DownloadPackages.WINDOWS_64.value,
                                DownloadPackages.UNIX_LINUX64.value]
                        )

            -   For service pack and hotfixes

                >>> commcell_obj.download_software(
                        options='DownloadOptions.SERVICEPACK_AND_HOTFIXES.value',
                        os_list=[DownloadPackages.UNIX_MAC.value],
                        service_pack=13
                        )

                    **NOTE:** service_pack parameter must be specified for third option

        """

        # To set the default value if option is none
        if options is None:
            options = 'latest service pack'

        if DownloadOptions.LATEST_SERVICEPACK.value == options:
            self.update_option = {
                'SPName': 'latest',
                'IsSPName': False,
                'isSpDelayedDays': True,
                'isHotfixesDownload': False
            }
        elif DownloadOptions.lATEST_HOTFIXES.value == options:
            self.update_option = {
                'SPName': 'hotfix',
                'IsSPName': False,
                'isSpDelayedDays': True,
                'isHotfixesDownload': True
            }
        else:
            if service_pack is None:
                raise SDKException('Download', '102')

            self.update_option = {
                'SPName': 'SP{0}'.format(service_pack),
                'IsSPName': True,
                'isSpDelayedDays': False,
                'isHotfixesDownload': False
            }

        # to set the default value if os_list is none
        if os_list is None:
            os_list = ['Windows(X64)']

        request_json = {
            "taskInfo": {
                "task": {
                    "taskType": 1,
                    "initiatedFrom": 2,
                    "policyType": 0,
                    "alert": {
                        "alertName": ""
                    },
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
                            "operationType": 4019
                        },
                        "options": {
                            "adminOpts": {
                                "updateOption": {
                                    "syncUpdateCaches": True,
                                    "spName": self.update_option['SPName'],
                                    "isWindows": True,
                                    "majorOnly": False,
                                    "isSpName": self.update_option['IsSPName'],
                                    "copyUpdates": True,
                                    "isHotfixesDownload": self.update_option['isHotfixesDownload'],
                                    "isSpDelayedDays": self.update_option['isSpDelayedDays'],
                                    "copySoftwareAndUpdates": False,
                                    "isUnix": True,
                                    "unixDownloadPackages": {
                                        "linuxosX64": 'Linux X86_64' in os_list,
                                        "solarisosX64": 'Solaris X86_64' in os_list,
                                        "solsparcos": 'Solaris-SPARC-X86' in os_list,
                                        "freeBSDos": 'Freebsd X86' in os_list,
                                        "linuxos": 'Linux X86' in os_list,
                                        "linuxosPPC64le": 'Linux PPC64le' in os_list,
                                        "freeBSDosX64": 'Freebsd X86_64' in os_list,
                                        "solarisos": 'Solaris SPARC' in os_list,
                                        "linuxs390os": 'Linux-S390-31' in os_list,
                                        "darwinos": 'macOS' in os_list,
                                        "linuxosS390": 'Linux-S390' in os_list,
                                        "aixppcos": 'Aix-PPC-32' in os_list,
                                        "linuxosPPC64": 'Linux-PPC-64' in os_list,
                                        "aixos": 'Aix PPC' in os_list,
                                        "hpos": 'HP IA64' in os_list,
                                        "solos": 'Solaris X86' in os_list
                                    },
                                    "windowsDownloadPackages": {
                                        "windowsX64": 'Windows(X64)' in os_list,
                                        "windows32": 'Windows(32)' in os_list
                                    },
                                    "clientAndClientGroups": [
                                        {
                                            "_type_": 2
                                        }
                                    ],
                                    "downloadUpdatesJobOptions": {
                                        "downloadSoftware": True
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }

        flag, response = self._cvpysdkcommcell_object.make_request(
            'POST', self._services['CREATE_TASK'], request_json
        )

        if flag:
            if response.json():
                if "jobIds" in response.json():
                    return Job(self.commcell_object, response.json()['jobIds'][0])

                else:
                    raise SDKException('Download', '101')

            else:
                raise SDKException('Response', '102')
        else:
            raise SDKException('Response', '101')
