import org.junit.Test;
import testHelp.*;
import static org.junit.Assert.assertEquals;

import java.io.PrintStream;

public class TestJunit {
	
   AngryDog spike = new AngryDog("Spike");
   Dog husky = new Dog("Kiro");	
   
   @Test
   public void testSpeak()
   {      
      assertEquals("Grrrrr... " + husky.speak() , spike.speak());
   }
}
