import unittest, random, sys, time
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_gbm, h2o_jobs as h2j, h2o_import
import h2o_exec as h2e, h2o_util


DO_PLOT = True
COL = 1
PHRASE = "func1"

initList = [
    (None, "func1=function(x){max(x[,%s])}" % COL),
    # (None, "func2=function(x){a=3;nrow(x[,%s])*a}" % COL),
    # (None, "func3=function(x){apply(x[,%s],2,sum)/nrow(x[,%s])}" % (COL, col) ),
    # (None, "function(x) { cbind( mean(x[,1]), mean(x[,%s]) ) }" % COL),
    # (None, "func4=function(x) { mean( x[,%s]) }" % COL),
    # (None, "func5=function(x) { sd( x[,%s]) }" % COL),
    # (None, "func6=function(x) { quantile(x[,%s] , c(0.9) ) }" % COL),
]

def write_syn_dataset(csvPathname, rowCount, colCount, minInt, maxInt, SEED):
    r1 = random.Random(SEED)
    dsf = open(csvPathname, "w+")

    for i in range(rowCount):
        rowData = []
        for j in range(colCount):
            ri = r1.randint(minInt,maxInt)
            rowData.append(ri)

        rowDataCsv = ",".join(map(str,rowData))
        dsf.write(rowDataCsv + "\n")

    dsf.close()

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1,java_heap_GB=12)
        else:
            h2o_hosts.build_cloud_with_hosts()

    @classmethod
    def tearDownClass(cls):
        ### time.sleep(3600)
        h2o.tear_down_cloud()

    def test_ddply_plot(self):
        h2o.beta_features = True
        SYNDATASETS_DIR = h2o.make_syn_dir()

        tryList = [
            (1000000, 5, 'cD', 0, 10, 30), 
            (1000000, 5, 'cD', 0, 20, 30), 
            (1000000, 5, 'cD', 0, 30, 30), 
            (1000000, 5, 'cD', 0, 40, 30), 
            (1000000, 5, 'cD', 0, 50, 30), 
            (1000000, 5, 'cD', 0, 70, 30), 
            (1000000, 5, 'cD', 0, 100, 30), 
            (1000000, 5, 'cD', 0, 130, 30), 
            (1000000, 5, 'cD', 0, 160, 30), 
            # (1000000, 5, 'cD', 0, 320, 30), 
            # starts to fail here. too many groups?
            # (1000000, 5, 'cD', 0, 640, 30), 
            # (1000000, 5, 'cD', 0, 1280, 30), 
            ]

        ### h2b.browseTheCloud()
        xList = []
        eList = []
        fList = []
        trial = 0
        for (rowCount, colCount, hex_key, minInt, maxInt, timeoutSecs) in tryList:
            SEEDPERFILE = random.randint(0, sys.maxint)
            # csvFilename = 'syn_' + str(SEEDPERFILE) + "_" + str(rowCount) + 'x' + str(colCount) + '.csv'
            csvFilename = 'syn_' + "binary" + "_" + str(rowCount) + 'x' + str(colCount) + '.csv'

            csvPathname = SYNDATASETS_DIR + '/' + csvFilename
            print "Creating random", csvPathname, "with range", (maxInt-minInt)+1
            write_syn_dataset(csvPathname, rowCount, colCount, minInt, maxInt, SEEDPERFILE)

            # PARSE train****************************************
            hexKey = 'r.hex'
            parseResult = h2i.import_parse(path=csvPathname, schema='put', hex_key=hexKey)

            for resultKey, execExpr in initList:
                h2e.exec_expr(h2o.nodes[0], execExpr, resultKey=resultKey, timeoutSecs=60)


            # do it twice..to get the optimal cached delay for time?
            execExpr = "a1 = ddply(r.hex, c(1,2), " + PHRASE + ")"
            start = time.time()
            h2e.exec_expr(h2o.nodes[0], execExpr, resultKey=None, timeoutSecs=60)
            ddplyElapsed = time.time() - start
            print "ddplyElapsed:", ddplyElapsed

            execExpr = "a2 = ddply(r.hex, c(1,2), " + PHRASE + ")"
            start = time.time()
            (execResult, result) = h2e.exec_expr(h2o.nodes[0], execExpr, resultKey=None, timeoutSecs=60)
            groups = execResult['num_rows']
            maxExpectedGroups = ((maxInt - minInt) + 1) ** 2
            h2o_util.assertApproxEqual(groups, maxExpectedGroups,  rel=0.2, 
                msg="groups %s isn't close to expected amount %s" % (groups, maxExpectedGroups))

            ddplyElapsed = time.time() - start
            print "ddplyElapsed:", ddplyElapsed
            print "execResult", h2o.dump_json(execResult)

            # should be same answer in both cases
            execExpr = "d=sum(a1!=a2)==0"
            (execResult, result) = h2e.exec_expr(h2o.nodes[0], execExpr, resultKey=None, timeoutSecs=60)
            print "execResult", h2o.dump_json(execResult)
            self.assertEqual(result, 1, "a1 and a2 weren't equal? %s" % result)

            # xList.append(ntrees)
            trial += 1
            # this is the biggest it might be ..depends on the random combinations
            # groups = ((maxInt - minInt) + 1) ** 2
            xList.append(groups)
            eList.append(ddplyElapsed)
            fList.append(ddplyElapsed)
            

        if DO_PLOT:
            xLabel = 'groups'
            eLabel = 'ddplyElapsed'
            fLabel = 'ddplyElapsed'
            eListTitle = ""
            fListTitle = ""
            h2o_gbm.plotLists(xList, xLabel, eListTitle, eList, eLabel, fListTitle, fList, fLabel)

if __name__ == '__main__':
    h2o.unit_main()
