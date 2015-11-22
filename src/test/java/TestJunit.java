import org.junit.Test;
import testHelp.*;
import static org.junit.Assert.assertEquals;


import java.lang.reflect.Method;
import java.util.PriorityQueue;
public class TestJunit {
   public final String LAB_NAME = "CurvingGrades";	
   @Test
   public void test1() {
      String response = ConsoleTester.getOutput(LAB_NAME, "3\r\n87\r\n91\r\n74");
      String expected = "How many grades will you enter? Enter grade 1: Enter grade 2: Enter grade 3: Original: 87 With curve: 96\r\nOriginal: 91 With curve: 100\r\nOriginal: 74 With curve: 83\r\n";
      String rawResponse = response.trim().replace(" ","").replace("\r","").replace("\n","").toLowerCase();
      String rawExpected = expected.trim().replace(" ","").replace("\r","").replace("\n","").toLowerCase();
      
      assertEquals("expected response: " + expected + "; received response: " + response,rawResponse,rawExpected);
   }
}
