#!/usr/bin/env/ python
"""
_CRABRESTModel_t_

"""

import json
import unittest
import logging
import os
from WMQuality.WebTools.RESTClientAPI import methodTest
from WMQuality.WebTools.RESTBaseUnitTest import RESTBaseUnitTest
from WMQuality.WebTools.RESTServerSetup import DefaultConfig
from WMCore.Cache.WMConfigCache import ConfigCache
from WMCore.Database.CMSCouch import CouchServer
from WMCore.FwkJobReport.Report import Report
from CRABRESTModel import getJobsFromRange
from WMCore.HTTPFrontEnd.RequestManager.ReqMgrWebTools import allSoftwareVersions
import WMCore.RequestManager.RequestDB.Interface.Admin.SoftwareManagement as SoftwareAdmin

databaseURL = os.getenv("DATABASE")
databaseSocket = os.getenv("DBSOCK")

couchURL = os.getenv("COUCHURL")
workloadDB = 'workload_db_test'
configCacheDB = 'config_cache_test'
jsmCacheDB = 'jsmcache_test'


class CRABRESTModelTest(RESTBaseUnitTest):
    """
    _CRABRESTModel_ test
    """
    psetTweaks = '{"process": {"maxEvents": {"parameters_": ["input"], "input": 10}, \
"outputModules_": ["output"], "parameters_": ["outputModules_"], \
"source": {"parameters_": ["fileNames"], "fileNames": []}, \
"output": {"parameters_": ["fileName"], "fileName": "outfile.root"}, \
"options": {"parameters_": ["wantSummary"], "wantSummary": true}}}'

    confFile = '''import FWCore.ParameterSet.Config as cms
process = cms.Process("Slurp")

process.source = cms.Source("PoolSource", fileNames = cms.untracked.vstring())
process.maxEvents = cms.untracked.PSet( input       = cms.untracked.int32(10) )
process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )

process.output = cms.OutputModule("PoolOutputModule",
    outputCommands = cms.untracked.vstring("drop *", "keep recoTracks_*_*_*"),
    fileName = cms.untracked.string("outfile.root"),
)
process.out_step = cms.EndPath(process.output)'''

    insConfParams = {
        "Group" : "Analysis",
        "Team" : "Analysis",
        "UserDN" : "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=mmascher/CN=720897/CN=Marco Mascheroni",
        "ConfFile" : confFile,
        "PsetTweaks" : psetTweaks, #json
        "PsetHash" : "21cb400c6ad63c3a97fa93f8e8785127", #edmhash
        "Label" : "the label",
        "Description" : "the description"
    }

    insUserParams = {
        "Group" : "Analysis",
        "UserDN" : "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=mmascher/CN=720897/CN=Marco Mascheroni",
        "Team" : "Analysis",
        "Email" : "marco.mascheroni@cern.ch"
    }

    postReqParams = {
        "Username": "mmascher",
        "RequestorDN": "/DC=ch/DC=cern/OU=Organic Units/OU=Users/CN=mmascher/CN=720897/CN=Marco Mascheroni",
        "outputFiles": [
            "out.root"
        ],
        "Group": "Analysis",
        "RequestType": "Analysis",
        "InputDataset": "/RelValProdTTbar/JobRobot-MC_3XY_V24_JobRobot-v1/GEN-SIM-DIGI-RECO",
        "JobSplitAlgo": "FileBased",
        "ProcessingVersion": "",
        "AnalysisConfigCacheDoc": "_",
        "Requestor": "mmascher",
        "DbsUrl": "http://cmsdbsprod.cern.ch/cms_dbs_prod_global/servlet/DBSServlet",
        "ScramArch": "slc5_ia32_gcc434",
        "JobSplitArgs": {
            "files_per_job": 100
        },
        "RequestName": "crab_MyAnalysis__",
        "Team": "Analysis",
        "asyncDest": "T2_IT_Bari",
        "CMSSWVersion": "CMSSW_3_9_7"
    }

    dataLocParams = {
        "requestID" : "mmascher_crab_MyAnalysis___110429_030846",
        "jobRange" : '125-126,127,128-129'
    }


    def initialize(self):
        self.config = DefaultConfig('CRABRESTModel')
        self.config.Webtools.environment = 'development'
        self.config.Webtools.error_log_level = logging.ERROR
        self.config.Webtools.access_log_level = logging.ERROR
        self.config.Webtools.port = 8588

        #DB Parameters used by RESTServerSetup
        self.config.UnitTests.views.active.rest.database.connectUrl = databaseURL
        self.config.UnitTests.views.active.rest.database.socket = databaseSocket
        #DB Parameters used by
        self.config.UnitTests.section_('database')
        self.config.UnitTests.database.connectUrl = databaseURL
        self.config.UnitTests.database.socket = databaseSocket
        self.config.UnitTests.object = 'CRABRESTModel'
        self.config.UnitTests.views.active.rest.model.couchUrl = couchURL
        self.config.UnitTests.views.active.rest.model.workloadCouchDB = workloadDB
        self.config.UnitTests.views.active.rest.configCacheCouchURL = couchURL
        self.config.UnitTests.views.active.rest.configCacheCouchDB = configCacheDB
        self.config.UnitTests.views.active.rest.jsmCacheCouchURL = couchURL
        self.config.UnitTests.views.active.rest.jsmCacheCouchDB = jsmCacheDB
        self.config.UnitTests.views.active.rest.agentDN = ''
        self.config.UnitTests.views.active.rest.SandBoxCache_endpoint = ''
        self.config.UnitTests.views.active.rest.SandBoxCache_port = ''
        self.config.UnitTests.views.active.rest.SandBoxCache_basepath = ''
        self.config.UnitTests.views.active.rest.logLevel = 'DEBUG'

        self.schemaModules = ['WMCore.RequestManager.RequestDB']
        self.urlbase = self.config.getServerUrl()


    #Override setup to add software versions
    def setUp(self):
        """
        _setUp_
        """
        RESTBaseUnitTest.setUp(self)
        self.testInit.setupCouch("workload_db_test")
        self.testInit.setupCouch("config_cache_test", "ConfigCache")

        self.testInit.setupCouch(jsmCacheDB + "/fwjrs", "FWJRDump")

        for v in allSoftwareVersions():
            SoftwareAdmin.addSoftware(v)


    def tearDown(self):
        self.testInit.tearDownCouch()
        self.testInit.clearDatabase()


    def insertConfig(self):
        """
        _insertConfig_
        """
        host = "http://%s:%s " % (self.config.Webtools.host, self.config.Webtools.port)
        api = "/%s/rest/config/" % (self.config.Webtools.application.lower())

        jsonString = json.dumps(self.insConfParams, sort_keys=False)
        result, exp = methodTest('POST', host + api, jsonString, 'application/json', \
                                 'application/json', {'code' : 200})
        self.assertTrue(exp is not None)

        return json.loads(result)


    def testPostUserConfig(self):
        """
        _testPostUserConfig_
        """
        result = self.insertConfig()

        self.assertTrue( result.has_key("DocID") )
        self.assertTrue( result.has_key("DocRev") )
        self.assertTrue( len(result["DocID"])>0 )
        self.assertTrue( len(result["DocRev"])>0 )

        #chek if document result["DocID"] is in couch
        confCache = ConfigCache(self.config.UnitTests.views.active.rest.configCacheCouchURL, \
                    self.config.UnitTests.views.active.rest.configCacheCouchDB)
        #and contains the PSet
        confCache.loadByID(result["DocID"])
        self.assertTrue( len(confCache.getPSetTweaks())>0)


    def insertUser(self):
        """
        _insertUser_
        """
        host = "http://%s:%s " % (self.config.Webtools.host, self.config.Webtools.port)
        api = "/%s/rest/user/" % (self.config.Webtools.application.lower())

        jsonString = json.dumps(self.insUserParams, sort_keys=False)
        result, exp = methodTest('POST', host + api, jsonString, 'application/json', \
                                 'application/json', {'code' : 200})
        self.assertTrue(exp is not None)
        return json.loads(result)


    def testAddUser(self):
        """
        _testAddUser_
        """

        result = self.insertUser()

        self.assertTrue(result.has_key("group"))
        self.assertTrue(result.has_key("hn_name"))
        self.assertTrue(result.has_key("team"))

        self.assertEqual(result["team"] , "Analysis registered")
        self.assertEqual(result["hn_name"] , "mmascher")
        self.assertEqual(result["group"] , "'Analysis'egistered")


    def testPostRequest(self):
        """
        _testPostRequest_
        """
        host = "http://%s:%s " % (self.config.Webtools.host, self.config.Webtools.port)
        api = "/%s/rest/task/%s" % (self.config.Webtools.application.lower(), \
                                    self.postReqParams['RequestName'])

        #_insertConfig has been already tested in the previous test method
        result = self.insertConfig()
        self.postReqParams['AnalysisConfigCacheDoc'] = result['DocID']

        #Posting a request without registering the user first
        jsonString = json.dumps(self.postReqParams, sort_keys=False)
        result, exp = methodTest('POST', host + api, jsonString, \
                        'application/json', 'application/json', {'code' : 500})
        self.assertTrue(exp is not None)

        #Again, insertUser tested before. It should work
        self.insertUser()

        result, exp = methodTest('POST', host + api, jsonString, \
                        'application/json', 'application/json', {'code' : 200})
        self.assertTrue(exp is not None)
        result = json.loads(result)
        self.assertTrue(result.has_key("ID"))
        #SINCE python 2.7 :(
        #self.assertRegexpMatches(result['ID'], \
        #           "mmascher_crab_MyAnalysis__\d\d\d\d\d\d_\d\d\d\d\d\d")
        self.assertTrue(result['ID'].startswith("%s_%s" % (self.postReqParams["Username"], \
                                          self.postReqParams["RequestName"])))

    outpfn = 'srm://srmcms.pic.es:8443/srm/managerv2?SFN=/pnfs/pic.es/data/cms/store/user/mmascher/RelValProdTTbar/\
1304039730//0000/4C86B480-0D72-E011-978B-002481CFE25E.root'

    def injectFWJR(self, reportXML, jobID, retryCount, taskName):
        couchServer = CouchServer(os.environ["COUCHURL"])
        changeStateDB = couchServer.connectDatabase(jsmCacheDB + "/fwjrs")
        myReport = Report("cmsRun1")
        myReport.parse(reportXML)
        myReport.setTaskName(taskName)
        myReport.data.cmsRun1.status = 0
        myReport.data.cmsRun1.output.output.files.file0.OutputPFN = self.outpfn
        fwjrDocument = {"_id": "%s-%s" % (jobID, retryCount),
                        "jobid": jobID,
                        "retrycount": retryCount,
                        "fwjr": myReport.__to_json__(None),
                        "type": "fwjr"}
        changeStateDB.queue(fwjrDocument, timestamp = True)
        changeStateDB.commit()


    def testGetJobsFromRange(self):
        result = getJobsFromRange("1")
        self.assertEqual(result, [1])

        result = getJobsFromRange("1 , 2, 5")
        self.assertEqual(result, [1, 2, 5])

        result = getJobsFromRange("1 , 2-6 , 5 , 7-9")
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 5, 7, 8, 9])


    def testGetDataLocation(self):
        host = "http://%s:%s " % (self.config.Webtools.host, self.config.Webtools.port)
        api = "/%s/rest/data/" % (self.config.Webtools.application.lower())

        fwjrPath = os.path.join(os.path.dirname(__file__), 'Report.xml')
        self.injectFWJR(fwjrPath, 127, 0, "/%s/Analysis" % self.dataLocParams["requestID"])
        self.injectFWJR(fwjrPath, 128, 0, "/%s/Analysis" % self.dataLocParams["requestID"])

        result, exp = methodTest('GET', host + api, self.dataLocParams, \
                        'application/json', 'application/json', {'code' : 200})
        self.assertTrue(exp is not None)
        result = json.loads(result)

        self.assertEqual(result['127'], self.outpfn)
        self.assertEqual(result['128'], self.outpfn)

        #Check job with multiple fwjr
        self.injectFWJR(fwjrPath, 127, 1, "/%s/Analysis" % self.dataLocParams["requestID"])
        result, exp = methodTest('GET', host + api, self.dataLocParams, \
                        'application/json', 'application/json', {'code' : 200})
        self.assertTrue(exp is not None)
        result = json.loads(result)

        self.assertEqual(result['127'], self.outpfn)
        self.assertEqual(result['128'], self.outpfn)

        #Test invalid ranges
        self.dataLocParams['jobRange'] = 'I'
        result, exp = methodTest('GET', host + api, self.dataLocParams, \
                        'application/json', 'application/json', {'code' : 400})
        self.assertTrue(exp is not None)



if __name__ == "__main__":
    unittest.main()