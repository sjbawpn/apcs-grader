import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import java.io.PrintStream;
import java.io.FileOutputStream;

public class TestRunner {
   public static void main(String[] args) {
      
      // testHelper changes the system output stream without restoring it
      PrintStream original = new PrintStream(System.out);
      Result result = JUnitCore.runClasses(TestJunit.class);
      
      try
      {
      	FileOutputStream out = new FileOutputStream("result.log");
      	PrintStream file = new PrintStream(out);           
      	System.setOut(file);
      }
      //TODO handle exception better
      catch (Exception e)
      {
	     System.setOut(original);
      }
      
      for (Failure failure : result.getFailures())
      {
         System.out.println(failure.getDescription().getDisplayName() + " Failed with the following message:");
         System.out.println("\t" + failure.getMessage());
      }
      
      if (result.wasSuccessful())
      {
         System.out.println("All tests passed!");
      }
      else if (result.getFailureCount() < result.getRunCount())
      {
         System.out.println("Some tests failed");
      } else if (result.getFailureCount() == result.getRunCount())
      {      	
	 System.out.println("All tests failed");
      }
      
      System.out.println((result.getRunCount() - result.getFailureCount()) + "/" + result.getRunCount());
   }
}  	
