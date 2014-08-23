import unittest, time, sys
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_import as h2i, h2o_jobs


class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global localhost
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(node_count=1)
        else:
            h2o_hosts.build_cloud_with_hosts(node_count=3)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def notest_RF_iris2(self):
        h2o.beta_features = True
        trees = ",".join(map(str,range(1,4)))
        timeoutSecs = 20
        csvPathname = 'iris/iris2.csv'
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, schema='put')
        h2o_cmd.runSpeeDRF(parseResult=parseResult, ntrees=trees, timeoutSecs=timeoutSecs)

    def test_RF_poker100(self):
        MISSING_RESPONSE = False
        DO_MODEL_INSPECT = False
        trees = ",".join(map(str,range(10,50,2)))
        timeoutSecs = 20
        csvPathname = 'poker/poker100'
        parseResult = h2i.import_parse(bucket='smalldata', path=csvPathname, schema='put')
        jobs = []
        for i in range(1):
            if MISSING_RESPONSE:
                rfResult = h2o_cmd.runSpeeDRF(parseResult=parseResult, ntrees=trees, timeoutSecs=timeoutSecs)
            else:
                rfResult = h2o_cmd.runSpeeDRF(parseResult=parseResult, response='C11', ntrees=trees, timeoutSecs=timeoutSecs)
            job_key = rfResult['job_key']
            model_key = rfResult['destination_key']
            jobs.append( (job_key, model_key) )

        h2o_jobs.pollWaitJobs(timeoutSecs=300)

        for job_key, model_key  in jobs:

            gridResult = h2o.nodes[0].speedrf_grid_view(job_key=job_key, destination_key=model_key)
            print "speedrf grid result for %s:", h2o.dump_json(gridResult)

            print "speedrf grid result errors:", gridResult['prediction_errors']
            for i,j in enumerate(gridResult['jobs']):
                if DO_MODEL_INSPECT:
                    print "\nspeedrf result %s:" % i, h2o.dump_json(h2o_cmd.runInspect(key=j['destination_key']))
                else:
                    # model = h2o.nodes[0].speedrf_view(modelKey=j['destination_key'])
                    model = h2o.nodes[0].speedrf_view(modelKey=j['destination_key'])
                    print "model:", h2o.dump_json(model)


            # h2o_rf.showRFGridResults(GBMResult, 15)



    def notest_GenParity1(self):
        h2o.beta_features = True
        SYNDATASETS_DIR = h2o.make_syn_dir()
        parityPl = h2o.find_file('syn_scripts/parity.pl')

        # two row dataset gets this. Avoiding it for now
        # java.lang.ArrayIndexOutOfBoundsException: 1
        # at hex.rf.Data.sample_fair(Data.java:149)

        # always match the run below!
        print "\nAssuming two row dataset is illegal. avoiding"

        for x in xrange(10,20,10):
            shCmdString = "perl " + parityPl + " 128 4 "+ str(x) + " quad " + SYNDATASETS_DIR
            h2o.spawn_cmd_and_wait('parity.pl', shCmdString.split())
            # algorithm for creating the path and filename is hardwired in parity.pl.
            csvFilename = "parity_128_4_" + str(x) + "_quad.data"

        trees = "1,2,3,4,5,6"
        timeoutSecs = 20
        # always match the gen above!
        # FIX! we fail if min is 3
        for x in xrange(10,20,10):
            sys.stdout.write('.')
            sys.stdout.flush()
            csvFilename = "parity_128_4_" + str(x) + "_quad.data"
            csvPathname = SYNDATASETS_DIR + '/' + csvFilename
            parseResult = h2i.import_parse(path=csvPathname, schema='put')
            h2o_cmd.runSpeeDRF(parseResult=parseResult, response=8, ntrees=trees, timeoutSecs=timeoutSecs)
            timeoutSecs += 2

if __name__ == '__main__':
    h2o.unit_main()
