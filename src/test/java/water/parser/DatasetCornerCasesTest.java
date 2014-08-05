package water.parser;

import static junit.framework.Assert.assertEquals;
import static junit.framework.Assert.assertTrue;

import org.junit.Test;

import water.*;
import water.fvec.Frame;
import water.fvec.ParseDataset2;
import water.api.Constants.Extensions;

public class DatasetCornerCasesTest extends TestUtil {

  /* The following tests deal with one line dataset ended by different number of newlines. */

  /*
   * HTWO-87-related bug test
   *
   *  - only one line dataset - guessing parser should recognize it.
   *  - this datasets are ended by different number of \n (0x0A):
   *    - HTWO-87-one-line-dataset-0.csv    - the line is NOT ended by \n
   *    - HTWO-87-one-line-dataset-1.csv    - the line is ended by 1 \n     (0x0A)
   *    - HTWO-87-one-line-dataset-2.csv    - the line is ended by 2 \n     (0x0A 0x0A)
   *    - HTWO-87-one-line-dataset-1dos.csv - the line is ended by \r\n     (0x0D 0x0A)
   *    - HTWO-87-one-line-dataset-2dos.csv - the line is ended by 2 \r\n   (0x0D 0x0A 0x0D 0x0A)
   */
  @Test public void testOneLineDataset() {
    // max number of dataset files
    final String tests[] = {"0", "1unix", "2unix", "1dos", "2dos" };
    final String test_dir    = "smalldata/test/";
    final String test_prefix = "HTWO-87-one-line-dataset-";

    for (int i = 0; i < tests.length; i++) {
      String datasetFilename = test_dir + test_prefix + tests[i] + ".csv";
      String keyname     = test_prefix + tests[i] + Extensions.HEX;
      testOneLineDataset(datasetFilename, keyname);
    }
  }

  private void testOneLineDataset(String filename, String keyname) {
    Key fkey = load_test_file(filename);
    Key okey = Key.make(keyname);
    Frame fr = ParseDataset2.parse(okey,new Key[]{fkey});

    assertEquals(filename + ": number of chunks == 1", 1, fr.anyVec().nChunks());
    assertEquals(filename + ": number of rows   == 2", 2, fr.numRows());
    assertEquals(filename + ": number of cols   == 9", 9, fr.numCols());

    fr.delete();
  }
}
