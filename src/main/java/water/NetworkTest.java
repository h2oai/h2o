package water;

import water.api.DocGen;
import water.util.Utils;

import java.util.Random;


public class NetworkTest extends Func {
  static final int API_WEAVER=1; // This file has auto-gen'd doc & json fields
  static public DocGen.FieldDoc[] DOC_FIELDS; // Initialized from Auto-Gen code.

  @API(help = "Message sizes", filter = Default.class, json=true)
  public int[] msg_sizes = new int[]{1,1<<10,1<<20}; //INPUT

  @API(help = "Repeats", filter = Default.class, json=true)
  public int repeats = 10; //INPUT

  @API(help = "Latencies in microseconds (for each message size, for each node)", json=true)
  public float[][] microseconds; //OUTPUT

  @API(help = "Bandwidths in MB/s (for each message size, for each node)", json=true)
  public float[][] bandwidths; //OUTPUT

  @API(help = "Nodes", json=true)
  public String[] nodes; //OUTPUT

  @Override protected void execImpl() {
    microseconds = new float[msg_sizes.length][];
    bandwidths = new float[msg_sizes.length][];
    for (int i=0; i<msg_sizes.length; ++i) {
      microseconds[i] = scatter(msg_sizes[i], repeats);
      Utils.div(microseconds[i], 1e3f);
      bandwidths[i] = new float[microseconds[i].length];
      for (int j=0; j< microseconds[i].length; ++j) {
        bandwidths[i][j] = msg_sizes[i] / microseconds[i][j];
      }
    }
    nodes = new String[H2O.CLOUD.size()];
    for (int i=0; i<nodes.length; ++i)
      nodes[i] = H2O.CLOUD._memary[i]._key.toString();
  }

  /**
   * Helper class that contains a payload and has an empty compute2().
   * If it is remotely executed, it will just send the payload over the wire.
   */
  private static class PingPongTask extends DTask<PingPongTask> {
    private final byte[] _payload;

    public PingPongTask(int msg_size){
      _payload = new byte[msg_size];
      new Random().nextBytes(_payload);
    }
    @Override public void compute2() {
      tryComplete();
    }
  }

  /**
   * Send a message from this node to all nodes (including self)
   * @param msg_size message size in bytes
   * @return Time in nanoseconds that it took to send the message (one per node)
   */
  private static float[] scatter(int msg_size, int repeats) {
    PingPongTask ppt = new PingPongTask(msg_size); //same payload for all nodes
    float[] times = new float[H2O.CLOUD.size()];
    for (int i=0; i<H2O.CLOUD.size(); ++i) { //loop over compute nodes
      H2ONode node = H2O.CLOUD._memary[i];
      for (int l=0; l<repeats; ++l) {
        Timer t = new Timer();
        new RPC(node, ppt).call().get(); //blocking send
        times[i] += (float) t.nanos();
      }
      times[i] /= repeats;
    }
    return times;
  }

  @Override
  public boolean toHTML(StringBuilder sb) {
    DocGen.HTML.section(sb,"Origin: " + H2O.SELF._key);

    sb.append("<table cellpadding='10'>");
    sb.append("<tr>");
    sb.append("<th>Destination / Message Size</th>");
    for (int m=0;m<msg_sizes.length;++m) {
      sb.append("<th>");
      sb.append(PrettyPrint.bytes(msg_sizes[m]));
      sb.append("</th>");
    }
    for (int n=0;n<H2O.CLOUD.size();++n) {
      sb.append("</tr>");

      sb.append("<tr>");
      sb.append("<td>");
      sb.append(H2O.CLOUD._memary[n]._key);
      sb.append("</td>");
      for (int m=0;m<msg_sizes.length;++m) {
        sb.append("<td>");
        sb.append(PrettyPrint.usecs((long)microseconds[m][n]) + ", "
                + PrettyPrint.bytesPerSecond((long)(1e6*bandwidths[m][n])));
        sb.append("</td>");
      }
    }
    sb.append("</tr>");
    sb.append("</table>");

    return true;
  }
}
