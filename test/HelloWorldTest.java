import org.junit.Test;
import static org.junit.Assert.*;

public class HelloWorldTest {

    @Test
    public void testMessage() {
        assertEquals("Hello, World!", HelloWorld.getMessage());
    }
}